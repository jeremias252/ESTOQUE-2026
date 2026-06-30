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

def validar_e_formatar_hora(texto):
    texto = texto.strip().replace(":", "")
    if len(texto) == 3 and texto.isdigit():
        texto = "0" + texto
    if len(texto) == 4 and texto.isdigit():
        hora = texto[:2]
        minuto = texto[2:]
        if 0 <= int(hora) < 24 and 0 <= int(minuto) < 60:
            return f"{hora}:{minuto}"
    return None

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
st.set_page_config(page_title="Controle de Estoque V6", page_icon="📦", layout="centered")

st.title("📦 Sistema de Estoque Móvel - V6")

# AGORA SÃO 3 ABAS
aba_separador, aba_coordenador, aba_gestor = st.tabs(["📲 Separador", "📋 Coordenador", "📊 Gestor (Visão Geral)"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    st.header("Registrar Novo Estoque")
    
    nome = st.selectbox("Seu Nome:", lista_separadores)
    produto = st.selectbox("Modelo do Produto:", lista_produtos)
    quantidade = st.number_input("Quantidade Produzida:", min_value=1, step=1)
    
    if produto != "Selecione..." and produto in dicionario_produtos:
        tempo_unidade = dicionario_produtos[produto]
        if tempo_unidade > 0:
            tempo_meta = tempo_unidade * quantidade
            st.info(f"🎯 **Meta:** {tempo_unidade} min/un. Total esperado: **{tempo_meta} minutos**.")
    
    col1, col2 = st.columns(2)
    with col1:
        hora_inicio = st.text_input("Horário de Início (Ex: 1730):", placeholder="HHMM")
    with col2:
        hora_fim = st.text_input("Horário de Término (Ex: 1800):", placeholder="HHMM")
        
    if st.button("🚀 Enviar para Conferência", use_container_width=True):
        if nome == "Selecione..." or produto == "Selecione..." or not hora_inicio or not hora_fim:
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
        else:
            inicio_formatado = validar_e_formatar_hora(hora_inicio)
            fim_formatado = validar_e_formatar_hora(hora_fim)
            
            if not inicio_formatado or not fim_formatado:
                st.error("❌ Horário inválido! Digite apenas os números (ex: 1730) ou use HH:MM (ex: 17:30).")
            else:
                data_hoje = datetime.now().strftime("%d/%m/%Y")
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (nome, produto, quantidade, inicio_formatado, fim_formatado, data_hoje, 'Pendente'))
                conn.commit()
                st.success(f"✅ Enviado com sucesso ({inicio_formatado} às {fim_formatado})! Aguarde aprovação.")

# ----------------- ABA 2: COORDENADOR -----------------
with aba_coordenador:
    st.header("Área do Coordenador (Dia a Dia)")
    senha_coord = st.text_input("Senha do Coordenador:", type="password", key="senha_coord")
    
    if senha_coord == "1234":
        st.subheader("📋 Pedidos Pendentes de Conferência")
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty:
            st.info("Nenhum registro aguardando aprovação.")
        else:
            for index, row in df_pendentes.iterrows():
                with st.expander(f"🔔 {row['separador']} - {row['produto']} ({row['quantidade']} un)"):
                    st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']} | **Data:** {row['data']}")
                    if st.button(f"✓ Dar OK (Assinar)", key=f"coord_ok_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                        conn.commit()
                        st.success(f"Registro Aprovado!")
                        st.rerun()

        st.markdown("---")
        st.subheader("📅 Desempenho Diário")
        data_selecionada = st.date_input("Escolha o dia:", value=date.today(), key="data_coord")
        data_str = data_selecionada.strftime("%d/%m/%Y")
        
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        if not df_todos_aprovados.empty:
            df_aprovados = df_todos_aprovados[df_todos_aprovados['data'] == data_str]
            if not df_aprovados.empty:
                df_aprovados['Minutos Gastos Reais'] = df_aprovados.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                df_aprovados['Tempo Padrão Unidade'] = df_aprovados['produto'].map(dicionario_produtos).fillna(0)
                df_aprovados['Meta de Tempo Total'] = df_aprovados['Tempo Padrão Unidade'] * df_aprovados['quantidade']
                
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
                ranking_func.columns = ['Separador', 'Produtos Feitos', 'Meta de Tempo', 'Tempo Gasto', 'Eficiência']
                st.dataframe(ranking_func, hide_index=True, use_container_width=True)
            else:
                st.warning(f"Sem registros aprovados no dia {data_str}.")
        else:
            st.info("Nenhum dado aprovado no sistema.")
    elif senha_coord != "":
        st.error("Senha incorreta.")

# ----------------- ABA 3: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Visão Estratégica (Mês/Semana)")
    senha_gestor = st.text_input("Senha do Gestor Geral:", type="password", key="senha_gestor")
    
    if senha_gestor == "9999": # SENHA DO GESTOR
        st.subheader("📆 Avaliação por Período")
        st.write("Selecione um intervalo de datas para ver o acumulado da equipe:")
        
        # Filtro de período (Data Início e Data Fim)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_inicio = st.date_input("Data de Início:", value=date.today())
        with col_d2:
            data_fim = st.date_input("Data Final:", value=date.today())
            
        df_geral = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_geral.empty:
            # Converte a coluna de datas do formato BR para formato de cálculo
            df_geral['data_calc'] = pd.to_datetime(df_geral['data'], format='%d/%m/%Y').dt.date
            
            # Filtra os dados pelo período selecionado
            df_filtrado = df_geral[(df_geral['data_calc'] >= data_inicio) & (df_geral['data_calc'] <= data_fim)]
            
            if not df_filtrado.empty:
                df_filtrado['Minutos Gastos Reais'] = df_filtrado.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                df_filtrado['Tempo Padrão Unidade'] = df_filtrado['produto'].map(dicionario_produtos).fillna(0)
                df_filtrado['Meta de Tempo Total'] = df_filtrado['Tempo Padrão Unidade'] * df_filtrado['quantidade']
                
                # TOTALIZADORES
                st.markdown("---")
                st.write(f"**Resumo do período ({data_inicio.strftime('%d/%m')} até {data_fim.strftime('%d/%m')}):**")
                total_pecas = df_filtrado['quantidade'].sum()
                horas_trabalhadas = int(df_filtrado['Minutos Gastos Reais'].sum() / 60)
                st.success(f"📦 Total de Produtos Feitos: **{total_pecas}** | ⏱️ Horas Produtivas Focadas: **{horas_trabalhadas}h**")
                
                # RANKING ACUMULADO
                st.subheader("🏆 Ranking Acumulado do Período")
                ranking_gestor = df_filtrado.groupby('separador').agg(
                    Total_Produtos=('quantidade', 'sum'),
                    Meta_Tempo=('Meta de Tempo Total', 'sum'),
                    Tempo_Gasto=('Minutos Gastos Reais', 'sum')
                ).reset_index()
                
                ranking_gestor['Eficiência Média'] = (ranking_gestor['Meta_Tempo'] / ranking_gestor['Tempo_Gasto']) * 100
                ranking_gestor['Eficiência Média'] = ranking_gestor['Eficiência Média'].fillna(0).map(lambda x: f"{x:.1f}%")
                ranking_gestor['Tempo_Gasto'] = ranking_gestor['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                
                ranking_gestor = ranking_gestor.sort_values(by='Total_Produtos', ascending=False)
                ranking_gestor.columns = ['Separador', 'Soma de Produtos', 'Meta Total', 'Tempo Total Gasto', 'Eficiência Média']
                
                st.dataframe(ranking_gestor[['Separador', 'Soma de Produtos', 'Tempo Total Gasto', 'Eficiência Média']], hide_index=True, use_container_width=True)
                
            else:
                st.warning("Não há nenhum dado aprovado neste intervalo de datas selecionado.")
        else:
            st.info("Nenhum registro foi aprovado no sistema ainda.")
            
    elif senha_gestor != "":
        st.error("Senha de gestor incorreta.")
