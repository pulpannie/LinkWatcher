"""Module for finding vulnerabilities based on a definitions file."""

import ast
import json
from collections import defaultdict
from ..core.node_types import AssignmentNode, IfNode, AssignmentCallNode, ObjectRepresentation, print_obj

from ..analysis.definition_chains import build_def_use_chain, build_use_def_chain, get_if_stmt_original_variables, get_sink_original_variables, get_use_def_chains, get_real_chains
from ..analysis.lattice import Lattice
from ..core.node_types import (
    AssignmentNode,
    BBorBInode,
    IfNode,
    TaintedNode
)
from ast import Call, Name, Attribute
from ..helper_visitors import (
    CallVisitor,
    RHSVisitor,
    VarsVisitor
)
from .trigger_definitions_parser import parse, Source
from .vulnerability_helper import (
    Sanitiser,
    TriggerNode,
    Triggers,
    vuln_factory,
    VulnerabilityType
)
from ..analysis.constraint_table import constraint_table

def identify_triggers(
    cfg,
    sources,
    sinks,
    lattice,
    nosec_lines
):
    """Identify sources, sinks and sanitisers in a CFG.

    Args:
        cfg(CFG): CFG to find sources, sinks and sanitisers in.
        sources(tuple): list of sources, a source is a (source, sanitiser) tuple.
        sinks(tuple): list of sources, a sink is a (sink, sanitiser) tuple.
        nosec_lines(set): lines with # nosec whitelisting

    Returns:
        Triggers tuple with sink and source nodes and a sanitiser node dict.
    """
    assignment_nodes = filter_cfg_nodes(cfg, AssignmentNode)
    tainted_nodes = filter_cfg_nodes(cfg, TaintedNode)
    tainted_trigger_nodes = [
        TriggerNode(
            Source('Framework function URL parameter'),
            cfg_node=node
        ) for node in tainted_nodes
    ]
    sources_in_file = find_triggers(assignment_nodes, sources, nosec_lines)
    sources_in_file.extend(tainted_trigger_nodes)

    find_secondary_sources(assignment_nodes, sources_in_file, lattice)

    sinks_in_file = find_triggers(cfg.nodes, sinks, nosec_lines)

    sanitiser_node_dict = build_sanitiser_node_dict(cfg, sinks_in_file)

    return Triggers(sources_in_file, sinks_in_file, sanitiser_node_dict)


def filter_cfg_nodes(
    cfg,
    cfg_node_type
):
    tmp = [node for node in cfg.nodes if isinstance(node, cfg_node_type)]
    return tmp


def find_secondary_sources(
    assignment_nodes,
    sources,
    lattice
):
    """
        Sets the secondary_nodes attribute of each source in the sources list.

        Args:
            assignment_nodes([AssignmentNode])
            sources([tuple])
            lattice(Lattice): the lattice we're analysing.
    """
    for source in sources:
        source.secondary_nodes = find_assignments(assignment_nodes, source, lattice)


def find_assignments(
    assignment_nodes,
    source,
    lattice
):
    old = list()
    # propagate reassignments of the source node
    new = [source.cfg_node]

    while new != old:
        update_assignments(new, assignment_nodes, source.cfg_node, lattice)
        old = new

    # remove source node from result
    del new[0]

    return new


def update_assignments(
    assignment_list,
    assignment_nodes,
    source,
    lattice
):
    for node in assignment_nodes:
        for other in assignment_list:
            if node not in assignment_list and lattice.in_constraint(other, node):
                append_node_if_reassigned(assignment_list, other, node)


def append_node_if_reassigned(
    assignment_list,
    secondary,
    node
):
    if (
        secondary.left_hand_side in node.right_hand_side_variables or
        secondary.left_hand_side == node.left_hand_side
    ):
        assignment_list.append(node)


def find_triggers(
    nodes,
    trigger_words,
    nosec_lines
):
    """Find triggers from the trigger_word_list in the nodes.

    Args:
        nodes(list[Node]): the nodes to find triggers in.
        trigger_word_list(list[Union[Sink, Source]]): list of trigger words to look for.
        nosec_lines(set): lines with # nosec whitelisting

    Returns:
        List of found TriggerNodes
    """
    trigger_nodes = list()
    for node in nodes:
        if node.line_number not in nosec_lines:
            trigger_nodes.extend(iter(label_contains(node, trigger_words)))
    return trigger_nodes


