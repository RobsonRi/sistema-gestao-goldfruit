# preco_frete.py

class PrecoFrete:
    """Representa uma linha da tabela de preços, contendo os valores para uma localidade."""

    def __init__(self, localidade_id, valor_truck=0.0, valor_toco=0.0, valor_3_4=0.0, id=None):
        self.id = id
        self.localidade_id = localidade_id
        self.valor_truck = float(valor_truck)
        self.valor_toco = float(valor_toco)
        self.valor_3_4 = float(valor_3_4)

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        # Note que o id da localidade é a chave principal da lógica, não o id da linha.
        return {
            "localidade_id": self.localidade_id,
            "valor_truck": self.valor_truck,
            "valor_toco": self.valor_toco,
            "valor_3_4": self.valor_3_4
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de PrecoFrete a partir de um dicionário."""
        return cls(
            id=data_dict.get("id"),
            localidade_id=data_dict.get("localidade_id"),
            valor_truck=data_dict.get("valor_truck", 0.0),
            valor_toco=data_dict.get("valor_toco", 0.0),
            valor_3_4=data_dict.get("valor_3_4", 0.0)
        )

    def __str__(self):
        """Representação em string do objeto."""
        return f"PrecoFrete(ID: {self.id}, Localidade ID: {self.localidade_id})"