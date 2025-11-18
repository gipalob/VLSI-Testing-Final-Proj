from .helpers import color as c
from .helpers import Graph
from .fault_collapse import Faults

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
                if choice not in [1, 2, 3]: choice = 0
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
        idx = -1
        while idx < 0:
            inp = input().strip()
            if not isinstance(inp, int) or inp not in range(len(self.fault.fault_list.keys())):
                print(f"{c.FAIL}{c.BOLD}Invalid input. Please enter a valid fault index.{c.ENDC}", end="")
                idx = -1
            else:
                idx = int(inp)
    
    def all_faults(self):
        pass
    
    def detectability(self):
        pass
    
    def d_algorithm(self, *args, **kwargs):
        chosen_faults = kwargs.get("chosen_faults", None)
        chosen_inps = kwargs.get("chosen_inps", None)
        
        if not chosen_faults and not chosen_inps:
            raise ValueError("Either 'chosen_faults' or 'chosen_inps' must be provided to run D-Algorithm.")
        
        
            
        
        
        
        
        