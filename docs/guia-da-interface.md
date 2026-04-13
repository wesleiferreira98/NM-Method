# Guia da interface

A interface compara `UCTαβ` contra `UCT` em um Mini Gomoku local. Ela foi construída para acompanhar a ideia central do artigo “Ancestor-Based α-β Bounds for Monte-Carlo Tree Search”: usar informações dos ancestrais do caminho de seleção para modular a exploração do MCTS.

## Configuração

O painel lateral permite ajustar:

- **Partidas**: quantidade de jogos da comparação.
- **Simulações por lance**: orçamento de MCTS em cada jogada.
- **Constante UCT C**: peso de exploração do UCT padrão.
- **Constante Cαβ**: peso usado no cálculo dos limites ancestrais.
- **Tamanho do tabuleiro**: tamanho do Mini Gomoku.
- **Linha para vencer**: quantidade de peças em sequência necessária para vencer.
- **Semente**: controla a repetibilidade do experimento.
- **Velocidade dos checkpoints**: atraso visual entre snapshots do streaming.

O botão **Rodar comparação** inicia a execução. Durante a execução, ele muda para **Parar comparação**.

## Métricas

A tela mostra:

- **Score UCTαβ**: média acumulada do método com limites ancestrais.
- **Score UCT**: média acumulada do UCT padrão.
- **Vencedor**: método com maior score acumulado.
- **Vitórias UCTαβ**: taxa de vitórias do método principal.
- **Status**: estado da conexão de streaming.

O score usa vitória como `1`, empate como `0.5` e derrota como `0`.

Os dois métodos jogam com a mesma ajuda tática básica: vitória imediata, bloqueio de ameaça imediata e playouts com preferência por casas centrais. Isso reduz partidas decididas por ruído puro e deixa o efeito dos limites ancestrais mais visível.

## Complexidade

Na interface, os cartões de explicação mostram a complexidade das duas seleções:

- `UCT`: tempo por lance `O(S · d · b)` e espaço `O(T)`.
- `UCTαβ`: tempo por lance `O(S · d · b)` e espaço `O(T) + O(1)` por simulação.

Aqui, `S` é o número de simulações por lance, `d` é a profundidade média da simulação, `b` é a quantidade média de filhos examinados na seleção e `T` é a quantidade de nós armazenados na árvore de busca. A diferença do `UCTαβ` aparece no custo constante da seleção, porque ele carrega e atualiza limites ancestrais durante a descida.

## Gráfico

O gráfico **Score acumulado** mostra a evolução da comparação por checkpoint:

- linha verde: `UCTαβ`;
- linha laranja: `UCT`.

## Última partida

O painel final mostra o tabuleiro da última partida recebida e os últimos lances. Os símbolos `X` e `O` indicam o jogador no tabuleiro; o método associado muda de partida para partida porque a aplicação alterna quem começa para reduzir viés de primeiro jogador.
