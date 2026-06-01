from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Aluno, Item, Emprestimo, Avaliacao, Denuncia


@admin.register(Aluno)
class AlunoAdmin(UserAdmin):
    model        = Aluno
    list_display = ['nome', 'matricula', 'email', 'campus', 'curso', 'avaliacao_media', 'is_bloqueado', 'data_cadastro']
    list_filter  = ['campus', 'curso', 'is_bloqueado', 'is_staff']
    search_fields = ['nome', 'matricula', 'email']
    ordering     = ['-data_cadastro']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dados Pessoais', {'fields': ('nome', 'matricula', 'telefone', 'foto')}),
        ('Acadêmico', {'fields': ('curso', 'campus')}),
        ('Estatísticas', {'fields': ('avaliacao_media', 'total_avaliacoes', 'emprestimos_realizados', 'emprestimos_concluidos')}),
        ('Permissões', {'fields': ('is_ativo', 'is_bloqueado', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'matricula', 'nome', 'curso', 'campus', 'password1', 'password2'),
        }),
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = ['nome', 'dono', 'categoria', 'disponivel', 'visualizacoes', 'data_publicacao']
    list_filter   = ['categoria', 'disponivel', 'estado']
    search_fields = ['nome', 'dono__nome', 'descricao']
    ordering      = ['-data_publicacao']


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display  = ['item', 'solicitante', 'dono', 'status', 'data_solicitacao', 'data_prevista_devolucao']
    list_filter   = ['status']
    search_fields = ['item__nome', 'solicitante__nome', 'dono__nome']
    date_hierarchy = 'data_solicitacao'


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display  = ['avaliador', 'avaliado', 'nota', 'emprestimo', 'data_criacao']
    list_filter   = ['nota']
    search_fields = ['avaliador__nome', 'avaliado__nome']
    ordering      = ['-data_criacao']


@admin.register(Denuncia)
class DenunciaAdmin(admin.ModelAdmin):
    list_display = ['denunciante', 'motivo', 'status', 'data_criacao']
    list_filter  = ['motivo', 'status']
