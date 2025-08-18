class Pessoa:
    # A importação 'uuid' foi removida.

    def __init__(self, nome, funcao, cpf=None, data_nascimento=None, telefone=None, email=None, cnh=None, categoria_cnh=None, id=None, is_motorista=0):
        self.id = id
        self.nome = nome
        self.funcao = funcao
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.telefone = telefone
        self.email = email
        self.cnh = cnh
        self.categoria_cnh = categoria_cnh
        self.is_motorista = is_motorista

    def to_dict(self):
        """Converte o objeto Pessoa para um dicionário com os dados a serem salvos."""
        # O 'id' foi removido para manter o padrão.
        return {
            "nome": self.nome,
            "funcao": self.funcao,
            "cpf": self.cpf,
            "data_nascimento": self.data_nascimento,
            "telefone": self.telefone,
            "email": self.email,
            "cnh": self.cnh,
            "categoria_cnh": self.categoria_cnh,
            'is_motorista': self.is_motorista
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de Pessoa a partir de um dicionário."""

        return cls(
            id=data_dict.get("id"),
            nome=data_dict.get("nome"),
            funcao=data_dict.get("funcao"),
            cpf=data_dict.get("cpf"),
            data_nascimento=data_dict.get("data_nascimento"),
            telefone=data_dict.get("telefone"),
            email=data_dict.get("email"),
            cnh=data_dict.get("cnh"),
            categoria_cnh=data_dict.get("categoria_cnh"),
            is_motorista=data_dict.get('is_motorista', 0)
        )

    def __str__(self):
        """Representação em string do objeto Pessoa."""
        return f"Pessoa(ID: {self.id}, Nome: {self.nome}, Função: {self.funcao})"