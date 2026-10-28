"""Testes de resolução, conflitos, transações e interface de pacotes."""

import tempfile
from pathlib import Path
import unittest

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .package_app import CATALOG_PATH, SCENARIOS, PackagePreview
from .package_model import Catalog, Package, Requirement, Session, parse_requests, version_key


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.baseline = Catalog.load(CATALOG_PATH)

    def plan(self, scenario):
        return self.catalog.plan(parse_requests(SCENARIOS[scenario][1]), self.baseline)

    def test_transitive_closure_order_and_single_version_per_package(self):
        plan = self.plan("desktop")
        self.assertTrue(plan.success)
        self.assertEqual(len(plan.selected), 17)
        self.assertEqual(len(plan.actions), 15)
        self.assertIn("libpng", plan.selected)
        self.assertEqual(plan.selected["libui"].version, "1.0")
        self.assertEqual(plan.selected["libssl"].version, "1.0")
        position = {name: index for index, name in enumerate(plan.order)}
        for package in plan.selected.values():
            for dep in package.depends:
                self.assertTrue(dep.accepts(plan.selected[dep.name].version))
                self.assertLess(position[dep.name], position[package.name])

    def test_different_failure_kinds_are_distinguished_and_never_mutate_installed(self):
        for scenario, expected in [("versoes", "versao"), ("conflito", "conflito"),
                                   ("ausente", "ausente"), ("ciclo", "ciclo"), ("instalado", "versao")]:
            with self.subTest(scenario=scenario):
                plan = self.plan(scenario)
                self.assertFalse(plan.success)
                self.assertEqual(plan.issues[0].kind, expected)
                self.assertEqual(plan.actions, [])
                self.assertEqual(self.baseline, {"base-files": "1.0", "libcore": "1.0"})

    def test_conflicts_are_checked_even_when_only_one_package_declares_them(self):
        plan = self.catalog.plan(parse_requests("alternate-server, web-server"), self.baseline)
        self.assertFalse(plan.success)
        self.assertEqual(set(plan.issues[0].nodes), {"web-server", "alternate-server"})
        self.assertEqual(plan.issues[0].kind, "conflito")

    def test_cycle_is_an_actual_closed_path(self):
        plan = self.plan("ciclo")
        path = plan.issues[0].nodes
        self.assertEqual(path[0], path[-1])
        for source, target in zip(path, path[1:]):
            self.assertTrue(plan.graph.has_edge(source, target))

    def test_backtracking_discards_dependencies_of_failed_versions(self):
        plan = self.plan("alternativa")
        self.assertTrue(plan.success)
        self.assertEqual(plan.selected["compat-app"].version, "1.0")
        self.assertNotIn("missing-sdk", plan.graph)

    def test_backtracking_can_select_an_acyclic_older_version(self):
        catalog = Catalog([Package("a", "2.0", (Requirement("b"),)),
                           Package("a", "1.0"), Package("b", "1.0", (Requirement("a"),))])
        plan = catalog.plan([Requirement("a")], {})
        self.assertTrue(plan.success)
        self.assertEqual(plan.selected["a"].version, "1.0")
        self.assertEqual(set(plan.graph), {"a"})

    def test_installed_versions_are_locked_unless_explicitly_requested(self):
        self.assertFalse(self.plan("instalado").success)
        upgrade = self.plan("upgrade")
        self.assertTrue(upgrade.success)
        self.assertEqual(upgrade.selected["libcore"].version, "2.0")
        self.assertIn("libcore", upgrade.actions)

    def test_upgrading_cannot_break_an_existing_reverse_dependency(self):
        state = {**self.baseline, "libssl": "1.0", "protected-agent": "1.0"}
        plan = self.catalog.plan(parse_requests("modern-browser, libcore>=2.0, libssl>=2.0"), state)
        self.assertFalse(plan.success)
        self.assertEqual(plan.issues[0].kind, "versao")
        self.assertIn("protected-agent", plan.issues[0].message)

    def test_conflicts_with_already_installed_packages_are_rejected(self):
        session = Session(self.catalog, dict(self.baseline))
        plan = session.analyze("web-server")
        for _ in plan.actions:
            session.advance()
        result = session.analyze("alternate-server")
        self.assertFalse(result.success)
        self.assertEqual(result.issues[0].kind, "conflito")

    def test_numeric_versions_and_ranges(self):
        self.assertGreater(version_key("1.10"), version_key("1.9"))
        self.assertEqual(version_key("1"), version_key("1.0.0"))
        requirement = Requirement("lib", ">=1.5,<2.0")
        self.assertTrue(requirement.accepts("1.10"))
        self.assertFalse(requirement.accepts("2.0"))
        catalog = Catalog([Package("a", "1.0")])
        self.assertEqual(catalog.plan([Requirement("a")], {"a": "1"}).actions, [])
        for value in ["1:2.0-1", "v2", "", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                version_key(value)

    def test_invalid_requests_and_duplicate_numeric_versions_are_rejected(self):
        for text in ["", "a,,b", "a|b", "a>=invalid", "Pacote"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_requests(text)
        with self.assertRaises(ValueError):
            Catalog([Package("a", "1.0"), Package("a", "1")])
        catalog = Catalog([Package("a", "1.0", (Requirement("a"),))])
        with self.assertRaises(ValueError):
            catalog.validate_state({"a": "1.0"})

    def test_search_limit_is_inconclusive_and_does_not_claim_unsatisfiability(self):
        plan = self.catalog.plan([Requirement("desktop-suite")], self.baseline, limit=2)
        self.assertFalse(plan.success)
        self.assertEqual(plan.issues[0].kind, "limite")


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.catalog, self.baseline = Catalog.load(CATALOG_PATH)
        self.session = Session(self.catalog, dict(self.baseline))

    def test_installation_stages_packages_then_commits_only_the_complete_transaction(self):
        plan = self.session.analyze("desktop-suite")
        for _ in plan.actions[:-1]:
            self.session.advance()
            self.assertEqual(self.session.installed, self.baseline)
        self.session.advance()
        self.assertTrue(self.session.applied)
        self.assertEqual(len(self.session.installed), 17)
        self.catalog.validate_state(self.session.installed)
        self.assertIsNone(self.session.advance())

    def test_reanalysis_discards_uncommitted_operations(self):
        self.session.analyze("desktop-suite")
        self.session.advance()
        self.session.analyze("web-server")
        self.assertEqual(self.session.staged, [])
        self.assertEqual(self.session.installed, self.baseline)

    def test_blocked_and_stale_plans_cannot_execute(self):
        self.session.analyze("cycle-alpha")
        with self.assertRaises(ValueError):
            self.session.advance()
        self.session.analyze("desktop-suite")
        self.session.installed["libssl"] = "1.0"
        with self.assertRaises(ValueError):
            self.session.advance()

    def test_removal_impact_finds_transitive_dependents_in_reverse_order(self):
        plan = self.session.analyze("desktop-suite")
        for _ in plan.actions:
            self.session.advance()
        impacted, order = self.catalog.removal_impact("libcore", self.session.installed)
        self.assertIn("desktop-suite", impacted)
        self.assertIn("browser", impacted)
        self.assertNotIn("base-files", impacted)
        self.assertEqual(order[-1], "libcore")
        self.assertLess(order.index("browser"), order.index("libnet"))
        self.assertEqual(len(self.session.installed), 17)


class PackageInterfaceTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_rendering_installation_version_conflict_and_explicit_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            for scenario in ["desktop", "versoes", "conflito"]:
                with self.subTest(scenario=scenario):
                    preview = PackagePreview(scenario=scenario)
                    path = Path(directory) / f"{scenario}.png"
                    preview.fig.savefig(path)
                    self.assertGreater(path.stat().st_size, 1000)
                    plt.close(preview.fig)

    def test_modified_request_requires_reanalysis_before_advancing(self):
        preview = PackagePreview()
        preview.request_box.set_val("web-server")
        with self.assertRaises(ValueError):
            preview.advance()
        preview.analyze()
        preview.advance()
        self.assertEqual(len(preview.session.staged), 1)


if __name__ == "__main__":
    unittest.main()
