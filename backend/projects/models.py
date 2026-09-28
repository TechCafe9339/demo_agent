from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLANNING = "planning", "Planning"
        GENERATING = "generating", "Generating"
        BUILDING = "building", "Building"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    initial_prompt = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def get_or_create_main_conversation(self):
        conversation, created = self.conversations.get_or_create(
            title="Main Development Chat"
        )

        return conversation

    def __str__(self):
        return self.name

class ApplicationSpecification(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="application_specification",
    )

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    application_type = models.CharField(
        max_length=100,
        default="web_application",
    )

    stack = models.JSONField(
        default=dict,
    )

    features = models.JSONField(
        default=list,
    )

    entities = models.JSONField(
        default=list,
    )

    pages = models.JSONField(
        default=list,
    )

    user_roles = models.JSONField(
        default=list,
    )

    assumptions = models.JSONField(
        default=list,
    )

    version = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"Specification for {self.project.name}"
        )