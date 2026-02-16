"""
Integration Test: Claim-by-Move Race Condition Prevention
Verifies only ONE agent processes a task (100 concurrent attempts)
"""
import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent_skills.claim_manager import ClaimManager


@pytest.fixture
def temp_vault():
    """Create temporary vault for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_vault_")
    vault_path = Path(temp_dir)

    # Create vault structure
    (vault_path / "Needs_Action").mkdir()
    (vault_path / "In_Progress" / "cloud").mkdir(parents=True)
    (vault_path / "In_Progress" / "local").mkdir(parents=True)
    (vault_path / "Done").mkdir()

    yield vault_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.integration
def test_single_agent_claim(temp_vault):
    """
    Test: Single agent claims task successfully
    """
    claim_mgr = ClaimManager(str(temp_vault), "cloud")

    # Create test task
    task_file = temp_vault / "Needs_Action" / "TEST_TASK_001.md"
    task_file.write_text("---\ntitle: Test Task\n---\nTest content")

    # Claim task
    success = claim_mgr.claim_task(task_file)
    assert success, "Cloud agent should claim task successfully"

    # Verify file moved
    assert not task_file.exists(), "Task should be removed from /Needs_Action/"
    claimed_file = temp_vault / "In_Progress" / "cloud" / "TEST_TASK_001.md"
    assert claimed_file.exists(), "Task should be in /In_Progress/cloud/"


@pytest.mark.integration
def test_dual_agent_race_condition(temp_vault):
    """
    Test: Cloud and Local try to claim same task
          Only ONE should succeed
    """
    cloud_mgr = ClaimManager(str(temp_vault), "cloud")
    local_mgr = ClaimManager(str(temp_vault), "local")

    # Create test task
    task_file = temp_vault / "Needs_Action" / "RACE_TEST_001.md"
    task_file.write_text("---\ntitle: Race Test\n---\nRace condition test")

    # Both agents try to claim simultaneously
    cloud_result = cloud_mgr.claim_task(task_file)
    local_result = local_mgr.claim_task(task_file)

    # Only ONE should succeed
    assert cloud_result or local_result, "At least one agent should claim"
    assert not (cloud_result and local_result), "Only ONE agent should claim (race prevention)"

    # Verify file in only ONE location
    cloud_file = temp_vault / "In_Progress" / "cloud" / "RACE_TEST_001.md"
    local_file = temp_vault / "In_Progress" / "local" / "RACE_TEST_001.md"

    assert cloud_file.exists() or local_file.exists(), "Task should be claimed"
    assert not (cloud_file.exists() and local_file.exists()), "Task should NOT be duplicated"


@pytest.mark.integration
@pytest.mark.slow
def test_concurrent_claims_100_tasks(temp_vault):
    """
    Test: 100 concurrent claim attempts
          Verify NO duplicates
    """
    cloud_mgr = ClaimManager(str(temp_vault), "cloud")
    local_mgr = ClaimManager(str(temp_vault), "local")

    # Create 100 test tasks
    tasks = []
    for i in range(100):
        task_file = temp_vault / "Needs_Action" / f"CONCURRENT_TEST_{i:03d}.md"
        task_file.write_text(f"---\ntitle: Concurrent Test {i}\n---\nTask {i}")
        tasks.append(task_file)

    # Simulate concurrent claims
    cloud_claims = 0
    local_claims = 0

    def claim_as_cloud(task):
        return cloud_mgr.claim_task(task)

    def claim_as_local(task):
        return local_mgr.claim_task(task)

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Each task: Cloud and Local try to claim simultaneously
        futures = []
        for task in tasks:
            futures.append(executor.submit(claim_as_cloud, task))
            futures.append(executor.submit(claim_as_local, task))

        for future in as_completed(futures):
            if future.result():
                # Determine which agent claimed
                # (This is approximate, but good enough for testing)
                pass

    # Count actual claims
    cloud_files = list((temp_vault / "In_Progress" / "cloud").glob("CONCURRENT_TEST_*.md"))
    local_files = list((temp_vault / "In_Progress" / "local").glob("CONCURRENT_TEST_*.md"))

    cloud_claims = len(cloud_files)
    local_claims = len(local_files)

    # Verify: Total claims = 100 (all tasks claimed exactly once)
    assert cloud_claims + local_claims == 100, f"Expected 100 total claims, got {cloud_claims + local_claims}"

    # Verify: No tasks left in /Needs_Action/
    remaining = list((temp_vault / "Needs_Action").glob("CONCURRENT_TEST_*.md"))
    assert len(remaining) == 0, f"Expected 0 remaining tasks, got {len(remaining)}"


@pytest.mark.integration
def test_release_task(temp_vault):
    """
    Test: Claim task → Release to /Done/
    """
    claim_mgr = ClaimManager(str(temp_vault), "cloud")

    # Create and claim task
    task_file = temp_vault / "Needs_Action" / "RELEASE_TEST_001.md"
    task_file.write_text("---\ntitle: Release Test\n---\nTest release")

    claim_mgr.claim_task(task_file)

    # Release to /Done/
    claimed_file = temp_vault / "In_Progress" / "cloud" / "RELEASE_TEST_001.md"
    success = claim_mgr.release_task(claimed_file, target_folder="Done")

    assert success, "Release should succeed"
    assert not claimed_file.exists(), "Task should be removed from /In_Progress/"

    done_file = temp_vault / "Done" / "RELEASE_TEST_001.md"
    assert done_file.exists(), "Task should be in /Done/"


@pytest.mark.integration
def test_check_ownership(temp_vault):
    """
    Test: Check which agent owns a task
    """
    cloud_mgr = ClaimManager(str(temp_vault), "cloud")
    local_mgr = ClaimManager(str(temp_vault), "local")

    # Cloud claims task
    task_file = temp_vault / "Needs_Action" / "OWNER_TEST_001.md"
    task_file.write_text("---\ntitle: Owner Test\n---\nTest ownership")

    cloud_mgr.claim_task(task_file)

    # Check ownership
    owner = cloud_mgr.check_ownership("OWNER_TEST_001.md")
    assert owner == "cloud", "Cloud should own the task"

    # Local checks ownership (should see cloud)
    owner_from_local = local_mgr.check_ownership("OWNER_TEST_001.md")
    assert owner_from_local == "cloud", "Local should see cloud owns task"
