import streamlit as st
import pandas as pd
import sqlite3
import re
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

# =====================================================================
# ÁREA DE EDIÇÃO: SEPARADORES, PRODUTOS E OUTRAS ATIVIDADES
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

atividades_apoio_texto = """
Embalar Mercadoria
Colocar Etiquetas
Fazer Pedido em Outro Setor
Organização/Limpeza
Suporte Geral Operacional
"""

dicionario_produtos = {}
for linha in produtos_texto.strip().split('\n'):
    if '=' in linha:
        nome, tempo = linha.split('=')
        dicionario_produtos[nome.strip()] = float(tempo.strip())
    elif linha.strip():
        dicionario_produtos[linha.strip()] = 0.0

lista_separadores = ["Selecione..."] + [s.strip() for s in separadores_texto.strip().split('\n') if s.strip()]
lista_produtos = ["Selecione..."] + [p.strip() for p in produtos_texto.strip().split('\n') if p.strip()] 
lista_selecao_produtos = ["Selecione...", "⚠️ ATIVIDADE DE APOIO (Outro Setor)"] + list(dicionario_produtos.keys())
lista_apoio = [a.strip() for a in atividades_apoio_texto.strip().split('\n') if a.strip()]

# =====================================================================
# FIM DA ÁREA DE EDIÇÃO
# =====================================================================

# 3. INTERFACE DO USUÁRIO (STREAMLIT)
st.set_page_config(page_title="Controle de Estoque", page_icon="📦", layout="centered")

esconder_menu_ingles = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(esconder_menu_ingles, unsafe_allow_html=True)

st.title("📦 Sistema de Estoque Móvel")
st.image("https://caixatomada.com/wp-content/uploads/2020/03/b_03-1.png", width=200)

aba_separador, aba_coordenador, aba_gestor = st.tabs(["📲 Separador", "📋 Coordenador", "📊 Gestor"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    # GAMIFICAÇÃO: TOP 3 DO DIA
    data_hoje_str = datetime.now().strftime("%d/%m/%Y")
    df_podio = pd.read_sql_query("SELECT separador, quantidade, produto FROM estoque WHERE status = 'Aprovado' AND data = ?", conn, params=(data_hoje_str,))
    if not df_podio.empty:
        df_podio_est = df_podio[~df_podio['produto'].str.startswith("APOIO:")]
        if not df_podio_est.empty:
            ranking_top3 = df_podio_est.groupby('separador')['quantidade'].sum().reset_index().sort_values('quantidade', ascending=False).head(3)
            if len(ranking_top3) > 0:
                st.markdown("### 🏆 Top 3 de Produção (Hoje)")
                cols = st.columns(3)
                medalhas = ["🥇", "🥈", "🥉"]
                for i, (idx, row_podio) in enumerate(ranking_top3.iterrows()):
                    with cols[i]:
                        st.info(f"{medalhas[i]} **{row_podio['separador']}**\n\n📦 {row_podio['quantidade']} un")
                st.markdown("---")

    st.header("Registrar Novo Estoque / Atividade")
    
    nome = st.selectbox("Seu Nome:", lista_separadores)
    produto_selecionado = st.selectbox("O que você fez?", lista_selecao_produtos)
    
    if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
        tipo_apoio = st.selectbox("Qual atividade de apoio você realizou?", lista_apoio)
        quantidade = 0
        st.info("💡 Você está registrando tempo de suporte. Foque em colocar os horários corretos.")
    else:
        quantidade = st.number_input("Quantidade Produzida:", min_value=1, step=1)
        if produto_selecionado != "Selecione..." and produto_selecionado in dicionario_produtos:
            tempo_unidade = dicionario_produtos[produto_selecionado]
            if tempo_unidade > 0:
                tempo_meta = tempo_unidade * quantidade
                st.info(f"🎯 **Meta:** {tempo_unidade} min/un. Total esperado: **{tempo_meta} minutos**.")
    
    col1, col2 = st.columns(2)
    with col1:
        hora_inicio = st.text_input("Horário de Início:", placeholder="Ex: 1430")
    with col2:
        hora_fim = st.text_input("Horário de Término:", placeholder="Ex: 1500")
        
    if st.button("🚀 Enviar para Conferência", use_container_width=True):
        if nome == "Selecione..." or produto_selecionado == "Selecione..." or not hora_inicio or not hora_fim:
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
        else:
            inicio_corrigido = auto_corrigir_hora(hora_inicio)
            fim_corrigido = auto_corrigir_hora(hora_fim)
            
            if not inicio_corrigido or not fim_corrigido:
                st.error("❌ Não conseguimos identificar os números no horário. Tente novamente.")
            else:
                produto_salvar = f"APOIO: {tipo_apoio}" if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)" else produto_selecionado
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (nome, produto_salvar, quantidade, inicio_corrigido, fim_corrigido, data_hoje_str, 'Pendente'))
                conn.commit()
                st.success(f"✅ Enviado com sucesso ({inicio_corrigido} às {fim_corrigido})! Aguarde aprovação.")

