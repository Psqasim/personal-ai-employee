#!/usr/bin/env python3
"""
GitHub Actions Workflow Validator - Validates workflow YAML files

Usage:
    validate_workflow.py <workflow_file>
    validate_workflow.py .github/workflows/ci.yml
    validate_workflow.py --all  # Validate all workflows in .github/workflows/

Checks:
    - Valid YAML syntax
    - Required fields (name, on, jobs)
    - Valid trigger events
    - Job structure validation
    - Common issues and best practices

Examples:
    python scripts/validate_workflow.py .github/workflows/ci.yml
    python scripts/validate_workflow.py --all
"""

import sys
import argparse
from pathlib import Path
import yaml


VALID_EVENTS = {
    "push", "pull_request", "pull_request_target", "workflow_dispatch",
    "workflow_call", "schedule", "release", "issues", "issue_comment",
    "create", "delete", "deployment", "deployment_status", "fork",
    "gollum", "label", "member", "milestone", "page_build", "project",
    "project_card", "project_column", "public", "registry_package",
    "repository_dispatch", "status", "watch", "workflow_run"
}

COMMON_ACTIONS = {
    "actions/checkout",
    "actions/setup-python",
    "actions/setup-node",
    "actions/cache",
    "actions/upload-artifact",
    "actions/download-artifact",
}


class ValidationError:
    def __init__(self, message: str, severity: str = "error"):
        self.message = message
        self.severity = severity  # error, warning, info

    def __str__(self):
        icon = {"error": "X", "warning": "!", "info": "i"}[self.severity]
        return f"[{icon}] {self.message}"


def validate_yaml_syntax(content: str) -> tuple[dict | None, list[ValidationError]]:
    """Validate YAML syntax."""
    errors = []
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            errors.append(ValidationError("Workflow must be a YAML dictionary"))
            return None, errors
        return data, errors
    except yaml.YAMLError as e:
        errors.append(ValidationError(f"Invalid YAML syntax: {e}"))
        return None, errors


def validate_required_fields(workflow: dict) -> list[ValidationError]:
    """Validate required top-level fields."""
    errors = []

    if "name" not in workflow:
        errors.append(ValidationError("Missing 'name' field", "warning"))

    if "on" not in workflow:
        errors.append(ValidationError("Missing 'on' field (triggers)"))

    if "jobs" not in workflow:
        errors.append(ValidationError("Missing 'jobs' field"))
    elif not isinstance(workflow["jobs"], dict):
        errors.append(ValidationError("'jobs' must be a dictionary"))
    elif not workflow["jobs"]:
        errors.append(ValidationError("'jobs' cannot be empty"))

    return errors


def validate_triggers(workflow: dict) -> list[ValidationError]:
    """Validate trigger events."""
    errors = []

    if "on" not in workflow:
        return errors

    triggers = workflow["on"]

    # Handle string trigger
    if isinstance(triggers, str):
        triggers = [triggers]

    # Handle list of triggers
    if isinstance(triggers, list):
        for trigger in triggers:
            if trigger not in VALID_EVENTS:
                errors.append(ValidationError(f"Unknown trigger event: {trigger}", "warning"))

    # Handle dict triggers
    if isinstance(triggers, dict):
        for trigger in triggers.keys():
            if trigger not in VALID_EVENTS:
                errors.append(ValidationError(f"Unknown trigger event: {trigger}", "warning"))

        # Check push/PR branch filters
        for event in ["push", "pull_request"]:
            if event in triggers and isinstance(triggers[event], dict):
                event_config = triggers[event]
                if "branches" in event_config and "branches-ignore" in event_config:
                    errors.append(ValidationError(
                        f"Cannot use both 'branches' and 'branches-ignore' in {event}",
                        "error"
                    ))

    return errors


