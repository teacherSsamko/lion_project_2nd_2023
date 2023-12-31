from rest_framework import serializers

from .models import Post, Follow
from django.contrib.auth.models import User


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at", "updated_at", "hidden")


class PostUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            "id",
            "user",
            "content",
            "image",
            "created_at",
            "updated_at",
            "hidden",
        )

    image = serializers.ImageField(required=False)


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("follower", "following")
        read_only_fields = ("follower",)

    def unfollow(self, follower, following):
        Follow.objects.filter(follower=follower, following=following).delete()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "following")
        read_only_fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "following",
        )

    following = serializers.SerializerMethodField()

    def get_following(self, user) -> bool:
        if Follow.objects.filter(follower=self.context["request"].user, following=user):
            return True
        return False
