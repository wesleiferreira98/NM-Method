from __future__ import annotations

import math
import random
from dataclasses import dataclass


CHECKPOINTS = 24
EMPTY = "."
PLAYER_MARKS = ("X", "O")


@dataclass(frozen=True)
class SimulationConfig:
    matches: int = 80
    simulations: int = 300
    c: float = 1.35
    c_alpha_beta: float = 1.2
    seed: int = 42
    board_size: int = 5
    win_length: int = 4


@dataclass(frozen=True)
class GameState:
    board: tuple[str, ...]
    player: int
    board_size: int
    win_length: int

    @classmethod
    def new(cls, board_size: int, win_length: int) -> "GameState":
        return cls(
            board=tuple([EMPTY] * (board_size * board_size)),
            player=0,
            board_size=board_size,
            win_length=win_length,
        )

    def legal_actions(self) -> list[int]:
        return [index for index, mark in enumerate(self.board) if mark == EMPTY]

    def apply(self, action: int) -> "GameState":
        next_board = list(self.board)
        next_board[action] = PLAYER_MARKS[self.player]
        return GameState(
            board=tuple(next_board),
            player=1 - self.player,
            board_size=self.board_size,
            win_length=self.win_length,
        )

    def winner(self) -> int | None:
        lines = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for row in range(self.board_size):
            for col in range(self.board_size):
                mark = self.board[row * self.board_size + col]
                if mark == EMPTY:
                    continue

                for d_row, d_col in lines:
                    end_row = row + (self.win_length - 1) * d_row
                    end_col = col + (self.win_length - 1) * d_col
                    if not (0 <= end_row < self.board_size and 0 <= end_col < self.board_size):
                        continue

                    if all(
                        self.board[(row + step * d_row) * self.board_size + col + step * d_col] == mark
                        for step in range(self.win_length)
                    ):
                        return PLAYER_MARKS.index(mark)

        return None

    def is_terminal(self) -> bool:
        return self.winner() is not None or EMPTY not in self.board

    def reward_for(self, player: int) -> float:
        winner = self.winner()
        if winner is None:
            return 0.5
        return 1.0 if winner == player else 0.0


def _winning_actions(state: GameState, player: int) -> list[int]:
    actions = []
    for action in state.legal_actions():
        board = list(state.board)
        board[action] = PLAYER_MARKS[player]
        probe = GameState(
            board=tuple(board),
            player=1 - player,
            board_size=state.board_size,
            win_length=state.win_length,
        )
        if probe.winner() == player:
            actions.append(action)
    return actions


def _center_weighted_choice(state: GameState, rng: random.Random) -> int:
    center = (state.board_size - 1) / 2
    weighted_actions = []

    for action in state.legal_actions():
        row = action // state.board_size
        col = action % state.board_size
        distance = abs(row - center) + abs(col - center)
        weight = 1 / (1 + distance)
        weighted_actions.append((action, weight))

    total = sum(weight for _, weight in weighted_actions)
    draw = rng.random() * total
    running = 0.0
    for action, weight in weighted_actions:
        running += weight
        if running >= draw:
            return action

    return weighted_actions[-1][0]


class MCTSNode:
    def __init__(self, state: GameState, parent: "MCTSNode | None" = None, action: int | None = None):
        self.state = state
        self.parent = parent
        self.action = action
        self.player_just_moved = 1 - state.player
        self.children: list[MCTSNode] = []
        self.untried_actions = state.legal_actions()
        self.visits = 0
        self.total_value = 0.0

    def mean_value(self) -> float:
        if self.visits == 0:
            return 0.5
        return self.total_value / self.visits

    def is_fully_expanded(self) -> bool:
        return not self.untried_actions

    def expand(self, rng: random.Random) -> "MCTSNode":
        action = rng.choice(self.untried_actions)
        self.untried_actions.remove(action)
        child = MCTSNode(self.state.apply(action), parent=self, action=action)
        self.children.append(child)
        return child


def _confidence(parent_visits: int, child_visits: int, c_value: float) -> float:
    if child_visits <= 0:
        return float("inf")
    return c_value * math.sqrt(math.log(max(parent_visits, 2)) / child_visits)


def _uct_score(parent: MCTSNode, child: MCTSNode, c_value: float) -> float:
    return child.mean_value() + _confidence(parent.visits, child.visits, c_value)


