import datetime
import html
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.site_oper import SiteOper
from app.helper.sites import SitesHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType
from app.utils.http import RequestUtils
from app.utils.site import SiteUtils
from app.utils.string import StringUtils


class DStudioSignIn(_PluginBase):
    plugin_name = "DStudio签到"
    plugin_desc = "自动完成 DStudio 每日签到"
    plugin_icon = "signin.png"
    plugin_version = "1.2.0"
    plugin_author = "silverfoxonline"
    author_url = "https://github.com/silverfoxonline/MoviePilot-Plugins"
    plugin_config_prefix = "dstudiosignin_"
    plugin_order = 4
    auth_level = 1

    _enabled = False
    _onlyonce = False
    _notify = True
    _cron = "10 8 * * *"
    _scheduler: Optional[BackgroundScheduler] = None
    _run_lock = threading.Lock()

    def init_plugin(self, config: dict = None):
        self.stop_service()

        if config:
            self._enabled = config.get("enabled", False)
            self._onlyonce = config.get("onlyonce", False)
            self._notify = config.get("notify", True)
            self._cron = config.get("cron") or "10 8 * * *"

        if self._onlyonce:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(
                func=self.sign_in,
                trigger="date",
                run_date=datetime.datetime.now(tz=pytz.timezone(settings.TZ))
                + datetime.timedelta(seconds=3),
                name="DStudio签到立即运行",
            )
            self._scheduler.start()
            self._onlyonce = False
            self.__update_config()

    def get_state(self) -> bool:
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        if not self._enabled or not self._cron:
            return []
        try:
            return [{
                "id": "DStudioSignIn",
                "name": "DStudio每日签到",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.sign_in,
                "kwargs": {},
            }]
        except Exception as err:
            logger.error(f"[DStudioSignIn] 定时配置错误: {err}")
            return []

    def stop_service(self):
        if self._scheduler:
            self._scheduler.remove_all_jobs()
            if self._scheduler.running:
                self._scheduler.shutdown()
            self._scheduler = None

    def sign_in(self):
        if not self._run_lock.acquire(blocking=False):
            logger.warning("[DStudioSignIn] 签到任务正在运行，本次跳过")
            return

        started_at = datetime.datetime.now()
        try:
            site = self.__find_site()
            if not site:
                self.__finish(False, "未找到 DStudio 站点配置", "请先在站点管理中添加 dstudio.me")
                return

            site_name = site.get("name") or "DStudio"
            site_url = site.get("url") or ""
            site_cookie = site.get("cookie")
            if not site_url or not site_cookie:
                self.__finish(False, "站点配置不完整", "请检查 DStudio 的地址和 Cookie")
                return

            sign_url = "https://dstudio.me/attendance.php"
            logger.info(f"[DStudioSignIn] 开始签到: {site_name} - {sign_url}")
            request = RequestUtils(
                cookies=site_cookie,
                ua=site.get("ua"),
                proxies=settings.PROXY if site.get("proxy") else None,
                timeout=site.get("timeout") or 60,
            )
            response = request.get_res(url=sign_url)

            if response is None:
                self.__record_site_result(site_url, started_at, False)
                self.__finish(False, "签到失败", "无法打开 DStudio 签到页")
                return
            if response.status_code != 200:
                self.__record_site_result(site_url, started_at, False)
                self.__finish(False, "签到失败", f"签到页返回 HTTP {response.status_code}")
                return

            page_source = response.text or ""
            if not SiteUtils.is_logged_in(page_source):
                self.__record_site_result(site_url, started_at, False)
                self.__finish(False, "Cookie已失效", "DStudio 返回了未登录页面")
                return

            success, status, message = self._parse_result(page_source)
            if not success and self._has_signin_form(page_source):
                logger.info("[DStudioSignIn] 检测到待签到表单，正在提交")
                response = request.post_res(
                    url=sign_url,
                    data={},
                    headers={"Referer": sign_url},
                )
                if response is None:
                    self.__record_site_result(site_url, started_at, False)
                    self.__finish(False, "签到失败", "无法提交 DStudio 签到表单")
                    return
                if response.status_code != 200:
                    self.__record_site_result(site_url, started_at, False)
                    self.__finish(False, "签到失败", f"签到请求返回 HTTP {response.status_code}")
                    return

                page_source = response.text or ""
                if not SiteUtils.is_logged_in(page_source):
                    self.__record_site_result(site_url, started_at, False)
                    self.__finish(False, "Cookie已失效", "DStudio 签到请求返回了未登录页面")
                    return
                success, status, message = self._parse_result(page_source)

            stats = self._parse_stats(page_source)
            self.__record_site_result(site_url, started_at, success)
            self.__finish(success, status, message, stats)
        except Exception as err:
            logger.exception(f"[DStudioSignIn] 签到异常: {err}")
            self.__finish(False, "签到异常", str(err))
        finally:
            self._run_lock.release()

    def __find_site(self) -> Optional[dict]:
        for site in SitesHelper().get_indexers():
            if site.get("public"):
                continue
            domain = StringUtils.get_url_domain(site.get("url") or "")
            if domain == "dstudio.me" or domain.endswith(".dstudio.me"):
                return site
        return None

    @staticmethod
    def _parse_result(page_source: str) -> Tuple[bool, str, str]:
        text = DStudioSignIn._extract_text(page_source)
        detail_match = re.search(
            r"这是您的第\s*\d+\s*次签到，已连续签到\s*\d+\s*天，"
            r"本次签到获得\s*\d+\s*个魔力值[。.]?",
            text,
        )
        detail = detail_match.group(0) if detail_match else ""

        rank_match = re.search(r"今日签到排名[：:]\s*\d+\s*/\s*\d+", text)
        if rank_match:
            detail = f"{detail} {rank_match.group(0)}".strip()

        if re.search(r"今日.{0,16}(?:已签到|签到已完成)", text):
            return True, "今日已签到", detail or "DStudio 今日签到已完成"
        if "签到成功" in text or detail_match:
            return True, "签到成功", detail or "DStudio 签到成功"

        failure_match = re.search(r"(?:签到失败|签到错误|发生错误)[^。.!！]{0,100}", text)
        if failure_match:
            return False, "签到失败", failure_match.group(0)
        return False, "结果未知", "已登录，但签到页未返回可识别的成功状态"

    @staticmethod
    def _has_signin_form(page_source: str) -> bool:
        for form_tag in re.findall(r"<form\b[^>]*>", page_source, flags=re.I):
            is_post = re.search(r"\bmethod\s*=\s*(['\"]?)post\1", form_tag, flags=re.I)
            targets_attendance = re.search(
                r"\baction\s*=\s*(['\"]?)(?:https://dstudio\.me/|\./)?attendance\.php"
                r"(?:\?[^'\"\s>]*)?\1",
                form_tag,
                flags=re.I,
            )
            if is_post and targets_attendance:
                return True
        return False

    @staticmethod
    def _extract_text(page_source: str) -> str:
        source = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", page_source, flags=re.I | re.S)
        source = re.sub(r"<[^>]+>", " ", source)
        return re.sub(r"\s+", " ", html.unescape(source)).strip()

    @staticmethod
    def _parse_stats(page_source: str) -> Dict[str, Any]:
        text = DStudioSignIn._extract_text(page_source)
        patterns = {
            "sign_count": r"第\s*(\d+)\s*次签到",
            "streak_days": r"连续签到\s*(\d+)\s*天",
            "reward": r"本次签到获得\s*(\d+)\s*个魔力值",
        }
        stats = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            stats[key] = int(match.group(1)) if match else None

        rank_match = re.search(r"今日签到排名[：:]\s*(\d+)\s*/\s*(\d+)", text)
        stats["rank"] = f"{rank_match.group(1)} / {rank_match.group(2)}" if rank_match else None
        return stats

    def __record_site_result(self, site_url: str, started_at: datetime.datetime, success: bool):
        domain = StringUtils.get_url_domain(site_url)
        if not domain:
            return
        seconds = max(0, int((datetime.datetime.now() - started_at).total_seconds()))
        if success:
            SiteOper().success(domain=domain, seconds=seconds)
        else:
            SiteOper().fail(domain)

    def __finish(self, success: bool, status: str, message: str, stats: Optional[dict] = None):
        record = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "message": message,
            **(stats or {}),
        }
        history = self.get_data("signin_history") or []
        history.append(record)
        self.save_data("signin_history", history[-100:])

        log_message = f"[DStudioSignIn] {status}: {message}"
        if success:
            logger.info(log_message)
        else:
            logger.error(log_message)

        if self._notify:
            self.post_message(
                title=f"【DStudio签到】{status}",
                mtype=NotificationType.SiteMessage,
                text=message,
            )

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "onlyonce": self._onlyonce,
            "notify": self._notify,
            "cron": self._cron,
        })

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
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
                        "model": "notify", "label": "发送通知",
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VCronField", "props": {
                        "model": "cron", "label": "执行周期", "placeholder": "10 8 * * *",
                    }}],
                }],
            }, {
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [{"component": "VAlert", "props": {
                        "type": "info",
                        "variant": "tonal",
                        "text": "使用站点管理中 dstudio.me 的 Cookie、UA 和代理设置；请先确保该站点已添加且 Cookie 有效。",
                    }}],
                }],
            }],
        }], {
            "enabled": False,
            "onlyonce": False,
            "notify": True,
            "cron": "10 8 * * *",
        }

    def get_page(self) -> List[dict]:
        records = list(reversed(self.get_data("signin_history") or []))
        if not records:
            return [{
                "component": "VAlert",
                "props": {
                    "type": "info",
                    "variant": "tonal",
                    "text": "暂无签到记录，请先运行一次签到。",
                },
            }]

        headers = ["时间", "状态", "本次魔力", "连续签到", "累计签到", "今日排名"]
        return [{
            "component": "VCard",
            "props": {
                "variant": "outlined",
                "class": "pa-4",
                "style": "border-radius: 14px;",
            },
            "content": [{
                "component": "div",
                "props": {
                    "class": "text-h6 font-weight-bold mb-4",
                    "style": "letter-spacing: 0.2px;",
                },
                "text": "📊 DStudio 签到历史",
            }, {
                "component": "VTable",
                "props": {
                    "density": "compact",
                    "hover": True,
                    "fixed-header": True,
                    "height": "32rem",
                },
                "content": [{
                    "component": "thead",
                    "content": [{
                        "component": "tr",
                        "content": [{
                            "component": "th",
                            "props": {"class": "text-start"},
                            "text": title,
                        } for title in headers],
                    }],
                }, {
                    "component": "tbody",
                    "content": [self.__build_history_row(record) for record in records],
                }],
            }],
        }]

    @staticmethod
    def __build_history_row(record: dict) -> dict:
        status = record.get("status") or "未知"
        success = status in {"签到成功", "今日已签到"}
        status_color = "success" if success else "warning" if status == "结果未知" else "error"

        def metric(key: str, icon: str) -> str:
            value = record.get(key)
            return f"{value} {icon}" if value is not None else "—"

        cells = [{
            "component": "td",
            "props": {"class": "text-medium-emphasis"},
            "text": record.get("time") or "—",
        }, {
            "component": "td",
            "content": [{
                "component": "VChip",
                "props": {
                    "size": "small",
                    "variant": "outlined",
                    "color": status_color,
                    "title": record.get("message") or status,
                },
                "text": status,
            }],
        }]
        cells.extend({
            "component": "td",
            "props": {"class": "text-medium-emphasis"},
            "text": value,
        } for value in [
            metric("reward", "✨"),
            metric("streak_days", "🔥"),
            metric("sign_count", "📅"),
            metric("rank", "🏆"),
        ])
        return {
            "component": "tr",
            "content": cells,
        }

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []
