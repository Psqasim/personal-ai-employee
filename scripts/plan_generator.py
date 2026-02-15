#!/usr/bin/env python3
"""
Plan Generator - Multi-Step Plan Detection and Generation

Monitors vault/Inbox/ for multi-step task keywords and generates execution plans.
The generated plans are sent to vault/Pending_Approval/Plans/ for human approval
before execution by the Ralph Wiggum loop.

Keywords Triggering Plan Generation:
- "plan", "onboard", "campaign", "project", "setup", "workflow", "process"

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T036 (plan detection + generation), T037 (step generation), T038 (approval request)
"""

import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add agent_skills to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills.vault_parser import parse_frontmatter


# T036: Multi-step keyword detection
MULTI_STEP_KEYWORDS = [
    "plan", "onboard", "campaign", "project", "setup",
    "workflow", "process", "automate", "sequence", "steps"
]


def detect_multi_step_task(task_file: Path) -> Optional[Dict[str, Any]]:
    """
    Detect if a task file contains multi-step keywords.

    Args:
        task_file: Path to task file in vault/Inbox/

    Returns:
        Task data dict if multi-step detected, None otherwise

    Keywords: plan, onboard, campaign, project, setup, workflow, process
    """
    try:
        frontmatter, body = parse_frontmatter(str(task_file))

        # Combine subject/title and body for keyword matching
        task_text = f"{frontmatter.get('subject', '')} {frontmatter.get('title', '')} {body}".lower()

        # Check for multi-step keywords
        if any(keyword in task_text for keyword in MULTI_STEP_KEYWORDS):
            return {
                "task_id": task_file.stem,
                "file_path": str(task_file),
                "subject": frontmatter.get("subject", frontmatter.get("title", "Untitled Task")),
                "description": body.strip(),
                "priority": frontmatter.get("priority", "Medium"),
                "frontmatter": frontmatter
            }

        return None

    except Exception as e:
        print(f"[plan_generator] Error parsing task file {task_file}: {e}")
        return None


def generate_plan(task_data: Dict[str, Any], company_handbook_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate multi-step Plan from task description.
    T036: Plan generation with Claude API

    Args:
        task_data: Task data from detect_multi_step_task()
        company_handbook_path: Path to Company_Handbook.md for context

    Returns:
        Plan dict with objective, steps, metadata

    Note: This is a simplified version. In production, this would:
    1. Call Claude API with task description + company context
    2. Parse Claude's response to extract objective and steps
    3. Validate step structure and dependencies

    For now, we'll use a template-based approach for reliability.
    """
    task_description = task_data["description"]
    subject = task_data["subject"]

    # Extract business context from handbook (if available)
    business_context = ""
    if company_handbook_path and Path(company_handbook_path).exists():
        try:
            with open(company_handbook_path, 'r', encoding='utf-8') as f:
                # Read first 500 chars for context (avoid loading huge files)
                business_context = f.read(500)
        except Exception:
            pass

    # T037: Generate plan steps from task description
    # In production, this would use Claude API. For reliability, using pattern matching:
    steps = generate_plan_steps(task_description, subject)

    # Create plan data structure
    plan_id = f"PLAN_{_slugify(subject)}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"

    plan = {
        "plan_id": plan_id,
        "objective": subject,
        "steps": steps,
        "total_steps": len(steps),
        "completed_steps": 0,
        "status": "awaiting_approval",
        "approval_required": True,
        "estimated_time": _estimate_plan_time(steps),
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "iteration_count": 0,
        "original_task_id": task_data["task_id"]
    }

    return plan


def generate_plan_steps(task_description: str, subject: str) -> List[Dict[str, Any]]:
    """
    T037: Generate PlanStep array from task description.

    This is a simplified pattern-matching approach. In production, this would:
    1. Use Claude API to intelligently parse task into discrete steps
    2. Identify action types (email, whatsapp, linkedin, file creation)
    3. Detect dependencies between steps
    4. Extract parameters for each action

    Args:
        task_description: Full task description text
        subject: Task subject/title

    Returns:
        List of PlanStep dicts

    Pattern Matching Logic:
    - "email" → mcp_email step
    - "whatsapp" → mcp_whatsapp step
    - "linkedin" or "post" → mcp_linkedin step
    - "calendar" or "meeting" → notify_human (no calendar MCP yet)
    - Default → notify_human for manual handling
    """
    steps = []
    step_num = 1

    # Detect explicit numbered steps in description
    # Pattern: "1. Do X", "2. Do Y", etc.
    numbered_steps = re.findall(r'\d+\.\s+(.+?)(?=\d+\.|$)', task_description, re.DOTALL)

    if numbered_steps:
        # Use explicitly numbered steps from user
        for step_text in numbered_steps:
            step_text = step_text.strip()
            if not step_text:
                continue

            # Determine action type from step text
            action_type, action_params = _infer_action_from_text(step_text)

            steps.append({
                "step_num": step_num,
                "description": step_text[:200],  # Truncate long descriptions
                "action_type": action_type,
                "action_params": action_params,
                "dependencies": _infer_dependencies(step_num, steps),
                "status": "pending",
                "mcp_action_log_id": None,
                "retry_count": 0
            })
            step_num += 1
    else:
        # Fallback: Create single notify_human step for complex tasks
        steps.append({
            "step_num": 1,
            "description": f"{subject} - Review and execute manually",
            "action_type": "notify_human",
            "action_params": {
                "message": f"Plan created for: {subject}\n\nDescription:\n{task_description[:500]}\n\nPlease review and execute steps manually."
            },
            "dependencies": [],
            "status": "pending",
            "mcp_action_log_id": None,
            "retry_count": 0
        })

    return steps


def _infer_action_from_text(step_text: str) -> tuple[str, Dict[str, Any]]:
    """
    T037: Infer action type and parameters from step description text.

    Args:
        step_text: Step description text

    Returns:
        (action_type, action_params) tuple

    Action Type Detection:
    - Contains "email" + "@" → mcp_email
    - Contains "whatsapp" or "message" → mcp_whatsapp
    - Contains "linkedin" or "post" → mcp_linkedin
    - Contains "file" or "document" → create_file
    - Default → notify_human
    """
    step_lower = step_text.lower()

    # Email detection
    if "email" in step_lower and "@" in step_text:
        # Extract email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', step_text)
        to_email = email_match.group(0) if email_match else "unknown@example.com"

        # Extract subject (look for "re:" or quoted text)
        subject_match = re.search(r'(re:|subject:)\s*["\']?([^"\']+)["\']?', step_text, re.IGNORECASE)
        subject = subject_match.group(2) if subject_match else "Follow-up"

        return ("mcp_email", {
            "to": to_email,
            "subject": subject,
            "body": f"[AI will generate appropriate body based on context]\n\nOriginal request: {step_text[:200]}"
        })

    # WhatsApp detection
    elif "whatsapp" in step_lower or ("message" in step_lower and "send" in step_lower):
        # Extract contact name (look for "to X" pattern)
        contact_match = re.search(r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', step_text)
        contact = contact_match.group(1) if contact_match else "Contact"

        return ("mcp_whatsapp", {
            "chat_id": _slugify(contact),
            "message": f"[AI will generate message]\n\nContext: {step_text[:200]}"
        })

    # LinkedIn detection
    elif "linkedin" in step_lower or "post" in step_lower:
        return ("mcp_linkedin", {
            "text": f"[AI will generate LinkedIn post]\n\nTopic: {step_text[:200]}"
        })

    # File creation detection
    elif "file" in step_lower or "document" in step_lower or "create" in step_lower:
        # Extract filename if mentioned
        filename_match = re.search(r'([A-Za-z0-9_-]+\.md)', step_text)
        filename = filename_match.group(1) if filename_match else "output.md"

        return ("create_file", {
            "file_path": f"vault/Plans/{filename}",
            "content": f"# File Created by Plan\n\n{step_text}\n\nGenerated: {datetime.now().isoformat()}"
        })

    # Default: notify human for manual handling
    else:
        return ("notify_human", {
            "message": step_text
        })


def _infer_dependencies(current_step_num: int, previous_steps: List[Dict]) -> List[int]:
    """
    T037: Infer step dependencies from context.

    Simple heuristic: Each step depends on the previous step (sequential execution)
    unless it's the first step.

    In production, Claude API would analyze step relationships and detect:
    - Parallel steps (no dependencies)
    - Complex dependencies (step 3 depends on steps 1 AND 2)

    Args:
        current_step_num: Current step number (1-indexed)
        previous_steps: List of previously generated steps

    Returns:
        List of step_num values this step depends on
    """
    if current_step_num == 1:
        return []  # First step has no dependencies
    else:
        return [current_step_num - 1]  # Depend on previous step (sequential)


def create_approval_request(plan: Dict[str, Any], vault_path: str):
    """
    T038: Create approval request file in vault/Pending_Approval/Plans/.

    The approval request contains:
    - Plan summary (objective, steps count)
    - Steps preview (first 3 steps)
    - Human approval instruction (move to vault/Approved/Plans/)

    Args:
        plan: Plan dict from generate_plan()
        vault_path: Absolute path to vault root
    """
    vault = Path(vault_path)
    pending_approval_plans = vault / "Pending_Approval" / "Plans"
    pending_approval_plans.mkdir(parents=True, exist_ok=True)

    # Create approval request file
    approval_file = pending_approval_plans / f"{plan['plan_id']}_approval.md"

    # Generate steps preview (first 3 steps)
    steps_preview = ""
    for i, step in enumerate(plan['steps'][:3], 1):
        steps_preview += f"{i}. {step['description'][:100]}\n"

    if len(plan['steps']) > 3:
        steps_preview += f"... and {len(plan['steps']) - 3} more steps\n"

    # Write approval request
    content = f"""---
plan_id: {plan['plan_id']}
objective: {plan['objective']}
total_steps: {plan['total_steps']}
estimated_time: {plan['estimated_time']}
status: awaiting_approval
created_at: {plan['created_at']}
---

# Plan Approval Request

**Objective**: {plan['objective']}
**Total Steps**: {plan['total_steps']}
**Estimated Time**: {plan['estimated_time']}

## Steps Preview

{steps_preview}

## Approval Instructions

To approve this plan for autonomous execution:
1. Review the full plan details in `vault/Plans/{plan['plan_id']}.md`
2. **Move this file to `vault/Approved/Plans/`** to authorize execution
3. The Ralph Wiggum loop will execute all steps autonomously (max 10 iterations)

To reject this plan:
- Move this file to `vault/Rejected/` and the plan will be archived

## Safety Notes

- All MCP actions (email, WhatsApp, LinkedIn) require explicit approval
- Plan execution will be logged to `vault/Logs/Plan_Execution/`
- If any step fails after 3 retries, the plan will escalate to `vault/Needs_Action/`
- Max 10 iterations before automatic escalation to human review

**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    with open(approval_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[plan_generator] Approval request created: {approval_file.name}")


def save_plan_file(plan: Dict[str, Any], vault_path: str):
    """
    Save Plan.md to vault/Plans/ directory.

    Args:
        plan: Plan dict from generate_plan()
        vault_path: Absolute path to vault root
    """
    vault = Path(vault_path)
    plans_dir = vault / "Plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    plan_file = plans_dir / f"{plan['plan_id']}.md"

    # Generate steps markdown
    steps_md = ""
    for step in plan['steps']:
        status_icon = "x" if step['status'] == "completed" else " "
        deps = f" (Dependencies: {', '.join(map(str, step['dependencies']))})" if step['dependencies'] else ""
        steps_md += f"- [{status_icon}] Step {step['step_num']}: {step['description']}{deps}\n"

    # Write plan file
    content = f"""---
plan_id: {plan['plan_id']}
objective: {plan['objective']}
total_steps: {plan['total_steps']}
completed_steps: {plan['completed_steps']}
status: {plan['status']}
approval_required: {plan['approval_required']}
estimated_time: {plan['estimated_time']}
created_at: {plan['created_at']}
started_at: {plan['started_at']}
completed_at: {plan['completed_at']}
iteration_count: {plan['iteration_count']}
original_task_id: {plan.get('original_task_id', 'unknown')}
steps:
"""

    # Add steps as YAML array
    for step in plan['steps']:
        content += f"""  - step_num: {step['step_num']}
    description: {step['description']}
    action_type: {step['action_type']}
    action_params: {step['action_params']}
    dependencies: {step['dependencies']}
    status: {step['status']}
    mcp_action_log_id: {step['mcp_action_log_id']}
    retry_count: {step['retry_count']}
"""

    content += f"""---

# Plan: {plan['objective']}

## Objective
{plan['objective']}

## Steps

{steps_md}

## Progress

**Status**: {plan['status']}
**Completed**: {plan['completed_steps']}/{plan['total_steps']} steps
**Iterations Used**: {plan['iteration_count']}/10
**Created**: {plan['created_at']}
**Started**: {plan['started_at'] or 'Not started'}

## Approval

This plan requires human approval before execution.
See `vault/Pending_Approval/Plans/{plan['plan_id']}_approval.md` for approval instructions.
"""

    with open(plan_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[plan_generator] Plan file saved: {plan_file.name}")


def monitor_inbox_for_plans(vault_path: str, poll_interval: int = 120):
    """
    Monitor vault/Inbox/ for multi-step tasks and generate plans.

    Args:
        vault_path: Absolute path to vault root
        poll_interval: Seconds between polls (default: 120)
    """
    vault = Path(vault_path)
    inbox_dir = vault / "Inbox"
    company_handbook = vault / "Company_Handbook.md"

    print(f"[plan_generator] Starting plan generator (poll interval: {poll_interval}s)")
    print(f"[plan_generator] Monitoring: {inbox_dir}")
    print(f"[plan_generator] Output: vault/Plans/ and vault/Pending_Approval/Plans/")

    processed_tasks = set()  # Track processed task IDs

    while True:
        try:
            # Scan inbox for task files
            if inbox_dir.exists():
                for task_file in inbox_dir.glob("*.md"):
                    task_id = task_file.stem

                    # Skip already processed
                    if task_id in processed_tasks:
                        continue

                    # Detect multi-step task (T036)
                    task_data = detect_multi_step_task(task_file)

                    if task_data:
                        print(f"[plan_generator] Multi-step task detected: {task_id}")

                        # Generate plan (T036, T037)
                        plan = generate_plan(
                            task_data,
                            company_handbook_path=str(company_handbook) if company_handbook.exists() else None
                        )

                        # Save plan file to vault/Plans/
                        save_plan_file(plan, vault_path)

                        # Create approval request (T038)
                        create_approval_request(plan, vault_path)

                        print(f"[plan_generator] Plan created: {plan['plan_id']}")
                        processed_tasks.add(task_id)

        except Exception as e:
            print(f"[plan_generator] Error during plan generation: {e}")
            import traceback
            traceback.print_exc()

        # Wait before next poll
        time.sleep(poll_interval)


# Utility functions

def _slugify(text: str) -> str:
    """Convert text to slug (lowercase, hyphens, no special chars)"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')[:50]  # Max 50 chars


def _estimate_plan_time(steps: List[Dict]) -> str:
    """
    Estimate plan execution time based on step count and action types.

    Simple heuristic:
    - mcp_email, mcp_whatsapp, mcp_linkedin: 2 min/step
    - create_file: 30 sec/step
    - notify_human: 5 min/step (requires human action)
    """
    total_minutes = 0
    for step in steps:
        action_type = step['action_type']
        if action_type in ["mcp_email", "mcp_whatsapp", "mcp_linkedin"]:
            total_minutes += 2
        elif action_type == "create_file":
            total_minutes += 0.5
        elif action_type == "notify_human":
            total_minutes += 5
        else:
            total_minutes += 1  # Unknown action type

    if total_minutes < 60:
        return f"{int(total_minutes)} minutes"
    else:
        hours = total_minutes / 60
        return f"{hours:.1f} hours"


# Main entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plan Generator - Multi-Step Task Detection")
    parser.add_argument("--vault", default="vault", help="Path to vault directory")
    parser.add_argument("--interval", type=int, default=120, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run once and exit (for testing)")

    args = parser.parse_args()

    vault_path = os.path.abspath(args.vault)

    if args.once:
        # Single scan mode (for testing)
        print(f"[plan_generator] Single scan mode - checking {vault_path}/Inbox/")

        # TODO: Implement single scan logic
        print("[plan_generator] Single scan complete")
    else:
        # Continuous monitoring mode
        monitor_inbox_for_plans(vault_path, poll_interval=args.interval)
