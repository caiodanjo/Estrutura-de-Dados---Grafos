from typing import Dict, List, Tuple, Optional
from math import isfinite
from collections import deque


class GrafoTransito:

    def _init_(
        self,
        direcionado: bool = True,
        adjacencia_inicial: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> None:
        """
        Cria o grafo e, opcionalmente, carrega uma estrutura inicial.

        :param direcionado: se True, o grafo é direcionado (ruas de mão única).
        :param adjacencia_inicial: dicionário no formato:
            {
                "A": {"B": 3.5, "C": 10},
                "B": {"C": 2},
                ...
            }
        """
        self.direcionado: bool = direcionado
        self.adj: Dict[str, Dict[str, float]] = {}

        if adjacencia_inicial:
            self._carregar_adjacencia_inicial(adjacencia_inicial)

    # ------------- Somente leitura / inspeção (Etapa 1) --------------

    def intersecoes(self) -> List[str]:
        return sorted(self.adj.keys())

    def ruas(self) -> List[Tuple[str, str, float]]:
        """
        Retorna a lista de ruas (arestas) como tuplas (origem, destino, tempo).
        Útil para inspecionar o estado atual sem modificar nada.
        """
        resultado: List[Tuple[str, str, float]] = []
        for origem, destinos in self.adj.items():
            for destino, tempo in destinos.items():
                resultado.append((origem, destino, tempo))
        return resultado

    def vizinhos(self, intersecao: str) -> List[Tuple[str, float]]:
        """
        Retorna os vizinhos alcançáveis diretamente a partir da interseção informada,
        como lista de tuplas (destino, tempo).
        Não cria, não remove — apenas consulta.
        """
        self._validar_intersecao_nome(intersecao)
        if intersecao not in self.adj:
            return []
        return sorted(self.adj[intersecao].items(), key=lambda p: p[0])

    def possui_intersecao(self, nome: str) -> bool:
        """Verifica se a interseção existe no grafo."""
        return nome in self.adj

    def possui_rua(self, origem: str, destino: str) -> bool:
        """Verifica se existe a rua (aresta) origem -> destino."""
        if origem not in self.adj:
            return False
        return destino in self.adj[origem]

    def numero_de_intersecoes(self) -> int:
        """Quantidade de vértices."""
        return len(self.adj)

    def numero_de_ruas(self) -> int:
        """Quantidade de arestas."""
        return sum(len(destinos) for destinos in self.adj.values())

    def exibir(self) -> str:
        linhas: List[str] = []
        for origem in sorted(self.adj.keys()):
            destinos_fmt = ", ".join(
                f"{dest} ({tempo:.2f} min)" for dest, tempo in sorted(self.adj[origem].items())
            )
            linhas.append(f"{origem} -> {destinos_fmt}")
        return "\n".join(linhas)

    def _repr_(self) -> str:
        return f"GrafoTransito(direcionado={self.direcionado}, intersecoes={len(self.adj)}, ruas={self.numero_de_ruas()})"

    # ------------------ Suporte interno (Etapa 1) --------------------

    def _carregar_adjacencia_inicial(self, adj: Dict[str, Dict[str, float]]) -> None:
        """
        Carrega uma estrutura inicial de adjacência com validação.
        Esta função é usada apenas no construtor (não adiciona/remover depois).
        """
        if not isinstance(adj, dict):
            raise ValueError("adjacencia_inicial deve ser um dicionário de dicionários.")

        # Primeiro cria todas as chaves de origem garantindo nomes válidos
        for origem, destinos in adj.items():
            self._validar_intersecao_nome(origem)
            if origem not in self.adj:
                self.adj[origem] = {}

            if not isinstance(destinos, dict):
                raise ValueError(f"Os destinos de '{origem}' devem ser um dicionário de destino->tempo.")

        # Agora valida cada aresta e copia os tempos
        for origem, destinos in adj.items():
            for destino, tempo in destinos.items():
                self._validar_intersecao_nome(destino)
                self._validar_tempo(float(tempo))
                if destino not in self.adj:
                    # Garante que toda interseção destino também exista como chave (mesmo sem saída)
                    self.adj[destino] = {}
                self.adj[origem][destino] = float(tempo)

    @staticmethod
    def _validar_intersecao_nome(nome: str) -> None:
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Nome da interseção deve ser uma string não vazia.")

    @staticmethod
    def _validar_tempo(tempo_min: float) -> None:
        if not isinstance(tempo_min, (int, float)):
            raise ValueError("Tempo deve ser numérico (int ou float).")
        if not isfinite(tempo_min) or tempo_min <= 0:
            raise ValueError("Tempo deve ser um número finito e maior que zero.")
        
    # ------------------ Manipulação (Etapa 2) --------------------

    def adicionar_intersecao(self, nome: str) -> None:
        """
        Adiciona uma nova interseção (vértice) ao grafo.
        Se já existir, não faz nada.
        """
        self._validar_intersecao_nome(nome)
        if nome not in self.adj:
            self.adj[nome] = {}

    def remover_intersecao(self, nome: str) -> None:
        """
        Remove a interseção informada e todas as ruas ligadas a ela.
        """
        self._validar_intersecao_nome(nome)
        if nome not in self.adj:
            raise ValueError(f"Interseção '{nome}' não existe e não pode ser removida.")

        # Remove todas as ruas de origem nesta interseção
        del self.adj[nome]

        # Remove todas as ruas que chegam nela
        for origem in list(self.adj.keys()):
            if nome in self.adj[origem]:
                del self.adj[origem][nome]

    def adicionar_rua(self, origem: str, destino: str, tempo_min: float) -> None:
        """
        Adiciona uma rua (aresta) com o tempo de deslocamento.
        Se o grafo não for direcionado, cria também a rua inversa.
        """
        self._validar_intersecao_nome(origem)
        self._validar_intersecao_nome(destino)
        self._validar_tempo(tempo_min)

        if origem not in self.adj:
            self.adj[origem] = {}
        if destino not in self.adj:
            self.adj[destino] = {}

        self.adj[origem][destino] = float(tempo_min)

        if not self.direcionado:
            self.adj[destino][origem] = float(tempo_min)

    def remover_rua(self, origem: str, destino: str) -> None:
        """
        Remove a rua (aresta) origem -> destino.
        Se o grafo não for direcionado, remove também o caminho inverso.
        """
        self._validar_intersecao_nome(origem)
        self._validar_intersecao_nome(destino)

        if origem not in self.adj or destino not in self.adj[origem]:
            raise ValueError(f"Rua de '{origem}' para '{destino}' não existe.")

        del self.adj[origem][destino]

        if not self.direcionado and destino in self.adj and origem in self.adj[destino]:
            del self.adj[destino][origem]

    def listar_caminhos(self, origem: str) -> List[List[str]]:
        """
        Lista todos os caminhos possíveis a partir de uma interseção.
        Usa busca em profundidade (DFS).
        """
        self._validar_intersecao_nome(origem)
        if origem not in self.adj:
            raise ValueError(f"Interseção '{origem}' não existe no grafo.")

        caminhos: List[List[str]] = []

        def dfs(atual: str, caminho: List[str]):
            for vizinho in self.adj[atual]:
                if vizinho not in caminho:  # evita ciclos
                    novo_caminho = caminho + [vizinho]
                    caminhos.append(novo_caminho)
                    dfs(vizinho, novo_caminho)

        dfs(origem, [origem])
        return caminhos

    def existe_trajeto(self, origem: str, destino: str) -> bool:
        """
        Verifica se existe algum caminho entre origem e destino.
        Usa busca em largura (BFS).
        """
        self._validar_intersecao_nome(origem)
        self._validar_intersecao_nome(destino)

        if origem not in self.adj or destino not in self.adj:
            raise ValueError("Uma das interseções informadas não existe.")

        visitados = set()
        fila = deque([origem])

        while fila:
            atual = fila.popleft()
            if atual == destino:
                return True
            visitados.add(atual)
            for vizinho in self.adj[atual]:
                if vizinho not in visitados:
                    fila.append(vizinho)

        return False