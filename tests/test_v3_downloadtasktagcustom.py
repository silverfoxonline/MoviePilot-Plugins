import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, PropertyMock, patch


def module(name, **attrs):
    result = types.ModuleType(name)
    result.__dict__.update(attrs)
    return result


class TorrentMissing(Exception):
    pass


stubs = {
    'pytz': module('pytz'),
    'apscheduler': module('apscheduler'),
    'apscheduler.schedulers': module('apscheduler.schedulers'),
    'apscheduler.schedulers.background': module('apscheduler.schedulers.background', BackgroundScheduler=object),
    'apscheduler.triggers': module('apscheduler.triggers'),
    'apscheduler.triggers.cron': module('apscheduler.triggers.cron', CronTrigger=object),
    'qbittorrentapi': module('qbittorrentapi'),
    'qbittorrentapi.exceptions': module('qbittorrentapi.exceptions', NotFound404Error=TorrentMissing),
    'app': module('app'),
    'app.schemas': module('app.schemas', ServiceInfo=object),
    'app.sdk': module('app.sdk'),
    'app.sdk.config': module('app.sdk.config', settings=Mock()),
    'app.sdk.logging': module('app.sdk.logging', logger=Mock()),
    'app.sdk.plugin': module('app.sdk.plugin', _PluginBase=object),
    'app.sdk.services': module('app.sdk.services', DownloaderHelper=object),
}
path = pathlib.Path(__file__).parents[1] / 'plugins.v3' / 'downloadtasktagcustom' / '__init__.py'
spec = importlib.util.spec_from_file_location('downloadtasktagcustom_v3_test', path)
plugin_module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, stubs):
    spec.loader.exec_module(plugin_module)


class DownloadTaskTagCustomTest(unittest.TestCase):
    def test_deleted_torrent_does_not_abort_remaining_scan(self):
        plugin_class = plugin_module.DownloadTaskTagCustom
        plugin = object.__new__(plugin_class)
        plugin._tracker_mappings = {'example.org': 'EXAMPLE'}
        plugin._event = Mock()
        plugin._event.is_set.return_value = False
        plugin._save_records = Mock()

        class DeletedTorrent:
            @property
            def trackers(self):
                raise TorrentMissing('deleted')

        valid = types.SimpleNamespace(
            trackers=[{'tier': 0, 'url': 'https://example.org/announce'}],
            get=lambda key, default='': {'hash': 'abc', 'name': 'fixture', 'tags': ''}.get(key, default),
        )
        downloader = Mock()
        downloader.get_torrents.return_value = ([DeletedTorrent(), valid], None)
        service = types.SimpleNamespace(name='fixture', type='qbittorrent', instance=downloader)
        with patch.object(plugin_class, 'service_infos', new_callable=PropertyMock, return_value={'fixture': service}), \
                patch.object(plugin_class, '_add_labels', return_value=(True, '')) as add_labels:
            plugin._do_scan()
        add_labels.assert_called_once()
        self.assertEqual(add_labels.call_args.args[1], 'abc')


if __name__ == '__main__':
    unittest.main()
