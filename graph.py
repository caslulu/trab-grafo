"Grafo implementado sem uso de bibliotecas externas para futura remoção de blibiotecas no futuro para atender a necessidade de não utilizar bibliotecas externas. - Caio Kfuri"

class Graph:
    def __init__(self):
        self.vertices = {}
        self.arestas = []

    def add_vertice(self, v):
        if v not in self.vertices:
            self.vertices[v] = []

    def add_aresta(self, u, v):
        self.add_vertice(u)
        self.add_vertice(v)
        aresta = (u, v)
        if aresta not in self.arestas:
            self.arestas.append(aresta)
            self.vertices[u].append(v)

    def vizinhos(self, v):
        return self.vertices.get(v, [])

    def __repr__(self):
        return f"Graph(V={len(self.vertices)}, E={len(self.arestas)})"


    def kahn(self): "Método para ordenação topológica usando o algoritmo de Kahn."

    def dfs_cicle(self): "Método para detecção de ciclos usando busca em profundidade (DFS)."


if __name__ == "__main__":
    g = Graph()
    # Exemplo: 'libssl' é pré-requisito de 'curl' e 'python'
    g.add_aresta("libssl", "curl")
    g.add_aresta("libssl", "python")
    g.add_aresta("python", "minha_aplicacao")
    print("Grafo criado:", g)
    print("\nLista de Adjacência:")
    for vertice, vizinhos in g.vertices.items():
        print(f"  {vertice} -> {vizinhos}")
