"""
Plan Executor - Ralph Wiggum Loop Implementation

This module implements the Ralph Wiggum loop for autonomous multi-step plan execution.
Features:
- Max 10 iterations before human escalation
- State persistence to vault/In_Progress/{plan_id}/state.md
- Dependency checking before step execution
- Retry logic (3 attempts with exponential backoff)
- Graceful error escalation to vault/Needs_Action/

Named "Ralph Wiggum loop" after the Simpsons character who innocently tries
things repeatedly until someone intervenes - fitting for our autonomous execution!

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import local modules
from agent_skills.mcp_client import get_mcp_client
from agent_skills.vault_parser import parse_plan_file, ExecutionState


async def execute_plan_ralph_wiggum_loop(plan_id: str, vault_path: str) -> bool:
    """
    Execute plan using Ralph Wiggum loop (max 10 iterations).

    Args:
        plan_id: Plan identifier (e.g., "PLAN_onboarding_2026-02-14")
        vault_path: Absolute path to vault root

    Returns:
        True if plan completed successfully, False if escalated or failed

    Exit Conditions:
        1. All steps completed → success
        2. Max iterations (10) reached → escalate to human
        3. Step blocked by unresolvable error → escalate to human
    """
    vault = Path(vault_path)
    plan_file = vault / "Plans" / f"{plan_id}.md"

    if not plan_file.exists():
        print(f"[plan_executor] Plan file not found: {plan_file}")
        return False

    # Load plan
    plan = parse_plan_file(str(plan_file))

    # Initialize or load execution state
    state_dir = vault / "In_Progress" / plan_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state.md"

    if state_file.exists():
        # Resume from previous execution
        state = _load_execution_state(str(state_file))
        print(f"[plan_executor] Resuming plan {plan_id} from step {state.current_step}")
    else:
        # Initialize new execution
        state = ExecutionState(
            plan_id=plan_id,
            current_step=1,
            iterations_remaining=int(os.getenv("MAX_PLAN_ITERATIONS", "10")),
            loop_start_time=datetime.now()
        )
        _save_execution_state(state, str(state_file))

    # Ralph Wiggum loop
    while state.iterations_remaining > 0:
        # Exit condition 1: All steps complete
        completed_count = sum(1 for step in plan.steps if step.status == "completed")
        if completed_count == len(plan.steps):
            print(f"[plan_executor] Plan {plan_id} completed! All {len(plan.steps)} steps done.")
            _finalize_plan(plan_file, vault, status="completed")
            _update_dashboard(vault, f"Plan: {plan.objective} - COMPLETED ✓")
            state_dir.rmdir()  # Cleanup state
            return True

        # Get current step
        if state.current_step > len(plan.steps):
            # Loop back to find next pending step
            state.current_step = 1

        step = plan.steps[state.current_step - 1]

        # Skip already completed steps
        if step.status == "completed":
            state.current_step += 1
            continue

        # Exit condition 2: Step blocked by dependencies
        if not _dependencies_met(step, plan.steps):
            print(f"[plan_executor] Step {step.step_num} blocked by dependencies")
            _mark_step_blocked(step, plan_file)
            _create_escalation(vault, plan_id, f"Step {step.step_num} blocked by unmet dependencies")
            return False

        # Execute step
        print(f"[plan_executor] Executing step {step.step_num}: {step.description}")

        try:
            result = await _execute_step(step, plan, vault)
            _mark_step_completed(step, plan_file)
            _log_mcp_action(vault, result, plan_id, step.step_num)

            # Move to next step
            state.current_step += 1
            state.last_action = step.description
            state.last_action_timestamp = datetime.now()

        except Exception as e:
            # Retry step (up to 3 times with exponential backoff)
            retry_count = int(os.getenv("PLAN_STEP_RETRY_COUNT", "3"))
            if step.retry_count < retry_count:
                step.retry_count += 1
                wait_time = 5 * (2 ** step.retry_count)  # 10s, 20s, 40s
                print(f"[plan_executor] Step {step.step_num} failed, retry {step.retry_count}/{retry_count} in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                # Step failed after max retries
                print(f"[plan_executor] Step {step.step_num} failed after {retry_count} retries: {e}")
                _mark_step_blocked(step, plan_file)
                _create_escalation(vault, plan_id, f"Step {step.step_num} failed: {e}")
                return False

        # Update state and decrement iterations
        state.iterations_remaining -= 1
        _save_execution_state(state, str(state_file))
        _update_dashboard(vault, f"Plan: {plan.objective} - Step {state.current_step}/{len(plan.steps)} executing")

    # Exit condition 3: Max iterations reached
    print(f"[plan_executor] Plan {plan_id} escalated: max iterations (10) reached")
    _create_escalation(vault, plan_id, "Max iterations (10) reached without completion")
    _finalize_plan(plan_file, vault, status="escalated")
    return False


async def _execute_step(step: Any, plan: Any, vault: Path) -> Dict[str, Any]:
    """
    Execute a single plan step (may involve MCP invocation or file creation).

    Args:
        step: PlanStep object
        plan: Plan object
        vault: Path to vault root

    Returns:
        Execution result dict

    Raises:
        Exception: On step execution failure
    """
    mcp_client = get_mcp_client(timeout=30)

    if step.action_type == "mcp_email":
        # Invoke email MCP
        params = step.action_params
        result = mcp_client.call_tool(
            mcp_server="email-mcp",
            tool_name="send_email",
            arguments={
                "to": params.get("to"),
                "subject": params.get("subject"),
                "body": params.get("body")
            }
        )
        return {"action": "mcp_email", "result": result}

    elif step.action_type == "mcp_whatsapp":
        # Invoke whatsapp MCP
        params = step.action_params
        result = mcp_client.call_tool(
            mcp_server="whatsapp-mcp",
            tool_name="send_message",
            arguments={
                "chat_id": params.get("chat_id"),
                "message": params.get("message")
            }
        )
        return {"action": "mcp_whatsapp", "result": result}

    elif step.action_type == "mcp_linkedin":
        # Invoke linkedin MCP
        params = step.action_params
        result = mcp_client.call_tool(
            mcp_server="linkedin-mcp",
            tool_name="create_post",
            arguments={
                "text": params.get("text"),
                "author_urn": os.getenv("LINKEDIN_AUTHOR_URN", "")
            }
        )
        return {"action": "mcp_linkedin", "result": result}

    elif step.action_type == "create_file":
        # Create file in vault
        params = step.action_params
        file_path = vault / params.get("file_path", "")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(params.get("content", ""))

        return {"action": "create_file", "result": {"file_path": str(file_path), "status": "created"}}

    elif step.action_type == "notify_human":
        # Create notification in vault/Needs_Action/
        params = step.action_params
        notification_file = vault / "Needs_Action" / f"{plan.plan_id}_notification_{step.step_num}.md"

        with open(notification_file, 'w', encoding='utf-8') as f:
            f.write(f"""---
