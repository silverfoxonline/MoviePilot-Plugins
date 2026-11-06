"""Offline regression tests for V3 download-history media identities."""

import ast
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock


class MediaSource(Enum):
    TMDB = "themoviedb"
    Douban = "douban"


def resolve_media_identity(media_source, media_id):
    try:
        return MediaSource(media_source), media_id
    except (ValueError, TypeError):
        return None, None


class DownloadSiteIdentityTests(TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parents[1] / "plugins.v3/downloadsitetagcustom/__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        plugin = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DownloadSiteTagCustom")
        method = next(n for n in plugin.body if isinstance(n, ast.FunctionDef) and n.name == "_get_tmdb_info")
        module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
        cls.projector = mock.Mock()
        namespace = {
            "MediaSource": MediaSource,
            "resolve_media_identity": resolve_media_identity,
            "MediaChain": lambda: cls.projector,
        }
        exec(compile(module, str(path), "exec"), namespace)
        cls.get_info = staticmethod(namespace["_get_tmdb_info"])

    def setUp(self):
        self.chain = mock.Mock()
        self.plugin = SimpleNamespace(chain=self.chain)
        self.projector.reset_mock()

    def test_tmdb_identity_uses_existing_tmdb_chain(self):
        self.chain.tmdb_info.return_value = {"genre_ids": [16]}
        record = SimpleNamespace(media_source="themoviedb", media_id="1399")
        self.assertEqual(self.get_info(self.plugin, record, "tv"), {"genre_ids": [16]})
        self.chain.tmdb_info.assert_called_once_with(mtype="tv", tmdbid=1399)
        self.projector.convert_media_identity.assert_not_called()

    def test_other_source_converts_complete_identity(self):
        self.projector.convert_media_identity.return_value = {"genre_ids": [16]}
        record = SimpleNamespace(media_source="douban", media_id="12345")
        self.assertEqual(self.get_info(self.plugin, record, "tv"), {"genre_ids": [16]})
        self.projector.convert_media_identity.assert_called_once_with(
            target_source=MediaSource.TMDB, media_source=MediaSource.Douban,
            media_id="12345", mtype="tv",
        )
        self.chain.tmdb_info.assert_not_called()

    def test_missing_or_invalid_identity_does_not_query(self):
        for source, media_id in [(None, None), ("themoviedb", "invalid")]:
            with self.subTest(source=source, media_id=media_id):
                record = SimpleNamespace(media_source=source, media_id=media_id)
                self.assertIsNone(self.get_info(self.plugin, record, "tv"))
        self.chain.tmdb_info.assert_not_called()
        self.projector.convert_media_identity.assert_not_called()
