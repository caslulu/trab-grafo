# Documentação do projeto

O foco atual é o **DepGraph**, simulador de conflitos em dependências entre pacotes inspirado no Linux.

## Índice

| Documento | Conteúdo |
| --- | --- |
| [Protótipo de pacotes](prototipo-networkx/README.md) | Instalação, funcionamento, restrições de versão, conflitos, transações, dez imagens e limitações. |
| [Guia geral](../agent.md) | Requisitos do enunciado e planejamento da entrega acadêmica com grafos próprios. |
| [Enunciado](../TP.pdf) | PDF original do professor. |
| [Apresentação](../README.md) | Integrantes, objetivo e início rápido. |
| [Histórico do exemplo de tarefas](prototipo-networkx/tarefas-historico.md) | Primeira exploração, substituída pelo foco em pacotes. |

## Organização

```text
docs/
├── README.md
└── prototipo-networkx/
    ├── README.md
    ├── tarefas-historico.md
    ├── imagens/
    │   ├── pacotes-01-plano-instalacao.png
    │   ├── ...
    │   ├── pacotes-10-impacto-remocao.png
    │   └── imagens anteriores de tarefas
    ├── sem-ciclo.png  (histórico)
    └── com-ciclo.png  (histórico)
```

Centralizar os novos guias e artefatos em subpastas temáticas de `docs/`, com suas imagens próximas ao documento correspondente e links neste índice. Usar nomes em minúsculas, sem espaços nem acentos, e links relativos.

Distinguir funcionalidades implementadas, propostas da versão final e registros históricos. Documentar a origem dos dados e a reprodução de imagens e resultados. O `agent.md` e o PDF original permanecem na raiz.
