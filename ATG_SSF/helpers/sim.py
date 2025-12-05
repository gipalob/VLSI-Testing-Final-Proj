from .fault_collapse import Faults
from .helpers import color, Graph, GateOps

# This modular file contains logic for Simulating the circuit given an input and injected faults
# This process works by prompting the user for each input, and leverages "healthy" and "faulty" versions of the circuit

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
        
        # Get user input
        self.init_print()
        
        # Run "healthy" sim
        self.sim_vals["healthy"] = self.simulate(self.sim_vals["healthy"])
        # Conditionally run "faulted" sim
        if len(self.chosen_faults) > 0:
            self.sim_vals["faulted"] = self.simulate(self.sim_vals["faulted"], sim_fault=True)
    
    def init_print(self):
        """
        Print available faults, get PIs for test
        """
        print(f"{color.HEADER}{color.BOLD}Would you like to simulate any faults (Y/N)? {color.ENDC}", end="")
        choice = input().strip().lower()
        if choice == 'y':
            # Enumerate collapsed fault list
            print(f"{color.HEADER}{color.BOLD}Fault list to choose from:{color.ENDC}\n")
            self.faults.print_fault_classes(indices=True)
            # Read comma separated list of faults to apply
            print(f"\n{color.HEADER}{color.BOLD}Input the indices of the faults you would like to simulate, comma seperated: {color.ENDC}", end="")
            inp = [int(i.strip()) for i in input().strip().split(",") if i.strip().isdigit()]
            print(f"{color.HEADER}{color.BOLD}Chosen fault #s:{color.ENDC}")
            print(f"\t{inp}")

            # Get subset of faults selected by user
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
            
        # Print each PI and prompt user for a 0/1 value for each
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
        # Display the chosen input vector to the user
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
        # Set all gates to unknown
        sim_vals = {gate_name: 'x' for gate_name in self.gates.keys()}
        
        # Set PIs to user specified values
        [sim_vals.update({pi: self.chosen_inps[pi]}) for pi in self.chosen_inps.keys()]
        
        # Override PIs if applicable faults are enabled
        if sim_fault:
            for gate in sim_vals.keys():
                if self.gates[gate]["type"] == "PI" and gate in self.chosen_faults:
                    fault_val = self.chosen_faults[gate]
                    print(f"{color.WARNING}{color.BOLD}Injecting fault on PI '{gate}': forcing output to {fault_val}{color.ENDC}")
                    sim_vals[gate] = ("fault", fault_val)
        
        # Get gates with PIs set
        gate_list = [gate for gate in self.gates.keys()]
        current = 0 # Start with PI 0
    
        # Loop gates till all values are known
        while 'x' in sim_vals.values():
            # Roll over - no indexing errors
            if current >= len(gate_list):
                # Find next unknown gate
                for g, v in sim_vals.items():
                    if v == 'x':
                        current = gate_list.index(g)
                        break
                continue
            # Source info for current gate
            gate = gate_list[current]
            gate_dat = self.gates[gate]
            output = self.graph.get_neighbors(gate)
            # Skip solved gates
            if sim_vals[gate] != 'x':
                current = gate_list.index(output[0]) if output else current + 1
                continue
            # Skip PI
            if gate_dat["type"] == "PI":
                sim_vals[gate] = self.chosen_inps[gate]
                current = gate_list.index(output[0]) if output else current + 1 # move Greedily
                continue
            # Case where current gate needs to be solved
            else: 
                # Get current gate's input gates
                inputs = {inp: sim_vals[inp] for inp in gate_dat["inputs"]}
                # If current gate has unknown input, solve that input first
                if 'x' in inputs.values():
                    for inp_name, inp_val in inputs.items():
                        if inp_val == 'x':
                            # Cannot evaluate current gate, first must justify undetermined input
                            current = gate_list.index(inp_name)
                            break
                    continue
                # Case where current gate can be solved now
                else:
                    # All inputs known, evaluate gate
                    # This method also supports n-input gates :) 
                    gate_func = getattr(GateOps, gate_dat["type"], None)
                    
                    if gate_func is None:
                        raise ValueError(f"Unsupported gate type '{gate_dat['type']}' for simulation.")
                    eval_set = []

                    # Get gate output, checking for fault
                    for g, i in inputs.items():
                        if isinstance(i, tuple) and i[0] == "fault":
                            eval_set.append(i[1])
                        else:
                            eval_set.append(i)
                    sim_vals[gate] = gate_func(eval_set)
                                        
                    # Inject fault if enabled
                    if gate in self.chosen_faults and sim_fault:
                        fault_val = self.chosen_faults[gate]
                        print(f"{color.WARNING}{color.BOLD}Injecting fault on gate '{gate}': forcing output to {fault_val}{color.ENDC}")
                        sim_vals[gate] = ("fault", fault_val)
                        
                    current = gate_list.index(output[0]) if output else current + 1 # Greedily move through gates
        # Return outputs once all gate values are known
        return sim_vals
        
    # Method for printing simulation results from sim_vals, comparing healthy and faulted circuits
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
        
                    
                    
                    
                

            
            
            