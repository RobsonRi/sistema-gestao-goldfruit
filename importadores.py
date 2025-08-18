# importadores.py

import csv
import sqlite3
from pessoa import Pessoa
from centro_custo import CentroCusto
from abastecimento import Abastecimento
from posto import Posto
from veiculo import Veiculo
from transportadora import Transportadora
from localidade import Localidade
from viagem import Viagem


# (No futuro, adicionaremos outros imports aqui, como Veiculo, Posto, etc.)

class ImportadorDeFuncionarios:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def executar(self):
        """Lê o arquivo CSV de funcionários e insere os dados no banco."""
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        is_motorista_val = int(row.get('is_motorista', 0))

                        pessoa_data = Pessoa(
                            nome=row.get('nome', '').strip().upper(),
                            funcao=row.get('funcao', '').strip().upper(),
                            cpf=row.get('cpf', '').strip(),
                            data_nascimento=row.get('data_nascimento', '').strip(),
                            telefone=row.get('telefone', '').strip(),
                            email=row.get('email', '').strip(),
                            cnh=row.get('cnh', '').strip().upper(),
                            categoria_cnh=row.get('categoria_cnh', '').strip().upper(),
                            is_motorista=is_motorista_val
                        )

                        if not pessoa_data.nome or not pessoa_data.funcao:
                            self.erros += 1
                            continue

                        # Usamos uma transação para a inserção
                        self.db_manager.insert('pessoas', pessoa_data.to_dict())
                        self.sucesso += 1
                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except (ValueError, TypeError, KeyError):
                        self.erros += 1

            # Retorna um dicionário com o resumo da operação
            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}

        except Exception as e:
            # Retorna um dicionário com uma mensagem de erro geral
            return {"erro_leitura": str(e)}


class ImportadorDeCentrosDeCusto:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def executar(self):
        """Lê o arquivo CSV de Centros de Custo e insere os dados no banco."""
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        nome_cc = row.get('nome', '').strip().upper()
                        if not nome_cc:
                            self.erros += 1
                            continue

                        cc_data = CentroCusto(
                            nome=nome_cc,
                            descricao=row.get('descricao', '').strip().upper()
                        )


                        self.db_manager.insert('centros_custo', cc_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    # --- MUDANÇA AQUI PARA CAPTURAR O ERRO DETALHADO ---
                    except Exception as e:
                        print(f"!!! Erro inesperado ao processar a linha: {row} -> O erro foi: {e}")
                        self.erros += 1

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}

        except Exception as e:
            return {"erro_leitura": str(e)}


# Em importadores.py

