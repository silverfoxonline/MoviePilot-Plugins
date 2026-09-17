import datetime
import threading
from typing import Any, Dict, List, Optional, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.helper.downloader import DownloaderHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import ServiceInfo


class DownloadTaskTagCustom(_PluginBase):
    plugin_name = "下载任务标签自定义"
    plugin_desc = "根据 Tracker 域名为下载任务添加自定义标签"
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/icons/Youtube-dl_B.png"
    plugin_version = "1.0.0"
    plugin_author = "silverfoxonline"
    author_url = "https://github.com/silverfoxonline/MoviePilot-Plugins"
    plugin_config_prefix = "downloadtasktagcustom_"
    plugin_order = 3
    auth_level = 1

    _enabled = False
    _onlyonce = False
    _cron = "*/10 * * * *"
    _downloaders: List[str] = []
    _tracker_mappings_str = ""
    _tracker_mappings: Dict[str, str] = {}
    _scheduler: Optional[BackgroundScheduler] = None
    _event = threading.Event()

    DEFAULT_MAPPINGS = "\n".join([
        "blutopia.cc -> BLU",
        "aither.cc -> AITHER",
        "tracker.beyond-hd.me -> BHD",
    ])

    def init_plugin(self, config: dict = None):
        self.stop_service()
        self._event.clear()

        if config:
            self._enabled = config.get("enabled", False)
            self._onlyonce = config.get("onlyonce", False)
            self._cron = config.get("cron") or "*/10 * * * *"
            self._downloaders = config.get("downloaders") or []
            self._tracker_mappings_str = config.get("tracker_mappings_str") or self.DEFAULT_MAPPINGS
        else:
            self._tracker_mappings_str = self.DEFAULT_MAPPINGS

        self._tracker_mappings = self._parse_tracker_mappings(self._tracker_mappings_str)

        if self._onlyonce:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            self._scheduler.add_job(
                func=self._scan_downloaders,
                trigger="date",
                run_date=datetime.datetime.now(tz=pytz.timezone(settings.TZ)) + datetime.timedelta(seconds=3),
                name="下载任务自定义标签立即运行",
            )
            self._scheduler.start()
            self._onlyonce = False
            self.update_config({
                "enabled": self._enabled,
                "onlyonce": False,
                "cron": self._cron,
                "downloaders": self._downloaders,
                "tracker_mappings_str": self._tracker_mappings_str,
            })

    def get_state(self) -> bool:
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        if not self._enabled or not self._cron:
            return []
        try:
            return [{
                "id": "DownloadTaskTagCustom",
                "name": "下载任务标签自定义",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self._scan_downloaders,
                "kwargs": {},
            }]
        except Exception as err:
            logger.error(f"[DownloadTaskTagCustom] 定时配置错误: {err}")
            return []

    def stop_service(self):
        self._event.set()
        if self._scheduler:
            self._scheduler.remove_all_jobs()
            if self._scheduler.running:
                self._scheduler.shutdown()
            self._scheduler = None

    @property
    def service_infos(self) -> Optional[Dict[str, ServiceInfo]]:
        if not self._downloaders:
            logger.warning("[DownloadTaskTagCustom] 尚未选择下载器")
            return None
        services = DownloaderHelper().get_services(name_filters=self._downloaders)
        active_services = {
            name: service for name, service in services.items()
            if service.instance and not service.instance.is_inactive()
        }
        return active_services or None

    def _scan_downloaders(self):
        services = self.service_infos
        if not services or not self._tracker_mappings:
            return

        scanned = 0
        tagged = 0
        logger.info("[DownloadTaskTagCustom] 开始扫描下载任务")
        for service in services.values():
            if self._event.is_set():
                return
            torrents, error = service.instance.get_torrents()
            if error or not torrents:
                continue
            for torrent in torrents:
                if self._event.is_set():
                    return
                scanned += 1
                labels = self._matched_labels(self._get_trackers(torrent, service.type))
                if not labels:
                    continue
                current_labels = self._get_labels(torrent, service.type)
                new_labels = sorted(set(labels) - set(current_labels))
                if not new_labels:
                    continue
                torrent_hash = self._get_hash(torrent, service.type)
                if not torrent_hash:
                    continue
                self._add_labels(service, torrent_hash, torrent, current_labels, new_labels)
                tagged += 1
        logger.info(f"[DownloadTaskTagCustom] 扫描完成: {scanned} 个任务，新增标签 {tagged} 个任务")

    def _matched_labels(self, trackers: List[str]) -> List[str]:
        labels = []
        for tracker in trackers:
            tracker_lower = tracker.lower()
            for tracker_pattern, label in self._tracker_mappings.items():
                if tracker_pattern.lower() in tracker_lower:
                    labels.append(label)
        return list(dict.fromkeys(labels))

    @staticmethod
    def _parse_tracker_mappings(mapping_str: str) -> Dict[str, str]:
        mappings = {}
        for raw_line in (mapping_str or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "->" not in line:
                continue
            tracker_pattern, label = (part.strip() for part in line.split("->", 1))
            if tracker_pattern and label:
                mappings[tracker_pattern] = label
        return mappings

    @staticmethod
    def _get_hash(torrent: Any, downloader_type: str) -> str:
        return torrent.get("hash", "") if downloader_type == "qbittorrent" else torrent.hashString

    @staticmethod
    def _get_trackers(torrent: Any, downloader_type: str) -> List[str]:
        if downloader_type == "qbittorrent":
            return [
                tracker.get("url") for tracker in (torrent.trackers or [])
                if tracker.get("tier", -1) >= 0 and tracker.get("url")
            ]
        return [
            tracker.announce for tracker in (torrent.trackers or [])
            if tracker.tier >= 0 and tracker.announce
        ]

    @staticmethod
    def _get_labels(torrent: Any, downloader_type: str) -> List[str]:
        if downloader_type == "qbittorrent":
            tags = torrent.get("tags", "")
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        return torrent.labels or []

    @staticmethod
    def _add_labels(service: ServiceInfo, torrent_hash: str, torrent: Any,
                    current_labels: List[str], new_labels: List[str]):
        if service.type == "qbittorrent":
            service.instance.set_torrents_tag(ids=torrent_hash, tags=new_labels)
        else:
            labels = sorted(set(current_labels).union(new_labels))
            service.instance.set_torrent_tag(ids=torrent_hash, tags=labels)
        logger.warning(
            f"[DownloadTaskTagCustom] 下载器: {service.name} 种子id: {torrent_hash} "
            f"新增标签: {','.join(new_labels)}"
        )

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [{
            "component": "VForm",
            "content": [{
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VSwitch", "props": {
                        "model": "enabled", "label": "启用插件"
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 3},
                    "content": [{"component": "VSwitch", "props": {
                        "model": "onlyonce", "label": "立即运行一次"
                    }}],
                }, {
                    "component": "VCol",
                    "props": {"cols": 12, "md": 6},
                    "content": [{"component": "VCronField", "props": {
                        "model": "cron", "label": "执行周期", "placeholder": "*/10 * * * *"
                    }}],
                }],
            }, {
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [{"component": "VSelect", "props": {
                        "model": "downloaders", "label": "下载器", "multiple": True,
                        "chips": True, "clearable": True,
                        "items": [{"title": item.name, "value": item.name}
                                  for item in DownloaderHelper().get_configs().values()],
                    }}],
                }],
            }, {
                "component": "VRow",
                "content": [{
                    "component": "VCol",
                    "props": {"cols": 12},
                    "content": [{"component": "VTextarea", "props": {
                        "model": "tracker_mappings_str",
                        "label": "Tracker 与标签映射",
                        "rows": 8,
                        "placeholder": "每行一条：tracker域名 -> 标签名",
                        "hint": "匹配 Tracker 地址后直接添加右侧标签，不依赖 MP2 站点管理。",
                    }}],
                }],
            }],
        }], {
            "enabled": False,
            "onlyonce": False,
            "cron": "*/10 * * * *",
            "downloaders": [],
            "tracker_mappings_str": self.DEFAULT_MAPPINGS,
        }

    def get_page(self) -> List[dict]:
        return []

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []
