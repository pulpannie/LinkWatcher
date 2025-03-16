from collections import defaultdict

from copy import deepcopy
from .constraint_table import constraint_table
from ..core.node_types import AssignmentNode, IfNode, AssignmentCallNode, ObjectRepresentation, print_obj
import ast

def get_constraint_nodes(
    node,
    lattice
):
    for n in lattice.get_elements(constraint_table[node]):
        if n is not node:
            yield n


def build_def_use_chain(
    cfg_nodes,
    lattice
):
    def_use = defaultdict(list)
    # For every node
    for node in cfg_nodes:
        # That's a definition
        if isinstance(node, AssignmentNode):
            # Get the uses
            for variable in node.right_hand_side_variables:
                # Loop through most of the nodes before it
                for earlier_node in get_constraint_nodes(node, lattice):
                    # and add them to the 'uses list' of each earlier node, when applicable
                    # 'earlier node' here being a simplification
                    if variable in earlier_node.left_hand_side:
                        def_use[earlier_node].append(node)
    return def_use


def check_conditions(lhs, rhs, cur_lhs):
    rhs_with_fields = rhs.split(".")
    rhs_is_attribute = True if len(rhs_with_fields) > 1 else False
    lhs_with_fields = lhs.split(".")
    lhs_is_attribute = True if len(lhs_with_fields) > 1 else False
    cur_lhs_with_fields = cur_lhs.split(".")
    cur_lhs_is_attribute = True if len(cur_lhs_with_fields) > 1 else False
    return rhs_with_fields, rhs_is_attribute, lhs_with_fields, lhs_is_attribute, cur_lhs_with_fields, cur_lhs_is_attribute

def get_str_from_attribute(attr):
    tmp = attr.value
    passed_variable = ""
    while (isinstance(tmp, ast.Attribute)):
        passed_variable = "." + tmp.attr + passed_variable
        tmp = tmp.value
    if (isinstance(tmp, ast.Name)):
        passed_variable = tmp.id + passed_variable
    return passed_variable

def get_name_from_attribute(attr):
    tmp = attr.value
    while (isinstance(tmp, ast.Attribute)):
        tmp = tmp.value
    if (isinstance(tmp, ast.Name)):
        return tmp.id

def change_object_earlier_nodes(earlier_obj, earlier_node):
    tmp_obj = deepcopy(earlier_obj)
    if tmp_obj.earlier_nodes:
        tmp_obj.earlier_nodes = [earlier_node]
    for i in range(0, len(tmp_obj.fields)):
        tmp_obj.fields[i] = change_object_earlier_nodes(tmp_obj.fields[i], earlier_node)
    return tmp_obj

def get_or_extend_object(obj, name, rhs, earlier_node, change=0, seen=""):
    if name == seen + obj.name:
        tmp2 = {'earlier_node': earlier_node, 'field': rhs}
        if tmp2 not in obj.earlier_nodes and change:
            obj.earlier_nodes.append(tmp2)
        return obj
    else:
        for i, field in enumerate(obj.fields):
            cor_obj = get_or_extend_object(field, name, rhs, earlier_node, change, seen+obj.name+".")
            if cor_obj:
                return cor_obj
        if seen+obj.name in name:
            tmp = name.replace(seen+obj.name+".", '')
            tmp = tmp.split(".")
            while len(tmp) > 0:
                name = tmp.pop(0)
                tmp_obj = ObjectRepresentation(name)
                tmp_obj.parent = obj
                obj.fields.append(tmp_obj)
                obj = tmp_obj
                if len(tmp) == 0 and change:
                     tmp2 = {'earlier_node': earlier_node, 'field': rhs}
                     if tmp2 not in obj.earlier_nodes:
                        obj.earlier_nodes.append(tmp2)
            return obj
    return None

def loop_through_and_compare(lhs_obj, rhs_obj, earlier_node):

    tmp = []
    for i, field in enumerate(rhs_obj.fields):
        tmp.append(field.name)
    for i, field in enumerate(lhs_obj.fields):
        if field.name in tmp:
            index = tmp.index(field.name)          
            loop_through_and_compare(field, rhs_obj.fields[index], earlier_node)
        else:
            #create and add field obj to rhs_obj.fields
            tmp_obj = ObjectRepresentation(field.name)
            rhs_obj_fields = rhs_obj.fields
            tmp_obj.parent = rhs_obj
            rhs_obj_fields.append(tmp_obj)
            loop_through_and_compare(field, tmp_obj, earlier_node)


