"""Workspace upgrades preserve data and expose one ordinary model directory."""
import errno
import fcntl
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from moss_runtime import paths
from moss_runtime import assets


def write(path, content=b'fixture'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def legacy_workspace(root):
    write(root / 'state/runtime.lock', b'')
    write(root / 'state/models.lock', b'')
    write(root / 'models/loras/adapter.safetensors', b'weight fixture')
    write(root / 'models/loras/adapter.safetensors.part.moss.json', b'ownership fixture')
    write(root / 'user/default/workflows/edited.json', b'user edit')
    write(root / 'input/example.png', b'input fixture')
    write(root / 'output/example.png', b'output fixture')


def test_workspace_rename_preserves_every_file_inode_size_and_timestamp(tmp_path):
    old, new = tmp_path / 'moss', tmp_path / 'ComfyUI'
    legacy_workspace(old)
    before = {p.relative_to(old): paths._identity(p) for p in old.rglob('*') if p.is_file()}
    assert paths.migrate_legacy_workspace(old, new)
    assert not old.exists()
    assert {p.relative_to(new): paths._identity(p) for p in new.rglob('*') if p.is_file()} == before
    assert paths.migrate_legacy_workspace(old, new) is False


def test_both_roots_or_unmanaged_legacy_are_preserved(tmp_path):
    old, new = tmp_path / 'moss', tmp_path / 'ComfyUI'
    legacy_workspace(old)
    write(new / 'keep.txt', b'user data')
    with pytest.raises(RuntimeError, match='Both workspace roots'):
        paths.migrate_legacy_workspace(old, new)
    assert (old / 'models/loras/adapter.safetensors').read_bytes() == b'weight fixture'
    assert (new / 'keep.txt').read_bytes() == b'user data'
    unrelated = tmp_path / 'unmanaged'
    write(unrelated / 'project.txt')
    with pytest.raises(RuntimeError, match='no managed state'):
        paths.migrate_legacy_workspace(unrelated, tmp_path / 'unused')
    assert (unrelated / 'project.txt').is_file()


def test_running_legacy_runtime_blocks_workspace_migration(tmp_path):
    old, new = tmp_path / 'moss', tmp_path / 'ComfyUI'
    legacy_workspace(old)
    with (old / 'state/runtime.lock').open('r+') as active:
        fcntl.flock(active, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='still in use'):
            paths.migrate_legacy_workspace(old, new)
    assert old.is_dir() and not new.exists()


def test_migrated_weights_need_no_download_and_partial_receipt_keeps_its_inode(tmp_path):
    old, new = tmp_path / 'moss', tmp_path / 'ComfyUI'
    legacy_workspace(old)
    payload = b'weight fixture'
    model = {'id': 'existing', 'path': 'loras/adapter.safetensors',
             'url': 'https://example.invalid/weights', 'size': len(payload),
             'sha256': hashlib.sha256(payload).hexdigest(), 'license': 'MIT',
             'source': {'repository': 'fixture/models'}, 'profiles': ['common']}
    partial_model = {**model, 'id': 'partial', 'path': 'loras/partial.safetensors'}
    partial = assets._claim_partial(old / 'models' / partial_model['path'], partial_model)
    partial.write_bytes(payload[:3])
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'schema_version': 1, 'models': [model]}))
    paths.migrate_legacy_workspace(old, new)
    assert assets._owned_partial(new / 'models' / partial_model['path'], partial_model).st_size == 3
    with patch.object(assets, '_run_curl', side_effect=AssertionError('Unexpected download')):
        result = assets.prepare_models(manifest, new)
    assert result['verified'] == 1 and result['downloaded'] == 0


def test_custom_upload_moves_to_canonical_loras_and_baked_path_aliases_it(tmp_path):
    comfy, data = tmp_path / 'baked', tmp_path / 'ComfyUI'
    write(comfy / 'models/loras/put_loras_here', b'')
    upload = write(comfy / 'models/loras/uploaded.safetensors', b'user uploaded weights')
    identity = paths._identity(upload)
    write(data / 'models/loras/bundled.safetensors', b'bundled weights')
    paths.expose_persistent_models(comfy, data)
    target = data / 'models/loras/uploaded.safetensors'
    assert paths._identity(target) == identity
    assert (comfy / 'models').is_symlink()
    assert (comfy / 'models/loras/uploaded.safetensors').samefile(target)
    assert not (data / 'models/loras/put_loras_here').exists()
    assert (data / 'models/loras/bundled.safetensors').read_bytes() == b'bundled weights'
    paths.expose_persistent_models(comfy, data)  # Idempotent restart.


def test_identical_uploaded_copy_is_deduplicated_but_conflicts_move_nothing(tmp_path):
    comfy, data = tmp_path / 'baked', tmp_path / 'ComfyUI'
    write(comfy / 'models/loras/same.safetensors', b'identical')
    target = write(data / 'models/loras/same.safetensors', b'identical')
    identity = paths._identity(target)
    paths.expose_persistent_models(comfy, data)
    assert paths._identity(target) == identity
    assert (comfy / 'models').is_symlink()
    other, destination = tmp_path / 'other', tmp_path / 'destination'
    write(other / 'models/loras/a-new.safetensors', b'new')
    write(other / 'models/loras/conflict.safetensors', b'old')
    write(destination / 'models/loras/conflict.safetensors', b'new')
    with pytest.raises(RuntimeError, match='conflicts'):
        paths.expose_persistent_models(other, destination)
    assert (other / 'models/loras/a-new.safetensors').read_bytes() == b'new'
    assert not (destination / 'models/loras/a-new.safetensors').exists()
    assert (destination / 'models/loras/conflict.safetensors').read_bytes() == b'new'


def test_cross_filesystem_upload_copy_is_verified_before_source_removal(tmp_path):
    comfy, data = tmp_path / 'baked', tmp_path / 'ComfyUI'
    source = write(comfy / 'models/loras/custom.safetensors', b'opaque user weights')
    actual_link = paths.os.link

    def cross_device(path, destination, **kwargs):
        if Path(path) == source:
            raise OSError(errno.EXDEV, 'cross-device fixture')
        return actual_link(path, destination, **kwargs)

    with patch.object(paths.os, 'link', side_effect=cross_device):
        paths.expose_persistent_models(comfy, data)
    assert (data / 'models/loras/custom.safetensors').read_bytes() == b'opaque user weights'
    assert (comfy / 'models').is_symlink()
    assert not list((data / 'models/loras').glob('.moss-migrate-*'))


def test_unexpected_links_and_same_directory_are_never_deleted(tmp_path):
    comfy, data = tmp_path / 'baked', tmp_path / 'ComfyUI'
    external = write(tmp_path / 'elsewhere/keep.safetensors')
    (comfy / 'models').mkdir(parents=True)
    (comfy / 'models/linked.safetensors').symlink_to(external)
    with pytest.raises(RuntimeError, match='Unexpected model entry'):
        paths.expose_persistent_models(comfy, data)
    assert external.read_bytes() == b'fixture'
    same = tmp_path / 'same'
    write(same / 'models/loras/keep.safetensors')
    paths.expose_persistent_models(same, same)
    assert (same / 'models/loras/keep.safetensors').read_bytes() == b'fixture'
