from rest_framework import serializers

from .models import AdminBoundary


class AdminBoundarySerializer(serializers.ModelSerializer):
    bbox = serializers.ListField()

    class Meta:
        model = AdminBoundary
        fields = ("pk", "level", "gid_0", "gid_1", "gid_2", "gid_3", "gid_3", "name_0", "name_1", "name_2",
                  "name_3", "name_4", "bbox")