#def replace_earlier_nodes(obj, earlier_node):
    # for field in obj.fields:
    #     if earlier_node not in field.earlier_nodes:
    #         field.earlier_nodes.append(earlier_node)
        # replace_earlier_nodes(field, earlier_node)
    # if earlier_node not in obj.earlier_nodes:
    #     obj.earlier_nodes.append(earlier_node)
    #print("obj?")
    #print_obj(obj)


def update_object(lhs_obj, rhs_obj, earlier_node):

    loop_through_and_compare(lhs_obj, rhs_obj, earlier_node)
    #replace_earlier_nodes(rhs_obj, earlier_node)


def build_use_def_chain(
        cfg_nodes,
        lattice
):
    use_def = defaultdict(dict)
    for node in cfg_nodes:
        if isinstance(node, AssignmentNode):
            variables = node.right_hand_side_variables
            print("label:", node.label, type(node), type(node.ast_node),"\nvariables:",variables)
        # elif isinstance(node, IfNode):
        #     variables = node.variables
            for rhs in variables:
                for earlier_node in get_constraint_nodes(node, lattice):
                    lhs = earlier_node.left_hand_side
                    cur_lhs = node.left_hand_side
                    if not check_diff_variable(rhs, lhs):

                        """Handle cur_lhs"""
                        mod_cur_lhs = cur_lhs 
                        if isinstance(node.ast_node, ast.AugAssign):
                            if not check_diff_variable(cur_lhs, rhs):
                                mod_cur_lhs = rhs
                        if isinstance(node.ast_node, ast.Call):
                            #get argument belonging to rhs.
                            passed_variable = None
                            keyword_arg = None
                            for keyword in node.ast_node.keywords:
                                passed_variable = get_str_from_attribute(keyword)
                                if passed_variable == rhs:
                                    if keyword.arg:
                                        keyword_arg = keyword.arg
                                    break
                            if passed_variable and passed_variable == rhs:
                                mod_cur_lhs = cur_lhs + "." + keyword_arg
                        if isinstance(node.ast_node, ast.Call):
                            tmp = node.ast_node.func
                            if isinstance(tmp, ast.Attribute):
                                call_object = ""
                                rhs_object = ""
                                tmp = tmp.value
                                while isinstance(tmp, ast.Attribute):
                                    if tmp.attr == "objects":
                                        call_object = ""
                                    elif call_object == "":
                                        call_object = tmp.attr
                                    else:
                                        call_object = tmp.attr + "." + call_object
                                    if rhs_object == "":
                                        rhs_object = tmp.attr
                                    else:
                                        rhs_object = tmp.attr + "." + rhs_object
                                    tmp = tmp.value
                                if isinstance(tmp, ast.Name):
                                    if call_object != "":
                                        call_object = tmp.id + "." + call_object
                                    else:
                                        call_object = tmp.id
                                    if rhs_object == "":
                                        rhs_object = tmp.id
                                    else:
                                        rhs_object = tmp.id + "." + rhs_object
                                if rhs == rhs_object:
                                    rhs = call_object
                        """second case: lhs=item.cart, rhs=item"""
                        if len(lhs) > len(rhs) and rhs in lhs:
                            lhs_obj = get_or_extend_object(earlier_node.obj, lhs, lhs, earlier_node)
                            rhs_obj= get_or_extend_object(node.obj, mod_cur_lhs + lhs.replace(rhs, ''), lhs, earlier_node, 1)

                        else:
                            """case where cur_lhs is attribute"""
                            """Check for cases where RHS and LHS don't match 1:1"""
                            """first case: LHS == RHS 1:1"""
                            """third case: lhs=item, rhs=item.cart"""
                            lhs_obj= get_or_extend_object(earlier_node.obj, rhs, rhs, earlier_node)
                            rhs_obj= get_or_extend_object(node.obj, mod_cur_lhs, rhs, earlier_node, 1)
                        
                        update_object(lhs_obj, rhs_obj, earlier_node)
                            

                        
    return use_def
 

