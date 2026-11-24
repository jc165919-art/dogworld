"""Conexão com o banco. SQLite por padrão; PostgreSQL ao definir DATABASE_URL."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def iniciar_banco(app) -> None:
    """Cria as tabelas e cadastra as raças iniciais se o banco estiver vazio."""
    from raca import semear_racas

    with app.app_context():
        db.create_all()
        semear_racas()