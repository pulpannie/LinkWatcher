"""This formatter outputs the issues as plain text."""
from ..vulnerabilities.vulnerability_helper import SanitisedVulnerability
import ast, json
from collections import defaultdict

def convert_object_to_dict(obj, iteration=0, sink=None, source=None):
    obj_dict = defaultdict(list)
    for earlier_node in obj.earlier_nodes:
        obj_dict['earlier_nodes'].append({'field': earlier_node['field'], 'line_number': earlier_node['earlier_node'].line_number, 'path': earlier_node['earlier_node'].path})
    for field in obj.fields:
        obj_dict[obj.name].append(convert_object_to_dict(field, iteration+1))
    if not obj.fields:
        obj_dict = {obj.name: obj_dict}
    if iteration == 0:
        obj_dict= {'source': {'label':source.label, 'line_number':source.line_number, 'path':source.path},'sink': {'label': sink.label, 'line_number': sink.line_number, 'path': sink.path}, list(obj_dict)[0]: list(obj_dict.values())[0]}
    return obj_dict

def get_earliest(node, chain):
    earlier_nodes = chain[node]
    for earlier_node in earlier_nodes:
        if earlier_node['earlier_node']:
            print("not empty", node, chain[node])
            yield from get_earliest(earlier_node['earlier_node'], chain)
        else:
            print("empty?", node)
            yield node, earlier_node

def append_chain(node, chain, arr=[]):
    arr.append(node)
    earlier_nodes = chain[node]
    for earlier_node in earlier_nodes:
        if earlier_node['earlier_node']:
            append_chain(earlier_node['earlier_node'], chain, arr)
    return arr

def report(
    vulnerabilities,
    fileobj,
    print_sanitised,
):
    """
    Prints issues in text format.

    Args:
        vulnerabilities: list of vulnerabilities to report
        fileobj: The output file object, which may be sys.stdout
        print_sanitised: Print just unsanitised vulnerabilities or sanitised vulnerabilities as well
    """
    n_vulnerabilities = len(vulnerabilities)
    # unsanitised_vulnerabilities = [v for v in vulnerabilities if not isinstance(v, SanitisedVulnerability)]
    # n_unsanitised = len(unsanitised_vulnerabilities)
    # n_sanitised = n_vulnerabilities - n_unsanitised
    # heading = "{} vulnerabilit{} found{}{}\n".format(
    #     'No' if n_vul == 0 else n_unsanitised,
    #     'y' if n_unsanitised == 1 else 'ies',
    #     " (plus {} sanitised)".format(n_sanitised) if n_sanitised else "",
    #     ':' if n_vulnerabilities else '.',
    # )
    heading = "{} vulnerabilit{} found{}\n".format(
        'No' if n_vulnerabilities == 0 else n_vulnerabilities,
        'y' if n_vulnerabilities == 1 else 'ies',
        ':' if n_vulnerabilities else '.',
    )
    #vulnerabilities_to_print = vulnerabilities if print_sanitised else unsanitised_vulnerabilities
    vulnerabilities_to_print = vulnerabilities

    print("HERE")
    shared_vars = defaultdict(list)
    with fileobj:
        fileobj.write(heading)

        # for i, vulnerability in enumerate(vulnerabilities_to_print, start=1):
        #     fileobj.write('Vulnerability {}:\n{}\n'.format(i, vulnerability))
        #     rhs_str =  ""
        #     if_stmts = ""
        #     else_stmts = ""
        #     for node in vulnerability.reassignment_nodes:
        #         if node == "original_node" or node == "original_variables":
        #             continue
        #         if node.right_hand_side_variables:
        #             rhs_str = rhs_str + ' '.join(node.right_hand_side_variables) 
        #             rhs_str = rhs_str + '->'
        #         if node.if_statements_seen:
        #             for if_stmt in node.if_statements_seen:
        #                 if if_stmt.label not in if_stmts:
        #                     if_stmts += if_stmt.label + ","
        #         if node.else_statements_seen:
        #             for else_stmt in node.else_statements_seen:
        #                 if else_stmt.label not in else_stmts:
        #                     else_stmts += else_stmt.label + ","
        #     fileobj.write('Total variables that were used in sink variable TODO: {}\n'.format(rhs_str))     
        #     fileobj.write('If statements that influenced this sink: {}\n'.format(if_stmts))
        #     fileobj.write('Else statements that influenced this sink:  {}\n\n'.format(else_stmts))
        
