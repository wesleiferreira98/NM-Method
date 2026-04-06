import numpy as np
import random
import matplotlib.pyplot as plt
from collections import defaultdict

# =========================
# CONFIG
# =========================
CARDS = ["J", "Q", "K", "J", "Q", "K"]

# =========================
# HISTÓRICO / ESTADO
# =========================
def split_history(full_history):
    if "|" not in full_history:
        return full_history, ""
    left, right = full_history.split("|", 1)
    return left, right

def round_terminal(hist):
    return hist in ("cc", "bc", "bf", "cbc", "cbf")

def current_round(full_history):
    r0, _ = split_history(full_history)
    return 0 if not round_terminal(r0) else 1

def current_player(full_history):
    r0, r1 = split_history(full_history)
    active = r0 if not round_terminal(r0) else r1
    return len(active) % 2

def legal_actions_round(hist):
    # início da rodada ou após check
    if hist == "":
        return ["c", "b"]
    if hist == "c":
        return ["c", "b"]
    # após bet, o outro jogador decide call/fold
    if hist == "b":
        return ["c", "f"]
    if hist == "cb":
        return ["c", "f"]
    return []

def legal_actions(full_history):
    r0, r1 = split_history(full_history)
    if not round_terminal(r0):
        return legal_actions_round(r0)
    return legal_actions_round(r1)

def next_state(full_history, action):
    r0, r1 = split_history(full_history)

    # rodada 0 ainda aberta
    if not round_terminal(r0):
        r0_new = r0 + action
        if round_terminal(r0_new):
            # se rodada 0 terminou em fold, jogo todo termina
            if r0_new in ("bf", "cbf"):
                return r0_new + "|"
            # senão avança para rodada 1
            return r0_new + "|"
        return r0_new + "|" + r1

    # rodada 1
    r1_new = r1 + action
    return r0 + "|" + r1_new

# =========================
# TERMINAL / PAYOFF
# =========================
def hand_strength(card, board):
    # par vence carta alta
    return (card == board, card)

def showdown_payoff(p1_card, p2_card, board_card, pot):
    h1 = hand_strength(p1_card, board_card)
    h2 = hand_strength(p2_card, board_card)
    if h1 > h2:
        return pot
    if h2 > h1:
        return -pot
    return 0

def terminal_utility(p1_card, p2_card, board_card, full_history):
    r0, r1 = split_history(full_history)

    # fold na rodada 0
    if r0 == "bf":
        return 1
    if r0 == "cbf":
        return -1

    # rodada 0 terminada, rodada 1 em andamento ou terminada
    if round_terminal(r0):
        # fold na rodada 1
        if r1 == "bf":
            return 2
        if r1 == "cbf":
            return -2

        # showdown depois de duas rodadas completas
        if round_terminal(r1):
            # pote simplificado:
            # cc|cc -> 1
            # qualquer call em alguma rodada aumenta pote
            pot = 1
            if r0 in ("bc", "cbc"):
                pot += 1
            if r1 in ("bc", "cbc"):
                pot += 1
            return showdown_payoff(p1_card, p2_card, board_card, pot)

    return None

def is_terminal(full_history, p1_card, p2_card, board_card):
    return terminal_utility(p1_card, p2_card, board_card, full_history) is not None

# =========================
# INFOSET
# =========================
def info_key(player, private_card, board_card, history):
    rd = current_round(history)
    public = board_card if rd == 1 else None
    return (player, private_card, public, history)

# =========================
# REGRET MATCHING
# =========================
def regret_matching(regret_vec):
    positive = np.maximum(regret_vec, 0.0)
    s = np.sum(positive)
    if s > 1e-12:
        return positive / s
    return np.ones_like(regret_vec) / len(regret_vec)

