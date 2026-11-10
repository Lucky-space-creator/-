"""
pool_split.py —— 每日瓜分奖池的分账逻辑（修复版）

约定：
· 所有金额都是整数「分」，系统里不存在半分钱。
· weights 是每个人的贡献权重（线上用的是「合格采集秒数」）。
硬规则：分完之后，所有人拿到的钱加起来必须【正好等于】池子总额。

原实现的问题：
    [round(pool_cents * w / total) for w in weights]
    每个人各自四舍五入，误差不会互相抵消，因此 sum 可能比 pool_cents 多也可能少；
    同时 Python 的 round() 是「银行家舍入」（round(0.5) == 0、round(2.5) == 2），
    连「谁该进位」的直觉都不成立。此外 float 除法在超大金额上还会丢精度。

修复思路（最大余数法 / Hamilton 法，也叫 Hare quota）：
    1. 先按整除拿到每人「至少」应得的整数分（floor），这部分加起来一定 ≤ 总额；
    2. 剩下的零头一定小于人数，按余数从大到小逐个补 1 分，补到总额用尽为止；
    3. 全程整数运算（divmod），不出现浮点数。
"""

from __future__ import annotations


def split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """把 pool_cents 按 weights 的比例分给每个人，返回每人拿到多少分。

    返回列表与 weights 一一对应，且 sum(返回值) == pool_cents 恒成立。

    平局规则（余数相同时谁先拿那 1 分）：
        余数大 → 权重大 → 下标小。
    这样结果是确定的、可复现的，也便于对账时解释「为什么是他多拿 1 分」。

    :raises ValueError: 池子为负、权重为负，或 weights 为空但池子不为 0。
    """
    if pool_cents < 0:
        raise ValueError(f"pool_cents must be >= 0, got {pool_cents}")
    if any(w < 0 for w in weights):
        raise ValueError(f"weights must be >= 0, got {weights}")

    n = len(weights)
    if n == 0:
        if pool_cents:
            raise ValueError("pool_cents > 0 but no recipients")
        return []

    total = sum(weights)
    if total == 0:
        # 所有人都没有合格时长，但池子里有钱：没有比「在场的人平分」更中立的规则。
        # 也可以选择直接抛错（把决定权交回调用方），但那样这条硬规则就守不住了，
        # 所以这里选择把池子分完，并把规则写进文档。
        quotient, remainder = divmod(pool_cents, n)
        return [quotient + (1 if i < remainder else 0) for i in range(n)]

    # 1) 每个人先拿整数部分；余数用于第 2 步排序
    shares: list[int] = []
    remainders: list[int] = []
    for w in weights:
        quotient, remainder = divmod(pool_cents * w, total)  # 纯整数，无浮点误差
        shares.append(quotient)
        remainders.append(remainder)

    # 2) 还有多少分没分出去？一定满足 0 <= leftover < n
    leftover = pool_cents - sum(shares)

    # 3) 余数从大到小补 1 分（平局：权重大优先，再按下标先后）
    order = sorted(range(n), key=lambda i: (-remainders[i], -weights[i], i))
    for i in order[:leftover]:
        shares[i] += 1

    return shares


if __name__ == "__main__":
    # 题目里的例子：奖池 100 元，三个人权重相同
    print(split_pool(10000, [1, 1, 1]))          # [3334, 3333, 3333]，合计 10000
    print(split_pool(100, [1] * 6))               # 合计 100，不会变成 102
    print(sum(split_pool(10**18 + 7, [3, 5, 7, 11])))  # 超大金额同样精确
