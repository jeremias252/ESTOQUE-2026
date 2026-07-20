import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
import base64
import os
from datetime import datetime, date

# CONFIGURAÇÕES FIXAS DO SEU REPOSITÓRIO
GITHUB_USER = "jeremias252"
GITHUB_REPO = "ESTOQUE-2026"
BACKUP_FILE_NAME = "backup_estoque.db"

# 1. FUNÇÃO MÁGICA: RESTAURAR E GERENCIAR BACKUP NO GITHUB
def gerenciar_backup_inicial():
    if "GITHUB_TOKEN" not in st.secrets:
        return
        
    token = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{BACKUP_FILE_NAME}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    if not os.path.exists("controle_estoque.db"):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                conteudo_base64 = response.json()["content"]
                conteudo_bytes = base64.b64decode(conteudo_base64)
                with open("controle_estoque.db", "wb") as f:
                    f.write(conteudo_bytes)
                st.cache_resource.clear()
            except:
                pass

def salvar_backup_no_github():
    if "GITHUB_TOKEN" not in st.secrets:
        st.error("❌ Erro: GITHUB_TOKEN não configurado no painel Secrets do Streamlit!")
        return False
        
    token = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{BACKUP_FILE_NAME}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    if not os.path.exists("controle_estoque.db"):
        st.error("❌ Nenhum banco de dados local encontrado para fazer backup.")
        return False
        
    with open("controle_estoque.db", "rb") as f:
        conteudo_bytes = f.read()
    conteudo_base64 = base64.b64encode(conteudo_bytes).decode("utf-8")
    
    sha = None
    res_get = requests.get(url, headers=headers)
    if res_get.status_code == 200:
        sha = res_get.json()["sha"]
        
    dados = {
        "message": f"Backup automatico do estoque: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "content": conteudo_base64
    }
    if sha:
        dados["sha"] = sha
        
    res_put = requests.put(url, headers=headers, json=dados)
    if res_put.status_code in [200, 201]:
        return True
    else:
        return False

gerenciar_backup_inicial()

# 2. CONFIGURAÇÃO DO BANCO DE DADOS LOCAL OTIMIZADO
@st.cache_resource
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

