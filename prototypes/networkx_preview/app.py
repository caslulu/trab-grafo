"""Janela local com Matplotlib e exportação de prévias sem interface gráfica."""

import argparse
from pathlib import Path
import textwrap

from .model import Project


EXAMPLES = Path(__file__).parent / "examples"
OUTPUT = Path("outputs/prototipo-networkx")
COLORS = {
    "background": "#F3F6FB", "ink": "#14213D", "muted": "#64748B",
    "pending": "#CBD5E1", "ready": "#4F78EE", "done": "#26A88A",
    "cycle": "#E66B63", "edge": "#9AAAC4",
}


class Preview:
    def __init__(self, project, interactive=True):
        import matplotlib.pyplot as plt

        self.project = project
        self.widgets = []  # Matplotlib precisa manter referências dos widgets.
        self.fig = plt.figure(figsize=(15, 9), facecolor=COLORS["background"])
        self.fig.canvas.manager.set_window_title("Grafos | Dependências entre tarefas")
        self.fig.text(.045, .945, "Dependências entre tarefas", fontsize=23,
                      weight="bold", color=COLORS["ink"])
        self.fig.text(.045, .908, "TEMA 9  /  EXPLORAÇÃO VISUAL COM NETWORKX",
                      fontsize=10, color=COLORS["muted"])
        self.graph_ax = self.fig.add_axes([.025, .22, .65, .63])
        self.info_ax = self.fig.add_axes([.71, .64, .25, .22])
        self.status = self.fig.text(.045, .105, "", fontsize=11,
                                    color=COLORS["ink"], va="top")
        self.fig.text(.045, .035, "A → B: B depende de A.  |  Edições reiniciam a simulação.",
                      fontsize=10, color=COLORS["muted"])
        if interactive:
            self._controls()
        else:
            self.fig.text(.71, .55, "COMO EXPLORAR", weight="bold", color=COLORS["ink"])
            self.fig.text(.71, .51,
                          "Abra a versão interativa para:\n\n"
                          "• adicionar tarefas e dependências;\n"
                          "• alternar entre exemplos;\n"
                          "• avançar a execução passo a passo;\n"
                          "• salvar o projeto e uma imagem.",
                          fontsize=11, color=COLORS["muted"], linespacing=1.8, va="top")
        self.refresh("Carregue um exemplo ou edite as tarefas para explorar o grafo.")

    def _button(self, bounds, text, action, primary=False):
        from matplotlib.widgets import Button

        ax = self.fig.add_axes(bounds)
        button = Button(ax, text,
                        color=COLORS["ready"] if primary else "#E2E8F0",
                        hovercolor="#B7C9FA")
        button.label.set_fontsize(9)
        button.label.set_color("white" if primary else COLORS["ink"])
        for spine in ax.spines.values():
            spine.set_visible(False)

        def invoke(_event):
            try:
                message = action()
            except (ValueError, OSError) as error:
                self.refresh(str(error), error=True)
            else:
                self.refresh(message)

        button.on_clicked(invoke)
        self.widgets.append(button)

    def _textbox(self, y, label):
        from matplotlib.widgets import TextBox

        self.fig.text(.71, y + .042, label, fontsize=9, color=COLORS["muted"])
        ax = self.fig.add_axes([.71, y, .25, .034])
        box = TextBox(ax, "", color="white", hovercolor="#EEF2FF")
        box.text_disp.set_fontsize(10)
        for spine in ax.spines.values():
            spine.set_edgecolor("#D7DFEC")
        self.widgets.append(box)
        return box

    def _controls(self):
        self._button([.71, .585, .12, .035], "Exemplo válido",
                     lambda: self._example("sem_ciclo"))
        self._button([.84, .585, .12, .035], "Exemplo com ciclo",
                     lambda: self._example("com_ciclo"))
        self.task_id = self._textbox(.505, "ID da tarefa (ex.: G)")
        self.task_name = self._textbox(.435, "Nome da tarefa")
        self._button([.71, .386, .12, .034], "Adicionar tarefa", self._add_task)
        self._button([.84, .386, .12, .034], "Remover pelo ID", self._remove_task)
        self.source = self._textbox(.31, "Origem / pré-requisito (ID)")
        self.target = self._textbox(.24, "Destino / dependente (ID)")
        self._button([.71, .192, .12, .034], "Adicionar relação", self._add_edge)
        self._button([.84, .192, .12, .034], "Remover relação", self._remove_edge)
        self._button([.045, .16, .19, .045], "Avançar uma tarefa", self._advance, primary=True)
        self._button([.25, .16, .16, .045], "Reiniciar simulação", self._restart)
        self._button([.425, .16, .16, .045], "Salvar JSON + PNG", self._save)

    def _example(self, name):
        self.project = Project.load(EXAMPLES / f"{name}.json")
        return "Exemplo carregado. A simulação foi reiniciada."

    def _add_task(self):
        self.project.add_task(self.task_id.text, self.task_name.text)
        return "Tarefa adicionada. A ordem e a simulação foram atualizadas."

    def _remove_task(self):
        self.project.remove_task(self.task_id.text)
        return "Tarefa e suas dependências removidas."

    def _add_edge(self):
        self.project.add_dependency(self.source.text, self.target.text)
        return "Dependência registrada. Confira o diagnóstico do grafo."

    def _remove_edge(self):
        self.project.remove_dependency(self.source.text, self.target.text)
        return "Dependência removida. Confira a nova ordem de execução."

    def _advance(self):
        task = self.project.advance()
        if task is None:
            return "Todas as tarefas foram concluídas." if self.project.graph else "Não há tarefas para executar."
        return f"Concluída: {task} — {self.project.graph.nodes[task]['nome']}."

    def _restart(self):
        self.project.restart()
        return "Simulação reiniciada. Nenhuma tarefa foi executada."

    def _save(self):
        self.project.save(OUTPUT / "projeto.json")
        self.fig.savefig(OUTPUT / "grafo.png", dpi=150, facecolor=self.fig.get_facecolor())
        return f"Projeto e imagem salvos em {OUTPUT}/."

    def refresh(self, message="", error=False):
        graph = self.project.graph
        cycle = self.project.cycle()
        order = [] if cycle else self.project.order()
        self._draw_graph(cycle)
        self._draw_info(cycle, order)
        self.status.set_text(textwrap.fill(message, 80))
        self.status.set_color(COLORS["cycle"] if error else COLORS["ink"])
        self.fig.canvas.draw_idle()

    def _draw_graph(self, cycle):
        import networkx as nx
        from matplotlib.lines import Line2D

        ax = self.graph_ax
        ax.clear()
        ax.set_facecolor(COLORS["background"])
        ax.axis("off")
        graph = self.project.graph
        ax.set_title(f"{len(graph)} tarefas    /    {graph.number_of_edges()} dependências",
                     loc="left", fontsize=12, color=COLORS["muted"], pad=14)
        if not graph:
            ax.text(.5, .5, "Adicione uma tarefa para começar.", ha="center",
                    color=COLORS["muted"], transform=ax.transAxes)
            return
        if cycle:
            positions = nx.circular_layout(graph)
        else:
            generations = list(nx.topological_generations(graph))
            positions = {
                task: (column, (len(layer) - 1) / 2 - row)
                for column, layer in enumerate(generations)
                for row, task in enumerate(layer)
            }
        cycle_nodes = {task for edge in cycle for task in edge}
        cycle_edges = set(cycle)
        completed = set(self.project.completed)
        ready = {
            task for task in graph
            if task not in completed and all(parent in completed for parent in graph.predecessors(task))
        } if not cycle else set()
        node_colors = [
            COLORS["cycle"] if task in cycle_nodes else
            COLORS["done"] if task in completed else
            COLORS["ready"] if task in ready else COLORS["pending"]
            for task in graph
        ]
        nx.draw_networkx_nodes(graph, positions, ax=ax, node_color=node_colors,
                               node_size=1500, linewidths=3, edgecolors="white")
        nx.draw_networkx_edges(
            graph, positions, ax=ax, node_size=1500, arrows=True, arrowsize=22,
            width=2, edge_color=[COLORS["cycle"] if edge in cycle_edges else COLORS["edge"]
                                 for edge in graph.edges],
            connectionstyle="arc3,rad=0.08" if cycle else "arc3,rad=0",
        )
        nx.draw_networkx_labels(graph, positions, ax=ax, labels={task: task for task in graph},
                                font_size=13, font_weight="bold", font_color=COLORS["ink"])
        for task, (x, y) in positions.items():
            ax.annotate(textwrap.fill(graph.nodes[task]["nome"], 18), (x, y),
                        xytext=(0, -34), textcoords="offset points", ha="center", va="top",
                        fontsize=10, color=COLORS["ink"])
        ax.margins(x=.17, y=.38)
        if not cycle and len(generations) == 1:
            ax.set_xlim(-1, 1)
        legend = [Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS[key],
                         markeredgecolor="none", markersize=9, label=label)
                  for key, label in [("pending", "Pendente"), ("ready", "Pronta"),
                                     ("done", "Concluída"), ("cycle", "No ciclo")]]
        ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(.5, -.03),
                  ncol=4, frameon=False, fontsize=9, labelcolor=COLORS["muted"])

    def _draw_info(self, cycle, order):
        ax = self.info_ax
        ax.clear()
        ax.axis("off")
        graph = self.project.graph
        if cycle:
            title, color = "CICLO DETECTADO", COLORS["cycle"]
            path = [cycle[0][0]] + [target for _, target in cycle]
            detail = " → ".join(path)
            body = "Execução bloqueada.\nRemova uma dependência do ciclo."
        elif graph:
            title, color = "FLUXO VÁLIDO", COLORS["done"]
            detail = "Ordem: " + " → ".join(order)
            body = f"Concluídas: {len(self.project.completed)} de {len(graph)}"
            remaining = [task for task in order if task not in self.project.completed]
            body += f"\nPróxima: {remaining[0]}" if remaining else "\nSimulação concluída."
        else:
            title, color = "GRAFO VAZIO", COLORS["muted"]
            detail, body = "Nenhuma tarefa cadastrada.", "Cadastre uma tarefa ou abra um exemplo."
        ax.text(0, .96, title, fontsize=13, weight="bold", color=color, va="top")
        ax.text(0, .72, textwrap.fill(detail, 36), fontsize=11, color=COLORS["ink"], va="top",
                clip_on=True)
        ax.text(0, .30, body, fontsize=10, color=COLORS["muted"], va="top", linespacing=1.7)


def main():
    parser = argparse.ArgumentParser(description="Protótipo visual do tema 9 com NetworkX.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--exemplo", choices=["sem_ciclo", "com_ciclo"], default="sem_ciclo")
    source.add_argument("--arquivo", type=Path, help="Projeto JSON para visualizar.")
    parser.add_argument("--exportar", type=Path, help="Salvar uma imagem PNG sem abrir janela.")
    args = parser.parse_args()
    try:
        project = Project.load(args.arquivo or EXAMPLES / f"{args.exemplo}.json")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.exportar:
        import matplotlib
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    preview = Preview(project, interactive=not args.exportar)
    if args.exportar:
        args.exportar.parent.mkdir(parents=True, exist_ok=True)
        preview.fig.savefig(args.exportar, dpi=150, facecolor=preview.fig.get_facecolor())
        plt.close(preview.fig)
        print(f"Imagem gerada: {args.exportar}")
    else:
        plt.show()
