from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────
    # ── Auth ──────────────────────────────
    path('auth/cadastro/', views.CadastroView.as_view(),  name='cadastro'),
    path('auth/login/',    views.LoginView.as_view(),     name='login'),
    path('auth/logout/',   views.LogoutView.as_view(),    name='logout'),
    path('auth/esqueci-senha/', views.EsqueciSenhaView.as_view(), name='esqueci-senha'),

    # ── Perfil ────────────────────────────
    path('perfil/',          views.MeuPerfilView.as_view(),   name='meu-perfil'),
    path('alunos/<int:pk>/', views.AlunoDetailView.as_view(), name='aluno-detail'),
    path('alunos/<int:pk>/avaliacoes/', views.AvaliacoesAlunoView.as_view(), name='aluno-avaliacoes'),

    # ── Itens / Catálogo ──────────────────
    path('itens/',                views.CatalogoView.as_view(),      name='catalogo'),
    path('itens/<int:pk>/',       views.ItemDetailView.as_view(),    name='item-detail'),
    path('meus-itens/',           views.MeusItensView.as_view(),     name='meus-itens'),
    path('meus-itens/<int:pk>/',  views.MeuItemDetailView.as_view(), name='meu-item-detail'),

    # ── Empréstimos ───────────────────────
    path('emprestimos/',                      views.MeusEmprestimosView.as_view(),  name='emprestimos'),
    path('emprestimos/<int:pk>/status/',      views.EmprestimoStatusView.as_view(), name='emprestimo-status'),

    # ── Avaliações ────────────────────────
    path('avaliacoes/',            views.AvaliacaoCreateView.as_view(),    name='avaliacao-create'),
    path('avaliacoes/recebidas/',  views.AvaliacoesRecebidasView.as_view(), name='avaliacoes-recebidas'),

    # ── Denúncias ─────────────────────────
    path('denuncias/', views.DenunciaView.as_view(), name='denuncia'),

    # ── Dashboard ─────────────────────────
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # ── Relatório semanal ─────────────────
    path('relatorio/semanal/', views.RelatorioSemanalView.as_view(), name='relatorio-semanal'),

    # ── Admin ─────────────────────────────
    path('admin-api/usuarios/',                    views.AdminUsuariosView.as_view(),  name='admin-usuarios'),
    path('admin-api/usuarios/<int:pk>/bloqueio/',  views.AdminBloqueioView.as_view(),  name='admin-bloqueio'),
    path('admin-api/denuncias/',                   views.AdminDenunciasView.as_view(), name='admin-denuncias'),
]
