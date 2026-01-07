# app/models.py
from django.db import models
from django.contrib.auth.models import User # Django組み込みのUserモデルをインポート
class Post(models.Model):
    class Meta:
        app_label = 'testApp'
    # 投稿内容：文字数制限のないテキストフィールド
    content = models.TextField()

    # 投稿日時：データが作成された時に自動で日時を記録
    created_at = models.DateTimeField(auto_now_add=True)

    # 投稿者：Userモデルと「一対多」の関係で紐づける
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    def total_likes(self):
        return self.likes.count()
    def __str__(self):
        # 管理画面などで見やすいように、オブジェクトの文字列表現を定義
        return f'{self.author.username}: {self.content[:20]}'