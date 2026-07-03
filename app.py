import streamlit as st
import pandas as pd
import sqlite3
import re
import random
from datetime import datetime, date

# 1. CONFIGURAÇÃO DO BANCO DE DADOS
def conectar_banco():
    conn = sqlite3.connect('controle_estoque.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            separador TEXT,
            produto TEXT,
            quantidade INTEGER,
            hora_inicio TEXT,
            hora_fim TEXT,
            data TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    return conn

conn = conectar_banco()

# 2. FUNÇÕES AUXILIARES
def calcular_minutos(h_inicio, h_fim):
    try:
        formato = "%H:%M"
        inicio = datetime.strptime(h_inicio, formato)
        fim = datetime.strptime(h_fim, formato)
        if fim < inicio:
            return ((fim - inicio).seconds / 60) + 1440
        return (fim - inicio).seconds / 60
    except:
        return 0

def auto_corrigir_hora(texto):
    numeros = re.sub(r'\D', '', texto) if texto else ''
    if not numeros: return None
    if len(numeros) == 1: numeros = f"0{numeros}00"
    elif len(numeros) == 2: numeros = f"{numeros}00"
    elif len(numeros) == 3: numeros = f"0{numeros}"
    elif len(numeros) > 4: numeros = numeros[:4]
    hora, minuto = int(numeros[:2]), int(numeros[2:])
    if hora > 23: hora = 23
    if minuto > 59: minuto = 59
    return f"{hora:02d}:{minuto:02d}"

def obter_bom_dia():
    hora = datetime.now().hour
    if hora < 12: return "Bom dia"
    elif hora < 18: return "Boa tarde"
    else: return "Boa noite"

# =====================================================================
# ÁREA DE EDIÇÃO: SEPARADORES, SETORES, SENHAS E PRODUTOS
# =====================================================================

separadores_texto = """
Henrique
Fran
Leonardo
Patrick
Fabiano
Sérgio
Marcello
"""

aprendizes_texto = """
Renan
"""

setor_separadores = {
    "Henrique": "Torres",
    "Fran": "Torres",
    "Leonardo": "Torres",
    "Patrick": "Torres",
    "Fabiano": "Caixas",
    "Marcello": "Caixas",
    "Sérgio": "Caixas",
    "Renan": "Caixas"
}

senhas_separadores = {
    "Henrique": "1010",
    "Fran": "2020",
    "Leonardo": "3030",
    "Patrick": "4040",
    "Fabiano": "5050",
    "Sérgio": "6060",
    "Marcello": "7070",
    "Renan": "8080"
}

# MEGA DICIONÁRIO DE INTERAÇÕES 
mensagens_personalizadas = {
    "Henrique": {
        "saudacao": [
            "E aí Henrique! Estacionou o Vectra na vaga hoje ou subiu no canteiro de novo? 🚗🪴",
            "Cuidado com a calçada na hora de ir embora com o Vectra, hein! 🛑🚙",
            "Fala piloto! Hoje a rota é pelo asfalto ou por cima do canteiro? 🌿🏎️",
            "Já deu aquele trato no Vectra branco hoje? 🚗💨",
            "Pronto pra acelerar na produção pique Vectra na rodovia? 🛣️",
            "O Vectra tá brilhando no estacionamento hoje? ✨",
            "Bora botar a produção pra andar mais rápido que o Vectra! 🏎️",
            "Aí sim! Chegou o piloto do Vectra branco! Bora trampar! 🏁",
            "E aí Henrique, já calibrou os pneus do Vectra hoje? 🚗💨",
            "O motor do Vectra já tá aquecido pra bater meta? 🔥"
        ],
        "elogio": [
            "Passou por cima da meta igual passa por cima do canteiro! Aí sim! 🚀🪴",
            "Produção tão rápida que até subiu na calçada! Voou, Henrique! 🚙💨",
            "Não tem obstáculo pra você! Passa por cima da meta e do canteiro se precisar! 🏆🌿",
            "Acelerando na produção mais que o Vectra na reta! Foguete! 🚀",
            "Zero a cem em 3 segundos nessa meta! Brabíssimo! 🏎️",
            "Pisou fundo agora, hein! 💨",
            "O Vectra branco passou voando! Boa, Henrique! 🦅",
            "Com essa velocidade, nem radar pega! Sensacional! 📸",
            "Passou a quinta marcha e sumiu! Foguete! 🚀",
            "Produzindo no estilo Vectra: com classe e velocidade! 🏆"
        ]
    },
    "Fran": {
        "saudacao": [
            "Opa, Catarina na área! Vai rolar aquele sushi caprichado mais tarde? 🍣",
            "Já separou o shoyu pra hoje, Catarina? 🥢",
            "A melhor sushiman da empresa chegou! 🍱",
            "Bora produzir com a mesma precisão que você corta um salmão! 🔪🐟",
            "Preparada pra enrolar essas metas igual temaki? 🍙",
            "Catarina chegou! O salmão já tá fresco pra hoje? 🍣",
            "Bora enrolar essas metas com a mesma agilidade dos sushis! 🍱",
            "Prepara o wasabi que a Catarina chegou com tudo! 🔥",
            "Sushiman de elite no estoque! Pra cima, Fran! 🥢",
            "O menu degustação hoje é de metas batidas, Catarina? 🏆"
        ],
        "elogio": [
            "Trabalho fino e de qualidade, igualzinho ao seu sushi, Catarina! 🍣🔥",
            "Entregou tudo num combo premium! 🍱",
            "Qualidade nota 10, estilo chef Catarina! 🔪",
            "Mandou bem demais! Merece até um combinado de salmão hoje! 🍣🏆",
            "Produção rodando lisinha igual faca de sushiman! Aulas! 🥢",
            "Produção nota 10, com aquele toque de chef! 👩‍🍳",
            "Cortou as pendências igual faca afiada! Samurai! 🥷",
            "Estoque tá igual rodízio: não para de chegar coisa boa! 🍣🚀",
            "Aí sim, Catarina! Entregando qualidade premium! ⭐",
            "Até o mestre do sushi ficaria com inveja dessa agilidade! 👏"
        ]
    },
    "Leonardo": {
        "saudacao": [
            "E aí Magrão! O Kadettão vermelho tá brilhando hoje? 🚗🔴",
            "Pronto pra botar a fábrica pra girar no vermelho, Magrão? 🔴🔥",
            "Deixou o Kadett descansando ou veio acelerando, Magrão? 🏁",
            "Bora! Produção pedindo aquele motor de Kadett! 🚀",
            "Aí o Magrão chegou! O terror dos radares com o Kadett vermelho! 🚦",
            "Fala Magrão! O Kadett tá roncando alto hoje? 🚗💨",
            "Bora botar o Kadettão na rua e a produção na tela! 🔴",
            "O asfalto até ferveu quando o Kadett do Magrão chegou! 🔥",
            "Aperta o cinto que o Magrão chegou pra acelerar! 🏎️",
            "E aí Magrão! Kadett vermelho no estacionamento é sinal de meta batida! 🏁"
        ],
        "elogio": [
            "Mais rápido que o Kadett vermelho na descida, Magrão! Voou! 🦅",
            "Velocidade máxima atingida! Parabéns Magrão! 🏆",
            "O Magrão botou o Kadett na pista e ninguém segura! 🏎️💨",
            "Fez a curva e bateu a meta! Monstro! 🏁",
            "Brabo! O Kadett vermelho tem que respeitar essa produção! 🚀",
            "O Magrão não anda, ele desfila! Amassou na produção! 🏆",
            "Queimou pneu e deixou a concorrência comendo poeira! 💨",
            "No estilo Kadett: clássico, rápido e imparável! 🔴🚀",
            "Aceleração pura, Magrão! Ninguém te alcança hoje! 🦅",
            "Pisou no acelerador da produtividade! Gênio! 👏"
        ]
    },
    "Patrick": {
        "saudacao": [
            "E as vendas de bolacha, tão rendendo? 🍪💰",
            "Trouxe pacote de bolacha pra galera hoje, Patrick? 🍪👀",
            "O rei da bolacha tá na área! Bora produzir! 👑",
            "Hoje é dia de faturar no estoque e na bolacha! 💸",
            "Pique fábrica de bolacha: produção a milhão! 🏭🍪",
            "Patrick na área! Já garantiu o estoque de bolacha da firma? 🍪",
            "Bora adoçar o dia com muita produção e venda de bolacha! 💰",
            "O magnata das bolachas chegou pra dominar o estoque! 👑",
            "Seja bem-vindo, Patrick! O café com bolacha já tá no esquema? ☕",
            "Hoje a meta é vender muito e produzir mais ainda! Pra cima! 🚀"
        ],
        "elogio": [
            "Produzindo mais que a fábrica de bolacha inteira! Brabo! 🍪🚀",
            "Caiu o pix da bolacha e a meta de produção! Aí sim! 💸🔥",
            "Bolacha crocante e meta batida! Voando, Patrick! 🦅",
            "O cara é bom de venda e bom de produção! Monstro! 🏆",
            "Estoque tá cheio igual pacote novo! Mandou bem! 📦",
            "Empreendedorismo e produção! Esse é o Patrick! 💸",
            "Mais uma caixa pronta, mais uma bolacha vendida! Sucesso! 🍪🔥",
            "O cara é um fenômeno nos dois estoques: no nosso e no das bolachas! 📦",
            "Lucro alto e meta batida! Patrick voando! 🦅",
            "É o CEO do estoque! Parabéns pelo trampo! 🏆"
        ]
    },
    "Fabiano": {
        "saudacao": [
            "Respeita a experiência! (Ou devo dizer Vovô? 👴🏼😂)",
            "O Vovô chegou! A sabedoria da empresa tá on! 🧠💡",
            "Bora ensinar a garotada como se faz, Fabiano? 📚",
            "A coluna tá boa pra bater meta hoje, Fabiano? Brincadeira! 😂",
            "Salve Vovô! Prepara o café forte que hoje tem! ☕",
            "A lenda viva chegou! Salve, Fabiano! 🏆",
            "Abre alas pro Vovô que ele vai mostrar como se faz! 👴🏼🚀",
            "E aí Fabiano! A experiência em pessoa tá na área! 🧠",
            "Vovô on-line! Prestem atenção nas aulas, pessoal! 📚",
            "Mostrando serviço e liderando o time! Bora Vovô! 💪"
        ],
        "elogio": [
            "Aí sim, Vovô! Mostrando pra garotada como é que se trabalha de verdade! 🏆",
            "A experiência conta muito! Trabalho impecável, Fabiano! 👏",
            "Velha guarda amassando nas metas! Brabo demais! 👴🏼🚀",
            "Fez parecer fácil! Vovô tem a manha! 🎮",
            "Aulas de produção com o Fabiano! Os novinhos piram! 📚🔥",
            "Com essa bagagem toda, a produção até sai mais fácil! 💼",
            "Vovô tá on fire! O terror da garotada nova! 🔥",
            "A sabedoria vence a pressa! Trabalho perfeito, Fabiano! 🥇",
            "Mostrando que panela velha é que faz comida boa! Brabo! 🍲",
            "Impecável como sempre! Aulas y aulas, Fabiano! 👏"
        ]
    },
    "Sérgio": {
        "saudacao": [
            "Tá sobrando tempo pra treinar as tartarugas hoje, Sérgio? 🐢😂",
            "As tartarugas já tão ninjas? 🥷🐢",
            "Acelera aí pra não ficar no ritmo das tartarugas, Sérgio! 🏃‍♂️💨",
            "E aí mestre Splinter, como tão as tartarugas? 🐢🍕",
            "Sérgio na área! Bora botar velocidade ninja hoje! ⚡",
            "Sérgio, as tartarugas comeram muita pizza hoje? 🍕🐢",
            "Prepara o casco que hoje o dia promete, Mestre! 🥷",
            "E aí Sérgio! O treinamento ninja hoje é aqui no estoque? ⚔️",
            "As tartarugas tão na torcida por você hoje! Bora! 🐢🏁",
            "Salve Sérgio! Cuidado pra não ficar na velocidade do casco hoje, hein! 🏃‍♂️💨"
        ],
        "elogio": [
            "Boa! Se treinar tartaruga já dá trabalho, imagina bater essa meta! Sensacional! 🐢🔥",
            "Ritmo de lebre, nada de tartaruga! Voou, Sérgio! 🦅",
            "Mestre das tartarugas e da produção! Parabéns! 🏆",
            "Ninja demais! Aprovado com sucesso! 🥷",
            "Tá mais rápido que tartaruga ladeira abaixo! Mandou bem! 🚀",
            "Movimentos calculados, pura técnica ninja no estoque! 🥷🔥",
            "As tartarugas tão orgulhosas dessa velocidade toda! 🐢🚀",
            "Cawabunga, Sérgio! Amassou demais na produção! 🍕🏆",
            "Ritmo insano, nem o Mestre Splinter te segura! 🐀💨",
            "Evoluiu da tartaruga pro guepardo! Aí sim! 🐆"
        ]
    },
    "Marcello": {
        "saudacao": [
            "Como você sempre diz: Foco na PRODUÇÃO! 🏭👊",
            "Chegou o homem que respira PRODUÇÃO! ⚙️",
            "A palavra do dia é: PRODUÇÃO! 🗣️",
            "Já gritou PRODUÇÃO hoje, Marcello? 📣",
            "Vamos botar essa PRODUÇÃO pra girar, Marcello! 🔥",
            "Grita bem alto pra acordar o setor: PRODUUUUÇÃO! 🗣️🏭",
            "Fala Marcello! O relógio bateu e é hora da PRODUÇÃO! ⏳",
            "Chegou a força motriz do estoque! Foco total! ⚙️",
            "O general da PRODUÇÃO tá no comando! Bora! 🚀",
            "Marcello, o sistema até tremeu quando você digitou a senha! 😂"
        ],
        "elogio": [
            "PRODUÇÃO a milhão, hein Marcello! Não deixa a peteca cair! 🏭🚀",
            "Isso sim que é PRODUÇÃO de verdade! Amassou! 👊",
            "Gritou PRODUÇÃO e entregou tudo! Monstro! 🏆",
            "O cara é a própria máquina de PRODUÇÃO! 🤖",
            "Meta alcançada em nome da PRODUÇÃO! Parabéns! 🎉",
            "A empresa inteira ouviu esse envio: PRODUUUÇÃO! 📣🔥",
            "O Marcello não brinca em serviço! Só entrega pesada! 📦🏆",
            "Mais um lote que sai com a marca da PRODUÇÃO a milhão! 🏭💨",
            "Impecável! Você é a definição da palavra PRODUÇÃO! ⭐",
            "Tá de parabéns! Se todo mundo focasse assim, a gente dobrava a fábrica! 👏"
        ]
    },
    "Renan": {
        "saudacao": [
            "Cuidado pra não prender esse cabelão nas caixas do estoque, hein! 💇‍♂️😂",
            "E aí cabeludo! Bora botar pra quebrar hoje? 🎸",
            "Gastou meio pote de shampoo hoje nesse cabelão, Renan? 🧴",
            "O cabelão tá solto pra voar no estoque hoje? 🦅",
            "Chegou o aprendiz cabeludo! Bora focar nas metas! 🚀",
            "Fala Renan! O cabelão já tá amarrado pra não enroscar em nada? 💇‍♂️",
            "E aí rockstar do estoque! Bora pro palco (fábrica)! 🎸🎤",
            "Salve Aprendiz! O cabelo longo te dá superpoderes hoje? 🦸‍♂️",
            "Chegou o Sansão do estoque! Prepara pra produzir! 🦁",
            "O vento bate no cabelão e ele acelera! Bora Renan! 🌪️"
        ],
        "elogio": [
            "Mandou bem demais! Até jogou o cabelão pro lado pra comemorar! 🎸🔥",
            "Aprendiz nota mil! Tá ganhando moral, Renan! 🏆",
            "Voando baixo! O vento até bagunçou o cabelão! 💨",
            "Estoque dominado pelo cabeludo! Brabo! 🤘",
            "Ligeiro demais! Continua assim, Renan! 🚀",
            "É muito talento pra um aprendiz só! E muito cabelo também! 😂🔥",
            "Esse envio merecia até um solo de guitarra! 🎸⚡",
            "Tá dominando as caixas como ninguém! Futuro promissor! 🌟",
            "Voou igual comercial de shampoo! Parabéns Renan! 🧴🚀",
            "O cabeludo não tá pra brincadeira! Excelente trabalho! 🏆"
        ]
    }
}

produtos_torres_texto = """
TR03 = 5
TR03W = 7
TR03A = 5
TR03AW = 7
TR02A = 5
TR02AW = 6
TR03AW  COM DUO = 10
TR03A  COM DUO = 10
TR03A TOPO EM PEDRA  2,5 mm = 7
TR03A TOPO EM PEDRA  4 mm = 7
TR03A TOPO EM PEDRA  2,5 mm TOM DEDICADA = 10
TR03 2TM + 1VER = 7
TR03  4mm = 7
TR03A  2 TOM +VM = 8
TR02AW  1TOM + VM = 6
TR03AW  2 TOM + VM = 8
TR02A  4mm² = 5
 TR02AW  4mm = 6 
"""

produtos_caixas_texto = """

CXP01T = 1
CXP01 = 1
CX04S = 1
CX56 = 1
CX34ABS = 1
CX44 = 1
CX23ABS = 1
CX01S = 1
CX02S = 1
CX03S = 1
CXEP02 = 1
CXEP03 = 1
"""

atividades_apoio_texto = """
Embalar Mercadoria
Colocar Etiquetas
Fazer Pedido em Outro Setor
Organização/Limpeza
Suporte Geral Operacional
"""

atividades_aprendiz_texto = """
⚠️ FAZER ESTOQUE (Contar Peças)
Contagem de Estoque
Abrir Material para Separadores
Ajudar nos Pedidos
Embalar Pedidos
Organização/Limpeza do Setor
"""

materiais_abertura_texto = """
Tomada
CAT6
CAT5
Espelho RJ45
Indução Automática
Indução Semiautomática
"""

dicionario_torres = {}
for linha in produtos_torres_texto.strip().split('\n'):
    if '=' in linha:
        nome_prod, tempo = linha.split('=')
        dicionario_torres[nome_prod.strip()] = float(tempo.strip())
    elif linha.strip():
        dicionario_torres[linha.strip()] = 0.0

dicionario_caixas = {}
for linha in produtos_caixas_texto.strip().split('\n'):
    if '=' in linha:
        nome_prod, tempo = linha.split('=')
        dicionario_caixas[nome_prod.strip()] = float(tempo.strip())
    elif linha.strip():
        dicionario_caixas[linha.strip()] = 0.0

dicionario_produtos = {**dicionario_torres, **dicionario_caixas}

lista_separadores = ["Selecione..."] + [s.strip() for s in separadores_texto.strip().split('\n') if s.strip()]
lista_aprendizes = ["Selecione..."] + [a.strip() for a in aprendizes_texto.strip().split('\n') if a.strip()]
lista_apoio = [a.strip() for a in atividades_apoio_texto.strip().split('\n') if a.strip()]
lista_tarefas_aprendiz = [t.strip() for t in atividades_aprendiz_texto.strip().split('\n') if t.strip()]
lista_materiais_abrir = ["Selecione..."] + [m.strip() for m in materiais_abertura_texto.strip().split('\n') if m.strip()]

# =====================================================================
# FIM DA ÁREA DE EDIÇÃO
# =====================================================================

st.set_page_config(page_title="Controle de Estoque", page_icon="📦", layout="centered")

esconder_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(esconder_menu, unsafe_allow_html=True)

st.title("📦 Sistema de Estoque Móvel")
st.image("https://caixatomada.com/wp-content/uploads/2020/03/b_03-1.png", width=200)

aba_separador, aba_aprendiz, aba_coordenador, aba_gestor = st.tabs(["📲 Separador", "👦 Aprendiz", "📋 Coordenador", "📊 Gestor"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    data_hoje_str = datetime.now().strftime("%d/%m/%Y")
    df_podio = pd.read_sql_query("SELECT separador, quantidade, produto FROM estoque WHERE status = 'Aprovado' AND data = ?", conn, params=(data_hoje_str,))
    
    if not df_podio.empty:
        df_podio_est = df_podio[
            ~df_podio['produto'].str.startswith("APOIO:") & 
            ~df_podio['produto'].str.startswith("APRENDIZ") & 
            ~df_podio['produto'].str.startswith("ADIANTAMENTO:") &
            ~df_podio['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])
        ]
        if not df_podio_est.empty:
            ranking_top3 = df_podio_est.groupby('separador')['quantidade'].sum().reset_index().sort_values('quantidade', ascending=False).head(3)
            if len(ranking_top3) > 0:
                st.markdown("### 🏆 Pódio do Dia (Estoque)")
                cols = st.columns(3)
                medalhas = ["🥇", "🥈", "🥉"]
                for i, (idx, row_podio) in enumerate(ranking_top3.iterrows()):
                    with cols[i]:
                        st.info(f"{medalhas[i]} **{row_podio['separador']}**\n\n📦 {row_podio['quantidade']} un")
                st.markdown("---")

    st.header("Seu Painel de Lançamento")
    nome = st.selectbox("Quem é você?", lista_separadores, key="sel_sep_main")
    
    senha_digitada = ""
    if nome != "Selecione...":
        senha_digitada = st.text_input("Digite seu PIN de acesso:", type="password", key="pwd_sep_main")

    if nome != "Selecione..." and senha_digitada == senhas_separadores.get(nome, ""):
        opcoes_saudacao = mensagens_personalizadas.get(nome, {}).get("saudacao", ["Bora produzir? 🚀"])
        msg_saudacao = random.choice(opcoes_saudacao)
        st.success(f"🔓 {obter_bom_dia()}, {nome}! {msg_saudacao}")
        
        setor_do_funcionario = setor_separadores.get(nome, "Todos")
        
        lista_opcoes_dinamica = ["Selecione...", "⚠️ ATIVIDADE DE APOIO (Outro Setor)", "📦 ADIANTAR PEDIDOS (Dia Seguinte)", "Contagem de Estoque"]
        
        if setor_do_funcionario == "Torres":
            lista_opcoes_dinamica += ["Cortar Cabos", "Testar Torres", "Caixas Plug"] + list(dicionario_torres.keys())
        elif setor_do_funcionario == "Caixas":
            lista_opcoes_dinamica += list(dicionario_caixas.keys())
        else:
            lista_opcoes_dinamica += ["Cortar Cabos", "Testar Torres", "Caixas Plug"] + list(dicionario_produtos.keys())
            
        produto_selecionado = st.selectbox("O que você fez agora?", lista_opcoes_dinamica, key="sel_prod_main")
        
        if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
            tipo_apoio = st.selectbox("Qual apoio você deu pra equipe?", lista_apoio)
            quantidade = 0
            st.info("💡 Foca em lançar o horário certinho que você passou ajudando!")
            
        elif produto_selecionado == "📦 ADIANTAR PEDIDOS (Dia Seguinte)":
            quantidade = st.number_input("Quantos pedidos você adiantou?", min_value=1, step=1, key="num_qtd_adiant")
            st.info("💡 Sensacional! Registra o horário certinho que você passou adiantando esses pedidos.")
            
        elif produto_selecionado in ["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"]:
            quantidade = 0
            st.info(f"💡 Você selecionou a atividade administrativa: **{produto_selecionado}**. Foque em colocar o horário de início e fim corretos.")
            
        else:
            quantidade = st.number_input("Quantidade (Unidades):", min_value=1, step=1, key="num_qtd_main")
            if produto_selecionado != "Selecione..." and produto_selecionado in dicionario_produtos:
                tempo_unidade = dicionario_produtos[produto_selecionado]
                if tempo_unidade > 0:
                    tempo_meta = tempo_unidade * quantidade
                    st.caption(f"🎯 O tempo padrão pra isso seria aprox. **{tempo_meta} minutos**.")
        
        col1, col2 = st.columns(2)
        with col1: hora_inicio = st.text_input("Hora que começou:", placeholder="Ex: 1430", key="txt_ini_main")
        with col2: hora_fim = st.text_input("Hora que terminou:", placeholder="Ex: 1500", key="txt_fim_main")
            
        if st.button("🚀 Enviar pro Coordenador", use_container_width=True, key="btn_env_main"):
            if produto_selecionado == "Selecione..." or not hora_inicio or not hora_fim:
                st.error("❌ Opa! Preenche tudo aí antes de enviar.")
            else:
                inicio_corrigido = auto_corrigir_hora(hora_inicio)
                fim_corrigido = auto_corrigir_hora(hora_fim)
                if not inicio_corrigido or not fim_corrigido:
                    st.error("❌ Vish, não entendi os números do horário. Tenta de novo.")
                else:
                    if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
                        produto_salvar = f"APOIO: {tipo_apoio}"
                    elif produto_selecionado == "📦 ADIANTAR PEDIDOS (Dia Seguinte)":
                        produto_salvar = "ADIANTAMENTO: Pedidos"
                    else:
                        produto_salvar = produto_selecionado
                        
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                   (nome, produto_salvar, quantidade, inicio_corrigido, fim_corrigido, data_hoje_str, 'Pendente'))
                    conn.commit()
                    
                    st.toast('Enviado com sucesso! 🚀', icon='✅')
                    st.balloons()
                    opcoes_elogio = mensagens_personalizadas.get(nome, {}).get("elogio", ["Atividade enviada com sucesso!"])
                    msg_elogio = random.choice(opcoes_elogio)
                    st.success(f"🎉 **{msg_elogio}** (Aguardando OK do coordenador)")

        st.markdown("---")
        st.subheader("🔍 Conferir meu histórico de hoje")
        data_consulta = st.date_input("Escolha o dia:", value=date.today(), key="date_consult_sep", format="DD/MM/YYYY")
        data_cons_str = data_consulta.strftime("%d/%m/%Y")
        
        df_historico_sep = pd.read_sql_query("SELECT produto, quantidade, status FROM estoque WHERE separador = ? AND data = ?", conn, params=(nome, data_cons_str))
        if df_historico_sep.empty:
            st.info("Nada registrado ainda.")
        else:
            df_historico_sep['produto'] = df_historico_sep['produto'].str.replace("APOIO: ", "Apoio: ").str.replace("ADIANTAMENTO: ", "Adiantou: ")
            st.dataframe(df_historico_sep, hide_index=True, use_container_width=True)
            
    elif senha_digitada != "":
        st.error("❌ Senha errada, parça! Digita o PIN correto aí.")

# ----------------- ABA 1.5: MENOR APRENDIZ -----------------
with aba_aprendiz:
    st.header("📲 Área do Aprendiz")
    nome_apr = st.selectbox("Quem é você?", lista_aprendizes, key="sel_apr")
    
    senha_digitada_apr = ""
    if nome_apr != "Selecione...":
        senha_digitada_apr = st.text_input("Digite seu PIN de acesso:", type="password", key="pwd_apr")
        
    if nome_apr != "Selecione..." and senha_digitada_apr == senhas_separadores.get(nome_apr, ""):
        opcoes_saudacao_apr = mensagens_personalizadas.get(nome_apr, {}).get("saudacao", ["Vamos ao trabalho? 🚀"])
        msg_saudacao_apr = random.choice(opcoes_saudacao_apr)
        st.success(f"🔓 {obter_bom_dia()}, {nome_apr}! {msg_saudacao_apr}")
        
        tarefa_apr = st.selectbox("O que você fez agora?", lista_tarefas_aprendiz, key="sel_tarefa_apr")
        
        prod_apr = "Selecione..."
        qtd_apr = 0
        
        if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)":
            setor_do_aprendiz = setor_separadores.get(nome_apr, "Todos")
            if setor_do_aprendiz == "Torres":
                lista_prod_aprendiz = list(dicionario_torres.keys())
            elif setor_do_aprendiz == "Caixas":
                lista_prod_aprendiz = list(dicionario_caixas.keys())
            else:
                lista_prod_aprendiz = list(dicionario_produtos.keys())
                
            prod_apr = st.selectbox("Qual modelo?", ["Selecione..."] + lista_prod_aprendiz, key="prod_apr_est")
            qtd_apr = st.number_input("Quantidade:", min_value=1, step=1, key="qtd_apr_est")
            
        elif tarefa_apr == "Abrir Material para Separadores":
            prod_apr = st.selectbox("Que material você abriu?", lista_materiais_abrir, key="mat_apr_abrir")
            qtd_apr = st.number_input("Quantidade (un/caixas):", min_value=1, step=1, key="qtd_apr_abrir")
            
        elif tarefa_apr == "Contagem de Estoque":
            prod_apr = "Contagem de Estoque"
            qtd_apr = 0
            st.info("💡 Você marcou Contagem de Estoque. Registre a hora de início e fim normalmente.")
        else:
            prod_apr = tarefa_apr
            
        col_apr1, col_apr2 = st.columns(2)
        with col_apr1: hora_ini_apr = st.text_input("Hora que começou:", placeholder="Ex: 0800", key="ini_apr")
        with col_apr2: hora_fim_apr = st.text_input("Hora que terminou:", placeholder="Ex: 1200", key="fim_apr")
        
        if st.button("🚀 Enviar pro Coordenador", use_container_width=True, key="btn_apr"):
            if (tarefa_apr in ["⚠️ FAZER ESTOQUE (Contar Peças)", "Abrir Material para Separadores"] and prod_apr == "Selecione...") or not hora_ini_apr or not hora_fim_apr:
                st.error("❌ Preenche tudo aí antes de enviar!")
            else:
                ini_corr_apr = auto_corrigir_hora(hora_ini_apr)
                fim_corr_apr = auto_corrigir_hora(hora_fim_apr)
                if not ini_corr_apr or not fim_corr_apr:
                    st.error("❌ Horário inválido.")
                else:
                    if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)":
                        produto_salvar_apr = f"APRENDIZ ESTOQUE: {prod_apr}"
                    elif tarefa_apr == "Abrir Material para Separadores":
                        produto_salvar_apr = f"APRENDIZ ABRIR: {prod_apr}"
                    elif tarefa_apr == "Contagem de Estoque":
                        produto_salvar_apr = "APRENDIZ: Contagem de Estoque"
                    else:
                        produto_salvar_apr = f"APRENDIZ: {prod_apr}"
                        
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                   (nome_apr, produto_salvar_apr, qtd_apr, ini_corr_apr, fim_corr_apr, data_hoje_str, 'Pendente'))
                    conn.commit()
                    
                    st.toast('Atividade salva! 🚀', icon='✅')
                    st.balloons()
                    opcoes_elogio_apr = mensagens_personalizadas.get(nome_apr, {}).get("elogio", ["Valeu pela força!"])
                    msg_elogio_apr = random.choice(opcoes_elogio_apr)
                    st.success(f"🎉 **{msg_elogio_apr}** Registro enviado pro chefe.")
                    
    elif senha_digitada_apr != "":
        st.error("❌ Senha incorreta!")

