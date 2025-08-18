# localidade.py

class Localidade:
    """Representa um destino de frete (cidade, fazenda, etc.)."""

    def __init__(self, nome, cidade="", estado="", id=None):
        self.id = id
        self.nome = nome
        self.cidade = cidade
        self.estado = estado

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        return {
            "nome": self.nome,
            "cidade": self.cidade,
            "estado": self.estado
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de Localidade a partir de um dicionário."""
        return cls(
            id=data_dict.get("id"),
            nome=data_dict.get("nome"),
            cidade=data_dict.get("cidade"),
            estado=data_dict.get("estado")
        )

    def __str__(self):
        """Representação em string do objeto."""
        return f"Localidade(ID: {self.id}, Nome: {self.nome})"