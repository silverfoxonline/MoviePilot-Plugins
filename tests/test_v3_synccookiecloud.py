import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


def module(name, **attrs):
    result = types.ModuleType(name)
    result.__dict__.update(attrs)
    return result


stubs = {
    'pytz': module('pytz'),
    'apscheduler': module('apscheduler'),
    'apscheduler.schedulers': module('apscheduler.schedulers'),
    'apscheduler.schedulers.background': module('apscheduler.schedulers.background', BackgroundScheduler=object),
    'apscheduler.triggers': module('apscheduler.triggers'),
    'apscheduler.triggers.cron': module('apscheduler.triggers.cron', CronTrigger=object),
    'app': module('app'),
    'app.db': module('app.db'),
    'app.db.oper': module('app.db.oper'),
    'app.db.oper.site': module('app.db.oper.site', SiteOper=object),
    'app.sdk': module('app.sdk'),
    'app.sdk.config': module('app.sdk.config', settings=Mock()),
    'app.sdk.logging': module('app.sdk.logging', logger=Mock()),
    'app.sdk.plugin': module('app.sdk.plugin', _PluginBase=object),
    'app.sdk.utilities': module('app.sdk.utilities', CryptoJsUtils=object),
}
path = pathlib.Path(__file__).parents[1] / 'plugins.v3' / 'synccookiecloud' / '__init__.py'
spec = importlib.util.spec_from_file_location('synccookiecloud_v3_test', path)
plugin_module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, stubs):
    spec.loader.exec_module(plugin_module)


class SyncCookieCloudTest(unittest.TestCase):
    def test_cookie_values_keep_equals_and_empty_cookies_are_skipped(self):
        plugin = object.__new__(plugin_module.SyncCookieCloud)
        plugin._get_crypt_key = Mock(return_value=b'fixture')
        sites = Mock()
        sites.list_order_by_pri.return_value = [
            types.SimpleNamespace(url='https://example.org', cookie='session=a=b; mode=test'),
            types.SimpleNamespace(url='https://api.example.org', cookie=''),
        ]
        crypto = Mock()
        crypto.encrypt.return_value = b'encrypted'
        with tempfile.TemporaryDirectory() as tmp:
            settings = types.SimpleNamespace(COOKIECLOUD_ENABLE_LOCAL=True, COOKIE_PATH=pathlib.Path(tmp), COOKIECLOUD_KEY='fixture')
            with patch.object(plugin_module, 'settings', settings), \
                    patch.object(plugin_module, 'SiteOper', return_value=sites), \
                    patch.object(plugin_module, 'CryptoJsUtils', crypto):
                plugin._SyncCookieCloud__sync_to_cookiecloud()
            payload = json.loads(crypto.encrypt.call_args.args[0])['cookie_data']
            self.assertEqual(payload['example.org'][0]['value'], 'a=b')
            self.assertNotIn('api.example.org', payload)
            self.assertTrue((pathlib.Path(tmp) / 'fixture.json').exists())


if __name__ == '__main__':
    unittest.main()
