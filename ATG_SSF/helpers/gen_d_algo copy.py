from .helpers import color as c
from .helpers import Graph
from .helpers import ControllingInversionVals as ci
from .helpers import GateOps as ops
from .fault_collapse import Faults
from typing import Tuple, Optional

class DAlgo_Gen:
    def __init__(self, gates, graph: Graph, fault: Faults):
        """
        Generate test vectors using D-Algorithm
        """
        self.d_front = [] #All gates whose output value is currently x but have one or more error signals on their inputs
        self.j_front = [] #All gates whose output is known, but not implied by inputs
        self.fault = fault
        self.gates = gates
        self.graph = graph
        self.PIs = [k for k, v in gates.items() if v["type"] == "PI"]
        
        print(f"{c.BOLD}{c.HEADER}Select an option for D-Algorithm test generation:{c.ENDC}")
        print(f"{c.OKCYAN}", end="")
        print(f"[1] Generate test vector(s) for a specific fault")
        print(f"[2] Generate test vectors for all faults")
        print(f"[3] Determine detectable faults for a specific input vector")
        print(f"{c.ENDC}", end="")
        
        choice = -1
        while choice not in [1, 2, 3]:
            if choice == 0:
                print(f"{c.FAIL}{c.BOLD}Invalid choice. Please enter 1, 2, or 3.{c.ENDC}")
                
            print(f"{c.HEADER}{c.BOLD}Enter choice (1-3): {c.ENDC}", end="")
            try:
                choice = int(input().strip())
                if choice not in [1, 2, 3]: 
                    choice = 0
            except:
                choice = 0
        if choice == 1:
            self.specific_fault()
        elif choice == 2:
            self.all_faults()
        elif choice == 3:
            self.detectability()
                
    def specific_fault(self):
        self.fault.print_fault_classes(indices=True)
        print(f"{c.HEADER}{c.BOLD}Enter the index of the fault to generate a test vector for: {c.ENDC}", end="")
        chosen = None
        avail = [k for k in self.fault.fault_list.keys()]
        while not chosen:
            inp = input().strip()
            try: 
                inp = int(inp)
                chosen = avail[inp]
                if inp < 0 or inp >= len(avail):
                    raise IndexError
            except:
                print(f"{c.FAIL}{c.BOLD}Invalid input. Please enter a valid fault index.{c.ENDC}", end="")
                chosen = None
                
            else:
                chosen = avail[int(inp)]
        
        chosen_fault = {chosen: self.fault.fault_list[chosen]}
        self.d_algorithm(chosen_fault=chosen_fault)
        
    
    def all_faults(self):
        # Keyed by tuple of (gate, fault), as a single gate can have multiple displayable faults
        fault_vectors = {}
        for gate, faults in self.fault.fault_list.items():
            for f in faults:
                chosen_fault = {gate: f}
                print(f"{c.HEADER}{c.BOLD}Generating test vector for fault s-a-{f} at gate {gate}:{c.ENDC}")
                fault_vectors[(gate, f)] = self.d_algorithm(chosen_fault=chosen_fault)
                
    
    def detectability(self):
        print(f"{c.HEADER}{c.BOLD}Enter the input vector: {c.ENDC}", end="")
        chosen_inps = {}
        for pi in self.PIs:
            val = None
            while val not in ['0', '1']:
                print(f"{c.HEADER}{c.BOLD}{pi}: {c.ENDC}", end="")
                val = input().strip()
                if val not in ['0', '1']:
                    print(f"{c.FAIL}{c.BOLD}Invalid input. Please enter 0 or 1.{c.ENDC}", end="")
            chosen_inps[pi] = int(val)
        self.d_algorithm(chosen_inps=chosen_inps)
    
    def d_algorithm(self, *args, **kwargs):
        """
        Run a D-algorithm for a fault. 
        Only runs on a single fault; matching of generated vectors to faults will be handled by callee
        """
        chosen_fault = kwargs.get("chosen_fault", {})
        chosen_inps = kwargs.get("chosen_inps", {})
        
        if not chosen_fault and not chosen_inps:
            raise ValueError("Either 'chosen_fault' or 'chosen_inps' must be provided to run D-Algorithm.")
        
        try:
            assert isinstance(chosen_fault, dict)
        except:
            raise ValueError("'chosen_fault' must be a dictionary mapping gates to faults.")
        try:
            assert isinstance(chosen_inps, dict)
        except:
            raise ValueError("'chosen_fault' must be a dictionary mapping gates to faults.")
        
        circuit_vals = {gate: 'x' for gate in self.gates.keys()}
        solved = False
        gate_list = [gate for gate in self.gates.keys()]
        idx = -1
        
        for pi, val in chosen_inps.items():
            circuit_vals[pi] = val
        
        # Start evaluation at the first gate with an induced fault
        for gate in gate_list:
            if gate in chosen_fault.keys():
                idx = gate_list.index(gate)
                break
        if idx == -1:
            idx = 0
        
        def justify(gate, fault, targ) -> Tuple[list, bool]:
            """
            Justify a fault at a given gate
            """
            if fault:
                targ = not fault # We need to justify the opposite value to activate the fault
            gate_type = self.gates[gate]["type"]
            inps = self.gates[gate]["inputs"]
            
            # Determine blend of inputs to achieve target output
            ci_vals = getattr(ci, gate_type, None)
            op_func = getattr(ops, gate_type, None)
            if ci_vals is None or op_func is None:
                raise ValueError(f"Unsupported gate type '{gate_type}' for justification.")
            c, i = ci_vals
            
            
            for inp in inps:
                if circuit_vals[inp] == 'x':
                    res = justify(inp, None)
                            
        found_faults = []
        test_vectors = [{}]                  
        
        while not solved:
            curGate = gate_list[idx]
            
            if curGate in chosen_fault.keys():
                circuit_vals[curGate] = ("s-a", chosen_fault[curGate])
                res = justify(curGate, chosen_fault[curGate], None)
                if res[0][0] == "PI":
                    neighbors = self.graph.get_neighbors(curGate)
                    if neighbors:
                        [self.d_front.append(n) for n in neighbors if n not in self.d_front]
            else:
                for inp in self.gates[curGate]["inputs"]:
                    if circuit_vals[inp] == 'x':
                        continue
                    elif "s-a" in circuit_vals[inp]:
                        # We need to justify current gate such that fault is propagated
                        
                        
                        
            
                
                
