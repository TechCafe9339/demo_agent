from .docker import DockerSandbox


class ProjectSandbox:

    def __init__(self, workspace_manager):
        self.workspace = workspace_manager
        self.docker = DockerSandbox(
            workspace_manager
        )

    def install_frontend(self):
        return self.docker.run(
            [
                "npm",
                "install",
                "--no-audit",
                "--no-fund",
            ],
            cwd="frontend",
            timeout=900,
        )

    def build_frontend(self):
        return self.docker.run(
            ["npm", "run", "build"],
            cwd="frontend",
            timeout=600,
        )

    def install_backend(self):
        return self.docker.run(
            [
                "npm",
                "install",
                "--no-audit",
                "--no-fund",
            ],
            cwd="backend",
            timeout=900,
        )

    def build_backend(self):
        return self.docker.run(
            ["npm", "run", "build"],
            cwd="backend",
            timeout=600,
        )

    def run_frontend_command(
        self,
        command: list[str],
        timeout: int = 600,
    ):
        return self.docker.run(
            command,
            cwd="frontend",
            timeout=timeout,
        )

    def run_backend_command(
        self,
        command: list[str],
        timeout: int = 600,
    ):
        return self.docker.run(
            command,
            cwd="backend",
            timeout=timeout,
        )