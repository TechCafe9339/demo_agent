import json

from agents.prompts.repair import (
    REPAIR_SYSTEM_PROMPT,
)

from agents.providers.factory import (
    get_llm_provider,
)

from agents.schemas.repair import (
    RepairResult,
)


class RepairAgentService:

    MAX_ATTEMPTS = 2

    def __init__(self):
        self.llm = get_llm_provider()

    def repair(
        self,
        *,
        application_specification: dict,
        task: dict,
        errors: list[str],
        file_tree: list[str],
        relevant_files: dict[str, str],
    ) -> RepairResult:

        payload = {
            "application_specification": application_specification,
            "task": task,
            "validation_errors": errors,
            "project_file_tree": file_tree,
            "relevant_files": relevant_files,
        }

        last_error = None

        for attempt in range(self.MAX_ATTEMPTS):
            try:
                return self._generate(
                    payload,
                    previous_error=(
                        str(last_error)
                        if last_error
                        else None
                    ),
                )

            except ValueError as exc:
                last_error = exc

        raise ValueError(
            f"Repair generation failed after "
            f"{self.MAX_ATTEMPTS} attempts."
        ) from last_error


    def _generate(
        self,
        payload: dict,
        previous_error: str | None = None,
    ) -> RepairResult:

        messages = [
            {
                "role": "system",
                "content": REPAIR_SYSTEM_PROMPT,
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
            messages.append({
                "role": "user",
                "content": (
                    "Your previous response was invalid. "
                    "Return a valid JSON object matching "
                    "the required repair schema. "
                    "Do not return explanations or markdown. "
                    f"Previous error: {previous_error[:1000]}"
                ),
            })

        response = self.llm.generate(
            messages,
            temperature=0.1,
            json_mode=True,
        )

        if not response.content or not response.content.strip():
            raise ValueError(
                "Repair agent returned an empty response."
            )

        data = self._parse_json(response.content)

        return RepairResult.model_validate(data)

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
            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Repair agent returned "
                "invalid JSON.\n\n"
                f"{content}"
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Repair output must "
                "be a JSON object."
            )

        return data