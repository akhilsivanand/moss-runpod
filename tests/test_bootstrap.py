import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from moss_runtime.bootstrap import serve


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
