import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import streamlit as st

class FirebaseManager:
    def __init__(self, credential_path="chave-firebase.json"):
        try:
            if not firebase_admin._apps:
                cred_obj = None
                if os.path.exists(credential_path):
                    cred_obj = credentials.Certificate(credential_path)
                else:
                    key_str = st.secrets["FIREBASE_JSON_KEY"]
                    key_dict = json.loads(key_str)
                    cred_obj = credentials.Certificate(key_dict)
                if cred_obj:
                    firebase_admin.initialize_app(cred_obj)
                else:
                    raise FileNotFoundError("Não foi possível encontrar a chave de credenciais.")
            self.db = firestore.client()
        except Exception as e:
            st.error(f"❌ Falha crítica ao conectar com o Firebase: {e}")
            self.db = None

    def fetch_all(self, collection_name):
        if not self.db: return []
        try:
            docs = self.db.collection(collection_name).stream()
            data_list = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                data_list.append(data)
            # A CORREÇÃO ESTÁ AQUI: O 'return' está fora do loop 'for'
            return data_list
        except Exception as e:
            print(f"Erro ao buscar todos os docs em '{collection_name}': {e}")
            return []


    def insert(self, collection_name, data):
        """Insere um novo documento em uma coleção."""
        if not self.db: return None
        try:
            # Firestore não gosta de 'id' nos dados de inserção
            if 'id' in data:
                del data['id']
            update_time, doc_ref = self.db.collection(collection_name).add(data)
            return doc_ref.id
        except Exception as e:
            print(f"Erro ao inserir em '{collection_name}': {e}")
            raise

    def update(self, collection_name, doc_id, data):
        """Atualiza um documento existente."""
        if not self.db: return
        try:
            # Firestore não gosta de 'id' nos dados de atualização
            if 'id' in data:
                del data['id']
            self.db.collection(collection_name).document(doc_id).update(data)
        except Exception as e:
            print(f"Erro ao atualizar em '{collection_name}': {e}")
            raise

    def delete(self, collection_name, doc_id):
        """Exclui um documento."""
        if not self.db: return
        try:
            self.db.collection(collection_name).document(doc_id).delete()
        except Exception as e:
            print(f"Erro ao excluir em '{collection_name}': {e}")
            raise

    def fetch_precos_frete_com_detalhes(self):
        """
        Busca a tabela de preços e "junta" o nome da localidade.
        Esta é a versão Firestore do nosso antigo JOIN.
        """
        if not self.db: return []

        try:
            # Passo 1: Buscar todas as localidades e criar um dicionário de busca (ID -> Nome)
            localidades_docs = self.db.collection('localidades').stream()
            localidades_lookup = {doc.id: doc.to_dict().get('nome', 'N/A') for doc in localidades_docs}

            # Passo 2: Buscar todos os preços
            precos_docs = self.db.collection('tabela_precos_frete').stream()

            # Passo 3: Juntar os dados em Python
            dados_completos = []
            for preco_doc in precos_docs:
                preco_data = preco_doc.to_dict()
                localidade_id = preco_data.get('localidade_id')

                # Monta o dicionário de resultado com o nome da localidade
                resultado = {
                    'id': preco_doc.id,
                    'localidade_nome': localidades_lookup.get(localidade_id, "LOCALIDADE NÃO ENCONTRADA"),
                    'valor_truck': preco_data.get('valor_truck', 0.0),
                    'valor_toco': preco_data.get('valor_toco', 0.0),
                    'valor_3_4': preco_data.get('valor_3_4', 0.0)
                }
                dados_completos.append(resultado)

            return dados_completos
        except Exception as e:
            print(f"Erro ao buscar detalhes de preços de frete: {e}")
            return []

    def fetch_viagens_com_detalhes(self, data_inicio_str, data_fim_str):
        """
        Busca as viagens e "junta" os nomes da transportadora, localidade e veículo.
        """
        if not self.db: return []

        try:
            # Passo 1: Preparar os dicionários de busca
            transportadoras_docs = self.db.collection('transportadoras').stream()
            transportadoras_lookup = {doc.id: doc.to_dict().get('nome', 'N/A') for doc in transportadoras_docs}

            localidades_docs = self.db.collection('localidades').stream()
            localidades_lookup = {doc.id: doc.to_dict().get('nome', 'N/A') for doc in localidades_docs}

            veiculos_docs = self.db.collection('veiculos').stream()
            veiculos_lookup = {doc.id: f"{doc.to_dict().get('placa')} ({doc.to_dict().get('modelo')})" for doc in
                               veiculos_docs}

            # Passo 2: Buscar as viagens filtrando pela data
            viagens_ref = self.db.collection('viagens')
            query = viagens_ref.where(
                filter=firestore.FieldFilter('data_viagem', '>=', data_inicio_str)
            ).where(
                filter=firestore.FieldFilter('data_viagem', '<=', data_fim_str)
            )
            viagens_docs = query.stream()

            # Passo 3: Juntar tudo em Python
            dados_completos = []
            for doc in viagens_docs:
                viagem_data = doc.to_dict()

                # Monta o dicionário de resultado
                resultado = {
                    'id': doc.id,
                    'data_viagem': viagem_data.get('data_viagem'),
                    'transportadora_nome': transportadoras_lookup.get(viagem_data.get('transportadora_id'), "N/A"),
                    'localidade_nome': localidades_lookup.get(viagem_data.get('localidade_id'), "N/A"),
                    'tipo_caminhao': viagem_data.get('tipo_caminhao'),
                    # --- A CORREÇÃO ESTÁ AQUI ---
                    # A chave agora é 'valor_base_frete' para bater com o banco e a UI
                    'valor_base_frete': viagem_data.get('valor_base_frete'),
                    'bonus_percentual': viagem_data.get('bonus_percentual', 0),
                    'motorista_nome': viagem_data.get('motorista_nome'),
                    'veiculo_info': veiculos_lookup.get(viagem_data.get('veiculo_id'), 'N/A')
                }
                dados_completos.append(resultado)

            dados_completos.sort(key=lambda x: x['data_viagem'], reverse=True)

            return dados_completos
        except Exception as e:
            print(f"Erro ao buscar detalhes de viagens: {e}")
            return []

    def fetch_by_id(self, collection_name, doc_id):
        """
        Busca um único documento em uma coleção pelo seu ID.
        Retorna um dicionário com os dados ou None se não for encontrado.
        """
        if not self.db or not doc_id:
            return None
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id  # Adiciona o ID ao dicionário para consistência
                return data
            else:
                return None
        except Exception as e:
            print(f"Erro ao buscar documento por ID em '{collection_name}': {e}")
            return None