class ImportadorDeAbastecimentos:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def _preparar_lookups(self):
        """Cria dicionários de busca para conversão rápida de nomes para IDs."""
        self.motoristas_lookup = {p['nome'].upper().strip(): p['id'] for p in self.db_manager.fetch_all('pessoas') if
                                  p['is_motorista']}
        self.veiculos_lookup = {v['placa'].upper().strip(): v['id'] for v in self.db_manager.fetch_all('veiculos')}
        self.cc_lookup = {cc['nome'].upper().strip(): cc['id'] for cc in self.db_manager.fetch_all('centros_custo')}
        self.postos_lookup = {p['nome'].upper().strip(): p['id'] for p in
                              self.db_manager.fetch_all('postos_combustivel')}

    def executar(self):
        """Lê o arquivo CSV, valida, busca os IDs e insere os abastecimentos."""
        self._preparar_lookups()

        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                print("\n--- INICIANDO DEPURAÇÃO DA IMPORTAÇÃO DE ABASTECIMENTOS ---")

                for i, row in enumerate(csv_reader, 2):  # Começa na linha 2 por causa do cabeçalho
                    try:
                        # Busca os IDs
                        motorista_nome = row.get('motorista_nome', '').upper().strip()
                        veiculo_placa = row.get('veiculo_placa', '').upper().strip()
                        cc_nome = row.get('centro_custo_nome', '').upper().strip()
                        posto_nome = row.get('posto_nome', '').upper().strip()

                        motorista_id = self.motoristas_lookup.get(motorista_nome)
                        veiculo_id = self.veiculos_lookup.get(veiculo_placa)
                        cc_id = self.cc_lookup.get(cc_nome)
                        posto_id = self.postos_lookup.get(posto_nome)

                        # Validação com print de depuração
                        if not all([motorista_id, veiculo_id, cc_id, posto_id]):
                            print(f"[DEBUG] Erro na Linha {i}: Falha ao encontrar correspondência.")
                            if not motorista_id: print(f"  -> Motorista não encontrado: '{motorista_nome}'")
                            if not veiculo_id: print(f"  -> Veículo não encontrado: '{veiculo_placa}'")
                            if not cc_id: print(f"  -> Centro de Custo não encontrado: '{cc_nome}'")
                            if not posto_id: print(f"  -> Posto não encontrado: '{posto_nome}'")
                            self.erros += 1
                            continue

                        # Conversão de valores
                        qtd = float(str(row.get('quantidade_litros', 0)).replace(',', '.'))
                        val_unit = float(str(row.get('valor_unitario', 0)).replace(',', '.'))
                        outros_val = float(str(row.get('outros_gastos_valor', 0)).replace(',', '.'))

                        ab_data = Abastecimento(
                            data_hora=row.get('data_hora'), motorista_id=motorista_id,
                            veiculo_id=veiculo_id, centro_custo_id=cc_id, posto_id=posto_id,
                            numero_cupom=row.get('numero_cupom', '').strip(),
                            tipo_combustivel=row.get('tipo_combustivel', '').strip().upper(),
                            quantidade_litros=qtd, valor_unitario=val_unit,
                            valor_total=(qtd * val_unit),
                            outros_gastos_valor=outros_val,
                            outros_gastos_descricao=row.get('outros_gastos_descricao', '').strip().upper()
                        )

                        if not ab_data.numero_cupom:
                            print(f"[DEBUG] Erro na Linha {i}: Número do cupom está vazio.")
                            self.erros += 1
                            continue

                        self.db_manager.insert('abastecimentos', ab_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"[DEBUG] Erro na Linha {i}: Dados inválidos na linha. Erro: {e}")
                        self.erros += 1

                print("--- FIM DA DEPURAÇÃO ---")

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}
        except Exception as e:
            return {"erro_leitura": str(e)}


class ImportadorDePostos:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def executar(self):
        """Lê o arquivo CSV de postos e insere os dados no banco."""
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        nome_posto = row.get('nome', '').strip().upper()
                        if not nome_posto:
                            self.erros += 1
                            continue

                        posto_data = Posto(
                            nome=nome_posto,
                            cidade=row.get('cidade', '').strip().upper(),
                            estado=row.get('estado', '').strip().upper()
                        )

                        self.db_manager.insert('postos_combustivel', posto_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except Exception:
                        self.erros += 1

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}

        except Exception as e:
            return {"erro_leitura": str(e)}


class ImportadorDeVeiculos:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def _preparar_lookups(self):
        """Cria um dicionário de busca para converter nome de transportadora em ID."""
        self.transportadoras_lookup = {t['nome'].upper().strip(): t['id'] for t in
                                       self.db_manager.fetch_all('transportadoras')}

    def executar(self):
        """Lê o arquivo CSV de veículos e insere os dados no banco."""
        self._preparar_lookups()

        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        tipo_prop = row.get('tipo_propriedade', 'PROPRIO').strip().upper()
                        transportadora_id = None

                        if tipo_prop == 'TERCEIRO':
                            nome_transp = row.get('transportadora_nome', '').strip().upper()
                            if not nome_transp:
                                self.erros += 1
                                continue  # Pula se for de terceiro mas não tiver nome de transportadora

                            transportadora_id = self.transportadoras_lookup.get(nome_transp)
                            if not transportadora_id:
                                self.erros += 1  # Pula se a transportadora não for encontrada
                                continue

                        veiculo_data = Veiculo(
                            placa=row.get('placa', '').strip().upper(),
                            marca=row.get('marca', '').strip().upper(),
                            modelo=row.get('modelo', '').strip().upper(),
                            ano=int(row.get('ano', 0)),
                            cor=row.get('cor', '').strip().upper(),
                            tipo_combustivel=row.get('tipo_combustivel', '').strip().upper(),
                            km_atual=float(row.get('km_atual', 0.0)),
                            tipo_propriedade=tipo_prop,
                            transportadora_id=transportadora_id
                        )

                        if not veiculo_data.placa:
                            self.erros += 1
                            continue

                        self.db_manager.insert('veiculos', veiculo_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except (ValueError, TypeError, KeyError):
                        self.erros += 1

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}

        except Exception as e:
            return {"erro_leitura": str(e)}


