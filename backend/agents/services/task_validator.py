from dataclasses import dataclass, field

from agents.models import PlanTask

from workspaces.manager import WorkspaceManager
from workspaces.sandbox import ProjectSandbox


@dataclass
class ValidationResult:
    success: bool
    errors: list[str] = field(
        default_factory=list
    )
    logs: list[str] = field(
        default_factory=list
    )


class TaskValidatorService:

    def validate(
        self,
        *,
        workspace: WorkspaceManager,
        task: PlanTask,
    ) -> ValidationResult:

        sandbox = ProjectSandbox(
            workspace
        )

        errors = []
        logs = []

        if (
            task.task_type
            == PlanTask.TaskType.DATABASE
        ):
            self._validate_database(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

        elif (
            task.task_type
            == PlanTask.TaskType.BACKEND
        ):
            self._validate_backend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

        elif (
            task.task_type
            == PlanTask.TaskType.FRONTEND
        ):
            self._validate_frontend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

        elif (
            task.task_type
            == PlanTask.TaskType.INTEGRATION
        ):
            self._validate_backend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

            self._validate_frontend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

        elif (
            task.task_type
            == PlanTask.TaskType.BUILD
        ):
            self._validate_backend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

            self._validate_frontend(
                sandbox=sandbox,
                errors=errors,
                logs=logs,
            )

        return ValidationResult(
            success=not errors,
            errors=errors,
            logs=logs,
        )

    def _validate_database(
        self,
        *,
        sandbox,
        errors,
        logs,
    ):
        result = (
            sandbox.run_backend_command(
                [
                    "npx",
                    "prisma",
                    "validate",
                ]
            )
        )

        self._collect_result(
            result=result,
            errors=errors,
            logs=logs,
        )

    def _validate_backend(
        self,
        *,
        sandbox,
        errors,
        logs,
    ):
        result = (
            sandbox.build_backend()
        )

        self._collect_result(
            result=result,
            errors=errors,
            logs=logs,
        )

    def _validate_frontend(
        self,
        *,
        sandbox,
        errors,
        logs,
    ):
        result = (
            sandbox.build_frontend()
        )

        self._collect_result(
            result=result,
            errors=errors,
            logs=logs,
        )

    def _collect_result(
        self,
        *,
        result,
        errors,
        logs,
    ):
        if result.stdout:
            logs.append(
                result.stdout
            )

        if result.stderr:
            logs.append(
                result.stderr
            )

        if not result.success:
            error = (
                result.stderr.strip()
                or result.stdout.strip()
                or (
                    "Validation command "
                    "failed without output."
                )
            )

            errors.append(
                error
            )