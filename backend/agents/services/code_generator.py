import json

from pydantic import ValidationError

from agents.prompts.code_generator import (
    CODE_GENERATOR_SYSTEM_PROMPT,
)

from agents.providers.factory import (
    get_llm_provider,
)

from agents.schemas.code_generation import (
    CodeGenerationResult,
)

from agents.models import PlanTask


class CodeGeneratorService:

    MAX_ATTEMPTS = 2

    def __init__(self):
        self.llm = get_llm_provider()

    def generate(
        self,
        *,
        task: PlanTask,
        application_specification: dict,
        file_tree: list[str],
        relevant_files: dict[str, str],
    ) -> CodeGenerationResult:

        payload = {
            "application_specification":
                application_specification,

            "task": {
                "id": task.task_number,
                "type": task.task_type,
                "title": task.title,
                "description": task.description,
                "files": task.files,
                "dependencies": task.dependencies,
            },

            "project_file_tree": file_tree,

            "relevant_files": relevant_files,
        }

        last_error = None

        for _ in range(
            self.MAX_ATTEMPTS
        ):
            try:
                return self._generate(
                    payload
                )

            except (
                ValueError,
                ValidationError,
            ) as exc:
                last_error = exc

        raise ValueError(
            "Code generation failed after "
            f"{self.MAX_ATTEMPTS} attempts."
        ) from last_error

    def _generate(
        self,
        payload: dict,
    ) -> CodeGenerationResult:

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": (
                        CODE_GENERATOR_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        payload,
                        indent=2,
                    ),
                },
            ],
            temperature=0.1,
        )

        if not response.content:
            raise ValueError(
                "Qwen returned an empty response."
            )

        data = self._parse_json(
            response.content
        )

        return (
            CodeGenerationResult
            .model_validate(data)
        )

    def _parse_json(
        self,
        content: str,
    ) -> dict:

        cleaned = content.strip()

        if cleaned.startswith(
            "```json"
        ):
            cleaned = cleaned[7:]

        elif cleaned.startswith(
            "```"
        ):
            cleaned = cleaned[3:]

        if cleaned.endswith(
            "```"
        ):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Qwen returned invalid code "
                "generation JSON.\n\n"
                f"Raw output:\n{content}"
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Code generation output "
                "must be a JSON object."
            )

        return data