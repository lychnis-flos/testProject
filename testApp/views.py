import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse 
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from rest_framework import generics
# APIアクセス時のエラー処理のためにrequests.exceptionsをインポート
from requests.exceptions import RequestException 

from .models import Post
from .forms import PostForm
from .serializers import PostSerializer 


# =================================================================
# 1. タイムライン関連ビュー (N+1問題解決済み、検索機能統合済み)
# =================================================================

def timeline(request):
    # URLのクエリパラメータから'q'の値を取得する
    query = request.GET.get('q')
    
    # 🌟 性能最適化: select_related('author') を全てのクエリに適用し、N+1問題を解決
    # これがベースとなるクエリセットであり、posts に代入する
    posts = Post.objects.select_related('author').order_by('-created_at')

    if query:
        # クエリがあれば、posts に、contentにその文字列を含む投稿をフィルタリング
        # [エラー修正点]: 未定義変数 base_query を削除し、posts を使用
        posts = posts.filter(content__icontains=query)
    # else:
        # クエリがない場合は、既に select_related が適用された全投稿データ (posts) が使われるため、
        # この else ブロックは不要です。
        
    context = {
        'posts': posts,
        'query': query, # 検索キーワードをテンプレートに渡す
    }
    return render(request, 'timeline.html', context)


def post_detail(request, pk):
    # pkを使って、Postオブジェクトを1件だけ取得する
    # 存在しない場合は404エラーを返す
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'post_detail.html', {'post': post})

@login_required
def post_create(request):
    # 1. POSTリクエスト（送信ボタン押下時）の処理
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('timeline')
    # 2. GETリクエスト（ページ初回表示時）の処理
    else:
        form = PostForm() # 空のフォームを作成
    # 3. GETリクエスト、または POSTが失敗した場合
    return render(request, 'post_create.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk) 
    # 権限チェック：投稿者とログインユーザーが一致しない場合はリダイレクト
    if request.user != post.author:
        return redirect('post_detail', pk=pk)
        
    if request.method == 'POST':
        # 既存のインスタンスを渡してフォームを生成
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=pk)
    else:
        # 既存のインスタンスを渡してフォームを生成（初期表示）
        form = PostForm(instance=post)
        
    return render(request, 'post_edit.html', {'form': form, 'post': post})
    
@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author:
        return redirect('post_detail', pk=pk)
    if request.method == 'POST':
        post.delete() # データを削除
        return redirect('timeline') # タイムラインにリダイレクト
        
    return render(request, 'post_confirm_delete.html', {'post': post})


def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    if post.likes.filter(id=user.id).exists():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True
        
    context = {
    'liked': liked, # 今の状態（いいねしたのか、外したのか）
    'count': post.total_likes(), # 最新のいいね数
    }
    # JsonResponseを使ってJSON形式で返却
    return JsonResponse(context)


# =================================================================
# 2. 外部API関連ビュー (エラー処理強化済み)
# =================================================================

def weather(request):
# 1. 都市と座標の辞書を定義
    locations = {
    'Kanazawa': {'lat': 36.59, 'lon': 136.60},
    'Tokyo': {'lat': 35.68, 'lon': 139.76},
    'Osaka': {'lat': 34.69, 'lon': 135.50},
    'Sapporo': {'lat': 43.06, 'lon': 141.35},
    'Naha': {'lat': 26.21, 'lon': 127.68},
    }
    # 2. デフォルトは金沢 GETリクエストで指定があれば変更する
    city_name = 'Kanazawa'
    if request.GET.get('city') and request.GET.get('city') in locations:
        city_name = request.GET.get('city')
    # 3. 辞書から緯度・経度を取り出す
    lat = locations[city_name]['lat']
    lon = locations[city_name]['lon']
    
    # 4. APIへのリクエストURLを作成 (open-meteo.comに注意)
    api_url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true'
    
    try:
        # 5. requestsを使ってデータを取得し、接続・HTTPエラーをチェック
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # 4xx, 5xxエラー時に例外を発生させる
        
        # 6. JSON解析
        data = response.json()
        
        # 7. テンプレートに渡すデータを作成
        context = {
            'city': city_name,
            'temperature': data['current_weather']['temperature'],
            'windspeed': data['current_weather']['windspeed'],
            'weathercode': data['current_weather']['weathercode'],
        }
        
    except (RequestException, ValueError, KeyError):
        # 接続エラー、JSON解析エラー、データ構造エラーをキャッチ
        context = {
            'city': city_name,
            'error_message': "天気情報の取得に失敗しました。APIサーバーまたはネットワークを確認してください。",
            'temperature': '---',
            'windspeed': '---',
            'weathercode': '---',
        }
        
    return render(request, 'weather.html', context)
    
    
def dog(request):
    api_url = "https://dog.ceo/api/breeds/image/random"
    api_key = "your_secret_api_key_here"
    header_data = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get(api_url, headers=header_data, timeout=10)
        print(f"DEBUG: Status Code: {response.status_code}")
        response.raise_for_status() 
        data = response.json()
        if data.get("status") == "success":
            image_url = data.get("message")
            error_message = None
        else:
            image_url = None
            error_message = "API 响应状态异常。"
            
    except (RequestException, ValueError):
        image_url = None
        error_message = "访问狗图 API 失败，请检查网络或认证信息。"
        
    context = {
        "image_url": image_url,
        "error_message": error_message,
    }
    return render(request, "dog.html", context)

# =================================================================
# 3. 認証・APIエンドポイント関連ビュー
# =================================================================

class PostListAPIView(generics.ListAPIView):
# どのデータの一覧を返すか
    queryset = Post.objects.all()
    # どの翻訳者（シリアライザ）を使ってJSONに変換するか
    serializer_class = PostSerializer

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # 登録成功後はログインページへ
    template_name = 'signup.html'