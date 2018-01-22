import os
import typing

import graphviz

from checkmerge import ir


class GraphVizFormatter(object):
    """
    Formatter for the intermediate representation (IR) that uses GraphViz. This formatter can output GraphViz source and
    render it to different image formats.
    """

    def __init__(self, name: typing.Optional[str] = None):
        """
        :param name: The name of the graph.
        """
        # Initialize fields
        self.graph = graphviz.Digraph(name)

    def add_tree(self, t: ir.Node, name: typing.Optional[str] = None,
                 dependencies: bool = False) -> "GraphVizFormatter":
        """
        Adds an IR tree to the graph. Multiple trees can be rendered in the same graph, where every tree will be a
        subgraph.

        This method is declarative and will return the same instance as it was called on.

        :param t: The tree to add.
        :param name: The name of the subgraph.
        :param dependencies: Whether to show dependencies in the graph.
        :return: The instance of the formatter.
        """
        graph = graphviz.Digraph(name=name)

        # Build graph
        for node in t.nodes:
            # Add the node, prefix label with counter
            graph.node(hex(hash(node)), label=str(node))

            # If dependencies are enabled, add them
            if dependencies:
                for dependency in node.dependencies:
                    graph.edge(hex(hash(node)), hex(hash(dependency.node)), str(dependency.type), color='red')

            # Add edges to the children (forward reference)
            for child in node.children:
                graph.edge(hex(hash(node)), hex(hash(child)))

        # Add graph to root
        self.graph.subgraph(graph)

        # Return self for declarative use
        return self

    def add_node(self, node: ir.Node, dependencies: bool = False) -> "GraphVizFormatter":
        """
        Adds a single IR node to the graph.

        This method is declarative and will return the same instance as it was called on.

        :param node: The node to add.
        :param dependencies: Whether to show dependencies in the graph.
        :return: The instance of the formatter.
        """
        self.graph.node(hex(hash(node)), label=str(node))

        if dependencies:
            for dependency in node.dependencies:
                self.graph.edge(hex(hash(node)), hex(hash(dependency.node)), str(dependency.type), color='red')

        # Return self for declarative use
        return self

    def to_graphviz(self) -> str:
        """
        :return: The GraphViz source of the graph.
        """
        return self.graph.source

    def to_svg(self) -> bytes:
        """
        Renders the graph in SVG.

        :return: The bytes of the SVG file with the rendered graph.
        """
        return self.render('svg')

    def to_png(self) -> bytes:
        """
        Renders the graph in PNG.

        :return: The bytes of the PNG file with the rendered graph.
        """
        return self.render('png')

    def render(self, format: str) -> bytes:
        """
        Renders the graph in the given format. The supported formats are decided on by the GraphViz implementation on
        the system.

        :param format: The format to render the graph in.
        :return: The bytes of the rendered graph.
        """
        return self.graph.pipe(format=format)

    def save(self, file: str) -> None:
        """
        Saves the graph to the provided file path.

        :param file: The path to the file to save the graph in.
        """
        path = os.path.split(file)
        self.graph.save(filename=path[-1], directory=os.path.join(*path[:-1]))