def check_diff_variable(rhs, lhs):
    rhs = rhs.split(".")
    lhs = lhs.split(".")
    min_len = min(len(rhs), len(lhs))
    skip = False
    
    # ex) check for definitions of 하위 attributes
    if len(rhs) <= len(lhs):
        for i in range(len(rhs)):
            if rhs[i] != lhs[i]:
                skip = True
    # ex) user.username used and user defined
    else:
        for i in range(len(lhs)):
            # print("rhs, lhs: ",rhs[i], lhs[i])
            if rhs[i] != lhs[i]:
                skip = True
    return skip

def get_all_values(d, k=""):
    for key, value in d.items():
        if isinstance(value, dict):
            k = key + "."
            yield from get_all_values(value, k)
        if isinstance(value, list):
            yield k + key, value

#returns node.fields[k] where k is the field we are looking for.
def get_field(d, field, sink_field, k2=""):
    for key, value in d.items():
        if isinstance(value, dict):
            if field == k2 + key:
                field = "traversing"
                sink_field = sink_field.split(".")
                sink_field = sink_field[0] + "."
                #print("traversing:", sink_field, d, value)
                sink_field = sink_field + key + "."
            k2 = k2 + key + "."
            yield from get_field(value, field, sink_field, k2)
        if isinstance(value, list):
            if field == k2 + key:
                yield {'sink_field': sink_field, 'definitions': value}
            elif field == "traversing":
                sink_field = sink_field + key
                yield {'sink_field': sink_field, 'definitions': value}


def traverse_use_def(node, field, sink_field, key=None, sources=[]):
    #print("node.fields", node.fields, field)
    arr = []
    for tmp in get_field(node.fields, field, sink_field):
        if tmp:
            arr.append(tmp)
    #print("arr:", arr)
    for fields in arr:
        for definition in fields['definitions']:
            if definition['earlier_node']:
                key = definition['field']
                traverse_use_def(definition['earlier_node'], definition['field'], fields['sink_field'], key, sources)
            else:
                sources.append({"sink_field": fields['sink_field'], "source_node": node, "field": key})
    return sources
 
def get_fields_with_earlier_nodes(obj, name):
    for field in obj.fields:
        yield from get_fields_with_earlier_nodes(field, name+"."+field.name)
    if obj.earlier_nodes:
        yield obj, name

def get_object(obj, name, seen=""):
    if name == seen + obj.name:
        return obj
    else:
        for i, field in enumerate(obj.fields):
            cor_obj = get_object(field, name, seen+obj.name+".")
            if cor_obj:
                return cor_obj

def convert_object_to_dict(obj):
    obj_dict = defaultdict(list)
    for earlier_node in obj.earlier_nodes:
        obj_dict['earlier_nodes'].append(earlier_node)
    for field in obj.fields:
        obj_dict['fields'].append(convert_object_to_dict(field))
    obj_dict = {obj.name: obj_dict}
    return obj_dict

def loop_and_change(obj, sub_obj):
    if not obj or not sub_obj:
        return
    if sub_obj.earlier_nodes:
        for e in sub_obj.earlier_nodes:
            obj.earlier_nodes.append(e)
    tmp = []
    for i, field in enumerate(obj.fields):
        tmp.append(field.name)
    for i, field in enumerate(sub_obj.fields):
        if field.name in tmp:
            index = tmp.index(field.name)
            # if not obj.fields[index].earlier_nodes and field.earlier_nodes:
            #     obj.fields[index].earlier_nodes = field.earlier_nodes
            
            loop_and_change(obj.fields[index], field)

def get_use_def_chains(
    current_node,
    name,
    sources,
    addition=""
):
    #print("USE-DEF CHAIN", current_node, name)
    
    obj = current_node.obj
    counter = 0
    copy = deepcopy(obj)
    if isinstance(current_node.ast_node, ast.Call) and isinstance(current_node.ast_node.func, ast.Attribute):
        if get_str_from_attribute(current_node.ast_node.func)+"."+ current_node.ast_node.func.attr == "form.cleaned_data.get" or get_str_from_attribute(current_node.ast_node.func)+"."+ current_node.ast_node.func.attr == "self.request.POST.get":
            addition = current_node.ast_node.args[0].s
    
    #if current_node in sources:
    for field, field_name in get_fields_with_earlier_nodes(obj, obj.name):
        print_obj(field)
        counter = counter + 1
        for i, earlier_node in enumerate(field.earlier_nodes):
            tmp = get_use_def_chains(earlier_node['earlier_node'], earlier_node['field'], sources, addition)                
            #already recursively looked, delete from copy.earlier_nodes list
            a = get_object(copy, field_name)
            if not a:
                continue
            for i, n in enumerate(a.earlier_nodes):
                if n['earlier_node'].label == earlier_node['earlier_node'].label:
                    a.earlier_nodes.pop(i)
                    break
            #change subobj of copy to tmp (recursion result)
            loop_and_change(a, tmp)

    if counter == 0:
        obj = ObjectRepresentation(name)
        if addition:
            name = name+"."+addition
        obj.earlier_nodes = [{'earlier_node': current_node, 'field': name}]      
        return obj

    return copy

