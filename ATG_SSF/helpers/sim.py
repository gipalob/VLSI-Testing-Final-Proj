from .fault_collapse import Faults
from .helpers import color
class Simulate:
    def __init__(self, gates, graph, faults: Faults, en_feat):
        self.gates = gates
        self.graph = graph
        self.faults = faults
        self.en_feat = en_feat
        
        self.chosen_inps = {}
        self.chosen_faults = {}
        
        self.init_print()
        self.simulate()
    
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

            # this one's pretty bad lol
            # this is sooooooooooooooo python 
            self.chosen_faults = dict(
                {
                    idx: (gate, f)
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
        
        
    def simulate(self):
        PO_ct = sum(1 for g in self.gates.values() if g["level"] == max(g["level"] for g in self.gates.values()))
        PO_vals = {}
        while len(PO_vals) != PO_ct:
            pass