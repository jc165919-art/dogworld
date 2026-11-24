"""Instala localmente o modelo Argos Translate de inglês para português."""
import argostranslate.package
import argostranslate.translate


def _tradutor_instalado():
    idiomas = {
        idioma.code: idioma
        for idioma in argostranslate.translate.get_installed_languages()
    }
    origem = idiomas.get("en")
    destino = idiomas.get("pt")
    return origem.get_translation(destino) if origem and destino else None


def main() -> None:
    tradutor = _tradutor_instalado()
    if tradutor is None:
        print("Consultando os modelos de tradução disponíveis...")
        argostranslate.package.update_package_index()
        pacote = next(
            (
                pacote
                for pacote in argostranslate.package.get_available_packages()
                if pacote.from_code == "en" and pacote.to_code == "pt"
            ),
            None,
        )
        if pacote is None:
            raise RuntimeError(
                "Não foi encontrado um modelo Argos de inglês para português."
            )

        print("Baixando e instalando o modelo inglês-português...")
        caminho = pacote.download()
        argostranslate.package.install_from_path(caminho)
        argostranslate.translate.get_installed_languages.cache_clear()
        tradutor = _tradutor_instalado()

    if tradutor is None:
        raise RuntimeError("O modelo foi instalado, mas não ficou disponível para tradução.")

    print("Preparando os recursos para tradução offline...")
    tradutor.translate("A friendly dog is part of the family.")
    print("Modelo instalado. As traduções serão feitas localmente.")


if __name__ == "__main__":
    main()
