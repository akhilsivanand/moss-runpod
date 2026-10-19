"""Release gates fail on incomplete public packages without inventing GPU evidence."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_release", ROOT / "scripts/check_release.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "package"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))

    def tearDown(self):
        self.temporary.cleanup()

    def test_prepared_source_does_not_require_gpu_report(self):
        (self.root / "docs/validation.json").unlink(missing_ok=True)
        result = checker.check_release(self.root)
        self.assertEqual(result["source"], "passed")
        self.assertEqual(result["gpu_validation"], "not_checked")

    def test_missing_workflow_is_a_source_failure(self):
        (self.root / "workflows/api/photography-bf16.json").unlink()
        with self.assertRaisesRegex(checker.ReleaseError, "missing"):
            checker.check_release(self.root)

    def test_model_must_have_a_revision_pinned_url(self):
        path = self.root / "config/models.json"
        manifest = json.loads(path.read_text())
        manifest["models"][0]["url"] = manifest["models"][0]["url"].replace(manifest["models"][0]["source"]["revision"], "main")
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(checker.ReleaseError, "pinned"):
            checker.check_release(self.root)

    def test_publish_refuses_placeholder_registry(self):
        path = self.root / 'deploy/pod-template.json'
        pod = json.loads(path.read_text())
        pod['imageName'] = 'ghcr.io/' + 'OWNER/moss-comfyui:0.1.0'
        path.write_text(json.dumps(pod))
        with self.assertRaisesRegex(checker.ReleaseError, "identities"):
            checker.check_release(self.root, publish=True)

    def test_publish_requires_gpu_report_after_identity_is_resolved(self):
        for path, content in list(checker.text_files(self.root)):
            path.write_text(content.replace("OWNER", "example-maintainer"))
        (self.root / "docs/validation.json").unlink(missing_ok=True)
        with self.assertRaisesRegex(checker.ReleaseError, "validation.json"):
            checker.check_release(self.root, publish=True)


if __name__ == "__main__":
    unittest.main()
