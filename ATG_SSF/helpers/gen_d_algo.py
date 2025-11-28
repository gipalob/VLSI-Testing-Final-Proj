from .helpers import color
from .helpers import Graph
from .helpers import ControllingInversionVals as ci
from .helpers import GateOps as ops
from .helpers import DGateOps as dops
from .fault_collapse import Faults
from typing import Tuple, Optional
import json 

from typing import Dict, List, Set, Optional, Union, NamedTuple
from typing import Dict, List, Optional, Union

class DAlgorithm:
    def __init__(self, netlist: Dict[str, Dict], graph, fault_list, debug: bool = False):
        self.netlist = netlist
        self.graph = graph
        self.debug = debug
        # fault_list: object with .fault_list dict {gate: [0,1]}
        self.fault_list = [
            (gate, fault)
            for gate, faults in fault_list.fault_list.items()   
            for fault in faults
        ]

    # --- UTILITY ---
    def is_PI(self, w): return self.netlist[w]['type'] == 'PI'
    def is_PO(self, w): return self.netlist[w]['type'] == 'PO'
    def other_val(self, v):
        if v==0: return 1
        if v==1: return 0
        if v=='D': return "D'"
        if v=="D'": return 'D'
        return v
    def check_DCs(self, gate: str, assignment: dict) -> Tuple[bool | None, str]:
        """
        Check if a gate has Dont Care inputs
        """
        if self.debug: print(f"{color.BOLD}Check_DCs: Checking gate {gate}{color.ENDC}")
        inps = self.netlist[gate]['inputs']
        
        # We don't have anything to work off of - no inputs have been assigned to gate
        if len([i for i in inps if i == 'X']) == len(inps):
            if self.debug: print("Check_DCs: All inputs are X - cannot determine DCs")
            return (None, "")
        # Don't Cares really only apply to PIs, and we don't want to say a PI is DC if it has fanout
        if len([i for i in inps if self.is_PI(i)]):
            pi_gts = [i for i in inps if self.is_PI(i)]
            for pi in pi_gts:
                if len(self.graph.get_neighbors(pi)) > 1:
                    if self.debug: print(f"Check_DCs: PI input {pi} has fanout - cannot be DC")
                    return (False, "")
        
        c, i = ci.__dict__.get(self.netlist[gate]['type'], (None, None))
        if c is None: raise ValueError(f"Unsupported gate type '{self.netlist[gate]['type']}' for DC checking.")
        cur_assignments = [assignment[inp] for inp in inps]
        if c in cur_assignments and 'X' in cur_assignments:
            return (True, [i for i in inps if (assignment[i] == 'X') or (assignment[i] == c)][0])
        if self.debug: print("Check_DCs: No DCs found")
        return (False, "")
            
            
            

    # --- FRONTIER COMPUTATION ---
    def get_D_frontier(self, assignment) -> List[str]:
        lst = []
        for gname, gate in self.netlist.items():
            ins = [assignment[x] for x in gate['inputs']]
            if (('D' in ins or "D'" in ins) and assignment[gname] == "X"):
                lst.append(gname)
        return lst

    def get_J_frontier(self, assignment) -> List[str]:
        lst = []
        for gname, gate in self.netlist.items():
            if assignment[gname] in (0,1,"D","D'") and any(assignment[x] == "X" for x in gate['inputs']):
                lst.append(gname)
        return lst

    def error_at_PO(self, assignment) -> bool:
        return any(self.is_PO(g) and assignment[g] in ("D", "D'") for g in self.netlist)

    # --- MAIN RECURSIVE D-ALGORITHM ---
    def D_alg(self, assignment: Dict[str, Union[int,str]], depth=0) -> Optional[Dict]:
        assignment = dict(assignment)  # Copy for recursive call
        if self.debug: print(f"\n{color.OKBLUE}New DAlg call{color.ENDC}")
        if self.debug: print(f"Initial assignement at depth {depth}:\n{json.dumps(assignment, indent = 2)}")
        if not self.Imply_and_check(assignment):
            if self.debug: print(f"Depth: {depth}, Conflict detected during implication.")
            return None

        if self.error_at_PO(assignment):
            # Optionally: verify all signals justified
            if self.debug: print(f"Depth: {depth}, Error at PO")
            return assignment

        Dfront = self.get_D_frontier(assignment)
        if not Dfront:
            Jfront = self.get_J_frontier(assignment)
            if not len(Jfront):
                if self.debug: print(f"Depth: {depth}, J_frontier empty; success")
                return assignment
            
            for G in Jfront:
                if self.debug: print(f"Depth: {depth}, Jfront: {Jfront}")
                dc_check, dc_input = self.check_DCs(G, assignment)
                if dc_check: assignment[dc_input] = "DC"

                untried_inputs = [inp for inp in self.netlist[G]['inputs'] if assignment[inp] == 'X']
                if not untried_inputs:
                    continue
                
                c, i = ci.__dict__.get(self.netlist[G]['type'], (None, None))
                for inp in untried_inputs:
                    # Try assigning non-controlling value to X
                    assignment[inp] = c
                    if self.debug: print(f"Depth: {depth}, Trying assignment in jfront loop: {inp} = {c}")
                    result = self.D_alg(assignment, depth+1)
                    if result is not None:
                        return result
                    
                    # Backtrack this assignment
                    nc = self.other_val(getattr(ci, self.netlist[G]['type']).c)
                    assignment[inp] = nc
        
        # Decision: for each D-frontier, try each X input only ONCE at this depth
        # (no repeat, so recursion depth is finite)
        for G in Dfront:
            if self.debug: print(f"Depth: {depth}, Dfront: {Dfront}")
            controls = getattr(ci, self.netlist[G]['type'])
            c = controls.c

            untried_inputs = [inp for inp in self.netlist[G]['inputs'] if assignment[inp] == 'X']
            if not untried_inputs:
                if self.debug: print(f"{color.WARNING}Depth: {depth}, all inputs tried, continuing{color.ENDC}")
                continue
            for inp in untried_inputs:
                # Try assigning controlling value to X
                assignment[inp] = int(not c)
                if self.debug: print(f"Depth: {depth}, Trying assignment in dfront loop: {inp} = {c}")
                result = self.D_alg(assignment, depth+1)
                if result is not None:
                    if self.debug: print(f"{color.OKGREEN}Depth: {depth}, Success assigning {inp} to {assignment[inp]}!{color.ENDC}")
                    return result
                # Backtrack this assignment
                if self.debug: print(f"{color.WARNING}Depth: {depth}, Failure assigning {inp} to {assignment[inp]}- trying {c}{color.ENDC}")
                assignment[inp] = c
                
        
        return None

    # --- FAULT INJECTION ---
    def inject_fault(self, assignment: Dict[str, Union[int,str]], wire: str, stuck_val: int):
        # Activate stuck-at fault as D or D'
        assignment[wire] = 'D' if stuck_val == 0 else "D'"
        return assignment

    # --- SIMULATION/IMPLICATION ---
    def Imply_and_check(self, assignment: Dict[str, Union[int,str]]) -> bool:
        changed = True
        while changed:
            changed = False
            for g, info in self.netlist.items():
                if info['type'] in ('PI','PO'): continue
                ins = [assignment.get(x, "X") for x in info['inputs']]
                out = assignment.get(g, "X")
                if out != "X": continue
                if self.debug: print(f"Imply_and_Check: Simulating {info['type']} gate {g} with inputs {ins}")

                if all(v in (0, 1, 'D', "D'") for v in ins):
                    try:
                        func = getattr(dops, info['type'])
                        assignment[g] = func(ins)
                        if self.debug: print(f"Imply_and_Check: Assigned {g} = {assignment[g]}")
                        changed = True
                    except AttributeError:
                        raise ValueError(f"Unsupported gate type '{info['type']}' for D-Algorithm simulation.")

        return True

    # --- SOLVE ---
    def solve(self):
        pattern_solutions = []
        for (wire, stuck_val) in self.fault_list:
            if self.debug: print(f"\n\n\n{color.OKGREEN}Processing fault at {wire} stuck-at-{stuck_val}{color.ENDC}")
            initial_assignment = {w: 'X' for w in self.netlist}
            self.inject_fault(initial_assignment, wire, stuck_val)
            res = self.D_alg(initial_assignment)
            if res is not None:
                pattern_solutions.append(res)
            if self.debug: print(f"Result for {wire} s-a-{stuck_val}: {res}")
        return pattern_solutions