from .menu import Menu
import sys

# Program entrypoint
if __name__ == "__main__":
    debug = False
    if len(sys.argv) != 2:
        if len(sys.argv) == 3 and "--debug" in sys.argv[2]:
            flag = sys.argv[2].split('=')[1].lower()
            if flag == 'true':
                debug = True
        else:
            print("Usage: python -m ATG_SSF <path_to_circuit_file> --debug = bool, default false")
            sys.exit(1)
        
    fpath = sys.argv[1]
    
    
    ui = Menu(fpath, debug = debug)
    ui.en_features()
    ui.print_menu()