# ----------------- ABA 2: COORDENADOR -----------------
with aba_coordenador:
    st.header("Área do Coordenador (Dia a Dia)")
    senha_coord = st.text_input("Senha do Coordenador:", type="password", key="senha_coord")
    
    if senha_coord == "1234":
        st.subheader("📋 Pedidos e Atividades Pendentes")
        df_pendentes = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Pendente'", conn)
        
        if df_pendentes.empty:
            st.info("Nenhum registro aguardando aprovação.")
        else:
            for index, row in df_pendentes.iterrows():
                tipo_card = "🛠️ APOIO" if row['produto'].startswith("APOIO:") else "🔔 ESTOQUE"
                detalhe_qtd = "" if row['produto'].startswith("APOIO:") else f"({row['quantidade']} un)"
                
                with st.expander(f"{tipo_card} {row['separador']} - {row['produto'].replace('APOIO: ', '')} {detalhe_qtd}"):
                    st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']} | **Data:** {row['data']}")
                    
                    # BOTÕES DE APROVAR OU REJEITAR
                    col_ok, col_rej = st.columns(2)
                    with col_ok:
                        if st.button(f"✓ Dar OK", key=f"coord_ok_{row['id']}", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success(f"Registro Aprovado!")
                            st.rerun()
                    with col_rej:
                        if st.button(f"❌ Rejeitar", key=f"coord_rej_{row['id']}", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM estoque WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.error(f"Registro apagado e rejeitado!")
                            st.rerun()

        st.markdown("---")
        st.subheader("📅 Desempenho e Rankings Diários")
        
        data_selecionada = st.date_input("Escolha o dia para analisar:", value=date.today(), key="data_coord", format="DD/MM/YYYY")
        data_str = data_selecionada.strftime("%d/%m/%Y")
        
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        if not df_todos_aprovados.empty:
            df_diario = df_todos_aprovados[df_todos_aprovados['data'] == data_str].copy()
            if not df_diario.empty:
                df_diario['Minutos Gastos Reais'] = df_diario.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                df_prod_diario = df_diario[~df_diario['produto'].str.startswith("APOIO:")].copy()
                df_ap_diario = df_diario[df_diario['produto'].str.startswith("APOIO:")].copy()
                
                st.write(f"### 📈 Resumo do Dia {data_str}")
                
                if not df_prod_diario.empty:
                    st.markdown("#### 🏆 Produtividade no Estoque")
                    df_prod_diario['Tempo Padrão Unidade'] = df_prod_diario['produto'].map(dicionario_produtos).fillna(0)
                    df_prod_diario['Meta de Tempo Total'] = df_prod_diario['Tempo Padrão Unidade'] * df_prod_diario['quantidade']
                    
                    rk_est_dia = df_prod_diario.groupby('separador').agg(
                        Total_Produtos=('quantidade', 'sum'),
                        Meta_Tempo=('Meta de Tempo Total', 'sum'),
                        Tempo_Gasto=('Minutos Gastos Reais', 'sum')
                    ).reset_index()
                    
                    rk_est_dia['Eficiência'] = (rk_est_dia['Meta_Tempo'] / rk_est_dia['Tempo_Gasto']) * 100
                    rk_est_dia['Eficiência'] = rk_est_dia['Eficiência'].fillna(0).map(lambda x: f"{x:.1f}%")
                    rk_est_dia['Tempo_Gasto'] = rk_est_dia['Tempo_Gasto'].map(lambda x: f"{int(x)} min")
                    rk_est_dia = rk_est_dia.sort_values(by='Total_Produtos', ascending=False)
                    rk_est_dia.columns = ['Separador', 'Produtos Feitos', 'Meta de Tempo', 'Tempo Gasto', 'Eficiência']
                    st.dataframe(rk_est_dia[['Separador', 'Produtos Feitos', 'Tempo Gasto', 'Eficiência']], hide_index=True, use_container_width=True)
                
                if not df_ap_diario.empty:
                    st.markdown("#### 🛠️ Tempo em Outros Setores")
                    rk_ap_dia = df_ap_diario.groupby('separador').agg(Minutos_Apoio=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_ap_dia['Tempo Total de Apoio'] = rk_ap_dia['Minutos_Apoio'].map(lambda x: f"{int(x)} min" if x < 60 else f"{int(x/60)}h {int(x%60)}m")
                    rk_ap_dia = rk_ap_dia.sort_values(by='Minutos_Apoio', ascending=False)
                    st.dataframe(rk_ap_dia[['separador', 'Tempo Total de Apoio']], hide_index=True, use_container_width=True)
            else:
                st.warning(f"Sem registros aprovados no dia {data_str}.")
        else:
            st.info("Nenhum dado aprovado no sistema.")
    elif senha_coord != "":
        st.error("Senha incorreta.")

# ----------------- ABA 3: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Visão Estratégica")
    senha_gestor = st.text_input("Senha do Gestor Geral:", type="password", key="senha_gestor")
    
    if senha_gestor == "9999":
        st.subheader("⚠️ Zona de Risco")
        with st.expander("Clique aqui para opções de EXCLUSÃO"):
            separador_para_deletar = st.selectbox("Escolha o separador para limpar o histórico:", lista_separadores, key="del_sep")
            confirmacao_individual = st.checkbox(f"Confirmo que desejo apagar o histórico de {separador_para_deletar}.", key="chk_ind")
            if st.button("🗑️ APAGAR HISTÓRICO DELE(A)", type="primary", disabled=not confirmacao_individual or separador_para_deletar == "Selecione..."):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE separador = ?", (separador_para_deletar,))
                conn.commit()
                st.success(f"💥 Todo o histórico apagado!")
                st.rerun()
                
            st.markdown("---")
            confirmacao_total = st.checkbox("Eu entendo que essa ação vai zerar TODO o sistema e não pode ser desfeita.", key="chk_tot")
            if st.button("🔥 APAGAR TODOS OS REGISTROS DO SISTEMA", type="primary", disabled=not confirmacao_total):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque")
                conn.commit()
                st.success("💥 O banco de dados foi completamente zerado!")
                st.rerun()
                
        st.markdown("---")
        st.subheader("📆 Avaliação por Período")
        col_d1, col_d2 = st.columns(2)
        with col_d1: data_inicio = st.date_input("Data de Início:", value=date.today(), format="DD/MM/YYYY")
        with col_d2: data_fim = st.date_input("Data Final:", value=date.today(), format="DD/MM/YYYY")
            
        df_geral = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_geral.empty:
            df_geral['data_calc'] = pd.to_datetime(df_geral['data'], format='%d/%m/%Y').dt.date
            df_filtrado = df_geral[(df_geral['data_calc'] >= data_inicio) & (df_geral['data_calc'] <= data_fim)].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Minutos Gastos Reais'] = df_filtrado.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                
                df_producao = df_filtrado[~df_filtrado['produto'].str.startswith("APOIO:")].copy()
                df_apoio = df_filtrado[df_filtrado['produto'].str.startswith("APOIO:")].copy()
                
                st.markdown("---")
                st.write(f"### 📈 Resumo Geral do Período")
                st.write(f"**Produtos Feitos:** {df_producao['quantidade'].sum()} unidades | **Tempo de Apoio:** {int(df_apoio['Minutos Gastos Reais'].sum() / 60)} horas")
                
                # BOTÃO DE EXPORTAÇÃO EXCEL/CSV
                csv_dados = df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(
                    label="📥 Baixar Relatório (Para Excel)",
                    data=csv_dados,
                    file_name=f"relatorio_estoque_{data_inicio.strftime('%d-%m')}_a_{data_fim.strftime('%d-%m')}.csv",
                    mime="text/csv",
                    type="primary"
                )
                
                # DASHBOARD: GRÁFICOS VISUAIS
                if not df_producao.empty:
                    st.markdown("#### 📊 Gráfico: Quantidade de Produtos por Separador")
                    grafico_dados = df_producao.groupby('separador')['quantidade'].sum().reset_index()
                    st.bar_chart(data=grafico_dados.set_index('separador'))
                
                st.subheader("🏆 1. Ranking de Produtividade no Estoque")
                if not df_producao.empty:
                    df_producao['Tempo Padrão Unidade'] = df_producao['produto'].map(dicionario_produtos).fillna(0)
                    df_producao['Meta de Tempo Total'] = df_producao['Tempo Padrão Unidade'] * df_producao['quantidade']
                    
                    ranking_est = df_producao.groupby('separador').agg(
                        Total_Produtos=('quantidade', 'sum'),
                        Meta_Tempo=('Meta de Tempo Total', 'sum'),
                        Tempo_Gasto=('Minutos Gastos Reais', 'sum')
                    ).reset_index()
                    
                    ranking_est['Eficiência Média'] = (ranking_est['Meta_Tempo'] / ranking_est['Tempo_Gasto']) * 100
                    ranking_est['Eficiência Média'] = ranking_est['Eficiência Média'].fillna(0).map(lambda x: f"{x:.1f}%")
                    ranking_est['Tempo_Gasto'] = ranking_est['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    ranking_est = ranking_est.sort_values(by='Total_Produtos', ascending=False)
                    ranking_est.columns = ['Separador', 'Produtos Feitos', 'Meta Total', 'Tempo Total Gasto', 'Eficiência Média']
                    st.dataframe(ranking_est[['Separador', 'Produtos Feitos', 'Tempo Total Gasto', 'Eficiência Média']], hide_index=True, use_container_width=True)
                
                st.subheader("🛠️ 2. Relatório de Horas em Atividades de Apoio")
                if not df_apoio.empty:
                    ranking_ap = df_apoio.groupby('separador').agg(Minutos_Apoio=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_ap['Tempo Total de Apoio'] = ranking_ap['Minutos_Apoio'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    ranking_ap = ranking_ap.sort_values(by='Minutos_Apoio', ascending=False)
                    ranking_ap.columns = ['Funcionário', 'Minutos', 'Tempo Total Dedicado a Outros Setores']
                    st.dataframe(ranking_ap[['Funcionário', 'Tempo Total Dedicado a Outros Setores']], hide_index=True, use_container_width=True)
                    
            else:
                st.warning("Não há dados aprovados neste intervalo de datas.")
        else:
            st.info("Nenhum registro foi aprovado no sistema ainda.")
    elif senha_gestor != "":
        st.error("Senha de gestor incorreta.")