def label_contains(
    node,
    triggers
):
    """Determine if node contains any of the trigger_words provided.

    Args:
        node(Node): CFG node to check.
        trigger_words(list[Union[Sink, Source]]): list of trigger words to look for.

    Returns:
        Iterable of TriggerNodes found. Can be multiple because multiple
        trigger_words can be in one node.
    """
    for trigger in triggers:
        if trigger.trigger_word in node.label:
            yield TriggerNode(trigger, node)


def build_sanitiser_node_dict(
    cfg,
    sinks_in_file
):
    """Build a dict of string -> TriggerNode pairs, where the string
       is the sanitiser and the TriggerNode is a TriggerNode of the sanitiser.

    Args:
        cfg(CFG): cfg to traverse.
        sinks_in_file(list[TriggerNode]): list of TriggerNodes containing
                                          the sinks in the file.

    Returns:
        A string -> TriggerNode dict.
    """
    sanitisers = list()
    for sink in sinks_in_file:
        sanitisers.extend(sink.sanitisers)

    sanitisers_in_file = list()
    for sanitiser in sanitisers:
        for cfg_node in cfg.nodes:
            if sanitiser in cfg_node.label:
                sanitisers_in_file.append(Sanitiser(sanitiser, cfg_node))

    sanitiser_node_dict = dict()
    for sanitiser in sanitisers:
        sanitiser_node_dict[sanitiser] = list(find_sanitiser_nodes(
            sanitiser,
            sanitisers_in_file
        ))
    return sanitiser_node_dict


def find_sanitiser_nodes(
    sanitiser,
    sanitisers_in_file
):
    """Find nodes containing a particular sanitiser.

    Args:
        sanitiser(string): sanitiser to look for.
        sanitisers_in_file(list[Node]): list of CFG nodes with the sanitiser.

    Returns:
        Iterable of sanitiser nodes.
    """
    for sanitiser_tuple in sanitisers_in_file:
        if sanitiser == sanitiser_tuple.trigger_word:
            yield sanitiser_tuple.cfg_node


def get_sink_args(cfg_node):
    if isinstance(cfg_node.ast_node, ast.Call):
        rhs_visitor = RHSVisitor()
        rhs_visitor.visit(cfg_node.ast_node)
        return rhs_visitor.result
    elif isinstance(cfg_node.ast_node, ast.Assign):
        return cfg_node.right_hand_side_variables
    elif isinstance(cfg_node, BBorBInode):
        return cfg_node.args
    else:
        vv = VarsVisitor()
        vv.visit(cfg_node.ast_node)
        return vv.result


def get_sink_args_which_propagate(sink, ast_node):
    sink_args_with_positions = CallVisitor.get_call_visit_results(sink.trigger.call, ast_node)
    sink_args = []
    kwargs_present = set()

    for i, vars in enumerate(sink_args_with_positions.args):
        kwarg = sink.trigger.get_kwarg_from_position(i)
        if kwarg:
            kwargs_present.add(kwarg)
        if sink.trigger.kwarg_propagates(kwarg):
            sink_args.extend(vars)

    for keyword, vars in sink_args_with_positions.kwargs.items():
        kwargs_present.add(keyword)
        if sink.trigger.kwarg_propagates(keyword):
            sink_args.extend(vars)

    if (
        # Either any unspecified kwarg propagates
        not sink.trigger.arg_list_propagates or
        # or there are some propagating kwargs which have not been passed by keyword
        sink.trigger.kwarg_list - kwargs_present
    ):
        sink_args.extend(sink_args_with_positions.unknown_args)
        sink_args.extend(sink_args_with_positions.unknown_kwargs)

    return sink_args


def get_vulnerability_chains(
    current_node,
    sink,
    def_use,
    chain=[]
):
    """Traverses the def-use graph to find all paths from source to sink that cause a vulnerability.

    Args:
        current_node()
        sink()
        def_use(dict):
        chain(list(Node)): A path of nodes between source and sink.
    """
    for use in def_use[current_node]:
        if use == sink:
            yield chain
        else:
            vuln_chain = list(chain)
            vuln_chain.append(use)
            yield from get_vulnerability_chains(
                use,
                sink,
                def_use,
                vuln_chain
            )
            
    #print("sink: ", sink)
    # print("current node:", current_node)
    # print("type of def_use", type(chain[0]))
    #print("chain: ", chain)

