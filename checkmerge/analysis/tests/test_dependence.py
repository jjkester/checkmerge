import unittest

from checkmerge import app
from checkmerge.analysis.dependence import DependenceAnalysis
from checkmerge.ir import IRNode, Dependency, DependencyType


class DependenceAnalysisTestCase(unittest.TestCase):
    def setUp(self):
        self.ancestor = IRNode(typ="FunctionDef", label="calc", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="VariableDef", label="c", children=[
                    IRNode(typ="BinaryOperator", label="+", children=[
                        IRNode(typ="VariableRef", label="a"),
                        IRNode(typ="VariableRef", label="b"),
                    ]),
                ]),
                IRNode(typ="FunctionCall", label="printf", children=[
                    IRNode(typ="StringLiteral"),
                    IRNode(typ="VariableRef", label="c"),
                ]),
                IRNode(typ="Return", children=[
                    IRNode(typ="VariableRef", label="c"),
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

        self.branch1 = IRNode(typ="FunctionDef", label="calc", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="VariableDef", label="c", children=[
                    IRNode(typ="BinaryOperator", label="-", children=[
                        IRNode(typ="BinaryOperator", label="+", children=[
                            IRNode(typ="VariableRef", label="a"),
                            IRNode(typ="VariableRef", label="b"),
                        ]),
                        IRNode(typ="IntegerLiteral", label="1"),
                    ]),
                ]),
                IRNode(typ="FunctionCall", label="printf", children=[
                    IRNode(typ="StringLiteral"),
                    IRNode(typ="VariableRef", label="c"),
                ]),
                IRNode(typ="Return", children=[
                    IRNode(typ="VariableRef", label="c"),
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

        self.branch2 = IRNode(typ="FunctionDef", label="calc", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="VariableDef", label="c", children=[
                    IRNode(typ="BinaryOperator", label="+", children=[
                        IRNode(typ="VariableRef", label="a"),
                        IRNode(typ="VariableRef", label="b"),
                    ]),
                ]),
                IRNode(typ="FunctionCall", label="printf", children=[
                    IRNode(typ="StringLiteral"),
                    IRNode(typ="VariableRef", label="c"),
                ]),
                IRNode(typ="Return", children=[
                    IRNode(typ="BinaryOperator", label="-", children=[
                        IRNode(typ="VariableRef", label="c"),
                        IRNode(typ="IntegerLiteral", label="1"),
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
