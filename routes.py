from flask import Blueprint, jsonify, request

from dogapi import TheDogAPIError, buscar_raca as buscar_raca_api, listar_racas as listar_racas_api
from raca import Raca

racas_bp = Blueprint("racas", __name__)


@racas_bp.get("/api/racas")
def listar_racas():
    busca = request.args.get("busca", "").strip()
    try:
        pagina = int(request.args.get("pagina", "0"))
    except ValueError:
        return jsonify({"erro": "O número da página é inválido."}), 400
    if pagina < 0:
        return jsonify({"erro": "O número da página não pode ser negativo."}), 400

    limite = 24
    try:
        racas, total = listar_racas_api(busca, pagina, limite)
    except TheDogAPIError as erro:
        return jsonify({"erro": str(erro)}), erro.status_code

    return jsonify({
        "resultados": racas,
        "pagina": pagina,
        "limite": limite,
        "total": total,
        "tem_mais": (pagina + 1) * limite < total,
    })


@racas_bp.get("/api/racas/<int:raca_id>")
def detalhe_raca(raca_id):
    try:
        return jsonify(buscar_raca_api(raca_id))
    except TheDogAPIError as erro:
        return jsonify({"erro": str(erro)}), erro.status_code


@racas_bp.get("/api/racas/<slug>")
def buscar_raca(slug):
    raca = Raca.query.filter_by(slug=slug).first()
    if raca is None:
        return jsonify({"erro": "Raça não encontrada."}), 404

    return jsonify(raca.to_dict())
