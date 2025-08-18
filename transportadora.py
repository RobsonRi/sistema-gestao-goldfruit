# transportadora.py

class Transportadora:
    """Representa uma empresa ou pessoa que realiza fretes."""

    def __init__(self, nome, telefone="", contato="", id=None):
        self.id = id
        self.nome = nome
        self.telefone = telefone
        self.contato = contato

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        return {
            "nome": self.nome,
            "telefone": self.telefone,
            "contato": self.contato
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de Transportadora a partir de um dicionário."""
        return cls(
            id=data_dict.get("id"),
            nome=data_dict.get("nome"),
            telefone=data_dict.get("telefone"),
            contato=data_dict.get("contato")
        )

    def __str__(self):
        """Representação em string do objeto."""
        return f"Transportadora(ID: {self.id}, Nome: {self.nome})"