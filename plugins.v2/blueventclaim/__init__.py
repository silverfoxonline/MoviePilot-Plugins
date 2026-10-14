"""BLU 活动奖励自动领取。"""

import datetime
import html
import re
import threading
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.site_oper import SiteOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType
from app.utils.http import RequestUtils


class BLUEventClaim(_PluginBase):
    """使用 MoviePilot 中的 BLU Cookie 领取当天活动奖励。"""

    plugin_name = "BLU活动奖励自动领取"
    plugin_desc = "通过 BLU 网页接口自动领取当天 Event 奖励"
    plugin_icon = "https://blutopia.cc/favicon.svg"
    plugin_version = "1.0.1"
    plugin_author = "silverfoxonline"
    author_url = "https://github.com/silverfoxonline/MoviePilot-Plugins"
    plugin_config_prefix = "blueventclaim_"
    plugin_order = 12
    auth_level = 1

    DEFAULT_EVENT_URL = "https://blutopia.cc/giveaways/4"
    DEFAULT_CRON = "5 9 * * *"
    REQUEST_TIMEOUT = 30
    MAX_HISTORY = 10
    MAX_EVENT_SNAPSHOTS = 20

    _enabled = False
    _onlyonce = False
    _notify = True
    _cron = DEFAULT_CRON
    _random_delay = 0
    _event_url = DEFAULT_EVENT_URL
    _cookie = ""
    _scheduler: Optional[BackgroundScheduler] = None
    _claim_lock = threading.Lock()

    def init_plugin(self, config: dict = None):
        """读取配置，并按需安排一次性领取。"""
        self.stop_service()
        if config:
            self._enabled = config.get("enabled", False)
            self._onlyonce = config.get("onlyonce", False)
            self._notify = config.get("notify", True)
            self._cron = config.get("cron") or self.DEFAULT_CRON
            try:
                self._random_delay = min(max(int(config.get("random_delay") or 0), 0), 60)
            except (TypeError, ValueError):
                self._random_delay = 0
            self._event_url = (config.get("event_url") or self.DEFAULT_EVENT_URL).strip()
            self._cookie = (config.get("cookie") or "").strip()

        if self._onlyonce:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(
                func=self._claim_reward,
                trigger="date",
                run_date=datetime.datetime.now(tz=pytz.timezone(settings.TZ))
                + datetime.timedelta(seconds=3),
                name="BLU活动奖励立即领取",
            )
            self._scheduler.start()
            self._onlyonce = False
            self._save_config()

    def get_state(self) -> bool:
        """返回插件启用状态。"""
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        """注册每日领取任务。"""
        if not self._enabled or not self._cron:
            return []
        try:
            trigger = CronTrigger.from_crontab(self._cron)
            trigger.jitter = self._random_delay * 60
            return [{
                "id": "BLUEventClaim",
                "name": "BLU活动奖励自动领取",
                "trigger": trigger,
                "func": self._claim_reward,
                "kwargs": {},
            }]
        except Exception as err:
            logger.error(f"[BLUEventClaim] 定时配置错误: {err}")
            return []

    def stop_service(self):
        """停止插件自行创建的一次性调度器。"""
        if self._scheduler:
            self._scheduler.remove_all_jobs()
            if self._scheduler.running:
                self._scheduler.shutdown()
            self._scheduler = None

    def _save_config(self):
        """保存当前配置，并复位一次性运行开关。"""
        self.update_config({
            "enabled": self._enabled,
            "onlyonce": False,
            "notify": self._notify,
            "cron": self._cron,
            "random_delay": self._random_delay,
            "event_url": self._event_url,
            "cookie": self._cookie,
        })

    def _claim_reward(self):
        """串行执行一次领取，并保存可审计的结果。"""
        if not self._claim_lock.acquire(blocking=False):
            logger.warning("[BLUEventClaim] 已有领取任务运行，本次跳过")
            return
        try:
            result = self._do_claim()
        except Exception as err:
            logger.exception(f"[BLUEventClaim] 领取异常: {err}")
            result = {"status": "失败", "message": str(err)}
        finally:
            self._claim_lock.release()

        record = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_url": result.get("event_url", self._event_url),
            "status": result["status"],
            "reward": result.get("reward", ""),
            "message": result.get("message", ""),
            "total_days": result.get("total_days"),
            "claimed_days": result.get("claimed_days"),
        }
        history = self.get_data("claim_logs") or []
        self.save_data("claim_logs", (history + [record])[-self.MAX_HISTORY:])

        if result.get("days") is not None:
            snapshots = self.get_data("event_snapshots") or {}
            snapshots[record["event_url"]] = {
                "event_url": record["event_url"],
                "event_title": result.get("event_title", "BLU Event"),
                "updated_at": record["time"],
                "total_days": result.get("total_days", 0),
                "claimed_days": result.get("claimed_days", 0),
                "expired_days": result.get("expired_days", 0),
                "future_days": result.get("future_days", 0),
                "claimable_days": result.get("claimable_days", 0),
                "reward_totals": result.get("reward_totals", []),
                "days": result.get("days", []),
            }
            if len(snapshots) > self.MAX_EVENT_SNAPSHOTS:
                snapshots = dict(list(snapshots.items())[-self.MAX_EVENT_SNAPSHOTS:])
            self.save_data("event_snapshots", snapshots)

        log_message = f"[BLUEventClaim] {record['status']}: {record['message']}"
        if record["status"] == "失败":
            logger.error(log_message)
        else:
            logger.info(log_message)

        if self._notify and record["status"] in ("成功", "失败"):
            reward_text = f"\n奖励：{record['reward']}" if record["reward"] else ""
            progress_text = ""
            if record["total_days"] is not None and record["claimed_days"] is not None:
                progress_text = f"\n活动进度：{record['claimed_days']} / {record['total_days']} 天"
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"【BLU活动奖励】{record['status']}",
                text=f"{record['message']}{reward_text}{progress_text}",
            )

    def _do_claim(self) -> Dict[str, Any]:
        """读取活动页并在需要时提交一次领取请求。"""
        event_url = self._normalized_event_url(self._event_url)
        if not event_url:
            return {"status": "失败", "message": "活动地址必须是 blutopia.cc 的 HTTPS 地址"}

        site = SiteOper().get_by_domain("blutopia.cc")
        cookie = self._cookie or (site.cookie if site else "")
        if not cookie:
            return {"status": "失败", "message": "未填写 Cookie，MoviePilot 中也未找到 BLU 站点 Cookie"}

        user_agent = (site.ua if site else "") or settings.USER_AGENT
        proxies = settings.PROXY if site and site.proxy else None

        session = requests.Session()
        request = RequestUtils(
            ua=user_agent,
            cookies=cookie,
            proxies=proxies,
            session=session,
            timeout=self.REQUEST_TIMEOUT,
            referer=event_url,
            accept_type="text/html,application/xhtml+xml",
        )

        page = request.get_res(url=event_url)
        error = self._response_error(page, "读取活动页")
        if error:
            return error
        if self._is_login_page(page):
            return {"status": "失败", "message": "BLU Cookie 已失效，请先在站点设置中更新"}

        page_state = self._page_state(page.text)
        progress = self._event_progress(page.text)
        if page_state["claimed"]:
            reward = self._claimed_reward(page.text)
            return {
                "event_url": event_url,
                "status": "已领取",
                "reward": reward,
                "message": "今天的活动奖励已经领取，无需重复提交",
                **progress,
            }

        csrf_token = self._csrf_token(page.text)
        if not csrf_token:
            return {
                "event_url": event_url,
                "status": "失败",
                "message": "活动页未找到 CSRF token",
                **progress,
            }

        claim_url = self._claim_url(page.text, event_url)
        if not claim_url:
            detail = "今天尚未开放领取" if page_state["future"] else "活动页未找到领取表单"
            return {"event_url": event_url, "status": "失败", "message": detail, **progress}

        response = request.post_res(
            url=claim_url,
            data={"_token": csrf_token},
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://blutopia.cc",
                "Referer": event_url,
                "X-CSRF-TOKEN": csrf_token,
            },
        )
        error = self._response_error(response, "提交领取请求")
        if error:
            return {"event_url": event_url, **error, **progress}
        if self._is_login_page(response):
            return {
                "event_url": event_url,
                "status": "失败",
                "message": "领取时登录失效，请更新 BLU Cookie",
                **progress,
            }
        if not self._page_state(response.text)["claimed"]:
            return {
                "event_url": event_url,
                "status": "失败",
                "message": "领取请求已提交，但返回页面未显示今天已领取",
                **progress,
            }

        reward = self._claimed_reward(response.text)
        progress = self._event_progress(response.text)
        return {
            "event_url": event_url,
            "status": "成功",
            "reward": reward,
            "message": "今天的 BLU 活动奖励领取成功",
            **progress,
        }

    @staticmethod
    def _normalized_event_url(value: str) -> str:
        """仅接受 BLU 活动详情页，避免携带 Cookie 请求到其他主机。"""
        try:
            parsed = urlparse(value.strip())
        except (AttributeError, ValueError):
            return ""
        if parsed.scheme != "https" or parsed.hostname != "blutopia.cc":
            return ""
        if not re.fullmatch(r"/giveaways/\d+/?", parsed.path):
            return ""
        return f"https://blutopia.cc{parsed.path.rstrip('/')}"

    @staticmethod
    def _csrf_token(page_html: str) -> str:
        """从活动页 meta 标签读取 Laravel CSRF token。"""
        match = re.search(
            r'<meta\s+[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)',
            page_html or "",
            re.IGNORECASE,
        )
        if not match:
            match = re.search(
                r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']csrf-token["\']',
                page_html or "",
                re.IGNORECASE,
            )
        return html.unescape(match.group(1)) if match else ""

    @staticmethod
    def _claim_url(page_html: str, event_url: str) -> str:
        """优先采用页面表单 action，只允许同站的 claims 端点。"""
        for action in re.findall(r'<form\b[^>]*action=["\']([^"\']+)["\']', page_html or "", re.I):
            candidate = urljoin(event_url, html.unescape(action))
            parsed = urlparse(candidate)
            if parsed.hostname == "blutopia.cc" and re.fullmatch(
                r"/giveaways/\d+/claims/?", parsed.path
            ):
                return candidate
        if re.search(r"events__prize-icon--today(?!-claimed)", page_html or "", re.I):
            return f"{event_url.rstrip('/')}/claims"
        return ""

    @staticmethod
    def _page_state(page_html: str) -> Dict[str, bool]:
        """识别当天奖励状态。"""
        text = page_html or ""
        return {
            "claimed": bool(re.search(r"events__prize-icon--today-claimed", text, re.I)),
            "future": bool(re.search(r"events__prize-icon--future", text, re.I))
            and not bool(re.search(r"events__prize-icon--today(?!-claimed)", text, re.I)),
        }

    @staticmethod
    def _claimed_reward(page_html: str) -> str:
        """读取 today-claimed 卡片中显示的奖励文本。"""
        match = re.search(
            r'<article\b[^>]*class=["\'][^"\']*events__prize[^"\']*["\'][^>]*>'
            r'(?:(?!</article>).)*events__prize-icon--today-claimed'
            r'(?:(?!</article>).)*</article>',
            page_html or "",
            re.I | re.S,
        )
        if not match:
            return ""
        text = re.sub(r"<[^>]+>", " ", match.group(0))
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        text = re.sub(r"^[A-Z][a-z]{2}\s+\d{1,2}\s*", "", text)
        return text

    @classmethod
    def _event_progress(cls, page_html: str) -> Dict[str, Any]:
        """解析活动名称、逐日状态和动态奖励汇总。"""
        days = cls._event_days(page_html)
        status_counts = {
            status: sum(day["status"] == status for day in days)
            for status in ("已领取", "已过期未领", "待开放", "今日待领取")
        }
        return {
            "event_title": cls._event_title(page_html),
            "total_days": len(days),
            "claimed_days": status_counts["已领取"],
            "expired_days": status_counts["已过期未领"],
            "future_days": status_counts["待开放"],
            "claimable_days": status_counts["今日待领取"],
            "reward_totals": cls._reward_totals(days),
            "days": days,
        }

    @staticmethod
    def _event_title(page_html: str) -> str:
        """读取活动标题。"""
        match = re.search(
            r'<h2\b[^>]*class=["\'][^"\']*panel__heading[^"\']*["\'][^>]*>(.*?)</h2>',
            page_html or "",
            re.I | re.S,
        )
        return BLUEventClaim._plain_text(match.group(1)) if match else "BLU Event"

    @staticmethod
    def _event_days(page_html: str) -> List[Dict[str, Any]]:
        """把每个活动奖励卡片转换为日期、状态、奖励和原始提示。"""
        articles = re.findall(
            r'<article\b[^>]*class=["\'][^"\']*events__prize[^"\']*["\'][^>]*>'
            r'(?:(?!</article>).)*</article>',
            page_html or "",
            re.I | re.S,
        )
        days = []
        for article in articles:
            date_match = re.search(r"<h3\b[^>]*>(.*?)</h3>", article, re.I | re.S)
            date_text = BLUEventClaim._plain_text(date_match.group(1)) if date_match else "未知日期"
            messages = [
                BLUEventClaim._plain_text(content)
                for _, content in re.findall(
                    r'<([a-z0-9]+)\b[^>]*class=["\'][^"\']*events__prize-message'
                    r'[^"\']*["\'][^>]*>(.*?)</\1>',
                    article,
                    re.I | re.S,
                )
            ]
            messages = [message for message in messages if message]
            claimed = bool(re.search(
                r"events__prize-winnings-list|events__prize-icon--today-claimed",
                article,
                re.I,
            ))
            if claimed:
                status = "已领取"
                rewards = [
                    message for message in messages
                    if message.lower() not in {"expired", "check back later!"}
                ]
            elif re.search(r"events__prize-icon--today(?!-claimed)", article, re.I):
                status = "今日待领取"
                rewards = []
            elif re.search(r"events__prize-icon--past|\bExpired\b", article, re.I):
                status = "已过期未领"
                rewards = []
            elif re.search(r"events__prize-icon--future|Check back later", article, re.I):
                status = "待开放"
                rewards = []
            else:
                status = "状态未知"
                rewards = []
            days.append({
                "date": date_text,
                "status": status,
                "rewards": rewards,
                "message": " / ".join(messages),
            })
        return days

    @staticmethod
    def _reward_totals(days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """汇总已领取日期中的已知及未知奖励类型。"""
        totals: Dict[str, Dict[str, Any]] = {}
        for day in days:
            if day.get("status") != "已领取":
                continue
            for reward in day.get("rewards") or []:
                parsed = BLUEventClaim._parse_reward(reward)
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
                item["display"] = BLUEventClaim._format_bytes(item["value"])
            elif item["kind"] == "count":
                item["display"] = f"× {int(item['value'])}"
            else:
                item["display"] = BLUEventClaim._format_number(item["value"])
        return result

    @staticmethod
    def _parse_reward(reward: str) -> Dict[str, Any]:
        """识别常见奖励；未知奖励按名称动态分组。"""
        text = re.sub(r"\s+", " ", html.unescape(reward or "")).strip()
        number = r"([\d,]+(?:\.\d+)?)"

        match = re.fullmatch(number + r"\s*(?:BON|BP|BONUS(?:\s+POINTS?)?)", text, re.I)
        if match:
            return {"key": "bon", "label": "BON", "kind": "number", "value": BLUEventClaim._number(match.group(1))}

        match = re.fullmatch(number + r"\s*(?:FL\s*)?(?:TOKENS?|FREELEECH\s+TOKENS?)", text, re.I)
        if match:
            return {"key": "fl_tokens", "label": "FL Token", "kind": "number", "value": BLUEventClaim._number(match.group(1))}

        match = re.fullmatch(
            number + r"\s*(KiB|MiB|GiB|TiB|KB|MB|GB|TB)(?:\s+UPLOAD)?",
            text,
            re.I,
        )
        if match:
            unit = match.group(2).lower()
            powers = {"kb": 1, "mb": 2, "gb": 3, "tb": 4, "kib": 1, "mib": 2, "gib": 3, "tib": 4}
            base = 1024 if "i" in unit else 1000
            value = BLUEventClaim._number(match.group(1)) * (base ** powers[unit])
            return {"key": "upload", "label": "上传量", "kind": "bytes", "value": value}

        match = re.fullmatch(number + r"\s+(.+)", text)
        if match:
            label = re.sub(r"\s+", " ", match.group(2)).strip()
            key = "other:" + label.casefold()
            return {"key": key, "label": label, "kind": "number", "value": BLUEventClaim._number(match.group(1))}

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

    @staticmethod
    def _plain_text(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", html.unescape(text)).strip()

    @staticmethod
    def _is_login_page(response: requests.Response) -> bool:
        """识别 Cookie 失效后的登录页或重定向。"""
        path = urlparse(response.url or "").path.rstrip("/")
        return path == "/login" or bool(re.search(
            r'<form\b[^>]*(?:action=["\'][^"\']*/login|id=["\']login)',
            response.text or "",
            re.I,
        ))

    @staticmethod
    def _response_error(response: Optional[requests.Response], action: str) -> Optional[Dict[str, str]]:
        """将空响应和非成功 HTTP 状态转成统一结果。"""
        if response is None:
            return {"status": "失败", "message": f"{action}无响应"}
        if response.status_code >= 400:
            return {"status": "失败", "message": f"{action}失败（HTTP {response.status_code}）"}
        return None

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """返回插件配置表单。"""
        return [{
            "component": "VForm",
            "content": [{
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VSwitch", "props": {
                        "model": "enabled", "label": "启用插件",
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VSwitch", "props": {
                        "model": "onlyonce", "label": "立即运行一次",
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VSwitch", "props": {
                        "model": "notify", "label": "成功或失败时通知",
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VCronField", "props": {
                        "model": "cron", "label": "执行周期", "placeholder": self.DEFAULT_CRON,
                    }}],
                }],
            }, {
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VTextField", "props": {
                        "model": "random_delay",
                        "label": "随机延迟（分钟）",
                        "type": "number",
                        "min": 0,
                        "max": 60,
                        "hint": "Cron 到点后随机延迟 0～N 分钟；0 表示关闭。",
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 9},
                    "content": [{"component": "VTextField", "props": {
                        "model": "event_url",
                        "label": "BLU 活动详情页",
                        "placeholder": self.DEFAULT_EVENT_URL,
                        "hint": "活动编号变化时只需更新此地址；Cookie 自动读取 MoviePilot 的 BLU 站点配置。",
                    }}],
                }],
            }, {
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [{"component": "VTextField", "props": {
                        "model": "cookie",
                        "label": "BLU Cookie（可选）",
                        "type": "password",
                        "placeholder": "留空则读取 MoviePilot 的 BLU 站点 Cookie",
                        "hint": "填写后优先使用此 Cookie；不会写入插件日志或领取历史。",
                    }}],
                }],
            }, {
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": "仅定时任务或立即运行时访问 BLU；打开详情页只读取本地缓存。已领取时请求一次，需要领取时请求两次。随机延迟只影响 Cron 定时任务，不影响立即运行。",
                },
            }],
        }], {
            "enabled": False,
            "onlyonce": False,
            "notify": True,
            "cron": self.DEFAULT_CRON,
            "random_delay": 0,
            "event_url": self.DEFAULT_EVENT_URL,
            "cookie": "",
        }

    def get_page(self) -> List[dict]:
        """只读取本地缓存，展示当前活动统计、逐日状态和执行历史。"""
        event_url = self._normalized_event_url(self._event_url) or self._event_url
        snapshot = (self.get_data("event_snapshots") or {}).get(event_url)
        all_records = list(reversed(self.get_data("claim_logs") or []))
        records = [
            item for item in all_records
            if item.get("event_url") == event_url
            or (not item.get("event_url") and event_url == self.DEFAULT_EVENT_URL)
        ][:10]
        latest_record = records[0] if records else None
        if latest_record:
            latest_status = latest_record.get("status") or "状态未知"
            latest_detail = " · ".join(filter(None, [
                latest_record.get("time"),
                latest_record.get("message"),
                f"奖励：{latest_record.get('reward')}" if latest_record.get("reward") else "",
            ]))
            latest_alert = {
                "component": "VAlert",
                "props": {
                    "type": "error" if latest_status == "失败" else "success",
                    "variant": "tonal",
                    "title": f"最近执行：{latest_status}",
                    "text": latest_detail,
                    "class": "mb-4",
                },
            }
        else:
            latest_alert = {
                "component": "VAlert",
                "props": {
                    "type": "warning",
                    "variant": "tonal",
                    "title": "尚未执行",
                    "text": "勾选“立即运行一次”并保存配置后，任务会在约 3 秒后执行。",
                    "class": "mb-4",
                },
            }

        history_components = [{
            "component": "div",
            "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"},
            "text": "执行历史",
        }, {
            "component": "VRow",
            "content": [{
                "component": "VCol",
                "props": {"cols": 12},
                "content": [{
                    "component": "VDataTable",
                    "props": {
                        "headers": [
                            {"title": "时间", "key": "time"},
                            {"title": "结果", "key": "status"},
                            {"title": "本次奖励", "key": "reward"},
                            {"title": "说明", "key": "message"},
                        ],
                        "items": records,
                        "items-per-page": -1,
                        "hide-default-footer": True,
                        "density": "compact",
                        "hover": True,
                    },
                }],
            }],
        }]
        if not snapshot:
            return [latest_alert, {
                "component": "VAlert",
                "props": {
                    "type": "warning",
                    "variant": "tonal",
                    "title": "暂无每日状态缓存",
                    "text": "最近一次读取尚未产生有效的活动页面；具体结果请查看上方提示和下方执行历史。",
                    "class": "mb-4",
                },
            }, *history_components]

        summary = [
            ("活动总天数", snapshot.get("total_days", 0), "info"),
            ("已领取", snapshot.get("claimed_days", 0), "success"),
            ("已过期未领", snapshot.get("expired_days", 0), "error"),
            ("今日待领取", snapshot.get("claimable_days", 0), "warning"),
            ("待开放", snapshot.get("future_days", 0), "info"),
        ]
        reward_totals = snapshot.get("reward_totals") or []
        status_icons = {
            "已领取": "✅ 已领取",
            "已过期未领": "⛔ 已过期未领",
            "今日待领取": "🎁 今日待领取",
            "待开放": "⏳ 待开放",
            "状态未知": "❔ 状态未知",
        }
        day_items = [{
            "date": day.get("date", "未知日期"),
            "status": status_icons.get(day.get("status"), day.get("status", "状态未知")),
            "detail": " / ".join(day.get("rewards") or []) or day.get("message") or "—",
        } for day in snapshot.get("days") or []]
        day_split = (len(day_items) + 1) // 2
        day_columns = [day_items[:day_split], day_items[day_split:]]
        event_heading = (
            f"{snapshot.get('event_title') or 'BLU Event'}  "
            f"(Start: {self._event_start_date(snapshot)})"
        )

        page = [{
            "component": "VAlert",
            "props": {
                "type": "info",
                "variant": "tonal",
                "title": event_heading,
                "class": "mb-4",
            },
        }, latest_alert, {
            "component": "VRow",
            "content": [{
                "component": "VCol",
                "props": {"cols": 12, "sm": 6, "md": 2},
                "content": [{
                    "component": "VAlert",
                    "props": {
                        "type": color,
                        "variant": "tonal",
                        "title": title,
                        "text": str(value),
                    },
                }],
            } for title, value, color in summary],
        }, {
            "component": "div",
            "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"},
            "text": "奖励总计",
        }]

        if reward_totals:
            page.append({
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12, "sm": 6, "md": 3},
                    "content": [{
                        "component": "VAlert",
                        "props": {
                            "type": "success",
                            "variant": "tonal",
                            "title": item.get("label") or "其他奖励",
                            "text": item.get("display") or "—",
                        },
                    }],
                } for item in reward_totals],
            })
        else:
            page.append({
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": "当前活动尚无已领取奖励。",
                },
            })

        page.extend([{
            "component": "div",
            "props": {"class": "text-h6 font-weight-bold mt-4 mb-2"},
            "text": "每日状态",
        }, {
            "component": "VRow",
            "content": [{
                "component": "VCol",
                "props": {"cols": 12, "md": 6},
                "content": [{
                    "component": "VDataTable",
                    "props": {
                        "headers": [
                            {"title": "日期", "key": "date"},
                            {"title": "状态", "key": "status"},
                            {"title": "奖励 / BLU 原始提示", "key": "detail"},
                        ],
                        "items": items,
                        "items-per-page": -1,
                        "hide-default-footer": True,
                        "density": "compact",
                        "hover": True,
                    },
                }],
            } for items in day_columns if items],
        }])
        page.extend(history_components)
        return page

    @staticmethod
    def _event_start_date(snapshot: Dict[str, Any]) -> str:
        """根据首个活动日期和缓存时间补全年份。"""
        days = snapshot.get("days") or []
        first_date = days[0].get("date", "") if days else ""
        match = re.fullmatch(r"([A-Za-z]{3})\s+(\d{1,2})", first_date.strip())
        if not match:
            return "—"

        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month = months.get(match.group(1).lower())
        if not month:
            return "—"

        updated_at = snapshot.get("updated_at") or ""
        try:
            checked = datetime.datetime.strptime(updated_at[:10], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            checked = datetime.date.today()
        try:
            candidates = [
                datetime.date(checked.year + offset, month, int(match.group(2)))
                for offset in (-1, 0, 1)
            ]
        except ValueError:
            return "—"
        start = min(candidates, key=lambda value: abs((value - checked).days))
        return start.strftime("%Y/%m/%d")

    def get_command(self) -> List[Dict[str, Any]]:
        """本插件不注册远程命令。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """本插件不暴露 MoviePilot API。"""
        return []
