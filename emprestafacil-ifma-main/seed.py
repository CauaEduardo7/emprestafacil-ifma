import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emprestafacil.settings')
django.setup()

from core.models import Aluno, Item, Emprestimo, Avaliacao
from datetime import date, timedelta

# Admin
admin, _ = Aluno.objects.get_or_create(
    email='admin@ifma.edu.br',
    defaults={'nome': 'Administrador IFMA', 'matricula': 'ADMIN001',
              'curso': 'ads', 'campus': 'monte_castelo',
              'is_staff': True, 'is_superuser': True, 'is_ativo': True}
)
admin.set_password('admin123'); admin.save()

alunos_data = [
    ('joao.santos@acad.ifma.edu.br', 'João Silva Santos',    '20221TADS0142', 'ads',          'monte_castelo', '(98) 98765-4321'),
    ('maria.lima@acad.ifma.edu.br',  'Maria Oliveira Lima',  '20221TADS0205', 'ads',          'maracana',      '(98) 99876-5432'),
    ('pedro.costa@acad.ifma.edu.br', 'Pedro Costa Alves',   '20201EDIF0033', 'edificacoes',  'monte_castelo', '(98) 97654-3210'),
    ('ana.ferreira@acad.ifma.edu.br','Ana Paula Ferreira',   '20211ADMI0088', 'administracao','imperatriz',    '(99) 98888-7777'),
    ('carlos.souza@acad.ifma.edu.br','Carlos Henrique Souza','20221ELET0019', 'eletrotecnica','timon',         '(99) 97777-6666'),
]

alunos = []
for email, nome, mat, curso, campus, tel in alunos_data:
    a, created = Aluno.objects.get_or_create(email=email, defaults={
        'nome': nome, 'matricula': mat, 'curso': curso,
        'campus': campus, 'telefone': tel, 'is_ativo': True,
        'emprestimos_realizados': 5, 'emprestimos_concluidos': 4,
    })
    if created:
        a.set_password('senha123'); a.save()
    alunos.append(a)

itens_data = [
    (alunos[0], 'Cálculo I – Stewart 8ª Ed.',    'livros',       'Livro completo de Cálculo I.',        '2 semanas', 'otimo',  True),
    (alunos[0], 'Carregador USB-C 65W',           'eletronicos',  'Carregador universal USB-C.',         '1 semana',  'bom',    True),
    (alunos[1], 'Notebook Dell Inspiron 15',       'eletronicos',  'Notebook Dell i5 8GB RAM 256GB SSD.', '3 dias',    'otimo',  True),
    (alunos[1], 'Calculadora HP 50g',              'academicos',   'Calculadora científica HP 50g.',      '2 semanas', 'bom',    True),
    (alunos[2], 'Prancheta A1 com Paralela',       'academicos',   'Prancheta A1 com régua paralela.',    '1 mês',     'bom',    True),
    (alunos[2], 'Kit de Ferramentas Manuais',      'ferramentas',  'Kit com martelo, chaves e alicate.',  '1 semana',  'bom',    True),
    (alunos[3], 'Fone Sony WH-1000XM4',            'eletronicos',  'Fone bluetooth com cancelamento.',    '3 dias',    'novo',   True),
    (alunos[3], 'Álgebra Linear – Boldrini',       'livros',       'Álgebra Linear e Aplicações.',        '2 semanas', 'bom',    True),
    (alunos[4], 'Multímetro Digital Minipa',       'equipamentos', 'Medição de tensão, corrente e R.',   '3 dias',    'otimo',  True),
    (alunos[4], 'Arduino Uno R3 + Kit Sensores',   'equipamentos', 'Arduino com kit completo.',           '2 semanas', 'otimo',  True),
    (alunos[0], 'Cadeira de Escritório Ergonômica','moveis',       'Cadeira para home office.',           '1 mês',     'bom',    False),
    (alunos[1], 'Gravador de Voz Digital 8GB',     'eletronicos',  'Gravador para aulas e entrevistas.',  '1 semana',  'bom',    True),
]

itens = []
for dono, nome, cat, desc, prazo, estado, disp in itens_data:
    item, _ = Item.objects.get_or_create(nome=nome, dono=dono, defaults={
        'categoria': cat, 'descricao': desc, 'prazo_maximo': prazo,
        'estado': estado, 'disponivel': disp, 'visualizacoes': 12,
    })
    itens.append(item)

# Empréstimos de exemplo
hoje = date.today()
emp_data = [
    (alunos[1], alunos[0], itens[0], 'devolvido', hoje - timedelta(days=8), hoje - timedelta(days=2)),
    (alunos[2], alunos[1], itens[2], 'ativo',     hoje - timedelta(days=3), hoje + timedelta(days=4)),
    (alunos[3], alunos[1], itens[3], 'devolvido', hoje - timedelta(days=12),hoje - timedelta(days=5)),
    (alunos[0], alunos[2], itens[4], 'atrasado',  hoje - timedelta(days=10),hoje - timedelta(days=3)),
    (alunos[4], alunos[3], itens[6], 'pendente',  None,                     hoje + timedelta(days=7)),
]

emprestimos = []
for sol, dono, item, status, data_prev, data_prev_dev in emp_data:
    from django.utils import timezone as tz
    emp, created = Emprestimo.objects.get_or_create(
        solicitante=sol, dono=dono, item=item,
        defaults={
            'status': status,
            'prazo_combinado': '1 semana',
            'data_prevista_devolucao': data_prev_dev if data_prev_dev else None,
            'data_devolucao': tz.now() - timedelta(days=2) if status == 'devolvido' else None,
        }
    )
    if created and status == 'devolvido':
        # Marca item como disponível
        item.disponivel = True; item.save()
    emprestimos.append(emp)

# Avaliações
avs_data = [
    (emprestimos[0], alunos[1], alunos[0], 5, 'Excelente! Devolveu no prazo e o livro estava impecável.'),
    (emprestimos[2], alunos[3], alunos[1], 4, 'Bom colega, cuidou bem da calculadora. Recomendo!'),
]
for emp, avaliador, avaliado, nota, comentario in avs_data:
    Avaliacao.objects.get_or_create(emprestimo=emp, defaults={
        'avaliador': avaliador, 'avaliado': avaliado,
        'nota': nota, 'comentario': comentario,
    })

# Recalcula médias
for a in alunos:
    a.recalcular_avaliacao()

print('✅ Dados de exemplo criados!')
print('   Admin: admin@ifma.edu.br / admin123')
print('   Aluno: joao.santos@acad.ifma.edu.br / senha123')
