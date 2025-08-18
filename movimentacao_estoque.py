from datetime import datetime

class MovimentacaoEstoque:


    def __init__(self, tipo, produto_id, quantidade, data_hora=None, pessoa_id=None, observacao="", id=None):
        # A lógica complexa de ID foi substituída por esta linha simples.
        self.id = id

        self.tipo = tipo  # "entrada" ou "saida"
        self.produto_id = produto_id
        self.quantidade = quantidade
        self.data_hora = data_hora if data_hora is not None else datetime.now()
        self.pessoa_id = pessoa_id  # ID do funcionário que retirou
        self.observacao = observacao

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""

        return {
            "tipo": self.tipo,
            "produto_id": self.produto_id,
            "quantidade": self.quantidade,
            "data_hora": self.data_hora.isoformat(),  # Converte datetime para string ISO
            "pessoa_id": self.pessoa_id,
            "observacao": self.observacao
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de MovimentacaoEstoque a partir de um dicionário."""

        data_hora_str = data_dict.get("data_hora")
        data_hora_obj = datetime.fromisoformat(data_hora_str) if data_hora_str else None

        return cls(
            id=data_dict.get("id"),
            tipo=data_dict.get("tipo"), # Usar .get() é mais seguro que colchetes
            produto_id=data_dict.get("produto_id"),
            quantidade=data_dict.get("quantidade"),
            data_hora=data_hora_obj,
            pessoa_id=data_dict.get("pessoa_id"),
            observacao=data_dict.get("observacao", "")
        )

    def __str__(self):
        """Representação em string do objeto, útil para depuração."""

        return (f"Movimentacao(ID: {self.id}, Tipo: {self.tipo}, Produto ID: {self.produto_id}, "
                f"Qtd: {self.quantidade}, Data: {self.data_hora.strftime('%d/%m/%Y %H:%M')}, "
                f"Pessoa ID: {self.pessoa_id if self.pessoa_id else 'N/A'})")