"""Renderiza as fontes UML locais em SVG e PNG, sem serviço remoto."""

import argparse
import hashlib
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", required=True, type=Path, help="Caminho do PlantUML 1.2026.4")
    args = parser.parse_args()
    jar = args.jar.resolve()
    if not jar.is_file():
        parser.error(f"JAR não encontrado: {jar}")
    sources = sorted((ROOT / "uml").glob("[0-9][0-9]-*.puml"))
    if not sources:
        parser.error("Nenhuma fonte UML encontrada")
    output = ROOT / "imagens"
    output.mkdir(exist_ok=True)
    base = ["java", "-Djava.awt.headless=true", "-jar", str(jar), "-charset", "UTF-8", "-failfast2"]
    # -o é relativo ao diretório das fontes; estilo.puml não é figura independente.
    for fmt in ("svg", "png"):
        subprocess.run(
            base + [f"-t{fmt}", "-o", str(output), *map(str, sources)],
            cwd=ROOT / "uml",
            check=True,
        )
        for source in sources:
            artifact = output / f"{source.stem}.{fmt}"
            if not artifact.is_file() or artifact.stat().st_size == 0:
                raise RuntimeError(f"Artefato ausente ou vazio: {artifact}")
    print(f"Geradas {len(sources)} figuras em SVG e PNG.")
    print(f"SHA-256 do JAR: {hashlib.sha256(jar.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
