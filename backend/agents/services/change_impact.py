import json
from pathlib import Path

from django.conf import settings

from agents.providers.factory import (
    get_llm_provider,
)


class ChangeImpactAnalyzer:

    MAX_FILES = 250

    def __init__(self):
        self.llm = get_llm_provider()

    def _workspace_root(
        self,
        project,
    ) -> Path:
        return (
            Path(settings.BASE_DIR).parent
            / "generated_workspaces"
            / f"project_{project.id}"
        )

    def _get_file_tree(
        self,
        project,
    ) -> list[str]:
        root = self._workspace_root(project)

        if not root.exists():
            return []

        ignored_directories = {
            "node_modules",
            ".next",
            "dist",
            ".git",
            "__pycache__",
            ".turbo",
        }

        ignored_files = {
            ".env",
            ".env.local",
            ".env.production",
            ".env.development",
        }

        files = []

        for path in root.rglob("*"):
            if len(files) >= self.MAX_FILES:
                break

            if not path.is_file():
                continue

            relative = path.relative_to(root)

            if any(part in ignored_directories for part in relative.parts):
                continue

            if path.name in ignored_files:
                continue

            if path.name.lower().startswith(".env."):
                continue

            files.append(relative.as_posix())

        return sorted(files)

    def analyze(
        self,
        *,
        project,
        change_request: str,
    ) -> dict:

        project_files = self._get_file_tree(project)

        schema = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                },
                "affected_files": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "new_files": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "risk": {
                    "type": "string",
                    "enum": [
                        "low",
                        "medium",
                        "high",
                    ],
                },
                "reason": {
                    "type": "string",
                },
            },
            "required": [
                "summary",
                "affected_files",
                "new_files",
                "risk",
                "reason",
            ],
            "additionalProperties": False,
        }

        files_text = "\n".join(project_files) if project_files else "No files found."

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a software "
                    "change-impact analyzer.\n\n"
                    "Analyze a requested change "
                    "against an existing project.\n\n"
                    "Rules:\n"
                    "- affected_files must contain "
                    "only existing files from the "
                    "provided file list.\n"
                    "- new_files may contain files "
                    "that should be created.\n"
                    "- Never invent existing paths.\n"
                    "- Keep the change scope minimal.\n"
                    "- Do not modify code.\n"
                    "- Return only structured JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""
PROJECT:
{project.name}

ORIGINAL REQUEST:
{project.initial_prompt}

CURRENT STATUS:
{project.status}

REQUESTED CHANGE:
{change_request}

EXISTING PROJECT FILES:
{files_text}

Determine:
1. Which existing files are affected.
2. Which new files may be required.
3. Risk level.
4. Why those files are affected.
""",
            },
        ]

        response = self.llm.generate(
            messages,
            temperature=0,
            json_schema=schema,
        )

        result = json.loads(response.content)

        existing_files = set(project_files)

        # Extra protection against
        # hallucinated existing paths.
        result["affected_files"] = [
            path for path in result["affected_files"] if path in existing_files
        ]

        return result
