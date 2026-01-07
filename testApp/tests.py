from django.test import TestCase
from django.contrib.auth.models import User
from .models import Post

class PostModelTest(TestCase):
    def test_str_representation(self):
        # 1. Arrange (準備)
        user = User.objects.create_user(username='testuser', password='password')
        # 创建一个短内容，避免 __str__ 截断引发的混乱
        post = Post.objects.create(author=user, content='Simple Test Post') 
        
        # 2. Act (実行)
        str_output = str(post) 
        print(str_output)
        # 3. Assert (検証)
        # 预期输出应该是 '用户名: 内容' (不截断)
        self.assertEqual(str_output, 'testuser: Simple Test Post') # <--- 修正为正确的预期输出