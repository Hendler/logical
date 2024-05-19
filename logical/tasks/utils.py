import os



ROOT_REPO_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))




def double_line(line):
    print(line)
    print(line)


def printlogo() :
    os.system("clear")
    ENDC = "\033[0m"

    RED = "\033[48;5;88m"
    WHITE = "\033[48;5;188m"

    W = WHITE + "    "
    WP = WHITE + "              "
    R = RED + "    "

    double_line(WP + W + W + W + W + W + W + W + WP)
    double_line(WP + R + W + R + W + R + W + R + WP)
    double_line(WP + R + R + R + R + W + R + W + WP)
    double_line(WP + R + W + R + R + R + R + R + WP)
    double_line(WP + W + W + W + W + W + W + W + WP)
    print(ENDC)
    print("                  2013-2023 HAI.AI, LLC            ")
    print("")
    print("WELCOME TO LOGICAL - beep \a beep \a")



