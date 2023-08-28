from rest_framework import serializers

from .models import Post, Follow


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
