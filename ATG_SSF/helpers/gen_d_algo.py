from .helpers import color
from .helpers import Graph
from .helpers import ControllingInversionVals as ci
from .helpers import GateOps as ops
from .helpers import DGateOps as dops
from .fault_collapse import Faults
from typing import Tuple, Optional
import json 
import time
from random import randint as rand

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
        self.solutions = {}
        self.refined_solns = []

    # --- UTILITY ---
    def is_PI(self, w): return self.netlist[w]['type'] == 'PI'
    def is_PO(self, w): return self.netlist[w]['type'] == 'PO'
    def other_val(self, v):
        if v==0: return 1
        if v==1: return 0
        if v=='D': return "D'"
        if v=="D'": return 'D'
        return v
    def check_DCs(self, assignment: dict) -> dict:
        """
        Check if any gate has Dont Care inputs
        """
        l1_gts = [g for g in self.netlist.keys() if self.netlist[g]['level'] == 1]
        for g in l1_gts:
            ins = [(x, assignment[x]) for x in self.netlist[g]['inputs']]
            c, i = ci.__dict__.get(self.netlist[g]['type'], (None, None))
            func = dops.__dict__.get(self.netlist[g]['type'], None)
            if c is None or func is None: raise ValueError(f"Unsupported gate type '{self.netlist[g]['type']}' for D-Algorithm simulation.")
            if any(v == c for _, v in ins):
                # At least one input is controlling value, so assuming no fanout rest are DCs
                # This doesn't catch all DCs in all cases. but good enough
                keep = [i for i, v in enumerate(ins) if v[1] == c][0]
                for idx, (inp_name, inp_val) in enumerate(ins):
                    if idx == keep: continue
                    if len(self.graph.get_neighbors(inp_name)) == 1:
                        if inp_val not in ('D', "D'"):
                            assignment[inp_name] = "DC"
                            if self.debug: print(f"{color.OKCYAN}check_DCs: Setting {inp_name} to {assignment[inp_name]} as DC to maintain controlling value at gate {g}{color.ENDC}")
        return assignment


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
        # This is messy. Probably can be optimized; implementing Justify / Propagate functions.
        # But- it seems to work? So don't want to touch it 
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
        while len(Dfront): 
            for G in Dfront:
                if self.debug: print(f"Depth: {depth}, Dfront: {Dfront}")
                c, i = ci.__dict__.get(self.netlist[G]['type'], (None, None))
                if c == None: raise ValueError(f"Unsupported gate type '{self.netlist[G]['type']}' for D-Algorithm simulation.")
                
                
                untried_inputs = [inp for inp in self.netlist[G]['inputs'] if assignment[inp] == 'X']
                if not untried_inputs:
                    if self.debug: print(f"{color.WARNING}Depth: {depth}, all inputs tried, continuing{color.ENDC}")
                    continue
                # Assign not-c to all untried inputs
                for inp in untried_inputs:
                    assignment[inp] = int(not c)
                    if self.debug: print(f"Depth: {depth}, Trying assignment in dfront loop: {inp} = {c}")
                    
                    result = self.D_alg(assignment, depth+1)
                    if self.debug: print(f"Depth: {depth}, Assigment result: {result}")
                    if result is not None:
                        if self.debug: print(f"{color.OKGREEN}Depth: {depth}, Success assigning {inp} to {assignment[inp]}!{color.ENDC}")
                        return result
                    # Backtrack this assignment
                    if self.debug: print(f"{color.WARNING}Depth: {depth}, Failure assigning {inp} to {assignment[inp]}- trying {c}{color.ENDC}")
                    assignment[inp] = c
                return self.D_alg(assignment, depth+1)
            
            Dfront = self.get_D_frontier(assignment)
                    
        Jfront = self.get_J_frontier(assignment)
        if not len(Jfront):
            if self.debug: print(f"Depth: {depth}, J_frontier empty; success")
            return self.check_DCs(assignment) # Assert Don't Cares and return
        
        for G in Jfront:
            if self.debug: print(f"Depth: {depth}, Jfront: {Jfront}")

            untried_inputs = [inp for inp in self.netlist[G]['inputs'] if assignment[inp] == 'X']
            if not untried_inputs:
                continue
            
            c, i = ci.__dict__.get(self.netlist[G]['type'], (None, None))
            if self.debug: print(f"{color.OKBLUE}C/I for gate {G} ({self.netlist[G]['type']}): {c}/{i}{color.ENDC}")
            if c == None: raise ValueError(f"Unsupported gate type '{self.netlist[G]['type']}' for D-Algorithm simulation.")
            for inp in untried_inputs:
                # Try assigning non-controlling value to X
                if assignment[G] in ('D', "D'") and (assignment[inp] != 'D' or assignment[inp] != "D'"):
                    stuck_val = 0 if assignment[G] == 'D' else 1
                    if stuck_val == c:
                        assignment[inp] = int(not c)
                    else:
                        assignment[inp] = c
                elif assignment[G] == int(not c):
                    assignment[inp] = int(not c)
                else: 
                    assignment[inp] = c
                if self.debug: print(f"Depth: {depth}, Trying assignment in jfront loop: {inp} = {assignment[inp]}")
                result = self.D_alg(assignment, depth+1)
                if result is not None:
                    return result
                else: 
                    if self.debug: print(f"Depth: {depth}, Failure assigning {inp} to {assignment[inp]}- trying {c}{color.ENDC}")
                    # Backtrack this assignment
                    nc = self.other_val(c)
                    assignment[inp] = nc
                    return self.D_alg(assignment, depth+1)
                
        return None

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
                ins = [assignment[x] for x in info['inputs']]
                in_names = [x for x in info['inputs']]
                out = assignment[g]
                c, i = ci.__dict__.get(info['type'], (None, None))
                op = dops.__dict__.get(info['type'], None)
                if c is None or op is None: raise ValueError(f"Unsupported gate type '{info['type']}' for D-Algorithm simulation.")
                
                if out in ('D', "D'") and all(v == 'X' for v in ins):
                    if self.debug: print(f"{color.WARNING}Imply_and_Check: Gate {g} output is faulted but all inputs are X- checking input implications made by fault{color.ENDC}")
                    # Gate is faulted, implying inputs to a specific value
                    stuck_val = 0 if out == 'D' else 1
                    
                    if stuck_val == c:
                        targ_val = int(not c)
                    else:      
                        targ_val = c
                        
                    # First, see if setting just one input to targ_val suffices
                    test_sets = [[]]
                    # First test is with just one input set to targ_val, rest X
                    for i in range(0, len(ins)):
                        if i == 0:  test_sets[0].append(targ_val)
                        else:       test_sets[0].append('X')
                    
                    # Then all inputs set to targ_val
                    test_sets.append([targ_val for _ in ins])
                    
                    # Then one input to not targ_val, rest x
                    test_sets.append([])
                    for i in range(0, len(ins)):
                        if i == 0:  test_sets[-1].append(int(not targ_val))
                        else:       test_sets[-1].append('X')
                    # Then all inputs to not targ_val
                    test_sets.append([int(not targ_val) for _ in ins])
                    # One test_set will result in the fault-free output being not(stuck_val)
                    
                    for test_set in test_sets:
                        res = op(test_set)
                        if res != 'X' and res != stuck_val:
                            # Found valid input assignment
                            if self.debug: print(f"{color.OKCYAN}Found valid test set for gate {g} to justify faulted output {out}:{color.ENDC}")
                            for idx, val in enumerate(test_set):
                                if self.debug: print(f"\t{color.OKBLUE}Setting {info['inputs'][idx]} to {val}{color.ENDC}")
                                assignment[info['inputs'][idx]] = val
                                changed = True
                                break

                elif out != "X":
                    continue

                elif all(v in (0, 1, 'D', "D'") for v in ins):
                    # First, check if we have faults on both inputs of current gate
                    # Remember, we sim one fault at a time here. So faults on both inputs -> conflict
                    if all(v in ('D', "D'") for v in ins):
                        # Check which fault line matches gate controlling value 
                        tmp_ins = [1 if v == "D'" else 0 for v in ins]
                        # Change the fault that is not matching controlling value to non-controlling value to allow fault to propagated 
                        if tmp_ins.count(c) == 1:
                            change_idx = tmp_ins.index(int(not c))
                            assignment[in_names[change_idx]] = int(not c)
                            changed = True
                        else: 
                            # Randomly assert one of the inputs to non-controlling value until hopefully one works
                            change_idx = rand(0, len(ins)-1)
                            assignment[in_names[change_idx]] = int(not c)
                            changed = True
                    else: 
                        func = dops.__dict__.get(info['type'])
                        if func is None: raise ValueError(f"Unsupported gate type '{info['type']}' for D-Algorithm simulation.")
                        res = func(ins)
                        # Make sure result matches assignment
                        if res != assignment[g] and res != 'X':
                            if int(not c) == assignment[g] and c in ins:
                                # Need to set one input to non-controlling value
                                for idx, val in enumerate(ins):
                                    if val == c:
                                        assignment[in_names[idx]] = int(not c)
                                        if self.debug: print(f"{color.OKCYAN}Imply_and_Check: Setting {in_names[idx]} to {int(not c)} to achieve output {assignment[g]} at gate {g}{color.ENDC}")
                                        changed = True
                                        break
                        assignment[g] = func(ins)
                        if self.debug: print(f"Imply_and_Check: Assigned {g} = {assignment[g]} with inputs: ")
                        if self.debug: [print(f"\t{x}: {assignment[x]}") for x in info['inputs']]
                        changed = True

        return True

    # --- SOLVE ---
    def solve(self):
        print(f"\t{color.OKGREEN}Generating tests using D-Algorithm{color.ENDC}", end = "")
        for (wire, stuck_val) in self.fault_list:
            print(f"{color.OKGREEN}{color.BOLD}.{color.ENDC}", end = "")
            
            if self.debug: print(f"\n\n\n{color.OKGREEN}Processing fault at {wire} stuck-at-{stuck_val}{color.ENDC}")
            initial_assignment = {w: 'X' for w in self.netlist}
            self.inject_fault(initial_assignment, wire, stuck_val)
            res = self.D_alg(initial_assignment)
            if res is not None:
                self.solutions[(wire, stuck_val)] = res
                if self.debug: print(f"Result for {wire} s-a-{stuck_val}: {res}")
            else:
                print(f"\n")
                print(f"{color.FAIL}No test found for {wire} s-a-{stuck_val}{color.ENDC}")
        print(f"\n\t{color.OKGREEN}{color.BOLD}{color.ITALIC}All possible vectors generated!{color.ENDC}")
        return self.solutions
    
    def refine_solutions(self):
        """
        Refine solutions to just test vectors (PI assignments only)
        """
        for (wire, stuck_val), sol in self.solutions.items():
            pi_assignments = {g: val for g, val in sol.items() if self.is_PI(g)}
            self.refined_solns.append(((wire, stuck_val), pi_assignments))
            
        print(f"\n{color.OKBLUE}{color.BOLD}{color.UNDERLINE}Test Vectors:{color.ENDC}{color.OKBLUE}{color.ITALIC}('DC' indicates a don't care input){color.ENDC}")
        print(f"{color.OKBLUE}{color.ITALIC}There is a risk that not all DCs will be caught- however, the DCs that are caught are true DCs.{color.ENDC}\n")
        print(f"{color.BOLD}{color.OKCYAN}Fault\t| PI Assignments")
        print(f"\t| {'\t| '.join([pi for pi in self.netlist if self.is_PI(pi)])}{color.ENDC}")
        print(f"{'-'*50}")
        for (wire, stuck_val), pi_assignments in self.refined_solns:
            print(f"{color.BOLD}{wire} s-a-{stuck_val}{color.ENDC} | ", end="")
            # Make sure the vector has the opposite value to the stuck-at for PIs with faults 
            pr_assignments = {
                k: v 
                if v in (0,1,'DC') 
                else f"{color.FAIL}{color.BOLD}{1 if v == 'D' else 0}{color.ENDC}"
                for k, v in pi_assignments.items() 
            }
            print("\t| ".join(f"{mod}" for mod in pr_assignments.values()))
        
        return self.refined_solns
    
    def sim_print(self):
        """
        Re-print refined solutions for Simulation
        """
        print(f"{color.BOLD}{color.OKCYAN}Index\t| Fault\t\t| PI Assignments")
        print(f"\t\t\t| {'\t| '.join([pi for pi in self.netlist if self.is_PI(pi)])}{color.ENDC}")
        print(f"{'-'*60}")
        for idx, ((wire, stuck_val), pi_assignments) in enumerate(self.refined_solns):
            print(f"{idx}\t| {color.BOLD}{wire} s-a-{stuck_val}{color.ENDC}\t| ", end="")
            # Make sure the vector has the opposite value to the stuck-at for PIs with faults 
            pr_assignments = {
                k: v 
                if v in (0,1,'DC') 
                else f"{color.FAIL}{color.BOLD}{1 if v == 'D' else 0}{color.ENDC}"
                for k, v in pi_assignments.items() 
            }
            print("\t| ".join(f"{mod}" for mod in pr_assignments.values()))