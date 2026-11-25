import unittest
from unittest.mock import patch

from app import app
from dogapi import _formatar_raca, listar_racas


class ListarRacasTest(unittest.TestCase):
    def setUp(self):
        self.contexto = app.app_context()
        self.contexto.push()
        self.addCleanup(self.contexto.pop)

    @patch("dogapi._traduzir", side_effect=lambda texto: texto)
    @patch("dogapi._obter")
    def test_busca_encontra_raca_com_erros_de_digitacao(self, obter, _traduzir):
        obter.return_value = (
            [
                {
                    "id": 1,
                    "name": "Golden Retriever",
                    "description": "A friendly family dog.",
                },
                {"id": 2, "name": "Labrador Retriever"},
                {"id": 3, "name": "Pug"},
            ],
            3,
        )

        racas, total = listar_racas("golen retreiver", pagina=0, limite=24)

        self.assertEqual(total, 1)
        self.assertEqual([raca["nome"] for raca in racas], ["Golden Retriever"])
        self.assertEqual(racas[0]["caracteristicas"], [])
        self.assertTrue(_traduzir.called)
        obter.assert_called_once_with(
            "breeds", {"page": 0, "limit": 1000, "order": "ASC"}
        )

    @patch("dogapi._obter")
    def test_busca_nao_inclui_nomes_semelhantes_com_palavras_menores(self, obter):
        obter.return_value = (
            [
                {"id": 1, "name": "Golden Retriever"},
                {"id": 2, "name": "Golden Mountain Dog"},
                {"id": 3, "name": "Glen of Imaal Terrier"},
                {"id": 4, "name": "Olde English Bulldogge"},
            ],
            4,
        )

        racas, total = listar_racas("golden", pagina=0, limite=24)

        self.assertEqual(total, 2)
        self.assertEqual(
            [raca["nome"] for raca in racas],
            ["Golden Mountain Dog", "Golden Retriever"],
        )

    @patch("dogapi._obter")
    def test_busca_sem_correspondencia_nao_retorna_racas_aleatorias(self, obter):
        obter.return_value = (
            [
                {"id": 1, "name": "Golden Retriever"},
                {"id": 2, "name": "Labrador Retriever"},
            ],
            2,
        )

        racas, total = listar_racas("qzxwrr", pagina=0, limite=24)

        self.assertEqual(racas, [])
        self.assertEqual(total, 0)

    @patch("dogapi._traduzir", side_effect=lambda texto: f"PT: {texto}")
    def test_formata_informacoes_em_portugues_mantendo_nome_e_url(self, traduzir):
        raca = _formatar_raca({
            "id": 1,
            "name": "Golden Retriever",
            "description": "Friendly family dog",
            "temperament": "Friendly, intelligent",
            "breed_group": "Working",
            "life_span": "10-12",
            "weight": {"metric": "Male: 29-34; Female: 25-29"},
            "wikipedia_url": "https://example.com/dog",
        })

        self.assertEqual(raca["nome"], "Golden Retriever")
        self.assertEqual(raca["resumo"], "PT: Friendly family dog")
        self.assertIn(
            {"rotulo": "Temperamento", "valor": "PT: Friendly, intelligent"},
            raca["caracteristicas"],
        )
        self.assertIn(
            {"rotulo": "Mais informações", "valor": "https://example.com/dog"},
            raca["caracteristicas"],
        )
        self.assertEqual(
            next(item["valor"] for item in raca["caracteristicas"] if item["rotulo"] == "Grupo"),
            "Trabalho",
        )
        self.assertEqual(
            next(
                item["valor"]
                for item in raca["caracteristicas"]
                if item["rotulo"] == "Expectativa de vida"
            ),
            "10-12 anos",
        )
        self.assertEqual(traduzir.call_count, 4)
        self.assertNotIn(
            "https://example.com/dog",
            [chamada.args[0] for chamada in traduzir.call_args_list],
        )

    @patch("dogapi._traduzir")
    def test_resumo_de_fallback_permanece_em_portugues(self, traduzir):
        raca = _formatar_raca({"id": 1, "name": "Raça sem descrição"})

        self.assertEqual(
            raca["resumo"],
            "Consulte as características para conhecer esta raça.",
        )
        traduzir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