# def get_use_def_chains(
#     current_node,
#     source,
#     use_def,
#     chain=[]
# ):
#     if use_def[current_node] == []:
#         print("empty use_def")
#         print("current_node: ", current_node)
#         print("\n")
#         # use_def_chain = list(chain)
#         # use_def_chain.append(source)
#         yield chain
#     for definition in use_def[current_node]:
#         if definition == source:
#             print("[definition == source]")
#             print("")
#             print("source: ", source, "\ncurrent node: ", current_node, "\nuse_def[current_node]: ", use_def[current_node])
#             print("")            
#             print("definition: ", definition)
#             print("")
#             print("chain: ", chain)
#             print("\n\n")
#             use_def_chain = list(chain)
#             use_def_chain.append(definition)
#             yield from get_use_def_chains(
#                 definition,
#                 source,
#                 use_def,
#                 use_def_chain
#             )
#         else:
#             use_def_chain = list(chain)
#             use_def_chain.append(definition)
#             print("[inside else]")
#             print("source: ", source, "\ncurrent node: ", current_node, "\n\nuse_def[current_node]: ", use_def[current_node])
#             print("")
#             print("definition: ", definition)
#             print("")
#             print("chain: ", chain)
#             print("")
#             print("next recursive call use_def[current_node]: ", use_def[definition])
#             print("\n\n")
#             yield from get_use_def_chains(
#                 definition,
#                 source,
#                 use_def,
#                 use_def_chain
#             )



# def get_use_def_chains(
#     current_node,
#     sink,
#     use_def,
#     chain=defaultdict(list)
# ):
#     if use_def[current_node] == []:
#         if current_node not in chain['original_node']:
#             chain['original_node'].append(current_node)
#         #for lhs in current_node.left_hand_side:
#         if current_node.left_hand_side not in chain['original_variables']:
#             chain['original_variables'].append(current_node.left_hand_side)
#         return chain
    
#     for definition in use_def[current_node]:
#         if(definition not in chain[current_node]):
#             chain[current_node].append(definition)
#         chain = get_use_def_chains(
#             definition,
#             use_def,
#             chain
#         )

#     return chain

def how_vulnerable(
    chain,
    blackbox_mapping,
    sanitiser_nodes,
    potential_sanitiser,
    blackbox_assignments,
    interactive,
    vuln_deets
):
    """Iterates through the chain of nodes and checks the blackbox nodes against the blackbox mapping and sanitiser dictionary.

    Note: potential_sanitiser is the only hack here, it is because we do not take p-use's into account yet.
    e.g. we can only say potentially instead of definitely sanitised in the path_traversal_sanitised_2.py test.

    Args:
        chain(list(Node)): A path of nodes between source and sink.
        blackbox_mapping(dict): A map of blackbox functions containing whether or not they propagate taint.
        sanitiser_nodes(set): A set of nodes that are sanitisers for the sink.
        potential_sanitiser(Node): An if or elif node that can potentially cause sanitisation.
        blackbox_assignments(set[AssignmentNode]): set of blackbox assignments, includes the ReturnNode's of BBorBInode's.
        interactive(bool): determines if we ask the user about blackbox functions not in the mapping file.
        vuln_deets(dict): vulnerability details.

    Returns:test
        A VulnerabilityType depending on how vulnerable the chain is.
    """
    for i, current_node in enumerate(chain):
        if current_node in sanitiser_nodes:
            vuln_deets['sanitiser'] = current_node
            vuln_deets['confident'] = True
            return VulnerabilityType.SANITISED, interactive

        if isinstance(current_node, BBorBInode):
            if current_node.func_name in blackbox_mapping['propagates']:
                continue
            elif current_node.func_name in blackbox_mapping['does_not_propagate']:
                return VulnerabilityType.FALSE, interactive
            elif interactive:
                user_says = input(
                    'Is the return value of {} with tainted argument "{}" vulnerable? ([Y]es/[N]o/[S]top asking)'.format(
                        current_node.label,
                        chain[i - 1].left_hand_side
                    )
                ).lower()
                if user_says.startswith('s'):
                    interactive = False
                    vuln_deets['unknown_assignment'] = current_node
                    return VulnerabilityType.UNKNOWN, interactive
                if user_says.startswith('n'):
                    blackbox_mapping['does_not_propagate'].append(current_node.func_name)
                    return VulnerabilityType.FALSE, interactive
                blackbox_mapping['propagates'].append(current_node.func_name)
            else:
                vuln_deets['unknown_assignment'] = current_node
                return VulnerabilityType.UNKNOWN, interactive

    if potential_sanitiser:
        vuln_deets['sanitiser'] = potential_sanitiser
        vuln_deets['confident'] = False
        return VulnerabilityType.SANITISED, interactive

    return VulnerabilityType.TRUE, interactive


