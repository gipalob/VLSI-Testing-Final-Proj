from .helpers import Graph, color
from .helpers import ControllingInversionVals as ci
from typing import Dict, Tuple, List

import json

# This modular file contains the logic for collapsing the list of circuit SSF faults
# It creates an initial fault list for PIs and POs, and defines a collapse method that does the following:
#   - Removes functionally equivalent input faults
#   - Removes dominated input faults

class Faults:
    def __init__(self, gates: Dict[str, dict], graph: Graph, debug: bool = False):
        self.gates = gates
        self.graph = graph
        self.debug = debug
        # Create initial fault list - faults only on PIs and POs
        max_level = max(g["level"] for g in gates.values())
        self.fault_list = {
            k: [0, 1] 
            # if (gates[k]["type"] == "PI") or (gates[k]["level"] == max_level) 
            # else [] 
            for k in gates.keys()
        }
        self.undetectable_faults = {k: [] for k in gates.keys()}
    
    def collapse(self):
        # Start at PIs
        if self.debug: print(f"initial fault count: {sum(len(v) for v in self.fault_list.values())}") #debug print
        # Iterate gates
        for gate in self.gates:
            # Skip PIs
            gtyp = self.gates[gate]["type"]
            if gtyp == "PI":
                continue
            
            # Source control and inverse values for gate type
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
                            
                            # Source control and inverse values for neighboring fanout gate
                            fanout_gate = self.gates[neighbor]["type"]
                            tmp_c, tmp_i = ci.__dict__.get(fanout_gate, (None, None))
                            if tmp_c is None: raise ValueError(f"Unsupported gate type '{fanout_gate}' for fault collapsing.")
                            
                            # Conditionally prevent collapsing if fanout is intolerable
                            if (cXORi != (tmp_c ^ tmp_i)):
                                if self.debug: print(f"Cannot remove fault {cXORi} from line '{inp}' (gate '{gate}') due to fanout to gate '{neighbor}'") # Debug print
                                neighbor_fanout = True
                                break
                    # If fanout is tolerable / nonexistant, remove functionally eq fault
                    if not neighbor_fanout:
                        self.fault_list[inp].remove(cXORi)
                        self.undetectable_faults[inp].append(cXORi)
                        if self.debug: print(f"Removed fault {cXORi} from line '{inp}' (gate '{gate}')") # Debug print
                        
            # Dominant fault collapsing
            NOTcXORi = (not c) ^ i
            for inp in inps:
                if len(self.graph.get_neighbors(inp)) > 1: # skip if fanout exists
                    continue
                
                # If fault still exists
                if NOTcXORi in self.fault_list[inp]:
                    # Check next gate in case of PI
                    if self.gates[inp]["type"] == "PI":
                        next_inp = inps.index(inp) + 1
                        if not (next_inp < len(inps) and NOTcXORi in self.fault_list[inps[next_inp]]):
                            continue 
                    # Remove dominated fault
                    self.fault_list[inp].remove(NOTcXORi)
                    self.undetectable_faults[inp].append(NOTcXORi)
                    
        #debug print fault count
        if self.debug: print(f"{json.dumps(self.fault_list, indent=4)}")
        if self.debug: print(f"fault count: {sum(len(v) for v in self.fault_list.values())}")
        
    # CLI Styling for displaying collapsed fault list and (conditionally) undetectable faults
    def print_fault_classes(self, *args, **kwargs):
        """
        Optional kwargs: 
            vis: Visualize class instance to display fault classes on graph
        """
        indices = kwargs.get("indices", False)
        print(f"{color.HEADER}{color.BOLD}")
        if indices:
            print(f"Fault #\t| Gate\t| Fault")
        else:
            print(f"Fault classes after collapsing:\n")
            print(f"Gate\t| Fault(s)")
        print(f"{'-'*25}{color.ENDC}")
    
        idx = 0
        for gate, faults in self.fault_list.items():
            if indices and faults:
                print(f"{color.BOLD}{color.OKGREEN}", end="")
                for f in faults:
                    print(f"{idx}\t| {gate}\t| s-a-{f}")
                    idx += 1
                print(f"{color.ENDC}", end="")
            elif not indices:
                print(f"{color.OKGREEN}{gate}{' '*(8-len(gate))}{color.HEADER}{color.BOLD}|{color.ENDC} {', '.join('s-a-' + str(f) for f in faults) if faults else 'None'}")
        
        if kwargs.get("show_undetectable", False):
            print(f"{color.ENDC}\n{color.BOLD}{color.HEADER}Would you like to view the list of undetectable faults? (Y/N) {color.ENDC}")
            if input().strip().lower() == 'y':
                print(f"{color.HEADER}{color.BOLD}\nUndetectable Faults:\n{color.ENDC}")
                print(f"{color.BOLD}Gate\t| Undetectable Fault(s){color.ENDC}")
                print(f"{'-'*35}")
                for gate, faults in self.undetectable_faults.items():
                    print(f"{color.OKGREEN}{gate}{' '*(8-len(gate))}{color.HEADER}{color.BOLD}|{color.ENDC} {', '.join('s-a-' + str(f) for f in faults) if faults else 'None'}")
                print(f"{color.ENDC}")
                
        # if kwargs.get("vis", None): 
        #     print(f"{color.OKCYAN}{color.BOLD}Would you like to view the fault classes on the graph? (Y/N) {color.ENDC}")
        #     choice = input().strip().lower()
        #     if choice == 'y':
        #         pass

        