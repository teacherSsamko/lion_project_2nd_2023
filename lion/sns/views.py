import uuid

import boto3
from django.core.files.base import File
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import viewsets, views, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request

from .models import Post, Follow
from .serializers import PostSerializer, FollowSerializer, UserSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def create(self, request: Request, *args, **kwargs):
        user = request.user
        data = request.data

        if image := data.get("image"):
            data["image"] = image.read()

            image: File
            endpoint_url = "https://kr.object.ncloudstorage.com"
            access_key = settings.NCP_ACCESS_KEY
            secret_key = settings.NCP_SECRET_KEY
            bucket_name = "post-image-es"

            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            image_id = str(uuid.uuid4())
            ext = image.name.split(".")[-1]
            image_filename = f"{image_id}.{ext}"
            s3.upload_fileobj(image.file, bucket_name, image_filename)
            s3.put_object_acl(
                ACL="public-read",
                Bucket=bucket_name,
                Key=image_filename,
            )
            image_url = f"{endpoint_url}/{bucket_name}/{image_filename}"

        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data["user"] = user
            data["image_url"] = image_url if image else None
            res: Post = serializer.create(data)
            return Response(
                status=status.HTTP_201_CREATED, data=PostSerializer(res).data
            )
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

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

    @action(detail=True, methods=["post"])
    def hide(self, request, *args, **kwargs):
        post: Post = self.get_object()
        post.hidden = not post.hidden
        post.save()
        return Response(status=status.HTTP_200_OK)


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
        posts = Post.objects.filter(user__in=following_ids).filter(hidden=False)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class UsersView(views.APIView):
    def get(self, request):
        # get users list except the current user
        users = User.objects.exclude(id=request.user.id)
        serializer = UserSerializer(users, many=True, context={"request": request})
        return Response(serializer.data)
