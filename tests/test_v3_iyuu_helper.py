import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


app = types.ModuleType('app')
app.__path__ = []
sdk = types.ModuleType('app.sdk')
sdk.__path__ = []
network = types.ModuleType('app.sdk.network')
network.RequestUtils = object
path = pathlib.Path(__file__).parents[1] / 'plugins.v3' / 'iyuuautoseed' / 'iyuu_helper.py'
spec = importlib.util.spec_from_file_location('iyuu_helper_v3_test', path)
module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'app': app, 'app.sdk': sdk, 'app.sdk.network': network}):
    spec.loader.exec_module(module)


class IyuuHelperTest(unittest.TestCase):
    def test_rate_limit_stops_before_reseed_and_cools_down(self):
        helper = module.IyuuHelper('test')
        request = Mock(return_value=(None, '访问频率过快'))
        helper._IyuuHelper__request_iyuu = request
        with patch.object(module.time, 'monotonic', return_value=100):
            self.assertEqual(helper.get_seed_info(['abc']), (None, '访问频率过快'))
            self.assertEqual(helper.get_seed_info(['def']), (None, '访问频率过快'))
        request.assert_called_once_with(url='/reseed/sites/index')

    def test_missing_report_hash_does_not_send_reseed(self):
        helper = module.IyuuHelper('test')
        request = Mock(side_effect=[({'sites': [{'id': 1}]}, ''), ({}, '')])
        helper._IyuuHelper__request_iyuu = request
        result, message = helper.get_seed_info(['abc'])
        self.assertIsNone(result)
        self.assertIn('未返回站点哈希', message)
        self.assertEqual(request.call_count, 2)

    def test_expired_hash_is_refreshed_and_retried(self):
        helper = module.IyuuHelper('test')
        helper._sid_sha1 = 'old'
        helper._sites = {1: {'id': 1}}
        request = Mock(side_effect=[(None, '站点哈希值 require'), ({'sid_sha1': 'new'}, ''), ({'abc': []}, '')])
        helper._IyuuHelper__request_iyuu = request
        self.assertEqual(helper.get_seed_info(['abc']), ({'abc': []}, ''))
        self.assertEqual(request.call_args.kwargs['params']['sid_sha1'], 'new')

    def test_helper_state_is_not_shared(self):
        a = module.IyuuHelper('a')
        b = module.IyuuHelper('b')
        a._sites[1] = {'id': 1}
        self.assertEqual(b._sites, {})


if __name__ == '__main__':
    unittest.main()
