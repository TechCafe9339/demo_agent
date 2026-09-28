import shutil
import subprocess
from dataclasses import dataclass

from .exceptions import (
    CommandTimeoutError,
    WorkspaceNotFoundError,
    SandboxUnavailableError,
)


@dataclass
class DockerCommandResult:
    command: list[str]
    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.return_code == 0


class DockerSandbox:

    IMAGE = "node:24-bookworm"

    def __init__(self, workspace_manager):
        self.workspace = workspace_manager

    def ensure_docker_available(self):
        docker = shutil.which("docker")

        if docker is None:
            raise RuntimeError(
                "Docker CLI was not found. "
                "Make sure Docker Desktop is installed and running."
            )

        return docker

    def run(
    self,
    command: list[str],
    cwd: str = "",
    timeout: int = 300,
) -> DockerCommandResult:

        if not self.workspace.exists():
            raise WorkspaceNotFoundError(
                f"Workspace not found for "
                f"project {self.workspace.project.id}"
            )

        docker = self.ensure_docker_running()

        host_workspace = str(
            self.workspace.workspace_path.resolve()
        )

        project_id = (
            self.workspace.project.id
        )

        container_workdir = "/workspace"

        if cwd:
            container_workdir += f"/{cwd}"

        docker_command = [
            docker,
            "run",
            "--rm",

            "--memory",
            "2g",

            "--cpus",
            "2",

            "--pids-limit",
            "256",

            "--network",
            "bridge",

            "--workdir",
            container_workdir,

            "--volume",
            f"{host_workspace}:/workspace",
        ]

        # -----------------------------------------
        # Keep node_modules inside Linux volumes
        # -----------------------------------------

        if cwd == "backend":
            docker_command.extend(
                [
                    "--volume",
                    (
                        f"project_{project_id}_backend_node_modules:"
                        "/workspace/backend/node_modules"
                    ),
                ]
            )

        elif cwd == "frontend":
            docker_command.extend(
                [
                    "--volume",
                    (
                        f"project_{project_id}_frontend_node_modules:"
                        "/workspace/frontend/node_modules"
                    ),
                ]
            )

        docker_command.extend(
            [
                self.IMAGE,
                *command,
            ]
        )

        try:
            process = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )

        except subprocess.TimeoutExpired as exc:
            raise CommandTimeoutError(
                f"Docker command timed out "
                f"after {timeout} seconds."
            ) from exc

        return DockerCommandResult(
            command=command,
            return_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def ensure_docker_running(self):
        docker = self.ensure_docker_available()

        try:
            process = subprocess.run(
                [
                    docker,
                    "info",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                shell=False,
            )

        except subprocess.TimeoutExpired as exc:
            raise SandboxUnavailableError("Docker did not respond in time.") from exc

        if process.returncode != 0:
            raise SandboxUnavailableError(
                "Docker is installed but the Docker daemon "
                "is not running or cannot be reached.\n\n"
                f"{process.stderr or process.stdout}"
            )

        return docker