# 3. FUNÇÕES AUXILIARES
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
# ÁREA DE CONFIGURAÇÃO: PRODUTOS
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
CP01A = 1
RE04FN = 1
RE06FN = 1
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
# INTERFACE DO USUÁRIO (STREAMLIT)
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
            ~df_podio['produto'].str.startswith("PEGO DO ESTOQUE:") &
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
        st.success(f"🔓 {obter_bom_dia()}, {nome}! Acesso liberado.")
        setor_do_funcionario = setor_separadores.get(nome, "Todos")
        
        # NOVA OPÇÃO ADICIONADA AQUI: "🛒 PEGAR DO ESTOQUE (Reposição)"
        lista_opcoes_dinamica = ["Selecione...", "🛒 PEGAR DO ESTOQUE (Reposição)", "⚠️ ATIVIDADE DE APOIO (Outro Setor)", "📦 ADIANTAR PEDIDOS (Dia Seguinte)", "Contagem de Estoque"]
        
        if setor_do_funcionario == "Torres":
            lista_opcoes_dinamica += ["Cortar Cabos", "Testar Torres", "Caixas Plug"] + list(dicionario_torres.keys())
        elif setor_do_funcionario == "Caixas":
            lista_opcoes_dinamica += list(dicionario_caixas.keys())
        else:
            lista_opcoes_dinamica += ["Cortar Cabos", "Testar Torres", "Caixas Plug"] + list(dicionario_produtos.keys())
            
        produto_selecionado = st.selectbox("O que você fez agora?", lista_opcoes_dinamica, key="sel_prod_main")
        
        # Variáveis padrão
        modelo_pego = "Selecione..."
        hora_inicio = ""
        hora_fim = ""
        quantidade = 0
        
        # LÓGICA DE EXIBIÇÃO BASEADA NA OPÇÃO
        if produto_selecionado == "🛒 PEGAR DO ESTOQUE (Reposição)":
            modelo_pego = st.selectbox("Qual modelo você pegou?", ["Selecione..."] + list(dicionario_produtos.keys()))
            quantidade = st.number_input("Quantidade (Unidades):", min_value=1, step=1, key="num_qtd_estoque")
            st.info("💡 Apenas registre a quantidade. Não é necessário preencher horários para esta ação.")
            hora_inicio = "0000"
            hora_fim = "0000"
            
        elif produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
            tipo_apoio = st.selectbox("Qual apoio você deu pra equipe?", lista_apoio)
            quantidade = 0
            st.info("💡 Foque em lançar o horário certinho que você passou ajudando!")
            col1, col2 = st.columns(2)
            with col1: hora_inicio = st.text_input("Hora que começou:", placeholder="Ex: 1430")
            with col2: hora_fim = st.text_input("Hora que terminou:", placeholder="Ex: 1500")
            
        elif produto_selecionado == "📦 ADIANTAR PEDIDOS (Dia Seguinte)":
            quantidade = st.number_input("Quantos pedidos você adiantou?", min_value=1, step=1)
            st.info("💡 Registre o horário certinho que você passou adiantando esses pedidos.")
            col1, col2 = st.columns(2)
            with col1: hora_inicio = st.text_input("Hora que começou:", placeholder="Ex: 1430")
            with col2: hora_fim = st.text_input("Hora que terminou:", placeholder="Ex: 1500")
            
        elif produto_selecionado in ["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"]:
            quantidade = 0
            st.info(f"💡 Você selecionou uma atividade administrativa. Foque nos horários de início e fim.")
            col1, col2 = st.columns(2)
            with col1: hora_inicio = st.text_input("Hora que começou:", placeholder="Ex: 1430")
            with col2: hora_fim = st.text_input("Hora que terminou:", placeholder="Ex: 1500")
            
        elif produto_selecionado != "Selecione...":
            quantidade = st.number_input("Quantidade (Unidades):", min_value=1, step=1)
            if produto_selecionado in dicionario_produtos:
                tempo_unidade = dicionario_produtos[produto_selecionado]
                if tempo_unidade > 0:
                    st.caption(f"🎯 O tempo padrão pra isso seria aprox. **{tempo_unidade * quantidade} minutos**.")
            col1, col2 = st.columns(2)
            with col1: hora_inicio = st.text_input("Hora que começou:", placeholder="Ex: 1430")
            with col2: hora_fim = st.text_input("Hora que terminou:", placeholder="Ex: 1500")
            
        if st.button("🚀 Enviar pro Coordenador", use_container_width=True, key="btn_env_main"):
            if produto_selecionado == "Selecione...":
                st.error("❌ Selecione uma atividade antes de enviar.")
            elif produto_selecionado == "🛒 PEGAR DO ESTOQUE (Reposição)" and modelo_pego == "Selecione...":
                st.error("❌ Selecione o modelo que você pegou do estoque.")
            elif not hora_inicio or not hora_fim:
                st.error("❌ Preencha os horários antes de enviar.")
            else:
                inicio_corrigido = auto_corrigir_hora(hora_inicio)
                fim_corrigido = auto_corrigir_hora(hora_fim)
                if not inicio_corrigido or not fim_corrigido:
                    st.error("❌ Horário inválido.")
                else:
                    if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
                        produto_salvar = f"APOIO: {tipo_apoio}"
                    elif produto_selecionado == "📦 ADIANTAR PEDIDOS (Dia Seguinte)":
                        produto_salvar = "ADIANTAMENTO: Pedidos"
                    elif produto_selecionado == "🛒 PEGAR DO ESTOQUE (Reposição)":
                        produto_salvar = f"PEGO DO ESTOQUE: {modelo_pego}"
                    else:
                        produto_salvar = produto_selecionado
                        
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                   (nome, produto_salvar, quantidade, inicio_corrigido, fim_corrigido, data_hoje_str, 'Pendente'))
                    conn.commit()
                    
                    st.toast('Enviado com sucesso! 🚀', icon='✅')
                    st.success("🎉 Atividade enviada com sucesso! (Aguardando OK do coordenador)")

        st.markdown("---")
        st.subheader("🔍 Conferir meu histórico de hoje")
        data_consulta = st.date_input("Escolha o dia:", value=date.today(), key="date_consult_sep", format="DD/MM/YYYY")
        data_cons_str = data_consulta.strftime("%d/%m/%Y")
        
        df_historico_sep = pd.read_sql_query("SELECT produto AS Atividade, quantidade AS Qtd, hora_inicio AS Início, hora_fim AS Fim, status AS Status FROM estoque WHERE separador = ? AND data = ?", conn, params=(nome, data_cons_str))
        if df_historico_sep.empty: st.info("Nada registrado ainda.")
        else:
            df_historico_sep['Atividade'] = df_historico_sep['Atividade'].str.replace("APOIO: ", "Apoio: ").str.replace("ADIANTAMENTO: ", "Adiantou: ")
            st.dataframe(df_historico_sep, hide_index=True, use_container_width=True)
            
    elif senha_digitada != "": st.error("❌ Senha errada!")

