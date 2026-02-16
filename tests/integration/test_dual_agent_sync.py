"""
Integration Test: Dual Agent Sync (Cloud push → Local pull)
Verifies Cloud and Local agents sync via Git
"""
import pytest
import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.git_manager import GitManager
from agent_skills.git_sync_state import GitSyncStateManager


@pytest.fixture
def temp_vault():
    """Create temporary vault for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_vault_")
    vault_path = Path(temp_dir) / "vault"
    vault_path.mkdir()

    # Create vault structure
    (vault_path / "Inbox").mkdir()
    (vault_path / "Needs_Action").mkdir()
    (vault_path / "Logs" / "Cloud").mkdir(parents=True)
    (vault_path / "Logs" / "Local").mkdir(parents=True)

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_git_remote():
    """Create temporary bare Git repository (mock remote)"""
    temp_dir = tempfile.mkdtemp(prefix="test_remote_")
    remote_path = Path(temp_dir)

    # Initialize bare repo
    import git
    git.Repo.init(remote_path, bare=True)

    yield remote_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_cloud_push_local_pull(temp_vault, temp_git_remote):
    """
    Test: Cloud creates file → commits → pushes
          Local pulls → sees file
    """
    # Setup Cloud Git manager
    cloud_vault = temp_vault / "cloud"
    cloud_vault.mkdir()
    shutil.copytree(temp_vault, cloud_vault, dirs_exist_ok=True)

    cloud_git = GitManager(
        vault_path=str(cloud_vault),
        remote_url=str(temp_git_remote),
        branch="main"
    )

    # Setup Local Git manager
    local_vault = temp_vault / "local"
    local_vault.mkdir()

    # Cloud: Create test file
    test_file = cloud_vault / "Inbox" / "test_cloud_push.md"
    test_file.write_text("---\ntitle: Test Cloud Push\n---\nCloud created this file")

    # Cloud: Commit and push
    commit_hash = cloud_git.commit("test file", agent_id="cloud")
    assert commit_hash is not None, "Cloud commit should succeed"

    push_success = cloud_git.push(retries=1)
    assert push_success, "Cloud push should succeed"

    # Local: Clone from remote
    import git
    git.Repo.clone_from(str(temp_git_remote), str(local_vault))

    local_git = GitManager(
        vault_path=str(local_vault),
        remote_url=str(temp_git_remote),
        branch="main"
    )

    # Local: Pull
    pull_success, conflicts = local_git.pull(retries=1)
    assert pull_success, "Local pull should succeed"
    assert len(conflicts) == 0, "No conflicts expected"

    # Verify: Local sees Cloud's file
    local_test_file = local_vault / "Inbox" / "test_cloud_push.md"
    assert local_test_file.exists(), "Local should see Cloud's file"
    assert "Cloud created this file" in local_test_file.read_text()


@pytest.mark.integration
def test_git_sync_state_persistence(temp_vault):
    """
    Test: GitSyncState saves and loads correctly
    """
    state_manager = GitSyncStateManager(str(temp_vault))

    # Load default state
    state = state_manager.load_state()
    assert state.sync_status.value == "synced"

    # Update Cloud push
    state_manager.update_cloud_push("abc123def456" + "0" * 28)  # 40-char hash

    # Reload and verify
    state = state_manager.load_state()
    assert state.commit_hash_cloud.startswith("abc123")
    assert state.last_push_timestamp is not None

    # Update Local pull
    state_manager.update_local_pull("abc123def456" + "0" * 28, conflicts=[])

    # Reload and verify synced
    state = state_manager.load_state()
    assert state.is_synced(), "Should be synced when hashes match"


@pytest.mark.integration
def test_bidirectional_sync(temp_vault, temp_git_remote):
    """
    Test: Cloud pushes → Local pulls → Local commits → Local pushes → Cloud pulls
    """
    # Setup Cloud
    cloud_vault = temp_vault / "cloud"
    cloud_vault.mkdir()
    shutil.copytree(temp_vault, cloud_vault, dirs_exist_ok=True)

    import git
    cloud_repo = git.Repo.init(cloud_vault)
    cloud_repo.create_remote("origin", str(temp_git_remote))

    cloud_git = GitManager(str(cloud_vault), str(temp_git_remote), "main")

    # Cloud: Create initial commit
    (cloud_vault / "Inbox" / "initial.md").write_text("Initial file from Cloud")
    cloud_git.commit("initial commit", "cloud")
    cloud_git.push()

    # Local: Clone
    local_vault = temp_vault / "local"
    git.Repo.clone_from(str(temp_git_remote), str(local_vault))
    local_git = GitManager(str(local_vault), str(temp_git_remote), "main")

    # Local: Create file and push
    (local_vault / "Inbox" / "local_file.md").write_text("File from Local")
    local_git.commit("local commit", "local")
    local_git.push()

    # Cloud: Pull Local's changes
    cloud_git.pull()

    # Verify: Cloud sees Local's file
    assert (cloud_vault / "Inbox" / "local_file.md").exists()
    assert "File from Local" in (cloud_vault / "Inbox" / "local_file.md").read_text()
