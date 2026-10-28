"""Interface de um gerenciador didático de pacotes inspirado no Linux."""

import argparse
import json
from pathlib import Path
import textwrap

from .package_model import Catalog, Session, version_key


CATALOG_PATH = Path(__file__).parent / "examples/pacotes.json"
SCENARIOS = {
    "desktop": ("Ambiente gráfico", "desktop-suite"),
    "versoes": ("Versões incompatíveis", "modern-browser, legacy-backup, libcore>=2.0"),
    "conflito": ("Pacotes incompatíveis", "web-server, alternate-server"),
    "ausente": ("Dependência ausente", "broken-app"),
    "ciclo": ("Dependência circular", "cycle-alpha"),
    "upgrade": ("Atualização explícita", "modern-browser, libcore>=2.0"),
    "instalado": ("Versão instalada fixa", "modern-browser"),
    "alternativa": ("Busca de outra versão", "compat-app"),
}
COLORS = {"background": "#F3F6FB", "ink": "#17243D", "muted": "#62718A",
          "installed": "#B8C4D6", "planned": "#8277E8", "root": "#3D8ECC",
          "done": "#20A582", "error": "#E66D65", "edge": "#A5B3C9"}


class PackagePreview:
    def __init__(self, catalog_path=CATALOG_PATH, scenario="desktop", requests=None):
        import matplotlib.pyplot as plt

        self.catalog, self.baseline = Catalog.load(catalog_path)
        self.session = Session(self.catalog, dict(self.baseline))
        self.widgets = []
        self.planned_text = ""
        self.inspection = None
        self.fig = plt.figure(figsize=(18, 11), facecolor=COLORS["background"])
        self.fig.canvas.manager.set_window_title("DepGraph | Gerenciador de pacotes")
        self.fig.text(.04, .946, "DepGraph", fontsize=27, weight="bold", color=COLORS["ink"])
        self.fig.text(.17, .95, "GERENCIADOR DE PACOTES / SIMULAÇÃO", fontsize=11, color=COLORS["muted"])
        self.fig.text(.04, .91, "Dependências transitivas · Versões · Incompatibilidades · Ordem de instalação",
                      fontsize=12, color=COLORS["muted"])
        self.graph_ax = self.fig.add_axes([.025, .31, .66, .54])
        self.info_ax = self.fig.add_axes([.715, .665, .26, .195])
        self.log_ax = self.fig.add_axes([.04, .065, .635, .175])
        self.message = self.fig.text(.04, .27, "", fontsize=10, color=COLORS["ink"])
        self.fig.text(.04, .025, "Catálogo sintético. Nenhum comando do Linux é executado.  |  Clique em um pacote para inspecionar.",
                      fontsize=9, color=COLORS["muted"])
        self._controls()
        self.fig.canvas.mpl_connect("pick_event", self._pick)
        self.load_scenario(scenario, requests)

    def _button(self, rect, label, action, primary=False):
        from matplotlib.widgets import Button

        ax = self.fig.add_axes(rect)
        button = Button(ax, label, color="#4867DB" if primary else "#E1E7F0", hovercolor="#BFD0F6")
        button.label.set_color("white" if primary else COLORS["ink"])
        button.label.set_fontsize(9)
        for spine in ax.spines.values():
            spine.set_visible(False)

        def invoke(_event):
            try:
                message = action()
            except (ValueError, OSError) as error:
                self.render(str(error), error=True)
            else:
                self.render(message or "")

        button.on_clicked(invoke)
        self.widgets.append(button)

    def _controls(self):
        from matplotlib.widgets import TextBox

        self.fig.text(.715, .625, "PACOTES SOLICITADOS (ex.: desktop-suite)", fontsize=9, color=COLORS["muted"])
        ax = self.fig.add_axes([.715, .575, .26, .039])
        self.request_box = TextBox(ax, "", color="white", hovercolor="#EDF1FC")
        self.request_box.text_disp.set_fontsize(9)
        self.request_box.on_text_change(self._request_changed)
        self.widgets.append(self.request_box)
        self._button([.715, .525, .125, .035], "Analisar instalação", self.analyze, primary=True)
        self._button([.85, .525, .125, .035], "Próximo pacote", self.advance, primary=True)
        self._button([.715, .48, .125, .035], "Reiniciar plano", self.analyze)
        self._button([.85, .48, .125, .035], "Impacto da remoção", self.removal)
        self.fig.text(.715, .433, "CENÁRIOS DE DEMONSTRAÇÃO", fontsize=10, weight="bold", color=COLORS["ink"])
        for index, (key, (label, _)) in enumerate(SCENARIOS.items()):
            row, col = divmod(index, 2)
            self._button([.715 + col * .135, .38 - row * .047, .125, .035], label,
                         lambda key=key: self.load_scenario(key))
        self._button([.715, .145, .26, .036], "Salvar relatório JSON + imagem PNG", self.save)
        self.fig.text(.715, .116, "Instalação e atualização são simuladas.\nAs versões instaladas ficam fixas até serem\nsolicitadas explicitamente no pedido.",
                      fontsize=9, color=COLORS["muted"], va="top", linespacing=1.5)

    def _request_changed(self, text):
        if text != self.planned_text:
            self.message.set_text("Pedido alterado. Clique em Analisar instalação antes de avançar.")
            self.message.set_color(COLORS["muted"])
            self.fig.canvas.draw_idle()

    def load_scenario(self, key, requests=None):
        self.session = Session(self.catalog, dict(self.baseline))
        self.request_box.set_val(requests if requests is not None else SCENARIOS[key][1])
        self.analyze()
        self.render(f"Cenário: {SCENARIOS[key][0]}. O sistema simulado voltou ao estado inicial.")

    def analyze(self):
        plan = self.session.analyze(self.request_box.text)
        self.planned_text = self.request_box.text
        self.inspection = None
        return "Plano válido. Avance para preparar cada pacote." if plan.success else "Transação bloqueada. Consulte o diagnóstico."

    def advance(self):
        if self.request_box.text != self.planned_text:
            raise ValueError("O pedido mudou. Analise novamente antes de instalar.")
        self.inspection = None
        name = self.session.advance()
        if name is None:
            return "Não há operações pendentes. O sistema simulado está atualizado para este plano."
        return (f"Transação concluída: {name} foi o último pacote." if self.session.applied
                else f"Preparado: {name}. O estado instalado só muda ao concluir toda a transação.")

    def removal(self):
        name = self.request_box.text.strip()
        impacted, order = self.catalog.removal_impact(name, self.session.installed)
        self.inspection = [f"IMPACTO DA REMOÇÃO: {name}",
                           f"Dependentes afetados ({len(impacted)}): " + (", ".join(sorted(impacted)) or "nenhum"),
                           "Ordem de remoção em cascata: " + " → ".join(order),
                           "Somente análise: nenhum pacote foi removido."]
        return "Impacto calculado. Veja a análise no painel inferior."

    def save(self):
        destination = Path("outputs/prototipo-networkx")
        destination.mkdir(parents=True, exist_ok=True)
        plan = self.session.plan
        report = {
            "pedido": self.planned_text, "pedido_editado": self.request_box.text,
            "plano_valido": plan.success, "instalados": self.session.installed,
            "selecionados": {name: package.version for name, package in plan.selected.items()},
            "ordem_instalacao": plan.actions, "preparados": self.session.staged,
            "transacao_concluida": self.session.applied, "tentativas": plan.attempts,
            "diagnosticos": [{"tipo": issue.kind, "mensagem": issue.message} for issue in plan.issues],
            "historico": self.session.history,
        }
        (destination / "pacotes.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.fig.savefig(destination / "pacotes.png", dpi=150, facecolor=self.fig.get_facecolor())
        return f"Relatório e imagem salvos em {destination}/."

    def _pick(self, event):
        if event.artist is not getattr(self, "node_artist", None) or not len(event.ind):
            return
        name = self.node_order[event.ind[0]]
        selected = self.session.plan.selected.get(name)
        available = self.catalog.packages.get(name, [])
        package = selected or (available[0] if available else None)
        self.inspection = [f"PACOTE: {name}",
                           "Versões no catálogo: " + (", ".join(item.version for item in available) or "ausente"),
                           "Versão instalada: " + self.session.installed.get(name, "não instalado")]
        if package:
            self.inspection += [f"Metadados de {package.name} {package.version}",
                                "Depende de: " + ("; ".join(map(str, package.depends)) or "nenhum"),
                                "Conflita com: " + ("; ".join(map(str, package.conflicts)) or "nenhum")]
        self.render(f"Inspecionando {name}.")

    def render(self, message="", error=False):
        self._draw_graph()
        self._draw_info()
        self._draw_log()
        self.message.set_text(textwrap.fill(message, 108))
        self.message.set_color(COLORS["error"] if error else COLORS["ink"])
        self.fig.canvas.draw_idle()

    def _draw_graph(self):
        import networkx as nx
        from matplotlib.lines import Line2D

        ax = self.graph_ax
        ax.clear()
        ax.axis("off")
        plan = self.session.plan
        graph = plan.graph
        ax.set_title(f"{len(graph)} pacotes no plano  /  {graph.number_of_edges()} dependências  /  "
                     f"{len(self.session.installed)} instalados", loc="left", fontsize=11, color=COLORS["muted"], pad=18)
        if not graph:
            ax.text(.5, .5, "Nenhum pacote selecionado.", ha="center", transform=ax.transAxes)
            return
        if nx.is_directed_acyclic_graph(graph):
            positions = {name: (column, (len(layer) - 1) / 2 - row)
                         for column, layer in enumerate(nx.topological_generations(graph))
                         for row, name in enumerate(layer)}
        else:
            positions = nx.circular_layout(graph)
        roots = {req.name for req in plan.requests}
        errors = {name for issue in plan.issues for name in issue.nodes}
        staged = set(self.session.staged)
        colors = [COLORS["error"] if name in errors else
                  COLORS["done"] if name in staged else
                  COLORS["installed"] if name in self.session.installed and
                  (name not in plan.selected or version_key(self.session.installed[name]) == version_key(plan.selected[name].version)) else
                  COLORS["root"] if name in roots else COLORS["planned"] for name in graph]
        self.node_order = list(graph)
        size = 800 if len(graph) > 12 else 1300
        self.node_artist = nx.draw_networkx_nodes(graph, positions, ax=ax, node_size=size,
                                                  node_color=colors, edgecolors="white", linewidths=2)
        self.node_artist.set_picker(True)
        cycle_edges = set()
        for issue in plan.issues:
            if issue.kind == "ciclo":
                cycle_edges.update(zip(issue.nodes, issue.nodes[1:]))
        nx.draw_networkx_edges(graph, positions, ax=ax, node_size=size, arrows=True,
                               arrowsize=17, width=1.6,
                               edge_color=[COLORS["error"] if edge in cycle_edges else COLORS["edge"] for edge in graph.edges],
                               connectionstyle="arc3,rad=0.08" if cycle_edges else "arc3,rad=0")
        for issue in plan.issues:
            if issue.kind == "conflito" and len(issue.nodes) == 2:
                nx.draw_networkx_edges(graph, positions, ax=ax, edgelist=[issue.nodes],
                                       node_size=size, style="dashed", edge_color=COLORS["error"],
                                       width=2, arrows=False)
        for name, (x, y) in positions.items():
            version = graph.nodes[name].get("version", "?")
            ax.text(x, y, version, ha="center", va="center", fontsize=9, color=COLORS["ink"], weight="bold")
            ax.annotate(textwrap.fill(name, 15), (x, y), xytext=(0, -24), textcoords="offset points",
                        ha="center", va="top", fontsize=8, color=COLORS["ink"])
        ax.margins(x=.09, y=.25)
        legend = [Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS[key],
                         markersize=7, markeredgecolor="none", label=label)
                  for key, label in [("installed", "Já instalado"), ("planned", "Dependência"),
                                     ("root", "Solicitado"), ("done", "Preparado"), ("error", "Problema")]]
        ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(.5, -.035), ncol=5,
                  frameon=False, fontsize=8, labelcolor=COLORS["muted"])

    def _draw_info(self):
        ax = self.info_ax
        ax.clear()
        ax.axis("off")
        plan = self.session.plan
        title = "TRANSAÇÃO CONCLUÍDA" if self.session.applied else "PLANO VÁLIDO" if plan.success else "INSTALAÇÃO BLOQUEADA"
        ax.text(0, 1, title, fontsize=13, weight="bold", color=COLORS["done"] if plan.success else COLORS["error"], va="top")
        if plan.success:
            installs = sum(name not in plan.base for name in plan.actions)
            updates = len(plan.actions) - installs
            lines = [f"{installs} instalações  /  {updates} atualizações",
                     f"Preparados: {len(self.session.staged)} de {len(plan.actions)}",
                     f"Busca: {plan.attempts} versões examinadas"]
            if not self.session.applied and len(self.session.staged) < len(plan.actions):
                lines.append("Próximo: " + plan.actions[len(self.session.staged)])
        else:
            issue = plan.issues[0]
            lines = ["TIPO: " + issue.kind.upper(), textwrap.fill(issue.message, 47)]
        ax.text(0, .76, "\n".join(lines), fontsize=9, color=COLORS["ink"], va="top", linespacing=1.5)

    def _draw_log(self):
        ax = self.log_ax
        ax.clear()
        ax.set_facecolor("#17243D")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        plan = self.session.plan
        if self.inspection:
            lines = self.inspection
        elif self.session.history:
            lines = ["REGISTRO DA TRANSAÇÃO (últimas operações)"] + self.session.history[-5:]
        elif plan.success:
            lines = ["PLANO DE INSTALAÇÃO — dependências antes dos dependentes",
                     " → ".join(f"{name} {plan.selected[name].version}" for name in plan.actions) or "Nenhuma alteração necessária.",
                     "As versões já instaladas são preservadas, exceto quando incluídas no pedido.",
                     "Preparação em memória; o estado simulado só é atualizado ao fim da transação."]
        else:
            lines = ["DIAGNÓSTICO DO RESOLVEDOR", plan.issues[0].message,
                     "Nenhuma alteração aplicada ao sistema simulado.",
                     "Ajuste o pedido ou o catálogo e analise novamente."]
        wrapped = []
        for line in lines:
            wrapped.extend(textwrap.wrap(line, 113) or [""])
        ax.text(.02, .92, "\n".join(wrapped[:9]), color="#DCE6F7", fontsize=9,
                family="monospace", va="top", transform=ax.transAxes, linespacing=1.5, clip_on=True)