#LINKED VARS
        # for i, i_vulnerability in enumerate(vulnerabilities_to_print, start=0):
        #     i_source = i_vulnerability.source.label
        #     if i_source.replace('Entry function: ', '') in shared_vars:
        #         continue
        #     i_reassignment_nodes = i_vulnerability.reassignment_nodes[i_vulnerability.sink]
        #     flag = 0
        #     for j_vulnerability in vulnerabilities_to_print[i+1:]:
        #         j_source = j_vulnerability.source.label
        #         if i_source != j_source:
        #             continue
        #         j_reassignment_nodes = j_vulnerability.reassignment_nodes[j_vulnerability.sink]

        #         for i_reassignment_variable in i_reassignment_nodes:
        #             for i_reassignment_node in i_reassignment_nodes[i_reassignment_variable]:
        #                 for j_reassignment_variable in j_reassignment_nodes: 
        #                     print("i_reassignment_node, ",i_reassignment_node)
        #                     print("j_reassignment_nodes, ",j_reassignment_nodes[j_reassignment_variable])                
        #                     if i_reassignment_node in j_reassignment_nodes[j_reassignment_variable]:
        #                         flag = 1
        #                         var = i_reassignment_node
        #                         if i_reassignment_node in shared_vars[i_source.replace('Entry function: ', '')]:
        #                             shared_vars[i_source.replace('Entry function: ', '')][i_reassignment_node].append(j_vulnerability.sink)
        #                         else:
        #                             shared_vars[i_source.replace('Entry function: ', '')] = {i_reassignment_node:[j_vulnerability.sink]}
        #     if flag == 1:
        #         shared_vars[i_source.replace('Entry function: ', '')][var].append(i_vulnerability.sink)
        # shared = "Linked variables: \n"
        # print("shared vars: ", shared_vars)
        # for key in shared_vars:
        #     shared += "\tsource: {}\n".format(key)
        #     for i in shared_vars[key]:
                
        #         shared += "\tlocation: {} | {} | {}\n".format(i.left_hand_side, i.path, i.line_number)
        #         for item in shared_vars[key][i]:
        #             shared += "\t\t sinks:{} | {} | {} | {}\n".format(item.right_hand_side_variables, item.path, item.line_number, item.label)
        # fileobj.write(shared)

        
        # for i, vulnerability in enumerate(vulnerabilities_to_print, start=1):
        #     for if_stmt in i.sink.if_statements_seen:
        #         use_def
        #print("SOURCES: ", [node.cfg_node for node in vulnerability.sources])
        f = open("output2.json", "w")
        json_dict = defaultdict(list)
        #shared variables link-TEE
        for i_vulnerability in vulnerabilities_to_print:
            for j_vulnerability in vulnerabilities_to_print:
                if i_vulnerability == j_vulnerability or i_vulnerability['sink'] == j_vulnerability['sink']:
                    continue
                for i_k, i_v in i_vulnerability['chain'].items():
                    for j_k, j_v in j_vulnerability['chain'].items():
                        i_nodes =  append_chain(i_vulnerability['sink'],i_v, [])
                        j_nodes =  append_chain(j_vulnerability['sink'], j_v, [])
                        for i in i_nodes:
                            if i in j_nodes:
                                tmp = {'sink1': {'label': i_vulnerability['sink'].label, 'field': i_k, 'path': i_vulnerability['sink'].path, 'line_number': i_vulnerability['sink'].line_number}, \
                                       'sink2': {'label': j_vulnerability['sink'].label, 'field': j_k, 'path': j_vulnerability['sink'].path, 'line_number': j_vulnerability['sink'].line_number}, \
                                       'item': {'label': i.left_hand_side, 'path': i.path, 'line_number': i.line_number}}
                                if tmp not in shared_vars[i_vulnerability['first_node'].label]:
                                    shared_vars[i_vulnerability['first_node'].label].append(tmp)
                                break
        for vulnerability in vulnerabilities_to_print:
            chain = vulnerability['chain']
            sink_dict = defaultdict(list)
            sink_dict['sink'] = {'path': vulnerability['sink'].path, 'line_number': vulnerability['sink'].line_number, 'label': vulnerability['sink'].label}
            print("vulnerability:",  vulnerability['sink'].label, vulnerability['sink'].if_statements_seen)
            for field, v in chain.items():
                if not v:
                    continue
                earlier_node = vulnerability['sink']
                tmp_dict = defaultdict(list)
                for node, earlier in get_earliest(earlier_node, v):
                    if node != earlier:
                        tmp = {'path': node.path, 'line_number': node.line_number, 'field': earlier['field']}
                        if tmp not in tmp_dict[field]:
                            tmp_dict[field].append({'path': node.path, 'line_number': node.line_number, 'field': earlier['field']})
                sink_dict['fields'].append(tmp_dict)
            flag = 0
            for item in json_dict[vulnerability['first_node'].label]:
                if sink_dict['sink']['line_number'] == item['sink']['line_number']: 
                    flag = 1
                    break
            if flag == 0:
                json_dict[vulnerability['first_node'].label].append(sink_dict)
        #for vulnerability in vulnerabilities_to_print:
        #    json_dict = convert_object_to_dict(vulnerability['sink_origin'], sink=vulnerability['sink'], source=vulnerability['source'].cfg_node)
            #link-TEE cpython json file
        #    f.write(json.dumps(json_dict, indent=4))
        vulnerability_dict = dict()
        vulnerability_dict['direct_dataflow'] = json_dict
        #vulnerability_dict['comp_links'] = shared_vars
        f.write(json.dumps(vulnerability_dict, indent=4))


        f.close()




        # for key in shared_vars:
        #     for i in shared_vars[key]:
        #         tmp2 = {'variable': i.left_hand_side, 'path': i.path, 'line_number': i.line_number, 'sink': []}
        #         tmp = [i.left_hand_side, i.path, i.line_number]
        #         for sink in shared_vars[key][i]:
        #             tmp2['sink'].append({"label": sink.label, "line_number": sink.line_number, "path": sink.path})
        #         if tmp not in json_dict['variables_to_track']:
        #             json_dict['variables_to_track'].append(tmp)
        #         if tmp2 not in json_dict['variables_to_track2']:
        #             json_dict['variables_to_track2'].append(tmp2)
        # for i, vulnerability in enumerate(vulnerabilities_to_print, start=1):
        #     for variable in vulnerability.cpython['tainted']:
        #         if variable not in json_dict['tainted_variables']:
        #             # for tainted_by in vulnerability.cpython['tainted'][variable]['tainted_by']:
        #             #     for source_fields in vulnerability.cpython['tainted'][variable]['source_fields']:
        #             #         if tainted_by['sink_field'] == source_fields['sink_field'] and tainted_by['line_number'] == source_fields['line_number'] and tainted_by['path'] == source_fields['path']:
        #             #             if 'fields_used' in tainted_by:
        #             #                 for var in source_fields['fields_used']:
        #             #                     tainted_by['fields_used'].append(var)
        #             #             else:
        #             #                 tainted_by['fields_used'] = source_fields['fields_used']
        #             json_dict['tainted_variables'].append(vulnerability.cpython['tainted'][variable])
        #     for statement in vulnerability.cpython['if_statements']:
        #         if statement not in json_dict['if_statements']:
        #             json_dict['if_statements'].append(statement)