"""Reproduz a galeria do gerenciador de pacotes usando a própria interface."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .package_app import PackagePreview

DEFAULT_DESTINATION = Path(__file__).resolve().parents[2] / "docs/prototipo-networkx/imagens"
SCENARIOS = [
    ("pacotes-01-plano-instalacao", "desktop", "inicio"),
    ("pacotes-02-transacao-em-andamento", "desktop", "andamento"),
    ("pacotes-03-transacao-concluida", "desktop", "conclusao"),
    ("pacotes-04-versoes-incompativeis", "versoes", "inicio"),
    ("pacotes-05-pacotes-incompativeis", "conflito", "inicio"),
    ("pacotes-06-dependencia-ausente", "ausente", "inicio"),
    ("pacotes-07-dependencia-circular", "ciclo", "inicio"),
    ("pacotes-08-atualizacao", "upgrade", "inicio"),
    ("pacotes-09-versao-alternativa", "alternativa", "inicio"),
    ("pacotes-10-impacto-remocao", "desktop", "remocao"),
]


def prepare(preview, state):
    if state == "andamento":
        message = ""
        for _ in range(5):
            message = preview.advance()
        preview.render(message)
    elif state in ("conclusao", "remocao"):
        message = ""
        for _ in preview.session.plan.actions:
            message = preview.advance()
        preview.render(message)
        if state == "remocao":
            preview.request_box.set_val("libcore")
            preview.render(preview.removal())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    for name, scenario, state in SCENARIOS:
        preview = PackagePreview(scenario=scenario)
        try:
            prepare(preview, state)
            path = args.destino / f"{name}.png"
            preview.fig.savefig(path, dpi=150, facecolor=preview.fig.get_facecolor())
            print(f"Imagem gerada: {path}")
        finally:
            plt.close(preview.fig)


if __name__ == "__main__":
    main()
