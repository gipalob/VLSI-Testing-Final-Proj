from .menu import Menu
import sys
if __name__ == "__main__":
    fpath = sys.argv[1]
    ui = Menu(fpath)
    ui.en_features()
    ui.print_menu()
