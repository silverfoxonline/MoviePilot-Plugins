"""Offline parsing and request-flow tests; fixtures contain only redacted main nodes."""

import datetime
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class Scheduler:
    def __init__(self, **kwargs):
        self.running = False
        self.jobs = []

    def add_job(self, **kwargs):
        self.jobs.append(kwargs)

    def start(self):
        self.running = True

    def remove_all_jobs(self):
        self.jobs.clear()

    def shutdown(self, wait=True):
        self.running = False

    def get_job(self, job_id):
        return next((job for job in self.jobs if job.get("id") == job_id), None)

    def remove_job(self, job_id):
        self.jobs = [job for job in self.jobs if job.get("id") != job_id]


class DateTrigger:
    def __init__(self, run_date, timezone=None):
        self.run_date = run_date
        self.timezone = timezone


def module(name, **attrs):
    result = types.ModuleType(name)
    result.__dict__.update(attrs)
    return result


STUBS = {
    "pytz": module("pytz", timezone=lambda _: datetime.timezone.utc),
    "requests": module("requests", Session=Mock()),
    "apscheduler": module("apscheduler"),
    "apscheduler.schedulers": module("apscheduler.schedulers"),
    "apscheduler.schedulers.background": module("apscheduler.schedulers.background", BackgroundScheduler=Scheduler),
    "apscheduler.triggers": module("apscheduler.triggers"),
    "apscheduler.triggers.cron": module("apscheduler.triggers.cron", CronTrigger=Mock()),
    "apscheduler.triggers.date": module("apscheduler.triggers.date", DateTrigger=DateTrigger),
    "app": module("app"), "app.core": module("app.core"), "app.db": module("app.db"),
    "app.core.config": module("app.core.config", settings=types.SimpleNamespace(TZ="Asia/Shanghai", USER_AGENT="fixture-ua", PROXY={"https": "http://proxy.test"})),
    "app.db.site_oper": module("app.db.site_oper", SiteOper=Mock()),
    "app.log": module("app.log", logger=Mock()),
    "app.plugins": module("app.plugins", _PluginBase=object),
    "app.schemas": module("app.schemas"),
    "app.schemas.types": module("app.schemas.types", NotificationType=types.SimpleNamespace(SiteMessage="site")),
}
PATH = Path(__file__).parents[1] / "plugins.v2/seedpooleventclaim/__init__.py"
SPEC = importlib.util.spec_from_file_location("seedpooleventclaim", PATH)
PLUGIN_MODULE = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, STUBS):
    SPEC.loader.exec_module(PLUGIN_MODULE)
Plugin = PLUGIN_MODULE.SeedpoolEventClaim
FIXTURES = Path(__file__).parent / "fixtures/seedpool"


def fixture(name):
    return (FIXTURES / (name + ".html")).read_text(encoding="utf-8")


def response(page="", url=Plugin.EVENTS_URL, status=200, location=""):
    return types.SimpleNamespace(text=page, url=url, status_code=status, headers={"Location": location})


def claimed_page(event_id="7"):
    page = fixture(event_id)
    start = page.index('<form')
    end = page.index('</form>', start) + len('</form>')
    return (page[:start] + '<ul class="events__prize-winnings-list"><li><i class="events__prize-message">100 BON</i></li><li><i class="events__prize-message">2 FL Tokens</i></li></ul>' + page[end:]).replace("events__prize-icon--today-unclaimed", "events__prize-icon--today-claimed")


