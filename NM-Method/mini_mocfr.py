import numpy as np

# =========================
# JOGO: Rock-Paper-Scissors
# =========================
payoff = np.array([
    [0, -1, 1],
    [1, 0, -1],
    [-1, 1, 0]
])

n_actions = 3


# =========================
# Regret Matching
# =========================
def regret_matching(regret):
    positive_regret = np.maximum(regret, 0)
    sum_regret = np.sum(positive_regret)

    if sum_regret > 0:
        return positive_regret / sum_regret
    else:
        return np.ones(n_actions) / n_actions


# =========================
# Exploitability (simples)
# =========================
def exploitability(strategy, payoff):
    br = np.max(payoff @ strategy)  # best response
    value = strategy @ payoff @ strategy
    return br - value


# =========================
# MINI MoCFR
# =========================
def run_mocfr(iterations=5000, mu=0.01, interval=30):

    regret = np.zeros(n_actions)
    strategy = np.ones(n_actions) / n_actions

    # memória (momentum)
    ref_regret = np.zeros(n_actions)

    for t in range(1, iterations + 1):

        # política atual
        strategy = regret_matching(regret)

        # SELF-PLAY (ESSENCIAL)
        opponent_action = np.random.choice(n_actions, p=strategy)

        utilities = payoff[:, opponent_action]
        expected_utility = np.dot(strategy, utilities)

        # update normal (CFR)
        regret += (utilities - expected_utility)

        # MOMENTUM (estabilizado)
        regret += mu * (ref_regret - regret)

        # atualização periódica (buffer)
        if t % interval == 0:
            ref_regret = regret.copy()

        # monitoramento
        if t % 500 == 0:
            exp = exploitability(strategy, payoff)
            print(f"Iter {t}")
            print(f"  Strategy: {np.round(strategy, 4)}")
            print(f"  Exploitability: {exp:.6f}")
            print("-" * 40)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    run_mocfr(iterations=5000, mu=0.01, interval=30)