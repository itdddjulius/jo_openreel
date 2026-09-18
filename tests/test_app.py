import os
import subprocess
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import app, build_archive_query, build_dork, media_mime, playable_files, validate_query


class OpenReelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_and_home(self):
        health = self.client.get("/api/health").json()
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["version"], "1.1.0")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("OPENREELpy", response.text)

    def test_dork_and_archive_query(self):
        dork = build_dork("silent comedy films")
        self.assertIn("site:archive.org/details", dork)
        self.assertIn('"silent comedy films"', dork)
        self.assertIn("filetype:mp4", dork)
        self.assertEqual(
            build_archive_query("silent comedy"),
            "mediatype:movies AND (silent AND comedy)",
        )

    def test_unsafe_query_rejected(self):
        for query in ("movie torrent", "DRM bypass", "pirated latest movie"):
            with self.assertRaises(Exception) as caught:
                validate_query(query)
            self.assertEqual(getattr(caught.exception, "status_code", None), 422)

    def test_playable_selection_and_mime(self):
        metadata = {"files": [
            {"name": "thumb.mp4", "size": "9999", "format": "MPEG4"},
            {"name": "small.mp4", "size": "100", "format": "MPEG4"},
            {"name": "large.webm", "size": "200", "format": "WebM"},
            {"name": "private.mp4", "size": "300", "private": True},
        ]}
        files = playable_files(metadata)
        self.assertEqual([item["name"] for item in files], ["large.webm", "small.mp4"])
        self.assertEqual(media_mime("large.webm"), "video/webm")

    def test_document_allowlist(self):
        self.assertEqual(self.client.get("/docs/README.md").status_code, 200)
        self.assertEqual(self.client.get("/docs/NOT-ALLOWED.md").status_code, 404)

    def test_vercel_cold_import_from_project_root(self):
        root = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c", "from app import app; assert app.version == '1.1.0'"],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_required_deployment_assets_exist(self):
        root = Path(__file__).resolve().parents[1]
        required = [
            root / "templates" / "index.html",
            root / "static" / "app.css",
            root / "static" / "app.js",
            root / "docs" / "README.md",
        ]
        self.assertEqual([str(path) for path in required if not path.is_file()], [])


if __name__ == "__main__":
    unittest.main()