def get_tainted_node_in_sink_args(
    sink_args,
    nodes_in_constraint
):
    if not sink_args:
        return None
    # Starts with the node closest to the sink
    for node in nodes_in_constraint:
        if node.left_hand_side in sink_args:
            return node

def get_if_stmt_variables(if_stmt, prev=False):

    #if_chain = get_use_def_chains(if_stmt, use_def, defaultdict(list))    
    if isinstance(if_stmt, IfNode):
        if_stmt = if_stmt.ast_node.test
        result = get_if_stmt_variables(if_stmt)
        if isinstance(result, str):
            return [result]
        return result
    if isinstance(if_stmt, ast.keyword):
        return get_if_stmt_variables(if_stmt.value)
    if isinstance(if_stmt, Call):
        result = (get_if_stmt_variables(if_stmt.func, prev=True))
        if isinstance(result, list):
            arr = result
        else:
            arr = [result]
        for args in if_stmt.args:
            result = get_if_stmt_variables(args)
            arr.append(result)
        for keyword in if_stmt.keywords:
            result = get_if_stmt_variables(keyword)
            arr.append(result)
        return arr
    if isinstance(if_stmt, Attribute):
        a = get_if_stmt_variables(if_stmt.value) 
        if prev:
            return a
        if isinstance(a, str):
            a = a + "." + if_stmt.attr
            return a
        if isinstance(if_stmt, list):
            return a
    if isinstance(if_stmt, Name):
        return if_stmt.id

def get_earliest(node, chain):
    earlier_nodes = chain[node]
    for earlier_node in earlier_nodes:
        if earlier_node['earlier_node']:
            yield from get_earliest(earlier_node['earlier_node'], chain)
        else:
            yield node

def get_vulnerability(
    source,
    sink,
    triggers,
    lattice,
    cfg,
    interactive,
    blackbox_mapping
):
    """Get vulnerability between source and sink if it exists.

    Uses triggers to find sanitisers.

    Note: When a secondary node is in_constraint with the sink
              but not the source, the secondary is a save_N_LHS
              node made in process_function in expr_visitor.

    Args:
        source(TriggerNode): TriggerNode of the source.
        sink(TriggerNode): TriggerNode of the sink.
        triggers(Triggers): Triggers of the CFG.
        lattice(Lattice): the lattice we're analysing.
        cfg(CFG): .blackbox_assignments used in is_unknown, .nodes used in build_def_use_chain
        interactive(bool): determines if we ask the user about blackbox functions not in the mapping file.
        blackbox_mapping(dict): A map of blackbox functions containing whether or not they propagate taint.

    Returns:
        A Vulnerability if it exists, else None
    """
   # print("source: ", source)
    vuln_deets = {
        # 'source': source.cfg_node,
        # 'source_trigger_word': source.trigger_word,
        'source': source,
        'source_trigger_word': sink.trigger_word,
        'sink': sink.cfg_node,
        'sink_trigger_word': sink.trigger_word,
        'first_node': cfg.nodes[0]
    }

    sanitiser_nodes = set()
    potential_sanitiser = None
    if sink.sanitisers:
        for sanitiser in sink.sanitisers:
            for cfg_node in triggers.sanitiser_dict[sanitiser]:
                if isinstance(cfg_node, AssignmentNode):
                    sanitiser_nodes.add(cfg_node)
                elif isinstance(cfg_node, IfNode):
                    potential_sanitiser = cfg_node

    def_use = build_def_use_chain(
        cfg.nodes,
        lattice
    )


    use_def = build_use_def_chain(
        cfg.nodes,
        lattice
    )
    sources = [source.cfg_node for source in triggers.sources]

    chain = defaultdict(lambda: defaultdict(list))
    print_obj(sink.cfg_node.obj)
    #get_use_def_chains(sink.cfg_node, sink.cfg_node, use_def, chain=defaultdict(lambda: defaultdict(int)))
    copy = get_use_def_chains(sink.cfg_node, sink.cfg_node.obj.name, sources)
    get_real_chains(sink.cfg_node, sink.cfg_node.obj.name, sources, sink.cfg_node, chain)

    print_obj(copy)

    #print("chain: ", chain)
    # for node in cfg.nodes:
    #     if isinstance(node, IfNode):
    #         node.variables = get_if_stmt_variables(node)
    #         tmp = get_if_stmt_original_variables(node, lattice, use_def, chain, sink.cfg_node)
    #         #print("tmp: ", tmp)
    #         node_summary_variables = []
    #         flag = 0
    #         for variable in tmp:
    #             if variable[0] not in [variable[0] for variable in node.original_variables]:
    #                 node.original_variables.append(variable)
    #         #print("IfNode original variables: ", node.original_variables)
    #                 flag = 1
    #                 node_summary_variables.append(variable)
    #                 if variable[0] not in [variable[0] for variable in variables_to_track]:
    #                     variables_to_track.append(variable)
    #         if flag == 1:
    #             node_summary = {"label": node.label, "file": node.path, "line_number": node.line_number, "variables": node_summary_variables}
    #             implicit_flow.append(node_summary)

    #update_sink(sink.cfg_node)

    #tainted, original_variable_fields_used = get_sink_original_variables(sink.cfg_node, chain)
    # print("SINK: ", sink.cfg_node)
    # variables_to_track = []
    # for variable in tainted_fields.values:
    #     if variable[0] not in [variable[0] for variable in sink.cfg_node.original_variables]:
    #         sink.cfg_node.original_variables.append(variable)
    #         if variable[0] not in [variable[0] for variable in variables_to_track]:
    #             variables_to_track.append(variable)
    # print("SINK original variables: ", sink.cfg_node.original_variables)
    # print("variables to track:", variables_to_track)

    # vulnerability_type, interactive = how_vulnerable(
    #     chain,
    #     blackbox_mapping,
    #     sanitiser_nodes,
    #     potential_sanitiser,
    #     cfg.blackbox_assignments,
    #     interactive,
    #     vuln_deets
    # )
    # # if vulnerability_type == VulnerabilityType.FALSE:
    # #     continue
    # vuln_deets['reassignment_nodes'] = chain
    # vuln_deets['sources'] = source
    # vuln_deets['cpython'] = {
    #     "if_statements": implicit_flow, 
    #     "tainted": tainted,
    #     "original_variable_fields_used": original_variable_fields_used
    #     }
    vuln_deets['sink_origin'] = copy
    vuln_deets['chain'] = chain
    return vuln_deets
    # return None, interactive

    return None, interactive