def get_all_fields(obj, seen=""):
    for field in obj.fields:
        yield from get_all_fields(field, seen+"."+field.name)
    yield seen

def get_real_chains(
    current_node,
    name,
    sources,
    sink,
    chain,
    seen="",
    addition="",
    check=[],
    arr=[],
    scounter=0
):
    
    if sink == current_node:
        check = []
        for name1 in get_all_fields(current_node.obj, current_node.obj.name):
            check.append(name1)
    
    obj = get_object(current_node.obj, name) 
    counter = 0

    if isinstance(current_node.ast_node, ast.Call) and isinstance(current_node.ast_node.func, ast.Attribute):
        if get_str_from_attribute(current_node.ast_node.func)+"."+ current_node.ast_node.func.attr == "form.cleaned_data.get" or get_str_from_attribute(current_node.ast_node.func)+"."+ current_node.ast_node.func.attr == "self.request.POST.get":
            addition = current_node.ast_node.args[0].s

    for field, field_name in get_fields_with_earlier_nodes(obj, obj.name):     
        counter = counter + 1
        for i, earlier_node in enumerate(field.earlier_nodes):
            if sink == current_node:
                seen = field_name
                ret  = get_real_chains(earlier_node['earlier_node'], earlier_node['field'], sources, sink, chain, seen, addition, check, arr)
            elif check and seen + "." + field.name in check:
                ret = get_real_chains(earlier_node['earlier_node'], earlier_node['field'], sources, sink, chain, seen + "." + field.name, addition, check, arr)
            else:
                ret = get_real_chains(earlier_node['earlier_node'], earlier_node['field'], sources, sink, chain, seen, addition, check, arr)
            if ret:
                for k,v in chain.items():
                    tmp = {'earlier_node': earlier_node['earlier_node'], 'field': earlier_node['field']}
                    if tmp not in v[current_node]:
                        v[current_node].append({'earlier_node': earlier_node['earlier_node'], 'field': earlier_node['field']})

    if check and seen in check:
        if addition:
            name = name+"."+addition
        arr = defaultdict(list)
        arr[current_node].append({'earlier_node': {}, 'field': name}) 
        if not chain[seen]:
            chain[seen] = arr
        if chain[seen]:
            for field, field_name in get_fields_with_earlier_nodes(obj, obj.name):
                for i, earlier_node in enumerate(field.earlier_nodes):
                    if earlier_node['earlier_node'] in chain[seen]:
                        return chain[seen] 
            tmp = {'earlier_node': {}, 'field': name}
            if tmp not in chain[seen][current_node]:
                chain[seen][current_node].append(tmp)
        return chain[seen]
    return chain[seen]


def old_get_use_def_chains(
    current_node,
    sink,
    use_def,
    sink_variable = None,
    chain=defaultdict(lambda: defaultdict(list)),
    counter = 0
):
    #for variable in current_node.right_hand_side_variables:
    for variable in use_def[current_node]:
        #Case control for Constructor Method Calls
        for definition in use_def[current_node][variable]:
            # print("MIDDLE NODE current node, definition: ", current_node, current_node.line_number, definition, definition.line_number)
            # print("chain: ", chain)
            if(definition not in chain[current_node]):
                if(variable in chain[current_node]):
                    chain[current_node][variable].append(definition)
                else:
                    chain[current_node][variable] = [definition]
            if current_node == sink:
                sink_variable = variable
            counter = counter + 1
            chain = get_use_def_chains(
                current_node=definition,
                sink=sink,
                use_def=use_def,
                sink_variable=sink_variable,
                chain=chain,
                counter=counter
            )
    if use_def[current_node] == {}:
        if sink_variable not in chain['original_node']:
                chain['original_node'][sink_variable] = [current_node]
        else:
            if current_node not in chain['original_node'][sink_variable]:
                chain['original_node'][sink_variable].append(current_node)
        #for lhs in current_node.left_hand_side:
        if sink_variable not in chain['original_variables']:
            chain['original_variables'][sink_variable] = [current_node.left_hand_side]
        else:
            if current_node.left_hand_side not in chain['original_variables'][sink_variable]:
                chain['original_variables'][sink_variable].append(current_node.left_hand_side)
        # print("END NODE current node", current_node, current_node.line_number)
        return chain

    return chain

