"""This module contains all of the CFG nodes types."""
from collections import namedtuple

from ..helper_visitors import LabelVisitor, VarsVisitor
from ast import NodeVisitor
from collections import defaultdict

ControlFlowNode = namedtuple(
    'ControlFlowNode',
    (
        'test',
        'last_nodes',
        'break_statements'
    )
)


class IgnoredNode():
    """Ignored Node sent from an ast node that should not return anything."""
    pass


class ConnectToExitNode():
    """A common type between raise's and return's, used in return_handler."""
    pass


        

class ObjectRepresentation():
    def __init__(self, name):
        self.name = name
        self.fields = []
        self.earlier_nodes = []
        self.parent = None


def print_obj(obj, iteration=0):
    if iteration == 0:
        print("-----------BEGIN--------------")
    print("   "*iteration + "name: " + obj.name)
    if obj.parent:
        print("   "*iteration + "parent: " + obj.parent.name)
    print("   "*iteration + "earlier_nodes: ")
    for node in obj.earlier_nodes:
        print("   "*iteration, node['earlier_node'], "|", node['field'])
    for field in obj.fields:
        print_obj(field, iteration+1)
    if iteration == 0:
        print("------------END--------------")

def create_object(lhs):
    tmp = lhs.split(".")
    name = tmp.pop(0)
    obj = ObjectRepresentation(name)
    obj2 = obj
    while len(tmp) > 0:
        name = tmp.pop(0)
        tmp_obj = ObjectRepresentation(name)
        tmp_obj.parent = obj2
        obj2.fields.append(tmp_obj)
        obj2 = tmp_obj
        #print("parent: ", obj2.parent.name)
    return obj

class Node():
    """A Control Flow Graph node that contains a list of
    ingoing and outgoing nodes and a list of its variables."""

    def __init__(self, label, ast_node, *, test=None, line_number=None, path):
        """Create a Node that can be used in a CFG.

        Args:
            label(str): The label of the node, describing its expression.
            line_number(Optional[int]): The line of the expression of the Node.
        """
        self.label = label
        self.ast_node = ast_node
        if line_number:
            self.line_number = line_number
        elif ast_node:
            self.line_number = ast_node.lineno
        else:
            self.line_number = None
        self.path = path
        self.ingoing = list()
        self.outgoing = list()
        self.if_statements_seen = list()
        self.else_statements_seen = list()
        self.test = test
        self.original_variables = list()
        self.right_hand_side_fields = list()
        self.left_hand_side_fields = list()
        self.fields = dict()

    def as_dict(self):
        return {
            'label': self.label.encode('utf-8').decode('utf-8'),
            'line_number': self.line_number,
            'path': self.path,
        }

    def connect(self, successor):
        """Connect this node to its successor node by
        setting its outgoing and the successors ingoing."""
        if isinstance(self, ConnectToExitNode) and not isinstance(successor, EntryOrExitNode):
            return

        self.outgoing.append(successor)
        successor.ingoing.append(self)

    def connect_predecessors(self, predecessors):
        """Connect all nodes in predecessors to this node."""
        for n in predecessors:
            self.ingoing.append(n)
            n.outgoing.append(self)

    def __str__(self):
        """Print the label of the node."""
        return ''.join((' Label: ', self.label))

    def __repr__(self):
        """Print a representation of the node."""
        # label = ' '.join(('Label: ', self.label))
        # line_number = 'Line number: ' + str(self.line_number)
        # outgoing = ''
        # ingoing = ''
        # if self.ingoing:
        #     ingoing = ' '.join(('ingoing:\t', str([x.label for x in self.ingoing])))
        # else:
        #     ingoing = ' '.join(('ingoing:\t', '[]'))

        # if self.outgoing:
        #     outgoing = ' '.join(('outgoing:\t', str([x.label for x in self.outgoing])))
        # else:
        #     outgoing = ' '.join(('outgoing:\t', '[]'))

        # return '\n' + '\n'.join((label, line_number, ingoing, outgoing))

        return ''.join((' Label: ', self.label))
    
class BreakNode(Node):
    """CFG Node that represents a Break statement."""

    def __init__(self, ast_node, *, path):
        super().__init__(
            self.__class__.__name__,
            ast_node,
            path=path
        )


class IfNode(Node):
    """CFG Node that represents an If statement."""

    def __init__(self, test_node, ast_node, *, path):
        label_visitor = LabelVisitor()
        label_visitor.visit(test_node)
        # vars_visitor = VarsVisitor()
        # vars_visitor.visit(test_node)
        self.variables = list()

        super().__init__(
            'if ' + label_visitor.result + ':',
            ast_node,
            # test=vars_visitor.result,
            path=path
        )


class TryNode(Node):
    """CFG Node that represents a Try statement."""

    def __init__(self, ast_node, *, path):
        super().__init__(
            'try:',
            ast_node,
            path=path
        )