def validate_jobs(workflow: dict) -> list[ValidationError]:
    """Validate job definitions."""
    errors = []

    if "jobs" not in workflow or not isinstance(workflow["jobs"], dict):
        return errors

    for job_name, job in workflow["jobs"].items():
        if not isinstance(job, dict):
            errors.append(ValidationError(f"Job '{job_name}' must be a dictionary"))
            continue

        # Check runs-on
        if "runs-on" not in job and "uses" not in job:
            errors.append(ValidationError(f"Job '{job_name}' missing 'runs-on'"))

        # Check steps (unless it's a reusable workflow call)
        if "uses" not in job:
            if "steps" not in job:
                errors.append(ValidationError(f"Job '{job_name}' missing 'steps'"))
            elif not isinstance(job["steps"], list):
                errors.append(ValidationError(f"Job '{job_name}' steps must be a list"))
            elif not job["steps"]:
                errors.append(ValidationError(f"Job '{job_name}' has no steps"))
            else:
                # Validate steps
                for i, step in enumerate(job["steps"]):
                    step_errors = validate_step(job_name, i, step)
                    errors.extend(step_errors)

        # Check needs references
        if "needs" in job:
            needs = job["needs"]
            if isinstance(needs, str):
                needs = [needs]
            for needed_job in needs:
                if needed_job not in workflow["jobs"]:
                    errors.append(ValidationError(
                        f"Job '{job_name}' needs non-existent job '{needed_job}'"
                    ))

    return errors


def validate_step(job_name: str, step_index: int, step: dict) -> list[ValidationError]:
    """Validate a single step."""
    errors = []

    if not isinstance(step, dict):
        errors.append(ValidationError(f"Job '{job_name}' step {step_index} must be a dictionary"))
        return errors

    # Must have either 'uses' or 'run'
    if "uses" not in step and "run" not in step:
        errors.append(ValidationError(
            f"Job '{job_name}' step {step_index} must have 'uses' or 'run'"
        ))

    # Check action versions
    if "uses" in step:
        action = step["uses"]
        if "@" not in action and not action.startswith("./"):
            errors.append(ValidationError(
                f"Job '{job_name}' step {step_index}: Action '{action}' should specify version",
                "warning"
            ))

    return errors


def validate_best_practices(workflow: dict) -> list[ValidationError]:
    """Check for best practices."""
    errors = []

    # Check for timeout-minutes on jobs
    if "jobs" in workflow:
        for job_name, job in workflow["jobs"].items():
            if isinstance(job, dict) and "timeout-minutes" not in job:
                errors.append(ValidationError(
                    f"Job '{job_name}' should have 'timeout-minutes' set",
                    "info"
                ))

    # Check for concurrency settings
    if "concurrency" not in workflow:
        errors.append(ValidationError(
            "Consider adding 'concurrency' to prevent duplicate runs",
            "info"
        ))

    return errors


def validate_workflow(file_path: Path) -> tuple[bool, list[ValidationError]]:
    """Validate a workflow file."""
    all_errors = []

    # Read file
    try:
        content = file_path.read_text()
    except Exception as e:
        return False, [ValidationError(f"Cannot read file: {e}")]

    # Validate YAML syntax
    workflow, errors = validate_yaml_syntax(content)
    all_errors.extend(errors)
    if workflow is None:
        return False, all_errors

    # Validate structure
    all_errors.extend(validate_required_fields(workflow))
    all_errors.extend(validate_triggers(workflow))
    all_errors.extend(validate_jobs(workflow))
    all_errors.extend(validate_best_practices(workflow))

    # Determine if valid (no errors, warnings are ok)
    has_errors = any(e.severity == "error" for e in all_errors)

    return not has_errors, all_errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate GitHub Actions workflow files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("workflow_file", nargs="?",
                        help="Workflow file to validate")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Validate all workflows in .github/workflows/")

    args = parser.parse_args()

    if args.all:
        workflows_dir = Path(".github/workflows")
        if not workflows_dir.exists():
            print("No .github/workflows directory found")
            sys.exit(1)

        files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        if not files:
            print("No workflow files found")
            sys.exit(1)
    elif args.workflow_file:
        files = [Path(args.workflow_file)]
    else:
        parser.print_help()
        sys.exit(1)

    all_valid = True

    for file_path in files:
        print(f"\nValidating: {file_path}")
        print("-" * 50)

        valid, errors = validate_workflow(file_path)

        if errors:
            for error in errors:
                print(f"  {error}")
        else:
            print("  No issues found")

        if valid:
            print(f"  Result: VALID")
        else:
            print(f"  Result: INVALID")
            all_valid = False

    print("\n" + "=" * 50)
    if all_valid:
        print("All workflows are valid")
        sys.exit(0)
    else:
        print("Some workflows have errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
