from .helpers import color as c
from .helpers import Graph

class DAlgo_Gen:
    def __init__(self, gates, graph: Graph, faults):
        """
        Generate test vectors using D-Algorithm
        """
        print(f"{c.BOLD}{c.HEADER}Select an option for D-Algorithm test generation:{c.ENDC}")
        print(f"{c.OKCYAN}", end="")
        print(f"[1] Generate test vector(s) for a specific fault")
        print(f"[2] Generate test vectors for all faults")
        print(f"[3] Determine if a fault is detectable for a specific input vector")
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
        pass
    
    def all_faults(self):
        pass
    
    def detectability(self):
        pass
        
        
        
        
        