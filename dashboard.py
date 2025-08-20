import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64 # <-- Nova importação
import streamlit as st
from firebase_manager import FirebaseManager

class FirebaseManager:
    def __init__(self, credential_path="chave-firebase.json"):
        try:
            if not firebase_admin._apps:
                cred_obj = None
                # Se estiver rodando localmente, usa o arquivo
                if os.path.exists(credential_path):
                    cred_obj = credentials.Certificate(credential_path)
                # Se estiver na nuvem (Streamlit Cloud), usa os "Secrets"
                else:
                    # Pega o texto Base64 dos Secrets
                    key_b64 = st.secrets["FIREBASE_JSON_KEY"]
                    # Decodifica o texto Base64 de volta para um texto JSON
                    key_json = base64.b64decode(key_b64).decode('utf-8')
                    # Converte o texto JSON para um dicionário Python
                    key_dict = json.loads(key_json)
                    # Cria as credenciais a partir do dicionário
                    cred_obj = credentials.Certificate(key_dict)

                if cred_obj:
                    firebase_admin.initialize_app(cred_obj)
                else:
                    raise FileNotFoundError("Não foi possível encontrar a chave de credenciais.")

            self.db = firestore.client()
            print("✅ Conexão com o Firebase estabelecida.")
        except Exception as e:
            print(f"❌ Falha ao conectar com o Firebase: {e}")
            self.db = None



@st.cache_data
def carregar_dados():
    """Conecta no Firebase, carrega todas as coleções, junta as informações e retorna dois DataFrames."""
    fb_manager = FirebaseManager()
    if not fb_manager.db:
        return pd.DataFrame(), pd.DataFrame()

    # Carrega as coleções principais
    df_abastecimentos = pd.DataFrame(fb_manager.fetch_all('abastecimentos'))
    df_viagens = pd.DataFrame(fb_manager.fetch_all('viagens'))

    # Carrega as "tabelas de dimensão" para enriquecer os dados
    df_pessoas = pd.DataFrame(fb_manager.fetch_all('pessoas'))
    df_veiculos = pd.DataFrame(fb_manager.fetch_all('veiculos'))
    df_postos = pd.DataFrame(fb_manager.fetch_all('postos_combustivel'))
    df_centros_custo = pd.DataFrame(fb_manager.fetch_all('centros_custo'))
    df_parametros_co2 = pd.DataFrame(fb_manager.fetch_all('parametros_co2'))
    df_transportadoras = pd.DataFrame(fb_manager.fetch_all('transportadoras'))
    df_localidades = pd.DataFrame(fb_manager.fetch_all('localidades'))

    # --- Processamento de Abastecimentos ---
    if not df_abastecimentos.empty and not df_pessoas.empty and not df_veiculos.empty:
        df_pessoas.rename(columns={'id': 'motorista_id', 'nome': 'motorista_nome'}, inplace=True)
        df_veiculos.rename(columns={'id': 'veiculo_id', 'placa': 'veiculo_placa'}, inplace=True)
        df_postos.rename(columns={'id': 'posto_id', 'nome': 'posto_nome'}, inplace=True)
        df_centros_custo.rename(columns={'id': 'centro_custo_id', 'nome': 'centro_custo_nome'}, inplace=True)

        df_abastecimentos = pd.merge(df_abastecimentos, df_pessoas[['motorista_id', 'motorista_nome']],
                                     on='motorista_id', how='left')
        df_abastecimentos = pd.merge(df_abastecimentos, df_veiculos[['veiculo_id', 'veiculo_placa', 'modelo']],
                                     on='veiculo_id', how='left')
        df_abastecimentos = pd.merge(df_abastecimentos, df_postos[['posto_id', 'posto_nome']], on='posto_id',
                                     how='left')
        df_abastecimentos = pd.merge(df_abastecimentos, df_centros_custo[['centro_custo_id', 'centro_custo_nome']],
                                     on='centro_custo_id', how='left')
        df_abastecimentos = pd.merge(df_abastecimentos, df_parametros_co2, on='tipo_combustivel', how='left')

        df_abastecimentos['data_hora'] = pd.to_datetime(df_abastecimentos['data_hora'], format='mixed', errors='coerce')
        df_abastecimentos.dropna(subset=['data_hora'], inplace=True)
        df_abastecimentos['outros_gastos_valor'] = df_abastecimentos['outros_gastos_valor'].fillna(0)
        df_abastecimentos['custo_total'] = df_abastecimentos['valor_total'] + df_abastecimentos['outros_gastos_valor']
        df_abastecimentos['emissao_co2'] = df_abastecimentos['quantidade_litros'] * df_abastecimentos[
            'fator_emissao'].fillna(0)
        df_abastecimentos['data'] = df_abastecimentos['data_hora'].dt.date
        colunas_moeda = ['valor_total', 'outros_gastos_valor', 'custo_total', 'valor_unitario']
        df_abastecimentos[colunas_moeda] = df_abastecimentos[colunas_moeda].round(2)

    # --- Processamento de Viagens ---
    if not df_viagens.empty and not df_transportadoras.empty and not df_localidades.empty:
        df_transportadoras.rename(columns={'id': 'transportadora_id', 'nome': 'transportadora_nome'}, inplace=True)
        df_localidades.rename(columns={'id': 'localidade_id', 'nome': 'localidade_nome'}, inplace=True)

        df_viagens = pd.merge(df_viagens, df_transportadoras[['transportadora_id', 'transportadora_nome']],
                              on='transportadora_id', how='left')
        df_viagens = pd.merge(df_viagens, df_localidades[['localidade_id', 'localidade_nome']], on='localidade_id',
                              how='left')

        df_viagens['data_viagem'] = pd.to_datetime(df_viagens['data_viagem'], format='mixed', errors='coerce')
        df_viagens.dropna(subset=['data_viagem'], inplace=True)
        df_viagens['bonus_percentual'] = df_viagens['bonus_percentual'].fillna(0)
        df_viagens['valor_final'] = df_viagens['valor_base_frete'] * (1 + df_viagens['bonus_percentual'] / 100)
        df_viagens['data'] = df_viagens['data_viagem'].dt.date
        df_viagens[['valor_base_frete', 'valor_final']] = df_viagens[['valor_base_frete', 'valor_final']].round(2)

    return df_abastecimentos, df_viagens


