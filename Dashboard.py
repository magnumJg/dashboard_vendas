import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import random
from faker import Faker

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Dicionário de regiões por UF
regioes_brasil = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}

def obter_regiao(uf):
    for regiao, ufs in regioes_brasil.items():
        if uf in ufs:
            return regiao
    return 'Indefinida'


st.title('DASHBOARD DE VENDAS :shopping_trolley:')
#st.set_page_config(layout = 'wide')

## Leitura
dados = pd.read_json('dataset_vendas_v2.json')
dados['Região'] = dados['Local de compra'].apply(obter_regiao)
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], errors='coerce', dayfirst=True)
dados = dados.dropna(subset=['Data da Compra'])

## Filtros
### Filtro por região
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''
else:
    dados = dados[dados['Região'] == regiao]

### Filtro por ano
todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2025)
    dados = dados[dados['Data da Compra'].dt.year == ano]

### Filtro por vendedor
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas
### Tabelas de receitas
receita_estados = dados.groupby('Local de compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset = 'Local de compra')[['Local de compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local de compra', right_index = True).sort_values('Preço', ascending = False)

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

### Tabelas de quantidade de vendas
quantidade_estados = dados.groupby('Local de compra').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending = False)
localizacao = dados.drop_duplicates(subset = 'Local de compra')[['Local de compra', 'lat', 'lon']]
quantidade_estados = quantidade_estados.merge(localizacao, on = 'Local de compra')

quantidade_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M')).size().reset_index(name='Quantidade')
quantidade_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
quantidade_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

quantidade_categorias = dados.groupby('Categoria do Produto').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False)

### Tabelas de vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))


## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                   lat = 'lat',
                                   lon = 'lon',
                                   scope = 'south america',
                                   size = 'Preço',
                                   template = 'seaborn',
                                   hover_name = 'Local de compra',
                                   hover_data = {'lat':False,'lon':False},
                                   title = 'Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                                   x = 'Mes',
                                   y = 'Preço',
                                   markers = True,
                                   range_y = (0, receita_mensal.max()),
                                   color='Ano',
                                   line_dash = 'Ano',
                                   title = 'Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local de compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias.head(),
                                text_auto = True,
                                title = 'Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title = 'Receita')

##DESAFIO
fig_mapa_quantidade = px.scatter_geo(quantidade_estados,
                                   lat = 'lat',
                                   lon = 'lon',
                                   scope = 'south america',
                                   size = 'Quantidade',
                                   template = 'seaborn',
                                   hover_name = 'Local de compra',
                                   hover_data = {'lat':False,'lon':False},
                                   title = 'Quantidade por Estado') 

fig_quantidade_mensal = px.line(quantidade_mensal,
                                   x = 'Mes',
                                   y = 'Quantidade',
                                   markers = True,
                                   range_y = (0, receita_mensal.max()),
                                   color='Ano',
                                   line_dash = 'Ano',
                                   title = 'Quantidade mensal')

fig_quantidade_estados = px.bar(quantidade_estados.head(),
                             x = 'Local de compra',
                             y = 'Quantidade',
                             text_auto = True,
                             title = 'Top estados (quantidade)')
fig_quantidade_estados.update_layout(yaxis_title = 'Quantidade')

fig_quantidade_categorias = px.bar(quantidade_categorias.head(),
                                   x = 'Categoria do Produto',
                                   y = 'Quantidade',
                                   text_auto = True,
                                   title = 'Quantidade de vendas por categoria')
fig_quantidade_categorias.update_layout(yaxis_title = 'Quantidade')

## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])
with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_quantidade, use_container_width=True)
        st.plotly_chart(fig_quantidade_estados, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_quantidade_mensal, use_container_width = True)
        st.plotly_chart(fig_quantidade_categorias, use_container_width = True)
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)


#st.dataframe(quantidade_mensal)
#st.dataframe(receita_mensal)
st.dataframe(quantidade_categorias)
st.write(quantidade_categorias.dtypes)

st.write(dados.dtypes)

st.write('Printando ano do produto inicio')
st.write(ano)
st.write('Printando ano do produto fim')
st.dataframe(dados)