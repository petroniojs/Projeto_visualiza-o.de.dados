import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go




# -----------------------------
# Funções auxiliares
# -----------------------------
def carregar_dados(caminho_csv):
    df = pd.read_csv(caminho_csv)
    df['quantidade'] = df['quantidade'].str.replace(',', '.', regex=False).astype(float)
    return df

def filtrar_dados(df, distrito_selecionado):
    return df[df['distrito'] == distrito_selecionado]

def top_n_medicamentos_geral(df, n=10):
    return df.groupby('produto')['quantidade'].sum().sort_values(ascending=False).head(n).reset_index()

def top3_medicamentos_por_distrito(df):
    top3 = (
        df.groupby(['distrito', 'produto'])['quantidade']
        .sum()
        .reset_index()
        .sort_values(['distrito', 'quantidade'], ascending=[True, False])
    )
    return top3.groupby('distrito').head(3)






# -----------------------------
# Layout - Título e Filtros
# -----------------------------
st.set_page_config(page_title="Medicamentos por Distrito", layout="wide")
st.title("Distribuição de Medicamentos por Unidade de Saúde")

# Carregar dados
df = carregar_dados("medicamentos_por_unidade_de_saude.csv")

# Sidebar
st.sidebar.header("Filtros")
distritos = sorted(df['distrito'].dropna().unique())
distrito_selecionado = st.sidebar.selectbox("Selecione um Distrito", distritos)

# Filtrar dados por distrito
df_distrito = filtrar_dados(df, distrito_selecionado)



st.write("Esta visualização permite identificar, de forma clara, **quais distritos têm maior número de categorias com estoque zero ou abaixo do mínimo recomendado**, apoiando ações de redistribuição e planejamento mais eficiente da política de abastecimento.")
st.write("")
st.write("")

# -----------------------------
# Gráfico: Top 10 Medicamentos (Geral)
# -----------------------------
st.subheader("Medicamentos mais diponíveis na rede de saúde do Recife")
st.markdown("Na rede de saúde do Recife, os dados mostram um cuidado prioritário com doenças crônicas. A Losartana 50mg lidera em quantidade absoluta: são mais de 3 milhões de unidades distribuídas em 169 unidades diferentes. Juntas, Enalapril e Metformina somam mais de 4 milhões de comprimidos disponíveis. Essa concentração revela o esforço em manter sob controle os principais vilões da saúde pública: pressão alta e diabetes.")
st.write("")

top10_df = top_n_medicamentos_geral(df)

fig_top10 = px.bar(
    top10_df,
    x='quantidade',
    y='produto',
    orientation='h',
    text='quantidade',
    color='produto',
    title='Top 10 Medicamentos Mais Distribuídos',
)

fig_top10.update_layout(
    xaxis_title='Quantidade Total',
    yaxis_title='Medicamento',
    template='plotly_dark',
    height=500,
    showlegend=False
)
fig_top10.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_top10, use_container_width=True)






# -----------------------------
# Gráfico: Top 10 por Distrito
# -----------------------------
st.subheader("Medicamentos elegiveis em remanejamento de estoque")
top3_df = (
    df_distrito.groupby('produto')['quantidade']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_top3_distrito = px.bar(
    top3_df,
    x='produto',
    y='quantidade',
    color='produto',
    text='quantidade',
    title=f"Top 10 Medicamentos no Distrito {distrito_selecionado}"
)

fig_top3_distrito.update_layout(template='plotly_dark', showlegend=False)
fig_top3_distrito.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_top3_distrito, use_container_width=True)







# -----------------------------
# Gráfico: Top 10 por Distrito
# -----------------------------
st.subheader("Criticidade de Medicamento por Unidade de Saude")
# Agrupar a quantidade total de medicamentos por distrito
estoque_total_unid = df.groupby(["unidade","produto"])["quantidade"].sum().reset_index()
# classificar os estoques
def categorizar(qtd):
    if qtd == 0:
        return "Crítico"
    elif qtd <= 150:
        return "Alerta"
    else:
        return "Abastecido"
estoque_total_unid["criticidade"] = estoque_total_unid["quantidade"].apply(categorizar)







# -----------------------------
# DataFrame: Responsivo de acordo com o sidebar
# -----------------------------

# Sidebar - Filtros
st.sidebar.subheader("Filtros")

# Unidade
unidades = sorted(estoque_total_unid['unidade'].dropna().unique())
unidade_selecionada = st.sidebar.selectbox("Selecione uma Unidade", options=["Todos"] + unidades)

# Criticidade
criticidades = sorted(estoque_total_unid['criticidade'].dropna().unique())
criticidade_selecionada = st.sidebar.selectbox("Selecione uma Criticidade", options=["Todos"] + criticidades)

# Filtro condicional
df_filtrado = estoque_total_unid.copy()

if unidade_selecionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['unidade'] == unidade_selecionada]

if criticidade_selecionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['criticidade'] == criticidade_selecionada]

# Mostrar DataFrame
st.dataframe(df_filtrado)







#st.subheader("Quantidade de Produtos por Criticidade em cada Distrito")
st.write("")
#Relação única entre unidade e distrito
mapa_unidade_distrito = df[['unidade', 'distrito']].drop_duplicates()
#Merge com seu dataframe de criticidade
estoque_total_unid = estoque_total_unid.merge(mapa_unidade_distrito, on='unidade', how='left')
#Resultado agora tem as colunas: unidade, produto, quantidade, criticidade, distrito
#Agrupar por distrito e criticidade (quantos medicamentos estão em cada categoria por distrito)
criticidade_por_distrito = (
    estoque_total_unid.groupby(['distrito', 'criticidade'])['produto']
    .count()
    .reset_index()
    .rename(columns={'produto': 'quantidade'})
)

#Plot
fig_criticidade = px.bar(
    criticidade_por_distrito,
    x='distrito',
    y='quantidade',
    color='criticidade',
    title='Quantidade de Produtos por Criticidade em Cada Distrito',
    barmode='group',
    text='quantidade'
)
fig_criticidade.update_layout(template='plotly_dark')
st.plotly_chart(fig_criticidade, use_container_width=True)


st.write("")
st.markdown("Boas Práticas resultantes desta visualização: **Revisar os critérios de distribuição atual**, priorizando distritos com maior número de categorias críticas e em alerta.")
st.markdown("- **Realizar remanejamentos de estoque entre distritos**, sempre que possível, para garantir equidade no acesso.")
st.markdown("- **Monitorar continuamente** as categorias mais sensíveis para evitar ruptura completa.")





# -----------------------------
# Equipe
# -----------------------------
st.subheader("Equipe:")
st.write("Alberto")
st.write("Ayanne")
st.write("Ayrton")
st.write("Carlos")
st.write("Petronio")