plan_id: {plan.plan_id}
step_num: {step.step_num}
timestamp: {datetime.now().isoformat()}
---

# Human Notification Required

**Plan**: {plan.objective}
**Step**: {step.step_num} - {step.description}
**Message**: {params.get('message', 'Awaiting human action')}

Please complete this action manually and mark this step as done.
""")

        return {"action": "notify_human", "result": {"notification_file": str(notification_file)}}

    else:
        raise ValueError(f"Unknown action_type: {step.action_type}")


def _dependencies_met(step: Any, all_steps: List[Any]) -> bool:
    """Check if all step dependencies are completed"""
    for dep_step_num in step.dependencies:
        dep_step = next((s for s in all_steps if s.step_num == dep_step_num), None)
        if not dep_step or dep_step.status != "completed":
            return False
    return True


def _mark_step_completed(step: Any, plan_file: Path):
    """Update step status in Plan file (simplified - in production, use YAML update)"""
    step.status = "completed"
    # TODO: Update Plan file YAML frontmatter


def _mark_step_blocked(step: Any, plan_file: Path):
    """Mark step as blocked in Plan file"""
    step.status = "blocked"
    # TODO: Update Plan file YAML frontmatter


def _finalize_plan(plan_file: Path, vault: Path, status: str):
    """
    Finalize plan execution.

    For completed plans:
    - Move Plan.md to vault/Done/
    - Update Dashboard.md with completion message
    - Clean up vault/In_Progress/{plan_id}/

    For escalated plans:
    - Keep plan in vault/Plans/ with status updated
    - Create escalation file in vault/Needs_Action/
    """
    if status == "completed":
        # Move plan to Done/
        done_dir = vault / "Done"
        done_dir.mkdir(parents=True, exist_ok=True)

        destination = done_dir / plan_file.name
        if destination.exists():
            # If file already exists, append timestamp to avoid collision
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination = done_dir / f"{plan_file.stem}_{timestamp}{plan_file.suffix}"

        plan_file.rename(destination)
        print(f"[plan_executor] Plan moved to Done: {destination}")

        # Update Dashboard.md
        dashboard_file = vault / "Dashboard.md"
        if dashboard_file.exists():
            try:
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    dashboard_content = f.read()

                # Extract plan name from filename (e.g., PLAN_onboarding_2026-02-14.md -> onboarding)
                plan_name = plan_file.stem.replace("PLAN_", "").replace("_", " ")
                completion_message = f"\n- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Plan: {plan_name} - COMPLETED ✓"

                # Append to Recent Activity section or create one
                if "## Recent Activity" in dashboard_content:
                    # Insert after "## Recent Activity" header
                    dashboard_content = dashboard_content.replace(
                        "## Recent Activity\n",
                        f"## Recent Activity\n{completion_message}\n"
                    )
                else:
                    # Append at end
                    dashboard_content += f"\n## Recent Activity\n{completion_message}\n"

                with open(dashboard_file, 'w', encoding='utf-8') as f:
                    f.write(dashboard_content)

                print(f"[plan_executor] Dashboard updated with completion message")
            except Exception as e:
                print(f"[plan_executor] Warning: Failed to update Dashboard.md: {e}")

        # Clean up vault/In_Progress/{plan_id}/
        plan_id = plan_file.stem
        in_progress_dir = vault / "In_Progress" / plan_id
        if in_progress_dir.exists():
            try:
                # Remove all files in the directory
                for file in in_progress_dir.iterdir():
                    file.unlink()
                # Remove the directory itself
                in_progress_dir.rmdir()
                print(f"[plan_executor] Cleaned up In_Progress directory: {in_progress_dir}")
            except Exception as e:
                print(f"[plan_executor] Warning: Failed to clean up In_Progress directory: {e}")

    elif status == "escalated":
        # Plan stays in vault/Plans/ with status updated in frontmatter
        # Escalation file is created by _create_escalation()
        print(f"[plan_executor] Plan escalated: {plan_file.name}")

    else:
        print(f"[plan_executor] Unknown status for plan finalization: {status}")


def _create_escalation(vault: Path, plan_id: str, reason: str):
    """Create escalation file in vault/Needs_Action/"""
    escalation_file = vault / "Needs_Action" / f"plan_escalated_{plan_id}.md"

    with open(escalation_file, 'w', encoding='utf-8') as f:
        f.write(f"""---