# ----------------- ABA 1.5: MENOR APRENDIZ -----------------
with aba_aprendiz:
    st.header("📲 Área do Aprendiz")
    nome_apr = st.selectbox("Quem é você?", lista_aprendizes, key="sel_apr")
    senha_digitada_apr = ""
    if nome_apr != "Selecione...":
        senha_digitada_apr = st.text_input("Digite seu PIN de acesso:", type="password", key="pwd_apr")
        
    if nome_apr != "Selecione..." and senha_digitada_apr == senhas_separadores.get(nome_apr, ""):
        st.success(f"🔓 {obter_bom_dia()}, {nome_apr}! Acesso liberado.")
        tarefa_apr = st.selectbox("O que você fez agora?", lista_tarefas_aprendiz, key="sel_tarefa_apr")
        prod_apr, qtd_apr = "Selecione...", 0
        
        if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)":
            setor_do_aprendiz = setor_separadores.get(nome_apr, "Todos")
            lista_prod_aprendiz = list(dicionario_torres.keys()) if setor_do_aprendiz == "Torres" else list(dicionario_caixas.keys()) if setor_do_aprendiz == "Caixas" else list(dicionario_produtos.keys())
            prod_apr = st.selectbox("Qual modelo?", ["Selecione..."] + lista_prod_aprendiz, key="prod_apr_est")
            qtd_apr = st.number_input("Quantidade:", min_value=1, step=1, key="qtd_apr_est")
        elif tarefa_apr == "Abrir Material para Separadores":
            prod_apr = st.selectbox("Que material você abriu?", lista_materiais_abrir, key="mat_apr_abrir")
            qtd_apr = st.number_input("Quantidade (un/caixas):", min_value=1, step=1, key="qtd_apr_abrir")
        elif tarefa_apr == "Contagem de Estoque":
            prod_apr = "Contagem de Estoque"
            st.info("💡 Você marcou Contagem de Estoque. Registre os horários normalmente.")
        else: prod_apr = tarefa_apr
            
        col_apr1, col_apr2 = st.columns(2)
        with col_apr1: hora_ini_apr = st.text_input("Hora que começou:", placeholder="Ex: 0800", key="ini_apr")
        with col_apr2: hora_fim_apr = st.text_input("Hora que terminou:", placeholder="Ex: 1200", key="fim_apr")
        
        if st.button("🚀 Enviar pro Coordenador", use_container_width=True, key="btn_apr"):
            if (tarefa_apr in ["⚠️ FAZER ESTOQUE (Contar Peças)", "Abrir Material para Separadores"] and prod_apr == "Selecione...") or not hora_ini_apr or not hora_fim_apr:
                st.error("❌ Preencha tudo antes de enviar!")
            else:
                ini_corr_apr = auto_corrigir_hora(hora_ini_apr)
                fim_corr_apr = auto_corrigir_hora(hora_fim_apr)
                if not ini_corr_apr or not fim_corr_apr: st.error("❌ Horário inválido.")
                else:
                    if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)": produto_salvar_apr = f"APRENDIZ ESTOQUE: {prod_apr}"
                    elif tarefa_apr == "Abrir Material para Separadores": produto_salvar_apr = f"APRENDIZ ABRIR: {prod_apr}"
                    elif tarefa_apr == "Contagem de Estoque": produto_salvar_apr = "APRENDIZ: Contagem de Estoque"
                    else: produto_salvar_apr = f"APRENDIZ: {prod_apr}"
                        
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                   (nome_apr, produto_salvar_apr, qtd_apr, ini_corr_apr, fim_corr_apr, data_hoje_str, 'Pendente'))
                    conn.commit()
                    st.toast('Atividade salva! 🚀', icon='✅')
                    st.success("🎉 Atividade enviada com sucesso!")

