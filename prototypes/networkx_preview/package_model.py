"""Resolvedor didático de pacotes. Usa grafos do NetworkX nesta exploração."""

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

import networkx as nx


def version_key(version):
    """Versões numéricas simplificadas, não o formato de versões do dpkg."""
    if not isinstance(version, str) or not re.fullmatch(r"\d+(?:\.\d+){0,2}", version):
        raise ValueError(f"Versão inválida: {version!r}. Use números como 1.0 ou 2.1.3.")
    parts = tuple(int(part) for part in version.split("."))
    return parts + (0,) * (3 - len(parts))


def package_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*", name):
        raise ValueError(f"Nome de pacote inválido: {name!r}.")
    return name


def constraints(spec):
    if not isinstance(spec, str):
        raise ValueError("A restrição de versão deve ser um texto.")
    if spec.strip() in ("", "*"):
        return []
    result = []
    for item in spec.split(","):
        match = re.fullmatch(r"\s*(>=|<=|==|=|>|<)\s*(\d+(?:\.\d+){0,2})\s*", item)
        if not match:
            raise ValueError(f"Restrição de versão inválida: {spec!r}.")
        result.append((match[1], version_key(match[2])))
    return result


@dataclass(frozen=True)
class Requirement:
    name: str
    spec: str = "*"

    def __post_init__(self):
        package_name(self.name)
        constraints(self.spec)

    def accepts(self, version):
        candidate = version_key(version)
        for op, target in constraints(self.spec):
            if not {">=": candidate >= target, "<=": candidate <= target,
                    ">": candidate > target, "<": candidate < target,
                    "=": candidate == target, "==": candidate == target}[op]:
                return False
        return True

    def __str__(self):
        return self.name if self.spec == "*" else f"{self.name} {self.spec}"


def read_requirement(data):
    if not isinstance(data, dict):
        raise ValueError("Cada dependência/conflito precisa de nome e, opcionalmente, versao.")
    return Requirement(data.get("nome"), data.get("versao", "*"))


