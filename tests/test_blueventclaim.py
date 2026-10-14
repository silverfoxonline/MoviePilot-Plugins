"""Pure parsing tests for the MoviePilot v2 BLU event plugin."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _module(name, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass


_module("pytz", timezone=lambda value: value)
_module("requests", Session=_Dummy, Response=_Dummy)
_module("apscheduler")
_module("apscheduler.schedulers")
_module("apscheduler.schedulers.background", BackgroundScheduler=_Dummy)
_module("apscheduler.triggers")
_module("apscheduler.triggers.cron", CronTrigger=_Dummy)
_module("app")
_module("app.core")
_module("app.core.config", settings=types.SimpleNamespace(TZ="Asia/Shanghai", USER_AGENT="test", PROXY=None))
_module("app.db")
_module("app.db.site_oper", SiteOper=_Dummy)
_module("app.log", logger=_Dummy())
_module("app.plugins", _PluginBase=object)
_module("app.schemas")
_module("app.schemas.types", NotificationType=types.SimpleNamespace(SiteMessage="site"))
_module("app.utils")
_module("app.utils.http", RequestUtils=_Dummy)

PLUGIN_PATH = Path(__file__).parents[1] / "plugins.v2" / "blueventclaim" / "__init__.py"
SPEC = importlib.util.spec_from_file_location("blueventclaim", PLUGIN_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BLUEventClaim = MODULE.BLUEventClaim


class BLUEventClaimParserTest(unittest.TestCase):
    def test_claimed_page_and_reward(self):
        page = """
        <meta name="csrf-token" content="token-value">
        <article class="events__prize"><h3>Oct 14</h3>
          <i class="events__prize-icon--today-claimed"></i>
          <i class="events__prize-message">8924 BON</i>
        </article>
        """
        self.assertTrue(BLUEventClaim._page_state(page)["claimed"])
        self.assertEqual(BLUEventClaim._claimed_reward(page), "8924 BON")
        self.assertEqual(BLUEventClaim._csrf_token(page), "token-value")
        progress = BLUEventClaim._event_progress(page)
        self.assertEqual(progress["total_days"], 1)
        self.assertEqual(progress["claimed_days"], 1)
        self.assertEqual(progress["reward_totals"][0]["display"], "8,924")

    def test_daily_statuses_and_dynamic_reward_totals(self):
        page = """
        <h2 class="panel__heading">Autumn Event</h2>
        <article class="events__prize"><h3>Oct 13</h3>
          <i class="events__prize-icon--past"></i>
          <i class="events__prize-message">Expired</i>
        </article>
        <article class="events__prize"><h3>Oct 14</h3>
          <ul class="events__prize-winnings-list"></ul>
          <i class="events__prize-message">8924 BON</i>
          <i class="events__prize-message">2 FL Tokens</i>
          <i class="events__prize-message">100 GiB Upload</i>
          <i class="events__prize-message">2 Mystery Boxes</i>
        </article>
        <article class="events__prize"><h3>Oct 15</h3>
          <i class="events__prize-icon--today"></i>
        </article>
        <article class="events__prize"><h3>Oct 16</h3>
          <i class="events__prize-icon--future"></i>
          <i class="events__prize-message">Check back later!</i>
        </article>
        """
        progress = BLUEventClaim._event_progress(page)
        self.assertEqual(progress["event_title"], "Autumn Event")
        self.assertEqual(
            [progress[key] for key in (
                "total_days", "claimed_days", "expired_days", "claimable_days", "future_days",
            )],
            [4, 1, 1, 1, 1],
        )
        self.assertEqual(
            [day["status"] for day in progress["days"]],
            ["已过期未领", "已领取", "今日待领取", "待开放"],
        )
        totals = {item["label"]: item["display"] for item in progress["reward_totals"]}
        self.assertEqual(totals, {
            "BON": "8,924",
            "FL Token": "2",
            "上传量": "100 GiB",
            "Mystery Boxes": "2",
        })

    def test_claim_form_is_preferred(self):
        page = '<form action="/giveaways/4/claims" method="POST"></form>'
        self.assertEqual(
            BLUEventClaim._claim_url(page, "https://blutopia.cc/giveaways/4"),
            "https://blutopia.cc/giveaways/4/claims",
        )

    def test_today_marker_uses_expected_endpoint(self):
        page = '<i class="events__prize-icon--today"></i>'
        self.assertEqual(
            BLUEventClaim._claim_url(page, "https://blutopia.cc/giveaways/4"),
            "https://blutopia.cc/giveaways/4/claims",
        )

    def test_rejects_non_blu_event_urls(self):
        self.assertEqual(BLUEventClaim._normalized_event_url("https://example.com/giveaways/4"), "")
        self.assertEqual(BLUEventClaim._normalized_event_url("http://blutopia.cc/giveaways/4"), "")
        self.assertEqual(
            BLUEventClaim._normalized_event_url("https://blutopia.cc/giveaways/4/claims"), "",
        )

    def test_claim_flow_verifies_the_result_page(self):
        unclaimed = """
        <meta name="csrf-token" content="token-value">
        <form action="/giveaways/4/claims" method="POST"></form>
        <i class="events__prize-icon--today"></i>
        """
        claimed = """
        <article class="events__prize"><h3>Oct 14</h3>
          <i class="events__prize-icon--today-claimed"></i>
          <i class="events__prize-message">8924 BON</i>
        </article>
        """

        class FakeRequest:
            get_calls = 0
            post_calls = 0

            def __init__(self, *args, **kwargs):
                pass

            def get_res(self, **kwargs):
                FakeRequest.get_calls += 1
                return types.SimpleNamespace(status_code=200, url=kwargs["url"], text=unclaimed)

            def post_res(self, **kwargs):
                FakeRequest.post_calls += 1
                self.post_url = kwargs["url"]
                self.post_data = kwargs["data"]
                return types.SimpleNamespace(status_code=200, url=kwargs["url"], text=claimed)

        site = types.SimpleNamespace(cookie="session=test", ua="test", proxy=0)
        MODULE.SiteOper = lambda: types.SimpleNamespace(get_by_domain=lambda domain: site)
        MODULE.RequestUtils = FakeRequest

        plugin = BLUEventClaim()
        plugin._event_url = "https://blutopia.cc/giveaways/4"
        result = plugin._do_claim()
        self.assertEqual(result["status"], "成功")
        self.assertEqual(result["reward"], "8924 BON")
        self.assertEqual(result["total_days"], 1)
        self.assertEqual(result["claimed_days"], 1)
        self.assertEqual(FakeRequest.get_calls, 1)
        self.assertEqual(FakeRequest.post_calls, 1)

    def test_detail_page_reads_only_the_current_event_cache(self):
        class NetworkMustNotBeUsed:
            def __init__(self, *args, **kwargs):
                raise AssertionError("get_page must not create a network client")

        MODULE.RequestUtils = NetworkMustNotBeUsed
        current_url = "https://blutopia.cc/giveaways/4"
        other_url = "https://blutopia.cc/giveaways/99"
        plugin = BLUEventClaim()
        plugin._event_url = current_url
        stored = {
            "event_snapshots": {
                current_url: {
                    "event_title": "Current Event",
                    "updated_at": "2026-10-14 09:05:00",
                    "total_days": 1,
                    "claimed_days": 1,
                    "expired_days": 0,
                    "claimable_days": 0,
                    "future_days": 0,
                    "reward_totals": [{"label": "BON", "display": "8,924"}],
                    "days": [{
                        "date": "Oct 14", "status": "已领取",
                        "rewards": ["8924 BON"], "message": "8924 BON",
                    }],
                },
                other_url: {"event_title": "Other Event"},
            },
            "claim_logs": [{
                "event_url": current_url,
                "time": "2026-10-14 09:05:00",
                "status": "成功",
                "reward": "8924 BON",
                "message": "领取成功",
            }],
        }
        plugin.get_data = lambda key: stored.get(key)

        rendered = str(plugin.get_page())
        self.assertIn("Current Event", rendered)
        self.assertIn("8,924", rendered)
        self.assertNotIn("Other Event", rendered)


if __name__ == "__main__":
    unittest.main()
