from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model


class UserTests(APITestCase):

    def test_user_registration(self):
        url = '/accounts/register/'
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('user' in response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_user_profile(self):
        user = get_user_model().objects.create_user(
            username='testuser', email='testuser@example.com', password='password123'
        )
        self.client.login(username='testuser', password='password123')
        url = '/accounts/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