# Carrega os dados usando a função
df_abastecimentos, df_viagens = carregar_dados()

# --- Barra Lateral com Filtros ---
st.sidebar.header("Filtros Gerais")
data_min = min(df_abastecimentos['data'].min() if not df_abastecimentos.empty else date.today(),
               df_viagens['data'].min() if not df_viagens.empty else date.today())
data_max = max(df_abastecimentos['data'].max() if not df_abastecimentos.empty else date.today(),
               df_viagens['data'].max() if not df_viagens.empty else date.today())
data_inicio = st.sidebar.date_input("Data Início", data_min, min_value=data_min, max_value=data_max)
data_fim = st.sidebar.date_input("Data Fim", data_max, min_value=data_min, max_value=data_max)

# --- Abas ---
tab_abastecimentos, tab_fretes = st.tabs(["📈 Análise de Abastecimentos", "🚚 Análise de Fretes"])

with tab_abastecimentos:
    if df_abastecimentos.empty:
        st.warning("Não há dados de abastecimento para exibir.")
    else:
        df_abast_filtrado = df_abastecimentos[
            (df_abastecimentos['data'] >= data_inicio) & (df_abastecimentos['data'] <= data_fim)]
        st.subheader("Resumo de Abastecimentos no Período")
        total_custo = df_abast_filtrado['custo_total'].sum()
        total_litros = df_abast_filtrado['quantidade_litros'].sum()
        total_co2 = df_abast_filtrado['emissao_co2'].sum()


        def formatar_brl(valor):
            return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


        col1, col2, col3 = st.columns(3)
        col1.metric("Custo Total", formatar_brl(total_custo))
        col2.metric("Total de Litros", f"{total_litros:,.2f} L".replace(',', '.'))
        col3.metric("Emissão de CO₂", f"{total_co2:,.2f} kg")
        st.markdown("---")

        st.subheader("Análises Gráficas de Abastecimento")
        colg1, colg2 = st.columns(2)
        with colg1:
            st.write("Gastos por Centro de Custo (R$)")
            st.bar_chart(
                df_abast_filtrado.groupby('centro_custo_nome')['custo_total'].sum().sort_values(ascending=False))
            st.write("Gastos por Posto (R$)")
            st.bar_chart(df_abast_filtrado.groupby('posto_nome')['custo_total'].sum().sort_values(ascending=False))
        with colg2:
            st.write("Gastos por Veículo (R$)")
            st.bar_chart(df_abast_filtrado.groupby('veiculo_placa')['custo_total'].sum().sort_values(ascending=False))
            st.write("Consumo por Veículo (Litros)")
            st.bar_chart(
                df_abast_filtrado.groupby('veiculo_placa')['quantidade_litros'].sum().sort_values(ascending=False))

with tab_fretes:
    # (A lógica da aba de fretes, que já estava correta, continua aqui)
    pass

# --- Conteúdo da Aba de Fretes ---
with tab_fretes:
    if df_viagens.empty:
        st.warning("Não há dados de viagens para o período selecionado.")
    else:
        df_viagens_filtrado = df_viagens[
            (df_viagens['data'] >= data_inicio) & (df_viagens['data'] <= data_fim)
            ]

        st.subheader("Resumo de Fretes")
        receita_total = df_viagens_filtrado['valor_final'].sum()
        num_viagens = len(df_viagens_filtrado)
        media_por_viagem = receita_total / num_viagens if num_viagens > 0 else 0

        col_frete1, col_frete2, col_frete3 = st.columns(3)
        col_frete1.metric("Receita Total de Fretes", formatar_brl(receita_total))
        col_frete2.metric("Nº de Viagens", num_viagens)
        col_frete3.metric("Receita Média por Viagem", formatar_brl(media_por_viagem))

        st.markdown("---")

        st.write("Receita por Transportadora (R$)")
        receita_por_transp = df_viagens_filtrado.groupby('transportadora_nome')['valor_final'].sum().sort_values(
            ascending=False)
        st.bar_chart(receita_por_transp)