class ImportadorDeTransportadoras:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def executar(self):
        """Lê o arquivo CSV de transportadoras e insere os dados no banco."""
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        nome_transp = row.get('nome', '').strip().upper()
                        if not nome_transp:
                            self.erros += 1
                            continue

                        transp_data = Transportadora(
                            nome=nome_transp,
                            telefone=row.get('telefone', '').strip(),
                            contato=row.get('contato', '').strip().upper()
                        )

                        self.db_manager.insert('transportadoras', transp_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except Exception:
                        self.erros += 1

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}

        except Exception as e:
            return {"erro_leitura": str(e)}


class ImportadorDeLocalidades:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso = 0
        self.erros = 0
        self.duplicados = 0

    def executar(self):
        """Lê o arquivo CSV de localidades e insere os dados no banco."""
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        nome_loc = row.get('nome', '').strip().upper()
                        if not nome_loc:
                            self.erros += 1
                            continue

                        loc_data = Localidade(
                            nome=nome_loc,
                            cidade=row.get('cidade', '').strip().upper(),
                            estado=row.get('estado', '').strip().upper()
                        )

                        with self.db_manager.conn:
                            self.db_manager.insert('localidades', loc_data.to_dict())
                        self.sucesso += 1

                    except sqlite3.IntegrityError:
                        self.duplicados += 1
                    except Exception:
                        self.erros += 1

            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}
        except Exception as e:
            return {"erro_leitura": str(e)}


class ImportadorDeViagens:
    def __init__(self, db_manager, filepath):
        self.db_manager = db_manager
        self.filepath = filepath
        self.sucesso, self.erros, self.duplicados = 0, 0, 0

    def _preparar_lookups(self):
        """Prepara todos os dicionários de busca necessários."""
        self.transportadoras = self.db_manager.fetch_all('transportadoras')
        self.localidades = self.db_manager.fetch_all('localidades')
        self.veiculos = [v for v in self.db_manager.fetch_all('veiculos') if v['tipo_propriedade'] == 'TERCEIRO']
        self.precos_lookup = {}
        precos_db = self.db_manager.fetch_all('tabela_precos_frete')
        for preco in precos_db:
            loc_id = preco['localidade_id']
            if loc_id not in self.precos_lookup: self.precos_lookup[loc_id] = {}
            self.precos_lookup[loc_id]['TRUCK'] = preco['valor_truck']
            self.precos_lookup[loc_id]['TOCO'] = preco['valor_toco']
            self.precos_lookup[loc_id]['3/4'] = preco['valor_3_4']

        self.transportadoras_lookup = {t['nome'].upper().strip(): t['id'] for t in self.transportadoras}
        self.localidades_lookup = {l['nome'].upper().strip(): l['id'] for l in self.localidades}
        self.veiculos_lookup = {v['placa'].upper().strip(): v['id'] for v in self.veiculos}

    def executar(self):
        """Lê o CSV, busca IDs e preços, e insere as viagens."""
        self._preparar_lookups()
        try:
            with open(self.filepath, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        transp_nome = row.get('transportadora_nome', '').upper().strip()
                        loc_nome = row.get('localidade_nome', '').upper().strip()
                        placa = row.get('veiculo_placa', '').upper().strip()
                        tipo_caminhao = row.get('tipo_caminhao', '').upper().strip()

                        transp_id = self.transportadoras_lookup.get(transp_nome)
                        loc_id = self.localidades_lookup.get(loc_nome)
                        veiculo_id = self.veiculos_lookup.get(placa)

                        if not all([transp_id, loc_id, veiculo_id, tipo_caminhao]):
                            self.erros += 1;
                            continue

                        valor_cobrado = self.precos_lookup.get(loc_id, {}).get(tipo_caminhao, 0.0)

                        viagem_data = Viagem(
                            data_viagem=datetime.strptime(row.get('data_viagem'), '%d/%m/%Y').strftime('%Y-%m-%d'),
                            transportadora_id=transp_id, localidade_id=loc_id, veiculo_id=veiculo_id,
                            tipo_caminhao=tipo_caminhao,
                            motorista_nome=row.get('motorista_nome', '').upper().strip(),
                            valor_cobrado=valor_cobrado
                        )

                        with self.db_manager.conn:
                            self.db_manager.insert('viagens', viagem_data.to_dict())
                        self.sucesso += 1
                    except Exception:
                        self.erros += 1
            return {"sucesso": self.sucesso, "erros": self.erros, "duplicados": self.duplicados}
        except Exception as e:
            return {"erro_leitura": str(e)}