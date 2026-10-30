# Revisão dos diagramas principais

Revisão realizada em 30/10/2026 sobre as oito fontes PlantUML, as imagens renderizadas, os requisitos e a descrição da arquitetura proposta. A conferência separa coerência da modelagem e qualidade visual. Refere-se ao [conjunto principal](modelagens-principais.md); exemplos didáticos do guia e vistas históricas não são figuras da arquitetura final.

## Resultado por diagrama

| Diagrama | Avaliação e correção |
| --- | --- |
| 01 — Casos de uso | Ator, fronteira e seis objetivos coerentes com o escopo. Não havia cardinalidades nem sobreposição relevante. Preservado. |
| 02 — Classes do domínio | Quantidades coerentes, mas algumas eram atravessadas por setas e os dois papéis de `Requisito` ficavam próximos. Layout alterado para ELK, separando as entradas e os rótulos sem mudar os valores. |
| 03 — Classes do núcleo | A convergência de várias associações em `Catalogo` dificultava ligar cada `1` à sua seta. Layout alterado para separar as extremidades e preservar as associações. |
| 04 — Componentes | Dependências coerentes com a separação entre interface e núcleo. Layout alterado para tornar os percursos mais fáceis de acompanhar; cruzamento sem nó de junção não significa conexão entre setas. |
| 05 — Sequência de planejamento | Busca, validação e resultados coerentes. Refinado o encerramento: registrar qualquer plano e criar transação executável somente para resultado válido. |
| 06 — Sequência de transação | Preparação parcial e confirmação coerentes. Explicitado que a confirmação marca a conclusão na transação e registra o estado final como novo estado esperado. O bloqueio usa esse estado esperado, inclusive após conclusão. |
| 07 — Estados | Havia rótulos atravessando títulos de agrupamentos. Layout alterado, com estados compostos em retângulos sem abas e compartimentos vazios ocultos. Guardas, transição interna em `Concluida` e reanálise compartilhada preservadas. |
| 08 — Atividade | Resultados coerentes, mas contagem e expansão de candidatos estavam implícitas. Explicitados retirada do ramo, limite, incremento de tentativas, incorporação das dependências e preservação das alternativas. |

As cardinalidades das classes não precisaram ser alteradas para resolver a sobreposição. Os ajustes de comportamento acima detalham os contratos da proposta; não são correções já implementadas no código da aplicação.

## Conferência das cardinalidades

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

## Coerência dos fluxos

- Analisar não altera os instalados e mantém fixas as versões dos nomes não solicitados.
- Ciclo invalida uma atribuição; uma versão alternativa ainda pode produzir solução.
- Resultado inconclusivo não é prova de impossibilidade.
- Plano bloqueado ou inconclusivo não cria transação executável.
- Preparação parcial não confirma instalações. Falha de pré-requisito impede registrar o próximo pacote.
- Uma operação única pode ser preparada e confirmada no mesmo avanço. Zero operações também permite conclusão sem mudanças.
- Estado final é validado antes da aplicação. Após confirmar, torna-se o estado esperado para os próximos comandos.
- Mudanças no pedido ou no estado esperado exigem nova análise. Avançar em uma transação concluída e atual apenas informa a conclusão.
- Análise de remoção continua sendo consulta; nenhuma vista autoriza remover pacotes.

## Verificação dos artefatos

As oito fontes foram regeneradas em PNG e SVG com PlantUML 1.2026.4. A revisão incluiu leitura visual de cada figura, com atenção às extremidades das associações, cardinalidades, rótulos dos estados e limites das figuras. Também foram conferidos os arquivos gerados e os links locais.

Nas duas vistas de classes, as **15 cardinalidades** renderizadas foram comparadas às fontes. Uma conferência adicional das caixas aproximadas de texto no SVG não encontrou interseção entre esses números e outros textos. Essa checagem complementa a inspeção visual; não detecta sozinha todos os possíveis cruzamentos entre setas e letras.

A revisão confirma coerência com os requisitos e com os contratos propostos no nível de detalhe apresentado. As assinaturas conceituais e a arquitetura ainda precisam acompanhar a implementação final. Renderização e revisão visual não substituem testes do resolvedor ou validação do programa.
