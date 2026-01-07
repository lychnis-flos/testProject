from rest_framework import serializers
from .models import Post
# Postモデル専門の翻訳者を定義
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post # 翻訳対象のモデルを指定
        # どのフィールドを翻訳（JSONに含める）するかを指定
        fields = ['id', 'content', 'created_at']