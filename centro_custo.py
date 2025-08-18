class CentroCusto:
    def __init__(self, nome, descricao=None, id=None):
        self.id = id
        self.nome = nome
        self.descricao = descricao

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        # O 'id' foi removido para manter o padrão.
        return {
            'nome': self.nome,
            'descricao': self.descricao,
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de CentroCusto a partir de um dicionário."""

        return cls(
            id=data_dict.get("id"),
            nome=data_dict.get("nome"),
            descricao=data_dict.get("descricao")
        )

    def __str__(self):
        return f"CentroCusto(ID: {self.id}, Nome: {self.nome})"