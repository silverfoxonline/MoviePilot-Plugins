"""Offline ATH event parsing, notification and claim safety tests."""

import datetime
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from test_seedpooleventclaim import STUBS

PATH = Path(__file__).parents[1] / "plugins.v2/aithereventclaim/__init__.py"
SPEC = importlib.util.spec_from_file_location("aithereventclaim", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, STUBS):
    SPEC.loader.exec_module(MODULE)
Plugin = MODULE.AitherEventClaim
URL = "https://aither.cc/events/5"

INDEX = """<main class="page__event--index"><section>
<a href="https://aither.cc/events/raffle">Raffle</a>
<a href="https://aither.cc/events/filmclub">Film Club</a>
<a href="https://aither.cc/events/5"><div>Halloween 2026</div></a>
<a href="https://evil.test/events/6">Foreign</a>
</section></main>"""

DETAIL = """<html><head><meta name="csrf-token" content="fixture-token"></head>
<main class="page__event--show"><section><h2 class="panel__heading">Halloween 2026</h2>
<article class="events__prize"><h3>Oct 27</h3>
<i class="events__prize-icon--past"></i><i class="events__prize-message">Expired</i></article>
<article class="events__prize"><h3>Oct 28</h3>
<i class="events__prize-icon--today-claimed"></i><ul class="events__prize-winnings-list">
<li><i class="events__prize-message">3302 BON</i></li></ul></article>
<article class="events__prize"><h3>Oct 29</h3>
<i class="events__prize-icon--future"></i><i class="events__prize-message">Check back later!</i></article>
</section></main><footer><p><strong>Date:</strong><span>2026-10-28 01:38:38</span></p></footer></html>"""


def response(page, url=URL, status=200, location=""):
    return types.SimpleNamespace(text=page, url=url, status_code=status, headers={"Location": location})


