from .menu import Menu
import sys
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m ATG_SSF <path_to_circuit_file>")
        sys.exit(1)
    fpath = sys.argv[1]
    
    
    ui = Menu(fpath)
    ui.en_features()
    ui.print_menu()
