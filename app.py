"""Ponto de entrada da API do DogWorld.

Como rodar (dentro da pasta backend/):
    python setup_translation.py  # baixar modelo e recursos offline (uma vez)
    python app.py
ou:
    flask --app app run --debug
"""
import os

from flask import Flask, abort, jsonify, request, send_from_directory

from config import Config
from database import db, iniciar_banco
from routes import racas_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(racas_bp)
    iniciar_banco(app)

    @app.get("/api/status")
    def status():
        return jsonify({"servico": "DogWorld API", "ok": True})

    @app.get("/")
    def pagina_inicial():
        return send_from_directory(app.root_path, "index.html")

    @app.get("/<path:arquivo>")
    def arquivo_publico(arquivo: str):
        arquivos_raiz = {
            "favicon.png",
            "logo-dogworld.png",
            "logo-marca-claro.png",
            "script.js",
            "style.css",
        }
        if arquivo in arquivos_raiz:
            return send_from_directory(app.root_path, arquivo)
        if arquivo.startswith("img/"):
            return send_from_directory(
                os.path.join(app.root_path, "img"),
                arquivo[4:],
            )
        abort(404)

    # CORS mínimo: só o front-end configurado em FRONTEND_ORIGIN pode chamar a API
    @app.after_request
    def liberar_front(resposta):
        origem = request.headers.get("Origin")
        if origem and origem == app.config["FRONTEND_ORIGIN"]:
            resposta.headers["Access-Control-Allow-Origin"] = origem
            resposta.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
            resposta.headers["Vary"] = "Origin"
        return resposta

    @app.errorhandler(404)
    def nao_encontrado(_):
        return jsonify({"erro": "Rota não encontrada."}), 404

    @app.errorhandler(500)
    def erro_interno(_):
        return jsonify({"erro": "Erro interno do servidor."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    # debug só quando você pedir: FLASK_DEBUG=1 python app.py
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", "5000")))