def _uct_alpha_beta_score(
    parent: MCTSNode,
    child: MCTSNode,
    c_value: float,
    c_alpha_beta: float,
    alpha: float,
    beta: float,
    alpha_minus: float,
    beta_plus: float,
) -> float:
    if not math.isfinite(alpha) or not math.isfinite(beta):
        return _uct_score(parent, child, c_value)

    delta = 1 - (beta - alpha) * (1 - (beta_plus - alpha_minus))
    scaled_visits = delta * max(parent.visits, 2)
    if scaled_visits <= 1:
        return child.mean_value()

    delta_term = (c_alpha_beta**2) * math.log(scaled_visits)
    if delta_term <= 0:
        return _uct_score(parent, child, c_value)

    exploration = c_value * math.sqrt(delta_term * math.log(max(parent.visits, 2)) / child.visits)
    return child.mean_value() + exploration


def _select_child(
    node: MCTSNode,
    use_alpha_beta: bool,
    c_value: float,
    c_alpha_beta: float,
    alpha: float,
    beta: float,
    alpha_minus: float,
    beta_plus: float,
) -> MCTSNode:
    if use_alpha_beta:
        scorer = lambda child: _uct_alpha_beta_score(
            node,
            child,
            c_value,
            c_alpha_beta,
            alpha,
            beta,
            alpha_minus,
            beta_plus,
        )
    else:
        scorer = lambda child: _uct_score(node, child, c_value)

    return max(node.children, key=scorer)


def _rollout(state: GameState, rng: random.Random) -> GameState:
    current = state
    while not current.is_terminal():
        current = current.apply(_center_weighted_choice(current, rng))
    return current


def _backpropagate(node: MCTSNode, terminal_state: GameState) -> None:
    current: MCTSNode | None = node
    while current is not None:
        current.visits += 1
        current.total_value += terminal_state.reward_for(current.player_just_moved)
        current = current.parent


def choose_action(
    state: GameState,
    simulations: int,
    rng: random.Random,
    use_alpha_beta: bool,
    c_value: float,
    c_alpha_beta: float,
) -> tuple[int, dict]:
    winning_actions = _winning_actions(state, state.player)
    if winning_actions:
        action = rng.choice(winning_actions)
        return action, {
            "action": action,
            "visits": 0,
            "value": 1.0,
            "alphaBetaSelectionRate": 0.0,
            "children": [],
        }

    blocking_actions = _winning_actions(state, 1 - state.player)
    if blocking_actions:
        action = rng.choice(blocking_actions)
        return action, {
            "action": action,
            "visits": 0,
            "value": 0.5,
            "alphaBetaSelectionRate": 0.0,
            "children": [],
        }

    root = MCTSNode(state)
    root_player = state.player
    alpha_uses = 0

    for _ in range(simulations):
        node = root
        alpha = -math.inf
        beta = math.inf
        alpha_minus = 0.0
        beta_plus = 0.0

        while node.is_fully_expanded() and node.children and not node.state.is_terminal():
            parent = node
            used_alpha_beta = use_alpha_beta and math.isfinite(alpha) and math.isfinite(beta)
            node = _select_child(
                parent,
                use_alpha_beta,
                c_value,
                c_alpha_beta,
                alpha,
                beta,
                alpha_minus,
                beta_plus,
            )
            alpha_uses += int(used_alpha_beta)

            value = node.mean_value()
            value_for_root = value if parent.state.player == root_player else 1 - value
            bound = _confidence(parent.visits, node.visits, c_alpha_beta)

            if parent.state.player == root_player:
                if alpha < value_for_root - bound:
                    alpha = value_for_root - bound
                    alpha_minus = -bound
            elif beta > value_for_root + bound:
                beta = value_for_root + bound
                beta_plus = bound

        if not node.state.is_terminal() and node.untried_actions:
            node = node.expand(rng)

        terminal_state = _rollout(node.state, rng)
        _backpropagate(node, terminal_state)

    if not root.children:
        raise RuntimeError("Nenhuma acao legal disponivel para o MCTS.")

    best_child = max(root.children, key=lambda child: (child.visits, child.mean_value()))
    return best_child.action, {
        "action": best_child.action,
        "visits": best_child.visits,
        "value": round(best_child.mean_value(), 4),
        "alphaBetaSelectionRate": round(alpha_uses / max(1, simulations), 4),
        "children": sorted(
            [
                {
                    "action": child.action,
                    "row": child.action // state.board_size,
                    "col": child.action % state.board_size,
                    "visits": child.visits,
                    "value": round(child.mean_value(), 4),
                }
                for child in root.children
            ],
            key=lambda child: child["visits"],
            reverse=True,
        )[:8],
    }


