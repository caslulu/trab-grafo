"""Modelo exploratório. Os algoritmos desta versão são os do NetworkX."""

import json
from pathlib import Path

import networkx as nx


def required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} deve ser um texto não vazio.")
    return value.strip()


class Project:
    """Uma aresta A → B significa que B depende de A."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.completed = []

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("O JSON deve conter um objeto com tarefas e dependencias.")
        tasks = data.get("tarefas")
        edges = data.get("dependencias")
        if not isinstance(tasks, list) or not isinstance(edges, list):
            raise ValueError("tarefas e dependencias devem ser listas.")
        project = cls()
        for task in tasks:
            if not isinstance(task, dict):
                raise ValueError("Cada tarefa deve ser um objeto com id e nome.")
            description = task.get("descricao", "")
            if not isinstance(description, str):
                raise ValueError("A descrição da tarefa deve ser um texto.")
            project.add_task(task.get("id"), task.get("nome"), description)
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("Cada dependência deve ter origem e destino.")
            project.add_dependency(edge.get("origem"), edge.get("destino"))
        return project

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path):
        data = {
            "tarefas": [
                {"id": task, **attributes}
                for task, attributes in self.graph.nodes(data=True)
            ],
            "dependencias": [
                {"origem": source, "destino": target}
                for source, target in self.graph.edges
            ],
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def add_task(self, task_id, name, description=""):
        task_id = required_text(task_id, "ID")
        name = required_text(name, "Nome")
        if task_id in self.graph:
            raise ValueError(f"Já existe uma tarefa com ID {task_id}.")
        self.graph.add_node(task_id, nome=name, descricao=description)
        self.restart()

    def remove_task(self, task_id):
        task_id = required_text(task_id, "ID")
        self._require_task(task_id)
        self.graph.remove_node(task_id)
        self.restart()

    def _require_task(self, task_id):
        if task_id not in self.graph:
            raise ValueError(f"A tarefa {task_id} não existe.")

    def add_dependency(self, source, target):
        source = required_text(source, "Origem")
        target = required_text(target, "Destino")
        self._require_task(source)
        self._require_task(target)
        if self.graph.has_edge(source, target):
            return  # Aresta repetida não altera o grafo nem a simulação.
        self.graph.add_edge(source, target)
        self.restart()

    def remove_dependency(self, source, target):
        source = required_text(source, "Origem")
        target = required_text(target, "Destino")
        if not self.graph.has_edge(source, target):
            raise ValueError(f"A dependência {source} → {target} não existe.")
        self.graph.remove_edge(source, target)
        self.restart()

    def cycle(self):
        try:
            return list(nx.find_cycle(self.graph))
        except nx.NetworkXNoCycle:
            return []

    def order(self):
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("Existe um ciclo. Corrija as dependências antes de simular.") from None

    def advance(self):
        order = self.order()  # Bloqueia inclusive se outra componente estiver livre.
        if len(self.completed) == len(order):
            return None
        task = order[len(self.completed)]
        if not all(parent in self.completed for parent in self.graph.predecessors(task)):
            raise ValueError("Os pré-requisitos da tarefa ainda não foram concluídos.")
        self.completed.append(task)
        return task

    def restart(self):
        self.completed.clear()