def parse_requests(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Informe ao menos um pacote para instalar.")
    requests = []
    for item in text.split(","):
        match = re.fullmatch(r"\s*([a-z0-9][a-z0-9+.-]*)(?:\s*(>=|<=|==|=|>|<)\s*(\d+(?:\.\d+){0,2}))?\s*", item)
        if not match:
            raise ValueError("Use nomes separados por vírgula, como desktop-suite, libcore>=2.0.")
        requests.append(Requirement(match[1], f"{match[2]}{match[3]}" if match[2] else "*"))
    return requests


@dataclass(frozen=True)
class Package:
    name: str
    version: str
    depends: tuple = ()
    conflicts: tuple = ()
    description: str = ""


@dataclass
class Issue:
    kind: str
    message: str
    nodes: tuple = ()


@dataclass
class Plan:
    success: bool
    graph: nx.DiGraph
    selected: dict
    order: list
    actions: list
    issues: list
    base: dict
    requests: list
    attempts: int = 0


class Catalog:
    def __init__(self, packages):
        self.packages = {}
        for package in packages:
            package_name(package.name)
            key = version_key(package.version)
            versions = self.packages.setdefault(package.name, [])
            if any(version_key(item.version) == key for item in versions):
                raise ValueError(f"Pacote e versão duplicados: {package.name} {package.version}.")
            versions.append(package)
        for versions in self.packages.values():
            versions.sort(key=lambda package: version_key(package.version), reverse=True)

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("pacotes"), list):
            raise ValueError("O catálogo deve conter uma lista pacotes.")
        packages = []
        for item in data["pacotes"]:
            if not isinstance(item, dict):
                raise ValueError("Cada pacote deve ser um objeto JSON.")
            if not isinstance(item.get("depende", []), list) or not isinstance(item.get("conflita", []), list):
                raise ValueError("depende e conflita devem ser listas.")
            description = item.get("descricao", "")
            if not isinstance(description, str):
                raise ValueError("descricao deve ser texto.")
            packages.append(Package(package_name(item.get("nome")), item.get("versao"),
                                    tuple(read_requirement(req) for req in item.get("depende", [])),
                                    tuple(read_requirement(req) for req in item.get("conflita", [])),
                                    description))
        catalog = cls(packages)
        installed = data.get("instalados", {})
        if not isinstance(installed, dict):
            raise ValueError("instalados deve ser um mapa de nomes para versões.")
        catalog.validate_state(installed)
        return catalog, installed

    def get(self, name, version):
        for package in self.packages.get(name, []):
            if version_key(package.version) == version_key(version):
                return package
        raise ValueError(f"Pacote instalado fora do catálogo: {name} {version}.")

    def validate_state(self, installed):
        selected = {name: self.get(name, version) for name, version in installed.items()}
        graph = nx.DiGraph()
        graph.add_nodes_from(installed)
        for package in selected.values():
            for dep in package.depends:
                if dep.name not in installed or not dep.accepts(installed[dep.name]):
                    raise ValueError(f"Estado instalado inválido: {package.name} precisa de {dep}.")
                graph.add_edge(dep.name, package.name)
            for conflict in package.conflicts:
                if conflict.name in installed and conflict.accepts(installed[conflict.name]):
                    raise ValueError(f"Estado instalado inválido: {package.name} conflita com {conflict}.")
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("O estado instalado inicial deve ser acíclico neste simulador.")

    def plan(self, requests, installed, limit=20000):
        """Backtracking: uma versão por nome, sem remoção ou atualização implícita."""
        self.validate_state(installed)
        unlocked = {req.name for req in requests}
        requirements = [(req, "solicitação") for req in requests]
        requirements += [(Requirement(name, f"=={version}"), "sistema instalado")
                         for name, version in installed.items() if name not in unlocked]
        attempts = 0
        best_failure = None
        best_depth = -1
        inconclusive = None

        def graph_for(selected, reqs):
            graph = nx.DiGraph()
            for name, package in selected.items():
                graph.add_node(name, version=package.version)
            for req, owner in reqs:
                graph.add_node(req.name, version=selected[req.name].version if req.name in selected else installed.get(req.name, "?"))
                if owner not in ("solicitação", "sistema instalado"):
                    graph.add_node(owner, version=selected[owner].version if owner in selected else "?")
                    # Dependência aponta para dependente: ordem topológica instala a base primeiro.
                    if graph.has_edge(req.name, owner):
                        graph.edges[req.name, owner]["constraint"] += ", " + req.spec
                    else:
                        graph.add_edge(req.name, owner, constraint=req.spec)
            return graph

        def fail(selected, reqs, issue):
            nonlocal best_failure, best_depth, inconclusive
            depth = len(selected) + len(reqs)
            plan = Plan(False, graph_for(selected, reqs), dict(selected), [], [], [issue],
                        dict(installed), requests)
            if issue.kind == "limite":
                inconclusive = plan
            if depth >= best_depth:
                best_failure, best_depth = plan, depth
            return None

        def search(selected, reqs):
            nonlocal attempts
            if attempts >= limit or len(selected) >= 200:
                return fail(selected, reqs, Issue("limite", "Limite de busca atingido; resultado inconclusivo."))
            grouped = {}
            for req, owner in reqs:
                grouped.setdefault(req.name, []).append((req, owner))
            for name, specs in grouped.items():
                if name in selected and not all(req.accepts(selected[name].version) for req, _ in specs):
                    detail = "; ".join(f"{owner} exige {req}" for req, owner in specs)
                    available = ", ".join(item.version for item in self.packages.get(name, [])) or "nenhuma"
                    return fail(selected, reqs, Issue("versao", f"Versões incompatíveis de {name}. {detail}. Disponíveis: {available}.", (name,)))
            for package in selected.values():
                for conflict in package.conflicts:
                    other = selected.get(conflict.name)
                    if other and conflict.accepts(other.version):
                        return fail(selected, reqs, Issue("conflito", f"{package.name} {package.version} declara conflito com {other.name} {other.version}.", (package.name, other.name)))
            remaining = [name for name in grouped if name not in selected]
            if not remaining:
                graph = graph_for(selected, reqs)
                try:
                    order = list(nx.topological_sort(graph))
                except nx.NetworkXUnfeasible:
                    edges = nx.find_cycle(graph)
                    path = [edges[0][0]] + [target for _, target in edges]
                    return fail(selected, reqs, Issue("ciclo", "Dependência circular: " + " → ".join(path), tuple(path)))
                actions = [name for name in order if name not in installed or
                           version_key(installed[name]) != version_key(selected[name].version)]
                return Plan(True, graph, dict(selected), order, actions, [], dict(installed), requests)
            name = remaining[0]
            candidates = [package for package in self.packages.get(name, [])
                          if all(req.accepts(package.version) for req, _ in grouped[name])]
            if not candidates:
                detail = "; ".join(f"{owner} exige {req}" for req, owner in grouped[name])
                exists = name in self.packages
                available = ", ".join(item.version for item in self.packages.get(name, [])) or "nenhuma"
                return fail(selected, reqs, Issue("versao" if exists else "ausente",
                            f"{'Nenhuma versão compatível' if exists else 'Dependência ausente'}: {name}. {detail}. Disponíveis: {available}.", (name,)))
            for package in candidates:
                if attempts >= limit:
                    return fail(selected, reqs, Issue("limite", "Limite de busca atingido; resultado inconclusivo."))
                attempts += 1
                result = search({**selected, name: package},
                                reqs + [(dep, name) for dep in package.depends])
                if result:
                    return result
            return None

        result = search({}, requirements)
        plan = result or inconclusive or best_failure
        plan.attempts = attempts
        return plan

    def removal_impact(self, name, installed):
        if name not in installed:
            raise ValueError(f"{name} não está instalado na simulação.")
        graph = nx.DiGraph()
        graph.add_nodes_from(installed)
        for package, version in installed.items():
            for dep in self.get(package, version).depends:
                graph.add_edge(dep.name, package)
        impacted = nx.descendants(graph, name)
        order = list(reversed(list(nx.topological_sort(graph))))
        return impacted, [package for package in order if package == name or package in impacted]


