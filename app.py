import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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
        if fim < inicio: # Caso mude de dia à meia-noite
            return ((fim - inicio).seconds / 60) + 1440
        return (fim - inicio).seconds / 60
    except:
        return 0

# 3. INTERFACE DO USUÁRIO (STREAMLIT)
st.set_page_config(page_title="Controle de Estoque", page_icon="📦", layout="centered")

st.title("📦 Sistema de Estoque Móvel")

# Criando as abas para separar quem usa
aba_separador, aba_gestor = st.tabs(["📲 Área do Separador", "📊 Painel do Gestor (Você)"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    st.header("Registrar Novo Estoque")
    st.write("Preencha os dados assim que finalizar a atividade:")
    
    lista_separadores = ["Selecione...", "Henrique", "Leonardo", "Fran", "Patrick", "Sérgio", "Marcello", "Fabiano"]
    
    nome = st.selectbox("Seu Nome:", lista_separadores)
    produto = st.text_input("Nome/Código do Produto:").strip().upper()
    quantidade = st.number_input("Quantidade Produzida:", min_value=1, step=1)
    
    col1, col2 = st.columns(2)
    with col1:
        hora_inicio = st.text_input("Horário de Início (Ex: 14:00):", placeholder="HH:MM")
    with col2:
        hora_fim = st.text_input("Horário de Término (Ex: 14:45):", placeholder="HH:MM")
        
    if st.button("🚀 Enviar para Conferência", use_container_width=True):
        if nome == "Selecione..." or not produto or not hora_inicio or not hora_fim:
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
    
    # Sistema simples de senha para os separadores não mexerem no seu painel
    senha = st.text_input("Digite sua senha de administrador:", type="password")
    
    if senha == "Jere@160324": # Altere para a senha que desejar
        st.subheader("📋 Pedidos Aguardando sua Conferência")
        
        # Buscar pendentes
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty:
            st.info("Não há nenhum registro aguardando aprovação no momento.")
        else:
            for index, row in df_pendentes.iterrows():
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
        st.subheader("🏆 Filtro & Ranking de Produtividade (Aprovados)")
        
        # Buscar apenas os que você deu OK
        df_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_aprovados.empty:
            # Calcular o tempo de cada registro
            df_aprovados['Minutos Gastos'] = df_aprovados.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
            
            # Agrupar dados por Separador
            ranking = df_aprovados.groupby('separador').agg(
                Total_Produtos=('quantidade', 'sum'),
                Tempo_Total_Minutos=('Minutos Gastos', 'sum')
            ).reset_index()
            
            # Calcular velocidade (itens por minuto)
            ranking['Itens por Minuto'] = ranking['Total_Produtos'] / ranking['Tempo_Total_Minutos']
            ranking = ranking.sort_values(by='Total_Produtos', ascending=False)
            
            # Formatar tabela para exibição amigável
            ranking.columns = ['Separador', 'Produtos Feitos', 'Tempo Total (Minutos)', 'Velocidade (Itens/Min)']
            st.dataframe(ranking, hide_index=True, use_container_width=True)
            
            # Filtro por Produto
            st.subheader("🔍 Filtrar por Produto")
            produto_filtro = st.selectbox("Escolha o produto para auditar:", ["Todos"] + list(df_aprovados['produto'].unique()))
            if produto_filtro != "Todos":
                df_filtrado = df_aprovados[df_aprovados['produto'] == produto_filtro]
                st.dataframe(df_filtrado[['separador', 'quantidade', 'hora_inicio', 'hora_fim', 'data']], hide_index=True)
        else:
            st.info("Nenhum registro foi aprovado ainda hoje para gerar o ranking.")
            
    elif senha != "":
        st.error("Senha incorreta.")
