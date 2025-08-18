from datetime import datetime

class Produto:
    # A linha '_id_counter = 0' foi REMOVIDA.

    def __init__(self, nome, descricao="", quantidade_estoque=0, id=None):
        # A ordem dos parâmetros foi ajustada para melhor clareza e o id opcional ficou por último.
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.quantidade_estoque = int(quantidade_estoque)
        # O atributo 'data_criacao' foi REMOVIDO pois não era persistido no banco.

    def adicionar_estoque(self, quantidade):
        """Adiciona uma quantidade ao estoque do produto."""

        quantidade_add = int(quantidade)
        if quantidade_add > 0:
            self.quantidade_estoque += quantidade_add
            return True
        # Vamos levantar um erro aqui também para manter o padrão
        raise ValueError("Quantidade para adicionar deve ser maior que zero.")

    def remover_estoque(self, quantidade):
        """Remove uma quantidade do estoque, levantando um erro se indisponível."""

        quantidade_remover = int(quantidade)
        if quantidade_remover <= 0:
            raise ValueError("Quantidade para remover deve ser maior que zero.")

        if self.quantidade_estoque >= quantidade_remover:
            self.quantidade_estoque -= quantidade_remover
        else:
            raise ValueError(f"Estoque insuficiente de {self.nome}. Disponível: {self.quantidade_estoque}")

    def to_dict(self):
        """Converte o objeto para um dicionário APENAS com os dados a serem salvos."""

        return {
            "nome": self.nome,
            "descricao": self.descricao,
            "quantidade_estoque": self.quantidade_estoque
        }

    @classmethod
    def from_dict(cls, data_dict):
        """Cria uma instância de Produto a partir de um dicionário."""

        return cls(
            id=data_dict.get("id"),
            nome=data_dict.get("nome"), # Usar .get() aqui também é mais seguro
            descricao=data_dict.get("descricao"),
            quantidade_estoque=data_dict.get("quantidade_estoque", 0)
        )

    def __str__(self):
        """Representação em string do objeto Produto, útil para depuração."""

        return f"Produto(ID: {self.id}, Nome: {self.nome}, Estoque: {self.quantidade_estoque})"