# ----------------- ABA 2: COORDENADOR -----------------
with aba_coordenador:
    st.header("Área do Coordenador")
    senha_coord = st.text_input("Senha do Coordenador:", type="password", key="senha_coord")
    
    if senha_coord == "1234":
        
        # MENSAGEM EXCLUSIVA PARA O COORDENADOR LÍDER
        mensagens_coordenador = [
            "Fala, Líder! Bora colocar ordem na casa? 📋👊",
            "Acesso liberado, Coordenador! A equipe tá voando hoje! 🚀",
            "Chegou quem dita o ritmo! Vamos aprovar essa produção! 🏆",
            "Olho no lance, Líder! Bora conferir os números de hoje! 🧐📦",
            "Bem-vindo, Coordenador! O maestro da operação tá na área! 🎼⚡",
            "A tropa produziu, agora é com o Líder! Manda bala nas aprovações! ✅",
            "Fala, Líder! Puxando a frente da operação com maestria! 🦅",
            "O cara que faz a engrenagem girar chegou! Bom trabalho! ⚙️",
            "Coordenador on-line! Vamos deixar esse estoque nos trinques! ✨",
            "Acesso VIP para o Líder da operação! Bora pra cima! 🔥"
        ]
        st.success(f"🔓 {obter_bom_dia()}! {random.choice(mensagens_coordenador)}")

        st.subheader("📋 Fila de Aprovação")
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty:
            st.info("Nada pendente. A equipe tá de boa! ✌️")
        else:
            for index, row in df_pendentes.iterrows():
                if row['produto'].startswith("APRENDIZ ESTOQUE:"):
                    tipo_card = "👦 ESTOQUE APRENDIZ"
                    txt_prod = f"{row['produto'].replace('APRENDIZ ESTOQUE: ', '')} ({row['quantidade']} un)"
                elif row['produto'].startswith("APRENDIZ ABRIR:"):
                    tipo_card = "📦 ABRIR MATERIAL"
                    txt_prod = f"{row['produto'].replace('APRENDIZ ABRIR: ', '')} ({row['quantidade']} pçs)"
                elif row['produto'].startswith("APRENDIZ:"):
                    tipo_card = "👦 TAREFA APRENDIZ"
                    txt_prod = row['produto'].replace("APRENDIZ: ", "")
                elif row['produto'].startswith("APOIO:"):
                    tipo_card = "🛠️ APOIO SEPARADOR"
                    txt_prod = row['produto'].replace("APOIO: ", "")
                elif row['produto'] == "ADIANTAMENTO: Pedidos":
                    tipo_card = "🚀 ADIANTAR PEDIDOS"
                    txt_prod = f"{row['quantidade']} pedidos adiantados"
                elif row['produto'] in ["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"]:
                    tipo_card = "⚙️ ATIV. ADMINISTRATIVA"
                    txt_prod = row['produto']
                else:
                    tipo_card = "🔔 ESTOQUE SEPARADOR"
                    txt_prod = f"{row['produto']} ({row['quantidade']} un)"
                
                with st.expander(f"{tipo_card} | {row['separador']} - {txt_prod}"):
                    st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']} | **Data:** {row['data']}")
                    col_ok, col_rej = st.columns(2)
                    with col_ok:
                        st.write("") 
                        if st.button(f"✓ Dar OK", key=f"coord_ok_{row['id']}", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                    with col_rej:
                        confirmar_rej = st.checkbox("Confirmar ❌", key=f"chk_rej_{row['id']}")
                        if st.button(f"Rejeitar", key=f"coord_rej_{row['id']}", use_container_width=True, disabled=not confirmar_rej):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM estoque WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()

        st.markdown("---")
        st.subheader("📅 Desempenho e Rankings")
        col_c1, col_c2 = st.columns(2)
        with col_c1: data_inicio_coord = st.date_input("Data de Início:", value=date.today(), key="d_ini_coord", format="DD/MM/YYYY")
        with col_c2: data_fim_coord = st.date_input("Data Final:", value=date.today(), key="d_fim_coord", format="DD/MM/YYYY")
        
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        if not df_todos_aprovados.empty:
            df_todos_aprovados['data_calc'] = pd.to_datetime(df_todos_aprovados['data'], format='%d/%m/%Y').dt.date
            df_periodo_coord = df_todos_aprovados[(df_todos_aprovados['data_calc'] >= data_inicio_coord) & (df_todos_aprovados['data_calc'] <= data_fim_coord)].copy()
            
            if not df_periodo_coord.empty:
                df_periodo_coord['Minutos Gastos Reais'] = df_periodo_coord.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                
                df_prod_coord = df_periodo_coord[
                    ~df_periodo_coord['produto'].str.startswith("APOIO:") & 
                    ~df_periodo_coord['produto'].str.startswith("APRENDIZ") & 
                    ~df_periodo_coord['produto'].str.startswith("ADIANTAMENTO:") &
                    ~df_periodo_coord['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])
                ].copy()
                df_adiant_coord = df_periodo_coord[df_periodo_coord['produto'] == "ADIANTAMENTO: Pedidos"].copy()
                
                if not df_prod_coord.empty:
                    st.markdown("#### 🏆 Produtividade no Estoque")
                    df_prod_coord['Tempo Padrão Unidade'] = df_prod_coord['produto'].map(dicionario_produtos).fillna(0)
                    df_prod_coord['Meta de Tempo Total'] = df_prod_coord['Tempo Padrão Unidade'] * df_prod_coord['quantidade']
                    rk_est_c = df_prod_coord.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_est_c['Eficiência'] = (rk_est_c['Meta_Tempo'] / rk_est_c['Tempo_Gasto']) * 100
                    rk_est_c['Eficiência'] = rk_est_c['Eficiência'].fillna(0).map(lambda x: f"{x:.1f}%")
                    rk_est_c['Tempo_Gasto'] = rk_est_c['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_est_c[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência']], hide_index=True, use_container_width=True)
                
                if not df_adiant_coord.empty:
                    st.markdown("#### 🚀 Pedidos Adiantados")
                    rk_adiant_c = df_adiant_coord.groupby('separador').agg(Total_Pedidos=('quantidade', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_adiant_c['Tempo_Gasto'] = rk_adiant_c['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_adiant_c[['separador', 'Total_Pedidos', 'Tempo_Gasto']], hide_index=True, use_container_width=True)

            else:
                st.warning("Nada aprovado nessas datas.")

# ----------------- ABA 3: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Gestão")
    senha_gestor = st.text_input("Senha do Gestor Geral:", type="password", key="senha_gestor")
    
    if senha_gestor == "9999":
        st.subheader("📆 Fechamento por Período")
        col_d1, col_d2 = st.columns(2)
        with col_d1: data_inicio = st.date_input("Data de Início:", value=date.today(), key="ini_gestor", format="DD/MM/YYYY")
        with col_d2: data_fim = st.date_input("Data Final:", value=date.today(), key="fim_gestor", format="DD/MM/YYYY")
            
        df_geral = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_geral.empty:
            df_geral['data_calc'] = pd.to_datetime(df_geral['data'], format='%d/%m/%Y').dt.date
            df_filtrado = df_geral[(df_geral['data_calc'] >= data_inicio) & (df_geral['data_calc'] <= data_fim)].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Minutos Gastos Reais'] = df_filtrado.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                
                df_producao = df_filtrado[
                    ~df_filtrado['produto'].str.startswith("APOIO:") & 
                    ~df_filtrado['produto'].str.startswith("APRENDIZ") & 
                    ~df_filtrado['produto'].str.startswith("ADIANTAMENTO:") &
                    ~df_filtrado['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])
                ].copy()
                df_apoio = df_filtrado[df_filtrado['produto'].str.startswith("APOIO:")].copy()
                df_aprendiz_dados = df_filtrado[df_filtrado['produto'].str.startswith("APRENDIZ")].copy()
                df_adiantamento = df_filtrado[df_filtrado['produto'] == "ADIANTAMENTO: Pedidos"].copy()
                df_admin_seps = df_filtrado[df_filtrado['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])].copy()
                
                st.markdown("---")
                st.write(f"### 📈 Resumo Geral do Período")
                st.write(f"**Produtos Feitos:** {df_producao['quantidade'].sum()} un | **Pedidos Adiantados:** {df_adiantamento['quantidade'].sum()} pedidos")
                
                csv_dados = df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(label="📥 Baixar Relatório (Para Excel)", data=csv_dados, file_name="relatorio_estoque.csv", mime="text/csv", type="primary")
                
                st.subheader("🏆 1. Ranking de Produtividade (Separadores)")
                if not df_producao.empty:
                    df_producao['Tempo Padrão Unidade'] = df_producao['produto'].map(dicionario_produtos).fillna(0)
                    df_producao['Meta de Tempo Total'] = df_producao['Tempo Padrão Unidade'] * df_producao['quantidade']
                    ranking_est = df_producao.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_est['Eficiência Média'] = (ranking_est['Meta_Tempo'] / ranking_est['Tempo_Gasto']) * 100
                    ranking_est['Eficiência Média'] = ranking_est['Eficiência Média'].fillna(0).map(lambda x: f"{x:.1f}%")
                    ranking_est['Tempo_Gasto'] = ranking_est['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_est[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência Média']], hide_index=True, use_container_width=True)
                
                st.subheader("🛠️ 2. Relatório de Horas de Apoio (Separadores)")
                if not df_apoio.empty:
                    ranking_ap = df_apoio.groupby('separador').agg(Minutos_Apoio=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_ap['Tempo Total de Apoio'] = ranking_ap['Minutos_Apoio'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_ap[['separador', 'Tempo Total de Apoio']], hide_index=True, use_container_width=True)
                
                st.subheader("👦 3. Relatório do Menor Aprendiz")
                if not df_aprendiz_dados.empty:
                    df_aprendiz_dados['Atividade Mapeada'] = df_aprendiz_dados['produto'].str.replace("APRENDIZ ESTOQUE: ", "Estoque: ").str.replace("APRENDIZ ABRIR: ", "Abriu Material: ").str.replace("APRENDIZ: ", "")
                    rk_apr = df_aprendiz_dados.groupby(['separador', 'Atividade Mapeada']).agg(Tempo_Gasto=('Minutos Gastos Reais', 'sum'), Pecas_Feitas=('quantidade', 'sum')).reset_index()
                    rk_apr['Tempo Formato'] = rk_apr['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    rk_apr['Resultado Final'] = rk_apr.apply(lambda r: f"{r['Tempo Formato']} (Fez/Abriu {int(r['Pecas_Feitas'])} un)" if r['Pecas_Feitas'] > 0 else r['Tempo Formato'], axis=1)
                    
                    rk_apr = rk_apr.rename(columns={'separador': 'Aprendiz', 'Atividade Mapeada': 'Atividade'})
                    st.dataframe(rk_apr[['Aprendiz', 'Atividade', 'Resultado Final']], hide_index=True, use_container_width=True)
                else:
                    st.info("Nenhuma atividade de menor aprendiz registrada no período.")
                
                st.subheader("🚀 4. Relatório de Pedidos Adiantados")
                if not df_adiantamento.empty:
                    rk_adiant = df_adiantamento.groupby('separador').agg(Total_Pedidos=('quantidade', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_adiant['Tempo_Gasto'] = rk_adiant['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    rk_adiant.columns = ['Funcionário', 'Total de Pedidos', 'Tempo Dedicado']
                    st.dataframe(rk_adiant, hide_index=True, use_container_width=True)
                
                st.subheader("⚙️ 5. Relatório de Atividades Administrativas e de Setor")
                if not df_admin_seps.empty:
                    rk_admin = df_admin_seps.groupby(['separador', 'produto']).agg(Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_admin['Tempo Formato'] = rk_admin['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    rk_admin.columns = ['Funcionário', 'Atividade', 'Minutos', 'Tempo Dedicado']
                    st.dataframe(rk_admin[['Funcionário', 'Atividade', 'Tempo Dedicado']], hide_index=True, use_container_width=True)
                    
            else: st.warning("Não há dados aprovados neste intervalo de datas.")
            
        st.markdown("---")
        st.subheader("⚠️ Zona de Risco")
        with st.expander("Clique aqui para opções de EXCLUSÃO"):
            lista_todos_nomes = lista_separadores[1:] + lista_aprendizes[1:]
            separador_para_deletar = st.selectbox("Limpar histórico de alguém?", ["Selecione..."] + lista_todos_nomes, key="del_sep")
            confirmacao_individual = st.checkbox(f"Confirmo que desejo apagar permanentemente.", key="chk_ind")
            if st.button("🗑️ APAGAR HISTÓRICO", type="primary", disabled=not confirmacao_individual or separador_para_deletar == "Selecione..."):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE separador = ?", (separador_para_deletar,))
                conn.commit()
                st.success(f"💥 Limpo com sucesso!")
                st.rerun()
                
            st.markdown("---")
            confirmacao_total = st.checkbox("Entendo que isso ZERA o sistema.", key="chk_tot")
            if st.button("🔥 ZERAR TUDO", type="primary", disabled=not confirmacao_total):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque")
                conn.commit()
                st.success("💥 Banco zerado!")
                st.rerun()

    elif senha_gestor != "": st.error("Senha de gestor incorreta.")
