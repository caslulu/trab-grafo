# DepGraph — Documentação completa da aplicação e da modelagem

Consolidação: **30/10/2026**. Este documento reúne o escopo, os requisitos, os casos de uso, as oito figuras UML revisadas, os contratos e as orientações de implementação do DepGraph. Pode ser lido em sequência sem abrir os guias temáticos para compreender o sistema.

**Estado da documentação:** as funcionalidades de pacotes já existem no protótipo exploratório com NetworkX e Matplotlib. As classes em português, os componentes separados e os algoritmos próprios descritos nas figuras são a arquitetura proposta para a versão acadêmica. Esta documentação não declara essa migração como concluída e não substitui o relatório LaTeX/SBC obrigatório.

As fontes das figuras ficam em [uml/](uml/) e as imagens em [imagens/](imagens/). Os documentos temáticos continuam como fontes de manutenção dos respectivos assuntos; alterações neles devem ser refletidas nesta consolidação. Os diagramas PlantUML são a referência visual; os exemplos Mermaid anteriores são introdutórios.

## Sumário

1. [Contexto e escopo](#1-contexto-e-escopo)
2. [Modelo do problema e do grafo](#2-modelo-do-problema-e-do-grafo)
3. [Requisitos e regras](#3-requisitos-e-regras)
4. [Casos de uso detalhados](#4-casos-de-uso-detalhados)
5. [Arquitetura e oito diagramas UML](#5-arquitetura-e-oito-diagramas-uml)
6. [Cardinalidades e contratos](#6-cardinalidades-e-contratos)
7. [Dados de entrada e resultados](#7-dados-de-entrada-e-resultados)
8. [Algoritmos, correção e complexidade](#8-algoritmos-correção-e-complexidade)
9. [Rastreabilidade e validação](#9-rastreabilidade-e-validação)
10. [Execução e demonstração](#10-execução-e-demonstração)
11. [Evolução e entrega acadêmica](#11-evolução-e-entrega-acadêmica)
12. [Referências e manutenção](#12-referências-e-manutenção)

## 1. Contexto e escopo

O DepGraph aplica grafos ao tema Gestão de Conflitos em Sistemas de Dependência. Simula um gerenciador de pacotes: recebe pedidos de instalação ou atualização, considera um catálogo com várias versões e o estado já instalado, procura uma combinação compatível e calcula a precedência de instalação.

A interação ocorre em janela local. O usuário analisa o pedido, inspeciona o grafo e avança na preparação dos pacotes. A transação só modifica os instalados ao concluir toda a preparação e validar o estado final. A aplicação também consulta impacto de remoção e exporta resultados.

O catálogo atual é sintético, com 27 nomes e 32 versões. O cenário principal seleciona 17 pacotes, 26 relações de dependência e 15 novas instalações sobre dois pacotes inicialmente instalados. Esses números descrevem o exemplo do repositório, não um limite da arquitetura nem uma medição de desempenho.

Não há instalação real, download de pacotes, autenticação ou servidor. O ator externo é o usuário; o estado instalado é um mapa em memória. Comparação completa Debian/RPM, scripts, arquiteturas, pacotes virtuais, alternativas com `|` e remoção efetiva ficam fora do escopo inicial.

### Vocabulário

| Termo | Significado |
| --- | --- |
| Pacote no catálogo | Uma versão de um nome, acompanhada de metadados. |
| Requisito | Nome e condição que uma versão deve satisfazer. |
| Dependência | Requisito obrigatório para que outro pacote seja válido. |
| Incompatibilidade | Restrição que impede duas versões de coexistirem. |
| Seleção | Atribuição de uma versão por nome usada em uma tentativa de solução. |
| Plano | Resultado da análise, contendo seleção, grafo, ordem, operações ou diagnóstico. |
| Preparado | Pacote cuja operação foi simulada, ainda sem confirmação parcial nos instalados. |
| Confirmação | Aplicação do estado final validado à sessão. |
| Dependente | Pacote que precisa direta ou transitivamente de outro. |

## 2. Modelo do problema e do grafo

Sejam `C` o catálogo, `I` o mapa dos instalados e `P` a lista de pedidos. A busca tenta produzir uma seleção `S`, que associa cada nome a no máximo uma versão. O conjunto selecionado inclui os pacotes instalados preservados, os pedidos e todas as dependências necessárias.

Uma solução deve satisfazer simultaneamente:

1. A versão escolhida de cada pedido atende à restrição solicitada.
2. Toda dependência de uma versão selecionada aparece em `S` com uma versão aceita.
3. Nenhuma incompatibilidade declarada aplicável existe entre as versões selecionadas.
4. Nomes já instalados e não solicitados mantêm suas versões, respeitando também seus dependentes.
5. O grafo de precedência da seleção é acíclico na política didática adotada.

O grafo dirigido `G = (V, E)` possui um vértice por nome selecionado. Uma aresta `(A, B)` pertence a `E` quando B depende de A. A versão de A é informação do vértice; a restrição que B impõe a A é informação da relação. As arestas não têm pesos. Dependências compartilhadas não duplicam o vértice.

Uma ordenação topológica `T` deve satisfazer `posicao(A) < posicao(B)` para toda aresta `A → B`. Pode existir mais de uma ordem correta. A lista de operações é a subsequência de `T` que contém apenas nomes ausentes de `I` ou cuja versão selecionada difere da instalada.

**Exemplo conceitual:** se `editor` e `viewer` dependem de `libui`, o grafo contém `libui → editor` e `libui → viewer`. A biblioteca aparece uma vez e vem antes de ambos. Esse exemplo ilustra a orientação; não acrescenta nomes ao catálogo do projeto.

Se os dois aplicativos exigirem intervalos disjuntos de uma biblioteca, o pedido pode ser inviável mesmo sem ciclo. Por isso, resolução de versões e conflitos são verificações separadas da ordenação topológica.

## 3. Requisitos e regras

A situação de cada item é baseada no protótipo e na especificação registrada no repositório; não representa execução de testes nesta consolidação.

### Requisitos funcionais

| ID | Requisito e critério de aceitação | Situação |
| --- | --- | --- |
| RF01 | Carregar JSON de catálogo e estado instalado; rejeitar estrutura inválida, versões duplicadas equivalentes e estado inicial inconsistente com mensagem explicativa. | Existe no protótipo. |
| RF02 | Receber um ou mais pedidos; rejeitar entrada vazia ou sintaxe inválida antes de executar operações. | Existe no protótipo. |
| RF03 | Expandir dependências transitivas e selecionar uma versão por nome; toda dependência da solução deve existir e aceitar a versão selecionada. | Existe no protótipo. |
| RF04 | Preservar versões instaladas de nomes ausentes do pedido; permitir mudança de nomes explicitamente solicitados, mantendo válidos os dependentes existentes. | Existe no protótipo. |
| RF05 | Explorar versões alternativas; uma tentativa abandonada não pode deixar dependências residuais na solução. | Existe no protótipo. |
| RF06 | Distinguir dependência ausente, restrições incompatíveis, conflito declarado e ciclo; falhas não podem disponibilizar operações de instalação. | Existe no protótipo. |
| RF07 | Produzir ordem topológica; para toda aresta A → B, A deve preceder B. Mostrar um caminho fechado real quando houver ciclo. | Existe com NetworkX; implementar algoritmos próprios. |
| RF08 | Preparar um pacote por avanço; verificar pré-requisitos e manter o estado instalado intacto durante a preparação parcial. | Existe no protótipo. |
| RF09 | Confirmar o estado final somente após validação integral; concluir sem alterações quando o plano não tiver operações. | Existe no protótipo. |
| RF10 | Impedir avanço após mudança de pedido ou estado instalado; exigir nova análise e descartar preparação anterior ao replanejar. | Existe, com verificação do pedido na interface; centralizar no núcleo proposto. |
| RF11 | Calcular dependentes diretos e transitivos de um pacote instalado e ordem de remoção em cascata; a consulta não altera o estado. | Existe com NetworkX; implementar busca própria. |
| RF12 | Visualizar dependências, versões, diagnósticos e dados de um vértice selecionado. | Existe no protótipo. |
| RF13 | Exportar relatório JSON e imagem PNG; informar falhas de escrita ao usuário. | Existe no protótipo. |
| RF14 | Interromper busca ao atingir limite e informar resultado inconclusivo, sem afirmar inexistência de solução. | Existe no protótipo. |

### Regras do domínio

- **RD01 — Direção:** A → B significa que B depende de A. Conflitos são restrições separadas das arestas de precedência.
- **RD02 — Versões:** de um a três componentes numéricos, comparados numericamente. `1`, `1.0` e `1.0.0` são equivalentes.
- **RD03 — Restrições:** o modelo aceita intervalos com condições combinadas. A entrada textual atual de pedidos aceita uma condição por item separado por vírgula; não presumir suporte ao mesmo formato de intervalo nessa entrada.
- **RD04 — Política de busca:** preferir versões mais altas e retornar uma solução viável. Não há garantia de solução ótima, atualização mínima ou menor volume de download.
- **RD05 — Conflitos:** basta que uma das versões declare uma incompatibilidade aplicável à outra para impedir coexistência.
- **RD06 — Ciclos:** rejeitar ciclos por exigir precedência estrita, mesmo que gerenciadores reais adotem outras regras.
- **RD07 — Estado preservado:** todos os pacotes instalados participam da validação; não remover automaticamente um pacote para viabilizar o pedido.
- **RD08 — Diagnóstico:** uma falha de busca pode mostrar uma tentativa representativa; não equivale a enumerar todas as causas possíveis.

### Requisitos técnicos e acadêmicos

| ID | Critério |
| --- | --- |
| RN01 | Usar estrutura de grafo e processamento próprios na versão final; NetworkX fica isolado no protótipo ou em comparações de desempenho. |
| RN02 | Executar o núcleo sem janela, permitindo testes e experimentos independentes da interface. |
| RN03 | Implementar Kahn, DFS e busca de dependentes em O(V + E), sem alterar o grafo original durante análise. Medir o backtracking separadamente, pois pode ser exponencial. |
| RN04 | Registrar fontes dos dados, transformação, ambiente, sementes e repetições dos experimentos; não apresentar catálogo sintético como dados reais de Linux. |
| RN05 | Manter interface gráfica, UML coerente com o código e contribuições individuais identificáveis no Git. |
| RN06 | Produzir relatório LaTeX/SBC de 12–15 páginas, slides, apresentação de 10 minutos, vídeo de 12–18 minutos e pacote de entrega conforme o enunciado. |

### Evidências a produzir

Os testes de referência estão em [test_packages.py](../../prototypes/networkx_preview/test_packages.py). A migração deve preservar os cenários e acrescentar testes específicos da estrutura própria: grafo vazio, vértice isolado, laço, componentes desconexas, ciclo com dependentes externos e invariância do grafo após as consultas.

Na revisão final, verificar RF01–RF14 com testes ou demonstrações reproduzíveis. Para RN03, registrar análise dos algoritmos e medições efetivas. Para RN05–RN06, conferir os artefatos entregues. Ainda não há uma matriz completa de resultados da versão final.

### Fora do escopo inicial

Instalação real, downloads, scripts de manutenção, pacotes virtuais, múltiplas arquiteturas, sintaxe completa Debian/RPM, dependências opcionais, alternativas com `|`, remoção efetiva e resolução automática por desinstalação. Persistência de estado entre execuções não é requisito atual; exportar relatório não equivale a salvar e restaurar uma sessão.

## 4. Casos de uso detalhados

### UC01 — Carregar cenário

**Requisitos:** RF01, RF02. **Pré-condição:** catálogo válido disponível.

1. O usuário escolhe um cenário de demonstração.
2. A aplicação restaura a base instalada do cenário e descarta a sessão anterior.
3. Preenche o pedido, analisa e apresenta o resultado.

**Resultado:** nova sessão de demonstração. Catálogo ou estado inválido deve gerar erro explicativo. A restauração da base é própria da demonstração, não uma desinstalação real.

### UC02 — Analisar instalação ou atualização

**Requisitos:** RF02–RF07, RF10, RF14. **Pré-condição:** catálogo e estado instalado válidos.

1. O usuário informa nomes de pacotes e restrições opcionais e solicita análise.
2. A aplicação valida a entrada e registra pedido e estado usados no planejamento.
3. O resolvedor fixa os instalados não solicitados, expande dependências e tenta versões compatíveis.
4. Para uma atribuição completa, verifica a precedência e produz ordem topológica.
5. Mostra versões selecionadas, operações necessárias e grafo.

**Alternativas:** entrada inválida impede análise; falta de solução gera diagnóstico e bloqueia execução; limite de busca gera resultado inconclusivo. Um ciclo em uma tentativa permite tentar outra versão, quando houver candidatos.

**Resultado:** plano válido ou diagnóstico, sem alterar o estado instalado. Uma nova análise válida como entrada reinicia o progresso anterior. O plano pode conter zero operações se o pedido já estiver atendido.

### UC03 — Inspecionar pacote e diagnóstico

**Requisito:** RF12. **Pré-condição:** resultado de análise visível.

1. O usuário seleciona um vértice.
2. A aplicação mostra os metadados disponíveis, dependências e restrições relacionadas.
3. Em caso de falha, apresenta o diagnóstico associado ao resultado.

**Resultado:** consulta sem alteração de estado. Um nó de dependência ausente pode não ter metadados de pacote disponíveis.

### UC04 — Avançar transação simulada

**Requisitos:** RF08–RF10. **Pré-condição:** plano válido referente ao pedido e ao estado atuais.

1. O usuário solicita o próximo passo.
2. A aplicação verifica a validade do plano e os pré-requisitos da próxima operação no estado temporário.
3. Registra o pacote como preparado e atualiza o progresso.
4. Ao preparar a última operação, valida o estado final completo e confirma a transação em memória.

**Alternativas:** plano ausente, bloqueado ou desatualizado impede avanço; falha de pré-requisito ou validação impede confirmação; plano sem operações conclui sem alterar os instalados; avançar após conclusão não repete operações.

**Resultado:** durante preparação parcial, instalados intactos; após confirmação, estado final válido. A ação de reiniciar plano corresponde a uma nova análise, descartando a preparação parcial.

### UC05 — Analisar impacto de remoção

**Requisito:** RF11. **Pré-condição:** nome de um pacote instalado informado.

1. O usuário solicita a análise de impacto.
2. A aplicação percorre os dependentes no grafo do estado instalado.
3. Exibe o conjunto afetado e uma ordem de remoção que coloca dependentes antes das dependências.

**Alternativa:** nome não instalado gera erro explicativo.

**Resultado:** relatório de impacto; nenhum pacote é removido. O conjunto de dependentes exclui o pacote consultado; a ordem sugerida inclui esse pacote.

### UC06 — Exportar relatório e imagem

**Requisito:** RF13. **Pré-condição:** resultado de análise disponível.

1. O usuário solicita exportação.
2. A aplicação escreve o relatório JSON e uma imagem PNG da visualização.
3. Informa o destino ou o erro de escrita.

**Resultado:** arquivos para consulta e documentação. O relatório identifica pedido analisado e texto editado; exportar um resultado não autoriza executá-lo se estiver desatualizado. A exportação atual não garante atomicidade entre os dois arquivos: uma falha pode deixar apenas um deles gravado.

## 5. Arquitetura e oito diagramas UML

As figuras seguintes foram revisadas quanto à coerência e à legibilidade, incluindo as 15 cardinalidades das duas vistas de classes. Cada vista apresenta seu escopo, sua situação e os requisitos relacionados.

### Diagrama 1. Casos de uso — o que o usuário pode fazer

![Casos de uso do DepGraph](imagens/01-casos-de-uso.png)

[Fonte PlantUML](uml/01-casos-de-uso.puml) · [Figura vetorial SVG](imagens/01-casos-de-uso.svg)

O único ator externo é o usuário. A fronteira contém os seis objetivos descritos em [casos-de-uso.md](casos-de-uso.md). Catálogo, resolvedor e estado instalado são partes do sistema, não atores. Não foram adicionadas relações `include` ou `extend`, pois a ordem de execução de dois objetivos não justifica essas relações.

**Situação:** funcionalidades do protótipo a preservar. **Requisitos:** RF01–RF14, distribuídos nos seis casos de uso. Pré-condições e alternativas permanecem na especificação textual dos casos.

### Diagrama 2. Classes do domínio — quais informações são representadas

![Classes do domínio](imagens/02-classes-dominio.png)

[Fonte PlantUML](uml/02-classes-dominio.puml) · [Figura vetorial SVG](imagens/02-classes-dominio.svg)

`Pacote` representa uma versão disponível, com requisitos separados de dependência e incompatibilidade. `Catalogo` indexa as versões. `Plano` referencia os pedidos, versões selecionadas, grafo de precedência e diagnósticos; mantém uma cópia da base instalada e a lista de operações necessárias.

`ResultadoPlano` explicita três resultados: válido, bloqueado e inconclusivo. Essa enumeração é proposta para a versão final; o protótipo usa `success` e um diagnóstico de limite. Um grafo parcial pode existir em um resultado de falha para explicar o problema, sem autorizar a execução.

**Situação:** proposta. **Requisitos:** RF01–RF07 e RF14. As multiplicidades escritas restringem as extremidades de destino; multiplicidades inversas não especificadas não devem ser interpretadas como exclusividade. Associações não afirmam composição ou controle exclusivo de ciclo de vida. Tipos como `mapa` e `lista` são abreviações conceituais.

### Diagrama 3. Classes do núcleo — quem executa cada responsabilidade

![Classes do núcleo](imagens/03-classes-nucleo.png)

[Fonte PlantUML](uml/03-classes-nucleo.puml) · [Figura vetorial SVG](imagens/03-classes-nucleo.svg)

`Sessao` coordena os comandos e mantém os instalados. `Resolvedor` busca uma atribuição de versões sem alterar o estado. `Transacao` prepara operações vinculadas a um plano. Após validação integral, a sessão aplica o estado final. `AnaliseRemocao` consulta dependentes sem remover pacotes. `GrafoDependencias` implementa adjacência, Kahn, DFS e busca de dependentes.

`Catalogo` e `Plano` são as mesmas classes da vista anterior, com detalhes omitidos. As setas contínuas representam acesso por associação; as tracejadas representam dependência de uso. O catálogo usa o grafo para validar estados, enquanto o resolvedor o constrói para analisar as escolhas.

**Situação:** proposta de separação do atual `Catalog` e `Session`. **Requisitos:** RF03–RF11, RF14, RN01–RN03. As assinaturas são contratos conceituais, não uma API final já implementada.

### Diagrama 4. Componentes — como a aplicação será dividida

![Componentes do DepGraph](imagens/04-componentes.png)

[Fonte PlantUML](uml/04-componentes.puml) · [Figura vetorial SVG](imagens/04-componentes.svg)

A interface envia comandos ao núcleo e usa entrada/saída para carregar e exportar arquivos. O núcleo não depende da interface. Os componentes são responsabilidades lógicas, não processos nem diretórios já criados. Todas as setas são dependências de uso; interfaces fornecidas/requeridas não foram inventadas nesta etapa.

A migração precisa retirar NetworkX tanto do processamento quanto do layout e desenho da versão final. A camada gráfica pode utilizar recursos de desenho sem executar os algoritmos de domínio.

**Situação:** proposta. **Requisitos:** RF01, RF12–RF13, RN01–RN02.

### Diagrama 5. Sequência de planejamento — como um pedido vira plano

![Sequência de planejamento](imagens/05-sequencia-planejamento.png)

[Fonte PlantUML](uml/05-sequencia-planejamento.puml) · [Figura vetorial SVG](imagens/05-sequencia-planejamento.svg)

A sessão valida a entrada e o resolvedor verifica a base, consulta candidatos e explora versões. Uma atribuição completa compatível permite construir o grafo e tentar a ordem topológica. Se houver ciclo, a DFS obtém um caminho real para o diagnóstico; outras versões ainda podem ser tentadas. Ao abandonar um ramo, suas dependências são descartadas.

O laço resume a busca em profundidade, sem representar cada chamada recursiva. Uma solução encerra a busca; esgotamento produz bloqueio; limite atingido antes da conclusão produz resultado inconclusivo. Todos os caminhos preservam os instalados.

A sessão registra qualquer resultado de análise, mas cria uma transação executável somente quando o plano é válido.

**Situação:** proposta de colaboração entre as classes finais. **Requisitos:** RF02–RF07, RF10 e RF14.

### Diagrama 6. Sequência de transação — quando o estado pode mudar

![Sequência de preparação e confirmação](imagens/06-sequencia-transacao.png)

[Fonte PlantUML](uml/06-sequencia-transacao.puml) · [Figura vetorial SVG](imagens/06-sequencia-transacao.svg)

Cada avanço prepara no máximo uma operação. Os pré-requisitos são conferidos no estado temporário composto pelos instalados e pelas versões já preparadas. Uma falha impede a confirmação. Ao terminar todas as operações, o catálogo valida o estado completo antes de a sessão aplicá-lo.

**Casos de borda modelados:** plano ausente ou não válido; pedido ou base alterados; pré-requisito não satisfeito; validação final recusada; pedido já atendido sem operações; novo avanço após conclusão. Depois da confirmação, o estado final passa a ser o esperado, para que a atualização feita pela própria transação não gere um falso bloqueio.

**Situação:** proposta, centralizando no núcleo a regra hoje dividida entre interface e sessão. **Requisitos:** RF08–RF10.

### Diagrama 7. Estados — quais ações são permitidas em cada situação

![Estados do planejamento e da transação](imagens/07-estados.png)

[Fonte PlantUML](uml/07-estados.puml) · [Figura vetorial SVG](imagens/07-estados.svg)

A vista acompanha o ciclo da sessão durante planejamento e transação, inclusive quando ainda não existe plano. O estado composto `Resultado da análise` reúne os resultados e possui uma transição comum de reanálise. Dentro dele, `Plano disponível` reúne o plano pronto, a preparação e a conclusão. O pseudestado de escolha verifica o progresso após um avanço; a validação final ocorre antes da confirmação.

Uma única operação pode ser preparada e confirmada no mesmo avanço, assim como um pedido sem operações pode concluir sem modificar instalados. Não é necessário um clique extra para confirmar. Mudanças externas no pedido ou no estado esperado desatualizam o plano; a confirmação interna não é uma mudança externa.

Bloqueio, resultado inconclusivo, desatualização e falha impedem execução. Uma nova análise com sintaxe válida permite tentar novamente. Uma edição inválida não cria outra transação, mas impede o uso do pedido editado com um plano anterior. A sessão continua utilizável após concluir; por isso não há nó final de encerramento.

O avanço em `Concluida`, quando pedido e estado confirmado continuam iguais, é uma transição interna que apenas informa a conclusão. Não repete as operações nem compara os instalados com a base anterior à transação.

**Situação:** estados explícitos propostos. **Requisitos:** RF06, RF08–RF10 e RF14.

### Diagrama 8. Atividade de resolução — como a busca decide o resultado

![Atividade de resolução de versões](imagens/08-atividade-resolucao.png)

[Fonte PlantUML](uml/08-atividade-resolucao.puml) · [Figura vetorial SVG](imagens/08-atividade-resolucao.svg)

O fluxo explicita validação, fixação dos instalados não solicitados, exploração de ramos, checagem de restrições, alternativas, ordenação e resultados. A pilha representa os pontos de escolha da busca em profundidade; pode ser implementada explicitamente ou pela recursão.

Agendar candidatos não significa expandir antecipadamente todas as suas dependências. Cada ramo preserva suas próprias escolhas. Ao retirar um ramo que escolhe um candidato, verificar o limite, contar a tentativa e incorporar as dependências daquela versão à cópia de requisitos. O ramo inicial vazio não conta como escolha de versão. A pilha deve preservar as alternativas e explorar primeiro as versões mais altas. Um ramo inválido é descartado, não toda a busca. O diagnóstico de bloqueio é representativo, sem promessa de enumerar todas as causas.

**Situação:** algoritmo proposto, preservando a política do protótipo. **Requisitos:** RF03–RF07 e RF14; RN03. O custo pode ser exponencial na combinação de versões. Kahn e DFS, isoladamente, têm tempo O(V + E).

### Decisões consolidadas

| Decisão | Efeito sobre a implementação |
| --- | --- |
| Uma versão por nome no plano | Bibliotecas compartilhadas não duplicam vértices por dependente. |
| A → B significa que B depende de A | A ordem topológica instala pré-requisitos antes de dependentes. |
| Conflitos separados de precedência | Um grafo acíclico pode representar um pedido sem solução de versões. |
| Instalados não solicitados ficam fixos | A busca respeita a política de atualização explícita. |
| Preparação isolada da confirmação | Um avanço parcial não altera instalados. |
| Grafo e algoritmos próprios | NetworkX não participa do funcionamento da versão final. |
| Consulta de remoção sem execução | A modelagem não acrescenta desinstalação ao escopo. |

### Reprodução das figuras

Foi usado PlantUML **1.2026.4**, com Java 21 e execução local em modo headless. As classes, os componentes e os estados usam layout **ELK**, que separa melhor os rótulos das extremidades; casos de uso usam **Smetana**. Sequências e atividade usam os respectivos renderizadores internos. Não é necessário Graphviz externo para estas fontes. O JAR não é incluído no repositório.

Baixar a versão indicada na [distribuição oficial do PlantUML](https://github.com/plantuml/plantuml/releases/tag/v1.2026.4) e executar, na raiz do projeto:

```bash
python3 docs/modelagem/gerar_diagramas.py --jar /caminho/plantuml-1.2026.4.jar
```

SHA-256 do JAR utilizado:

```text
ebe66f9e67a12dc7aca4e10af67ab29b10ffa281bc72147dbfdc4c00d9de7664
```

O script gera os oito diagramas em PNG e SVG, usando o estilo compartilhado de `uml/estilo.puml`. Não modifica nem executa a aplicação. Fontes disponíveis no sistema podem alterar medidas e posicionamento em outra máquina.

Na preparação deste conjunto, os oito diagramas foram renderizados localmente e passaram por revisão visual. Também foram conferidos os links locais, a estrutura XML dos SVGs e os arquivos PNG gerados. Essa validação verifica os artefatos de modelagem; não comprova que a arquitetura proposta esteja implementada ou que a aplicação final passe nos testes.

### Uso no relatório e manutenção

As imagens já podem ser consultadas sem instalar um renderizador. Para o relatório, selecionar as vistas que sustentem a explicação e preferir figura vetorial quando o fluxo LaTeX permitir. Diagramas densos devem ocupar espaço suficiente ou ser apresentados em página própria; não reduzir até tornar atributos e condições ilegíveis.

Revisar nomes e contratos durante a implementação. Não declarar a arquitetura proposta como código entregue antes da migração. A exigência acadêmica de UML não determina que todas estas oito figuras precisem entrar no relatório; selecionar conforme clareza e limite de páginas.

## 6. Cardinalidades e contratos


Cada linha se lê da origem para o destino. A multiplicidade está na extremidade de destino e vale por instância da origem. A tabela permite conferir o significado mesmo sem ampliar a figura.

| Origem | Relação / destino | Multiplicidade no destino | Justificativa |
| --- | --- | --- | --- |
| Catalogo | versões disponíveis → Pacote | `0..*` | Catálogo pode conter zero ou mais versões de pacotes. |
| Pacote | dependencias → Requisito | `0..*` | Uma versão pode não ter dependências ou ter várias. |
| Pacote | incompatibilidades → Requisito | `0..*` | Uma versão pode não declarar conflitos ou declarar vários. |
| Plano | pedidos → Requisito | `1..*` | A análise aceita pelo menos um pedido; entrada vazia não cria plano. |
| Plano | versões selecionadas → Pacote | `0..*` | Um resultado de falha pode não selecionar nenhum pacote. |
| Plano | diagnósticos → Diagnostico | `0..*` | Um resultado válido pode não ter diagnósticos. |
| Plano | precedência → GrafoDependencias | `1` | Cada plano contém um grafo, que pode ser vazio ou parcial em caso de falha. |
| Sessao | Resolvedor | `1` | A sessão usa um resolvedor configurado na arquitetura proposta. |
| Sessao | Catalogo | `1` | A sessão trabalha com um catálogo. |
| Sessao | AnaliseRemocao | `1` | A sessão usa um serviço de consulta de remoção. |
| Sessao | preparação atual → Transacao | `0..1` | Pode não haver transação; há no máximo uma corrente. A mesma referência pode permanecer após concluir. |
| Transacao | Plano | `1` | Toda transação está vinculada a um plano válido. |
| Transacao | Catalogo | `1` | A validação final usa um catálogo. |
| Resolvedor | Catalogo | `1` | A busca consulta um catálogo. |
| AnaliseRemocao | Catalogo | `1` | A consulta usa o catálogo da sessão. |

Multiplicidade inversa omitida não deve ser preenchida por suposição: a vista não especifica exclusividade do objeto referenciado. `Plano → Pacote 0..*` permite vários objetos de versões selecionadas, mas a regra adicional limita a **uma versão por nome**. Uma cardinalidade sozinha não expressa essa restrição.

Os dois vínculos `Pacote → Requisito` têm papéis distintos. Não foram fundidos em uma única relação só para simplificar o desenho. Dependências e incompatibilidades continuam separadas. Setas tracejadas de uso não recebem cardinalidade: não representam coleções ou vínculos estruturais entre instâncias.

### Contratos das responsabilidades propostas

| Responsabilidade | Entrada e saída | Garantia |
| --- | --- | --- |
| Catalogo.consultar | Nome → versões disponíveis | Retorna candidatos do nome, sem decidir a solução global. |
| Catalogo.validarEstado | Mapa nome → versão | Rejeita pacotes desconhecidos, dependências inválidas, conflitos e ciclos. |
| Resolvedor.planejar | Pedidos, base instalada e limite → Plano | Não altera a base; distingue válido, bloqueado e inconclusivo. |
| GrafoDependencias.ordenar | Grafo → ordem ou indicação de ciclo | Cada pré-requisito precede seus dependentes; preserva o grafo. |
| GrafoDependencias.encontrarCiclo | Grafo → caminho fechado ou ausência de ciclo | Retorna arestas realmente presentes, sem confundir dependentes bloqueados com membros do ciclo. |
| Transacao.avancar | Estado instalado e pedido atual → progresso, conclusão ou erro | Prepara no máximo uma operação e exige vínculo com plano válido e atual. |
| Transacao.validarFinal | Seleção planejada → estado final validado | Não autoriza confirmação de estado inconsistente. |
| Sessao.avancar | Comando → resultado apresentado à interface | Aplica o estado final e marca a conclusão apenas após validação. |
| AnaliseRemocao.analisar | Nome instalado e base → afetados e ordem sugerida | Consulta sem modificar instalados. |

As assinaturas são conceituais. Definir na implementação os tipos de resultado e o mecanismo de erro, mantendo esses contratos. O plano deve ser tratado como instantâneo: alterar suas coleções externamente não pode mudar uma transação em andamento.

### Estado temporário e confirmação

Durante a preparação, os pré-requisitos são consultados em um estado temporário: a base instalada com as versões dos pacotes já preparados sobrepostas. Os instalados oficiais permanecem intactos até a confirmação integral. Se a última preparação concluir com sucesso e a seleção final passar na validação, a sessão substitui o mapa instalado e registra esse mapa como estado esperado.

Replanejar descarta a preparação anterior. Erro de sintaxe não cria um plano novo; um pedido editado não pode executar o plano anterior. Falha de escrita de relatório não equivale a falha de instalação, pois a exportação não executa a transação.

## 7. Dados de entrada e resultados

### Catálogo JSON

O formato atual usa `pacotes` como lista de versões e `instalados` como mapa. Cada dependência ou conflito contém `nome` e, opcionalmente, `versao`; a ausência da restrição representa aceitação de qualquer versão disponível.

Exemplo mínimo válido, reduzido a nomes existentes no catálogo:

```json
{
  "descricao": "Exemplo reduzido de catálogo sintético",
  "instalados": {"base-files": "1.0"},
  "pacotes": [
    {
      "nome": "base-files",
      "versao": "1.0",
      "descricao": "Base do sistema simulado",
      "depende": [],
      "conflita": []
    },
    {
      "nome": "libcore",
      "versao": "1.0",
      "descricao": "Biblioteca compartilhada",
      "depende": [{"nome": "base-files", "versao": ">=1.0"}],
      "conflita": []
    }
  ]
}
```

O catálogo completo está em [pacotes.json](../../prototypes/networkx_preview/examples/pacotes.json). Não é um espelho de uma distribuição Linux. A validação aceita dependências ausentes no catálogo para permitir cenários de erro; o resolvedor deve diagnosticá-las ao analisar um pedido afetado. Já o estado inicialmente instalado precisa ser consistente.

Nomes seguem o padrão `[a-z0-9][a-z0-9+.-]*`. Versões têm um a três componentes numéricos, normalizados para comparação: `1.10` é maior que `1.9`. As restrições aceitam `=`, `==`, `>`, `>=`, `<` e `<=`; o modelo de requisitos permite combinar condições como `>=1.0,<2.0`.

A caixa de pedidos atual usa vírgulas para separar itens e aceita uma condição por item. Exemplo: `modern-browser, libcore>=2.0`. Não confundir essa entrada com o formato de intervalos usado nos metadados JSON.

### Relatório e imagem da simulação

O protótipo grava `outputs/prototipo-networkx/pacotes.json` e `pacotes.png`. O relatório registra:

| Grupo | Campos atuais |
| --- | --- |
| Pedido e validade | `pedido`, `pedido_editado`, `plano_valido` |
| Estado e solução | `instalados`, `selecionados`, `ordem_instalacao` |
| Progresso | `preparados`, `transacao_concluida`, `historico` |
| Explicação da busca | `tentativas`, `diagnosticos` com tipo e mensagem |

No relatório atual, `ordem_instalacao` contém as operações necessárias, e não todos os vértices preservados da ordem topológica. `plano_valido: false` pode representar bloqueio ou busca inconclusiva; consultar o diagnóstico. A enumeração explícita de três resultados é proposta para a versão final.

Os arquivos são resultados de consulta, não um mecanismo de restauração da sessão. As duas gravações não são atômicas: um erro pode deixar apenas um arquivo produzido. Erros de escrita devem ser mostrados ao usuário.

## 8. Algoritmos, correção e complexidade

### Resolução de versões por backtracking

Acumular os pedidos e as versões fixas dos instalados não solicitados. Escolher um nome ainda sem atribuição, filtrar versões que atendem às condições conhecidas e explorar candidatos da maior versão para a menor. Cada escolha adiciona suas dependências ao ramo correspondente.

Ao encontrar restrição violada ou conflito, abandonar o ramo. Ao completar uma atribuição, construir o grafo e verificar a precedência. Um ciclo também pode levar ao retrocesso e à tentativa de outra versão. Dependências de escolhas abandonadas não podem permanecer na solução seguinte.

O raciocínio de correção depende de três propriedades: cada ramo representa suas próprias escolhas; a validação rejeita atribuições inválidas; uma solução só é aceita quando todos os requisitos e a precedência são satisfeitos. Com busca finita exaustiva e sem interrupção, esgotar os candidatos demonstra ausência de solução dentro da política. Com limite atingido, a conclusão correta é inconclusiva.

### Kahn para ordenação topológica

Copiar graus de entrada, enfileirar vértices com grau zero e remover um por vez da fila FIFO, reduzindo os graus dos sucessores na cópia. Um sucessor entra na fila apenas ao atingir zero. Se a quantidade processada for menor que `|V|`, não há ordem completa.

O invariante é que um vértice só é emitido após todos os seus predecessores. A consulta não altera as adjacências originais. Vértices restantes podem ser membros de ciclos ou apenas seus dependentes; usar DFS para identificar um ciclo concreto.

### DFS para reconstrução de ciclo

Percorrer todas as componentes com estados branco, cinza e preto. Uma aresta para vértice cinza fecha um caminho na pilha ativa. Usar predecessores para reconstruir esse caminho e repetir o primeiro vértice ao final. Um laço deve produzir um ciclo fechado com o mesmo nome nas duas extremidades.

### Dependentes e remoção

Percorrer sucessores do nome consultado com conjunto de visitados. Como as arestas vão da dependência ao dependente, esse percurso encontra os afetados. O conjunto de dependentes exclui o próprio nome consultado; a ordem sugerida de remoção inclui esse nome e usa a ordem topológica inversa do conjunto afetado. O estado não é alterado.

### Custos esperados

| Componente | Tempo | Espaço |
| --- | --- | --- |
| Adjacência do grafo | Construção O(V + E) | O(V + E) |
| Kahn com fila | O(V + E) | Auxiliar O(V) |
| DFS com caminho | O(V + E) | Auxiliar O(V) |
| Busca de dependentes | O(V + E) no pior caso | Auxiliar O(V) |
| Resolução de versões | Pode ser exponencial nas combinações de versões | Depende da estratégia de ramos e cópias de requisitos |

As três primeiras consultas de grafo não tornam linear o resolvedor completo. Medir separadamente leitura, resolução, ordenação, detecção de ciclos e desenho. A atividade apresenta uma pilha conceitual; uma implementação que materialize todos os ramos pode usar mais memória que outra que gere candidatos sob demanda.

## 9. Rastreabilidade e validação

A matriz abaixo relaciona comportamento, vista principal e evidência a verificar. É um plano de validação, não um registro de aprovação da versão final.

| Requisitos | Casos de uso / vistas | Evidência esperada |
| --- | --- | --- |
| RF01–RF02 | UC01–UC02; domínio e sequência de planejamento | Entradas inválidas rejeitadas e base inicial consistente. |
| RF03–RF05 | UC02; classes do núcleo e atividade | Fechamento transitivo, uma versão por nome, atualização explícita e alternativa sem resíduos. |
| RF06–RF07 | UC02–UC03; planejamento e estados | Diagnósticos distintos, caminho real de ciclo e ordem válida para todas as arestas. |
| RF08–RF10 | UC04; sequência de transação e estados | Instalados intactos durante preparação, confirmação final e bloqueio de plano desatualizado. |
| RF11 | UC05; núcleo e componentes | Dependentes corretos, ordem inversa e ausência de remoção efetiva. |
| RF12–RF13 | UC03 e UC06; casos de uso e componentes | Inspeção visual, JSON coerente, PNG legível e erro de escrita apresentado. |
| RF14 | UC02; planejamento, atividade e estados | Limite produz inconclusivo e nenhuma operação executável. |
| RN01–RN03 | Núcleo e componentes | Algoritmos próprios, núcleo sem janela e análise de custos compatível com o código. |
| RN04–RN06 | Documentação e materiais de entrega | Origem dos dados, experimentos reproduzíveis, UML atualizada e materiais acadêmicos completos. |

Complementar os cenários de referência com grafo vazio, vértice isolado, laço, ciclo desconexo e ciclo com dependentes externos. Validar ordem pelas relações de precedência, sem impor uma única sequência possível. Para transações, incluir zero operações, uma operação, falha intermediária, reinício, alteração de pedido, alteração de base e avanço após conclusão.

Os testes atuais estão em [test_packages.py](../../prototypes/networkx_preview/test_packages.py) e [test_preview.py](../../prototypes/networkx_preview/test_preview.py). A segunda suíte cobre o exemplo histórico de tarefas; seus resultados não representam cobertura adicional do núcleo final de pacotes.

Nos experimentos, variar nomes, versões por nome, quantidade de arestas, compartilhamento e tipos de conflito. Fixar sementes, registrar ambiente e versões, repetir medições e reportar dispersão. Comparações com NetworkX devem ficar isoladas do funcionamento final. Não há medições novas de desempenho nesta documentação.

As figuras foram renderizadas e revisadas conforme o [registro de revisão](revisao-dos-diagramas.md). Essa verificação cobre os artefatos de modelagem, não executa testes da aplicação.

## 10. Execução e demonstração

As instruções seguintes executam o **protótipo atual**, que requer Python 3.9 ou superior, NetworkX e Matplotlib nas versões registradas em [requirements.txt](../../prototypes/networkx_preview/requirements.txt).

Na raiz do repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r prototypes/networkx_preview/requirements.txt
python -m prototypes.networkx_preview
```

Para percorrer os principais resultados:

| Cenário | Resultado demonstrado |
| --- | --- |
| `desktop` | Plano viável com dependências compartilhadas. |
| `versoes` | Restrições de versão incompatíveis. |
| `conflito` | Incompatibilidade declarada entre pacotes. |
| `ausente` | Dependência inexistente no catálogo. |
| `ciclo` | Dependência circular. |
| `upgrade` | Atualização explicitamente solicitada. |
| `instalado` | Bloqueio por preservar uma versão instalada. |
| `alternativa` | Retrocesso para outra versão viável. |

Exemplo de seleção de cenário e comando de testes, a executar no ambiente preparado:

```bash
python -m prototypes.networkx_preview --cenario versoes
MPLBACKEND=Agg python -m unittest prototypes.networkx_preview.test_packages prototypes.networkx_preview.test_preview -v
```

Uma demonstração pode começar com o plano `desktop`, preparar um pacote e mostrar que os instalados ainda não mudaram, concluir e inspecionar o resultado. Em seguida, comparar incompatibilidade de versões com ciclo e mostrar a alternativa viável. A análise de remoção e a exportação encerram o percurso. Ao trocar de cenário, o protótipo restaura sua base de demonstração.

## 11. Evolução e entrega acadêmica

| Etapa | Resultado esperado |
| --- | --- |
| Grafo próprio | Listas de adjacência, Kahn, DFS e dependentes validados isoladamente. |
| Separação do núcleo | Extrair resolução, sessão, transação e análise de remoção conforme os contratos. |
| Integração | Conectar interface e entrada/saída e substituir também o layout e desenho dependentes de NetworkX. |
| Validação | Preservar os cenários, acrescentar casos de borda e realizar experimentos reproduzíveis. |
| Documentação final | Ajustar UML aos nomes e APIs efetivamente implementados e registrar responsabilidades reais. |
| Entrega | Relatório SBC de 12–15 páginas, slides, apresentação de 10 minutos, vídeo de 12–18 minutos e pacote exigido pelo enunciado. |

O planejamento acadêmico completo está em [agent.md](../../agent.md), referenciado ao [TP.pdf](../../TP.pdf). Confirmar prazo e procedimentos no Canvas. Não atribuir responsabilidades ou contribuições fictícias; registrar as tarefas e os commits efetivos de cada integrante. Cada membro deve cumprir sua própria entrega.

O relatório deve explicar o problema, a modelagem, os algoritmos, a correção, os custos, os dados, os experimentos e as limitações. Escolher figuras legíveis dentro do limite de páginas; esta documentação técnica não precisa ser copiada integralmente para o relatório.

## 12. Referências e manutenção

| Artefato | Uso |
| --- | --- |
| [Modelagens principais](modelagens-principais.md) | Galeria e explicações das oito vistas. |
| [Requisitos](requisitos.md) e [casos de uso](casos-de-uso.md) | Especificação temática de comportamentos e critérios. |
| [Arquitetura](arquitetura.md) e [comportamento](comportamento.md) | Comparação com classes atuais e vistas introdutórias. |
| [Guia de notação](guia-de-notacao.md) | Leitura e escrita de UML, Mermaid e PlantUML. |
| [Revisão](revisao-dos-diagramas.md) | Conferência das relações, cardinalidades e correções visuais. |
| [Guia do protótipo](../prototipo-networkx/README.md) | Interface atual e imagens dos cenários. |
| [Gerador das figuras](gerar_diagramas.py) | Reprodução local dos PNGs e SVGs. |

As referências oficiais de sintaxe e semântica estão no guia de notação. O conjunto de figuras usa PlantUML 1.2026.4; o comando e o hash do JAR estão na seção de reprodução junto aos diagramas. Não é necessário baixar dependências para simplesmente ler as imagens incluídas.

Ao mudar uma regra, atualizar os requisitos e casos de uso afetados, os contratos, as fontes `.puml` e esta consolidação; regenerar as figuras e revisar o resultado visual. Ao mudar apenas o layout, preservar a semântica das relações e conferir cardinalidades e rótulos. Registrar separadamente revisão de documentos, renderização, execução de testes e medições para manter claras as evidências disponíveis.

