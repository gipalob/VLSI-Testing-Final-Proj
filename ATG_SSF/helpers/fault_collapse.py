from .helpers import Graph, color
from .helpers import ControllingInversionVals as ci
from typing import Dict, Tuple, List

import json
class Faults:
    def __init__(self, gates: Dict[str, dict], graph: Graph):
        self.gates = gates
        self.graph = graph
        # Create initial fault list - faults only on PIs and POs
        max_level = max(g["level"] for g in gates.values())
        self.fault_list = {
            k: [0, 1] 
            # if (gates[k]["type"] == "PI") or (gates[k]["level"] == max_level) 
            # else [] 
            for k in gates.keys()
        }
    
    def collapse(self):
        # Start at PIs
        # print(f"initial fault count: {sum(len(v) for v in self.fault_list.values())}") #debug print
        for gate in self.gates:
            gtyp = self.gates[gate]["type"]
            if gtyp == "PI":
                continue
            
            inps = self.gates[gate]["inputs"]
            c, i = ci.__dict__.get(gtyp, (None, None))
            
            if c is None: raise ValueError(f"Unsupported gate type '{gtyp}' for fault collapsing.")
            
            cXORi = c ^ i
            # Remove functionally eq inp faults
            for inp in reversed(inps[1:]):
                if cXORi in self.fault_list[inp]:
                    # Before we remove a fault, though, we should check if this line has fanout
                    neighbors = self.graph.get_neighbors(inp)
                    neighbor_fanout = False
                    if len(neighbors) > 1:
                        for neighbor in neighbors:
                            if neighbor == gate: continue #skip the current gate
                            
                            fanout_gate = self.gates[neighbor]["type"]
                            tmp_c, tmp_i = ci.__dict__.get(fanout_gate, (None, None))
                            if tmp_c is None: raise ValueError(f"Unsupported gate type '{fanout_gate}' for fault collapsing.")
                            
                            if (cXORi != (tmp_c ^ tmp_i)):
                                # print(f"Cannot remove fault {cXORi} from line '{inp}' (gate '{gate}') due to fanout to gate '{neighbor}'") # Debug print
                                neighbor_fanout = True
                                break

                    if not neighbor_fanout:
                        self.fault_list[inp].remove(cXORi)
                        # print(f"Removed fault {cXORi} from line '{inp}' (gate '{gate}')") # Debug print
                        
            # Dominant fault collapsing
            NOTcXORi = (not c) ^ i
            for inp in inps:
                if len(self.graph.get_neighbors(inp)) > 1: # skip if fanout exists
                    continue
                
                if NOTcXORi in self.fault_list[inp]:
                    if self.gates[inp]["type"] == "PI":
                        next_inp = inps.index(inp) + 1
                        if not (next_inp < len(inps) and NOTcXORi in self.fault_list[inps[next_inp]]):
                            continue 
                    self.fault_list[inp].remove(NOTcXORi)
                    
        #debug print fault count
        # print(f"{json.dumps(self.fault_list, indent=4)}")
        # print(f"fault count: {sum(len(v) for v in self.fault_list.values())}")

        