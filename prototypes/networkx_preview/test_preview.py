"""Verificação dos fluxos do protótipo, incluindo renderização sem janela."""

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .app import EXAMPLES, Preview
from .model import Project


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.project = Project.load(EXAMPLES / "sem_ciclo.json")

    def test_order_contains_all_tasks_and_respects_every_dependency(self):
        order = self.project.order()
        self.assertEqual(set(order), set(self.project.graph))
        self.assertEqual(len(order), len(set(order)))
        positions = {task: index for index, task in enumerate(order)}
        for source, target in self.project.graph.edges:
            self.assertLess(positions[source], positions[target])

    def test_simulation_respects_prerequisites_and_stops(self):
        for _ in self.project.graph:
            previous = set(self.project.completed)
            task = self.project.advance()
            self.assertTrue(set(self.project.graph.predecessors(task)) <= previous)
        self.assertIsNone(self.project.advance())

    def test_cycle_path_is_real_and_blocks_all_execution(self):
        project = Project.load(EXAMPLES / "com_ciclo.json")
        project.add_task("ISOLADA", "Tarefa livre")
        cycle = project.cycle()
        self.assertTrue(cycle)
        self.assertEqual(cycle[0][0], cycle[-1][1])
        for source, target in cycle:
            self.assertTrue(project.graph.has_edge(source, target))
        self.assertNotIn("F", {task for edge in cycle for task in edge})
        with self.assertRaises(ValueError):
            project.advance()
        self.assertEqual(project.completed, [])

    def test_edit_invalidates_simulation_and_removal_cleans_edges(self):
        self.project.advance()
        self.project.add_dependency("C", "D")
        self.assertEqual(self.project.completed, [])
        self.project.remove_task("E")
        self.assertTrue(all("E" not in edge for edge in self.project.graph.edges))
        self.assertEqual(set(self.project.order()), set(self.project.graph))

    def test_duplicate_edge_does_not_change_simulation(self):
        self.project.advance()
        count = self.project.graph.number_of_edges()
        self.project.add_dependency("A", "B")
        self.assertEqual(count, self.project.graph.number_of_edges())
        self.assertEqual(self.project.completed, ["A"])

    def test_invalid_inputs_do_not_change_existing_graph(self):
        count = (len(self.project.graph), self.project.graph.number_of_edges())
        operations = [
            lambda: self.project.add_task("A", "Repetida"),
            lambda: self.project.add_task("", "Sem ID"),
            lambda: self.project.add_task("X", ""),
            lambda: self.project.add_dependency("A", "INEXISTENTE"),
            lambda: self.project.remove_task("INEXISTENTE"),
            lambda: self.project.remove_dependency("B", "A"),
        ]
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()
            self.assertEqual(count, (len(self.project.graph), self.project.graph.number_of_edges()))

    def test_invalid_json_structure_is_rejected(self):
        for data in [[], {}, {"tarefas": {}, "dependencias": []},
                     {"tarefas": ["A"], "dependencias": []},
                     {"tarefas": [], "dependencias": [{"origem": "A", "destino": "B"}]}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                Project.from_dict(data)

    def test_json_round_trip_preserves_tasks_descriptions_and_edges(self):
        self.project.add_task("G", "Revisão técnica", "Conferir documentação")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "projeto.json"
            self.project.save(path)
            restored = Project.load(path)
        self.assertEqual(dict(self.project.graph.nodes(data=True)), dict(restored.graph.nodes(data=True)))
        self.assertEqual(set(self.project.graph.edges), set(restored.graph.edges))

    def test_empty_isolated_self_loop_and_disconnected_cycle(self):
        project = Project()
        self.assertEqual(project.order(), [])
        self.assertIsNone(project.advance())
        project.add_task("A", "Isolada")
        self.assertEqual(project.advance(), "A")
        project.add_task("B", "Outra componente")
        project.add_dependency("B", "B")
        self.assertEqual(project.cycle(), [("B", "B")])
        with self.assertRaises(ValueError):
            project.advance()
        project.remove_dependency("B", "B")
        self.assertEqual(set(project.order()), {"A", "B"})


class PreviewTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_rendering_valid_cycle_empty_and_self_loop(self):
        projects = [Project.load(EXAMPLES / name) for name in ["sem_ciclo.json", "com_ciclo.json"]]
        projects.append(Project())
        loop = Project()
        loop.add_task("A", "Autodependência")
        loop.add_dependency("A", "A")
        projects.append(loop)
        with tempfile.TemporaryDirectory() as directory:
            for index, project in enumerate(projects):
                with self.subTest(index=index):
                    preview = Preview(project, interactive=False)
                    path = Path(directory) / f"preview-{index}.png"
                    preview.fig.savefig(path)
                    self.assertGreater(path.stat().st_size, 1000)
                    plt.close(preview.fig)

    def test_interactive_controls_edit_advance_and_recover_from_cycle(self):
        preview = Preview(Project.load(EXAMPLES / "sem_ciclo.json"))
        preview._advance()
        self.assertEqual(preview.project.completed, ["A"])
        preview.task_id.set_val("G")
        preview.task_name.set_val("Revisão")
        preview._add_task()
        self.assertEqual(preview.project.completed, [])
        preview.source.set_val("F")
        preview.target.set_val("G")
        preview._add_edge()
        self.assertTrue(preview.project.graph.has_edge("F", "G"))
        preview.refresh()
        preview._example("com_ciclo")
        with self.assertRaises(ValueError):
            preview._advance()
        preview.source.set_val("E")
        preview.target.set_val("B")
        preview._remove_edge()
        self.assertFalse(preview.project.cycle())
        preview._advance()
        preview.refresh()
        self.assertEqual(preview.project.completed, ["A"])


if __name__ == "__main__":
    unittest.main()
