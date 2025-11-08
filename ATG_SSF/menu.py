from .helpers.proc_netlist import process_netlist
from .helpers.fault_collapse import Faults
from .helpers.helpers import color as c
import os

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
        exit(1)
    return file_lines


class Menu:
    def __init__(self, fname: str):
        self.fname = fname
        #first, validate file and get into list
        self.file_lines = get_file_lines(fname)
        if not self.file_lines:
            print(f"{c.FAIL}File '{fname}' is empty.{c.ENDC}")
            exit(1)
        self.gates = None
        self.graph = None
        self.en_feat = False
        self.vis = None
        self.fault_list = None
        
    def clear(self):
        # windows
        if os.name == 'nt':
            _ = os.system('cls')
        # macOS/Linux
        else:
            _ = os.system('clear')


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
        elif choice == 'n':
            self.en_feat = False
            print(f"{c.WARNING}Additional features disabled.{c.ENDC}")
        elif choice == 'info':
            self.features(info = True)
        else: 
            print(f"{c.WARNING}Invalid choice.{c.ENDC}")
            self.en_features()
        
    def features(self, *args, **kwargs):
        if kwargs.get("info", False) == True:
            print("To use additional features, you must pip install -r ./ATG_SSF/requirements.txt")
            print("Additional features include:")
            print("\t- Circuit Graph Visualization")
            
            self.en_features()
        else: 
            try:
                import matplotlib.pyplot as plt
                import networkx as nx
                print(f"{c.OKGREEN}{c.BOLD}Additional features enabled.{c.ENDC}")
            except ImportError as e:
                raise ImportError("Required packages for additional features not found. Please pip install -r ./ATG_SSF/requirements.txt.") from e
        
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
            print(f"\n{c.HEADER}{c.BOLD}Main Menu:{c.ENDC}")
            [
                print(f"{c.OKCYAN}[{k}]: {c.BOLD}{v}{c.ENDC}") 
                for k, v in menu_elements.items()
            ]
            print(f"{c.BOLD}Selection: {c.ENDC}", end="")
            choice = input().strip()
            
            #input validation
            # clear menu after sel made
            # self.clear()
            try:
                choice = int(choice)
                assert choice < 8 and choice >= 0
            except ValueError:
                print(f"{c.FAIL}Invalid selection: {choice}{c.ENDC}")
                choice = -1
        
        
        
        if choice == 0:
            self.gates, self.graph = process_netlist(self.file_lines)
            print(f"\t{c.OKGREEN}Netlist processed successfully.{c.ENDC}")
            
            if self.en_feat:
                from .helpers.helpers import Visualize                
                print(f"\t{c.OKGREEN}Would you like to view the circuit's graph visualization? ('Y' / 'N'): {c.ENDC}", end="")
                v_choice = input().strip().lower()
                if v_choice == 'y':
                    self.vis = Visualize(self.gates, self.graph.edge_list)
                    self.vis.vis_circuit()
                        
        elif choice == 1:
            if (self.gates and self.graph):
                if (not self.fault_list):
                    self.fault_list = Faults(self.gates, self.graph)
                    
                self.fault_list.collapse()
                print(f"\t{c.OKGREEN}Fault collapsing completed successfully.{c.ENDC}")
            else:
                print(f"{c.FAIL}Please process the netlist first (Option 0).{c.ENDC}")
                
        elif choice == 2:
            if self.fault_list:
                self.fault_list.print_fault_classes()
            else:
                print(f"{c.FAIL}Please perform fault collapsing first (Option 1).{c.ENDC}")
            
        elif choice == 3:
            if (self.gates and self.graph and self.fault_list):
                from .helpers.sim import Simulate
                Simulate(self.gates, self.graph, self.fault_list, self.en_feat)
            else:
                print(f"{c.FAIL}Please ensure that the netlist is processed and fault collapsing is performed first (Options 0 and 1).{c.ENDC}")
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
                