class EntryOrExitNode(Node):
    """CFG Node that represents an Exit or an Entry node."""

    def __init__(self, label):
        super().__init__(label, None, line_number=None, path=None)


class RaiseNode(Node, ConnectToExitNode):
    """CFG Node that represents a Raise statement."""

    def __init__(self, ast_node, *, path):
        label_visitor = LabelVisitor()
        label_visitor.visit(ast_node)

        super().__init__(
            label_visitor.result,
            ast_node,
            path=path
        )


class AssignmentNode(Node):
    """CFG Node that represents an assignment."""

    def __init__(self, label, left_hand_side, ast_node, right_hand_side_variables, *, line_number=None, path):
        """Create an Assignment node.

        Args:
            label(str): The label of the node, describing the expression it represents.
            left_hand_side(str): The variable on the left hand side of the assignment. Used for analysis.
            ast_node(_ast.Assign, _ast.AugAssign, _ast.Return or None)
            right_hand_side_variables(list[str]): A list of variables on the right hand side.
            line_number(Optional[int]): The line of the expression the Node represents.
            path(string): Current filename.
        """
        super().__init__(label, ast_node, line_number=line_number, path=path)
        self.left_hand_side = left_hand_side
        self.right_hand_side_variables = right_hand_side_variables
        self.obj = create_object(left_hand_side)

    def __str__(self):
        """Print the label of the node."""
        return ''.join((' Label: ', self.label))
        
    def __repr__(self):
        output_string = super().__repr__()
        return output_string


class TaintedNode(AssignmentNode):
    """CFG Node that represents a tainted node.

    Only created in framework_adaptor.py and only used in `identify_triggers` of vulnerabilities.py
    """
    pass


class RestoreNode(AssignmentNode):
    """Node used for handling restore nodes returning from function calls."""

    def __init__(self, label, left_hand_side, right_hand_side_variables, *, line_number, path):
        """Create a Restore node.

        Args:
            label(str): The label of the node, describing the expression it represents.
            left_hand_side(str): The variable on the left hand side of the assignment. Used for analysis.
            right_hand_side_variables(list[str]): A list of variables on the right hand side.
            line_number(Optional[int]): The line of the expression the Node represents.
            path(string): Current filename.
        """
        super().__init__(label, left_hand_side, None, right_hand_side_variables, line_number=line_number, path=path)


class BBorBInode(AssignmentNode):
    """Node used for handling restore nodes returning from blackbox or builtin function calls."""

    def __init__(self, label, left_hand_side, ast_node, right_hand_side_variables, *, line_number, path, func_name):
        """Create a Restore node.

        Args:
            label(str): The label of the node, describing the expression it represents.
            left_hand_side(str): The variable on the left hand side of the assignment. Used for analysis.
            right_hand_side_variables(list[str]): A list of variables on the right hand side.
            line_number(Optional[int]): The line of the expression the Node represents.
            path(string): Current filename.
            func_name(string): The string we will compare with the blackbox_mapping in vulnerabilities.py
        """
        super().__init__(label, left_hand_side, ast_node, right_hand_side_variables, line_number=line_number, path=path)
        self.args = list()
        self.inner_most_call = self
        self.func_name = func_name


class AssignmentCallNode(AssignmentNode):
    """Node used for when a call happens inside of an assignment."""

    def __init__(
        self,
        label,
        left_hand_side,
        ast_node,
        right_hand_side_variables,
        *,
        line_number,
        path,
        call_node
    ):
        """Create an Assignment Call node.

        Args:
            label(str): The label of the node, describing the expression it represents.
            left_hand_side(str): The variable on the left hand side of the assignment. Used for analysis.
            ast_node
            right_hand_side_variables(list[str]): A list of variables on the right hand side.
            line_number(Optional[int]): The line of the expression the Node represents.
            path(string): Current filename.
            call_node(BBorBInode or RestoreNode): Used in connect_control_flow_node.
        """
        super().__init__(
            label,
            left_hand_side,
            ast_node,
            right_hand_side_variables,
            line_number=line_number,
            path=path
        )
        self.call_node = call_node
        self.blackbox = False


class ReturnNode(AssignmentNode, ConnectToExitNode):
    """CFG node that represents a return from a call."""

    def __init__(
        self,
        label,
        left_hand_side,
        ast_node,
        right_hand_side_variables,
        *,
        path
    ):
        """Create a return from a call node.

        Args:
            label(str): The label of the node, describing the expression it represents.
            left_hand_side(str): The variable on the left hand side of the assignment. Used for analysis.
            ast_node
            right_hand_side_variables(list[str]): A list of variables on the right hand side.
            path(string): Current filename.
        """
        super().__init__(
            label,
            left_hand_side,
            ast_node,
            right_hand_side_variables,
            line_number=ast_node.lineno,
            path=path
        )


class YieldNode(AssignmentNode):
    """CFG Node that represents a yield or yield from.

    The presence of a YieldNode means that a function is a generator.
    """
    pass
