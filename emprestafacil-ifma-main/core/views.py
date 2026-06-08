from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta, date

from .models import Aluno, Item, Emprestimo, Avaliacao, Denuncia
from .serializers import (
    AlunoSerializer, CadastroSerializer, LoginSerializer,
    ItemSerializer, ItemCreateSerializer,
    EmprestimoSerializer, AvaliacaoSerializer, DenunciaSerializer,
)


# ─── Auth ────────────────────────────────────────────────────────
class CadastroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = CadastroSerializer(data=request.data)
        if s.is_valid():
            user = s.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {'token': token.key, 'user': AlunoSerializer(user).data, 'mensagem': 'Cadastro realizado!'},
                status=status.HTTP_201_CREATED,
            )
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        if s.is_valid():
            user = s.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': AlunoSerializer(user).data})
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'mensagem': 'Logout realizado.'})


class EsqueciSenhaView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        nova_senha = request.data.get('nova_senha', '').strip()
        confirmar_senha = request.data.get('confirmar_senha', '').strip()

        if not email:
            return Response({'erro': 'Informe seu e-mail.'}, status=status.HTTP_400_BAD_REQUEST)

        if not nova_senha or not confirmar_senha:
            return Response({'erro': 'Informe e confirme a nova senha.'}, status=status.HTTP_400_BAD_REQUEST)

        if nova_senha != confirmar_senha:
            return Response({'erro': 'As senhas não conferem.'}, status=status.HTTP_400_BAD_REQUEST)

        aluno = Aluno.objects.filter(email__iexact=email).first()

        if not aluno:
            return Response({'erro': 'E-mail não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        aluno.set_password(nova_senha)
        aluno.save()

        Token.objects.filter(user=aluno).delete()

        return Response({'mensagem': 'Senha redefinida com sucesso! Faça login novamente.'}, status=status.HTTP_200_OK)

# ─── Perfil ──────────────────────────────────────────────────────

class MeuPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = AlunoSerializer

    def get_object(self):
        return self.request.user


class AlunoDetailView(generics.RetrieveAPIView):
    queryset         = Aluno.objects.filter(is_ativo=True, is_bloqueado=False)
    serializer_class = AlunoSerializer


# ─── Catálogo / Itens ────────────────────────────────────────────

class ItemPagination(PageNumberPagination):
    page_size            = 12
    page_size_query_param = 'page_size'
    max_page_size        = 48


class CatalogoView(generics.ListAPIView):
    """
    GET /api/itens/
    Filtros via query params:
      busca, categoria, campus, curso, disponivel, ordenar
    """
    serializer_class = ItemSerializer
    pagination_class = ItemPagination

    def get_queryset(self):
        qs = Item.objects.select_related('dono').all()
        p  = self.request.query_params

        busca = p.get('busca', '').strip()
        if busca:
            qs = qs.filter(Q(nome__icontains=busca) | Q(descricao__icontains=busca))

        categoria = p.get('categoria', '').strip()
        if categoria:
            qs = qs.filter(categoria=categoria)

        campus = p.get('campus', '').strip()
        if campus:
            qs = qs.filter(dono__campus=campus)

        curso = p.get('curso', '').strip()
        if curso:
            qs = qs.filter(dono__curso=curso)

        disponivel = p.get('disponivel', '').lower()
        if disponivel == 'true':
            qs = qs.filter(disponivel=True)
        elif disponivel == 'false':
            qs = qs.filter(disponivel=False)

        ordem_map = {
            'recente':   '-data_publicacao',
            'nome':      'nome',
            'avaliacao': '-dono__avaliacao_media',
        }
        qs = qs.order_by(ordem_map.get(p.get('ordenar', 'recente'), '-data_publicacao'))
        return qs


class ItemDetailView(generics.RetrieveAPIView):
    queryset         = Item.objects.select_related('dono').all()
    serializer_class = ItemSerializer

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        Item.objects.filter(pk=obj.pk).update(visualizacoes=obj.visualizacoes + 1)
        return super().retrieve(request, *args, **kwargs)


class MeusItensView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return ItemCreateSerializer if self.request.method == 'POST' else ItemSerializer

    def get_queryset(self):
        return Item.objects.filter(dono=self.request.user).order_by('-data_publicacao')

    def create(self, request, *args, **kwargs):
        s = ItemCreateSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            item = s.save()
            return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class MeuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ItemCreateSerializer

    def get_queryset(self):
        return Item.objects.filter(dono=self.request.user)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({'mensagem': 'Anúncio removido.'}, status=status.HTTP_204_NO_CONTENT)


# ─── Empréstimos ─────────────────────────────────────────────────

class MeusEmprestimosView(generics.ListCreateAPIView):
    serializer_class = EmprestimoSerializer

    def get_queryset(self):
        user = self.request.user
        tipo = self.request.query_params.get('tipo', 'solicitados')
        base = Emprestimo.objects.select_related(
            'solicitante', 'dono', 'item', 'item__dono'
        ).prefetch_related('avaliacao')

        # Atualiza atrasos automaticamente
        ativos = base.filter(status='ativo', data_prevista_devolucao__lt=timezone.now().date())
        ativos.update(status='atrasado')

        if tipo == 'cedidos':
            return base.filter(dono=user)
        return base.filter(solicitante=user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        s = EmprestimoSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            item = s.validated_data['item']
            if item.dono == request.user:
                return Response({'erro': 'Você não pode solicitar seu próprio item.'}, status=400)
            if not item.disponivel:
                return Response({'erro': 'Este item não está disponível.'}, status=400)
            emp = s.save()
            return Response(EmprestimoSerializer(emp, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class EmprestimoStatusView(APIView):
    """PATCH /api/emprestimos/<pk>/status/ — atualiza status do empréstimo."""

    STATUS_VALIDOS = ['ativo', 'devolvido', 'cancelado']

    def patch(self, request, pk):
        emp        = get_object_or_404(Emprestimo, pk=pk)
        novo_status = request.data.get('status')

        if novo_status not in self.STATUS_VALIDOS:
            return Response({'erro': f'Status inválido. Opções: {self.STATUS_VALIDOS}'}, status=400)

        if request.user not in (emp.dono, emp.solicitante):
            return Response({'erro': 'Sem permissão para alterar este empréstimo.'}, status=403)

        emp.status = novo_status

        if novo_status == 'ativo':
            # Marca item como indisponível
            Item.objects.filter(pk=emp.item.pk).update(disponivel=False)

        if novo_status == 'devolvido':
            emp.data_devolucao = timezone.now()
            # Libera o item
            Item.objects.filter(pk=emp.item.pk).update(disponivel=True)
            # Atualiza contadores
            Aluno.objects.filter(pk=emp.solicitante.pk).update(
                emprestimos_concluidos=emp.solicitante.emprestimos_concluidos + 1
            )
            Aluno.objects.filter(pk=emp.dono.pk).update(
                emprestimos_realizados=emp.dono.emprestimos_realizados + 1
            )

        if novo_status == 'cancelado':
            Item.objects.filter(pk=emp.item.pk).update(disponivel=True)

        emp.save()
        return Response(EmprestimoSerializer(emp, context={'request': request}).data)


# ─── Avaliações ──────────────────────────────────────────────────

class AvaliacaoCreateView(generics.CreateAPIView):
    """POST /api/avaliacoes/ — avalia um empréstimo após devolução."""
    serializer_class = AvaliacaoSerializer

    def create(self, request, *args, **kwargs):
        s = AvaliacaoSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            av = s.save()
            return Response(AvaliacaoSerializer(av).data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class AvaliacoesRecebidasView(generics.ListAPIView):
    """GET /api/avaliacoes/recebidas/ — lista avaliações recebidas pelo usuário logado."""
    serializer_class = AvaliacaoSerializer

    def get_queryset(self):
        return Avaliacao.objects.filter(avaliado=self.request.user).select_related(
            'avaliador', 'emprestimo__item'
        )


class AvaliacoesAlunoView(generics.ListAPIView):
    """GET /api/alunos/<pk>/avaliacoes/ — avaliações públicas de um aluno."""
    serializer_class = AvaliacaoSerializer

    def get_queryset(self):
        return Avaliacao.objects.filter(avaliado_id=self.kwargs['pk']).select_related(
            'avaliador', 'emprestimo__item'
        )


# ─── Denúncias ───────────────────────────────────────────────────

class DenunciaView(generics.CreateAPIView):
    serializer_class = DenunciaSerializer

    def create(self, request, *args, **kwargs):
        s = DenunciaSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            s.save()
            return Response({'mensagem': 'Denúncia registrada. Iremos analisar em breve.'}, status=201)
        return Response(s.errors, status=400)


# ─── Dashboard ───────────────────────────────────────────────────

class DashboardView(APIView):
    def get(self, request):
        from .models import CATEGORIA_CHOICES

        itens_por_cat = [
            {
                'categoria': cod,
                'nome': nome,
                'total': Item.objects.filter(categoria=cod).count(),
                'disponiveis': Item.objects.filter(categoria=cod, disponivel=True).count(),
            }
            for cod, nome in CATEGORIA_CHOICES
            if Item.objects.filter(categoria=cod).exists()
        ]

        emp_recentes = [
            {
                'id': e.id,
                'item': e.item.nome,
                'solicitante': e.solicitante.nome,
                'dono': e.dono.nome,
                'status': e.status,
                'data': e.data_solicitacao.strftime('%d/%m/%Y'),
            }
            for e in Emprestimo.objects.select_related('solicitante', 'dono', 'item').order_by('-data_solicitacao')[:5]
        ]

        return Response({
            'total_alunos':            Aluno.objects.filter(is_ativo=True).count(),
            'total_itens':             Item.objects.count(),
            'total_disponiveis':       Item.objects.filter(disponivel=True).count(),
            'total_emprestimos':       Emprestimo.objects.count(),
            'emprestimos_ativos':      Emprestimo.objects.filter(status__in=['ativo', 'atrasado']).count(),
            'emprestimos_devolvidos':  Emprestimo.objects.filter(status='devolvido').count(),
            'itens_por_categoria':     itens_por_cat,
            'emprestimos_recentes':    emp_recentes,
        })


# ─── Relatório Semanal ───────────────────────────────────────────

class RelatorioSemanalView(APIView):
    """
    GET /api/relatorio/semanal/?semana=YYYY-WW
    Retorna o relatório de empréstimos da semana indicada.
    Se não informado, usa a semana atual.
    Aceita ?formato=csv para exportar em texto CSV.
    """

    def _parse_semana(self, semana_str):
        """Recebe 'YYYY-WW' e retorna (date_inicio, date_fim)."""
        try:
            ano, sem = semana_str.split('-W')
            # Dia 1 da semana ISO
            inicio = date.fromisocalendar(int(ano), int(sem), 1)
        except Exception:
            hoje   = date.today()
            iso    = hoje.isocalendar()
            inicio = date.fromisocalendar(iso[0], iso[1], 1)
        return inicio, inicio + timedelta(days=6)

    def get(self, request):
        semana_str = request.query_params.get('semana', '')
        inicio, fim = self._parse_semana(semana_str) if semana_str else self._semana_atual()

        emprestimos = Emprestimo.objects.filter(
            data_solicitacao__date__range=(inicio, fim)
        ).select_related('solicitante', 'dono', 'item').order_by('data_solicitacao')

        linhas = [
            {
                'id':           e.id,
                'data':         e.data_solicitacao.strftime('%d/%m/%Y'),
                'item':         e.item.nome,
                'categoria':    e.item.get_categoria_display(),
                'quem_emprestou': e.dono.nome,
                'quem_recebeu': e.solicitante.nome,
                'campus':       e.dono.get_campus_display(),
                'status':       e.get_status_display(),
                'status_cod':   e.status,
                'data_prevista_devolucao': e.data_prevista_devolucao.strftime('%d/%m/%Y') if e.data_prevista_devolucao else '—',
                'data_devolucao': e.data_devolucao.strftime('%d/%m/%Y') if e.data_devolucao else '—',
            }
            for e in emprestimos
        ]

        resumo = {
            'total':      len(linhas),
            'ativos':     sum(1 for l in linhas if l['status_cod'] in ('ativo', 'pendente')),
            'devolvidos': sum(1 for l in linhas if l['status_cod'] == 'devolvido'),
            'atrasados':  sum(1 for l in linhas if l['status_cod'] == 'atrasado'),
            'cancelados': sum(1 for l in linhas if l['status_cod'] == 'cancelado'),
        }

        iso = inicio.isocalendar()

        # Exportação CSV
        if request.query_params.get('formato') == 'csv':
            return self._csv_response(linhas, inicio, fim)

        return Response({
            'semana':    f'{iso[0]}-W{iso[1]:02d}',
            'semana_label': f'Semana {iso[1]}/{iso[0]}',
            'periodo':   f'{inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}',
            'resumo':    resumo,
            'emprestimos': linhas,
        })

    def _semana_atual(self):
        hoje  = date.today()
        iso   = hoje.isocalendar()
        inicio = date.fromisocalendar(iso[0], iso[1], 1)
        return inicio, inicio + timedelta(days=6)

    def _csv_response(self, linhas, inicio, fim):
        from django.http import HttpResponse
        import csv, io

        buf = io.StringIO()
        w   = csv.writer(buf)
        w.writerow(['Data', 'Item', 'Categoria', 'Quem emprestou', 'Quem recebeu', 'Campus', 'Status', 'Prev. Devolução', 'Devolvido em'])
        for l in linhas:
            w.writerow([l['data'], l['item'], l['categoria'], l['quem_emprestou'],
                        l['quem_recebeu'], l['campus'], l['status'],
                        l['data_prevista_devolucao'], l['data_devolucao']])

        nome = f"relatorio_{inicio.strftime('%Y%m%d')}_{fim.strftime('%Y%m%d')}.csv"
        resp = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="{nome}"'
        return resp


# ─── Admin ───────────────────────────────────────────────────────

class AdminUsuariosView(generics.ListAPIView):
    serializer_class   = AlunoSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs    = Aluno.objects.all()
        busca = self.request.query_params.get('busca', '')
        if busca:
            qs = qs.filter(Q(nome__icontains=busca) | Q(matricula__icontains=busca))
        return qs


class AdminBloqueioView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        aluno = get_object_or_404(Aluno, pk=pk)
        aluno.is_bloqueado = not aluno.is_bloqueado
        aluno.save()
        acao = 'bloqueado' if aluno.is_bloqueado else 'desbloqueado'
        return Response({'mensagem': f'Usuário {acao}.'})


class AdminDenunciasView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = Denuncia.objects.select_related('denunciante', 'item', 'usuario_denunciado').all()
        data = [
            {
                'id':                d.id,
                'denunciante':       d.denunciante.nome,
                'item':              d.item.nome if d.item else None,
                'usuario_denunciado': d.usuario_denunciado.nome if d.usuario_denunciado else None,
                'motivo':            d.get_motivo_display(),
                'descricao':         d.descricao,
                'status':            d.status,
                'data':              d.data_criacao.strftime('%d/%m/%Y'),
            }
            for d in qs
        ]
        return Response(data)
