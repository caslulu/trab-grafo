# DepGraph — Protótipo NetworkX

Simulador de instalação e conflitos entre pacotes inspirado no Linux, com restrições de versão, dependências transitivas, backtracking, ciclos, transações e análise de remoção.

A documentação está em [docs/prototipo-networkx](../../docs/prototipo-networkx/README.md), incluindo dez imagens e os cenários de demonstração.

Na raiz, com as dependências instaladas:

```bash
python -m prototypes.networkx_preview
python -m prototypes.networkx_preview --cenario versoes
python -m prototypes.networkx_preview --pedidos "modern-browser, libcore>=2.0"
python -m prototypes.networkx_preview.gerar_imagens
```

As dependências estão em `requirements.txt`. O catálogo sintético está em `examples/pacotes.json`. A entrada principal usa `package_app.py` e `package_model.py`.

O primeiro exemplo de tarefas permanece disponível como histórico em `app.py`, `model.py` e na entrada `python -m prototypes.networkx_preview.tarefas`. Os argumentos antigos `--exemplo` e `--arquivo` pertencem apenas a essa entrada histórica.

A versão acadêmica final deverá substituir o NetworkX por estrutura e algoritmos próprios conforme o enunciado.
