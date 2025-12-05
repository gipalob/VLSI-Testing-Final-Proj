from typing import Dict, Tuple, NamedTuple
# Hold helper data structures used across the project

# Define coloring constants for CLI
class color:
    """
    sourced from blender build scripts
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'

# Define static resource for c/i values for all supported gate types
class ControllingInversionVals:
    """
    Pre-define controlling values / inversions for gates
    """
    class ci(NamedTuple):
        c: int  # controlling value
        i: int  # inversion value
        
    AND = ci(c=0, i=0)
    NAND = ci(c=0, i=1)
    OR = ci(c=1, i=0)
    NOR = ci(c=1, i=1)
    XOR = ci(c=1, i=1)

# Define operations for processing each gate in terms of simple 0/1
class GateOps:
    """
    Define operations for gate types
    """
    
    AND = lambda inputs: int(all(inputs))
    OR = lambda inputs: int(any(inputs))
    NAND = lambda inputs: int(not all(inputs))
    NOR = lambda inputs: int(not any(inputs))
    XOR = lambda inputs: int(sum(inputs) % 2)
    
# Define static methods for processing each gate in terms of more complex 0/1/'X'/'D'/'~D'
class DGateOps:
    @staticmethod
    def AND(inputs):
        if 0 in inputs:
            return 0
        if 'X' in inputs:
            return 'X'
        if all(x in (1, 'D') for x in inputs):
            if "D" in inputs:
                return 'D'
            else:
                return 1
        if all(x in (1, "D'") for x in inputs):
            if "D'" in inputs:
                return "D'"
            else:
                return 1
        return 'X'
    
    @staticmethod
    def OR(inputs):
        if 1 in inputs:
            return 1
        if 0 in inputs:
            if 'X' in inputs:
                return 'X'
            # All 0/D'
            if all(x in (0, "D'") for x in inputs):
                if "D'" in inputs:
                    return "D'"
                else:
                    return 0
            # All 0/D
            if all(x in (0, "D") for x in inputs):
                if "D" in inputs:
                    return 'D'
                else:
                    return 0
        return 'X'
    
    @staticmethod
    def NOT(input_):
        return {0:1, 1:0, 'D':"D'", "D'":'D', 'X':'X'}[input_]
    
    @staticmethod
    def NAND(inputs):
        return DGateOps.NOT(DGateOps.AND(inputs))
    
    @staticmethod
    def NOR(inputs):
        return DGateOps.NOT(DGateOps.OR(inputs))
    
    @staticmethod
    def XOR(inputs):
        # gf -> 'good' / 'faulty'
        to_gf = {0: (0, 0), 1: (1, 1), 'D': (1, 0), "D'": (0, 1)}
        g = 0
        f = 0
        for v in inputs:
            gi, fi = to_gf[v]
            g ^= gi
            f ^= fi
        if (g, f) == (1, 0):
            return 'D'
        elif (g, f) == (0, 1):
            return "D'"
        elif (g, f) == (0, 0):
            return 0
        elif (g, f) == (1, 1):
            return 1
        else:
            return 'X' 
# Define boilerplate methods for graphing capabilities
class Graph:
    def __init__(self, edge_list: list[tuple]):
        self.graph = {}
        self.edge_list = edge_list
        for u, v in edge_list:
            self._add_edge(u, v, directed=True)

    def add_vertex(self, vertex):
        if vertex not in self.graph:
            self.graph[vertex] = []

    def _add_edge(self, u, v, directed=False):
        self.add_vertex(u)
        self.add_vertex(v)
        self.graph[u].append(v)
        if not directed:
            self.graph[v].append(u) # For undirected graph

    def get_neighbors(self, vertex):
        return self.graph.get(vertex, [])

    def __str__(self):
        return str(self.graph)
    
    
    
# Define Boilerplate for displaying graph generated from circuit
class Visualize:
    def __init__(self, gates: Dict[str, dict], edge_list: list[Tuple[str, str]]):
        self.gates = gates
        self.edge_list = edge_list
        self.pos = {} #position map
        self.color_map = [] #color map
        self._create_pos_map()
        self._create_graph()

    def _create_graph(self):
        import networkx as nx
        self.graph = nx.DiGraph()
        self.graph.add_edges_from(self.edge_list)
        
    def _create_pos_map(self):
        pos = {}
        PI_ct = 0
        for gate, info in self.gates.items():            
            # X is level, Y is y coord of inputs from previous level
            x = info["level"]
            if info["inputs"]:
                y = sum(pos[inp][1] for inp in info["inputs"]) / len(info["inputs"])
            else: #level 0
                y = PI_ct
                PI_ct += 1
            pos[gate] = (x, y)
        
        self.pos = pos
        
    def vis_circuit(self):
        import matplotlib.pyplot as plt
        import networkx as nx
        
        #color map must be in order presented by graph nodes
        if not len(self.color_map):
            self.color_map = [
                'lightgreen' if (typ:= self.gates[node]['type']) == 'PI' else
                'lightblue' if typ == "OR" else
                'blue' if typ == "NOR" else
                'red' if typ == "AND" else
                'coral' if typ == "NAND" else
                'pink' if typ == "XOR" else
                'lightgrey'  # default
                for node in self.graph.nodes()
            ]

        nx.draw(self.graph, self.pos, node_color=self.color_map, node_size=1000, with_labels=True, arrows=True)
        plt.show()
        