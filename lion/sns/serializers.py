from rest_framework import serializers

from .models import Post, Follow
from django.contrib.auth.models import User


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at", "updated_at")


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
        fields = ("id", "username", "email", "first_name", "last_name")
        read_only_fields = ("id", "username", "email", "first_name", "last_name")
