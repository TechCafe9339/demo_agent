from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project

        fields = [
            "id",
            "name",
            "description",
            "initial_prompt",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "name": {
                "required": False,
            },
        }

    def validate_initial_prompt(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Project prompt cannot be empty."
            )

        return value

    def create(
        self,
        validated_data,
    ):
        prompt = validated_data[
            "initial_prompt"
        ]

        if not validated_data.get(
            "name"
        ):
            name = prompt[:60]

            if len(prompt) > 60:
                name += "..."

            validated_data[
                "name"
            ] = name

        return super().create(
            validated_data
        )