plan_id: {plan_id}
escalation_reason: {reason}
timestamp: {datetime.now().isoformat()}
---

# Plan Escalation

**Plan ID**: {plan_id}
**Reason**: {reason}
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recovery Actions
1. Review plan file in vault/Plans/{plan_id}.md
2. Check execution state in vault/In_Progress/{plan_id}/state.md
3. Resolve blocking issues manually
4. Restart plan execution or simplify plan
""")


def _log_mcp_action(vault: Path, result: Dict, plan_id: str, step_num: int):
    """Log MCP action to vault/Logs/MCP_Actions/"""
    log_dir = vault / "Logs" / "MCP_Actions"
    log_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.md"

    log_entry = f"""
## Plan Execution at {datetime.now().strftime('%H:%M:%S')}
**Plan ID**: {plan_id}
**Step**: {step_num}
**Action**: {result.get('action', 'unknown')}
**Result**: {result.get('result', {})}
"""

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)


def _update_dashboard(vault: Path, message: str):
    """Update dashboard with plan progress (simplified)"""
    # In production, this would update Dashboard.md
    print(f"[dashboard] {message}")


def _load_execution_state(state_file: str) -> ExecutionState:
    """Load ExecutionState from file"""
    from agent_skills.vault_parser import parse_execution_state
    return parse_execution_state(state_file)


def _save_execution_state(state: ExecutionState, state_file: str):
    """Save ExecutionState to file"""
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, 'w', encoding='utf-8') as f:
        f.write(f"""---
plan_id: {state.plan_id}
current_step: {state.current_step}
iterations_remaining: {state.iterations_remaining}
last_action: {state.last_action}
last_action_timestamp: {state.last_action_timestamp.isoformat() if state.last_action_timestamp else 'null'}
loop_start_time: {state.loop_start_time.isoformat() if state.loop_start_time else 'null'}
---

# Execution State

**Current Step**: {state.current_step}
**Iterations Remaining**: {state.iterations_remaining}/10
**Last Action**: {state.last_action}
""")


# Example usage
if __name__ == "__main__":
    # Example: Execute plan
    asyncio.run(execute_plan_ralph_wiggum_loop(
        plan_id="PLAN_onboarding_2026-02-14",
        vault_path="vault"
    ))
