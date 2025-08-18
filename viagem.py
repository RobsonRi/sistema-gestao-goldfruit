# viagem.py
from datetime import datetime


class Viagem:
    """Representa o registro de um frete (viagem) realizado com a nova estrutura de bônus."""

    def __init__(self, data_viagem, transportadora_id, localidade_id, tipo_caminhao, valor_base_frete,
                 bonus_percentual=0.0, veiculo_id=None, motorista_nome="", id=None):
        self.id = id

        if isinstance(data_viagem, str):
            self.data_viagem = datetime.strptime(data_viagem, '%Y-%m-%d').date()
        else:
            self.data_viagem = data_viagem

        self.transportadora_id = transportadora_id
        self.localidade_id = localidade_id
        self.tipo_caminhao = tipo_caminhao
        self.valor_base_frete = float(valor_base_frete)
        self.bonus_percentual = float(bonus_percentual)
        self.veiculo_id = veiculo_id
        self.motorista_nome = motorista_nome

    @property
    def valor_final(self):
        """Calcula e retorna o valor final do frete com o bônus. Isso é uma propriedade 'mágica'."""
        fator_bonus = 1 + (self.bonus_percentual / 100)
        return self.valor_base_frete * fator_bonus

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        return {
            "data_viagem": self.data_viagem.isoformat(),
            "transportadora_id": self.transportadora_id,
            "localidade_id": self.localidade_id,
            "tipo_caminhao": self.tipo_caminhao,
            "valor_base_frete": self.valor_base_frete,
            "bonus_percentual": self.bonus_percentual,
            "veiculo_id": self.veiculo_id,
            "motorista_nome": self.motorista_nome
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de Viagem a partir de um dicionário."""
        return cls(
            id=data_dict.get("id"),
            data_viagem=data_dict.get("data_viagem"),
            transportadora_id=data_dict.get("transportadora_id"),
            localidade_id=data_dict.get("localidade_id"),
            tipo_caminhao=data_dict.get("tipo_caminhao"),
            valor_base_frete=data_dict.get("valor_base_frete"),
            bonus_percentual=data_dict.get("bonus_percentual", 0.0),
            veiculo_id=data_dict.get("veiculo_id"),
            motorista_nome=data_dict.get("motorista_nome")
        )

    def __str__(self):
        return f"Viagem(ID: {self.id}, Data: {self.data_viagem}, Valor Final: {self.valor_final:.2f})"