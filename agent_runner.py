import os
import json
import subprocess
from pathlib import Path

from openai import OpenAI


# PROJECT PATH

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR / "sample_project"


# API CLIENT

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Please set your Groq API key "
        "as an environment variable."
    )

client = OpenAI(
    api_key=api_key.strip(),
    base_url="https://api.groq.com/openai/v1"
)


# READ PYTHON FILES

def get_python_files():
    """Return all Python files in the sample project."""
    return list(PROJECT_DIR.glob("*.py"))


# CREATE FILE SUMMARY

def summarize_file(file_path):
    """Create a simple summary of a Python file."""

    content = file_path.read_text(encoding="utf-8")

    functions = []

    for line in content.splitlines():
        line = line.strip()

        if line.startswith("def "):
            function_name = line.split("(")[0].replace("def ", "")
            functions.append(function_name)

    return {
        "file": file_path.name,
        "functions": functions,
        "content": content
    }


def build_project_context():
    """Read all Python files and create project context."""

    context = []

    for file_path in get_python_files():
        context.append(summarize_file(file_path))

    return context


# ASK AI FOR EDIT PLAN

def ask_agent_to_edit(context, instruction):

    summaries = []

    for item in context:
        summaries.append({
            "file": item["file"],
            "functions": item["functions"]
        })

    system_prompt = """
You are a coding agent working on a small Python project.

Your job is to understand the project structure and decide which files
need to be changed based on the user's instruction.

Return ONLY valid JSON.

The JSON must have this structure:

{
    "files_to_edit": [
        {
            "file": "filename.py",
            "reason": "why this file needs to change",
            "changes": "what should be changed"
        }
    ]
}

Do not include markdown.
"""

    prompt = f"""
Project file summaries:

{json.dumps(summaries, indent=2)}

User instruction:

{instruction}

Identify every file that needs to be changed.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return json.loads(response.choices[0].message.content)


# GENERATE EDITED FILE

def generate_file_edit(file_name, current_content, instruction):

    system_prompt = """
You are editing an existing Python file.

Return ONLY the complete updated file content.
Do not use markdown code fences.
Do not explain anything.
Preserve existing functionality unless the user specifically asks
for a change.
"""

    prompt = f"""
File name:
{file_name}

Current file content:
{current_content}

User instruction:
{instruction}

Return the complete updated content of this file.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


# BACKUP FILE

def backup_file(file_path):

    backup_path = file_path.with_suffix(
        file_path.suffix + ".bak"
    )

    backup_path.write_text(
        file_path.read_text(encoding="utf-8"),
        encoding="utf-8"
    )

    return backup_path


# APPLY EDITS

def apply_edits(plan, context, instruction):

    for edit in plan["files_to_edit"]:

        file_name = edit["file"]
        file_path = PROJECT_DIR / file_name

        if not file_path.exists():
            print(f"File not found: {file_name}")
            continue

        print(f"\nEditing: {file_name}")
        print(f"Reason: {edit['reason']}")

        backup_path = backup_file(file_path)

        print(f"Backup created: {backup_path.name}")

        current_content = file_path.read_text(
            encoding="utf-8"
        )

        new_content = generate_file_edit(
            file_name,
            current_content,
            instruction
        )

        file_path.write_text(
            new_content,
            encoding="utf-8"
        )

        print(f"Updated: {file_name}")


# RUN TESTS

def run_tests():

    print("\nRunning tests...")

    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "test_calculator.py",
            "-v"
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=30
    )

    print("\n----- TEST OUTPUT -----")
    print(result.stdout)

    if result.stderr:
        print("\n----- TEST ERRORS -----")
        print(result.stderr)

    if result.returncode == 0:
        print("\nTESTS PASSED")
    else:
        print("\nTESTS FAILED")

    return result.returncode == 0


# MAIN AGENT

def main():

    print("===================================")
    print("      MULTI-FILE CODING AGENT")
    print("===================================")

    instruction = (
        "Add input validation to the divide function so it raises "
        "ValueError on division by zero, and update the test file "
        "to test for it."
    )

    print("\nUser instruction:")
    print(instruction)

    print("\n1. Reading project files...")

    context = build_project_context()

    for item in context:
        print(
            f"- {item['file']}: "
            f"{item['functions']}"
        )

    print("\n2. Asking AI which files need editing...")

    plan = ask_agent_to_edit(
        context,
        instruction
    )

    print("\nAI EDIT PLAN:")
    print(json.dumps(plan, indent=2))

    print("\n3. Applying coordinated edits...")

    apply_edits(
        plan,
        context,
        instruction
    )

    print("\n4. Verifying changes...")

    run_tests()


if __name__ == "__main__":
    main()