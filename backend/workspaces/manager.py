import json
from pathlib import Path
from .templates import TemplateManager
from django.conf import settings

from .exceptions import (
    WorkspaceAlreadyExistsError,
    WorkspaceNotFoundError,
    InvalidWorkspacePathError,
)


class WorkspaceManager:

    IGNORED_DIRECTORIES = {
        "node_modules",
        ".next",
        ".git",
        "dist",
        "build",
        "__pycache__",
    }

    def __init__(self, project):

        self.project = project

        self.root = Path(
            settings.WORKSPACE_ROOT
        ).resolve()

        self.workspace_path = (
            self.root / f"project_{project.id}"
        ).resolve()

    def resolve_path(
        self,
        relative_path: str,
    ) -> Path:

        target = (
            self.workspace_path / relative_path
        ).resolve()

        try:
            target.relative_to(
                self.workspace_path
            )

        except ValueError:
            raise InvalidWorkspacePathError(
                f"Path escapes workspace: "
                f"{relative_path}"
            )

        return target

    def exists(self) -> bool:
        return self.workspace_path.exists()

    def ensure_exists(self):

        if not self.exists():
            raise WorkspaceNotFoundError(
                f"Workspace not found for "
                f"project {self.project.id}"
            )

    def create(self):

        if self.exists():
            raise WorkspaceAlreadyExistsError(
                f"Workspace already exists: "
                f"{self.workspace_path}"
            )

        self.workspace_path.mkdir(
            parents=True,
            exist_ok=False,
        )

        TemplateManager.copy_to_workspace(
            self.workspace_path
        )

        builder_directory = self.resolve_path(
            ".builder"
        )

        builder_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._create_project_manifest()

        return self.workspace_path

    def _create_project_manifest(self):

        manifest = {
            "project_id": self.project.id,
            "name": self.project.name,
            "stack": {
                "frontend": "nextjs",
                "backend": "express",
                "database": "mysql",
            },
            "status": "initialized",
        }

        manifest_path = self.resolve_path(
            "project.json"
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
            ),
            encoding="utf-8",
        )

    def write_file(
        self,
        relative_path: str,
        content: str,
    ):

        self.ensure_exists()

        file_path = self.resolve_path(
            relative_path
        )

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

        return file_path

    def read_file(
        self,
        relative_path: str,
    ) -> str:

        self.ensure_exists()

        file_path = self.resolve_path(
            relative_path
        )

        if not file_path.exists():
            raise FileNotFoundError(
                relative_path
            )

        if not file_path.is_file():
            raise IsADirectoryError(
                relative_path
            )

        return file_path.read_text(
            encoding="utf-8"
        )

    def delete_file(
        self,
        relative_path: str,
    ):

        self.ensure_exists()

        file_path = self.resolve_path(
            relative_path
        )

        if not file_path.exists():
            raise FileNotFoundError(
                relative_path
            )

        if not file_path.is_file():
            raise IsADirectoryError(
                relative_path
            )

        file_path.unlink()

    def list_files(self):

        self.ensure_exists()

        files = []

        for path in self.workspace_path.rglob("*"):

            relative = path.relative_to(
                self.workspace_path
            )

            if any(
                part in self.IGNORED_DIRECTORIES
                for part in relative.parts
            ):
                continue

            if path.is_file():
                files.append(
                    relative.as_posix()
                )

        return sorted(files)