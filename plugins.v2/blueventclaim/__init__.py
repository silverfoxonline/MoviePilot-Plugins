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
    plugin_version = "1.0.0"
    plugin_author = "silverfoxonline"
    author_url = "https://github.com/silverfoxonline/MoviePilot-Plugins"
    plugin_config_prefix = "blueventclaim_"
    plugin_order = 12
    auth_level = 1

    DEFAULT_EVENT_URL = "https://blutopia.cc/giveaways/4"
    DEFAULT_CRON = "5 9 * * *"
    REQUEST_TIMEOUT = 30
    MAX_HISTORY = 100

    _enabled = False
    _onlyonce = False
    _notify = True
    _cron = DEFAULT_CRON
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
            return [{
                "id": "BLUEventClaim",
                "name": "BLU活动奖励自动领取",
                "trigger": CronTrigger.from_crontab(self._cron),
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
            "status": result["status"],
            "reward": result.get("reward", ""),
            "message": result.get("message", ""),
        }
        history = self.get_data("claim_logs") or []
        self.save_data("claim_logs", (history + [record])[-self.MAX_HISTORY:])

        log_message = f"[BLUEventClaim] {record['status']}: {record['message']}"
        if record["status"] == "失败":
            logger.error(log_message)
        else:
            logger.info(log_message)

        if self._notify and record["status"] in ("成功", "失败"):
            reward_text = f"\n奖励：{record['reward']}" if record["reward"] else ""
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"【BLU活动奖励】{record['status']}",
                text=f"{record['message']}{reward_text}",
            )

    def _do_claim(self) -> Dict[str, str]:
        """读取活动页、提交领取请求，并再次读取页面验证结果。"""
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
        if page_state["claimed"]:
            reward = self._claimed_reward(page.text)
            return {
                "status": "已领取",
                "reward": reward,
                "message": "今天的活动奖励已经领取，无需重复提交",
            }

        csrf_token = self._csrf_token(page.text)
        if not csrf_token:
            return {"status": "失败", "message": "活动页未找到 CSRF token"}

        claim_url = self._claim_url(page.text, event_url)
        if not claim_url:
            detail = "今天尚未开放领取" if page_state["future"] else "活动页未找到领取表单"
            return {"status": "失败", "message": detail}

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
            return error
        if self._is_login_page(response):
            return {"status": "失败", "message": "领取时登录失效，请更新 BLU Cookie"}

        verify_page = request.get_res(url=event_url)
        error = self._response_error(verify_page, "验证领取结果")
        if error:
            return error
        if not self._page_state(verify_page.text)["claimed"]:
            return {"status": "失败", "message": "领取请求已提交，但页面未显示今天已领取"}

        reward = self._claimed_reward(verify_page.text)
        return {
            "status": "成功",
            "reward": reward,
            "message": "今天的 BLU 活动奖励领取成功",
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
                    "props": {"cols": 12},
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
                    "text": "插件先读取活动页和 CSRF token，再调用领取接口，最后重新读取页面验证结果。默认每天 09:05 执行。",
                },
            }],
        }], {
            "enabled": False,
            "onlyonce": False,
            "notify": True,
            "cron": self.DEFAULT_CRON,
            "event_url": self.DEFAULT_EVENT_URL,
            "cookie": "",
        }

    def get_page(self) -> List[dict]:
        """展示领取统计和最近记录。"""
        records = list(reversed(self.get_data("claim_logs") or []))
        summary = [
            ("总执行", len(records), "info"),
            ("领取成功", sum(item.get("status") == "成功" for item in records), "success"),
            ("已领取跳过", sum(item.get("status") == "已领取" for item in records), "warning"),
            ("失败", sum(item.get("status") == "失败" for item in records), "error"),
        ]
        return [{
            "component": "VRow",
            "content": [{
                "component": "VCol",
                "props": {"cols": 12, "sm": 6, "md": 3},
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
            "component": "VRow",
            "content": [{
                "component": "VCol",
                "props": {"cols": 12},
                "content": [{
                    "component": "VDataTableVirtual",
                    "props": {
                        "headers": [
                            {"title": "时间", "key": "time"},
                            {"title": "结果", "key": "status"},
                            {"title": "奖励", "key": "reward"},
                            {"title": "说明", "key": "message"},
                        ],
                        "items": records,
                        "height": "30rem",
                        "density": "compact",
                        "fixed-header": True,
                        "hover": True,
                    },
                }],
            }],
        }]

    def get_command(self) -> List[Dict[str, Any]]:
        """本插件不注册远程命令。"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """本插件不暴露 MoviePilot API。"""
        return []
