"""Gera a galeria da documentação usando a interface real do protótipo."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .app import EXAMPLES, Preview
from .model import Project


DEFAULT_DESTINATION = Path(__file__).resolve().parents[2] / "docs/prototipo-networkx/imagens"


def perform(preview, action):
    """Aplica uma ação e apresenta seu resultado como os botões da interface."""
    try:
        message = action()
    except (ValueError, OSError) as error:
        preview.refresh(str(error), error=True)
    else:
        preview.refresh(message)


def initial(preview):
    preview.refresh("Exemplo válido carregado. A tarefa A está pronta para executar.")


def in_progress(preview):
    for _ in range(3):
        perform(preview, preview._advance)


def completed(preview):
    for _ in preview.project.graph:
        perform(preview, preview._advance)
    perform(preview, preview._advance)


def blocked(preview):
    perform(preview, preview._advance)


def corrected(preview):
    preview.source.set_val("E")
    preview.target.set_val("B")
    perform(preview, preview._remove_edge)


def invalid_input(preview):
    preview.source.set_val("A")
    preview.target.set_val("X")
    perform(preview, preview._add_edge)


SCENARIOS = [
    ("01-interface-inicial", "sem_ciclo", initial),
    ("02-simulacao-em-andamento", "sem_ciclo", in_progress),
    ("03-simulacao-concluida", "sem_ciclo", completed),
    ("04-ciclo-detectado", "com_ciclo", blocked),
    ("05-ciclo-corrigido", "com_ciclo", corrected),
    ("06-validacao-de-entrada", "sem_ciclo", invalid_input),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=DEFAULT_DESTINATION,
                        help="Pasta de saída para as seis imagens PNG.")
    args = parser.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)
    for name, example, prepare in SCENARIOS:
        preview = Preview(Project.load(EXAMPLES / f"{example}.json"), interactive=True)
        try:
            prepare(preview)
            path = args.destino / f"{name}.png"
            preview.fig.savefig(path, dpi=150, facecolor=preview.fig.get_facecolor())
            print(f"Imagem gerada: {path}")
        finally:
            plt.close(preview.fig)


if __name__ == "__main__":
    main()
