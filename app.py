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
# ÁREA DE EDIÇÃO: SEPARADORES, PRODUTOS, MATERIAIS E SENHAS
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

# Altere aqui as senhas (PIN de 4 números) para cada um dos seus separadores
senhas_separadores = {
    "Henrique": "1010",
    "Fran": "2020",
    "Leonardo": "3030",
    "Patrick": "4040",
    "Fabiano": "5050",
    "Sérgio": "6060",
    "Marcello": "7070",
    "Renan Aprendiz": "8080" # O aprendiz também pode ter senha se quiser
}

aprendizes_texto = """
Renan Aprendiz
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

atividades_aprendiz_texto = """
⚠️ FAZER ESTOQUE (Contar Peças)
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

dicionario_produtos = {}
for linha in produtos_texto.strip().split('\n'):
    if '=' in linha:
        nome, tempo = linha.split('=')
        dicionario_produtos[nome.strip()] = float(tempo.strip())
    elif linha.strip():
        dicionario_produtos[linha.strip()] = 0.0

lista_separadores = ["Selecione..."] + [s.strip() for s in separadores_texto.strip().split('\n') if s.strip()]
lista_aprendizes = ["Selecione..."] + [a.strip() for a in aprendizes_texto.strip().split('\n') if a.strip()]
lista_selecao_produtos = ["Selecione...", "⚠️ ATIVIDADE DE APOIO (Outro Setor)"] + list(dicionario_produtos.keys())
lista_apoio = [a.strip() for a in atividades_apoio_texto.strip().split('\n') if a.strip()]
lista_tarefas_aprendiz = [t.strip() for t in atividades_aprendiz_texto.strip().split('\n') if t.strip()]
lista_materiais_abrir = ["Selecione..."] + [m.strip() for m in materiais_abertura_texto.strip().split('\n') if m.strip()]

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

aba_separador, aba_aprendiz, aba_coordenador, aba_gestor = st.tabs(["📲 Separador", "👦 Aprendiz", "📋 Coordenador", "📊 Gestor"])

