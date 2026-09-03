# Week 3 Multi-File Context Coding Agent

## Description
A Python coding agent that reads multiple project files, understands the project context, identifies which files need changes, applies coordinated edits, creates backups, and runs tests.

## Project Structure

- agent/agent_runner.py
- sample_project/calculator.py
- sample_project/test_calculator.py
- sample_project/main.py

## Features

- Reads multiple Python files
- Builds project context
- Uses an LLM to identify required files
- Applies coordinated changes
- Creates `.bak` backups
- Runs pytest automatically

## Example Task

Add validation to the `divide()` function so division by zero raises `ValueError`, and update the test file.

## Testing

5 tests passed successfully.
