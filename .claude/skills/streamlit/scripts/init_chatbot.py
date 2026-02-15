#!/usr/bin/env python3
"""
Initialize a new Streamlit chatbot project.

Usage:
    python init_chatbot.py <project_name> [--template basic|advanced]
"""

import argparse
import shutil
from pathlib import Path
import sys

def init_chatbot_project(project_name: str, template: str = "basic"):
    """Initialize a new Streamlit chatbot project from templates."""

    # Get the skill's assets directory
    skill_dir = Path(__file__).parent.parent
    assets_dir = skill_dir / "assets"

    # Determine template source
    if template == "basic":
        template_dir = assets_dir / "basic-chatbot"
    elif template == "advanced":
        template_dir = assets_dir / "advanced-chatbot"
    else:
        print(f"Error: Unknown template '{template}'. Use 'basic' or 'advanced'.")
        sys.exit(1)

    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    # Create project directory in current working directory
    project_path = Path.cwd() / project_name

    if project_path.exists():
        print(f"Error: Directory '{project_name}' already exists.")
        sys.exit(1)

    # Copy template to new project
    print(f"Creating Streamlit chatbot project: {project_name}")
    print(f"Template: {template}")
    print(f"Location: {project_path}")

    shutil.copytree(template_dir, project_path)

    print(f"\n✅ Project created successfully!")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")

    if template == "advanced":
        print(f"2. cp .streamlit/secrets.toml.example .streamlit/secrets.toml")
        print(f"3. Edit .streamlit/secrets.toml with your API keys")
        print(f"4. pip install -r requirements.txt")
        print(f"5. streamlit run app.py")
    else:
        print(f"2. pip install -r requirements.txt")
        print(f"3. streamlit run app.py")
        print(f"4. Replace simulate_response() with your LLM integration")

    print(f"\n📚 For more info, see the README.md in your project directory")

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Streamlit chatbot project"
    )
    parser.add_argument(
        "project_name",
        help="Name of the project directory to create"
    )
    parser.add_argument(
        "--template",
        choices=["basic", "advanced"],
        default="basic",
        help="Template to use (basic or advanced). Default: basic"
    )

    args = parser.parse_args()

    init_chatbot_project(args.project_name, args.template)

if __name__ == "__main__":
    main()
