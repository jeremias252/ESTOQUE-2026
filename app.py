import streamlit as st
import pandas as pd
import sqlite3
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

# =====================================================================
# ÁREA DE EDIÇÃO: SEPARADORES E PRODUTOS (COM TEMPO)
# =====================================================================

separadores_texto = """

Henrique
Fran
Leonardo
Patrick
Sérgio
Fabiano
Marcello

"""

# Regra: Digite o NOME DO PRODUTO = TEMPO EM MINUTOS
produtos_texto = """
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

# Lógica para ler os tempos e produtos
dicionario_produtos = {}
for linha in produtos_texto.strip().split('\n'):
    if '=' in linha:
        nome, tempo = linha.split('=')
        dicionario_produtos[nome.strip()] = float(tempo.strip())
    elif linha.strip():
        dicionario_produtos[linha.strip()] = 0.0

lista_separadores = ["Selecione..."] + [s.strip() for s in separadores_texto.strip().split('\n') if s.strip()]
lista_produtos = ["Selecione..."] + list(dicionario_produtos.keys())

# =====================================================================
# FIM DA ÁREA DE EDIÇÃO
# =====================================================================


# 3. INTERFACE DO USUÁRIO (STREAMLIT)
st.set_page_config(page_title="Controle de Estoque V4", page_icon="📦", layout="centered")

st.title("📦 Sistema de Estoque Móvel - V4")

aba_separador, aba_gestor = st.tabs(["📲 Área do Separador", "📊 Painel do Gestor (Você)"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    st.header("Registrar Novo Estoque")
    
    nome = st.selectbox("Seu Nome:", lista_separadores)
    produto = st.selectbox("Modelo do Produto:", lista_produtos)
    quantidade = st.number_input("Quantidade Produzida:", min_value=1, step=1)
    
    if produto != "Selecione..." and produto in dicionario_produtos:
        tempo_unidade = dicionario_produtos[produto]
        if tempo_unidade > 0:
            tempo_meta = tempo_unidade * grandmother_quantity if 'grandmother_quantity' in locals() else tempo_unidade * quantidade
            st.info(f"🎯 **Meta:** {tempo_unidade} min por unidade. Tempo esperado total: **{tempo_meta} minutos**.")
    
    col1, col2 = st.columns(2)
    with col1:
        hora_inicio = st.text_input("Horário de Início (Ex: 14:00):", placeholder="HH:MM")
    with col2:
        hora_fim = st.text_input("Horário de Término (Ex: 14:45):", placeholder="HH:MM")
        
    if st.button("🚀 Enviar para Conferência", use_container_width=True):
        if nome == "Selecione..." or produto == "Selecione..." or not hora_inicio or not hora_fim:
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
        else:
            data_hoje = datetime.now().strftime("%d/%m/%Y")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nome, produto, quantidade, hora_inicio, hora_fim, data_hoje, 'Pendente'))
            conn.commit()
            st.success("✅ Enviado com sucesso! Aguarde o OK do gestor.")

# ----------------- ABA 2: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Controle e Filtros")
    
    senha = st.text_input("Digite sua senha de administrador:", type="password")
    
    if senha == "1234":
        # 1. PEDIDOS PENDENTES (Mostra todos independente da data, para você não esquecer de aprovar nada)
        st.subheader("📋 Pedidos Aguardando sua Conferência")
        
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty:
            st.info("Não há nenhum registro aguardando aprovação no momento.")
        else:
            for index, row in df_pendentes.endswith if 'endswith' in dir(row) else df_pendentes.iterrows():
                with st.expander(f"🔔 {row['separador']} - {row['produto']} ({row['quantidade']} un)"):
                    st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']}")
                    st.write(f"**Data:** {row['data']}")
                    
                    if st.button(f"✓ Dar OK (Assinar)", key=f"ok_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.success(f"Registro de {row['separador']} Aprovado!")
                        st.rerun()

        st.markdown("---")
        
        # 2. FILTRO POR DATA DO RELATÓRIO
        st.subheader("📅 Filtrar Relatórios por Data")
        data_selecionada = st.date_input("Escolha o dia que deseja analisar:", value=date.today())
        data_formatada_str = data_selecionada.strftime("%d/%m/%Y")
        
        # Buscar os aprovados do banco
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_todos_aprovados.empty:
            # Filtrar o DataFrame para mostrar apenas o dia selecionado no calendário
            df_aprovados = df_todos_aprovados[df_todos_aprovados['data'] == data_formatada_str]
            
            if not df_aprovados.empty:
                df_aprovados['Minutos Gastos Reais'] = df_aprovados.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                df_aprovados['Tempo Padrão Unidade'] = df_aprovados['produto'].map(dicionario_produtos).fillna(0)
                df_aprovados['Meta de Tempo Total'] = df_aprovados['Tempo Padrão Unidade'] * df_aprovados['quantidade']
                
                # RANKING DE EFICIÊNCIA DO DIA DO SEPARADOR
                st.subheader(f"🏆 Ranking de Eficiência - Dia {data_formatada_str}")
                
                ranking_func = df_aprovados.groupby('separador').agg(
                    Total_Produtos=('quantidade', 'sum'),
                    Meta_Tempo=('Meta de Tempo Total', 'sum'),
                    Tempo_Gasto=('Minutos Gastos Reais', 'sum')
                ).reset_index()
                
                ranking_func['Eficiência'] = (ranking_func['Meta_Tempo'] / ranking_func['Tempo_Gasto']) * 100
                ranking_func['Eficiência'] = ranking_func['Eficiência'].fillna(0).map(lambda x: f"{x:.1f}%")
                
                ranking_func['Tempo_Gasto'] = ranking_func['Tempo_Gasto'].map(lambda x: f"{int(x)} min")
                ranking_func['Meta_Tempo'] = ranking_func['Meta_Tempo'].map(lambda x: f"{int(x)} min")
                
                ranking_func = ranking_func.sort_values(by='Total_Produtos', ascending=False)
                ranking_func.columns = ['Separador', 'Produtos Feitos', 'Tempo Ideal (Meta)', 'Tempo Real Gasto', 'Eficiência (%)']
                st.dataframe(ranking_func, hide_index=True, use_container_width=True)
                
                st.markdown("---")
                
                # DETALHADO POR PRODUTO DO DIA
                st.subheader("🔍 Consultar Histórico de Lançamentos do Dia")
                produto_filtro = st.selectbox("Escolha o produto para auditar:", ["Todos"] + list(df_aprovados['produto'].unique()))
                if produto_filtro != "Todos":
                    df_filtrado = df_aprovados[df_aprovados['produto'] == produto_filtro]
                    st.dataframe(df_filtrado[['separador', 'quantidade', 'hora_inicio', 'hora_fim']], hide_index=True, use_container_width=True)
                else:
                    st.dataframe(df_aprovados[['separador', 'produto', 'quantidade', 'hora_inicio', 'hora_fim']], hide_index=True, use_container_width=True)
            else:
                st.warning(f"Nenhum registro de estoque foi aprovado no dia {data_formatada_str}.")
        else:
            st.info("Nenhum registro foi aprovado no sistema até o momento.")
            
    elif senha != "":
        st.error("Senha incorreta.")