def find_vulnerabilities_in_cfg(
    cfg,
    definitions,
    lattice,
    blackbox_mapping,
    vulnerabilities_list,
    interactive,
    nosec_lines
):
    """Find vulnerabilities in a cfg.

    Args:
        cfg(CFG): The CFG to find vulnerabilities in.
        definitions(trigger_definitions_parser.Definitions): Source and sink definitions.
        lattice(Lattice): the lattice we're analysing.
        blackbox_mapping(dict): A map of blackbox functions containing whether or not they propagate taint.
        vulnerabilities_list(list): That we append to when we find vulnerabilities.
        interactive(bool): determines if we ask the user about blackbox functions not in the mapping file.
    """
    triggers = identify_triggers(
        cfg,
        definitions.sources,
        definitions.sinks,
        lattice,
        nosec_lines[cfg.filename]
    )

    for sink in triggers.sinks:
        #source = triggers.sources
        #for source in triggers.sources:
            # if len(source.cfg_node.label) == 1:
            #     continue
            # if source.cfg_node.line_number >= sink.cfg_node.line_number:
            #     continue
        vulnerability = get_vulnerability(
                triggers.sources,
                sink,
                triggers,
                lattice,
                cfg,
                interactive,
                blackbox_mapping
        )
        if vulnerability:
            vulnerabilities_list.append(vulnerability)


def find_vulnerabilities(
    cfg_list,
    blackbox_mapping_file,
    sources_and_sinks_file,
    interactive=False,
    nosec_lines=defaultdict(set)
):
    """Find vulnerabilities in a list of CFGs from a trigger_word_file.

    Args:
        cfg_list(list[CFG]): the list of CFGs to scan.
        blackbox_mapping_file(str)
        sources_and_sinks_file(str)
        interactive(bool): determines if we ask the user about blackbox functions not in the mapping file.
    Returns:
        A list of vulnerabilities.
    """
    vulnerabilities = list()
    definitions = parse(sources_and_sinks_file)

    with open(blackbox_mapping_file) as infile:
        blackbox_mapping = json.load(infile)
    for cfg in cfg_list:
        #print("cfg: ", cfg.nodes[0])
        find_vulnerabilities_in_cfg(
            cfg,
            definitions,
            Lattice(cfg.nodes),
            blackbox_mapping,
            vulnerabilities,
            interactive,
            nosec_lines
        )

    if interactive:
        with open(blackbox_mapping_file, 'w') as outfile:
            json.dump(blackbox_mapping, outfile, indent=4)

    return vulnerabilities
