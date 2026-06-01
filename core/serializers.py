from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import Aluno, Item, Emprestimo, Avaliacao, Denuncia


# ─── Aluno ───────────────────────────────────────────────────────

class AlunoPublicoSerializer(serializers.ModelSerializer):
    campus_display = serializers.CharField(source='get_campus_display', read_only=True)
    curso_display  = serializers.CharField(source='get_curso_display', read_only=True)

    class Meta:
        model  = Aluno
        fields = [
            'id', 'nome', 'curso', 'curso_display',
            'campus', 'campus_display', 'foto',
            'avaliacao_media', 'total_avaliacoes',
            'emprestimos_realizados', 'emprestimos_concluidos',
        ]


class AlunoSerializer(serializers.ModelSerializer):
    campus_display = serializers.CharField(source='get_campus_display', read_only=True)
    curso_display  = serializers.CharField(source='get_curso_display', read_only=True)
    total_itens    = serializers.SerializerMethodField()

    class Meta:
        model  = Aluno
        fields = [
            'id', 'nome', 'matricula', 'email', 'telefone',
            'curso', 'curso_display', 'campus', 'campus_display',
            'foto', 'avaliacao_media', 'total_avaliacoes',
            'emprestimos_realizados', 'emprestimos_concluidos',
            'data_cadastro', 'total_itens',
        ]
        read_only_fields = [
            'matricula', 'email', 'avaliacao_media', 'total_avaliacoes',
            'emprestimos_realizados', 'emprestimos_concluidos', 'data_cadastro',
        ]

    def get_total_itens(self, obj):
        return obj.itens.filter(disponivel=True).count()


class CadastroSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = Aluno
        fields = ['nome', 'matricula', 'email', 'telefone', 'curso', 'campus', 'password', 'password2']

    def validate_email(self, value):
        dominios = ('@acad.ifma.edu.br', '@ifma.edu.br')
        if not any(value.endswith(d) for d in dominios):
            raise serializers.ValidationError(
                'Use seu e-mail institucional (@acad.ifma.edu.br ou @ifma.edu.br).'
            )
        return value

    def validate_matricula(self, value):
        value = value.upper()
        if Aluno.objects.filter(matricula=value).exists():
            raise serializers.ValidationError('Esta matrícula já está cadastrada.')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'As senhas não coincidem.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = Aluno(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('E-mail ou senha inválidos.')
        if user.is_bloqueado:
            raise serializers.ValidationError('Conta bloqueada. Contate a administração.')
        data['user'] = user
        return data


# ─── Item ────────────────────────────────────────────────────────

class ItemSerializer(serializers.ModelSerializer):
    dono              = AlunoPublicoSerializer(read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    estado_display    = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model  = Item
        fields = [
            'id', 'dono', 'nome', 'categoria', 'categoria_display',
            'descricao', 'prazo_maximo', 'estado', 'estado_display',
            'foto', 'disponivel', 'observacoes', 'visualizacoes',
            'data_publicacao',
        ]
        read_only_fields = ['dono', 'visualizacoes', 'data_publicacao']


class ItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Item
        fields = [
            'nome', 'categoria', 'descricao', 'prazo_maximo',
            'estado', 'foto', 'disponivel', 'observacoes',
        ]

    def create(self, validated_data):
        validated_data['dono'] = self.context['request'].user
        return super().create(validated_data)


# ─── Avaliação ───────────────────────────────────────────────────

class AvaliacaoSerializer(serializers.ModelSerializer):
    avaliador_nome = serializers.CharField(source='avaliador.nome', read_only=True)
    avaliado_nome  = serializers.CharField(source='avaliado.nome', read_only=True)
    item_nome      = serializers.CharField(source='emprestimo.item.nome', read_only=True)

    class Meta:
        model  = Avaliacao
        fields = [
            'id', 'emprestimo', 'avaliador', 'avaliador_nome',
            'avaliado', 'avaliado_nome', 'item_nome',
            'nota', 'comentario', 'data_criacao',
        ]
        read_only_fields = ['avaliador', 'avaliado', 'data_criacao']

    def validate_emprestimo(self, emprestimo):
        user = self.context['request'].user
        # Apenas o solicitante pode avaliar após a devolução
        if emprestimo.solicitante != user:
            raise serializers.ValidationError('Apenas quem recebeu o item pode avaliar.')
        if emprestimo.status not in ('devolvido',):
            raise serializers.ValidationError('Só é possível avaliar após a devolução do item.')
        if hasattr(emprestimo, 'avaliacao'):
            raise serializers.ValidationError('Este empréstimo já foi avaliado.')
        return emprestimo

    def create(self, validated_data):
        emprestimo = validated_data['emprestimo']
        validated_data['avaliador'] = self.context['request'].user
        validated_data['avaliado']  = emprestimo.dono
        return super().create(validated_data)


# ─── Empréstimo ──────────────────────────────────────────────────

class EmprestimoSerializer(serializers.ModelSerializer):
    solicitante      = AlunoPublicoSerializer(read_only=True)
    dono             = AlunoPublicoSerializer(read_only=True)
    item             = ItemSerializer(read_only=True)
    item_id          = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source='item', write_only=True
    )
    status_display   = serializers.CharField(source='get_status_display', read_only=True)
    avaliacao        = AvaliacaoSerializer(read_only=True)
    pode_avaliar     = serializers.SerializerMethodField()

    class Meta:
        model  = Emprestimo
        fields = [
            'id', 'solicitante', 'dono', 'item', 'item_id',
            'prazo_combinado', 'data_prevista_devolucao',
            'status', 'status_display', 'observacoes',
            'data_solicitacao', 'data_devolucao',
            'avaliacao', 'pode_avaliar',
        ]
        read_only_fields = ['solicitante', 'dono', 'status', 'data_solicitacao', 'data_devolucao']

    def get_pode_avaliar(self, obj):
        user = self.context.get('request') and self.context['request'].user
        if not user:
            return False
        return (
            obj.status == 'devolvido'
            and obj.solicitante == user
            and not hasattr(obj, 'avaliacao')
        )

    def create(self, validated_data):
        request = self.context['request']
        item = validated_data['item']
        validated_data['solicitante'] = request.user
        validated_data['dono']        = item.dono
        return super().create(validated_data)


# ─── Denúncia ────────────────────────────────────────────────────

class DenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Denuncia
        fields = ['id', 'item', 'usuario_denunciado', 'motivo', 'descricao', 'data_criacao']
        read_only_fields = ['data_criacao']

    def create(self, validated_data):
        validated_data['denunciante'] = self.context['request'].user
        return super().create(validated_data)
