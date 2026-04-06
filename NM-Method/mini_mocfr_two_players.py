import numpy as np

# =========================
# JOGO: Rock-Paper-Scissors generalizado
# =========================
n_actions = 5
np.random.seed(42)

A = np.random.randn(n_actions, n_actions)
payoff = A - A.T  # zero-sum
payoff = payoff / np.max(np.abs(payoff))

# =========================
# Regret Matching
# =========================
def regret_matching(regret):
    positive = np.maximum(regret, 0)
    s = np.sum(positive)
    if s > 1e-12:
        return positive / s
    else:
        return np.ones(n_actions) / n_actions

# =========================
# Exploitability
# =========================
def exploitability(p1, p2):
    br1 = np.max(payoff @ p2)
    br2 = np.max((-payoff.T) @ p1)
    value = p1 @ payoff @ p2
    return (br1 - value) + (br2 + value)

# =========================
# Estratégia inicial
# =========================
def random_strategy():
    x = np.random.rand(n_actions)
    return x / np.sum(x)

# =========================
# MoCFR com reach probabilities (CFR-style)
# =========================
def run_mocfr(iterations=3000, mu=0.005, interval=50):

    # regrets separados
    r1 = np.zeros(n_actions)
    r2 = np.zeros(n_actions)

    # estratégias
    p1 = random_strategy()
    p2 = random_strategy()

    # médias (ponderadas por reach prob)
    p1_avg = np.zeros(n_actions)
    p2_avg = np.zeros(n_actions)

    # referências para momentum
    ref_r1 = r1.copy()
    ref_r2 = r2.copy()

    for t in range(1, iterations + 1):

        # estratégias atuais
        p1 = regret_matching(r1)
        p2 = regret_matching(r2)

        # =========================
        # REACH PROBABILITIES
        # =========================
        reach_p1 = 1.0
        reach_p2 = 1.0

        # =========================
        # UPDATE PLAYER 1
        # =========================
        u1 = payoff @ p2
        v1 = p1 @ u1

        # weighted by opponent reach (CFR correto)
        r1 += reach_p2 * (u1 - v1)

        # =========================
        # UPDATE PLAYER 2
        # =========================
        u2 = -payoff.T @ p1
        v2 = p2 @ u2

        r2 += reach_p1 * (u2 - v2)

        # =========================
        # MOMENTUM (MoCFR)
        # =========================
        if mu > 0:
            r1 += mu * (ref_r1 - r1)
            r2 += mu * (ref_r2 - r2)

        if t % interval == 0:
            ref_r1 = r1.copy()
            ref_r2 = r2.copy()

        # =========================
        # MÉDIA CFR (ponderada)
        # =========================
        p1_avg += reach_p1 * p1
        p2_avg += reach_p2 * p2

        avg_p1 = p1_avg / t
        avg_p2 = p2_avg / t

        # =========================
        # MONITORAMENTO
        # =========================
        if t % 200 == 0:
            exp = exploitability(avg_p1, avg_p2)

            print(f"Iter {t}")
            print(f"  Current P1: {np.round(p1, 4)}")
            print(f"  Avg P1:     {np.round(avg_p1, 4)}")
            print(f"  Current P2: {np.round(p2, 4)}")
            print(f"  Avg P2:     {np.round(avg_p2, 4)}")
            print(f"  Exploitability: {exp:.6f}")
            print("-" * 50)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("=== MoCFR (CFR-style) ===")
    run_mocfr(mu=0.005)

    print("\n=== CFR (baseline) ===")
    run_mocfr(mu=0.0)