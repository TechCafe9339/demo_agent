from pathlib import Path
import traceback

from django.conf import settings
from agents.services.change_impact import (
    ChangeImpactAnalyzer,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from agents.services.chat import AIChatService
from agents.services.chat_intent import (
    ProjectChatIntentService,
)
from agents.services.project_analysis import (
    ProjectAnalysisService,
)
from agents.services.project_planning import (
    ProjectPlanningService,
)
from agents.services.project_change import (
    ProjectChangeService,
)
from projects.models import Project
from projects.serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    # =========================================================
    # PROJECT OWNERSHIP
    # =========================================================

    def get_queryset(self):
        """
        A user can only access projects
        that belong to their account.
        """

        return Project.objects.filter(user=self.request.user).order_by("-id")

    def perform_create(
        self,
        serializer,
    ):
        """
        Automatically assign newly created
        projects to the logged-in user.
        """

        serializer.save(user=self.request.user)

    # =========================================================
    # PREPARE PROJECT
    # Requirement Analysis + Planning
    # =========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="prepare",
    )
    def prepare_project(
        self,
        request,
        pk=None,
    ):
        project = self.get_object()

        try:
            # -----------------------------------------
            # 1. Analyze requirements
            # -----------------------------------------

            analysis_service = ProjectAnalysisService()

            specification = analysis_service.analyze_project(project)

            # -----------------------------------------
            # 2. Create implementation plan
            # -----------------------------------------

            planning_service = ProjectPlanningService()

            plan = planning_service.create_plan(project)

            project.refresh_from_db()

            return Response(
                {
                    "project": ProjectSerializer(project).data,
                    "specification_id": specification.id,
                    "plan_id": plan.id,
                    "message": ("Project analyzed and " "planned successfully."),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            print("\n" "========== PREPARE PROJECT ERROR ==========")

            print(
                "PROJECT ID:",
                project.id,
            )

            print(
                "ERROR TYPE:",
                type(exc).__name__,
            )

            print(
                "ERROR:",
                str(exc),
            )

            print("TRACEBACK:")

            traceback.print_exc()

            print("===========================================" "\n")

            project.status = Project.Status.FAILED

            project.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "project_id": project.id,
                },
                status=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            )

    # =========================================================
    # PROJECT WORKSPACE
    # =========================================================

    @action(
        detail=True,
        methods=["get"],
        url_path="workspace",
    )
    def workspace(
        self,
        request,
        pk=None,
    ):
        project = self.get_object()

        specification_data = None
        plan_data = None

        # -----------------------------------------
        # Application Specification
        # -----------------------------------------

        if hasattr(
            project,
            "application_specification",
        ):
            specification = project.application_specification

            specification_data = {
                "id": specification.id,
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

        # -----------------------------------------
        # Implementation Plan
        # -----------------------------------------

        if hasattr(
            project,
            "implementation_plan",
        ):
            plan = project.implementation_plan

            tasks = []

            for task in plan.tasks.all().order_by("task_number"):
                tasks.append(
                    {
                        "id": task.id,
                        "task_number": task.task_number,
                        "title": task.title,
                        "status": task.status,
                    }
                )

            plan_data = {
                "id": plan.id,
                "tasks": tasks,
            }

        return Response(
            {
                "project": ProjectSerializer(project).data,
                "specification": specification_data,
                "plan": plan_data,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # PROJECT FILE TREE
    # =========================================================

    @action(
        detail=True,
        methods=["get"],
        url_path="files",
    )
    def project_files(
        self,
        request,
        pk=None,
    ):
        project = self.get_object()

        workspace_root = (
            Path(settings.BASE_DIR).parent
            / "generated_workspaces"
            / f"project_{project.id}"
        )

        if not workspace_root.exists():
            return Response(
                {
                    "exists": False,
                    "files": [],
                },
                status=status.HTTP_200_OK,
            )

        # -----------------------------------------
        # Directories that should never appear
        # in the web file explorer
        # -----------------------------------------

        ignored_directories = {
            "node_modules",
            ".next",
            "dist",
            ".git",
            "__pycache__",
            ".pytest_cache",
            ".turbo",
        }

        # -----------------------------------------
        # Secret / sensitive files
        # -----------------------------------------

        ignored_files = {
            ".env",
            ".env.local",
            ".env.development",
            ".env.production",
            ".env.test",
            ".npmrc",
        }

        def should_hide_file(
            path: Path,
        ):
            name = path.name.lower()

            if name in ignored_files:
                return True

            # Block any .env.* file
            if name.startswith(".env."):
                return True

            # Block common private-key files
            if name.endswith(
                (
                    ".pem",
                    ".key",
                    ".p12",
                    ".pfx",
                )
            ):
                return True

            return False

        def build_tree(
            directory: Path,
        ):
            items = []

            try:
                directory_items = directory.iterdir()

            except (
                PermissionError,
                OSError,
            ):
                return items

            for item in sorted(
                directory_items,
                key=lambda path: (
                    not path.is_dir(),
                    path.name.lower(),
                ),
            ):
                if item.is_dir() and item.name in ignored_directories:
                    continue

                if item.is_file() and should_hide_file(item):
                    continue

                relative_path = item.relative_to(workspace_root).as_posix()

                if item.is_dir():
                    items.append(
                        {
                            "name": item.name,
                            "path": relative_path,
                            "type": "directory",
                            "children": build_tree(item),
                        }
                    )

                else:
                    items.append(
                        {
                            "name": item.name,
                            "path": relative_path,
                            "type": "file",
                        }
                    )

            return items

        return Response(
            {
                "exists": True,
                "files": build_tree(workspace_root),
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # READ INDIVIDUAL PROJECT FILE
    # =========================================================

    @action(
        detail=True,
        methods=["get"],
        url_path="file",
    )
    def project_file(
        self,
        request,
        pk=None,
    ):
        project = self.get_object()

        requested_path = request.query_params.get(
            "path",
            "",
        ).strip()

        if not requested_path:
            return Response(
                {"error": "File path is required."},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        # -----------------------------------------
        # Block sensitive files
        # -----------------------------------------

        requested_name = Path(requested_path).name.lower()

        blocked_files = {
            ".env",
            ".env.local",
            ".env.development",
            ".env.production",
            ".env.test",
            ".npmrc",
        }

        if (
            requested_name in blocked_files
            or requested_name.startswith(".env.")
            or requested_name.endswith(
                (
                    ".pem",
                    ".key",
                    ".p12",
                    ".pfx",
                )
            )
        ):
            return Response(
                {"error": ("This file cannot " "be previewed.")},
                status=(status.HTTP_403_FORBIDDEN),
            )

        workspace_root = (
            Path(settings.BASE_DIR).parent
            / "generated_workspaces"
            / f"project_{project.id}"
        ).resolve()

        file_path = (workspace_root / requested_path).resolve()

        # -----------------------------------------
        # Prevent path traversal
        #
        # Example blocked:
        # ../../config/settings.py
        # -----------------------------------------

        try:
            file_path.relative_to(workspace_root)

        except ValueError:
            return Response(
                {"error": "Invalid file path."},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        if not file_path.exists() or not file_path.is_file():
            return Response(
                {"error": "File not found."},
                status=(status.HTTP_404_NOT_FOUND),
            )

        # Maximum preview size = 1 MB

        max_size = 1024 * 1024

        if file_path.stat().st_size > max_size:
            return Response(
                {"error": ("File is too large " "to preview.")},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        try:
            content = file_path.read_text(encoding="utf-8")

        except UnicodeDecodeError:
            return Response(
                {"error": ("Binary files cannot " "be previewed.")},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        except OSError as exc:
            return Response(
                {"error": ("Unable to read file: " f"{str(exc)}")},
                status=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            )

        return Response(
            {
                "name": file_path.name,
                "path": requested_path,
                "content": content,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # PROJECT CHAT
    # =========================================================

    @action(
        detail=True,
        methods=[
            "get",
            "post",
        ],
        url_path="chat",
    )
    def project_chat(
        self,
        request,
        pk=None,
    ):
        project = self.get_object()

        conversation = project.get_or_create_main_conversation()

        # =====================================================
        # GET CHAT HISTORY
        # =====================================================

        if request.method == "GET":
            messages = conversation.messages.all().order_by("created_at")

            return Response(
                {
                    "conversation_id": conversation.id,
                    "messages": [
                        {
                            "id": message.id,
                            "role": message.role,
                            "content": message.content,
                            "timestamp": message.created_at,
                        }
                        for message in messages
                    ],
                },
                status=status.HTTP_200_OK,
            )

        # =====================================================
        # POST USER MESSAGE
        # =====================================================

        content = request.data.get(
            "content",
            "",
        ).strip()

        if not content:
            return Response(
                {"error": ("Message cannot " "be empty.")},
                status=(status.HTTP_400_BAD_REQUEST),
            )

        # -----------------------------------------
        # Save user message first
        # -----------------------------------------

        user_message = conversation.messages.create(
            role="user",
            content=content,
        )

        try:
            # =====================================
            # 1. CLASSIFY MESSAGE INTENT
            # =====================================

            intent_service = ProjectChatIntentService()

            intent_result = intent_service.classify(content)

            intent = intent_result["intent"]

            intent_summary = intent_result["summary"]

            print(
                "CHAT INTENT:",
                intent,
            )

            print(
                "CHAT SUMMARY:",
                intent_summary,
            )

            # =====================================
            # 2. NORMAL QUESTION
            # =====================================

            if intent == "question":
                project_context = f"""
You are Prompt2Web, an AI assistant working on an existing software project.

PROJECT NAME:
{project.name}

PROJECT STATUS:
{project.status}

ORIGINAL PROJECT REQUEST:
{project.initial_prompt}

USER QUESTION:
{content}

Answer specifically about this project.

Give a clear and concise software-development explanation.

Do not claim that files were modified.

Do not claim that builds or tests were executed unless they actually were.
"""

                chat_service = AIChatService()

                llm_response = chat_service.send(project_context)

                assistant_content = llm_response.content.strip()

            # =====================================
            # 3. PROJECT CHANGE REQUEST
            # =====================================

            elif intent == "change_request":

                # -------------------------------------
                # 1. Analyze impact
                # -------------------------------------

                impact_analyzer = (
                    ChangeImpactAnalyzer()
                )

                impact = (
                    impact_analyzer
                    .analyze(
                        project=project,
                        change_request=content,
                    )
                )

                affected_files = (
                    impact.get(
                        "affected_files",
                        [],
                    )
                )

                new_files = (
                    impact.get(
                        "new_files",
                        [],
                    )
                )

                # -------------------------------------
                # 2. Apply actual change
                # -------------------------------------

                change_service = (
                    ProjectChangeService()
                )

                change_result = (
                    change_service
                    .apply(
                        project=project,
                        change_request=content,
                        affected_files=affected_files,
                        new_files=new_files,
                    )
                )

                written_files = (
                    change_result[
                        "written_files"
                    ]
                )

                written_text = (
                    "\n".join(
                        f"- {path}"
                        for path
                        in written_files
                    )
                    if written_files
                    else "- No files changed"
                )

                assistant_content = f"""
            The requested project change was applied.

            Change:
            {impact["summary"]}

            Risk:
            {impact["risk"].upper()}

            Files modified:
            {written_text}

            Details:
            {change_result["summary"]}

            The project files have been updated.

            Build and automated testing have not been executed yet.
            """
                impact_analyzer = (
                    ChangeImpactAnalyzer()
                )

                impact = (
                    impact_analyzer
                    .analyze(
                        project=project,
                        change_request=content,
                    )
                )

                affected_files = (
                    impact.get(
                        "affected_files",
                        [],
                    )
                )

                new_files = (
                    impact.get(
                        "new_files",
                        [],
                    )
                )

                affected_text = (
                    "\n".join(
                        f"- {path}"
                        for path
                        in affected_files
                    )
                    if affected_files
                    else "- None"
                )

                new_files_text = (
                    "\n".join(
                        f"- {path}"
                        for path
                        in new_files
                    )
                    if new_files
                    else "- None"
                )

                assistant_content = f"""
            I analyzed the requested project change.

            Requested change:
            {impact["summary"]}

            Risk:
            {impact["risk"].upper()}

            Affected existing files:
            {affected_text}

            New files:
            {new_files_text}

            Why:
            {impact["reason"]}

            No files have been modified yet.
            """

            # =====================================
            # UNKNOWN INTENT
            # =====================================

            else:
                raise ValueError(("Unknown chat intent: " f"{intent}"))

            if not assistant_content:
                raise ValueError(("LLM returned an " "empty response."))

            # =====================================
            # SAVE ASSISTANT MESSAGE
            # =====================================

            assistant_message = conversation.messages.create(
                role="assistant",
                content=(assistant_content),
            )

            # =====================================
            # RESPONSE TO FRONTEND
            # =====================================

            return Response(
                {
                    "intent": intent,
                    "intent_summary": intent_summary,
                    "user_message": {
                        "id": user_message.id,
                        "role": user_message.role,
                        "content": user_message.content,
                        "timestamp": user_message.created_at,
                    },
                    "assistant_message": {
                        "id": assistant_message.id,
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                        "timestamp": assistant_message.created_at,
                    },
                },
                status=(status.HTTP_201_CREATED),
            )

        except Exception as exc:
            print("\n" "========== PROJECT CHAT ERROR ==========")

            print(
                "PROJECT ID:",
                project.id,
            )

            print(
                "ERROR TYPE:",
                type(exc).__name__,
            )

            print(
                "ERROR:",
                str(exc),
            )

            traceback.print_exc()

            print("========================================" "\n")

            return Response(
                {
                    "error": ("AI response failed: " f"{str(exc)}"),
                    "error_type": type(exc).__name__,
                    "user_message": {
                        "id": user_message.id,
                        "role": user_message.role,
                        "content": user_message.content,
                        "timestamp": user_message.created_at,
                    },
                },
                status=(status.HTTP_502_BAD_GATEWAY),
            )
