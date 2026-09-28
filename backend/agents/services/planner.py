import json

from pydantic import ValidationError

from agents.prompts.planner import (
    PLANNER_SYSTEM_PROMPT,
)

from agents.providers.factory import (
    get_llm_provider,
)

from agents.schemas.plan import (
    ImplementationPlan,
)

from projects.models import (
    ApplicationSpecification,
)


class PlannerService:

    MAX_ATTEMPTS = 2

    def __init__(self):
        self.llm = get_llm_provider()

    def create_plan(
        self,
        specification: ApplicationSpecification,
    ) -> ImplementationPlan:

        payload = {
            "name": specification.name,
            "description": specification.description,
            "application_type": (
                specification.application_type
            ),
            "stack": specification.stack,
            "features": specification.features,
            "entities": specification.entities,
            "pages": specification.pages,
            "user_roles": specification.user_roles,
            "assumptions": specification.assumptions,
        }

        last_error = None

        for _ in range(self.MAX_ATTEMPTS):

            try:
                return self._generate_plan(
                    payload
                )

            except (
                ValueError,
                ValidationError,
            ) as exc:
                last_error = exc

        raise ValueError(
            "Planner failed after "
            f"{self.MAX_ATTEMPTS} attempts."
        ) from last_error

    def _generate_plan(
        self,
        specification_data: dict,
    ) -> ImplementationPlan:

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content": (
                        PLANNER_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        specification_data,
                        indent=2,
                    ),
                },
            ],
            temperature=0.1,
        )

        if not response.content:
            raise ValueError(
                "Qwen returned an empty plan."
            )

        data = self._parse_json(
            response.content
        )

        plan = ImplementationPlan.model_validate(
            data
        )

        self._validate_plan(plan)

        return plan

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
                "Qwen returned invalid planner JSON.\n\n"
                f"Raw output:\n{content}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Planner JSON root must be an object."
            )

        return data

    def _validate_plan(
        self,
        plan: ImplementationPlan,
    ) -> None:

        expected_ids = list(
            range(
                1,
                len(plan.tasks) + 1,
            )
        )

        actual_ids = [
            task.id
            for task in plan.tasks
        ]

        if actual_ids != expected_ids:
            raise ValueError(
                "Task IDs must be sequential "
                "starting from 1."
            )

        existing_ids = set()

        for task in plan.tasks:

            for dependency in task.dependencies:

                if dependency not in existing_ids:
                    raise ValueError(
                        f"Task {task.id} has invalid "
                        f"dependency {dependency}."
                    )

            existing_ids.add(
                task.id
            )