def update_sink(
        sink
):
    if_stmts = sink.if_statements_seen
    for stmt in if_stmts:
        for variable in stmt.variables:
            sink.right_hand_side_variables.append(variable)


def get_field_sensitive_sources(
        source,
        sink_chain,
        sink_variable
):
    field_sensitive_originals = defaultdict(lambda: defaultdict(list))
    for node in source:
        for sink_chain_node in sink_chain:
            if(sink_chain_node == "original_node" or sink_chain_node == "original_variables"):
                continue
            for variable in sink_chain_node.right_hand_side_variables:
                rhs = variable.split(".")
                lhs = node.left_hand_side.split(".")
                min_len = min(len(rhs), len(lhs))
                skip = False
                for i in range(min_len): 
                    if rhs[i] != lhs[i]:
                        skip = True
                if not skip:
                    tmp = [variable, sink_chain_node.path, sink_chain_node.line_number]
                    if variable not in [var[0] for var in field_sensitive_originals[node.left_hand_side]]:
                        field_sensitive_originals[node]['sink_field'] = sink_variable
                        field_sensitive_originals[node]['line_number'] = node.line_number
                        field_sensitive_originals[node]['path'] = node.path
                        field_sensitive_originals[node]['source_variable'] = node.left_hand_side
                        field_sensitive_originals[node]['fields_used'].append(tmp)

    return field_sensitive_originals

def get_if_stmt_original_variables(
        if_stmt,
        lattice,
        use_def,
        sink_chain,
        sink
):
    chain = defaultdict(list)
    original_variables = []
    if_use_def = build_if_use_def_chain(if_stmt, if_stmt.variables, lattice)
    for node in if_use_def:
        chain = get_use_def_chains(node, node, use_def, chain=defaultdict(list))

        for variable in node.right_hand_side_variables:
            if variable in chain['original_node']:
                tmp = get_field_sensitive_sources(chain['original_node'][variable], chain, variable)
                for var in tmp:
                    original_variables.append(var)

    for variable in chain['original_node']:
        # tmp = [variable.left_hand_side, variable.path, variable.line_number]
        # original_variables.append(tmp)
        original_variables.append(variable)
    # print("\n")

    # print("original variables: ", original_variables)
    # print("\n\n")

    return original_variables

def get_sink_original_variables(
    sink,
    chain
):
    sink_fields = defaultdict(lambda: defaultdict(list))
    for field in chain[sink]:
        # print("chain[original_node][variable]", variable, chain['original_node'][variable])
        tmp = {'sink_field': field, 'tainted_by': []}

        # for earlier_node in chain[sink][field]:
        #     earlier_node = earlier_node['earlier_node']
        #     earlier_lhs = earlier_node['rhs']
        #     while earlier_node is not {}:
        #         earlier_node_chain = chain[earlier_node]
        #         earlier_lhs_with_fields = earlier_lhs.split(".")
        #         if len(earlier_lhs_with_fields) > 1:
        #             for i in range(0, len(earlier_lhs_with_fields)):
        #                 earlier_node_chain
            # tmp2 = {
            #     'source_variable': org_node.left_hand_side,
            #     'line_number': org_node.line_number,
            #     'path': org_node.path,
            #     'fields_used': []
            #     }
            # original_variable= original_variable_fields_used[org_node]
            # if original_variable["source_variable"] == org_node.left_hand_side and original_variable['line_number'] == org_node.line_number and original_variable["path"] == org_node.path:
            #     tmp2['fields_used'] = original_variable["fields_used"]
            # tmp['tainted_by'].append(tmp2)
        # for org_node in original_variable_fields_used:
        #     if original_variable_fields_used[org_node] != {}:
        #         tainted[variable]['source_fields'].append(original_variable_fields_used[org_node])
    return sink_fields

