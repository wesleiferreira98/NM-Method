import numpy as np
import random
from collections import defaultdict

ACTIONS = ["c", "b"]

def regret_matching(r):
    pos = np.maximum(r, 0)
    s = np.sum(pos)
    if s > 1e-12:
        return pos / s
    return np.ones(len(ACTIONS)) / len(ACTIONS)

# =========================
# Leduc Simplificado
# =========================
class Leduc:
    def __init__(self):
        self.deck = [1,1,2,2,3,3]

    def deal(self):
        cards = random.sample(self.deck, 3)
        return cards[0], cards[1], cards[2]  # p1, p2, public

def terminal(history):
    return history.endswith("cc") or history.endswith("bc") or history.endswith("cbc")

def payoff(p1, p2, board, history):
    # showdown
    if history.endswith("cc"):
        s1 = (p1 == board, p1)
        s2 = (p2 == board, p2)
        return 1 if s1 > s2 else -1

    # fold situations
    if history.endswith("bc"):
        return 1
    if history.endswith("cbc"):
        return -1

    return None

# =========================
# CFR
# =========================
def train_leduc(iterations=20000, mu=0.0, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    regrets = defaultdict(lambda: np.zeros(len(ACTIONS)))
    strategy_sum = defaultdict(lambda: np.zeros(len(ACTIONS)))
    ref_regrets = defaultdict(lambda: np.zeros(len(ACTIONS)))

    game = Leduc()

    def cfr(history, p1, p2, board, prob1, prob2, round_):
        util_term = payoff(p1, p2, board, history)
        if util_term is not None:
            return util_term

        player = len(history) % 2
        info = (player, (p1 if player==0 else p2), board, history)

        strategy = regret_matching(regrets[info])
        util = np.zeros(len(ACTIONS))
        node_util = 0

        for i, a in enumerate(ACTIONS):
            next_h = history + a

            util[i] = -cfr(
                next_h,
                p1, p2, board,
                prob1 * strategy[i] if player==0 else prob1,
                prob2 * strategy[i] if player==1 else prob2,
                round_
            )

            node_util += strategy[i] * util[i]

        reach = prob2 if player==0 else prob1
        regrets[info] += reach * (util - node_util)

        strategy_sum[info] += (prob1 if player==0 else prob2) * strategy

        return node_util

    for t in range(1, iterations+1):
        p1, p2, board = game.deal()
        cfr("", p1, p2, board, 1, 1, 0)

        # momentum
        if mu > 0:
            for k in regrets:
                regrets[k] += mu * (ref_regrets[k] - regrets[k])

        if t % 200 == 0:
            for k in regrets:
                ref_regrets[k] = regrets[k].copy()

    return strategy_sum