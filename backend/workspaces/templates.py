import shutil
from pathlib import Path

from django.conf import settings


class TemplateManager:

    TEMPLATE_NAME = "next-express-mysql"

    @classmethod
    def get_template_path(cls) -> Path:
        return (
            Path(settings.BASE_DIR).parent
            / "templates"
            / cls.TEMPLATE_NAME
        ).resolve()

    @classmethod
    def copy_to_workspace(
        cls,
        workspace_path: Path,
    ):
        template_path = cls.get_template_path()

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template does not exist: "
                f"{template_path}"
            )

        for item in template_path.iterdir():

            destination = (
                workspace_path / item.name
            )

            if item.is_dir():

                shutil.copytree(
                    item,
                    destination,
                    dirs_exist_ok=True,
                )

            else:

                shutil.copy2(
                    item,
                    destination,
                )