def get_old_sink_original_variables(
    sink,
    chain
):
    original_variable_fields_used = defaultdict(lambda: defaultdict(list))
    tainted = defaultdict(lambda: defaultdict(list))
    for variable in sink.right_hand_side_variables:
        if variable in chain['original_node']:
            original_variable_fields_used = get_field_sensitive_sources(chain['original_node'][variable], chain, variable)
            # print("field_sensitive originals: ", original_variable_fields_used)
    for variable in sink.right_hand_side_variables:
        if variable not in chain['original_node']:
            continue
        # print("chain[original_node][variable]", variable, chain['original_node'][variable])
        tainted[variable]['sink'] = {"label": sink.label, "line_number": sink.line_number, "path": sink.path}
        tmp = {'sink_field': variable, 'tainted_by': []}

        for org_node in chain['original_node'][variable]:
            print("org_node: ", org_node)
            tmp2 = {
                'source_variable': org_node.left_hand_side,
                'line_number': org_node.line_number,
                'path': org_node.path,
                'fields_used': []
                }
            original_variable= original_variable_fields_used[org_node]
            if original_variable["source_variable"] == org_node.left_hand_side and original_variable['line_number'] == org_node.line_number and original_variable["path"] == org_node.path:
                tmp2['fields_used'] = original_variable["fields_used"]
            tmp['tainted_by'].append(tmp2)
        tainted[variable]['sink_fields'].append(tmp)
        print("original_variable_fields_used: ", original_variable_fields_used)
        # for org_node in original_variable_fields_used:
        #     if original_variable_fields_used[org_node] != {}:
        #         tainted[variable]['source_fields'].append(original_variable_fields_used[org_node])
    return tainted, original_variable_fields_used