# ----------------- ABA 1: SEPARADOR -----------------
with aba_separador:
    data_hoje_str = datetime.now().strftime("%d/%m/%Y")
    
    st.header("Registrar Novo Estoque / Atividade")
    nome = st.selectbox("Seu Nome:", lista_separadores, key="sel_sep_main")
    
    # MELHORIA: Campo de Senha para o Separador
    senha_digitada = ""
    if nome != "Selecione...":
        senha_digitada = st.text_input("Digite sua senha (PIN):", type="password", key="pwd_sep_main")

    produto_selecionado = st.selectbox("O que você fez?", lista_selecao_produtos, key="sel_prod_main")
    
    if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)":
        tipo_apoio = st.selectbox("Qual atividade de apoio você realizou?", lista_apoio)
        quantidade = 0
        st.info("💡 Você está registrando tempo de suporte. Foque em colocar os horários corretos.")
    else:
        quantidade = st.number_input("Quantidade Produzida:", min_value=1, step=1, key="num_qtd_main")
        if produto_selecionado != "Selecione..." and produto_selecionado in dicionario_produtos:
            tempo_unidade = dicionario_produtos[produto_selecionado]
            if tempo_unidade > 0:
                tempo_meta = tempo_unidade * quantidade
                st.info(f"🎯 **Meta:** {tempo_unidade} min/un. Total esperado: **{tempo_meta} minutos**.")
    
    col1, col2 = st.columns(2)
    with col1: hora_inicio = st.text_input("Horário de Início:", placeholder="Ex: 1430", key="txt_ini_main")
    with col2: hora_fim = st.text_input("Horário de Término:", placeholder="Ex: 1500", key="txt_fim_main")
        
    if st.button("🚀 Enviar para Conferência", use_container_width=True, key="btn_env_main"):
        if nome == "Selecione..." or produto_selecionado == "Selecione..." or not hora_inicio or not hora_fim or not senha_digitada:
            st.error("❌ Por favor, preencha todos os campos obrigatórios (incluindo sua senha)!")
        elif nome in senhas_separadores and senha_digitada != senhas_separadores[nome]:
            st.error("❌ Senha incorreta! Digite o PIN correto para enviar.")
        else:
            inicio_corrigido = auto_corrigir_hora(hora_inicio)
            fim_corrigido = auto_corrigir_hora(hora_fim)
            if not inicio_corrigido or not fim_corrigido:
                st.error("❌ Não conseguimos identificar os números no horário.")
            else:
                produto_salvar = f"APOIO: {tipo_apoio}" if produto_selecionado == "⚠️ ATIVIDADE DE APOIO (Outro Setor)" else produto_selecionado
                cursor = conn.cursor()
                cursor.execute('INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (nome, produto_salvar, quantidade, inicio_corrigido, fim_corrigido, data_hoje_str, 'Pendente'))
                conn.commit()
                st.success(f"✅ Enviado com sucesso! Aguarde aprovação.")

    # MELHORIA: Área para o próprio Separador consultar o histórico dele
    st.markdown("---")
    st.subheader("🔍 Consultar Meu Histórico Diário")
    if nome != "Selecione..." and nome in senhas_separadores and senha_digitada == senhas_separadores[nome]:
        data_consulta = st.date_input("Escolha o dia para ver seu estoque:", value=date.today(), key="date_consult_sep", format="DD/MM/YYYY")
        data_cons_str = data_consulta.strftime("%d/%m/%Y")
        
        df_historico_sep = pd.read_sql_query("SELECT produto, quantidade, status FROM estoque WHERE separador = ? AND data = ?", conn, params=(nome, data_cons_str))
        if df_historico_sep.empty:
            st.info("Você não tem lançamentos registrados neste dia.")
        else:
            # Limpa o texto "APOIO:" para ficar bonito para eles lerem
            df_historico_sep['produto'] = df_historico_sep['produto'].str.replace("APOIO: ", "Apoio: ")
            st.dataframe(df_historico_sep, hide_index=True, use_container_width=True)
    else:
        st.caption("🔒 Digite sua senha correta acima para liberar a consulta do seu histórico.")

# ----------------- ABA 1.5: MENOR APRENDIZ -----------------
with aba_aprendiz:
    st.header("📲 Área do Menor Aprendiz")
    nome_apr = st.selectbox("Seu Nome (Aprendiz):", lista_aprendizes, key="sel_apr")
    
    # Senha para o Aprendiz
    senha_digitada_apr = ""
    if nome_apr != "Selecione...":
        senha_digitada_apr = st.text_input("Digite sua senha (PIN) Aprendiz:", type="password", key="pwd_apr")
        
    tarefa_apr = st.selectbox("Qual atividade você realizou?", lista_tarefas_aprendiz, key="sel_tarefa_apr")
    
    prod_apr = "Selecione..."
    qtd_apr = 0
    
    if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)":
        prod_apr = st.selectbox("Qual modelo de produto você fez?", ["Selecione..."] + list(dicionario_produtos.keys()), key="prod_apr_est")
        qtd_apr = st.number_input("Quantidade Produzida:", min_value=1, step=1, key="qtd_apr_est")
    elif tarefa_apr == "Abrir Material para Separadores":
        prod_apr = st.selectbox("Qual material você abriu?", lista_materiais_abrir, key="mat_apr_abrir")
        qtd_apr = st.number_input("Quantidade aberta (un/caixas):", min_value=1, step=1, key="qtd_apr_abrir")
    else:
        prod_apr = tarefa_apr
        
    col_apr1, col_apr2 = st.columns(2)
    with col_apr1: hora_ini_apr = st.text_input("Horário de Início:", placeholder="Ex: 0800", key="ini_apr")
    with col_apr2: hora_fim_apr = st.text_input("Horário de Término:", placeholder="Ex: 1200", key="fim_apr")
    
    if st.button("🚀 Enviar Atividade do Aprendiz", use_container_width=True, key="btn_apr"):
        if nome_apr == "Selecione..." or (tarefa_apr in ["⚠️ FAZER ESTOQUE (Contar Peças)", "Abrir Material para Separadores"] and prod_apr == "Selecione...") or not hora_ini_apr or not hora_fim_apr or not senha_digitada_apr:
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
        elif nome_apr in senhas_separadores and senha_digitada_apr != senhas_separadores[nome_apr]:
            st.error("❌ Senha incorreta do Aprendiz!")
        else:
            ini_corr_apr = auto_corrigir_hora(hora_ini_apr)
            fim_corr_apr = auto_corrigir_hora(hora_fim_apr)
            if not ini_corr_apr or not fim_corr_apr:
                st.error("❌ Horários inválidos.")
            else:
                if tarefa_apr == "⚠️ FAZER ESTOQUE (Contar Peças)":
                    produto_salvar_apr = f"APRENDIZ ESTOQUE: {prod_apr}"
                elif tarefa_apr == "Abrir Material para Separadores":
                    produto_salvar_apr = f"APRENDIZ ABRIR: {prod_apr}"
                else:
                    produto_salvar_apr = f"APRENDIZ: {prod_apr}"
                    
                cursor = conn.cursor()
                cursor.execute('INSERT INTO estoque (separador, produto, quantity, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)' if 'quantity' in locals() else 'INSERT INTO estoque (separador, produto, quantidade, hora_inicio, hora_fim, data, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (nome_apr, produto_salvar_apr, qtd_apr, ini_corr_apr, fim_corr_apr, data_hoje_str, 'Pendente'))
                conn.commit()
                st.success(f"✅ Atividade enviada com sucesso!")

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
                else:
                    tipo_card = "🔔 ESTOQUE SEPARADOR"
                    txt_prod = f"{row['produto']} ({row['quantidade']} un)"
                
                with st.expander(f"{tipo_card} | {row['separador']} - {txt_prod}"):
                    st.write(f"**Horário:** {row['hora_inicio']} até {row['hora_fim']} | **Data:** {row['data']}")
                    col_ok, col_rej = st.columns(2)
                    with col_ok:
                        if st.button(f"✓ Dar OK", key=f"coord_ok_{row['id']}", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE estoque SET status = 'Aprovado' WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                    with col_rej:
                        if st.button(f"❌ Rejeitar", key=f"coord_rej_{row['id']}", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM estoque WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()

        st.markdown("---")
        st.subheader("📅 Avaliação e Rankings por Período")
        col_c1, col_c2 = st.columns(2)
        with col_c1: data_inicio_coord = st.date_input("Data de Início:", value=date.today(), key="d_ini_coord", format="DD/MM/YYYY")
        with col_c2: data_fim_coord = st.date_input("Data Final:", value=date.today(), key="d_fim_coord", format="DD/MM/YYYY")
        
        df_todos_aprovados = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        if not df_todos_aprovados.empty:
            df_todos_aprovados['data_calc'] = pd.to_datetime(df_todos_aprovados['data'], format='%d/%m/%Y').dt.date
            df_periodo_coord = df_todos_aprovados[(df_todos_aprovados['data_calc'] >= data_inicio_coord) & (df_todos_aprovados['data_calc'] <= data_fim_coord)].copy()
            
            if not df_periodo_coord.empty:
                df_periodo_coord['Minutos Gastos Reais'] = df_periodo_coord.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                df_prod_coord = df_periodo_coord[~df_periodo_coord['produto'].str.startswith("APOIO:") & ~df_periodo_coord['produto'].str.startswith("APRENDIZ")].copy()
                
                if not df_prod_coord.empty:
                    st.markdown("#### 🏆 Produtividade no Estoque (Separadores)")
                    df_prod_coord['Tempo Padrão Unidade'] = df_prod_coord['produto'].map(dicionario_produtos).fillna(0)
                    df_prod_coord['Meta de Tempo Total'] = df_prod_coord['Tempo Padrão Unidade'] * df_prod_coord['quantidade']
                    rk_est_c = df_prod_coord.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    rk_est_c['Eficiência'] = (rk_est_c['Meta_Tempo'] / rk_est_c['Tempo_Gasto']) * 100
                    rk_est_c['Eficiência'] = rk_est_c['Eficiência'].fillna(0).map(lambda x: f"{x:.1f}%")
                    rk_est_c['Tempo_Gasto'] = rk_est_c['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    st.dataframe(rk_est_c[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência']], hide_index=True, use_container_width=True)
            else:
                st.warning("Sem registros aprovados neste período.")

# ----------------- ABA 3: GESTOR (VOCÊ) -----------------
with aba_gestor:
    st.header("Painel de Visão Estratégica")
    senha_gestor = st.text_input("Senha do Gestor Geral:", type="password", key="senha_gestor")
    
    if senha_gestor == "9999":
        st.subheader("📆 Avaliação por Período")
        col_d1, col_d2 = st.columns(2)
        with col_d1: data_inicio = st.date_input("Data de Início:", value=date.today(), key="ini_gestor", format="DD/MM/YYYY")
        with col_d2: data_fim = st.date_input("Data Final:", value=date.today(), key="fim_gestor", format="DD/MM/YYYY")
            
        df_geral = pd.read_sql_query("SELECT * FROM estoque WHERE status = 'Aprovado'", conn)
        
        if not df_geral.empty:
            df_geral['data_calc'] = pd.to_datetime(df_geral['data'], format='%d/%m/%Y').dt.date
            df_filtrado = df_geral[(df_geral['data_calc'] >= data_inicio) & (df_geral['data_calc'] <= data_fim)].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Minutos Gastos Reais'] = df_filtrado.apply(lambda r: calcular_minutos(r['hora_inicio'], r['hora_fim']), axis=1)
                
                df_producao = df_filtrado[~df_filtrado['produto'].str.startswith("APOIO:") & ~df_filtrado['produto'].str.startswith("APRENDIZ")].copy()
                df_apoio = df_filtrado[df_filtrado['produto'].str.startswith("APOIO:")].copy()
                df_aprendiz_dados = df_filtrado[df_filtrado['produto'].str.startswith("APRENDIZ")].copy()
                
                st.markdown("---")
                st.write(f"### 📈 Resumo Geral do Período")
                st.write(f"**Produtos Feitos:** {df_producao['quantidade'].sum()} unidades | **Tempo de Apoio:** {int(df_apoio['Minutos Gastos Reais'].sum() / 60)} horas")
                
                csv_dados = df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(label="📥 Baixar Relatório (Para Excel)", data=csv_dados, file_name="relatorio_estoque.csv", mime="text/csv", type="primary")
                
                # TABELA 1
                st.subheader("🏆 1. Ranking de Produtividade (Separadores)")
                if not df_producao.empty:
                    df_producao['Tempo Padrão Unidade'] = df_producao['produto'].map(dicionario_produtos).fillna(0)
                    df_producao['Meta de Tempo Total'] = df_producao['Tempo Padrão Unidade'] * df_producao['quantidade']
                    ranking_est = df_producao.groupby('separador').agg(Total_Produtos=('quantidade', 'sum'), Meta_Tempo=('Meta de Tempo Total', 'sum'), Tempo_Gasto=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_est['Eficiência Média'] = (ranking_est['Meta_Tempo'] / ranking_est['Tempo_Gasto']) * 100
                    ranking_est['Eficiência Média'] = ranking_est['Eficiência Média'].fillna(0).map(lambda x: f"{x:.1f}%")
                    ranking_est['Tempo_Gasto'] = ranking_est['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_est[['separador', 'Total_Produtos', 'Tempo_Gasto', 'Eficiência Média']], hide_index=True, use_container_width=True)
                
                # TABELA 2
                st.subheader("🛠️ 2. Relatório de Horas de Apoio (Separadores)")
                if not df_apoio.empty:
                    ranking_ap = df_apoio.groupby('separador').agg(Minutos_Apoio=('Minutos Gastos Reais', 'sum')).reset_index()
                    ranking_ap['Tempo Total de Apoio'] = ranking_ap['Minutos_Apoio'].map(lambda x: f"{int(x/60)}h {int(x%60)}m")
                    st.dataframe(ranking_ap[['separador', 'Tempo Total de Apoio']], hide_index=True, use_container_width=True)
                
                # TABELA 3
                st.subheader("👦 3. Relatório de Atividades do Menor Aprendiz")
                if not df_aprendiz_dados.empty:
                    df_aprendiz_dados['Atividade Mapeada'] = df_aprendiz_dados['produto'].str.replace("APRENDIZ ESTOQUE: ", "Estoque: ").str.replace("APRENDIZ ABRIR: ", "Abriu Material: ").str.replace("APRENDIZ: ", "")
                    rk_apr = df_aprendiz_dados.groupby(['separador', 'Atividade Mapeada']).agg(Tempo_Gasto=('Minutos Gastos Reais', 'sum'), Pecas_Feitas=('quantidade', 'sum')).reset_index()
                    rk_apr['Tempo Formato'] = rk_apr['Tempo_Gasto'].map(lambda x: f"{int(x/60)}h {int(x%60)}m" if x >= 60 else f"{int(x)} min")
                    rk_apr['Resultado Final'] = rk_apr.apply(lambda r: f"{r['Tempo Formato']} (Fez/Abriu {int(r['Pecas_Feitas'])} un)" if r['Pecas_Feitas'] > 0 else r['Tempo Formato'], axis=1)
                    rk_apr.columns = ['Aprendiz', 'Atividade', 'Minutos', 'Pecas', 'Resultado Final']
                    st.dataframe(rk_apr[['Aprendiz', 'Atividade', 'Resultado Final']], hide_index=True, use_container_width=True)
                else:
                    st.info("Nenhuma atividade de menor aprendiz registrada no período.")
                    
            else: st.warning("Não há dados aprovados neste intervalo de datas.")
            
        # MELHORIA: ALTERADO PARA FICAR TOTALMENTE EMBAIXO NO CÓDIGO DO GESTOR
        st.markdown("---")
        st.subheader("⚠️ Zona de Risco Geral")
        with st.expander("Clique aqui para opções de EXCLUSÃO E LIMPEZA CRÍTICA"):
            lista_todos_nomes = lista_separadores[1:] + lista_aprendizes[1:]
            separador_para_deletar = st.selectbox("Escolha quem deseja limpar o histórico:", ["Selecione..."] + lista_todos_nomes, key="del_sep")
            confirmacao_individual = st.checkbox(f"Confirmo que desejo apagar permanentemente o histórico selecionado.", key="chk_ind")
            if st.button("🗑️ APAGAR HISTÓRICO", type="primary", disabled=not confirmacao_individual or separador_para_deletar == "Selecione..."):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque WHERE separador = ?", (separador_para_deletar,))
                conn.commit()
                st.success(f"💥 Histórico limpo com sucesso!")
                st.rerun()
                
            st.markdown("---")
            confirmacao_total = st.checkbox("Eu entendo que essa ação vai zerar TODO o sistema e não pode ser desfeita.", key="chk_tot")
            if st.button("🔥 APAGAR TODOS OS REGISTROS DO SISTEMA", type="primary", disabled=not confirmacao_total):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM estoque")
                conn.commit()
                st.success("💥 O banco de dados foi completamente zerado!")
                st.rerun()

    elif senha_gestor != "": st.error("Senha de gestor incorreta.")
