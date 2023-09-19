from django.contrib.auth.models import User
from rest_framework import viewsets, views
from rest_framework import status
from rest_framework.response import Response

from .models import Post, Follow
from .serializers import PostSerializer, FollowSerializer, UserSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        if self.action == "list":
            return Post.objects.filter(user=self.request.user)
        return super().get_queryset()

    def update(self, request, *args, **kwargs):
        if request.user != self.get_object().user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user != self.get_object().user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user != self.get_object().user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)


class FollowView(views.APIView):
    def post(self, request, format=None):
        serializer = FollowSerializer(data=request.data)
        if serializer.is_valid():
            following = serializer.validated_data["following"]
            qs = Follow.objects.filter(follower=request.user, following=following)
            if qs.exists():
                # unfollow
                qs.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            else:
                # follow
                Follow.objects.create(
                    follower=request.user,
                    following=following,
                )
                return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedView(views.APIView):
    def get(self, request, format=None):
        # get all posts from users that the user is following
        following_ids = Follow.objects.filter(follower=request.user).values_list(
            "following", flat=True
        )
        posts = Post.objects.filter(user__in=following_ids)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class UsersView(views.APIView):
    def get(self, request):
        # get users list except the current user
        users = User.objects.exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True, context={"request": request})
        return Response(serializer.data)
