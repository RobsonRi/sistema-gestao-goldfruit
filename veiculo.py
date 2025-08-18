# veiculo.py

class Veiculo:
    def __init__(self, marca, modelo, ano, placa, cor, tipo_combustivel,
                 km_atual=0, id=None, tipo_propriedade='PROPRIO', transportadora_id=None):
        self.id = id
        self.marca = marca
        self.modelo = modelo
        self.ano = int(ano)
        self.placa = placa.upper()
        self.cor = cor
        self.tipo_combustivel = tipo_combustivel
        self.km_atual = float(km_atual)
        # NOVOS ATRIBUTOS
        self.tipo_propriedade = tipo_propriedade
        self.transportadora_id = transportadora_id

    def registrar_nova_km(self, nova_km):
        if nova_km > self.km_atual:
            self.km_atual = nova_km
            return True
        else:
            raise ValueError(f"Erro: Nova quilometragem ({nova_km} km) deve ser maior que a atual ({self.km_atual} km).")

    def to_dict(self):
        """Converte o objeto para um dicionário com os dados a serem salvos."""
        return {
            'placa': self.placa,
            'marca': self.marca,
            'modelo': self.modelo,
            'ano': self.ano,
            'cor': self.cor,
            'tipo_combustivel': self.tipo_combustivel,
            'km_atual': self.km_atual,
            # NOVOS CAMPOS
            'tipo_propriedade': self.tipo_propriedade,
            'transportadora_id': self.transportadora_id
        }

    @classmethod
    def from_dict(cls, data):
        """Cria uma instância de Veiculo a partir de um dicionário."""
        return cls(
            id=data.get('id'),
            placa=data.get('placa', ''),
            marca=data.get('marca', ''),
            modelo=data.get('modelo', ''),
            ano=data.get('ano', 0),
            cor=data.get('cor', ''),
            tipo_combustivel=data.get('tipo_combustivel', ''),
            km_atual=data.get('km_atual', 0.0),
            # NOVOS CAMPOS
            tipo_propriedade=data.get('tipo_propriedade', 'PROPRIO'),
            transportadora_id=data.get('transportadora_id')
        )

    def __str__(self):
        """Representação em string do objeto Veiculo."""
        return f"Veiculo(ID: {self.id}, Placa: {self.placa}, Propriedade: {self.tipo_propriedade})"