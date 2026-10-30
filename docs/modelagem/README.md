# Modelagem do DepGraph

A [documentação completa](documentacao-completa.md) reúne o contexto, os requisitos, os casos de uso, os oito diagramas revisados, cardinalidades, contratos, dados, algoritmos, validação e execução em um único documento.

Esta é a base inicial de requisitos e diagramas para a versão acadêmica do simulador de pacotes. Foi preparada a partir do código do protótipo e dos requisitos registrados em [agent.md](../../agent.md), cuja referência é o [enunciado](../../TP.pdf).

## Por que modelar agora

O trabalho avalia UML. Para a aplicação, a modelagem também resolve decisões práticas: separar catálogo de resolução, substituir NetworkX por grafo próprio e definir quando uma transação pode alterar o estado instalado. Elaborar esses documentos antes da migração reduz ambiguidades entre os integrantes.

Os diagramas são uma primeira versão para orientar o desenvolvimento. Não representam uma arquitetura final já implementada. Cada documento identifica o que descreve o protótipo e o que propõe para a entrega.

As [principais modelagens em UML](modelagens-principais.md) estão disponíveis com oito figuras em PNG e SVG, fontes PlantUML e instruções de reprodução. Esse é o conjunto de referência para revisão e uso no relatório; os blocos Mermaid anteriores permanecem como vistas introdutórias.

| Documento | Utilidade |
| --- | --- |
| [Documentação completa](documentacao-completa.md) | Referência consolidada da aplicação e da modelagem, com as oito figuras incorporadas. |
| [Principais modelagens UML](modelagens-principais.md) | Galeria de casos de uso, classes de domínio e núcleo, componentes, sequências, estados e atividade, com fontes e imagens. |
| [Revisão dos diagramas](revisao-dos-diagramas.md) | Avaliação dos oito modelos, conferência de cardinalidades e correções de legibilidade e comportamento. |
| [Guia de formatação e notação](guia-de-notacao.md) | Explica Markdown, sintaxe Mermaid, símbolos, relações, UML, revisão e exportação. |
| [Requisitos e critérios de aceitação](requisitos.md) | Define comportamento, limites e evidências esperadas. |
| [Casos de uso e fluxos](casos-de-uso.md) | Explica o que o usuário faz e como tratar alternativas. |
| [Arquitetura e classes](arquitetura.md) | Registra classes atuais, componentes e classes propostas. |
| [Sequências e estados](comportamento.md) | Define planejamento, preparação, confirmação e invalidação. |

## Diagramas escolhidos

1. **Casos de uso:** delimita as funcionalidades disponíveis ao usuário.
2. **Classes do domínio:** representa catálogo, versões, requisitos e plano.
3. **Classes do núcleo:** distribui responsabilidades da implementação própria.
4. **Componentes propostos:** estabelece dependências entre interface, núcleo e arquivos.
5. **Sequência de planejamento:** mostra a colaboração entre sessão, resolvedor e grafo.
6. **Sequência de execução:** explicita preparação e confirmação da transação.
7. **Estados da transação:** trata plano bloqueado, progresso, conclusão e alterações externas.
8. **Atividade de resolução:** conecta busca de versões, conflitos, ciclos e limite de busca.

A vista de classes atuais em [arquitetura.md](arquitetura.md) complementa esse conjunto, registrando a estrutura real do protótipo antes da migração.

Não há necessidade inicial de diagrama de banco de dados: a aplicação usa JSON e estado em memória. Um diagrama de implantação acrescentaria pouco ao cenário local atual. Se surgirem banco de dados, servidor ou execução distribuída, reavaliar essas escolhas.

As vistas introdutórias estão em blocos Mermaid editáveis. Nelas, casos de uso, componentes e atividade usam fluxogramas simplificados. O conjunto de referência em [PlantUML](modelagens-principais.md) fornece as vistas em notação UML, incluindo ator, elipses e fronteira do sistema nos casos de uso, componentes, nós de atividade, decisões e estados compostos.

## Como manter

- Ao mudar uma regra, atualizar o requisito e os fluxos afetados.
- Ao implementar a arquitetura proposta, ajustar nomes, assinaturas e relações ao código real.
- Associar os critérios de aceitação aos testes efetivamente executados, sem presumir cobertura.
- Exportar as figuras para o relatório e conferir legibilidade no tamanho de impressão.
- Registrar responsáveis reais após a divisão do grupo; nenhuma atribuição foi presumida aqui.

## Pendências para fechar a modelagem

- Distribuir responsabilidades e confirmar prazo e procedimentos no Canvas.
- Validar esta divisão de módulos com o grupo e alinhar UML ao código final.
- Definir a base externa ou justificar o catálogo sintético e documentar sua origem.
- Definir o protocolo experimental, ambiente, tamanhos de entrada e limites de busca.
- Preparar o relatório SBC com as figuras selecionadas; esta documentação ainda não substitui o relatório obrigatório.
