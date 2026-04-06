import numpy as np
import random
import matplotlib.pyplot as plt
from collections import defaultdict

# =========================
# Regret Matching
# =========================
def regret_matching(r):
    pos = np.maximum(r, 0)
    s = np.sum(pos)
    if s > 1e-12:
        return pos / s
    return np.array([0.5, 0.5])

# =========================
# Treinamento CFR / MoCFR
# =========================
def train_kuhn(n_cards=3, iterations=20000, mu=0.0, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    deck = list(range(1, n_cards + 1))

    regrets = defaultdict(lambda: np.zeros(2))
    strategy_sum = defaultdict(lambda: np.zeros(2))
    ref_regrets = defaultdict(lambda: np.zeros(2))

    def terminal_utility(history, cards):
        p1, p2 = cards

        if history == "cc":
            return 1 if p1 > p2 else -1
        if history == "bc":
            return 1
        if history == "cbc":
            return -1
        if history == "bb":
            return 2 if p1 > p2 else -2
        if history == "cbb":
            return -2 if p1 > p2 else 2

        return None

    def cfr(history, cards, prob1, prob2):
        player = len(history) % 2

        util_term = terminal_utility(history, cards)
        if util_term is not None:
            return util_term

        info = (player, cards[player], history)

        strategy = regret_matching(regrets[info])
        util = np.zeros(2)
        node_util = 0

        for a in range(2):
            next_h = history + ("c" if a == 0 else "b")

            if player == 0:
                util[a] = -cfr(next_h, cards, prob1 * strategy[a], prob2)
            else:
                util[a] = -cfr(next_h, cards, prob1, prob2 * strategy[a])

            node_util += strategy[a] * util[a]

        reach = prob2 if player == 0 else prob1

        regrets[info] += reach * (util - node_util)
        strategy_sum[info] += (prob1 if player == 0 else prob2) * strategy

        return node_util

    for t in range(1, iterations + 1):
        cards = random.sample(deck, 2)
        cfr("", cards, 1.0, 1.0)

        # Momentum (MoCFR)
        if mu > 0:
            for k in regrets:
                regrets[k] += mu * (ref_regrets[k] - regrets[k])

        if t % 200 == 0:
            for k in regrets:
                ref_regrets[k] = regrets[k].copy()

    # média
    avg_strategy = {}
    for k in strategy_sum:
        s = np.sum(strategy_sum[k])
        if s > 0:
            avg_strategy[k] = strategy_sum[k] / s
        else:
            avg_strategy[k] = np.array([0.5, 0.5])

    return avg_strategy

# =========================
# Exploitability Monte Carlo
# =========================
def compute_exploitability_mc(strategy, n_cards, samples=1000):
    deck = list(range(1, n_cards + 1))

    def terminal_utility(history, cards):
        p1, p2 = cards

        if history == "cc":
            return 1 if p1 > p2 else -1
        if history == "bc":
            return 1
        if history == "cbc":
            return -1
        if history == "bb":
            return 2 if p1 > p2 else -2
        if history == "cbb":
            return -2 if p1 > p2 else 2

        return None

    def br_value(player, history, cards):
        util_term = terminal_utility(history, cards)
        if util_term is not None:
            return util_term if player == 0 else -util_term

        current = len(history) % 2
        info = (current, cards[current], history)
        strat = strategy.get(info, np.array([0.5, 0.5]))

        if current == player:
            return max(
                br_value(player, history + "c", cards),
                br_value(player, history + "b", cards)
            )
        else:
            return (
                strat[0] * br_value(player, history + "c", cards) +
                strat[1] * br_value(player, history + "b", cards)
            )

    total = 0

    for _ in range(samples):
        cards = random.sample(deck, 2)
        total += br_value(0, "", cards)
        total += br_value(1, "", cards)

    return total / (2 * samples)

# =========================
# Experimento
# =========================
def run_experiment():
    seeds = [1, 2, 3]
    card_sizes = [3, 5, 8, 12]

    results_cfr = []
    results_mocfr = []

    for n_cards in card_sizes:
        print(f"\nRodando para {n_cards} cartas...")

        cfr_vals = []
        mocfr_vals = []

        for s in seeds:
            strat_cfr = train_kuhn(n_cards, mu=0.0, seed=s)
            strat_mocfr = train_kuhn(n_cards, mu=0.005, seed=s)

            cfr_vals.append(compute_exploitability_mc(strat_cfr, n_cards))
            mocfr_vals.append(compute_exploitability_mc(strat_mocfr, n_cards))

        results_cfr.append((np.mean(cfr_vals), np.std(cfr_vals)))
        results_mocfr.append((np.mean(mocfr_vals), np.std(mocfr_vals)))

    # =========================
    # GRÁFICO
    # =========================
    x = card_sizes

    cfr_mean = [m for m, s in results_cfr]
    cfr_std = [s for m, s in results_cfr]

    mocfr_mean = [m for m, s in results_mocfr]
    mocfr_std = [s for m, s in results_mocfr]

    plt.figure()
    plt.errorbar(x, cfr_mean, yerr=cfr_std, label="CFR")
    plt.errorbar(x, mocfr_mean, yerr=mocfr_std, label="MoCFR")

    plt.xlabel("Número de cartas")
    plt.ylabel("Exploitability (MC)")
    plt.title("CFR vs MoCFR (Kuhn expandido)")
    plt.legend()

    plt.savefig("resultado_experimento.png", dpi=300, bbox_inches="tight")
    print("Gráfico salvo como resultado_experimento.png")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    run_experiment()