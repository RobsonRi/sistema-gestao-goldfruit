# abastecimento.py
from datetime import datetime

class Abastecimento:
    def __init__(self, data_hora=None, motorista_id=None, veiculo_id=None,
                 centro_custo_id=None, posto_id=None, numero_cupom="", descricao_cupom="",
                 tipo_combustivel="", quantidade_litros=0.0, valor_unitario=0.0,
                 valor_total=0.0, id=None,
                 outros_gastos_descricao="", outros_gastos_valor=0.0):
        self.id = id

        # Lógica de data robusta
        if isinstance(data_hora, str):
            try:
                self.data_hora = datetime.strptime(data_hora, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                try:
                    self.data_hora = datetime.strptime(data_hora, '%d/%m/%Y %H:%M')
                except ValueError:
                    try:
                        self.data_hora = datetime.fromisoformat(data_hora)
                    except ValueError:
                        self.data_hora = datetime.now()
        elif isinstance(data_hora, datetime):
            self.data_hora = data_hora
        else:
            self.data_hora = datetime.now()

        self.motorista_id = motorista_id
        self.veiculo_id = veiculo_id
        self.centro_custo_id = centro_custo_id
        self.posto_id = posto_id # Garante que o posto_id seja salvo
        self.numero_cupom = numero_cupom
        self.descricao_cupom = descricao_cupom
        self.tipo_combustivel = tipo_combustivel
        self.quantidade_litros = float(quantidade_litros)
        self.valor_unitario = float(valor_unitario)
        self.valor_total = float(valor_total)
        self.outros_gastos_descricao = outros_gastos_descricao
        self.outros_gastos_valor = float(outros_gastos_valor)

    def to_dict(self):
        """Converte o objeto para um dicionário, salvando a data no formato ISO."""
        return {
            'data_hora': self.data_hora.isoformat(),
            'motorista_id': self.motorista_id,
            'veiculo_id': self.veiculo_id,
            'centro_custo_id': self.centro_custo_id,
            'posto_id': self.posto_id,
            'numero_cupom': self.numero_cupom,
            'descricao_cupom': self.descricao_cupom,
            'tipo_combustivel': self.tipo_combustivel,
            'quantidade_litros': self.quantidade_litros,
            'valor_unitario': self.valor_unitario,
            'valor_total': self.valor_total,
            'outros_gastos_descricao': self.outros_gastos_descricao,
            'outros_gastos_valor': self.outros_gastos_valor
        }

    @classmethod
    def from_dict(cls, data):
        """Cria uma instância de Abastecimento a partir de um dicionário."""
        return cls(
            id=data.get('id'),
            data_hora=data.get('data_hora'),
            motorista_id=data.get('motorista_id'),
            veiculo_id=data.get('veiculo_id'),
            centro_custo_id=data.get('centro_custo_id'),
            posto_id=data.get('posto_id'),
            numero_cupom=data.get('numero_cupom', ''),
            descricao_cupom=data.get('descricao_cupom', ''),
            tipo_combustivel=data.get('tipo_combustivel', ''),
            quantidade_litros=data.get('quantidade_litros', 0.0),
            valor_unitario=data.get('valor_unitario', 0.0),
            valor_total=data.get('valor_total', 0.0),
            outros_gastos_descricao=data.get('outros_gastos_descricao', ""),
            outros_gastos_valor=data.get('outros_gastos_valor', 0.0)
        )