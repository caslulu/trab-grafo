# Documentação do projeto

Esta pasta centraliza os guias e as imagens do trabalho de Grafos, cujo tema é **Gestão de Conflitos em Sistemas de Dependência**.

## Índice

| Documento | Conteúdo |
| --- | --- |
| [Documentação do protótipo NetworkX](prototipo-networkx/README.md) | Funcionamento, arquitetura, instalação, roteiro de uso, galeria de imagens e limitações da versão exploratória. |
| [Guia geral do projeto](../agent.md) | Exigências acadêmicas, proposta da versão final, modelagem, planejamento e critérios de entrega. |
| [Enunciado oficial](../TP.pdf) | Requisitos e regras fornecidos pelo professor. |
| [Apresentação do repositório](../README.md) | Visão geral, integrantes e comandos para começar. |

## Organização

```text
docs/
├── README.md
└── prototipo-networkx/
    ├── README.md
    ├── sem-ciclo.png
    ├── com-ciclo.png
    └── imagens/
        ├── 01-interface-inicial.png
        ├── 02-simulacao-em-andamento.png
        ├── 03-simulacao-concluida.png
        ├── 04-ciclo-detectado.png
        ├── 05-ciclo-corrigido.png
        └── 06-validacao-de-entrada.png
```

O `agent.md` permanece na raiz como guia para o desenvolvimento, e o PDF original também permanece na raiz. Os documentos explicativos e as imagens de cada etapa devem ficar em uma subpasta temática de `docs/`, com links neste índice.

## Convenções para novos documentos

- Usar nomes de pastas e arquivos em minúsculas, sem espaços ou acentos.
- Guardar as imagens junto à documentação correspondente, em uma pasta `imagens/`.
- Usar links relativos para que a navegação funcione no repositório.
- Separar funcionalidades implementadas de propostas e trabalhos futuros.
- Registrar como reproduzir imagens e resultados gerados a partir do código.

O protótipo NetworkX é uma exploração inicial. A documentação da versão acadêmica com grafos e algoritmos próprios deverá ser adicionada conforme sua implementação.