def _play_match(config: SimulationConfig, match_index: int, rng: random.Random) -> dict:
    state = GameState.new(config.board_size, config.win_length)
    alpha_beta_player = match_index % 2
    move_log = []

    while not state.is_terminal():
        use_alpha_beta = state.player == alpha_beta_player
        action, search = choose_action(
            state,
            config.simulations,
            rng,
            use_alpha_beta=use_alpha_beta,
            c_value=config.c,
            c_alpha_beta=config.c_alpha_beta,
        )
        move_log.append(
            {
                "move": len(move_log) + 1,
                "player": PLAYER_MARKS[state.player],
                "method": "UCTαβ" if use_alpha_beta else "UCT",
                "row": action // config.board_size,
                "col": action % config.board_size,
                "value": search["value"],
                "visits": search["visits"],
                "alphaBetaSelectionRate": search["alphaBetaSelectionRate"],
            }
        )
        state = state.apply(action)

    winner = state.winner()
    alpha_beta_score = state.reward_for(alpha_beta_player)
    return {
        "winner": "Empate" if winner is None else PLAYER_MARKS[winner],
        "winnerMethod": "Empate"
        if winner is None
        else ("UCTαβ" if winner == alpha_beta_player else "UCT"),
        "alphaBetaPlayer": PLAYER_MARKS[alpha_beta_player],
        "alphaBetaScore": alpha_beta_score,
        "board": list(state.board),
        "moves": move_log,
    }


def _snapshot(
    config: SimulationConfig,
    timeline: list[dict],
    last_match: dict | None,
    match_number: int,
    done: bool,
) -> dict:
    score = timeline[-1]["score"] if timeline else 0.0
    uct_score = round(1 - score, 4)
    alpha_beta_wins = timeline[-1]["alphaBetaWins"] if timeline else 0
    uct_wins = timeline[-1]["uctWins"] if timeline else 0
    draws = timeline[-1]["draws"] if timeline else 0

    return {
        "game": f"Mini Gomoku {config.board_size}x{config.board_size}",
        "method": "Ancestor-Based alpha-beta Bounds for MCTS",
        "source": "local-mcts",
        "config": {
            "matches": config.matches,
            "simulations": config.simulations,
            "c": config.c,
            "cAlphaBeta": config.c_alpha_beta,
            "seed": config.seed,
            "boardSize": config.board_size,
            "winLength": config.win_length,
        },
        "timeline": timeline,
        "comparison": {
            "label": "UCT",
            "primaryLabel": "UCTαβ",
            "timeline": [
                {
                    "iteration": point["iteration"],
                    "score": point["uctScore"],
                    "winRate": point["uctWinRate"],
                }
                for point in timeline
            ],
            "finalScore": uct_score,
            "wins": uct_wins,
            "draws": draws,
        },
        "finalScore": score,
        "wins": alpha_beta_wins,
        "draws": draws,
        "lastMatch": last_match,
        "progress": round(match_number / config.matches, 4),
        "currentIteration": match_number,
        "done": done,
        "explanation": {
            "baseline": "UCT usa a selecao padrao baseada em media e exploracao local.",
            "alphaBeta": "UCTαβ ajusta a exploracao usando limites alpha e beta estimados a partir dos ancestrais do caminho de selecao.",
            "domain": "O ambiente usa Mini Gomoku local com playouts levemente informados para reduzir ruido sem favorecer um metodo no placar.",
        },
    }


def stream_mcts_comparison(config: SimulationConfig):
    rng = random.Random(config.seed)
    checkpoint_every = max(1, config.matches // CHECKPOINTS)
    timeline = []
    alpha_beta_total = 0.0
    alpha_beta_wins = 0
    uct_wins = 0
    draws = 0
    last_match = None

    for match_index in range(config.matches):
        last_match = _play_match(config, match_index, rng)
        alpha_beta_total += last_match["alphaBetaScore"]
        if last_match["winnerMethod"] == "UCTαβ":
            alpha_beta_wins += 1
        elif last_match["winnerMethod"] == "UCT":
            uct_wins += 1
        else:
            draws += 1

        match_number = match_index + 1
        if match_number == 1 or match_number % checkpoint_every == 0 or match_number == config.matches:
            score = alpha_beta_total / match_number
            timeline.append(
                {
                    "iteration": match_number,
                    "score": round(score, 4),
                    "winRate": round(alpha_beta_wins / match_number, 4),
                    "uctScore": round(1 - score, 4),
                    "uctWinRate": round(uct_wins / match_number, 4),
                    "drawRate": round(draws / match_number, 4),
                    "alphaBetaWins": alpha_beta_wins,
                    "uctWins": uct_wins,
                    "draws": draws,
                }
            )
            yield _snapshot(
                config=config,
                timeline=timeline[:],
                last_match=last_match,
                match_number=match_number,
                done=match_number == config.matches,
            )


def run_mcts_comparison(config: SimulationConfig) -> dict:
    result = None
    for result in stream_mcts_comparison(config):
        pass
    if result is None:
        raise RuntimeError("A simulacao nao produziu resultados.")
    return result
