# Requisitos e critérios de aceitação

Status: especificação inicial baseada no protótipo e no [guia acadêmico](../../agent.md). A coluna de situação distingue comportamento existente de trabalho para a versão final; não é um registro de testes executados nesta revisão.

## Problema e fronteiras

Um usuário solicita pacotes de um catálogo. O DepGraph considera as versões já instaladas, procura versões compatíveis e apresenta um plano de instalação ou um diagnóstico. A execução prepara operações em memória e só confirma o novo estado ao concluir a transação.

O usuário da interface é o único ator externo. Catálogo, resolvedor e sistema instalado simulado são partes da aplicação. Não existe comunicação com APT, sistema operacional para instalação, repositório remoto ou serviço de autenticação.

## Requisitos funcionais

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

## Regras do domínio

- **RD01 — Direção:** A → B significa que B depende de A. Conflitos são restrições separadas das arestas de precedência.
- **RD02 — Versões:** de um a três componentes numéricos, comparados numericamente. `1`, `1.0` e `1.0.0` são equivalentes.
- **RD03 — Restrições:** o modelo aceita intervalos com condições combinadas. A entrada textual atual de pedidos aceita uma condição por item separado por vírgula; não presumir suporte ao mesmo formato de intervalo nessa entrada.
- **RD04 — Política de busca:** preferir versões mais altas e retornar uma solução viável. Não há garantia de solução ótima, atualização mínima ou menor volume de download.
- **RD05 — Conflitos:** basta que uma das versões declare uma incompatibilidade aplicável à outra para impedir coexistência.
- **RD06 — Ciclos:** rejeitar ciclos por exigir precedência estrita, mesmo que gerenciadores reais adotem outras regras.
- **RD07 — Estado preservado:** todos os pacotes instalados participam da validação; não remover automaticamente um pacote para viabilizar o pedido.
- **RD08 — Diagnóstico:** uma falha de busca pode mostrar uma tentativa representativa; não equivale a enumerar todas as causas possíveis.

## Requisitos técnicos e acadêmicos

| ID | Critério |
| --- | --- |
| RN01 | Usar estrutura de grafo e processamento próprios na versão final; NetworkX fica isolado no protótipo ou em comparações de desempenho. |
| RN02 | Executar o núcleo sem janela, permitindo testes e experimentos independentes da interface. |
| RN03 | Implementar Kahn, DFS e busca de dependentes em O(V + E), sem alterar o grafo original durante análise. Medir o backtracking separadamente, pois pode ser exponencial. |
| RN04 | Registrar fontes dos dados, transformação, ambiente, sementes e repetições dos experimentos; não apresentar catálogo sintético como dados reais de Linux. |
| RN05 | Manter interface gráfica, UML coerente com o código e contribuições individuais identificáveis no Git. |
| RN06 | Produzir relatório LaTeX/SBC de 12–15 páginas, slides, apresentação de 10 minutos, vídeo de 12–18 minutos e pacote de entrega conforme o enunciado. |

## Evidências a produzir

Os testes de referência estão em [test_packages.py](../../prototypes/networkx_preview/test_packages.py). A migração deve preservar os cenários e acrescentar testes específicos da estrutura própria: grafo vazio, vértice isolado, laço, componentes desconexas, ciclo com dependentes externos e invariância do grafo após as consultas.

Na revisão final, verificar RF01–RF14 com testes ou demonstrações reproduzíveis. Para RN03, registrar análise dos algoritmos e medições efetivas. Para RN05–RN06, conferir os artefatos entregues. Ainda não há uma matriz completa de resultados da versão final.

## Fora do escopo inicial

Instalação real, downloads, scripts de manutenção, pacotes virtuais, múltiplas arquiteturas, sintaxe completa Debian/RPM, dependências opcionais, alternativas com `|`, remoção efetiva e resolução automática por desinstalação. Persistência de estado entre execuções não é requisito atual; exportar relatório não equivale a salvar e restaurar uma sessão.
