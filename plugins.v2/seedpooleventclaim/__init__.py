"""Seedpool 多活动奖励自动领取，参考同仓库 BLUEventClaim。"""

import datetime
import html
import re
import threading
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import pytz
import requests
from lxml import etree
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.site_oper import SiteOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType


class SeedpoolEventClaim(_PluginBase):
    plugin_name = "SP活动奖励自动领取"
    plugin_desc = "自动发现 Seedpool 全部活动，逐个领取当天奖励"
    plugin_icon = "signin.png"
    plugin_version = "1.0.2"
    plugin_author = "silverfoxonline"
    author_url = "https://github.com/silverfoxonline/MoviePilot-Plugins"
    plugin_config_prefix = "seedpooleventclaim_"
    plugin_order = 13
    auth_level = 1

    BASE_URL = "https://seedpool.org"
    EVENTS_URL = BASE_URL + "/events"
    DEFAULT_CRON = "15 */6 * * *"
    MAX_HISTORY = 100
    REQUEST_TIMEOUT = 30
    RETRY_INTERVAL_HOURS = 6
    MAX_RETRIES = 2
    _enabled = False
    _notify = True
    _cron = DEFAULT_CRON
    _cookie = ""
    _random_delay = 0
    _retry_interval_hours = RETRY_INTERVAL_HOURS
    _max_retries = MAX_RETRIES
    _scheduler = None
    _run_lock = threading.Lock()

    def init_plugin(self, config: dict = None):
        self.stop_service()
        config = config or {}
        self._enabled = config.get("enabled", False)
        self._notify = config.get("notify", True)
        self._cron = config.get("cron") or self.DEFAULT_CRON
        self._cookie = (config.get("cookie") or "").strip()
        self._random_delay = self._config_int(config, "random_delay", 0, 0, 60)
        self._retry_interval_hours = self._config_int(config, "retry_interval_hours", self.RETRY_INTERVAL_HOURS, 1, 24)
        self._max_retries = self._config_int(config, "max_retries", self.MAX_RETRIES, 0, 3)
        if config.get("onlyonce"):
            self.update_config({**config, "onlyonce": False})
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(
                func=self.claim_rewards, trigger="date",
                run_date=self._now() + datetime.timedelta(seconds=3),
                name="SP活动奖励立即领取",
            )
            self._scheduler.start()

    @staticmethod
    def _config_int(config: dict, key: str, default: int, minimum: int, maximum: int) -> int:
        try:
            return min(max(int(config.get(key, default)), minimum), maximum)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _now():
        return datetime.datetime.now(pytz.timezone(settings.TZ))

    def get_state(self) -> bool:
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        if not self._enabled:
            return []
        try:
            trigger = CronTrigger.from_crontab(self._cron, timezone=settings.TZ)
            trigger.jitter = self._random_delay * 60
            return [{
                "id": "SeedpoolEventClaim", "name": self.plugin_name,
                "trigger": trigger,
                "func": self.claim_rewards, "kwargs": {},
            }]
        except (ValueError, TypeError):
            logger.error("[SeedpoolEventClaim] Cron 配置无效")
            return []

    def stop_service(self):
        if self._scheduler:
            self._scheduler.remove_all_jobs()
            if self._scheduler.running:
                self._scheduler.shutdown()
            self._scheduler = None

    @classmethod
    def _safe_url(cls, value: str, base: str = "") -> str:
        """Cookie 和 CSRF 仅发送到本站标准 HTTPS 端口。"""
        try:
            parsed = urlparse(urljoin(base or cls.BASE_URL, value))
            if (parsed.scheme == "https" and parsed.hostname == "seedpool.org"
                    and parsed.port in (None, 443) and not parsed.username
                    and not parsed.password and not parsed.query and not parsed.fragment
                    and re.fullmatch(r"/events(?:/\d+(?:/claims)?)?/?", parsed.path)):
                return cls.BASE_URL + parsed.path.rstrip("/")
        except ValueError:
            pass
        return ""

    @staticmethod
    def _tree(page: str):
        root = etree.HTML(page or "")
        if root is None:
            raise ValueError("页面为空或无法解析")
        return root

    @staticmethod
    def _text(node) -> str:
        return " ".join(" ".join(node.itertext()).split())

    @staticmethod
    def _has_class(name: str) -> str:
        return f"contains(concat(' ', normalize-space(@class), ' '), ' {name} ')"

    @classmethod
    def _events(cls, page: str) -> List[dict]:
        root = cls._tree(page)
        mains = root.xpath(f"//main[{cls._has_class('page__event--index')}]")
        if not mains or not mains[0].xpath(".//table"):
            raise ValueError("未识别到活动列表，可能登录失效或页面结构已变化")
        events = {}
        for link in mains[0].xpath(".//a[@href]"):
            url = cls._safe_url(link.get("href"), cls.EVENTS_URL)
            if url and re.fullmatch(r"/events/\d+", urlparse(url).path):
                events[url] = {"event_url": url, "event_title": cls._text(link)}
        # 不按本机日期或 Active 图标过滤：附件中已结束活动也可能标为 Active。
        return list(events.values())

    @classmethod
    def _event(cls, page: str, event_url: str) -> dict:
        root = cls._tree(page)
        mains = root.xpath(f"//main[{cls._has_class('page__event--show')}]")
        if not mains:
            raise ValueError("未识别到活动详情，可能登录失效或页面结构已变化")
        main = mains[0]
        titles = main.xpath(f".//h2[{cls._has_class('panel__heading')}]")
        days = []
        claim = None
        for article in main.xpath(f".//article[{cls._has_class('events__prize')}]"):
            headings = article.xpath(".//h3")
            date = cls._text(headings[0]) if headings else "未知日期"
            messages = [cls._text(node) for node in article.xpath(
                f".//*[{cls._has_class('events__prize-message')}]"
            )]
            classes = set(" ".join(article.xpath(".//@class")).split())
            if ("events__prize-icon--today-claimed" in classes
                    or "events__prize-winnings-list" in classes):
                status = "已领取"
            elif "events__prize-icon--today-unclaimed" in classes or "events__prize-icon--today" in classes:
                status = "今日待领取"
            elif "events__prize-icon--past" in classes:
                status = "已过期未领"
            elif "events__prize-icon--future" in classes:
                status = "待开放"
            else:
                status = "状态未知"
            day = {"date": date, "status": status,
                   "rewards": messages if status == "已领取" else []}
            days.append(day)
            if status == "今日待领取":
                for form in article.xpath(".//form"):
                    action = cls._safe_url(form.get("action", ""), event_url)
                    if (action != event_url + "/claims"
                            or form.get("method", "get").lower() != "post"):
                        continue
                    data = {node.get("name"): node.get("value", "") for node in
                            form.xpath(".//input[@type='hidden'][@name]")}
                    if not data.get("_token"):
                        tokens = root.xpath("//meta[@name='csrf-token']/@content")
                        if tokens:
                            data["_token"] = tokens[0]
                    if data.get("_token"):
                        claim = {"url": action, "data": data, "date": date}
        if not days:
            raise ValueError("活动详情没有奖励卡片，无法判断领取状态")
        return {
            "event_title": cls._text(titles[0]) if titles else event_url.rsplit("/", 1)[-1],
            "days": days, "claim": claim,
            "total_days": len(days),
            "claimed_days": sum(day["status"] == "已领取" for day in days),
        }

    def _request(self, session, method: str, url: str, **kwargs):
        """显式跟随同站重定向；不将站点凭据带到其他域名或登录页。"""
        for _ in range(6):
            response = session.request(method, url, timeout=self.REQUEST_TIMEOUT,
                                       allow_redirects=False, **kwargs)
            if response.status_code in (301, 302, 303, 307, 308):
                target = self._safe_url(response.headers.get("Location", ""), url)
                if not target:
                    raise ValueError("重定向到登录页或非活动地址，请检查 SP Cookie")
                # 领取只提交一次，307/308 不重放 POST。
                if method == "POST" and response.status_code in (307, 308):
                    raise ValueError("领取请求要求重复提交，请稍后重新检查状态")
                method, url, kwargs = "GET", target, {}
                continue
            if response.status_code >= 400:
                raise ValueError(f"站点请求失败（HTTP {response.status_code}）")
            root = self._tree(response.text)
            if root.xpath("//input[@type='password']"):
                raise ValueError("SP Cookie 已失效，请更新站点 Cookie")
            return response
        raise ValueError("站点重定向次数过多")

    def _claim_event(self, session, event: dict) -> dict:
        url = event["event_url"]
        page = self._request(session, "GET", url)
        if self._safe_url(page.url) != url:
            raise ValueError("返回页面与目标活动不一致")
        progress = self._event(page.text, url)
        claim = progress.pop("claim")
        result = {**event, **progress}
        if not claim:
            if any(day["status"] == "今日待领取" for day in progress["days"]):
                return {**result, "status": "失败", "message": "可领卡片缺少有效表单或 CSRF token"}
            if any(day["status"] == "状态未知" for day in progress["days"]):
                return {**result, "status": "失败", "message": "存在无法识别的奖励状态，请检查页面"}
            today = self._now()
            month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[today.month - 1]
            if any(day["date"] == f"{month} {today.day}" and day["status"] == "待开放" for day in progress["days"]):
                return {**result, "status": "待开放", "message": "今天的活动奖励尚未开放领取"}
            return {**result, "status": "无可领奖励", "message": "当前没有可领取表单（已领、未开放或已结束）"}
        self._request(session, "POST", claim["url"], data=claim["data"], headers={
            "Origin": self.BASE_URL, "Referer": url,
            "X-CSRF-TOKEN": claim["data"]["_token"],
        })
        # 重新读取该活动，确认原来可领的那张卡片确实变为已领取。
        verified = self._request(session, "GET", url)
        if self._safe_url(verified.url) != url:
            raise ValueError("领取后返回页面与目标活动不一致")
        after = self._event(verified.text, url)
        after.pop("claim")
        day = next((item for item in after["days"] if item["date"] == claim["date"]), None)
        if not day or day["status"] != "已领取":
            return {**result, **after, "status": "失败", "message": "已提交领取，但原奖励卡片未显示已领取"}
        return {**result, **after, "status": "成功", "reward": " / ".join(day["rewards"]),
                "message": f"{claim['date']} 奖励已核验领取"}

    def _run(self) -> List[dict]:
        site = SiteOper().get_by_domain("seedpool.org")
        cookie = self._cookie or (site.cookie if site else "")
        if not cookie:
            raise ValueError("未填写 Cookie，MoviePilot 中也未找到 SP 站点 Cookie")
        with requests.Session() as session:
            session.headers.update({
                "User-Agent": (site.ua if site else "") or settings.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Referer": self.EVENTS_URL,
            })
            for part in cookie.split(";"):
                name, sep, value = part.strip().partition("=")
                if sep and name:
                    session.cookies.set(name, value, domain="seedpool.org", path="/")
            if site and site.proxy:
                session.proxies.update(settings.PROXY or {})
            listing = self._request(session, "GET", self.EVENTS_URL)
            if self._safe_url(listing.url) != self.EVENTS_URL:
                raise ValueError("返回页面不是活动列表")
            events = self._events(listing.text)
            results = []
            for event in events:
                try:
                    results.append(self._claim_event(session, event))
                except Exception as err:
                    results.append({**event, **self._failure(err)})
            return results

    @staticmethod
    def _failure(err: Exception) -> dict:
        # requests 异常可能含请求内容，仅记录类型，不泄露 Cookie 或表单 token。
        message = str(err) if isinstance(err, ValueError) else f"请求或处理异常（{type(err).__name__}），下次运行将重新检查"
        return {"status": "失败", "message": message}

    def claim_rewards(self, expected_date: str = ""):
        now = self._now()
        today = now.date().isoformat()
        if expected_date and expected_date != today:
            logger.info("[SeedpoolEventClaim] 补查已跨日，跳过过期任务")
            return
        if not self._run_lock.acquire(blocking=False):
            logger.info("[SeedpoolEventClaim] 已有任务运行，本次跳过")
            return
        try:
            usage = self.get_data("retry_usage") or {}
            used = usage.get("count", 0) if usage.get("date") == today else 0
            if expected_date:
                if used >= self._max_retries:
                    return
                used += 1
                self.save_data("retry_usage", {"date": today, "count": used})
            try:
                results = self._run()
            except Exception as err:
                results = [{"event_title": "活动列表", **self._failure(err)}]
            self._schedule_retry(results, used)
            checked = self._now().strftime("%Y-%m-%d %H:%M:%S")
            snapshots = self.get_data("event_snapshots") or {}
            records = []
            for result in results:
                record = {key: result.get(key, "") for key in
                          ("event_url", "event_title", "status", "reward", "message")}
                record["time"] = checked
                records.append(record)
                if result.get("days"):
                    snapshots[result["event_url"]] = {
                        **record, "days": result["days"],
                        "total_days": result["total_days"], "claimed_days": result["claimed_days"],
                    }
                logger.info(f"[SeedpoolEventClaim] {record['event_title']}：{record['status']}；{record['message']}")
            # 保留最近 30 个活动缓存；历史和缓存从不保存表单或 CSRF。
            snapshots = dict(sorted(snapshots.items(), key=lambda item: item[1].get("time", ""))[-30:])
            self.save_data("event_snapshots", snapshots)
            self.save_data("claim_logs", ((self.get_data("claim_logs") or []) + records)[-self.MAX_HISTORY:])
            summary = f"检查 {len(results)} 个活动，成功 {sum(r['status'] == '成功' for r in results)}，失败 {sum(r['status'] == '失败' for r in results)}"
            self.save_data("last_run", {"time": checked, "message": summary})
            if self._notify and any(r["status"] in ("成功", "失败") for r in results):
                self.post_message(
                    mtype=NotificationType.SiteMessage, title="【SP活动奖励】" + summary,
                    text="\n".join(f"{r['event_title']}：{r['status']}\n{r.get('reward') or r['message']}" for r in results),
                )
        finally:
            self._run_lock.release()

    def _schedule_retry(self, results: List[dict], used: int):
        """同一批活动共享补查任务；Cron 重复执行不重置当日次数或推迟已有任务。"""
        pending = [result for result in results if result["status"] == "待开放"]
        job_id = "SeedpoolEventClaimRetry"
        existing = self._scheduler.get_job(job_id) if self._scheduler else None
        if not pending or not self._max_retries:
            if existing and (not self._max_retries or not any(result["status"] == "失败" for result in results)):
                self._scheduler.remove_job(job_id)
            return
        now = self._now()
        run_date = now + datetime.timedelta(hours=self._retry_interval_hours)
        if used >= self._max_retries or (not existing and run_date.date() != now.date()):
            if existing:
                self._scheduler.remove_job(job_id)
            for result in pending:
                result["status"] = "失败"
                result["message"] += "；今日补查次数已用尽或已临近跨日"
            return
        try:
            if not self._scheduler:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            if not existing:
                self._scheduler.add_job(
                    func=self.claim_rewards, trigger="date", run_date=run_date,
                    kwargs={"expected_date": now.date().isoformat()},
                    id=job_id, name="SP活动奖励未开放补查",
                )
            if not self._scheduler.running:
                self._scheduler.start()
            for result in pending:
                result["message"] += "；已安排未开放补查"
        except Exception as err:
            for result in pending:
                result["status"] = "失败"
                result["message"] += f"；安排补查失败（{type(err).__name__}）"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        fields = [
            ("VSwitch", "enabled", "启用插件", {}),
            ("VSwitch", "onlyonce", "立即运行一次", {}),
            ("VSwitch", "notify", "成功或失败时通知", {}),
            ("VCronField", "cron", "执行周期", {"placeholder": self.DEFAULT_CRON}),
        ]
        return [{"component": "VForm", "content": [
            {"component": "VRow", "content": [{
                "component": "VCol", "props": {"cols": 12, "md": 3},
                "content": [{"component": component, "props": {"model": model, "label": label, **props}}] + (
                    [{"component": "div", "props": {"class": "text-body-2 mt-2"}, "text":
                      f"当前时区：{settings.TZ}；默认每 6 小时检查，领取日期以站点卡片为准。"}]
                    if model == "cron" else []),
            } for component, model, label, props in fields]},
            {"component": "VRow", "content": [{
                "component": "VCol", "props": {"cols": 12, "md": 3}, "content": [{
                    "component": "VTextField", "props": {"model": model, "label": label, "type": "number",
                        "min": minimum, "max": maximum, "hint": hint},
                }],
            } for model, label, minimum, maximum, hint in (
                ("random_delay", "随机延迟（分钟）", 0, 60, "Cron 到点后随机延迟 0～N 分钟；0 表示关闭。"),
                ("retry_interval_hours", "未开放补查间隔（小时）", 1, 24, "默认 6 小时；仅当天奖励未开放时补查，跨日自动跳过。"),
                ("max_retries", "当日最多补查次数", 0, 3, "默认 2 次；0 表示不补查，不计 Cron 和立即运行；多个活动共用一次补查。"),
            )]},
            {"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12}, "content": [
                {"component": "VTextField", "props": {
                    "model": "cookie", "label": "SP Cookie（可选）", "type": "password",
                    "placeholder": "留空则读取 MoviePilot 的 SP 站点 Cookie",
                    "hint": "填写后优先使用此 Cookie；UA 和代理读取 seedpool.org 站点设置。",
                }},
            ]}]},
            {"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text":
                "自动从 /events 获取所有活动并分别领取，以网页可领卡片为准。随机延迟只影响 Cron；补查会重新检查全部活动，已领取不重复提交。单个活动失败不影响其他活动。详情页只展示缓存，不访问站点。"}},
        ]}], {"enabled": False, "notify": True, "onlyonce": False, "cron": self.DEFAULT_CRON, "cookie": "",
              "random_delay": 0, "retry_interval_hours": self.RETRY_INTERVAL_HOURS, "max_retries": self.MAX_RETRIES}

    @staticmethod
    def _table(headers: tuple, keys: tuple, rows: List[dict]) -> dict:
        return {"component": "VTable", "props": {"density": "compact", "hover": True}, "content": [
            {"component": "thead", "content": [{"component": "tr", "content": [
                {"component": "th", "text": title} for title in headers]}]},
            {"component": "tbody", "content": [{"component": "tr", "content": [
                {"component": "td", "text": str(row.get(key) or "—")} for key in keys]} for row in rows]},
        ]}

    def get_page(self) -> List[dict]:
        """按活动名称分标签页；标签只切换缓存展示，不触发网络请求。"""
        last_run = self.get_data("last_run") or {}
        page = [{"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text":
                f"{last_run.get('time', '')} {last_run.get('message', '尚未执行，请勾选立即运行一次并保存')}"}}]
        snapshots = dict(self.get_data("event_snapshots") or {})
        records = list(reversed(self.get_data("claim_logs") or []))
        # 详情请求失败的活动仍有标签，展示错误和先前缓存；兼容 1.0.0 的数据。
        for record in records:
            url = record.get("event_url")
            if url and self._safe_url(url):
                snapshots.setdefault(url, {"event_title": record.get("event_title") or url})
        urls = sorted(snapshots, key=lambda url: (snapshots[url].get("event_title") or "", url))
        if urls:
            # MP2 PageRender 直接传 props，不提供 FormRender 的 v-model。
            # 使用原生 radio/label 与局部 CSS 切换，避免标签高亮变化但内容不切换。
            css = """
                .sp-event-tabs { position: relative; display: flex; flex-wrap: wrap; gap: 4px; }
                .sp-event-tabs > .sp-event-radio { position: absolute; opacity: 0; width: 1px; height: 1px; }
                .sp-event-tabs > .sp-event-label { padding: 12px 18px; cursor: pointer; border-bottom: 2px solid transparent; font-weight: 500; }
                .sp-event-tabs > .sp-event-radio:checked + .sp-event-label { color: rgb(var(--v-theme-primary)); border-color: currentColor; background: rgba(var(--v-theme-primary), .08); }
                .sp-event-tabs > .sp-event-radio:focus-visible + .sp-event-label { outline: 2px solid rgb(var(--v-theme-primary)); outline-offset: -2px; }
                .sp-event-tabs > .sp-event-panel { display: none; flex-basis: 100%; min-width: 0; padding-top: 16px; border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
            """
            controls, panels = [], []
            for index, url in enumerate(urls):
                tab_id = f"sp-event-{index}"
                panel_id = tab_id + "-panel"
                css += f"\n.sp-event-tabs > #{tab_id}:checked ~ #{panel_id} {{ display: block; }}"
                controls.extend([
                    {"component": "input", "props": {"type": "radio", "name": "sp-event-tabs", "id": tab_id,
                        "class": "sp-event-radio", "checked": index == 0, "aria-controls": panel_id,
                        "aria-label": snapshots[url].get("event_title") or url}},
                    {"component": "label", "props": {"for": tab_id, "id": tab_id + "-label", "class": "sp-event-label"},
                     "text": snapshots[url].get("event_title") or url},
                ])
                event_records = [record for record in records if record.get("event_url") == url]
                panels.append({"component": "section", "props": {"id": panel_id, "class": "sp-event-panel",
                    "aria-labelledby": tab_id + "-label"},
                    "content": self._event_page(url, snapshots[url], event_records)})
            page.append({"component": "div", "props": {"class": "sp-event-tabs mt-4"}, "content": [
                {"component": "style", "html": css}, *controls, *panels,
            ]})
        else:
            page.append({"component": "VAlert", "props": {"type": "warning", "variant": "tonal",
                "text": "暂无活动缓存。勾选立即运行一次并保存后，将按发现的活动名称生成标签页。"}})
        errors = [record for record in records if not record.get("event_url")]
        if errors:
            page.extend([{"component": "div", "props": {"class": "text-h6 mt-4 mb-2"}, "text": "活动列表执行历史"},
                         self._table(("时间", "结果", "说明"), ("time", "status", "message"), errors[:10])])
        return page

    def _event_page(self, url: str, snapshot: dict, records: List[dict]) -> List[dict]:
        """各活动独立沿用 BLU 的摘要、奖励卡片及三列每日状态。"""
        days = snapshot.get("days") or []
        latest = records[0] if records else snapshot
        status = latest.get("status") or "尚未执行"
        page = [{"component": "div", "props": {"class": "text-h5 font-weight-bold mt-2 mb-4"}, "text":
                 f"🎉 {snapshot.get('event_title') or 'SP Event'} · Event #{url.rsplit('/', 1)[-1]}"},
                {"component": "a", "props": {"href": url, "target": "_blank", "rel": "noopener noreferrer"}, "text": "查看站点活动页面"},
                {"component": "VAlert", "props": {"type": "error" if status == "失败" else "success" if status == "成功" else "info",
                    "variant": "tonal", "title": f"最近执行：{status}", "class": "my-4",
                    "text": " · ".join(filter(None, [latest.get("time"), latest.get("message"), latest.get("reward")]))}}]
        if days:
            summary = [("活动总天数", len(days), "info"),
                       ("已领取", sum(day["status"] == "已领取" for day in days), "success"),
                       ("已过期未领", sum(day["status"] == "已过期未领" for day in days), "error"),
                       ("今日待领取", sum(day["status"] == "今日待领取" for day in days), "warning"),
                       ("待开放", sum(day["status"] == "待开放" for day in days), "info")]
            page.append({"component": "div", "props": {"class": "text-body-2 mb-2"}, "text": f"状态缓存更新：{snapshot.get('time') or '—'}"})
            page.append({"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12, "sm": 6, "md": 2},
                "content": [{"component": "VAlert", "props": {"type": color, "variant": "tonal", "title": title, "text": str(value)}}],
            } for title, value, color in summary]})
            page.append({"component": "div", "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"}, "text": "奖励总计"})
            totals = self._reward_totals(days)
            if totals:
                page.append({"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12, "sm": 6, "md": 3},
                    "content": [{"component": "VAlert", "props": {"type": "success", "variant": "tonal", "title": item["label"], "text": item["display"]}}],
                } for item in totals]})
            else:
                page.append({"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text": "当前活动尚无已领取奖励。"}})
            current_month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[self._now().month - 1]
            visible = [day for day in days if day["date"].startswith(current_month + " ")] or days
            icons = {"已领取": "✅", "已过期未领": "⛔", "今日待领取": "🎁", "待开放": "⏳", "状态未知": "❔"}
            rows = [{"date": day["date"], "status": f"{icons.get(day['status'], '❔')} {day['status']} " + " / ".join(day["rewards"])} for day in visible]
            page.append({"component": "div", "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"}, "text": f"每日状态（{current_month}）"})
            page.append({"component": "VRow", "content": [{"component": "VCol", "props": {"cols": 12, "md": 4},
                "content": [self._table(("日期", "状态 / 奖励"), ("date", "status"), items)],
            } for items in (rows[:10], rows[10:20], rows[20:]) if items]})
        else:
            page.append({"component": "VAlert", "props": {"type": "warning", "variant": "tonal", "text": "暂无此活动的每日状态缓存，请查看最近执行结果。"}})
        page.extend([{"component": "div", "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"}, "text": "本活动执行历史（最近 10 条）"},
                     self._table(("时间", "结果", "本次奖励", "说明"), ("time", "status", "reward", "message"), records[:10])])
        return page

    @staticmethod
    def _reward_totals(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """汇总已领取日期中的已知及未知奖励类型。"""
        totals: Dict[str, Dict[str, Any]] = {}
        for day in days:
            if day.get("status") != "已领取":
                continue
            for reward in day.get("rewards") or []:
                parsed = SeedpoolEventClaim._parse_reward(reward)
                current = totals.setdefault(parsed["key"], {
                    "key": parsed["key"],
                    "label": parsed["label"],
                    "kind": parsed["kind"],
                    "value": 0,
                })
                current["value"] += parsed["value"]

        priority = {"bon": 0, "fl_tokens": 1, "upload": 2}
        result = sorted(totals.values(), key=lambda item: (priority.get(item["key"], 99), item["label"]))
        for item in result:
            if item["kind"] == "bytes":
                item["display"] = SeedpoolEventClaim._format_bytes(item["value"])
            elif item["kind"] == "count":
                item["display"] = f"× {int(item['value'])}"
            else:
                item["display"] = SeedpoolEventClaim._format_number(item["value"])
        return result

    @staticmethod
    def _parse_reward(reward: str) -> Dict[str, Any]:
        """识别常见奖励；未知奖励按名称动态分组。"""
        text = re.sub(r"\s+", " ", html.unescape(reward or "")).strip()
        number = r"([\d,]+(?:\.\d+)?)"

        match = re.fullmatch(number + r"\s*(?:BON|BP|BONUS(?:\s+POINTS?)?)", text, re.I)
        if match:
            return {"key": "bon", "label": "BON", "kind": "number", "value": SeedpoolEventClaim._number(match.group(1))}

        match = re.fullmatch(number + r"\s*(?:FL\s*)?(?:TOKENS?|FREELEECH\s+TOKENS?)", text, re.I)
        if match:
            return {"key": "fl_tokens", "label": "FL Token", "kind": "number", "value": SeedpoolEventClaim._number(match.group(1))}

        match = re.fullmatch(
            number + r"\s*(KiB|MiB|GiB|TiB|KB|MB|GB|TB)(?:\s+UPLOAD)?",
            text,
            re.I,
        )
        if match:
            unit = match.group(2).lower()
            powers = {"kb": 1, "mb": 2, "gb": 3, "tb": 4, "kib": 1, "mib": 2, "gib": 3, "tib": 4}
            base = 1024 if "i" in unit else 1000
            value = SeedpoolEventClaim._number(match.group(1)) * (base ** powers[unit])
            return {"key": "upload", "label": "上传量", "kind": "bytes", "value": value}

        match = re.fullmatch(number + r"\s+(.+)", text)
        if match:
            label = re.sub(r"\s+", " ", match.group(2)).strip()
            key = "other:" + label.casefold()
            return {"key": key, "label": label, "kind": "number", "value": SeedpoolEventClaim._number(match.group(1))}

        key = "other:" + text.casefold()
        return {"key": key, "label": text or "其他奖励", "kind": "count", "value": 1}

    @staticmethod
    def _number(value: str) -> float:
        return float((value or "0").replace(",", ""))

    @staticmethod
    def _format_number(value: float) -> str:
        return f"{int(value):,}" if float(value).is_integer() else f"{value:,.2f}".rstrip("0").rstrip(".")

    @staticmethod
    def _format_bytes(value: float) -> str:
        size = float(value)
        for unit in ("B", "KiB", "MiB", "GiB"):
            if abs(size) < 1024:
                return f"{size:,.2f}".rstrip("0").rstrip(".") + f" {unit}"
            size /= 1024
        return f"{size:,.2f}".rstrip("0").rstrip(".") + " TiB"

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []
