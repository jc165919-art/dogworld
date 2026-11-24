from database import db


class Raca(db.Model):
    __tablename__ = "racas"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    porte = db.Column(db.String(40), nullable=False)
    temperamento = db.Column(db.String(120), nullable=False)
    vida_media = db.Column(db.String(30), nullable=False)
    # Termo correspondente à raça na TheDogAPI.
    dog_api_id = db.Column(db.String(80))

    def to_dict(self) -> dict:
        return {
            "slug": self.slug,
            "nome": self.nome,
            "descricao": self.descricao,
            "porte": self.porte,
            "temperamento": self.temperamento,
            "vida_media": self.vida_media,
        }


RACAS_INICIAIS = [
    {
        "slug": "golden-retriever", "nome": "Golden Retriever",
        "descricao": "Dócil, paciente e sociável. Ótimo com crianças e com toda a família.",
        "porte": "Grande", "temperamento": "Amigável e obediente",
        "vida_media": "10 a 12 anos", "dog_api_id": "retriever/golden",
    },
    {
        "slug": "labrador", "nome": "Labrador",
        "descricao": "Ativo, leal e curioso. Adora brincar e aprende rápido com treino positivo.",
        "porte": "Grande", "temperamento": "Alegre e companheiro",
        "vida_media": "10 a 12 anos", "dog_api_id": "labrador",
    },
    {
        "slug": "poodle", "nome": "Poodle",
        "descricao": "Inteligente e elegante. Existe em vários tamanhos e pede escovação frequente.",
        "porte": "Do toy ao padrão", "temperamento": "Esperto e atento",
        "vida_media": "12 a 15 anos", "dog_api_id": "poodle/standard",
    },
    {
        "slug": "husky-siberiano", "nome": "Husky Siberiano",
        "descricao": "Enérgico e independente. Precisa de muito exercício e de rotina de passeios.",
        "porte": "Médio a grande", "temperamento": "Brincalhão e teimoso",
        "vida_media": "12 a 14 anos", "dog_api_id": "husky",
    },
]


def semear_racas() -> None:
    """Insere as raças iniciais apenas quando a tabela está vazia."""
    if Raca.query.first():
        return
    db.session.add_all(Raca(**dados) for dados in RACAS_INICIAIS)
    db.session.commit()