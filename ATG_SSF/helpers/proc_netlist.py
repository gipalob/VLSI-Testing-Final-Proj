from typing import Tuple, Dict
from .helpers import Graph
import json
def decomp_file(file_lines: list[str]):
    """
    Decomposes the netlist file lines into a gate list, with circuit level 
    Begins by stripping + removing comments, then parsing each line into components.
    We aren't trusting the 'primary input' / 'primary output' comment markers-
    instead, we will identify PIs and POs based on graph.
    The one assumption is that each gate line is {Output}, {Gate Type}, {Input1}, {Input2}...
    """
    # I loooove list comprehensions
    decomp_lines = (
        parts
        for line in (
            line.split('$')[0].strip()
            for line in file_lines
            if line and not line.startswith('$')
        )
        if (parts := [part.strip() for part in line.split(' ') if part.strip()]) and len(parts) >= 4
    )
    gates = {
        p[0]: {
            "type": p[1].upper(),
            "inputs": p[2:],
            "level": None
        }
        for p in decomp_lines
    }
    
    # Get Primary Inputs
    outps = set(gates.keys())
    inps = set(inp for g in gates.values() for inp in g["inputs"])
    PIs = inps - outps
    POs = outps - inps
    
    # Update gate list with PIs
    [gates.update({pi: {"type": "PI", "inputs": [], "level": 0}}) for pi in PIs]
    
    def level(gate):
        if gates[gate]["level"] is not None:
            return gates[gate]["level"]
        if gate in PIs:
            gates[gate]["level"] = 0
        else:
            gates[gate]["level"] = 1 + max(level(inp) for inp in gates[gate]["inputs"])
        return gates[gate]["level"]
    [level(gate) for gate in gates]
    
    # Last step - Make sure POs are highest level
    max_level = max(g["level"] for g in gates.values()) # This will actually be the PO level

    [gates[po].update({"level": max_level}) for po in POs]
    
    # Sort first by level, then alphabetically & return
    return dict(sorted(gates.items(), key=lambda item: (item[1]["level"], item[0])))

    
def get_edge_list(gates: Dict[str, dict]) -> list[Tuple[str, str]]:
    """
    Get edge list of graph
    """
    edge_list = []
    for output, gate_info in gates.items():
        for inp in gate_info["inputs"]:
            edge_list.append((inp, output))
    return edge_list

def process_netlist(file_lines: list[str]) -> Tuple[Dict[str, dict], Graph]:
    gates = decomp_file(file_lines)
    edge_list = get_edge_list(gates)
    
    # Get custom-class based graph, as we want to be sure we don't make networkx required ('optional feature')
    circuit_graph = Graph(edge_list)

    return gates, circuit_graph
    
    
