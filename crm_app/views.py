from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy # リダイレクト先を指定するためにインポート
from .models import Customer, Activity
from .forms import CustomerForm, ActivityForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


# 顧客一覧ページ用のビュー
class CustomerListView(LoginRequiredMixin, ListView):
    """
    顧客一覧を表示するビュー(ListViewを継承)
    """
    # 1. どのモデルのデータを取得するか
    model = Customer
    # 2. どのテンプレートファイルを使うか
    template_name = 'crm_app/customer_list.html'
    # 3. テンプレート内で使う変数名(指定しない場合、 'object_list' になる)
    context_object_name = 'customers'
    # おまけ： 1ページに表示する件数
    paginate_by = 10
    # おまけ： 並び順の指定(会社名順)
    # queryset = Customer.objects.all().order_by('company_name')
    # ↑以下の処理を追加時にコメントアウトした。
    
    def get_queryset(self):
        # 1.まず、基本となる「自分の担当顧客」を取得(第5回の内容)
        queryset = Customer.objects.filter(user=self.request.user).order_by('company_name')
        # 2.GETパラメータから'query'(検索キーワード)を取得
        query = self.request.GET.get('query')
        
        # 3.キーワードが存在する場合のみ地堀込みを行う
        if query:
            # Qオブジェクトを使って「OR条件」を構築
            # icontainsは「大文字小文字を区別しない部分一致」
            # 空白くギリで複数のキーワードに対応させたい場合は、ここでsplit()してループさせる等の工夫も可能
            # 今回は単純な１語検索の拡張
            queryset = queryset.filter(
                Q(company_name__icontains=query) |
                Q(contact_name__icontains=query) |
                Q(email__icontains=query) |
                Q(tags__name__icontains=query) # タグの名前でも検索可能に追加
            ).distinct() # 重複を除外
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートのvalue="{{ query }}"に渡す値を設定
        context['query'] = self.request.GET.get('query', '')
        return context
    
# 顧客詳細ページ用のビュー
class CustomerDetailView(LoginRequiredMixin, DetailView):
    """
    顧客詳細を表示するビュー(DetailViewを継承)
    """
    # 1. どのモデルのデータを取得するか
    model = Customer
    # 2. どのテンプレートファイルを使うか
    template_name = 'crm_app/customer_detail.html'
    # 3. テンプレート内で使う変数名(指定しない場合、 'object' または 'customer' になる)
    context_object_name = 'customer'
    
    def get_queryset(self):
        # 自分が担当のデータのみを対象とする
        return Customer.objects.filter(user=self.request.user)
    
# 顧客の新規登録ビュー
class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm_app/customer_form.html' # 新規も更新も同じテンプレートを使い回す
    success_url = reverse_lazy('customer_list') # 成功したら一覧ページにリダイレクト
    
    def form_valid(self, form):
        # フォームが保存される直前に、担当営業(user)フィールドに
        # 現在ログインしているユーザー(self.request.user)をセットする
        form.instance.user = self.request.user
        
        # 親クラス(CreateView)のform_validを呼び出し、保存処理を続行
        return super().form_valid(form)
    
# 顧客の更新ビュー
class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm_app/customer_form.html' # 新規も更新も同じテンプレートを使い回す
    success_url = reverse_lazy('customer_list') # 成功したら一覧ページにリダイレクト
    # <int:pk>で渡されたIDの顧客データ自動でフォームにセットしてくれる
    
    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)

# 顧客の削除ビュー
class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'crm_app/customer_confirm_delete.html' # 削除確認用の専用テンプレート
    success_url = reverse_lazy('customer_list') # 成功したら一覧ページにリダイレクト
    
    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)
    
@login_required
@require_POST
def ajax_add_activity(request):
    customer_id = request.POST.get('customer_id')
    customer = get_object_or_404(Customer, id=customer_id)
    
    if customer.user != request.user:
        return JsonResponse({'message':'権限がありません'}, status=403)
    
    form = ActivityForm(request.POST)
    
    if form.is_valid():
        activity = form.save(commit=False)
        activity.customer = customer
        activity.save()
        
        response_data = {
            'message':'成功しました',
            'activity_date': activity.activity_date.strftime('%Y-%m-%d'),
            'status': activity.get_status_display(),
            'note': activity.note,
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({'message':'入力内容に誤りがあります', 'errors': form.errors}, status=400)