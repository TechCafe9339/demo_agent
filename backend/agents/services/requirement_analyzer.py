import json

from pydantic import ValidationError

from agents.prompts.requirements import (
    REQUIREMENT_ANALYZER_SYSTEM_PROMPT,
)
from agents.providers.factory import (
    get_llm_provider,
)
from agents.schemas.requirements import (
    ApplicationSpecification,
)


class RequirementAnalyzer:
    MAX_ATTEMPTS = 2

    def __init__(self):
        self.llm = get_llm_provider()

    def analyze(
        self,
        user_prompt: str,
    ) -> ApplicationSpecification:

        if not user_prompt or not user_prompt.strip():
            raise ValueError(
                "User prompt cannot be empty."
            )

        last_error = None

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):
            try:
                return self._generate_specification(
                    user_prompt=user_prompt.strip(),
                )

            except (
                ValueError,
                ValidationError,
            ) as exc:
                last_error = exc

        raise ValueError(
            "Requirement analysis failed after "
            f"{self.MAX_ATTEMPTS} attempts."
        ) from last_error

    def _generate_specification(
        self,
        user_prompt: str,
    ) -> ApplicationSpecification:

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": (
                        REQUIREMENT_ANALYZER_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
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

        specification = (
            ApplicationSpecification.model_validate(
                data
            )
        )

        self._validate_stack(
            specification
        )

        return specification

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
                "Qwen did not return valid JSON.\n\n"
                f"Raw output:\n{content}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Qwen returned valid JSON, "
                "but the root value is not an object."
            )

        return data

    def _validate_stack(
        self,
        specification: ApplicationSpecification,
    ) -> None:

        stack = specification.stack

        expected = {
            "frontend": "nextjs",
            "backend": "express",
            "database": "mysql",
            "orm": "prisma",
            "language": "typescript",
        }

        actual = {
            "frontend": stack.frontend.strip().lower(),
            "backend": stack.backend.strip().lower(),
            "database": stack.database.strip().lower(),
            "orm": stack.orm.strip().lower(),
            "language": stack.language.strip().lower(),
        }

        if actual != expected:
            raise ValueError(
                "Qwen changed the fixed application stack. "
                f"Expected {expected}, got {actual}."
            )