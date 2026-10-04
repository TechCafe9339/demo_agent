import json

from agents.prompts.code_generator import (
    CODE_GENERATOR_SYSTEM_PROMPT,
)

from agents.providers.factory import (
    get_llm_provider,
)

from agents.schemas.code_generation import (
    CodeGenerationResult,
)


class CodeGeneratorService:

    MAX_ATTEMPTS = 3

    def __init__(self):
        self.llm = get_llm_provider()

    def generate(
        self,
        *,
        task,
        application_specification: dict,
        file_tree: list[str],
        relevant_files: dict[str, str],
    ) -> CodeGenerationResult:

        payload = {
            "application_specification": application_specification,
            "task": {
                "id": task.id,
                "task_number": task.task_number,
                "type": task.task_type,
                "title": task.title,
                "description": task.description,
                "files": task.files,
                "dependencies": task.dependencies,
            },
            "project_file_tree": file_tree,
            "relevant_files": relevant_files,
        }

        last_error: Exception | None = None

        for _ in range(self.MAX_ATTEMPTS):
            try:
                return self._generate(
                    payload,
                    previous_error=(str(last_error) if last_error else None),
                )

            except ValueError as exc:
                last_error = exc

        raise ValueError(
            "Code generation failed after "
            f"{self.MAX_ATTEMPTS} attempts. "
            f"Last error: {last_error}"
        ) from last_error

    def _generate(
        self,
        payload: dict,
        previous_error: str | None = None,
    ) -> CodeGenerationResult:

        messages = [
            {
                "role": "system",
                "content": CODE_GENERATOR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    payload,
                    indent=2,
                ),
            },
        ]

        if previous_error:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous output was rejected.\n\n"
                        f"Reason:\n"
                        f"{previous_error[:3000]}\n\n"
                        "Regenerate the task correctly.\n\n"
                        "STRICT REQUIREMENTS:\n"
                        '- "summary" MUST be a string.\n'
                        '- "operations" MUST be an array.\n'
                        "- Every write_file operation must include "
                        '"operation", "path", and "content".\n'
                        "- Do NOT import PrismaClient from "
                        "@prisma/client.\n"
                        "- Do NOT instantiate PrismaClient.\n"
                        '- Do NOT use "@/..." imports.\n'
                        "- Do NOT import individual generated "
                        "Prisma model files.\n"
                        "- Reuse the existing shared Prisma "
                        "instance.\n"
                        "- Use existing project files and "
                        "conventions.\n"
                        "- Relative NodeNext imports must "
                        "include .js.\n"
                        "- Return ONLY valid JSON."
                    ),
                }
            )

        response = self.llm.generate(
            messages,
            temperature=0.1,
            json_schema=(CodeGenerationResult.model_json_schema()),
        )

        if not response.content or not response.content.strip():
            raise ValueError("Code generator returned " "an empty response.")

        data = self._parse_json(response.content)

        try:
            result = CodeGenerationResult.model_validate(data)

        except Exception as exc:
            raise ValueError(
                "Generated JSON did not match "
                "CodeGenerationResult schema.\n"
                f"Validation error: {exc}\n\n"
                f"Raw response:\n"
                f"{response.content[:4000]}"
            ) from exc

        self._validate_generated_architecture(result)

        return result

    def _parse_json(
        self,
        content: str,
    ) -> dict:

        cleaned = content.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Qwen returned invalid "
                "code-generation JSON.\n\n"
                f"Raw output:\n{content}"
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError("Code-generation output " "must be a JSON object.")

        return data

    def _validate_generated_architecture(
        self,
        result: CodeGenerationResult,
    ) -> None:

        violations: list[str] = []

        for operation in result.operations:

            if operation.operation != "write_file":
                continue

            path = operation.path
            content = operation.content or ""

            if not path.startswith("backend/src/"):
                continue

            normalized = content.replace(
                "'",
                '"',
            )

            if '"@prisma/client"' in normalized and "PrismaClient" in normalized:
                violations.append(
                    f"{path}: importing "
                    "PrismaClient from "
                    "@prisma/client is forbidden. "
                    "Reuse the shared prisma instance."
                )

            if "new PrismaClient(" in content:
                violations.append(f"{path}: " "new PrismaClient() " "is forbidden.")

            if 'from "@/' in normalized:
                violations.append(f"{path}: " "@/ path aliases " "are forbidden.")

            if "generated/prisma/models/" in content:
                violations.append(
                    f"{path}: importing "
                    "individual generated Prisma "
                    "model files is forbidden."
                )

            if "backend/src/generated/prisma" in content:
                violations.append(
                    f"{path}: do not import "
                    "Prisma using project-root "
                    "absolute-style paths."
                )

        if violations:
            raise ValueError("ARCHITECTURE_VIOLATION:\n" + "\n".join(violations))
