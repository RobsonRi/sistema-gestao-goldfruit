# posto.py
class Posto:
    def __init__(self, nome, cidade="", estado="", id=None):
        self.id = id
        self.nome = nome
        self.cidade = cidade
        self.estado = estado

    def to_dict(self):
        return {"nome": self.nome, "cidade": self.cidade, "estado": self.estado}

    @classmethod
    def from_dict(cls, data_dict):
        return cls(id=data_dict.get("id"), nome=data_dict.get("nome"),
                   cidade=data_dict.get("cidade"), estado=data_dict.get("estado"))