# =========================
# CFR / MoCFR
# =========================
def run_cfr(iterations=30000, mu=0.0, seed=0):
    random.seed(seed)
    np.random.seed(seed)

    regrets = {}
    strategy_sum = {}
    ref_regrets = {}

    def get_arrays(key, n_actions):
        if key not in regrets:
            regrets[key] = np.zeros(n_actions, dtype=float)
            strategy_sum[key] = np.zeros(n_actions, dtype=float)
            ref_regrets[key] = np.zeros(n_actions, dtype=float)
        return regrets[key], strategy_sum[key], ref_regrets[key]

    def cfr(history, p1_card, p2_card, board_card, prob1, prob2):
        util_term = terminal_utility(p1_card, p2_card, board_card, history)
        if util_term is not None:
            return util_term

        player = current_player(history)
        private = p1_card if player == 0 else p2_card
        key = info_key(player, private, board_card, history)

        actions = legal_actions(history)
        reg, strat_sum, _ = get_arrays(key, len(actions))
        strategy = regret_matching(reg)

        reach_self = prob1 if player == 0 else prob2
        reach_opp = prob2 if player == 0 else prob1

        strat_sum += reach_self * strategy

        utils = np.zeros(len(actions), dtype=float)
        node_util = 0.0

        for i, act in enumerate(actions):
            nxt = next_state(history, act)
            if player == 0:
                utils[i] = -cfr(nxt, p1_card, p2_card, board_card,
                                prob1 * strategy[i], prob2)
            else:
                utils[i] = -cfr(nxt, p1_card, p2_card, board_card,
                                prob1, prob2 * strategy[i])
            node_util += strategy[i] * utils[i]

        reg += reach_opp * (utils - node_util)

        # momentum simples
        if mu > 0:
            reg += mu * (ref_regrets[key] - reg)

        return node_util

    for t in range(1, iterations + 1):
        cards = CARDS.copy()
        random.shuffle(cards)
        p1_card, p2_card, board_card = cards[:3]

        cfr("|", p1_card, p2_card, board_card, 1.0, 1.0)

        if t % 200 == 0:
            for k in regrets:
                ref_regrets[k] = regrets[k].copy()

    avg_strategy = {}
    for k, arr in strategy_sum.items():
        s = np.sum(arr)
        if s > 1e-12:
            avg_strategy[k] = arr / s
        else:
            avg_strategy[k] = np.ones_like(arr) / len(arr)

    return avg_strategy

# =========================
# BEST RESPONSE / EXPLOITABILITY APROX
# =========================
def evaluate_strategy(strategy, samples=2000, seed=123):
    random.seed(seed)
    np.random.seed(seed)

    def br_value(player_br, history, p1_card, p2_card, board_card):
        util_term = terminal_utility(p1_card, p2_card, board_card, history)
        if util_term is not None:
            return util_term if player_br == 0 else -util_term

        cur = current_player(history)
        private = p1_card if cur == 0 else p2_card
        key = info_key(cur, private, board_card, history)
        actions = legal_actions(history)

        if cur == player_br:
            best = -1e18
            for act in actions:
                nxt = next_state(history, act)
                val = br_value(player_br, nxt, p1_card, p2_card, board_card)
                if val > best:
                    best = val
            return best

        probs = strategy.get(key)
        if probs is None or len(probs) != len(actions):
            probs = np.ones(len(actions)) / len(actions)

        val = 0.0
        for i, act in enumerate(actions):
            nxt = next_state(history, act)
            val += probs[i] * br_value(player_br, nxt, p1_card, p2_card, board_card)
        return val

    total = 0.0
    for _ in range(samples):
        cards = CARDS.copy()
        random.shuffle(cards)
        p1_card, p2_card, board_card = cards[:3]

        total += br_value(0, "|", p1_card, p2_card, board_card)
        total += br_value(1, "|", p1_card, p2_card, board_card)

    return total / (2 * samples)

# =========================
# EXPERIMENTO
# =========================
def run_experiment():
    seeds = [0, 1, 2]
    results_cfr = []
    results_mocfr = []

    for s in seeds:
        strat_cfr = run_cfr(iterations=30000, mu=0.0, seed=s)
        strat_mo = run_cfr(iterations=30000, mu=0.01, seed=s)

        exp_cfr = evaluate_strategy(strat_cfr, samples=1500, seed=100 + s)
        exp_mo = evaluate_strategy(strat_mo, samples=1500, seed=200 + s)

        results_cfr.append(exp_cfr)
        results_mocfr.append(exp_mo)

        print(f"seed={s} | CFR={exp_cfr:.4f} | MoCFR={exp_mo:.4f}")

    mean_cfr = np.mean(results_cfr)
    mean_mo = np.mean(results_mocfr)
    std_cfr = np.std(results_cfr)
    std_mo = np.std(results_mocfr)

    print("CFR:", mean_cfr, "+-", std_cfr)
    print("MoCFR:", mean_mo, "+-", std_mo)

    plt.figure(figsize=(6, 4))
    plt.bar(["CFR", "MoCFR"], [mean_cfr, mean_mo], yerr=[std_cfr, std_mo])
    plt.ylabel("Exploitability (aprox)")
    plt.title("Leduc Poker Simplificado")
    plt.savefig("leduc_result.png", dpi=300, bbox_inches="tight")
    print("Gráfico salvo como leduc_result.png")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    run_experiment()