def build_if_use_def_chain(
        if_stmt,
        variables,
        lattice
):
    use_def = list()
    if variables is None:
        return use_def
    for variable in variables:                    
        for earlier_node in get_constraint_nodes(if_stmt, lattice):
            # if (variable == "order_item.quantity"):
            #     print("order_item.quantity: ", earlier_noself.request.userde)
            if variable is None:
                break
            
            rhs = variable.split(".")
            lhs = earlier_node.left_hand_side.split(".")
            min_len = min(len(rhs), len(lhs))
            skip = False
            for i in range(min_len):
                # print("rhs, lhs: ",rhs[i], lhs[i])
                if rhs[i] != lhs[i]:
                    skip = True
            if not skip:
                # print("not skipped: ", rhs, lhs)
                use_def.append(earlier_node)
    return use_def


                    # if isinstance(node.ast_node, ast.Call):
                    #     if len(rhs_with_fields) > 1:
                    #         for keyword in node.ast_node.keywords: 
                    #             tmp = keyword.value
                    #             passed_variable = ""
                    #             while (isinstance(tmp, ast.Attribute)):
                    #                 passed_variable = "." + tmp.attr + passed_variable
                    #                 tmp = tmp.value
                    #             if (isinstance(tmp, ast.Name)):
                    #                 passed_variable = tmp.id + passed_variable
                    #             if passed_variable == rhs:
                    #                 if not check_diff_variable(rhs, earlier_node.left_hand_side):
                    #                     node.fields[keyword.arg] = {earlier_node: earlier_node.fields}
                    #                     if(rhs in use_def[node]):
                    #                         use_def[node][rhs].append(earlier_node)
                    #                     else:
                    #                         use_def[node][rhs] = [earlier_node]
                    #     else:
                    #         if not node.ast_node.keywords:
                    #             if len(rhs_with_fields) == 1 and not check_diff_variable(rhs, earlier_node.left_hand_side):
                    #                 if earlier_node.fields:
                    #                     # if isinstance(earlier_node.ast_node.targets[0], ast.Attribute):
                    #                     #     continue
                    #                     node.fields = earlier_node.fields
                    #                     print("call node: ", node, node.line_number, earlier_node, earlier_node.line_number, "\n", node.fields)
                    #             continue
                    #         for keyword in node.ast_node.keywords: 
                    #             tmp = keyword.value
                    #             passed_variable = ""
                    #             while (isinstance(tmp, ast.Attribute)):
                    #                 passed_variable = "." + tmp.attr + passed_variable
                    #                 tmp = tmp.value
                    #             if (isinstance(tmp, ast.Name)):
                    #                 passed_variable = tmp.id + passed_variable

                    #             if passed_variable == rhs:
                    #                 if not check_diff_variable(rhs, earlier_node.left_hand_side):
                    #                     node.fields[keyword.arg] = {earlier_node: earlier_node.fields}
                    #                     if(rhs in use_def[node]):
                    #                         use_def[node][rhs].append(earlier_node)
                    #                     else:
                    #                         use_def[node][rhs] = [earlier_node]
                    # elif isinstance(node.ast_node, ast.Assign) and isinstance(node.ast_node.targets[0], ast.Attribute):
                    #     tmp = node.ast_node.targets[0]
                    #     passed_variable = ""
                    #     while (isinstance(tmp, ast.Attribute)):
                    #         passed_variable = "." + tmp.attr + passed_variable
                    #         tmp = tmp.value
                    #     passed_variable = passed_variable[1:]
                    #         # print("details: ", node, node.line_number, "\n", "rhs: ", rhs, "passed variable", passed_variable, "earlier_node.lhs: ", earlier_node.left_hand_side, "keyword: ", keyword.arg, "earlier_node.fields: ", earlier_node.fields)
                    #     if not check_diff_variable(rhs, earlier_node.left_hand_side):
                    #         print("details: ", node, node.line_number, "\n", "rhs: ", rhs, "earlier_node.lhs: ", earlier_node.left_hand_side, "passed_variable", passed_variable, "earlier_node.fields: ", earlier_node.fields)
                    #         node.fields[passed_variable] = {earlier_node: earlier_node.fields}
                    #         print("fields: ", node.fields)
                    #         if(rhs in use_def[node]):
                    #             use_def[node][rhs].append(earlier_node)
                    #         else:
                    #             use_def[node][rhs] = [earlier_node]
                    # if (variable == "order_item.quantity"):
                    #     print("order_item.quantity: ", earlier_node)
                    # elif len(rhs_with_fields) == 1 and not check_diff_variable(rhs, earlier_node.left_hand_side):
                    #     print("last if, ", node, node.line_number)
                    #     if earlier_node.fields:
                    #         node.fields = earlier_node.fields
                    #     if(rhs in use_def[node]):
                    #         use_def[node][rhs].append(earlier_node)
                    #     else:
                    #         use_def[node][rhs] = [earlier_node]

                        # if rhs_is_attribute:
                        #     tmp = earlier_node.fields
                        #     for i in range(0, len(rhs_with_fields)):
                        #         if not rhs_with_fields[i] in tmp:
                                    
                        #             tmp2 = [{'earlier_node': {}, 'fields': rhs}]
                        #             for j in range(len(rhs_with_fields)-1, i, -1):
                        #                 tmp2 = {rhs_with_fields[j]: tmp2}
                        #             tmp[rhs_with_fields[i]] = tmp2
                        #             #print("earlier node fields: ", earlier_node.fields)
                        #             break
                        #         else:
                        #             tmp = tmp[rhs_with_fields[i]]
                        #             #this also accounts for cases like lhs: user.age.field and rhs: user.age
                        #             # if isinstance(tmp, list):
                        #             #     tmp.append({'earlier_node': earlier_node, 'fields': rhs})
                        # else:
                        #     if not earlier_node.fields:
                        #         earlier_node.fields = {rhs:[{'earlier_node': {}, 'fields': rhs}]}
                        # # if lhs_is_attribute:
                        # #     tmp = earlier_node.fields
                        # #     for i in range(1, len(lhs_with_fields)):
                        # #         if not lhs_with_fields[i] in tmp:
                        # #             tmp2 = [{'earlier_node': earlier_node, 'fields': lhs}]
                        # #             for j in range(len(lhs_with_fields)-1, i, -1):
                        # #                 tmp2 = {lhs_with_fields[j]: tmp2}
                        # #             tmp[lhs_with_fields[i]] = tmp2
                        # #             #print("earlier node fields: ", earlier_node.fields)
                        # #             break
                        # #         else:
                        # #             tmp = tmp[lhs_with_fields[i]]
                        # #             #this also accounts for cases like lhs: user.age.field and rhs: user.age       
                        # if isinstance(node.ast_node, ast.Call):
                        #     #find corresponding keyword argument to rhs
                        #     #first convert all keyword arguments to rhs format
                        #     passed_variable = None
                        #     keyword_arg = None
                        #     for keyword in node.ast_node.keywords:
                        #         tmp = keyword.value
                        #         passed_variable = ""
                        #         while (isinstance(tmp, ast.Attribute)):
                        #             passed_variable = "." + tmp.attr + passed_variable
                        #             tmp = tmp.value
                        #         if (isinstance(tmp, ast.Name)):
                        #             passed_variable = tmp.id + passed_variable
                        #         if passed_variable == rhs:
                        #             keyword_arg = keyword.arg
                        #             break
                        #         #check if keyword argument matches rhs
                        #     #print("passed_var", passed_variable, ",", rhs)
                        #     if passed_variable and passed_variable == rhs:
                        #         # tmp = earlier_node.fields
                        #         # for i in range(0, len(rhs_with_fields)):
                        #         #     tmp = tmp[rhs_with_fields[i]]
                        #         if cur_lhs not in node.fields:
                        #             node.fields[cur_lhs] = {}
                        #         if keyword_arg in node.fields[cur_lhs]:
                        #             tmp = {'earlier_node': earlier_node, 'field': rhs}
                        #             if tmp not in node.fields[cur_lhs][keyword_arg]:
                        #                 node.fields[cur_lhs][keyword_arg].append({'earlier_node': earlier_node, 'field': rhs})
                        #         else:
                        #             node.fields[cur_lhs][keyword_arg] = [{'earlier_node': earlier_node, 'field': rhs}]
                        #         if(rhs in use_def[node]):
                        #             use_def[node][rhs].append(earlier_node)
                        #         else:
                        #             use_def[node][rhs] = [earlier_node]
                        #     else:
                        #         #in case where there are no call parameters like user=req.user
                        #         #cur_lhs does not account for lhs that are not names but attributes.
                        #         tmp = {'earlier_node': earlier_node, 'field': rhs}
                        #         if node.fields:
                        #             if cur_lhs not in node.fields:
                        #                 node.fields[cur_lhs] = {cur_lhs: [tmp]}
                        #             else:
                        #                 if tmp not in node.fields[cur_lhs]:
                        #                     node.fields[cur_lhs].append(tmp)
                        #         else:
                        #             node.fields[cur_lhs] = [{'earlier_node': earlier_node, 'field': rhs}]
                        #     print("CallNode: ", node, node.line_number, earlier_node.line_number, node.fields)
                        #     print("earlier node fields: ", earlier_node.fields)

                        # elif isinstance(node.ast_node, ast.Assign):
                        #     tmp = {}
                        #     if node.fields:
                        #         tmp = node.fields
                        #     else:
                        #         tmp = [{'earlier_node': earlier_node, 'field': rhs}]
                        #     if cur_lhs_is_attribute:   
                        #         skipped = False
                        #         for i in range(0, len(cur_lhs_with_fields)):
                        #             if not cur_lhs_with_fields[i] in tmp:
                        #                 tmp2 = tmp
                        #                 for j in range(len(cur_lhs_with_fields)-1, i, -1):
                        #                     tmp2 = {cur_lhs_with_fields[j]: tmp2}
                        #                 node.fields[cur_lhs_with_fields[i]] = tmp2
                        #             #print("earlier node fields: ", earlier_node.fields)
                        #                 break
                        #             else:
                        #                 tmp = tmp[lhs_with_fields[i]]
                        #     else:
                        #         tmp = {'earlier_node': earlier_node, 'field': rhs}
                        #         if node.fields and tmp not in node.fields[cur_lhs]:
                        #             node.fields[cur_lhs].append({'earlier_node': earlier_node, 'field': rhs})
                        #         else:
                        #             node.fields[cur_lhs] = [{'earlier_node': earlier_node, 'field': rhs}]

                        #     print("Assign node", node, node.line_number, earlier_node.line_number, node.fields)
                        #     print("earlier node fields: ", earlier_node.fields)
                            
                        #     if(rhs in use_def[node]):
                        #         use_def[node][rhs].append(earlier_node)
                        #     else:
                        #         use_def[node][rhs] = [earlier_node]