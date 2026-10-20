"""Release gates fail on incomplete public packages without inventing GPU evidence."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile


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

    def test_launch_rejects_manual_password_and_capacity_requirements(self):
        path = self.root / "deploy/pod-template.json"
        original = json.loads(path.read_text())
        for variable, value in (("MOSS_PASSWORD", ""), ("JUPYTER_PASSWORD", "shared-token"), ("MOSS_VOLUME_GB", "60")):
            with self.subTest(variable=variable):
                pod = {**original, "env": {**original["env"], variable: value}}
                path.write_text(json.dumps(pod))
                with self.assertRaisesRegex(checker.ReleaseError, "manual password, token or volume-size"):
                    checker.check_deployment(self.root)

    def test_native_connection_requires_platform_token_and_matching_port(self):
        path = self.root / "deploy/pod-console.json"
        original = json.loads(path.read_text())
        for changes, message in (({"startJupyter": False}, "Native Connect token"),
                                 ({"portsConfig": [{"name": "MOSS ComfyUI", "port": 8188}]}, "label port 8888")):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}))
                with self.assertRaisesRegex(checker.ReleaseError, message):
                    checker.check_deployment(self.root)

    def test_first_use_disk_and_explicit_startup_are_required(self):
        path = self.root / "deploy/pod-template.json"
        original = json.loads(path.read_text())
        for changes, message in (({"containerDiskInGb": 40}, "60 GB first-use disk"),
                                 ({"dockerStartCmd": []}, "baked startup script"),
                                 ({"dockerEntrypoint": ["bash"]}, "retain the image entry point")):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**original, **changes}))
                with self.assertRaisesRegex(checker.ReleaseError, message):
                    checker.check_deployment(self.root)

    def test_staging_tag_cannot_reuse_a_historical_gpu_report(self):
        pod = checker.read_json(self.root / "deploy/pod-template.json")
        pod["imageName"] = "ghcr.io/example-maintainer/moss-comfyui:staging"
        with self.assertRaisesRegex(checker.ReleaseError, "immutable digest"):
            checker.check_gpu_report(self.root, pod)

    def test_different_immutable_image_cannot_reuse_a_gpu_report(self):
        pod = checker.read_json(self.root / "deploy/pod-template.json")
        report = checker.read_json(self.root / "docs/validation.json")
        different = "0" * 64 if report["image_digest"][7:] != "0" * 64 else "1" * 64
        pod["imageName"] = "ghcr.io/example-maintainer/moss-comfyui@sha256:" + different
        with self.assertRaisesRegex(checker.ReleaseError, "differs from the GPU-tested digest"):
            checker.check_gpu_report(self.root, pod)

    def test_another_package_version_cannot_reuse_a_gpu_report(self):
        path = self.root / "docs/validation.json"
        report = checker.read_json(path)
        report["package_version"] = "0.0.0"
        path.write_text(json.dumps(report))
        pod = checker.read_json(self.root / "deploy/pod-template.json")
        with self.assertRaisesRegex(checker.ReleaseError, "package version"):
            checker.check_gpu_report(self.root, pod)

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

    def test_archive_retains_reviewed_publication_record_without_other_json(self):
        spec = importlib.util.spec_from_file_location(
            "package_release", self.root / "scripts/package_release.py")
        packager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packager)
        (self.root / "docs/unreviewed-publication.json").write_text(
            json.dumps({"not_for_release": True}))
        output = Path(self.temporary.name) / "source.zip"

        packager.package_release(self.root, output)

        with zipfile.ZipFile(output) as archive:
            record = "docs/publication-0.1.2.json"
            self.assertEqual(archive.read("moss-runpod/" + record),
                             (self.root / record).read_bytes())
            self.assertNotIn("moss-runpod/docs/unreviewed-publication.json",
                             archive.namelist())
            extracted = Path(self.temporary.name) / "extracted"
            archive.extractall(extracted)
        self.assertEqual(checker.check_release(extracted / "moss-runpod", publish=True)["publish"],
                         "passed")


if __name__ == "__main__":
    unittest.main()
