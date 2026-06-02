from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone


class AlunoManager(BaseUserManager):
    def create_user(self, email, matricula, password=None, **extra_fields):
        if not email:
            raise ValueError('E-mail é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, matricula=matricula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, matricula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_ativo', True)
        return self.create_user(email, matricula, password, **extra_fields)


CAMPUS_CHOICES = [
    ('monte_castelo', 'São Luís - Monte Castelo'),
]

CURSO_CHOICES = [
    ('engenharia_civil', 'Engenharia Civil'),
    ('engenharia_eletrica_industrial', 'Engenharia Elétrica Industrial'),
    ('engenharia_mecanica_industrial', 'Engenharia Mecânica Industrial'),
    ('sistemas_informacao', 'Sistemas de Informação'),
    ('design', 'Design'),
    ('ciencias_biologicas', 'Ciências Biológicas'),
    ('fisica', 'Física'),
    ('matematica', 'Matemática'),
    ('quimica', 'Química'),
    ('processos_quimicos', 'Processos Químicos'),
]

CATEGORIA_CHOICES = [
    ('livros', 'Livros'),
    ('eletronicos', 'Eletrônicos'),
    ('academicos', 'Materiais Acadêmicos'),
    ('ferramentas', 'Ferramentas'),
    ('moveis', 'Móveis'),
    ('equipamentos', 'Equipamentos'),
    ('outros', 'Outros'),
]

ESTADO_CHOICES = [
    ('novo', 'Novo'),
    ('otimo', 'Ótimo'),
    ('bom', 'Bom'),
    ('regular', 'Regular'),
    ('ruim', 'Ruim'),
]

EMPRESTIMO_STATUS = [
    ('pendente', 'Pendente'),
    ('ativo', 'Ativo'),
    ('atrasado', 'Atrasado'),
    ('devolvido', 'Devolvido'),
    ('cancelado', 'Cancelado'),
]

DENUNCIA_MOTIVO = [
    ('conteudo_inadequado', 'Conteúdo inadequado'),
    ('informacao_falsa', 'Informações falsas'),
    ('item_proibido', 'Item proibido'),
    ('comportamento', 'Comportamento inadequado'),
    ('outro', 'Outro'),
]

DENUNCIA_STATUS = [
    ('pendente', 'Pendente'),
    ('em_analise', 'Em análise'),
    ('resolvida', 'Resolvida'),
    ('arquivada', 'Arquivada'),
]


class Aluno(AbstractBaseUser, PermissionsMixin):
    nome = models.CharField(max_length=150)
    matricula = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9]+$', 'Matrícula inválida')]
    )
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)

    curso = models.CharField(
        max_length=50,
        choices=CURSO_CHOICES,
        default='sistemas_informacao'
    )

    campus = models.CharField(
        max_length=50,
        choices=CAMPUS_CHOICES,
        default='monte_castelo'
    )

    foto = models.ImageField(
        upload_to='fotos_perfil/',
        blank=True,
        null=True
    )

    avaliacao_media = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    total_avaliacoes = models.PositiveIntegerField(default=0)

    emprestimos_realizados = models.PositiveIntegerField(default=0)
    emprestimos_concluidos = models.PositiveIntegerField(default=0)

    is_ativo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_bloqueado = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultimo_acesso = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['matricula', 'nome']
    objects = AlunoManager()

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['-data_cadastro']

    def __str__(self):
        return f'{self.nome} ({self.matricula})'

    @property
    def is_active(self):
        return self.is_ativo and not self.is_bloqueado

    def recalcular_avaliacao(self):
        avs = self.avaliacoes_recebidas.all()
        total = avs.count()

        if total:
            from django.db.models import Avg
            media = avs.aggregate(m=Avg('nota'))['m'] or 5.0
            self.avaliacao_media = round(media, 1)
        else:
            self.avaliacao_media = 5.0

        self.total_avaliacoes = total
        self.save(update_fields=['avaliacao_media', 'total_avaliacoes'])


class Item(models.Model):
    dono = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='itens')
    nome = models.CharField(max_length=200)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    descricao = models.TextField()
    prazo_maximo = models.CharField(max_length=50, default='Combinável')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='bom')
    foto = models.ImageField(upload_to='fotos_itens/', blank=True, null=True)
    disponivel = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    visualizacoes = models.PositiveIntegerField(default=0)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['-data_publicacao']

    def __str__(self):
        return f'{self.nome} — {self.dono.nome}'


class Emprestimo(models.Model):
    solicitante = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='emprestimos_solicitados'
    )
    dono = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='emprestimos_cedidos'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='emprestimos'
    )
    prazo_combinado = models.CharField(max_length=100, blank=True)
    data_prevista_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EMPRESTIMO_STATUS, default='pendente')
    observacoes = models.TextField(blank=True)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_devolucao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'{self.solicitante.nome} → {self.item.nome}'

    def verificar_atraso(self):
        if (
            self.status == 'ativo'
            and self.data_prevista_devolucao
            and timezone.now().date() > self.data_prevista_devolucao
        ):
            self.status = 'atrasado'
            self.save(update_fields=['status'])
            return True
        return False


class Avaliacao(models.Model):
    emprestimo = models.OneToOneField(
        Emprestimo,
        on_delete=models.CASCADE,
        related_name='avaliacao'
    )
    avaliador = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='avaliacoes_feitas'
    )
    avaliado = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='avaliacoes_recebidas'
    )
    nota = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Avaliação de {self.avaliador.nome} para {self.avaliado.nome} — {self.nota}★'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.avaliado.recalcular_avaliacao()


class Denuncia(models.Model):
    denunciante = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='denuncias_feitas'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='denuncias',
        null=True,
        blank=True
    )
    usuario_denunciado = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='denuncias_recebidas',
        null=True,
        blank=True
    )
    motivo = models.CharField(max_length=50, choices=DENUNCIA_MOTIVO)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=DENUNCIA_STATUS, default='pendente')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Denúncia'
        verbose_name_plural = 'Denúncias'
        ordering = ['-data_criacao']

    def __str__(self):
        return f'Denúncia de {self.denunciante.nome}'