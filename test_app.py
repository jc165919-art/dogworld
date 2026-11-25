import unittest

from app import app


class RenderServingTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_homepage_and_assets_are_served(self):
        for path, content_type in (
            ("/", "text/html"),
            ("/style.css", "text/css"),
            ("/script.js", "text/javascript"),
            ("/img/hero.png", "image/png"),
        ):
            with self.subTest(path=path):
                resposta = self.client.get(path)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(content_type, resposta.content_type)
                resposta.close()

    def test_private_project_files_are_not_served(self):
        for path in ("/.env", "/config.py", "/dogworld.db"):
            with self.subTest(path=path):
                resposta = self.client.get(path)
                self.assertEqual(resposta.status_code, 404)
                resposta.close()

    def test_api_status_remains_available(self):
        resposta = self.client.get("/api/status")

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.get_json()["ok"])
        resposta.close()


if __name__ == "__main__":
    unittest.main()
