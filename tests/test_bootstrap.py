import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from moss_runtime.bootstrap import serve
from moss_runtime import bootstrap


def test_serverless_workers_isolate_runtime_but_share_model_cache(tmp_path):
    paths = []

    async def record(root, comfy, workspace, mode, models):
        assert mode == 'serverless'
        assert models == tmp_path
        assert workspace != models
        assert workspace.is_dir()
        paths.append(workspace)

    async def run():
        with patch('moss_runtime.bootstrap.serve_workspace', side_effect=record):
            await asyncio.gather(serve(Path('/package'), Path('/comfy'), tmp_path, 'serverless'),
                                 serve(Path('/package'), Path('/comfy'), tmp_path, 'serverless'))
    asyncio.run(run())
    assert paths[0] != paths[1]
    assert all(not path.exists() for path in paths)


def test_pod_uses_persistent_workspace(tmp_path):
    with patch('moss_runtime.bootstrap.serve_workspace', new_callable=AsyncMock) as start:
        asyncio.run(serve(Path('/package'), Path('/comfy'), tmp_path, 'pod'))
        start.assert_awaited_once_with(Path('/package'), Path('/comfy'), tmp_path, 'pod', tmp_path)


def test_default_pod_migrates_before_start_but_serverless_keeps_its_cache(tmp_path):
    old, current = tmp_path / 'moss', tmp_path / 'ComfyUI'
    (old / 'state').mkdir(parents=True)
    (old / 'models').mkdir()
    (old / 'state/runtime.lock').touch()
    (old / 'state/models.lock').touch()
    with patch.object(bootstrap, 'DEFAULT_DATA_ROOT', current), patch.object(bootstrap, 'LEGACY_DATA_ROOT', old):
        with patch.object(bootstrap, 'serve_workspace', new_callable=AsyncMock) as start:
            asyncio.run(serve(Path('/package'), Path('/comfy'), current, 'pod'))
            assert current.is_dir() and not old.exists()
            start.assert_awaited_once_with(Path('/package'), Path('/comfy'), current, 'pod', current)
        with patch.object(bootstrap, 'migrate_legacy_workspace', side_effect=AssertionError('Pod migration in Serverless')):
            with patch.object(bootstrap, 'serve_workspace', new_callable=AsyncMock) as start:
                asyncio.run(serve(Path('/package'), Path('/comfy'), current, 'serverless'))
                args = start.call_args.args
                assert args[2] != current and args[4] == current
