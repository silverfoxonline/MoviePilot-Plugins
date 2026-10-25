"""Seedpool 多活动奖励自动领取，参考同仓库 BLUEventClaim。"""

import datetime
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
    plugin_version = "1.0.0"
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
    _enabled = False
    _notify = True
    _cron = DEFAULT_CRON
    _cookie = ""
    _scheduler = None
    _run_lock = threading.Lock()

    def init_plugin(self, config: dict = None):
        self.stop_service()
        config = config or {}
        self._enabled = config.get("enabled", False)
        self._notify = config.get("notify", True)
        self._cron = config.get("cron") or self.DEFAULT_CRON
        self._cookie = (config.get("cookie") or "").strip()
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
    def _now():
        return datetime.datetime.now(pytz.timezone(settings.TZ))

    def get_state(self) -> bool:
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        if not self._enabled:
            return []
        try:
            return [{
                "id": "SeedpoolEventClaim", "name": self.plugin_name,
                "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ),
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

    def claim_rewards(self):
        if not self._run_lock.acquire(blocking=False):
            logger.info("[SeedpoolEventClaim] 已有任务运行，本次跳过")
            return
        try:
            try:
                results = self._run()
            except Exception as err:
                results = [{"event_title": "活动列表", **self._failure(err)}]
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

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        fields = [
            ("VSwitch", "enabled", "启用插件", {}),
            ("VSwitch", "notify", "领取结果通知", {}),
            ("VSwitch", "onlyonce", "立即运行一次", {}),
            ("VTextField", "cron", "执行周期", {"hint": f"使用 MP2 时区 {settings.TZ}；默认每 6 小时检查一次"}),
            ("VTextField", "cookie", "SP Cookie（可选）", {"type": "password", "hint": "留空使用 MoviePilot 中 seedpool.org 站点的 Cookie、UA 和代理设置"}),
        ]
        return [{"component": "VForm", "content": [
            {"component": "VRow", "content": [{
                "component": "VCol", "props": {"cols": 12, "md": 4 if component == "VSwitch" else 12},
                "content": [{"component": component, "props": {"model": model, "label": label, **props}}],
            } for component, model, label, props in fields]},
            {"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text":
                "自动从 /events 获取所有活动并分别领取，以网页可领卡片为准。每次先检查再提交，已领取不重复提交；单个活动失败不影响其他活动。详情页只展示缓存，不访问站点。"}},
        ]}], {"enabled": False, "notify": True, "onlyonce": False, "cron": self.DEFAULT_CRON, "cookie": ""}

    @staticmethod
    def _table(headers: tuple, keys: tuple, rows: List[dict]) -> dict:
        return {"component": "VTable", "props": {"density": "compact", "hover": True}, "content": [
            {"component": "thead", "content": [{"component": "tr", "content": [
                {"component": "th", "text": title} for title in headers]}]},
            {"component": "tbody", "content": [{"component": "tr", "content": [
                {"component": "td", "text": str(row.get(key) or "—")} for key in keys]} for row in rows]},
        ]}

    def get_page(self) -> List[dict]:
        last_run = self.get_data("last_run") or {}
        page = [{"component": "VAlert", "props": {"type": "info", "variant": "tonal", "text":
                f"{last_run.get('time', '')} {last_run.get('message', '尚未执行，请勾选立即运行一次并保存')}"}}]
        current_month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[self._now().month - 1]
        snapshots = self.get_data("event_snapshots") or {}
        for snapshot in sorted(snapshots.values(), key=lambda item: item.get("time", ""), reverse=True):
            page.append({"component": "div", "props": {"class": "text-h6 mt-4 mb-2"}, "text":
                         f"🎁 {snapshot['event_title']} · 已领 {snapshot['claimed_days']}/{snapshot['total_days']} 天 · 更新 {snapshot['time']}"})
            days = snapshot.get("days") or []
            visible = [day for day in days if day["date"].startswith(current_month + " ")] or days
            rows = [{"date": day["date"], "status": day["status"], "reward": " / ".join(day["rewards"])} for day in visible]
            page.append(self._table(("日期", "状态", "奖励"), ("date", "status", "reward"), rows))
        page.append({"component": "div", "props": {"class": "text-h6 mt-4 mb-2"}, "text": "执行历史（最近 100 条）"})
        page.append(self._table(("时间", "活动", "结果", "奖励", "说明"),
                                ("time", "event_title", "status", "reward", "message"),
                                list(reversed(self.get_data("claim_logs") or []))))
        return page

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []
