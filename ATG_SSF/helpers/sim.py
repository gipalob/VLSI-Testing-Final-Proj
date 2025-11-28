from .fault_collapse import Faults
from .helpers import color, Graph, GateOps
class Simulate:
    def __init__(self, gates, graph: Graph, faults: Faults, en_feat: bool = False, debug: bool = False):
        self.gates = gates
        self.graph = graph
        self.faults = faults
        self.en_feat = en_feat
        self.debug = debug
        self.chosen_inps = {}
        self.chosen_faults = {}
        self.sim_vals = {"faulted": {}, "healthy": {}}
        
        self.init_print()
        self.sim_vals["healthy"] = self.simulate(self.sim_vals["healthy"])
        if len(self.chosen_faults) > 0:
            self.sim_vals["faulted"] = self.simulate(self.sim_vals["faulted"], sim_fault=True)
    
    def init_print(self):
        """
        Print available faults, get PIs for test
        """
        print(f"{color.HEADER}{color.BOLD}Would you like to simulate any faults (Y/N)? {color.ENDC}", end="")
        choice = input().strip().lower()
        if choice == 'y':
            print(f"{color.HEADER}{color.BOLD}Fault list to choose from:{color.ENDC}\n")
            self.faults.print_fault_classes(indices=True)
            print(f"\n{color.HEADER}{color.BOLD}Input the indices of the faults you would like to simulate, comma seperated: {color.ENDC}", end="")
            inp = [int(i.strip()) for i in input().strip().split(",") if i.strip().isdigit()]
            print(f"{color.HEADER}{color.BOLD}Chosen fault #s:{color.ENDC}")
            print(f"\t{inp}")

            # this one's pretty bad lol. not integer addressed, actually maps to {gate: fault}
            # this is sooooooooooooooo python 
            self.chosen_faults = dict(
                {
                    idx: (gate, int(f))
                    for idx, (gate, faults) in enumerate(self.faults.fault_list.items()) 
                    for f in faults
                    if faults
                }[i] 
                for i in inp
            )
        else:
            print(f"{color.OKGREEN}{color.BOLD}No faults will be simulated.{color.ENDC}")
            
        PIs = [gate for gate, gdata in self.gates.items() if gdata["type"] == "PI"]
        print(f"\n{color.HEADER}{color.BOLD}Input PI vector:{color.ENDC}")
        for pi in PIs:
            val = -1
            while val not in [0, 1]:
                print(f"\t{color.OKCYAN}{color.BOLD}{pi}:  {color.ENDC}", end="")
                try:
                    val = int(input().strip())
                except:
                    val = -1
            self.chosen_inps[pi] = val
        print(f"\n{color.OKGREEN}{color.BOLD}Input vector set:{color.ENDC}")
        [
            print(f"\t{pi}: {val}") 
            for pi, val 
            in self.chosen_inps.items()
        ]
        
    def _get_gates(self, inp):
        """
        Get gates connected to a particular input
        """    
        return [
            gate 
            for gate, gdata 
            in self.gates.items() 
            if inp in gdata["inputs"]
        ]
    
    def simulate(self, sim_vals: dict, sim_fault: bool = False):
        """
        Event-Driven simulation of circuit.
        """        
        sim_vals = {gate_name: 'x' for gate_name in self.gates.keys()}
        
        # Init PI vals
        [sim_vals.update({pi: self.chosen_inps[pi]}) for pi in self.chosen_inps.keys()]
        
        # Make sure we assert PI to chosen faults (if any)
        if sim_fault:
            for gate in sim_vals.keys():
                if self.gates[gate]["type"] == "PI" and gate in self.chosen_faults:
                    fault_val = self.chosen_faults[gate]
                    print(f"{color.WARNING}{color.BOLD}Injecting fault on PI '{gate}': forcing output to {fault_val}{color.ENDC}")
                    sim_vals[gate] = ("fault", fault_val)
        
        gate_list = [gate for gate in self.gates.keys()]
        current = 0 # Start with PI 0
    
        while 'x' in sim_vals.values():
            # Make sure we don't over-index
            if current >= len(gate_list):
                # There are still undetermined values, find next 'x' gate
                for g, v in sim_vals.items():
                    if v == 'x':
                        current = gate_list.index(g)
                        break
                continue
                
            gate = gate_list[current]
            gate_dat = self.gates[gate]
            output = self.graph.get_neighbors(gate)
            if sim_vals[gate] != 'x':
                # Gate already evaluated, move to next gate
                current = gate_list.index(output[0]) if output else current + 1
                continue
            if gate_dat["type"] == "PI":
                sim_vals[gate] = self.chosen_inps[gate]
                current = gate_list.index(output[0]) if output else current + 1 # Greedily move through gates
                continue
            else: 
                # Get current gate's input gates
                inputs = {inp: sim_vals[inp] for inp in gate_dat["inputs"]}
                if 'x' in inputs.values():
                    for inp_name, inp_val in inputs.items():
                        if inp_val == 'x':
                            # Cannot evaluate current gate, first must justify undetermined input
                            current = gate_list.index(inp_name)
                            break
                    continue
                else:
                    # All inputs known, evaluate gate
                    # This method also supports n-input gates :) 
                    gate_func = getattr(GateOps, gate_dat["type"], None)
                    
                    if gate_func is None:
                        raise ValueError(f"Unsupported gate type '{gate_dat['type']}' for simulation.")
                    eval_set = []
                    for g, i in inputs.items():
                        if isinstance(i, tuple) and i[0] == "fault":
                            eval_set.append(i[1])
                        else:
                            eval_set.append(i)
                    sim_vals[gate] = gate_func(eval_set)
                                        
                    # Check if fault is to be injected here
                    if gate in self.chosen_faults and sim_fault:
                        fault_val = self.chosen_faults[gate]
                        print(f"{color.WARNING}{color.BOLD}Injecting fault on gate '{gate}': forcing output to {fault_val}{color.ENDC}")
                        sim_vals[gate] = ("fault", fault_val)
                        
                    current = gate_list.index(output[0]) if output else current + 1 # Greedily move through gates
        return sim_vals
        
    def print_sim(self):
        """
        Print simulation results
        """
        print(f"\n{color.HEADER}{color.BOLD}Simulation Results:{color.ENDC}\n")
        
        if len(self.chosen_faults) > 0:
            print(f"{color.BOLD}{color.UNDERLINE}{'Gate':<10} | {'Healthy':<10} | {'Faulted Circuit':<20}{color.ENDC}")
            for gate, val in self.sim_vals["faulted"].items():
                if isinstance(val, tuple) and val[0] == "fault":
                    print(f"{color.FAIL}{gate:<10} | {self.sim_vals['healthy'][gate]:<10} | {val[1]:<10} (fault injected){color.ENDC}")
                else:
                    print(f"{gate:<10} | {self.sim_vals['healthy'][gate]:<10} | {val:<10}")
        else:
            print(f"{color.BOLD}{color.UNDERLINE}{'Gate':<10} | {'Value':<10}{color.ENDC}")
            for gate, val in self.sim_vals["healthy"].items():
                if isinstance(val, tuple) and val[0] == "fault":
                    print(f"{color.FAIL}{gate:<10} | {val[1]:<10} (fault injected){color.ENDC}")
                else:
                    print(f"{gate:<10} | {val:<10}")
        
                    
                    
                    
                

            
            
            