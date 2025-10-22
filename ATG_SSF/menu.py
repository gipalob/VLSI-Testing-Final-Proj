from .helpers.proc_netlist import process_netlist
from .helpers.helpers import color as c

def get_file_lines(fname: str) -> list[str]:
    file_lines = []
    try:
        file_lines = [
            line.strip() 
            for line in open(fname, "r").readlines()
            if line.strip()
        ]
    except Exception as e:
        print(f"{c.FAIL}Error reading file '{fname}': {e}{c.ENDC}")
        return []
    return file_lines


class Menu:
    def __init__(self, fname: str):
        self.fname = fname
        #first, validate file and get into list
        self.file_lines = get_file_lines(fname)
        if not self.file_lines:
            print(f"{c.FAIL}File '{fname}' is empty.{c.ENDC}")
            return
        self.gates = None
        self.graph = None
        self.en_feat = False
        self.vis = None


    def en_features(self):
        print(f"{c.OKCYAN}{c.BOLD}Would you like to enable additional features?{c.ENDC} {c.OKGREEN}('Y' / 'N' / 'info'){c.ENDC}{c.OKCYAN}{c.BOLD}: {c.ENDC}", end="")
        choice = input().strip().lower()
        if choice == 'y': 
            try:
                self.features()
                self.en_feat = True
            except Exception as e:
                print(f"{c.FAIL}Error: {e}{c.ENDC}")
                print(f"{c.FAIL}Keeping additional features disabled.{c.ENDC}")
                self.en_feat = False
        elif choice == 'info':
            self.features(info = True)
        
    def features(self, *args, **kwargs):
        if kwargs.get("info", False) == True:
            print("To use additional features, you must pip install -r add_feat.txt")
            print("Additional features include:")
            print("\t- Circuit Graph Visualization")
            
            self.en_features()
        else: 
            try:
                import matplotlib.pyplot as plt
                import networkx as nx
                print(f"{c.OKGREEN}{c.BOLD}Additional features enabled.{c.ENDC}")
            except ImportError as e:
                raise ImportError("Required packages for additional features not found. Please install 'matplotlib' and 'networkx'.") from e
        
    def print_menu(self):
        #loop until valid input is given
        choice = -1           

        while choice == -1:        
            menu_elements = {
                "0": "Read the input net-list",
                "1": "Perform fault collapsing",
                "2": "List fault classes",
                "3": "Simulate",
                "4": "Generate tests (D-Algorithm)",
                "5": "Generate tests (PODEM)",
                "6": "Generate tests (Boolean Satisfaibility)",
                "7": "Exit"
            }
            
            [print(f"{c.OKCYAN}[{k}]: {c.BOLD}{v}{c.ENDC}") for k, v in menu_elements.items()]
            print(f"{c.BOLD}Selection: {c.ENDC}", end="")
            choice = input().strip()
            
            #input validation
            try:
                choice = int(choice)
                assert choice < 8 and choice >= 0
            except ValueError:
                print(f"{c.FAIL}Invalid selection.{c.ENDC}")
                choice = -1
        
        if choice == 0:
            self.gates, self.graph = process_netlist(self.file_lines)
            print(f"\t{c.OKGREEN}Netlist processed successfully.{c.ENDC}")
            
            if self.en_feat:
                from .helpers.helpers import Visualize
                self.vis = Visualize(self.gates, self.graph.edge_list)
                
                print(f"\t{c.OKGREEN}Would you like to view the circuit's graph visualization? ('Y' / 'N'): {c.ENDC}", end="")
                v_choice = input().strip().lower()
                if v_choice == 'y':
                    self.vis.vis_circuit()
                        
        elif choice == 1:
            pass
        elif choice == 2:
            pass
        elif choice == 3:
            pass
        elif choice == 4:
            pass
        elif choice == 5:
            pass
        elif choice == 6:
            pass
        elif choice == 7:
            print("Exiting...")
            exit(0)
            
        self.print_menu()  # Return to menu after action
                