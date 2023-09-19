from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Post, Follow


class PostTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="main")
        cls.post = Post.objects.create(user=cls.user, content="test")
        cls.user2 = User.objects.create_user(username="user2")

    def test_get_my_post(self):
        # create some posts
        post_n = 5
        for i in range(post_n):
            Post.objects.create(user=self.user, content=f"test{i}")
            Post.objects.create(user=self.user2, content=f"test{i}")
        # call get list api
        self.client.force_login(self.user)
        response = self.client.get(reverse("post-list"))
        # check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        my_post_n = Post.objects.filter(user=self.user).count()
        self.assertEqual(len(response.data), my_post_n)

    def test_update_post(self):
        # call update api
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("post-detail", args=[self.post.id]), {"content": "new content"}
        )
        # check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "new content")
        self.assertEqual(Post.objects.get(id=self.post.id).content, "new content")

        # try to update other user's post
        self.client.force_login(self.user2)
        response = self.client.patch(
            reverse("post-detail", args=[self.post.id]), {"content": "new content"}
        )
        # check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_post(self):
        # try to delete other user's post
        self.client.force_login(self.user2)
        response = self.client.delete(reverse("post-detail", args=[self.post.id]))
        # check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # call delete api
        self.client.force_login(self.user)
        response = self.client.delete(reverse("post-detail", args=[self.post.id]))
        # check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_follow_unfollow(self):
        # call follow api
        self.client.force_login(self.user)
        response = self.client.post(reverse("follow"), {"following": self.user2.id})
        # check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user, following=self.user2).exists()
        )

        # call unfollow api
        self.client.force_login(self.user)
        response = self.client.post(reverse("follow"), {"following": self.user2.id})
        # check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Follow.objects.filter(follower=self.user, following=self.user2).exists()
        )

    def test_get_following_posts(self):
        user3 = User.objects.create_user(username="user3")
        unfollowing_user = User.objects.create_user(username="unfollowing")
        # follow user2 and user3
        Follow.objects.create(follower=self.user, following=self.user2)
        Follow.objects.create(follower=self.user, following=user3)
        # create some posts
        post_n = 5
        for i in range(post_n):
            Post.objects.create(user=self.user, content=f"test{i}")
            Post.objects.create(user=self.user2, content=f"test{i}")
            Post.objects.create(user=user3, content=f"test{i}")
            Post.objects.create(user=unfollowing_user, content=f"test{i}")
        # call get list api
        self.client.force_login(self.user)
        response = self.client.get(reverse("feed"))
        # check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), post_n * 2)


class FollowingTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="main")
        cls.user2 = User.objects.create_user(username="sub")

    def test_get_user_list(self):
        follwing = []
        for i in range(1, 6):
            user = User.objects.create_user(username=f"user{i}")
            if i % 3 == 0:
                Follow.objects.create(follower=self.user, following=user)
                follwing.append(user.username)
        self.client.force_login(self.user)
        response = self.client.get(reverse("users"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        all_users_except_main_n = User.objects.exclude(id=self.user.id).count()
        self.assertEqual(len(response.data), all_users_except_main_n)
        print(response.data)
        for user in response.data:
            if user["username"] in follwing:
                self.assertEqual(user["following"], True)
            else:
                self.assertEqual(user["following"], False)
