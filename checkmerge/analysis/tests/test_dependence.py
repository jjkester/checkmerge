import unittest

from checkmerge import app
from checkmerge.analysis.dependence import DependenceAnalysis
from checkmerge.ir import Node, Dependency, DependencyType


class DependenceAnalysisTestCase(unittest.TestCase):
    def setUp(self):
        self.ancestor = Node(typ="FunctionDef", label="calc", children=[
            Node(typ="FunctionParam", label="a"),
            Node(typ="FunctionParam", label="b"),
            Node(typ="BasicBlock", children=[
                Node(typ="VariableDef", label="c", children=[
                    Node(typ="BinaryOperator", label="+", children=[
                        Node(typ="VariableRef", label="a"),
                        Node(typ="VariableRef", label="b"),
                    ]),
                ]),
                Node(typ="FunctionCall", label="printf", children=[
                    Node(typ="StringLiteral"),
                    Node(typ="VariableRef", label="c"),
                ]),
                Node(typ="Return", children=[
                    Node(typ="VariableRef", label="c"),
                ], is_memory_operation=True),
            ]),
        ])

        self.ancestor[2, 0, 0, 0].add_dependencies(Dependency(self.ancestor[0], DependencyType.REFERENCE),
                                                   Dependency(self.ancestor[0], DependencyType.FLOW))
        self.ancestor[2, 0, 0, 1].add_dependencies(Dependency(self.ancestor[1], DependencyType.REFERENCE),
                                                   Dependency(self.ancestor[1], DependencyType.FLOW))
        self.ancestor[2, 1, 1].add_dependencies(Dependency(self.ancestor[2, 0], DependencyType.REFERENCE),
                                                Dependency(self.ancestor[2, 0], DependencyType.FLOW))
        self.ancestor[2, 2, 0].add_dependencies(Dependency(self.ancestor[2, 0], DependencyType.REFERENCE),
                                                Dependency(self.ancestor[2, 1, 1], DependencyType.INPUT))

        self.branch1 = Node(typ="FunctionDef", label="calc", children=[
            Node(typ="FunctionParam", label="a"),
            Node(typ="FunctionParam", label="b"),
            Node(typ="BasicBlock", children=[
                Node(typ="VariableDef", label="c", children=[
                    Node(typ="BinaryOperator", label="-", children=[
                        Node(typ="BinaryOperator", label="+", children=[
                            Node(typ="VariableRef", label="a"),
                            Node(typ="VariableRef", label="b"),
                        ]),
                        Node(typ="IntegerLiteral", label="1"),
                    ]),
                ]),
                Node(typ="FunctionCall", label="printf", children=[
                    Node(typ="StringLiteral"),
                    Node(typ="VariableRef", label="c"),
                ]),
                Node(typ="Return", children=[
                    Node(typ="VariableRef", label="c"),
                ], is_memory_operation=True),
            ]),
        ])

        self.branch1[2, 0, 0, 0, 0].add_dependencies(Dependency(self.branch1[0], DependencyType.REFERENCE),
                                                     Dependency(self.branch1[0], DependencyType.FLOW))
        self.branch1[2, 0, 0, 0, 1].add_dependencies(Dependency(self.branch1[1], DependencyType.REFERENCE),
                                                     Dependency(self.branch1[1], DependencyType.FLOW))
        self.branch1[2, 1, 1].add_dependencies(Dependency(self.branch1[2, 0], DependencyType.REFERENCE),
                                               Dependency(self.branch1[2, 0], DependencyType.FLOW))
        self.branch1[2, 2, 0].add_dependencies(Dependency(self.branch1[2, 0], DependencyType.REFERENCE),
                                               Dependency(self.branch1[2, 1, 1], DependencyType.INPUT))

        self.branch2 = Node(typ="FunctionDef", label="calc", children=[
            Node(typ="FunctionParam", label="a"),
            Node(typ="FunctionParam", label="b"),
            Node(typ="BasicBlock", children=[
                Node(typ="VariableDef", label="c", children=[
                    Node(typ="BinaryOperator", label="+", children=[
                        Node(typ="VariableRef", label="a"),
                        Node(typ="VariableRef", label="b"),
                    ]),
                ]),
                Node(typ="FunctionCall", label="printf", children=[
                    Node(typ="StringLiteral"),
                    Node(typ="VariableRef", label="c"),
                ]),
                Node(typ="Return", children=[
                    Node(typ="BinaryOperator", label="-", children=[
                        Node(typ="VariableRef", label="c"),
                        Node(typ="IntegerLiteral", label="1"),
                    ]),
                ], is_memory_operation=True),
            ]),
        ])

        self.branch2[2, 0, 0, 0].add_dependencies(Dependency(self.branch2[0], DependencyType.REFERENCE),
                                                  Dependency(self.branch2[0], DependencyType.FLOW))
        self.branch2[2, 0, 0, 1].add_dependencies(Dependency(self.branch2[1], DependencyType.REFERENCE),
                                                  Dependency(self.branch2[1], DependencyType.FLOW))
        self.branch2[2, 1, 1].add_dependencies(Dependency(self.branch2[2, 0], DependencyType.REFERENCE),
                                               Dependency(self.branch2[2, 0], DependencyType.FLOW))
        self.branch2[2, 2, 0, 0].add_dependencies(Dependency(self.branch2[2, 0], DependencyType.REFERENCE),
                                                  Dependency(self.branch2[2, 1, 1], DependencyType.INPUT))

    def test_branch1_branch2(self):
        """Tests the dependence analysis between the ancestor and a modification."""
        config = app.CheckMerge().build_config().diff(self.branch1, self.branch2).analyze(DependenceAnalysis)
        changes = config.changes()
        analysis = list(config.analysis())

        self.assertEqual(1, len(analysis))

        change_set = set(analysis[0].changes)

        self.assertEqual({
            changes.changes_by_node[self.branch1[2, 0, 0]],
            changes.changes_by_node[self.branch1[2, 2]],
            changes.changes_by_node[self.branch2[2, 2]],
        }, change_set)
