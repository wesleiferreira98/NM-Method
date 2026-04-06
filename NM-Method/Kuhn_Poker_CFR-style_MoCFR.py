import numpy as np
import random

# =========================
# CONFIG
# =========================
N_CARDS = 12
ITERATIONS = 100000
INTERVAL = 500
MU = 0.01  # momentum

cards = [str(i) for i in range(1, N_CARDS + 1)]

# =========================
# STORAGE
# =========================
regret = {}
strategy_sum = {}

# =========================
# Regret Matching
# =========================
def regret_matching(regret_vec):
    positive = np.maximum(regret_vec, 0)
    s = np.sum(positive)
    if s > 1e-12:
        return positive / s
    return np.ones(len(regret_vec)) / len(regret_vec)

def get_strategy(info, n_actions):
    if info not in regret:
        regret[info] = np.zeros(n_actions)
        strategy_sum[info] = np.zeros(n_actions)
    return regret_matching(regret[info])

# =========================
# GAME LOGIC
# =========================
def card_value(c):
    return int(c)

def terminal_utility(history, c1, c2):
    if history == "cc":
        return 1 if card_value(c1) > card_value(c2) else -1
    if history == "bc":
        return 2 if card_value(c1) > card_value(c2) else -2
    if history == "bf":
        return 1
    if history == "cbf":
        return -1
    if history == "cbc":
        return 2 if card_value(c1) > card_value(c2) else -2
    raise ValueError(f"Histórico inválido: {history}")

def legal_actions(history):
    if history == "":
        return ['c', 'b']
    if history == "c":
        return ['c', 'b']
    if history == "b":
        return ['c', 'f']
    if history == "cb":
        return ['c', 'f']
    return []

def is_terminal(history):
    return history in ["cc", "bc", "bf", "cbf", "cbc"]

# =========================
# CFR / MoCFR
# =========================
def cfr(history, c1, c2, p1, p2, mu, ref_regret):
    if is_terminal(history):
        return terminal_utility(history, c1, c2)

    player = len(history) % 2
    card = c1 if player == 0 else c2
    info = (player, card, history)

    actions = legal_actions(history)
    strat = get_strategy(info, len(actions))

    utils = np.zeros(len(actions))
    node_util = 0.0

    for i, a in enumerate(actions):
        next_history = history + a
        if player == 0:
            utils[i] = -cfr(next_history, c1, c2, p1 * strat[i], p2, mu, ref_regret)
        else:
            utils[i] = -cfr(next_history, c1, c2, p1, p2 * strat[i], mu, ref_regret)
        node_util += strat[i] * utils[i]

    regret_delta = utils - node_util

    opp_reach = p2 if player == 0 else p1
    self_reach = p1 if player == 0 else p2

    regret[info] += opp_reach * regret_delta
    strategy_sum[info] += self_reach * strat

    # Momentum (MoCFR)
    if mu > 0:
        if info not in ref_regret:
            ref_regret[info] = regret[info].copy()
        regret[info] += mu * (ref_regret[info] - regret[info])

    return node_util

# =========================
# Average Strategy
# =========================
def average_strategy():
    avg = {}
    for info, ssum in strategy_sum.items():
        total = np.sum(ssum)
        if total > 1e-12:
            avg[info] = ssum / total
        else:
            avg[info] = np.ones_like(ssum) / len(ssum)
    return avg

# =========================
# BEST RESPONSE
# =========================
def best_response(history, c1, c2, avg_strategy, player):
    if is_terminal(history):
        return terminal_utility(history, c1, c2)

    current = len(history) % 2
    card = c1 if current == 0 else c2
    info = (current, card, history)

    actions = legal_actions(history)

    # jogador que responde → escolhe melhor ação
    if current == player:
        best = -np.inf
        for a in actions:
            val = best_response(history + a, c1, c2, avg_strategy, player)
            best = max(best, val)
        return best

    # segue estratégia média do oponente
    if info not in avg_strategy:
        probs = np.ones(len(actions)) / len(actions)
    else:
        probs = avg_strategy[info]

    val = 0.0
    for i, a in enumerate(actions):
        val += probs[i] * best_response(history + a, c1, c2, avg_strategy, player)

    return val

# =========================
# EXPLOITABILITY
# =========================
def compute_exploitability(avg_strategy):
    total = 0.0
    count = 0

    for i in range(len(cards)):
        for j in range(len(cards)):
            if i == j:
                continue

            c1, c2 = cards[i], cards[j]

            br1 = best_response("", c1, c2, avg_strategy, player=0)
            br2 = best_response("", c1, c2, avg_strategy, player=1)

            total += br1 + br2
            count += 1

    return total / count

# =========================
# TRAIN
# =========================
def train(mu):
    ref_regret = {}
    deck = cards[:]

    for t in range(1, ITERATIONS + 1):
        random.shuffle(deck)
        c1, c2 = deck[0], deck[1]

        cfr("", c1, c2, 1.0, 1.0, mu, ref_regret)

        if t % INTERVAL == 0:
            for k in regret:
                ref_regret[k] = regret[k].copy()

        if t % 5000 == 0:
            avg = average_strategy()
            exp = compute_exploitability(avg)
            print(f"Iter {t} | infosets={len(avg)} | exploitability={exp:.6f}")

    return average_strategy()

# =========================
# PRINT
# =========================
def print_some(avg, limit=20):
    print("\n=== Algumas estratégias ===")
    for i, (info, strat) in enumerate(sorted(avg.items())):
        print(info, np.round(strat, 3))
        if i >= limit:
            break

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print(f"=== MoCFR ({N_CARDS} cartas) ===")
    avg_mo = train(mu=MU)
    print_some(avg_mo)

    regret.clear()
    strategy_sum.clear()

    print(f"\n=== CFR ({N_CARDS} cartas) ===")
    avg_cfr = train(mu=0.0)
    print_some(avg_cfr)