class AitherEventClaimTest(unittest.TestCase):
    def setUp(self):
        self.plugin = Plugin()
        self.plugin._scheduler = None
        self.plugin._stopping = False
        self.plugin._notify = True
        self.data = {}
        self.config = {}
        self.plugin.get_data = self.data.get
        self.plugin.get_config = lambda: dict(self.config)
        self.plugin.save_data = lambda key, value: self.data.update({key: value})
        self.plugin.update_config = Mock(side_effect=lambda config: self.config.update(config))
        self.plugin.post_message = Mock()

    def test_numeric_event_discovery_and_bad_index(self):
        self.assertEqual(Plugin._events(INDEX), [{"event_url": URL, "event_title": "Halloween 2026"}])
        multiple = INDEX.replace("</section>", '<a href="/events/6">第二个活动</a><a href="/events/5">重复</a></section>')
        self.assertEqual([item["event_url"] for item in Plugin._events(multiple)], [URL, "https://aither.cc/events/6"])
        with self.assertRaises(ValueError):
            Plugin._events("<html><form><input type='password'></form></html>")
        for url in ("http://aither.cc/events/5", "https://evil.test/events/5",
                    "https://aither.cc:444/events/5", "https://aither.cc/events/5?x=1"):
            self.assertEqual(Plugin._safe_url(url), "")

    def test_claimed_detail_and_site_date(self):
        result = Plugin._event(DETAIL, URL)
        self.assertEqual(result["event_title"], "Halloween 2026")
        self.assertEqual(result["site_date"], "2026-10-28")
        self.assertEqual([d["status"] for d in result["days"]], ["已过期未领", "已领取", "待开放"])
        self.assertEqual(result["days"][1]["rewards"], ["3302 BON"])
        self.assertIsNone(result["claim"])
        self.assertEqual(self.plugin._activity_status(result)[1], "进行中")
        session = Mock()
        session.request.return_value = response(DETAIL)
        checked = self.plugin._claim_event(session, {"event_url": URL})
        self.assertEqual((checked["status"], checked["reward"]), ("已领取", "3302 BON"))
        self.assertEqual(session.request.call_count, 1)

    def test_pending_uses_site_date_not_mp_date(self):
        page = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--future")
        page = page.replace('class="events__prize-winnings-list"', 'class="other"')
        session = Mock()
        session.request.return_value = response(page)
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 29)):
            self.assertEqual(self.plugin._claim_event(session, {"event_url": URL})["status"], "待开放")
        self.assertEqual(session.request.call_count, 1)

    def test_claim_form_post_and_original_day_verification(self):
        form = '<form method="POST" action="/events/5/claims"><input type="hidden" name="_token" value="fixture-token"></form>'
        before = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--today-unclaimed")
        start, end = before.index('<ul class="events__prize-winnings-list">'), before.index('</ul>') + len('</ul>')
        before = before[:start] + form + before[end:]
        session = Mock()
        session.request.side_effect = [response(before), response("<html>ok</html>"), response(DETAIL)]
        result = self.plugin._claim_event(session, {"event_url": URL})
        self.assertEqual(result["status"], "成功")
        self.assertEqual(result["reward"], "3302 BON")
        self.assertEqual([c.args[0] for c in session.request.call_args_list], ["GET", "POST", "GET"])
        self.assertEqual(session.request.call_args_list[1].args[1], URL + "/claims")

    def test_unconfirmed_form_never_posts(self):
        page = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--today-unclaimed")
        page = page.replace('class="events__prize-winnings-list"', 'class="other"')
        session = Mock()
        session.request.return_value = response(page)
        self.assertEqual(self.plugin._claim_event(session, {"event_url": URL})["status"], "失败")
        self.assertEqual(session.request.call_count, 1)

    def test_retry_never_claims_after_site_date_changes(self):
        form = '<form method="POST" action="/events/5/claims"><input type="hidden" name="_token" value="fixture-token"></form>'
        page = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--today-unclaimed")
        start, end = page.index('<ul class="events__prize-winnings-list">'), page.index('</ul>') + len('</ul>')
        page = page[:start] + form + page[end:]
        session = Mock()
        session.request.return_value = response(page)
        result = self.plugin._claim_event(session, {"event_url": URL}, "2026-10-27")
        self.assertEqual(result["status"], "已跨日跳过")
        self.assertEqual(session.request.call_count, 1)

    def test_missing_site_date_does_not_guess_pending_from_mp_timezone(self):
        page = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--future")
        page = page.replace('class="events__prize-winnings-list"', 'class="other"')
        page = page.replace("2026-10-28 01:38:38", "")
        session = Mock()
        session.request.return_value = response(page)
        result = self.plugin._claim_event(session, {"event_url": URL})
        self.assertEqual(result["status"], "失败")
        self.assertIn("站点日期", result["message"])
        self.assertEqual(session.request.call_count, 1)

    def test_unverified_original_day_is_failure(self):
        form = '<form method="POST" action="/events/5/claims"><input type="hidden" name="_token" value="fixture-token"></form>'
        before = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--today-unclaimed")
        start, end = before.index('<ul class="events__prize-winnings-list">'), before.index('</ul>') + len('</ul>')
        before = before[:start] + form + before[end:]
        session = Mock()
        session.request.side_effect = [response(before), response("<html>ok</html>"), response(before)]
        result = self.plugin._claim_event(session, {"event_url": URL})
        self.assertEqual(result["status"], "失败")
        self.assertIn("原奖励卡片", result["message"])

    def test_bad_claim_endpoint_is_not_submitted(self):
        page = DETAIL.replace("events__prize-icon--today-claimed", "events__prize-icon--today-unclaimed")
        page = page.replace('<ul class="events__prize-winnings-list">', '<form method="POST" action="https://evil.test/events/5/claims">')
        page = page.replace('</ul>', '</form>')
        session = Mock()
        session.request.return_value = response(page)
        self.assertEqual(self.plugin._claim_event(session, {"event_url": URL})["status"], "失败")
        self.assertEqual(session.request.call_count, 1)

    def test_manual_notification_and_cache_are_isolated(self):
        parsed = Plugin._event(DETAIL, URL)
        parsed.pop("claim")
        result = {"event_url": URL, "status": "无可领奖励", "message": "已领取", **parsed}
        self.plugin.init_plugin({"onlyonce": True, "notify": True})
        self.config["onlyonce"] = True
        with patch.object(self.plugin, "_run", return_value=[result]):
            self.plugin.claim_rewards(onlyonce=True)
        text = self.plugin.post_message.call_args.kwargs["text"]
        self.assertIn("获取到 1 个活动", text)
        self.assertIn("已领取 1/过期 1/待开放 1", text)
        self.assertNotIn("fixture-token", json.dumps(self.data, ensure_ascii=False))
        page = json.dumps(self.plugin.get_page(), ensure_ascii=False)
        self.assertIn("Halloween 2026", page)
        self.assertIn("3302 BON", page)

    def test_manifest_and_low_frequency_default(self):
        manifest = json.loads((PATH.parents[2] / "package.v2.json").read_text(encoding="utf-8"))["AitherEventClaim"]
        self.assertEqual(manifest["version"], Plugin.plugin_version)
        self.assertEqual(Plugin.DEFAULT_CRON, "5 9 * * *")


if __name__ == "__main__":
    unittest.main()
