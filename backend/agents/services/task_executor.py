from django.utils import timezone

from agents.models import PlanTask

from agents.services.code_generator import (
    CodeGeneratorService,
)

from agents.services.file_operations import (
    FileOperationService,
)

from agents.services.repair_agent import (
    RepairAgentService,
)

from agents.services.task_validator import (
    TaskValidatorService,
)

from projects.models import Project

from workspaces.manager import (
    WorkspaceManager,
)

from workspaces.exceptions import (
    SandboxUnavailableError,
)


class TaskExecutorService:
    MAX_REPAIR_ATTEMPTS = 2

    def __init__(self):
        self.generator = CodeGeneratorService()
        self.validator = TaskValidatorService()
        self.repair_agent = RepairAgentService()

    def execute(
        self,
        *,
        project: Project,
        task: PlanTask,
    ) -> dict:

        self._validate_project_task(
            project=project,
            task=task,
        )

        self._validate_dependencies(task)

        workspace = WorkspaceManager(project)

        if not workspace.exists():
            raise ValueError(f"Workspace does not exist for " f"project {project.id}.")

        task.status = PlanTask.Status.RUNNING
        task.started_at = timezone.now()
        task.completed_at = None
        task.error_message = ""

        task.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "error_message",
                "updated_at",
            ]
        )

        try:
            # -----------------------------------------
            # 1. Load project context
            # -----------------------------------------

            file_tree = workspace.list_files()

            relevant_files = self._load_relevant_files(
                workspace=workspace,
                task=task,
            )

            specification_data = self._get_specification_data(project)

            # -----------------------------------------
            # 2. Ask Qwen to generate code
            # -----------------------------------------

            generation_result = self.generator.generate(
                task=task,
                application_specification=(specification_data),
                file_tree=file_tree,
                relevant_files=(relevant_files),
            )

            # -----------------------------------------
            # Enforce task file scope
            # -----------------------------------------

            allowed_paths = set(task.files)

            unexpected_paths = [
                operation.path
                for operation in generation_result.operations
                if operation.path not in allowed_paths
            ]

            if unexpected_paths:
                raise ValueError(
                    "Generator attempted to modify files "
                    "outside the current task scope: "
                    f"{unexpected_paths}. "
                    f"Allowed files: {sorted(allowed_paths)}"
                )

            # -----------------------------------------
            # 3. Apply generated file operations
            # -----------------------------------------

            changed_files = FileOperationService.apply(
                workspace=workspace,
                result=generation_result,
            )

            # -----------------------------------------
            # Verify expected task files exist
            # -----------------------------------------

            existing_files = set(
                workspace.list_files()
            )

            missing_files = [
                path
                for path in task.files
                if path not in existing_files
            ]

            if missing_files:
                raise ValueError(
                    "Generator did not create the required "
                    "task files: "
                    f"{missing_files}"
                )

            # -----------------------------------------
            # 4. Validate generated code
            # -----------------------------------------

            try:
                validation = self.validator.validate(
                    workspace=workspace,
                    task=task,
                )

            except SandboxUnavailableError:
                raise

            # -----------------------------------------
            # 5. Attempt automatic repair
            # -----------------------------------------

            repair_files = []

            if not validation.success:
                repair_result = self._repair_task(
                    project=project,
                    task=task,
                    workspace=workspace,
                    errors=validation.errors,
                )

                validation = repair_result["validation"]

                repair_files = repair_result["changed_files"]

            # -----------------------------------------
            # 6. Fail if validation still fails
            # -----------------------------------------

            if not validation.success:
                error_text = "\n\n".join(validation.errors)

                raise ValueError(
                    "Task validation failed "
                    "after automatic repair.\n\n"
                    f"{error_text}"
                )

            # -----------------------------------------
            # 7. Mark task completed
            # -----------------------------------------

            task.status = PlanTask.Status.COMPLETED

            task.completed_at = timezone.now()

            task.error_message = ""

            task.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            all_changed_files = list(dict.fromkeys(changed_files + repair_files))

            return {
                "success": True,
                "task_number": task.task_number,
                "task_title": task.title,
                "summary": generation_result.summary,
                "changed_files": all_changed_files,
                "validation_logs": validation.logs,
            }

        except Exception as exc:
            # -----------------------------------------
            # Mark task failed
            # -----------------------------------------

            task.status = PlanTask.Status.FAILED

            task.error_message = str(exc)

            task.completed_at = timezone.now()

            task.save(
                update_fields=[
                    "status",
                    "error_message",
                    "completed_at",
                    "updated_at",
                ]
            )

            raise

    # =================================================
    # Repair
    # =================================================

    def _repair_task(
        self,
        *,
        project: Project,
        task: PlanTask,
        workspace: WorkspaceManager,
        errors: list[str],
    ) -> dict:

        specification_data = (
            self._get_specification_data(
                project
            )
        )

        current_errors = errors

        changed_files: list[str] = []

        last_validation = None

        for attempt in range(
            1,
            self.MAX_REPAIR_ATTEMPTS + 1,
        ):
            # -----------------------------------------
            # 1. Current workspace tree
            # -----------------------------------------

            file_tree = workspace.list_files()

            # -----------------------------------------
            # 2. Build small repair context
            # -----------------------------------------

            repair_paths = set(
                task.files
            )

            repair_paths.update({
                "backend/src/config/prisma.ts",
                "backend/src/middleware/auth.middleware.ts",
                "backend/src/server.ts",
                "backend/package.json",
                "backend/tsconfig.json",
                "backend/prisma/schema.prisma",
            })

            repair_files: dict[str, str] = {}

            for path in repair_paths:
                try:
                    repair_files[path] = (
                        workspace.read_file(
                            path
                        )
                    )

                except (
                    FileNotFoundError,
                    UnicodeDecodeError,
                    IsADirectoryError,
                ):
                    continue

                except Exception:
                    continue

            # -----------------------------------------
            # 3. Build reduced file tree
            # -----------------------------------------

            repair_file_tree = [
                path
                for path in file_tree
                if (
                    path in repair_paths

                    or path.startswith(
                        "backend/src/controllers/"
                    )

                    or path.startswith(
                        "backend/src/routes/"
                    )

                    or path.startswith(
                        "backend/src/middleware/"
                    )

                    or path.startswith(
                        "backend/src/config/"
                    )
                )
            ]

            # Never send generated Prisma client files
            # to the repair LLM.
            repair_file_tree = [
                path
                for path in repair_file_tree
                if not path.startswith(
                    "backend/src/generated/prisma/"
                )
            ]

            # -----------------------------------------
            # 4. Ask repair agent
            # -----------------------------------------

            repair_result = (
                self.repair_agent.repair(
                    application_specification=(
                        specification_data
                    ),

                    task=(
                        self._get_task_data(
                            task
                        )
                    ),

                    errors=current_errors,

                    file_tree=(
                        repair_file_tree
                    ),

                    relevant_files=(
                        repair_files
                    ),
                )
            )

            # -----------------------------------------
            # 5. Apply repair
            # -----------------------------------------

            repair_changed_files = (
                FileOperationService.apply(
                    workspace=workspace,
                    result=repair_result,
                )
            )

            changed_files.extend(
                repair_changed_files
            )

            # -----------------------------------------
            # 6. Validate repaired task
            # -----------------------------------------

            last_validation = (
                self.validator.validate(
                    workspace=workspace,
                    task=task,
                )
            )

            if last_validation.success:
                return {
                    "validation":
                        last_validation,

                    "changed_files":
                        changed_files,

                    "attempts":
                        attempt,
                }

            # Feed the newest compiler errors
            # into the next repair attempt.
            current_errors = (
                last_validation.errors
            )

        return {
            "validation":
                last_validation,

            "changed_files":
                changed_files,

            "attempts":
                self.MAX_REPAIR_ATTEMPTS,
        }
    # =================================================
    # Dependencies
    # =================================================

    def _validate_dependencies(
        self,
        task: PlanTask,
    ) -> None:

        if not task.dependencies:
            return

        completed_numbers = set(
            task.plan.tasks.filter(
                task_number__in=(task.dependencies),
                status=(PlanTask.Status.COMPLETED),
            ).values_list(
                "task_number",
                flat=True,
            )
        )

        required_numbers = set(task.dependencies)

        missing = required_numbers - completed_numbers

        if missing:
            raise ValueError(
                "Task dependencies are " "not completed: " f"{sorted(missing)}"
            )

    # =================================================
    # Project / task relationship validation
    # =================================================

    def _validate_project_task(
        self,
        *,
        project: Project,
        task: PlanTask,
    ) -> None:

        if task.plan.project_id != project.id:
            raise ValueError("The supplied task does not " "belong to this project.")

    # =================================================
    # Application specification
    # =================================================

    def _get_specification_data(
        self,
        project: Project,
    ) -> dict:

        try:
            specification = project.application_specification

        except Exception as exc:
            raise ValueError(
                "Project does not have an " "application specification."
            ) from exc

        return {
            "name": specification.name,
            "description": specification.description,
            "application_type": specification.application_type,
            "stack": specification.stack,
            "features": specification.features,
            "entities": specification.entities,
            "pages": specification.pages,
            "user_roles": specification.user_roles,
            "assumptions": specification.assumptions,
        }

    # =================================================
    # Task data sent to repair agent
    # =================================================

    def _get_task_data(
        self,
        task: PlanTask,
    ) -> dict:

        return {
            "id": task.task_number,
            "type": task.task_type,
            "title": task.title,
            "description": task.description,
            "files": task.files,
            "dependencies": task.dependencies,
        }

    # =================================================
    # Relevant project files
    # =================================================

    def _load_relevant_files(
        self,
        *,
        workspace: WorkspaceManager,
        task: PlanTask,
    ) -> dict[str, str]:

        relevant = {}

        existing_files = set(workspace.list_files())

        candidate_files = set(task.files)

        # Important shared project context
        candidate_files.update(
            {
                # Backend
                "backend/package.json",
                "backend/tsconfig.json",
                "backend/prisma/schema.prisma",
                "backend/src/server.ts",
                # Frontend
                "frontend/package.json",
                "frontend/tsconfig.json",
                "frontend/next.config.ts",
                "frontend/app/layout.tsx",
                "frontend/app/page.tsx",
            }
        )

        for path in candidate_files:

            if path not in existing_files:
                continue

            try:
                relevant[path] = workspace.read_file(path)

            except (
                UnicodeDecodeError,
                IsADirectoryError,
            ):
                # Ignore non-text files.
                continue

        return relevant