@dataclass
class Session:
    catalog: Catalog
    installed: dict
    plan: object = None
    staged: list = field(default_factory=list)
    applied: bool = False
    history: list = field(default_factory=list)

    def analyze(self, text):
        requests = parse_requests(text)
        self.plan = self.catalog.plan(requests, self.installed)
        self.staged.clear()
        self.applied = False
        self.history.clear()
        return self.plan

    def advance(self):
        if not self.plan or not self.plan.success:
            raise ValueError("Instalação bloqueada: é necessário um plano válido.")
        if self.applied:
            return None
        if self.installed != self.plan.base:
            raise ValueError("O estado instalado mudou. Analise novamente antes de executar.")
        if len(self.staged) == len(self.plan.actions):
            self.applied = True
            return None
        name = self.plan.actions[len(self.staged)]
        package = self.plan.selected[name]
        temporary = {**self.installed, **{item: self.plan.selected[item].version for item in self.staged}}
        for dep in package.depends:
            if dep.name not in temporary or not dep.accepts(temporary[dep.name]):
                raise ValueError(f"Pré-requisito não satisfeito: {package.name} precisa de {dep}.")
        self.staged.append(name)
        operation = "ATUALIZAR" if name in self.installed else "INSTALAR"
        self.history.append(f"{operation} {name} {package.version}")
        if len(self.staged) == len(self.plan.actions):
            final = {item: selected.version for item, selected in self.plan.selected.items()}
            self.catalog.validate_state(final)
            self.installed = final
            self.applied = True
            self.history.append("Transação simulada concluída.")
        return name
