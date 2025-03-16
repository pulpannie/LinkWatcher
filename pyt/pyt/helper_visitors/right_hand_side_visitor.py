"""Contains a class that finds all names.
Used to find all variables on a right hand side(RHS) of assignment.
"""
import ast
from collections import defaultdict

class RHSVisitor(ast.NodeVisitor):
    """Visitor collecting all names."""

    def __init__(self):
        """Initialize result as list."""
        self.result = list()
        self.object_repr = ""

    def visit_Name(self, node):
        self.result.append(node.id)

    def visit_Call(self, node):
        #print("visit_Call node: ", ast.dump(node))
        if node.args:
            for arg in node.args:
                self.visit(arg)
        if node.keywords:
            tmp = defaultdict()
            for keyword in node.keywords:
                tmp2 = tmp
                tmp = defaultdict()
                tmp[keyword.arg] = tmp2
                node.left_hand_side_fields = tmp                
                self.visit(keyword)

    def visit_IfExp(self, node):
        # The test doesn't taint the assignment
        self.visit(node.body)
        self.visit(node.orelse)

    @classmethod
    def result_for_node(cls, node):
        visitor = cls()
        visitor.visit(node)
        return visitor.result
