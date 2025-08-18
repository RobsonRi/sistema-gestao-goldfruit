import sqlite3




class DatabaseManager:
    def __init__(self, db_name='dados.db'):
        """
        Inicializa o gerenciador do banco de dados e cria as tabelas se elas não existirem.
        """
        print("\n\n--- ALERTA: O DatabaseManager ANTIGO (SQLite) FOI INICIADO! ---\n\n")
        self.conn = sqlite3.connect(db_name)
        self.db_name = db_name
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    # --- GERENCIAMENTO DO ESQUEMA DO BANCO DE DADOS ---
    def _create_tables(self):
        """
        Cria todas as tabelas necessárias no banco de dados, organizadas por módulo.
        """
        # --- Módulo Principal (Gestão e Frota) ---
        self.cursor.execute('''
                             CREATE TABLE IF NOT EXISTS pessoas 
                             (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                nome TEXT NOT NULL,
                                funcao TEXT NOT NULL,
                                cpf TEXT,
                                data_nascimento TEXT,
                                telefone TEXT,
                                email TEXT,
                                cnh TEXT,
                                categoria_cnh TEXT,
                                is_motorista INTEGER DEFAULT 0
                            )
                            ''')
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS veiculos
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                placa
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                marca
                                TEXT,
                                modelo
                                TEXT,
                                cor
                                TEXT,
                                ano
                                INTEGER,
                                tipo_combustivel
                                TEXT,
                                km_atual
                                REAL,

                                -- NOVAS COLUNAS --
                                tipo_propriedade
                                TEXT
                                NOT
                                NULL
                                DEFAULT
                                'PROPRIO',
                                transportadora_id
                                INTEGER,
                                FOREIGN
                                KEY
                            (
                                transportadora_id
                            ) REFERENCES transportadoras
                            (
                                id
                            )
                                )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS centros_custo
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                nome
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                descricao
                                TEXT
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS abastecimentos
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                data_hora
                                TEXT
                                NOT
                                NULL,
                                motorista_id
                                INTEGER
                                NOT
                                NULL,
                                veiculo_id
                                INTEGER
                                NOT
                                NULL,
                                centro_custo_id
                                INTEGER
                                NOT
                                NULL,
                                posto_id
                                INTEGER
                                NOT
                                NULL, -- <-- NOVA COLUNA
                                numero_cupom
                                TEXT
                                NOT
                                NULL,
                                descricao_cupom
                                TEXT,
                                tipo_combustivel
                                TEXT
                                NOT
                                NULL,
                                quantidade_litros
                                REAL
                                NOT
                                NULL,
                                valor_unitario
                                REAL
                                NOT
                                NULL,
                                valor_total
                                REAL
                                NOT
                                NULL,
                                outros_gastos_descricao
                                TEXT,
                                outros_gastos_valor
                                REAL,
                                FOREIGN
                                KEY
                            (
                                motorista_id
                            ) REFERENCES pessoas
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                veiculo_id
                            ) REFERENCES veiculos
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                centro_custo_id
                            ) REFERENCES centros_custo
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                posto_id
                            ) REFERENCES postos_combustivel
                            (
                                id
                            ) 
                                )
                            ''')

        # --- Módulo de Estoque ---
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS produtos
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                nome
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                descricao
                                TEXT,
                                quantidade_estoque
                                INTEGER
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS movimentacoes_estoque
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                tipo
                                TEXT
                                NOT
                                NULL,
                                produto_id
                                INTEGER
                                NOT
                                NULL,
                                quantidade
                                INTEGER
                                NOT
                                NULL,
                                data_hora
                                TEXT
                                NOT
                                NULL,
                                pessoa_id
                                INTEGER,
                                observacao
                                TEXT,
                                FOREIGN
                                KEY
                            (
                                produto_id
                            ) REFERENCES produtos
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                pessoa_id
                            ) REFERENCES pessoas
                            (
                                id
                            )
                                )
                            ''')

        # --- Módulo de Fretes ---
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS transportadoras
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                nome
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                telefone
                                TEXT,
                                contato
                                TEXT
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS localidades
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                nome
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                cidade
                                TEXT,
                                estado
                                TEXT
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS tabela_precos_frete
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                localidade_id
                                INTEGER
                                NOT
                                NULL
                                UNIQUE,
                                valor_truck
                                REAL
                                DEFAULT
                                0,
                                valor_toco
                                REAL
                                DEFAULT
                                0,
                                valor_3_4
                                REAL
                                DEFAULT
                                0,
                                FOREIGN
                                KEY
                            (
                                localidade_id
                            ) REFERENCES localidades
                            (
                                id
                            )
                                )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS viagens
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                data_viagem
                                TEXT
                                NOT
                                NULL,
                                veiculo_id
                                INTEGER,
                                transportadora_id
                                INTEGER
                                NOT
                                NULL,
                                localidade_id
                                INTEGER
                                NOT
                                NULL,
                                tipo_caminhao
                                TEXT
                                NOT
                                NULL,
                                valor_base_frete
                                REAL
                                NOT
                                NULL, -- Renomeado de 'valor_cobrado'
                                bonus_percentual
                                REAL
                                NOT
                                NULL
                                DEFAULT
                                0,    -- NOVO CAMPO
                                motorista_nome
                                TEXT,
                                FOREIGN
                                KEY
                            (
                                veiculo_id
                            ) REFERENCES veiculos
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                transportadora_id
                            ) REFERENCES transportadoras
                            (
                                id
                            ),
                                FOREIGN KEY
                            (
                                localidade_id
                            ) REFERENCES localidades
                            (
                                id
                            )
                                )
                            ''')

        # --- Módulo de Configurações ---
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS parametros_co2
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                tipo_combustivel
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                fator_emissao
                                REAL
                                NOT
                                NULL
                            )
                            ''')
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS postos_combustivel
                            (
                                id
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                nome
                                TEXT
                                NOT
                                NULL
                                UNIQUE,
                                cidade
                                TEXT,
                                estado
                                TEXT
                            )
                            ''')


        self.conn.commit()

    # --- MÉTODOS DE CRUD GENÉRICOS ---
    def insert(self, table, data):
        """Insere um novo registro e retorna o ID."""
        if 'id' in data and data.get('id') is None:
            del data['id']
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        try:
            self.cursor.execute(query, list(data.values()))
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Erro ao inserir registro: {e}")
            raise

    def fetch_all(self, table):
        """Busca todos os registros de uma tabela."""
        self.cursor.execute(f'SELECT * FROM {table}')
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update(self, table_name, record_id, data):
        """Atualiza um registro com base no ID."""
        if not data: return
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        values = list(data.values())
        values.append(record_id)
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        try:
            self.cursor.execute(query, tuple(values))
        except sqlite3.Error as e:
            print(f"Erro ao atualizar o registro: {e}")
            raise

    def delete(self, table_name, record_id):
        """Exclui um registro com base no seu ID."""
        query = f"DELETE FROM {table_name} WHERE id = ?"
        try:
            self.cursor.execute(query, (record_id,))
        except sqlite3.Error as e:
            print(f"Erro ao excluir registro: {e}")
            raise

    # --- MÉTODOS DE CONSULTA ESPECIALIZADOS ---
    def fetch_abastecimentos_com_detalhes(self, data_inicio_str, data_fim_str):
        """Busca abastecimentos e já calcula o Custo Total da Nota."""
        query = """
                SELECT ab.id, \
                       ab.data_hora, \
                       p.nome                                               AS motorista_nome, \
                       v.placa || ' (' || v.marca || ' ' || v.modelo || ')' AS veiculo_info, \
                       cc.nome                                              AS centro_custo_nome, \
                       ab.tipo_combustivel, \
                       ab.quantidade_litros, \
                       ab.valor_unitario, \
                       ab.valor_total, \
                       ab.outros_gastos_valor, \
                       ab.outros_gastos_descricao, \
                       (ab.valor_total + IFNULL(ab.outros_gastos_valor, 0)) AS custo_total_nota
                FROM abastecimentos AS ab
                         LEFT JOIN pessoas AS p ON ab.motorista_id = p.id
                         LEFT JOIN veiculos AS v ON ab.veiculo_id = v.id
                         LEFT JOIN centros_custo AS cc ON ab.centro_custo_id = cc.id
                WHERE date (ab.data_hora) BETWEEN date (?) AND date (?)
                ORDER BY ab.data_hora DESC; \
                """
        try:
            self.cursor.execute(query, (data_inicio_str, data_fim_str))
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro ao buscar relatório de abastecimentos: {e}")
            return []

    def fetch_precos_frete_com_detalhes(self):
        """Busca a tabela de preços juntando o nome da localidade."""
        query = """
                SELECT p.id, \
                       l.nome AS localidade_nome, \
                       p.valor_truck, \
                       p.valor_toco, \
                       p.valor_3_4
                FROM tabela_precos_frete AS p \
                         JOIN \
                     localidades AS l ON p.localidade_id = l.id
                ORDER BY l.nome; \
                """
        try:
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro ao buscar tabela de preços de frete: {e}")
            return []

    def fetch_viagens_com_detalhes(self, data_inicio_str, data_fim_str):
        """
        Busca as viagens dentro de um período, juntando os nomes da transportadora,
        localidade e informações do veículo.
        """
        query = """
                SELECT vi.id,
                       vi.data_viagem, \
                       t.nome                                              AS transportadora_nome, \
                       l.nome                                              AS localidade_nome, \
                       vi.tipo_caminhao, \
                       vi.valor_cobrado, \
                       vi.motorista_nome, \
                       IFNULL(ve.placa || ' (' || ve.modelo || ')', 'N/A') AS veiculo_info
                FROM viagens AS vi \
                         JOIN transportadoras AS t ON vi.transportadora_id = t.id \
                         JOIN localidades AS l ON vi.localidade_id = l.id \
                         LEFT JOIN veiculos AS ve ON vi.veiculo_id = ve.id -- LEFT JOIN pois veiculo é opcional
                WHERE vi.data_viagem BETWEEN ? AND ?
                ORDER BY vi.data_viagem DESC; \
                """
        try:
            self.cursor.execute(query, (data_inicio_str, data_fim_str))
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro ao buscar relatório de viagens: {e}")
            return []

    def fetch_resumo_fretes_por_transportadora(self, data_inicio_str, data_fim_str):
        """
        Busca e agrupa as viagens por transportadora, somando os valores
        e contando o número de viagens dentro de um período.
        """
        query = """
                SELECT t.nome                AS transportadora_nome, \
                       COUNT(vi.id)          AS numero_viagens, \
                       SUM(vi.valor_cobrado) AS valor_total
                FROM viagens AS vi \
                         JOIN \
                     transportadoras AS t ON vi.transportadora_id = t.id
                WHERE vi.data_viagem BETWEEN ? AND ?
                GROUP BY t.nome
                ORDER BY valor_total DESC; \
                """
        try:
            self.cursor.execute(query, (data_inicio_str, data_fim_str))
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Erro ao buscar resumo de fretes: {e}")
            return []

    def fetch_viagens_com_detalhes(self, data_inicio_str, data_fim_str):
        """
        Busca as viagens e todos os seus detalhes, incluindo valor base e bônus.
        """
        query = """
                SELECT vi.id, \
                       vi.data_viagem, \
                       t.nome                                              AS transportadora_nome, \
                       l.nome                                              AS localidade_nome, \
                       vi.tipo_caminhao, \
                       vi.valor_base_frete, \
                       vi.bonus_percentual, \
                       vi.motorista_nome, \
                       IFNULL(ve.placa || ' (' || ve.modelo || ')', 'N/A') AS veiculo_info
                FROM viagens AS vi \
                         JOIN transportadoras AS t ON vi.transportadora_id = t.id \
                         JOIN localidades AS l ON vi.localidade_id = l.id \
                         LEFT JOIN veiculos AS ve ON vi.veiculo_id = ve.id
                WHERE vi.data_viagem BETWEEN ? AND ?
                ORDER BY vi.data_viagem DESC; \
                """
        try:
            self.cursor.execute(query, (data_inicio_str, data_fim_str))
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            # Esta é a mensagem que você estava vendo
            print(f"Erro ao buscar relatório de viagens: {e}")
            return []

    # --- GERENCIAMENTO DA CONEXÃO E TRANSAÇÕES ---
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()

    def close_connection(self):
        """Fecha a conexão com o banco de dados."""
        self.conn.close()