class SeedpoolEventClaimTest(unittest.TestCase):
    def setUp(self):
        self.plugin = Plugin()
        self.data = {}
        self.config = {}
        self.plugin.get_data = self.data.get
        self.plugin.get_config = lambda: dict(self.config)
        self.plugin.save_data = lambda key, value: self.data.update({key: value})
        self.plugin.update_config = Mock(side_effect=lambda config: self.config.update(config) or True)
        self.plugin.post_message = Mock()

    def test_real_index_discovers_all_events_including_ended_but_active(self):
        events = Plugin._events(fixture("index"))
        self.assertEqual([event["event_title"] for event in events], ["Dailies2", "Spooktober2026", "50PiB.Celebration"])
        self.assertEqual([event["event_url"] for event in events], [Plugin.BASE_URL + "/events/" + n for n in ("6", "7", "8")])

    def test_real_detail_forms_and_dates(self):
        for event_id, title in (("6", "Dailies2"), ("7", "Spooktober2026")):
            with self.subTest(event_id=event_id):
                result = Plugin._event(fixture(event_id), Plugin.BASE_URL + "/events/" + event_id)
                self.assertEqual(result["event_title"], title)
                self.assertEqual(result["claim"]["date"], "Oct 25")
                self.assertEqual(result["claim"]["url"], Plugin.BASE_URL + "/events/" + event_id + "/claims")
                self.assertEqual(result["claim"]["data"], {"_token": "fixture-token"})
                self.assertEqual(sum(day["status"] == "今日待领取" for day in result["days"]), 1)

    def test_claimed_card_has_rewards_and_no_claim(self):
        result = Plugin._event(claimed_page(), Plugin.BASE_URL + "/events/7")
        self.assertIsNone(result["claim"])
        day = next(day for day in result["days"] if day["date"] == "Oct 25")
        self.assertEqual(day["status"], "已领取")
        self.assertEqual(day["rewards"], ["100 BON", "2 FL Tokens"])

    def test_index_deduplicates_and_rejects_foreign_links(self):
        page = fixture("index").replace('</tbody>', '<tr><td><a href="/events/6">duplicate</a><a href="https://evil.test/events/9">bad</a></td></tr></tbody>')
        self.assertEqual(len(Plugin._events(page)), 3)

    def test_unrecognized_index_does_not_silently_mean_no_events(self):
        for page in ("<html>login</html>", "<main class='page__event--index'>challenge</main>"):
            with self.assertRaises(ValueError):
                Plugin._events(page)

    def test_valid_empty_index(self):
        self.assertEqual(Plugin._events('<main class="page__event--index"><table></table></main>'), [])

    def test_safe_urls(self):
        for url in ("https://evil.test/events/7", "http://seedpool.org/events/7", "https://seedpool.org:444/events/7", "https://x@seedpool.org/events/7", "https://seedpool.org/events/7?token=secret", "https://seedpool.org/logout", "https://seedpool.org:invalid/events/7"):
            self.assertEqual(Plugin._safe_url(url), "", url)

    def test_form_must_match_event_host_id_and_post(self):
        url = Plugin.BASE_URL + "/events/7"
        for replacement in ('action="https://evil.test/events/7/claims"', 'action="https://seedpool.org/events/6/claims"', 'action="http://seedpool.org/events/7/claims"'):
            page = fixture("7").replace('action="https://seedpool.org/events/7/claims"', replacement)
            self.assertIsNone(Plugin._event(page, url)["claim"])
        self.assertIsNone(Plugin._event(fixture("7").replace('method="POST"', 'method="GET"'), url)["claim"])

    def test_missing_token_rejects_claim(self):
        page = fixture("7").replace('value="fixture-token"', 'value=""')
        self.assertIsNone(Plugin._event(page, Plugin.BASE_URL + "/events/7")["claim"])

    def test_meta_token_fallback(self):
        page = '<meta content="meta-token" name="csrf-token">' + fixture("7").replace('value="fixture-token"', 'value=""')
        self.assertEqual(Plugin._event(page, Plugin.BASE_URL + "/events/7")["claim"]["data"]["_token"], "meta-token")

    def test_claim_verifies_original_card_independent_of_local_date(self):
        url = Plugin.BASE_URL + "/events/7"
        session = Mock()
        session.request.side_effect = [response(fixture("7"), url), response("<html>ok</html>", url), response(claimed_page(), url)]
        result = self.plugin._claim_event(session, {"event_url": url, "event_title": "Spooktober2026"})
        self.assertEqual(result["status"], "成功")
        self.assertEqual(result["reward"], "100 BON / 2 FL Tokens")
        self.assertEqual([call.args[0] for call in session.request.call_args_list], ["GET", "POST", "GET"])

    def test_already_claimed_never_posts(self):
        url = Plugin.BASE_URL + "/events/7"
        session = Mock()
        session.request.return_value = response(claimed_page(), url)
        self.assertEqual(self.plugin._claim_event(session, {"event_url": url})["status"], "无可领奖励")
        self.assertEqual(session.request.call_count, 1)

    def test_unverified_post_is_failure(self):
        url = Plugin.BASE_URL + "/events/7"
        session = Mock()
        session.request.return_value = response(fixture("7"), url)
        self.assertEqual(self.plugin._claim_event(session, {"event_url": url})["status"], "失败")

    def test_expired_and_future_cards_never_post(self):
        url = Plugin.BASE_URL + "/events/7"
        for state in ("past", "future"):
            session = Mock()
            session.request.return_value = response(fixture("7").replace("today-unclaimed", state), url)
            with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25)):
                self.assertEqual(self.plugin._claim_event(session, {"event_url": url})["status"], "待开放" if state == "future" else "无可领奖励")
            self.assertEqual(session.request.call_count, 1)

    def test_bad_form_is_failure_not_no_rewards(self):
        url = Plugin.BASE_URL + "/events/7"
        session = Mock()
        session.request.return_value = response(fixture("7").replace('value="fixture-token"', 'value=""'), url)
        self.assertEqual(self.plugin._claim_event(session, {"event_url": url})["status"], "失败")
        self.assertEqual(session.request.call_count, 1)

    def test_redirect_to_login_or_foreign_host_is_not_followed(self):
        for target in ("/login", "https://evil.test/events/7"):
            session = Mock()
            session.request.return_value = response(status=302, location=target)
            with self.assertRaises(ValueError):
                self.plugin._request(session, "GET", Plugin.EVENTS_URL)
            self.assertEqual(session.request.call_count, 1)

    def test_post_redirect_is_followed_as_get_without_csrf_body(self):
        session = Mock()
        session.request.side_effect = [response(status=302, location="/events/7"), response(fixture("7"))]
        self.plugin._request(session, "POST", Plugin.BASE_URL + "/events/7/claims", data={"_token": "secret"}, headers={"X-CSRF-TOKEN": "secret"})
        second = session.request.call_args_list[1]
        self.assertEqual(second.args[0], "GET")
        self.assertNotIn("data", second.kwargs)
        self.assertNotIn("headers", second.kwargs)

    def test_post_307_not_replayed(self):
        session = Mock()
        session.request.return_value = response(status=307, location="/events/7/claims")
        with self.assertRaises(ValueError):
            self.plugin._request(session, "POST", Plugin.BASE_URL + "/events/7/claims")
        self.assertEqual(session.request.call_count, 1)

    def test_http_errors_and_login_html(self):
        for res in (response(status=403), response(status=419), response('<input type="password">')):
            session = Mock()
            session.request.return_value = res
            with self.assertRaises(ValueError):
                self.plugin._request(session, "GET", Plugin.EVENTS_URL)

    def test_run_continues_other_events_and_inherits_site_settings(self):
        session = Mock()
        context = Mock()
        context.__enter__ = Mock(return_value=session)
        context.__exit__ = Mock(return_value=False)
        site = types.SimpleNamespace(cookie="session=a=b; other=c", ua="site-ua", proxy=True)
        with patch.object(PLUGIN_MODULE.requests, "Session", return_value=context), patch.object(PLUGIN_MODULE, "SiteOper") as oper:
            oper.return_value.get_by_domain.return_value = site
            with patch.object(self.plugin, "_request", return_value=response(fixture("index"))), patch.object(self.plugin, "_claim_event", side_effect=[TimeoutError("secret"), {"status": "成功"}, {"status": "无可领奖励"}]) as claim:
                results = self.plugin._run()
        self.assertEqual([r["status"] for r in results], ["失败", "成功", "无可领奖励"])
        self.assertEqual(claim.call_count, 3)
        self.assertNotIn("secret", results[0]["message"])
        session.cookies.set.assert_any_call("session", "a=b", domain="seedpool.org", path="/")
        session.headers.update.assert_called_once()
        self.assertEqual(session.headers.update.call_args.args[0]["User-Agent"], "site-ua")
        session.proxies.update.assert_called_once()

    def test_manual_cookie_and_missing_cookie(self):
        with patch.object(PLUGIN_MODULE, "SiteOper") as oper:
            oper.return_value.get_by_domain.return_value = None
            with self.assertRaises(ValueError):
                self.plugin._run()
            self.plugin._cookie = "manual=1"
            session = Mock()
            context = Mock(__enter__=Mock(return_value=session), __exit__=Mock(return_value=False))
            with patch.object(PLUGIN_MODULE.requests, "Session", return_value=context), patch.object(self.plugin, "_request", return_value=response('<main class="page__event--index"><table></table></main>')):
                self.assertEqual(self.plugin._run(), [])
            session.cookies.set.assert_called_once_with("manual", "1", domain="seedpool.org", path="/")

    def test_cache_notification_and_page_do_not_store_tokens_or_request(self):
        url = Plugin.BASE_URL + "/events/7"
        result = {"event_url": url, "event_title": "Spooktober2026", "status": "成功", "reward": "100 BON", "message": "verified", **Plugin._event(claimed_page(), url)}
        with patch.object(self.plugin, "_run", return_value=[result]):
            self.plugin.claim_rewards()
        self.assertNotIn("fixture-token", json.dumps(self.data))
        self.assertNotIn('"claim"', json.dumps(self.data))
        self.plugin.post_message.assert_called_once()
        with patch.object(self.plugin, "_run", side_effect=AssertionError("page must be cached")):
            self.assertIn("Spooktober2026", json.dumps(self.plugin.get_page()))

    def test_quiet_when_no_claim_and_releases_lock_after_error(self):
        with patch.object(self.plugin, "_run", return_value=[]):
            self.plugin.claim_rewards()
        self.plugin.post_message.assert_not_called()
        with patch.object(self.plugin, "_run", side_effect=TimeoutError("secret")):
            self.plugin.claim_rewards()
        self.assertNotIn("secret", json.dumps(self.data))
        self.assertFalse(self.plugin._run_lock.locked())

    def test_concurrent_run_skips(self):
        self.plugin._run_lock.acquire()
        try:
            with patch.object(self.plugin, "_run") as run:
                self.plugin.claim_rewards()
                run.assert_not_called()
        finally:
            self.plugin._run_lock.release()

    def test_onlyonce_and_defaults(self):
        self.plugin.init_plugin({"onlyonce": True})
        self.assertIsNone(self.plugin._scheduler)
        self.plugin.update_config.assert_not_called()
        self.assertTrue(self.plugin.get_state())
        once = self.plugin.get_service()[0]
        self.assertEqual(once["id"], "SeedpoolEventClaimOnce")
        self.assertEqual(once["func_kwargs"], {"onlyonce": True})
        with patch.object(self.plugin, "_run", return_value=[]):
            once["func"](**once["func_kwargs"])
        self.assertFalse(self.plugin.update_config.call_args.args[0]["onlyonce"])
        self.assertFalse(self.plugin.get_state())
        self.assertEqual(self.plugin.get_service(), [])
        self.assertEqual(self.plugin.get_form()[1]["cron"], Plugin.DEFAULT_CRON)

    def test_tabs_separate_each_events_rewards_and_history(self):
        for event_id, title, reward in (("6", "Dailies2", "100 BON"), ("7", "Spooktober2026", "900 BON")):
            url = Plugin.BASE_URL + "/events/" + event_id
            result = {"event_url": url, "event_title": title, "status": "成功", "reward": reward, "message": title + " verified",
                      **Plugin._event(claimed_page(event_id).replace("100 BON", reward), url)}
            with patch.object(self.plugin, "_run", return_value=[result]):
                self.plugin.claim_rewards()
        page = self.plugin.get_page()
        tabs = page[1]["content"]
        labels = [node for node in tabs if node["component"] == "label"]
        self.assertEqual([node["text"] for node in labels], ["🟢 Dailies2", "🟢 Spooktober2026"])
        radios = [node for node in tabs if node["component"] == "input"]
        self.assertEqual([node["props"]["checked"] for node in radios], [True, False])
        panels = [node for node in tabs if node["component"] == "section"]
        for radio, label, panel, other_name, expected_reward in zip(radios, labels, panels, ["Spooktober2026", "Dailies2"], ["100 BON", "900 BON"]):
            self.assertEqual(radio["props"]["aria-controls"], panel["props"]["id"])
            self.assertEqual(label["props"]["for"], radio["props"]["id"])
            css = tabs[0]["html"]
            self.assertIn(f"#{radio['props']['id']}:checked ~ #{panel['props']['id']} {{ display: block; }}", css)
            content = json.dumps(panel, ensure_ascii=False)
            self.assertNotIn(other_name, content)
            self.assertIn(expected_reward, content)
            for heading in ("活动总天数", "已领取", "已过期未领", "今日待领取", "待开放", "奖励总计", "每日状态", "本活动执行历史"):
                self.assertIn(heading, content)
            totals = Plugin._reward_totals(self.data["event_snapshots"][Plugin.BASE_URL + "/events/" + ("6" if expected_reward == "100 BON" else "7")]["days"])
            self.assertEqual(totals[0]["display"], expected_reward.split()[0])

    def test_failed_activity_has_its_own_tab_and_previous_cache(self):
        url = Plugin.BASE_URL + "/events/7"
        previous = {"event_url": url, "event_title": "Spooktober2026", "time": "2026-10-24 09:00:00", **Plugin._event(claimed_page(), url)}
        self.data["event_snapshots"] = {url: previous}
        self.data["claim_logs"] = [
            {"event_url": url, "event_title": "Spooktober2026", "time": "2026-10-25 09:00:00", "status": "失败", "message": "HTTP 403"},
            {"event_url": Plugin.BASE_URL + "/events/6", "event_title": "Dailies2", "status": "失败", "message": "HTTP 419"},
        ]
        content = json.dumps(self.plugin.get_page(), ensure_ascii=False)
        self.assertIn("HTTP 403", content)
        self.assertIn("HTTP 419", content)
        self.assertIn("2026-10-24 09:00:00", content)
        self.assertIn("100 BON", content)
        self.assertIn("暂无此活动的每日状态缓存", content)

    def test_daily_status_uses_three_columns_and_current_month(self):
        url = Plugin.BASE_URL + "/events/6"
        snapshot = {"time": "2026-10-25 09:00:00", **Plugin._event(fixture("6"), url)}
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25)):
            content = self.plugin._event_page(url, snapshot, [])
        daily_row = content[-3]
        columns = daily_row["content"]
        counts = [len(col["content"][0]["content"][1]["content"]) for col in columns]
        self.assertEqual(counts, [10, 10, 11])
        self.assertNotIn("Sep ", json.dumps(daily_row))

    def test_reward_totals_use_only_this_events_claimed_days(self):
        days = [{"status": "已领取", "rewards": ["100 BON", "2 FL Tokens", "1 GiB Upload", "2 Mystery Boxes"]},
                {"status": "已领取", "rewards": ["50 BON", "1024 MiB Upload", "Lucky Badge"]},
                {"status": "待开放", "rewards": ["999 BON"]}]
        totals = {item["key"]: item["display"] for item in Plugin._reward_totals(days)}
        self.assertEqual(totals["bon"], "150")
        self.assertEqual(totals["fl_tokens"], "2")
        self.assertEqual(totals["upload"], "2 GiB")
        self.assertEqual(totals["other:mystery boxes"], "2")
        self.assertEqual(totals["other:lucky badge"], "× 1")

    def test_config_uses_blu_cron_component(self):
        content = json.dumps(self.plugin.get_form(), ensure_ascii=False)
        self.assertIn("VCronField", content)
        self.assertIn("成功或失败时通知", content)

    def test_three_blu_options_are_configurable_and_no_event_url(self):
        self.plugin.init_plugin({"random_delay": "30", "retry_interval_hours": "6", "max_retries": "1"})
        self.assertEqual((self.plugin._random_delay, self.plugin._retry_interval_hours, self.plugin._max_retries), (30, 6, 1))
        form, defaults = self.plugin.get_form()
        text = json.dumps(form, ensure_ascii=False)
        for key in ("random_delay", "retry_interval_hours", "max_retries"):
            self.assertIn(key, text)
            self.assertIn(key, defaults)
        self.assertNotIn('"model": "event_url"', text)
        self.plugin.init_plugin({"random_delay": "invalid", "retry_interval_hours": None, "max_retries": 0})
        self.assertEqual((self.plugin._random_delay, self.plugin._retry_interval_hours, self.plugin._max_retries), (0, 6, 0))
        self.plugin.init_plugin({"random_delay": 999, "retry_interval_hours": -1, "max_retries": 99})
        self.assertEqual((self.plugin._random_delay, self.plugin._retry_interval_hours, self.plugin._max_retries), (60, 1, 3))

    def test_cron_jitter_does_not_delay_immediate_run(self):
        now = datetime.datetime(2026, 10, 25, 9)
        with patch.object(self.plugin, "_now", return_value=now):
            self.plugin.init_plugin({"enabled": True, "onlyonce": True, "random_delay": 30})
        trigger = Mock()
        with patch.object(self.plugin, "_now", return_value=now), patch.object(PLUGIN_MODULE.CronTrigger, "from_crontab", return_value=trigger):
            services = self.plugin.get_service()
        self.assertEqual(services[0]["trigger"].run_date, now + datetime.timedelta(seconds=3))
        self.assertEqual(services[1]["trigger"].jitter, 1800)
        self.assertNotIn("jitter", services[0]["kwargs"])

    def test_immediate_request_survives_init_and_service_reregistration(self):
        self.config.update({"onlyonce": True, "enabled": True, "cookie": "private-cookie", "random_delay": 30, "extra": "keep"})
        self.plugin.init_plugin(dict(self.config))
        first = self.plugin.get_service()
        self.plugin.stop_service()
        self.plugin.init_plugin(dict(self.config))
        second = self.plugin.get_service()
        self.assertEqual(first[0]["id"], second[0]["id"])
        self.plugin.update_config.assert_not_called()
        with patch.object(self.plugin, "_run", return_value=[]) as run:
            second[0]["func"](**second[0]["func_kwargs"])
            first[0]["func"](**first[0]["func_kwargs"])
        run.assert_called_once()
        self.assertFalse(self.config["onlyonce"])
        self.assertEqual(self.config["extra"], "keep")
        self.assertEqual(self.config["cookie"], "private-cookie")
        self.assertEqual(self.config["random_delay"], 30)
        self.assertNotIn("private-cookie", json.dumps(self.data))
        self.assertEqual([service["id"] for service in self.plugin.get_service()], ["SeedpoolEventClaim"])

    def test_persisted_immediate_flag_is_checked_when_registering_services(self):
        self.plugin.init_plugin({"enabled": False})
        self.config["onlyonce"] = True
        self.assertTrue(self.plugin.get_state())
        self.assertEqual(self.plugin.get_service()[0]["id"], "SeedpoolEventClaimOnce")

    def test_bad_cron_does_not_drop_immediate_task(self):
        self.plugin.init_plugin({"enabled": True, "onlyonce": True, "cron": "invalid"})
        with patch.object(PLUGIN_MODULE.CronTrigger, "from_crontab", side_effect=ValueError):
            self.assertEqual([service["id"] for service in self.plugin.get_service()], ["SeedpoolEventClaimOnce"])

    def test_immediate_callback_records_running_then_failure(self):
        self.plugin.init_plugin({"onlyonce": True})
        writes = []
        self.plugin.save_data = lambda key, value: (writes.append((key, value)), self.data.update({key: value}))
        with patch.object(self.plugin, "_run", side_effect=TimeoutError("private")):
            self.plugin.claim_rewards(onlyonce=True)
        states = [value["message"] for key, value in writes if key == "last_run"]
        self.assertEqual(states[0], "正在读取活动列表并逐个检查奖励")
        self.assertIn("失败 1", states[-1])
        self.assertFalse(self.config["onlyonce"])
        self.assertEqual(self.data["claim_logs"][-1]["status"], "失败")

    def test_pending_events_share_one_retry_and_daily_limit_survives_cron(self):
        self.plugin.init_plugin({"max_retries": 1, "retry_interval_hours": 6})
        now = datetime.datetime(2026, 10, 25, 9)
        pending = lambda: [{"event_title": title, "status": "待开放", "message": "尚未开放"} for title in ("Dailies2", "Spooktober2026")]
        with patch.object(self.plugin, "_now", return_value=now), patch.object(self.plugin, "_run", side_effect=pending):
            self.plugin.claim_rewards()
            scheduler = self.plugin._scheduler
            self.assertEqual(len(scheduler.jobs), 1)
            self.assertEqual(scheduler.jobs[0]["run_date"], now + datetime.timedelta(hours=6))
            self.assertEqual(scheduler.jobs[0]["kwargs"], {"expected_date": "2026-10-25"})
            self.plugin.claim_rewards()
            self.assertEqual(len(scheduler.jobs), 1)
        # APScheduler removes a date job before its callback runs.
        scheduler.remove_job("SeedpoolEventClaimRetry")
        with patch.object(self.plugin, "_now", return_value=now + datetime.timedelta(hours=6)), patch.object(self.plugin, "_run", side_effect=pending):
            self.plugin.claim_rewards(expected_date="2026-10-25")
            self.assertEqual(self.data["retry_usage"], {"date": "2026-10-25", "count": 1})
            self.assertEqual(scheduler.jobs, [])
            self.plugin.claim_rewards()
            self.assertEqual(scheduler.jobs, [])
        self.assertIn("补查次数已用尽", self.data["claim_logs"][-1]["message"])

    def test_retries_skip_cross_day_and_zero_disables_them(self):
        self.plugin.init_plugin({"max_retries": 0})
        pending = [{"status": "待开放", "message": "尚未开放"}]
        self.plugin._schedule_retry(pending, 0)
        self.assertIsNone(self.plugin._scheduler)
        self.plugin._max_retries = 2
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25, 22)):
            self.plugin._schedule_retry(pending, 0)
            self.assertIsNone(self.plugin._scheduler)
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 26, 1)), patch.object(self.plugin, "_run") as run:
            self.plugin.claim_rewards(expected_date="2026-10-25")
            run.assert_not_called()

    def test_existing_retry_keeps_earlier_time_and_cancels_when_done(self):
        self.plugin.init_plugin({"max_retries": 2, "retry_interval_hours": 6})
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25, 16)):
            self.plugin._schedule_retry([{"status": "待开放", "message": "尚未开放"}], 0)
        first = dict(self.plugin._scheduler.jobs[0])
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25, 20)):
            self.plugin._schedule_retry([{"status": "待开放", "message": "尚未开放"}], 0)
        self.assertEqual(self.plugin._scheduler.jobs, [first])
        self.plugin._schedule_retry([{"status": "成功"}], 0)
        self.assertEqual(self.plugin._scheduler.jobs, [])

    def test_stop_detaches_scheduler_without_waiting_for_running_callback(self):
        scheduler = Mock(running=True)
        def shutdown(**kwargs):
            self.assertFalse(kwargs["wait"])
            self.assertIsNone(self.plugin._scheduler)
            self.assertTrue(self.plugin._stopping)
        scheduler.shutdown.side_effect = shutdown
        self.plugin._scheduler = scheduler
        self.plugin.stop_service()
        scheduler.shutdown.assert_called_once_with(wait=False)
        scheduler.remove_all_jobs.assert_not_called()
        self.plugin.stop_service()
        scheduler.shutdown.assert_called_once()

    def test_finishing_callback_cannot_recreate_retry_scheduler_after_stop(self):
        self.plugin.init_plugin({"max_retries": 2})
        self.plugin.stop_service()
        with patch.object(PLUGIN_MODULE, "BackgroundScheduler") as factory:
            self.plugin._schedule_retry([{"status": "待开放", "message": "尚未开放"}], 0)
            factory.assert_not_called()
        self.plugin.init_plugin({"max_retries": 2})
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25, 9)):
            self.plugin._schedule_retry([{"status": "待开放", "message": "尚未开放"}], 0)
        self.assertTrue(self.plugin._scheduler.running)

    def test_claimable_site_card_still_wins_over_local_date(self):
        url = Plugin.BASE_URL + "/events/7"
        session = Mock()
        session.request.side_effect = [response(fixture("7"), url), response("<html>ok</html>", url), response(claimed_page(), url)]
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 26, 1)):
            self.assertEqual(self.plugin._claim_event(session, {"event_url": url})["status"], "成功")

    def test_index_error_stays_visible_without_activity_tabs(self):
        self.data["claim_logs"] = [{"event_title": "活动列表", "status": "失败", "message": "Cookie 已失效"}]
        content = json.dumps(self.plugin.get_page(), ensure_ascii=False)
        self.assertIn("Cookie 已失效", content)
        self.assertNotIn('"type": "radio"', content)

    def test_tab_activity_status_uses_period_not_daily_claim_status(self):
        events = Plugin._events(fixture("index"))
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25)):
            self.assertEqual([self.plugin._activity_status(event) for event in events],
                             [("🟢", "进行中"), ("🟢", "进行中"), ("⛔", "已过期")])
            claimed = {**events[1], **Plugin._event(claimed_page(), events[1]["event_url"])}
            self.assertEqual(self.plugin._activity_status(claimed), ("🟢", "进行中"))
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 1)):
            self.assertEqual(self.plugin._activity_status(events[1]), ("⏳", "尚未开始"))

    def test_tab_activity_status_supports_old_cache_and_year_boundary(self):
        old = {"time": "2026-10-25 09:00:00", "days": [{"date": "Oct 8"}, {"date": "Oct 16"}]}
        cross_year = {"time": "2026-12-25 09:00:00", "days": [{"date": "Dec 1"}, {"date": "Jan 10"}]}
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2026, 10, 25)):
            self.assertEqual(self.plugin._activity_status(old), ("⛔", "已过期"))
            self.assertEqual(self.plugin._activity_status({})[0], "❔")
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2027, 1, 10)):
            self.assertEqual(self.plugin._activity_status(cross_year), ("🟢", "进行中"))
        with patch.object(self.plugin, "_now", return_value=datetime.datetime(2027, 1, 11)):
            self.assertEqual(self.plugin._activity_status(cross_year), ("⛔", "已过期"))

    def test_manifest_matches_plugin(self):
        manifest = json.loads((PATH.parents[2] / "package.v2.json").read_text(encoding="utf-8"))["SeedpoolEventClaim"]
        self.assertEqual(manifest["version"], Plugin.plugin_version)
        self.assertEqual(manifest["name"], Plugin.plugin_name)


if __name__ == "__main__":
    unittest.main()
