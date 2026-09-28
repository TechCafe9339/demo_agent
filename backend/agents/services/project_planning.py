from agents.services.plan_persistence import (
    PlanPersistenceService,
)

from agents.services.planner import (
    PlannerService,
)

from projects.models import Project


class ProjectPlanningService:

    def __init__(self):
        self.planner = PlannerService()

    def create_plan(
        self,
        project: Project,
    ):

        specification = (
            project.application_specification
        )

        plan = self.planner.create_plan(
            specification
        )

        database_plan = (
            PlanPersistenceService.save(
                project=project,
                plan=plan,
            )
        )

        return database_plan