def main():
    parser = argparse.ArgumentParser(description="Gerenciador didático de pacotes com NetworkX.")
    parser.add_argument("--cenario", choices=list(SCENARIOS), default="desktop")
    parser.add_argument("--pedidos", help="Nomes e restrições, como modern-browser, libcore>=2.0.")
    parser.add_argument("--catalogo", type=Path, default=CATALOG_PATH)
    parser.add_argument("--exportar", type=Path, help="Renderizar a interface em PNG sem abrir janela.")
    parser.add_argument("--listar", action="store_true", help="Listar versões e relações do catálogo.")
    args = parser.parse_args()
    if args.exportar:
        import matplotlib
        matplotlib.use("Agg")
    try:
        if args.listar:
            catalog, _ = Catalog.load(args.catalogo)
            for name, versions in catalog.packages.items():
                for package in versions:
                    print(f"{name} {package.version} | depende: {', '.join(map(str, package.depends)) or '-'} | conflita: {', '.join(map(str, package.conflicts)) or '-'}")
            return
        preview = PackagePreview(args.catalogo, args.cenario, args.pedidos)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    import matplotlib.pyplot as plt
    if args.exportar:
        args.exportar.parent.mkdir(parents=True, exist_ok=True)
        preview.fig.savefig(args.exportar, dpi=150, facecolor=preview.fig.get_facecolor())
        plt.close(preview.fig)
        print(f"Imagem gerada: {args.exportar}")
    else:
        plt.show()
