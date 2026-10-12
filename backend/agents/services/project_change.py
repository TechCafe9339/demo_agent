import json
from pathlib import Path

from django.conf import settings

from agents.providers.factory import (
    get_llm_provider,
)


class ProjectChangeService:

    MAX_FILE_SIZE = 120_000

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
        ).resolve()

    def _safe_path(
        self,
        root: Path,
        relative_path: str,
    ) -> Path:
        target = (root / relative_path).resolve()

        try:
            target.relative_to(root)

        except ValueError:
            raise ValueError(f"Unsafe project path: {relative_path}")

        return target

    def _read_existing_files(
        self,
        *,
        project,
        paths: list[str],
    ) -> list[dict]:
        root = self._workspace_root(project)

        files = []

        for relative_path in paths:
            path = self._safe_path(
                root,
                relative_path,
            )

            if not path.exists() or not path.is_file():
                continue

            if path.stat().st_size > self.MAX_FILE_SIZE:
                continue

            try:
                content = path.read_text(encoding="utf-8")

            except UnicodeDecodeError:
                continue

            files.append(
                {
                    "path": relative_path,
                    "content": content,
                }
            )

        return files

    def apply(
        self,
        *,
        project,
        change_request: str,
        affected_files: list[str],
        new_files: list[str],
    ) -> dict:

        root = self._workspace_root(project)

        if not root.exists():
            raise ValueError("Project workspace does not exist.")

        existing_files = self._read_existing_files(
            project=project,
            paths=affected_files,
        )

        allowed_paths = set(affected_files + new_files)

        schema = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                },
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                            },
                            "content": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "path",
                            "content",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "summary",
                "files",
            ],
            "additionalProperties": False,
        }

        source_text = "\n\n".join(
            (f"FILE: {item['path']}\n" f"```text\n" f"{item['content']}\n" f"```")
            for item in existing_files
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the code modification "
                    "engine for Prompt2Web.\n\n"
                    "Modify an existing generated "
                    "web application.\n\n"
                    "Rules:\n"
                    "- Only return files that must actually be written.\n"
                    "- Only use allowed file paths.\n"
                    "- Preserve unrelated functionality.\n"
                    "- Return complete file contents.\n"
                    "- File content must contain real newline characters.\n"
                    "- Never return literal backslash-n sequences as source formatting.\n"
                    "- For Next.js client components, the first line must be exactly "
                    '"use client";\n'
                    "- Return syntactically valid TypeScript/TSX.\n"
                    "- Do not use markdown fences inside file content.\n"
                    "- Do not invent additional paths.\n"
                    "- Keep changes minimal and focused."
                ),
            },
            {
                "role": "user",
                "content": f"""
PROJECT:
{project.name}

ORIGINAL REQUEST:
{project.initial_prompt}

REQUESTED CHANGE:
{change_request}

ALLOWED EXISTING FILES:
{affected_files}

ALLOWED NEW FILES:
{new_files}

CURRENT FILE CONTENTS:

{source_text}

Return the complete updated contents for every file
that must be written in order to implement the change.
""",
            },
        ]

        response = self.llm.generate(
            messages,
            temperature=0.1,
            json_schema=schema,
        )

        result = json.loads(response.content)

        written_files = []

        for file_result in result["files"]:
            relative_path = file_result["path"]

            if relative_path not in allowed_paths:
                raise ValueError(
                    (
                        "LLM attempted to modify "
                        "unauthorized file: "
                        f"{relative_path}"
                    )
                )

            target = self._safe_path(
                root,
                relative_path,
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            generated_content = self._normalize_generated_content(
                path=relative_path,
                content=file_result["content"],
            )

            target.write_text(
                generated_content,
                encoding="utf-8",
            )

            written_files.append(relative_path)

        return {
            "summary": result["summary"],
            "written_files": written_files,
        }

    def _normalize_generated_content(
        self,
        *,
        path: str,
        content: str,
    ) -> str:
        """
        Fix common LLM serialization mistakes without
        changing normal source-code strings.
        """

        # Qwen occasionally returns an entire source file
        # as one line containing literal "\\n" sequences.
        #
        # Only normalize when the output strongly looks
        # like an accidentally double-escaped source file.
        if "\\n" in content and content.count("\n") <= 2 and content.count("\\n") >= 3:
            content = (
                content.replace("\\r\\n", "\n")
                .replace("\\n", "\n")
                .replace("\\t", "\t")
            )

        # Fix common invalid Next.js client directives.
        if path.endswith(
            (
                ".tsx",
                ".ts",
                ".jsx",
                ".js",
            )
        ):
            stripped = content.lstrip()

            invalid_directives = [
                "useClient",
                "use client;",
                "'use client;",
                '"use client;',
            ]

            for invalid in invalid_directives:
                if stripped.startswith(invalid):
                    prefix_length = len(content) - len(stripped)

                    remainder = stripped[len(invalid) :].lstrip()

                    content = content[:prefix_length] + '"use client";\n\n' + remainder

                    break

        return content