# ----------------- ABA 2: COORDENADOR -----------------
with aba_coordenador:
    st.header("Área do Coordenador")
    senha_coord = st.text_input("Senha do Coordenador:", type="password", key="senha_coord")
    
    if senha_coord == "1234":
        
        st.subheader("👀 O que a equipe fez hoje")
        data_hoje_str = datetime.now().strftime("%d/%m/%Y")
        df_hoje = pd.read_sql_query("SELECT separador AS Funcionário, produto AS Atividade, quantidade AS Qtd, hora_inicio AS Início, hora_fim AS Fim, status AS Status FROM estoque WHERE data = ?", conn, params=(data_hoje_str,))
        if not df_hoje.empty:
            df_hoje['Atividade'] = df_hoje['Atividade'].str.replace("PEGO DO ESTOQUE: ", "🛒 Reposição: ")
            st.dataframe(df_hoje, hide_index=True, use_container_width=True)
        else:
            st.info("Ninguém lançou nada hoje ainda.")

        st.markdown("---")
        st.subheader("📋 Fila de Aprovação (Pendentes)")
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty: st.info("Nada pendente para aprovar. A equipe tá de boa! ✌️")
        else:
            for index, row in df_pendentes.iterrows():
                if row['produto'].startswith("APRENDIZ ESTOQUE:"):
                    tipo_card, txt_prod = "👦 ESTOQUE APRENDIZ", f"{row['produto'].replace('APRENDIZ ESTOQUE: ', '')} ({row['quantidade']} un)"
                elif row['produto'].startswith("APRENDIZ ABRIR:"):
                    tipo_card, txt_prod = "📦 ABRIR MATERIAL", f"{row['produto'].replace('APRENDIZ ABRIR: ', '')} ({row['quantidade']} pçs)"
                elif row['produto'].startswith("APRENDIZ:"):
                    tipo_card, txt_prod = "👦 TAREFA APRENDIZ", row['produto'].replace("APRENDIZ: ", "")
                elif row['produto'].startswith("APOIO:"):
                    tipo_card, txt_prod = "🛠️ APOIO SEPARADOR", row['produto'].replace("APOIO: ", "")
                elif row['produto'].startswith("PEGO DO ESTOQUE:"):
                    tipo_card, txt_prod = "🛒 REPOSIÇÃO", f"{row['produto'].replace('PEGO DO ESTOQUE: ', '')} ({row['quantidade']} un)"
                elif row['produto'] == "ADIANTAMENTO: Pedidos":
                    tipo_card, txt_prod = "🚀 ADIANTAR PEDIDOS", f"{row['quantidade']} pedidos adiantados"
                elif row['produto'] in ["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"]:
                    tipo_card, txt_prod = "⚙️ ATIV. DE SETOR", row['produto']
                else: tipo_card, txt_prod = "🔔 ESTOQUE SEPARADOR", f"{row['produto']} ({row['quantidade']} un)"
                
                with st.expander(f"{tipo_card} | {row['separador']} - {txt_prod}"):
                    if row['hora_inicio'] != "00:00":
                        st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']} | **Data:** {row['data']}")
                    else:
                        st.write(f"**Data:** {row['data']} (Sem horário)")
                        
                    col_ok, col_rej = st.columns(2)
                    with col_ok:
                        if st.button(f"✓ Dar OK", key=f"coord_ok_{row['id']}", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                    with col_rej:
                        confirmar_rej = st.checkbox("Confirmar Rejeição ❌", key=f"chk_rej_{row['id']}")
                        if st.button(f"Rejeitar", key=f"coord_rej_{row['id']}", use_container_width=True, disabled=not confirmar_rej):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM estoque WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()

        st.markdown("---")
        st.subheader("📅 Desempenho e Rankings (Aprovados)")
        col_c1, col_c2 = st.columns(2)
        with col_c1: data_inicio_coord = st.date_input("Data de Início:", value=date.today(), key="d_ini_coord", format="DD/MM/YYYY")
        with col_c2: data_fim_coord = st.date_input("Data Final:", value=date.today(), key="d_fim_coord", format="DD/MM/YYYY")
        
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        if not df_todos_aprovados.empty:
            df_todos_aprovados['data_calc'] = pd.to_datetime(df_todos_aprovados['data'], format='%d/%m/%Y').dt.date
            df_periodo_coord = df_todos_aprovados[(df_todos_aprovados['data_calc'] >= data_inicio_coord) & (df_todos_aprovados['data_calc'] <= data_fim_coord)].copy()
            
            if not df_periodo_coord.empty:
                df_periodo_coord['Minutos Gastos Reais'] = df_periodo_coord.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                
                # EXTRATO DETALHADO LINHA A LINHA PARA O COORDENADOR
                st.markdown("#### 📋 Extrato Detalhado (Linha a Linha)")
                df_detalhado_coord = df_periodo_coord[['data', 'separador', 'produto', 'quantidade', 'hora_inicio', 'hora_fim', 'Minutos Gastos Reais']].copy()
                df_detalhado_coord['Minutos Gastos Reais'] = df_detalhado_coord['Minutos Gastos Reais'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                df_detalhado_coord['produto'] = df_detalhado_coord['produto'].str.replace("PEGO DO ESTOQUE: ", "🛒 Reposição: ")
                df_detalhado_coord.columns = ['Data', 'Funcionário', 'Atividade', 'Qtd', 'Início', 'Fim', 'Tempo Gasto']
                st.dataframe(df_detalhado_coord, hide_index=True, use_container_width=True)

                # RANKINGS AGRUPADOS (Exclui Reposição do cálculo de tempo/eficiência)
                df_prod_coord = df_periodo_coord[~df_periodo_coord['produto'].str.startswith("APOIO:") & ~df_periodo_coord['produto'].str.startswith("APRENDIZ") & ~df_periodo_coord['produto'].str.startswith("ADIANTAMENTO:") & ~df_periodo_coord['produto'].str.startswith("PEGO DO ESTOQUE:") & ~df_periodo_coord['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])].copy()
                df_adiant_coord = df_periodo_coord[df_periodo_coord['produto'] == "ADIANTAMENTO: Pedidos"].copy()
                df_pego_estoque = df_periodo_coord[df_periodo_coord['produto'].str.startswith("PEGO DO ESTOQUE:")].copy()
                
                if not df_prod_coord.empty:
                    st.markdown("#### 🏆 Produtividade no Estoque (Agrupado)")
                    df_prod_coord['Tempo Padrão Unidade'] = df_prod_coord['produto'].map(dicionario_produtos).fillna(0)
                    df_prod_coord['Meta de Tempo Total'] = df_prod_coord['Tempo Padrão Unidade'] * df_prod_coord['quantidade']
                    rk_est_c = df_prod_coord.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_est_c['Eficiência'] = (rk_est_c['Meta_Tempo'] / rk_est_c['Tempo_Gasto']) * 100
                    rk_est_c['Eficiência'] = rk_est_c['Eficiência'].fillna(0).map(lambda x: f"{x:.1f}%")
                    rk_est_c['Tempo_Gasto'] = rk_est_c['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_est_c[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência']], hide_index=True, use_container_width=True)
                
                if not df_pego_estoque.empty:
                    st.markdown("#### 🛒 Materiais Pegos do Estoque (Reposição)")
                    df_pego_estoque['Modelo'] = df_pego_estoque['produto'].str.replace("PEGO DO ESTOQUE: ", "")
                    rk_pego = df_pego_estoque.groupby(['separador', 'Modelo'])['quantidade'].sum().reset_index()
                    rk_pego.columns = ['Funcionário', 'Modelo Reposto', 'Qtd Total']
                    st.dataframe(rk_pego, hide_index=True, use_container_width=True)
                
                if not df_adiant_coord.empty:
                    st.markdown("#### 🚀 Pedidos Adiantados (Agrupado)")
                    rk_adiant_c = df_adiant_coord.groupby('separador').agg(Total_Pedidos=('quantidade', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_adiant_c['Tempo_Gasto'] = rk_adiant_c['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_adiant_c[['separador', 'Total_Pedidos', 'Tempo_Gasto']], hide_index=True, use_container_width=True)
            else: st.warning("Nada aprovado nessas datas.")

# ----------------- ABA 3: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Gestão")
    senha_gestor = st.text_input("Senha do Gestor Geral:", type="password", key="senha_gestor")
    
    if senha_gestor == "9999":
        st.subheader("🛡️ Proteção de Histórico (Backup Nuvem)")
        if st.button("💾 Salvar Backup Seguro no GitHub", type="primary", use_container_width=True):
            with st.spinner("Conectando ao GitHub e salvando histórico antigo e novo..."):
                if salvar_backup_no_github():
                    st.success("🎉 Sensacional! Backup feito com sucesso no seu GitHub. Histórico blindado!")
                else:
                    st.error("❌ Falha ao salvar no GitHub. Verifique as configurações de Secrets.")

        st.markdown("---")
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
                
                # TABELA NOVA: EXTRATO DETALHADO LINHA A LINHA PARA O GESTOR
                st.markdown("#### 📋 Extrato Detalhado do Período (Linha a Linha)")
                df_detalhado = df_filtrado[['data', 'separador', 'produto', 'quantidade', 'hora_inicio', 'hora_fim', 'Minutos Gastos Reais']].copy()
                df_detalhado['Minutos Gastos Reais'] = df_detalhado['Minutos Gastos Reais'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                df_detalhado['produto'] = df_detalhado['produto'].str.replace("PEGO DO ESTOQUE: ", "🛒 Reposição: ")
                df_detalhado.columns = ['Data', 'Funcionário', 'Atividade', 'Qtd', 'Início', 'Fim', 'Tempo Gasto']
                st.dataframe(df_detalhado, hide_index=True, use_container_width=True)

                df_producao = df_filtrado[~df_filtrado['produto'].str.startswith("APOIO:") & ~df_filtrado['produto'].str.startswith("APRENDIZ") & ~df_filtrado['produto'].str.startswith("ADIANTAMENTO:") & ~df_filtrado['produto'].str.startswith("PEGO DO ESTOQUE:") & ~df_filtrado['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])].copy()
                df_apoio = df_filtrado[df_filtrado['produto'].str.startswith("APOIO:")].copy()
                df_aprendiz_dados = df_filtrado[df_filtrado['produto'].str.startswith("APRENDIZ")].copy()
                df_adiantamento = df_filtrado[df_filtrado['produto'] == "ADIANTAMENTO: Pedidos"].copy()
                df_pego_estoque = df_filtrado[df_filtrado['produto'].str.startswith("PEGO DO ESTOQUE:")].copy()
                df_admin_seps = df_filtrado[df_filtrado['produto'].isin(["Contagem de Estoque", "Cortar Cabos", "Testar Torres", "Caixas Plug"])].copy()
                
                st.write(f"### 📈 Resumo Geral: {df_producao['quantidade'].sum()} un feitas | {df_adiantamento['quantidade'].sum()} pedidos adiantados")
                csv_dados = df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(label="📥 Baixar Relatório Completo (Excel)", data=csv_dados, file_name="relatorio_estoque.csv", mime="text/csv", type="primary")
                
                st.subheader("🏆 1. Ranking de Produtividade (Agrupado)")
                if not df_producao.empty:
                    df_producao['Tempo Padrão Unidade'] = df_producao['produto'].map(dicionario_produtos).fillna(0)
                    df_producao['Meta de Tempo Total'] = df_producao['Tempo Padrão Unidade'] * df_producao['quantidade']
                    ranking_est = df_producao.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_est['Eficiência Média'] = (ranking_est['Meta_Tempo'] / ranking_est['Tempo_Gasto']) * 100
                    ranking_est['Eficiência Média'] = ranking_est['Eficiência Média'].fillna(0).map(lambda x: f"{x:.1f}%")
                    ranking_est['Tempo_Gasto'] = ranking_est['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_est[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência Média']], hide_index=True, use_container_width=True)
                
                st.subheader("🛒 2. Materiais Pegos do Estoque (Reposição)")
                if not df_pego_estoque.empty:
                    df_pego_estoque['Modelo'] = df_pego_estoque['produto'].str.replace("PEGO DO ESTOQUE: ", "")
                    rk_pego = df_pego_estoque.groupby(['separador', 'Modelo'])['quantidade'].sum().reset_index()
                    rk_pego.columns = ['Funcionário', 'Modelo Reposto', 'Qtd Total']
                    st.dataframe(rk_pego, hide_index=True, use_container_width=True)
                else:
                    st.info("Nenhuma reposição de estoque registrada.")
                
                st.subheader("🛠️ 3. Relatório de Apoio (Agrupado)")
                if not df_apoio.empty:
                    ranking_ap = df_apoio.groupby('separador').agg(Minutos_Apoio=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_ap['Tempo Total'] = ranking_ap['Minutos_Apoio'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_ap[['separador', 'Tempo Total']], hide_index=True, use_container_width=True)
                
                st.subheader("👦 4. Menor Aprendiz (Agrupado)")
                if not df_aprendiz_dados.empty:
                    df_aprendiz_dados['Atividade'] = df_aprendiz_dados['produto'].str.replace("APRENDIZ ESTOQUE: ", "Estoque: ").str.replace("APRENDIZ ABRIR: ", "Abriu Material: ").str.replace("APRENDIZ: ", "")
                    rk_apr = df_aprendiz_dados.groupby(['separador', 'Atividade']).agg(Tempo_Gasto=('Minutos Gastos Reais', 'sum'), Pecas_Feitas=('quantidade', 'sum')).reset_index()
                    rk_apr['Resultado'] = rk_apr.apply(lambda r: f"{int(r['Tempo_Gasto'])} min (Fez/Abriu {int(r['Pecas_Feitas'])} un)" if r['Pecas_Feitas'] > 0 else f"{int(r['Tempo_Gasto'])} min", axis=1)
                    st.dataframe(rk_apr.rename(columns={'separador':'Aprendiz'})[['Aprendiz', 'Atividade', 'Resultado']], hide_index=True, use_container_width=True)
                
                st.subheader("🚀 5. Pedidos Adiantados (Agrupado)")
                if not df_adiantamento.empty:
                    rk_adiant = df_adiantamento.groupby('separador').agg(Total_Pedidos=('quantidade', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_adiant['Tempo'] = rk_adiant['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(rk_adiant.rename(columns={'separador':'Funcionário'})[['Funcionário', 'Total_Pedidos', 'Tempo']], hide_index=True, use_container_width=True)
                
                st.subheader("⚙️ 6. Atividades Administrativas e de Setor")
                if not df_admin_seps.empty:
                    rk_admin = df_admin_seps.groupby(['separador', 'produto']).agg(Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_admin['Tempo'] = rk_admin['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_admin.rename(columns={'separador':'Funcionário', 'produto':'Atividade'})[['Funcionário', 'Atividade', 'Tempo']], hide_index=True, use_container_width=True)
            else: st.warning("Sem dados aprovados.")
        
        st.markdown("---")
        st.subheader("⚠️ Zona de Risco")
        with st.expander("Opções de Exclusão"):
            lista_todos_nomes = lista_separadores[1:] + lista_aprendizes[1:]
            separador_para_deletar = st.selectbox("Limpar histórico de alguém?", ["Selecione..."] + lista_todos_nomes, key="del_sep")
            confirmacao_individual = st.checkbox("Confirmo que desejo apagar permanentemente.", key="chk_ind")
            if st.button("🗑️ APAGAR HISTÓRICO", type="primary", disabled=not confirmacao_individual or separador_para_deletar == "Selecione..."):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE separador = ?", (separador_para_deletar,))
                conn.commit()
                st.success("💥 Limpo com sucesso!")
                st.rerun()
