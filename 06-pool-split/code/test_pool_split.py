"""
test_pool_split.py —— 「分账总额必须等于奖池」的测试

同一份测试要能跑在两份实现上，所以被测模块由环境变量选择：

    # 在未修改的代码上跑（预期失败）
    POOL_SPLIT_MODULE=pool_split_original pytest -v test_pool_split.py

    # 在修改后的代码上跑（预期全部通过）
    pytest -v test_pool_split.py

核心不变量只有一条：sum(split_pool(pool, weights)) == pool。
围绕它再加两条可解释性约束：
    · 每人拿到的钱不能超过「理论上限 + 1 分」，也不能低于「理论下限」；
    · 结果必须可复现（同样输入跑两次结果一致）。
"""

from __future__ import annotations

import importlib
import itertools
import os
import random

import pytest

MODULE_NAME = os.environ.get("POOL_SPLIT_MODULE", "pool_split")
split_pool = importlib.import_module(MODULE_NAME).split_pool


def exact_share(pool_cents: int, weight: int, total: int) -> float:
    """理论上应得的金额（只用于断言，不参与实现）。"""
    return pool_cents * weight / total


# --------------------------------------------------------------------------------------
# 1. 题目要求的「会出错的输入」：每一个都是真实返回过的错误结果
# --------------------------------------------------------------------------------------
class TestReportedFailures:
    def test_docstring_example_underpays_by_one_cent(self):
        """题目自带的例子：10000 分 3 人等分，原实现返回 [3333]*3 = 9999，少发 1 分。"""
        result = split_pool(10000, [1, 1, 1])
        assert sum(result) == 10000, f"sum={sum(result)} != 10000 (result={result})"

    def test_six_equal_users_overpay_by_two_cents(self):
        """100 分 6 人等分：每人向上舍入到 17，合计 102，平台多发 2 分。"""
        result = split_pool(100, [1] * 6)
        assert sum(result) == 100, f"sum={sum(result)} != 100 (result={result})"

    def test_one_cent_three_users(self):
        """1 分钱分给 3 个人：round(0.33)=0，三个人都是 0，1 分钱凭空消失。"""
        result = split_pool(1, [1, 1, 1])
        assert sum(result) == 1, f"sum={sum(result)} != 1 (result={result})"


# --------------------------------------------------------------------------------------
# 2. 主不变量：穷举 + 随机
# --------------------------------------------------------------------------------------
class TestSumAlwaysEqualsPool:
    def test_exhaustive_small_domain(self):
        """穷举：池子 0..120 分 × 3 人权重 0..4 的全部组合，共 121 × 125 = 15125 组。

        比手写若干样例更容易发现「某些余数组合」才出问题的情况。
        """
        cases = 0
        for pool in range(0, 121):
            for weights in itertools.product(range(0, 5), repeat=3):
                result = split_pool(pool, list(weights))
                assert sum(result) == pool, f"pool={pool} weights={weights} -> {result}"
                cases += 1
        assert cases == 15125

    def test_exhaustive_four_users(self):
        """4 人，权重 0..3，池子 0..60：覆盖「零头要分给 2~3 个人」的情况。"""
        for pool in range(0, 61):
            for weights in itertools.product(range(0, 4), repeat=4):
                result = split_pool(pool, list(weights))
                assert sum(result) == pool, f"pool={pool} weights={weights} -> {result}"

    def test_randomized_many_users(self):
        """随机大范围：池子最大 10^7 分，人数最多 50，权重最多 10^5。固定种子可复现。"""
        rng = random.Random(20261110)
        for _ in range(500):
            n = rng.randint(1, 50)
            pool = rng.randint(0, 10_000_000)
            weights = [rng.randint(0, 100_000) for _ in range(n)]
            if sum(weights) == 0:
                weights[0] = 1
            result = split_pool(pool, weights)
            assert sum(result) == pool, f"pool={pool} n={n} -> {sum(result)}"
            assert len(result) == n
            assert all(share >= 0 for share in result)

    def test_huge_pool_beyond_float_precision(self):
        """10^18 级别的金额：float 只有 53 位有效位，原实现会从这里开始丢分。"""
        pool = 10**18 + 7
        weights = [3, 5, 7, 11]
        result = split_pool(pool, weights)
        assert sum(result) == pool


# --------------------------------------------------------------------------------------
# 3. 公平性 / 可解释性
# --------------------------------------------------------------------------------------
class TestFairness:
    def test_each_share_is_floor_or_floor_plus_one(self):
        """没有人能多拿 2 分，也没有人被少给：每个人只能是 floor 或 floor+1。"""
        rng = random.Random(7)
        for _ in range(200):
            n = rng.randint(1, 30)
            pool = rng.randint(0, 100_000)
            weights = [rng.randint(0, 1000) for _ in range(n)]
            total = sum(weights)
            if total == 0:
                continue
            result = split_pool(pool, weights)
            for share, weight in zip(result, weights):
                exact = exact_share(pool, weight, total)
                assert int(exact) <= share <= int(exact) + 1, (
                    f"share={share} exact={exact:.3f} weight={weight}")

    def test_heavier_weight_never_gets_less_than_lighter_by_more_than_one(self):
        """权重高的人不会比权重低的人少拿超过 1 分（四舍五入的误差上限）。"""
        rng = random.Random(11)
        for _ in range(100):
            pool = rng.randint(0, 10_000)
            weights = [rng.randint(1, 100) for _ in range(5)]
            result = split_pool(pool, weights)
            for i in range(len(weights)):
                for j in range(len(weights)):
                    if weights[i] > weights[j]:
                        assert result[i] >= result[j] - 1

    def test_deterministic(self):
        """同样输入跑两次结果必须一致，否则对账时无法解释。"""
        weights = [13, 7, 5, 3, 2]
        first = split_pool(10_000, weights)
        second = split_pool(10_000, weights)
        assert first == second


# --------------------------------------------------------------------------------------
# 4. 边界条件
# --------------------------------------------------------------------------------------
class TestEdgeCases:
    def test_single_recipient_gets_everything(self):
        assert split_pool(12345, [7]) == [12345]

    def test_more_users_than_cents(self):
        """1000 人分 3 分钱：恰好 3 人各拿 1 分，其余为 0，总额仍然精确。"""
        result = split_pool(3, [1] * 1000)
        assert sum(result) == 3
        assert sorted(result)[-3:] == [1, 1, 1]
        assert result.count(0) == 997

    def test_zero_weight_user_gets_nothing(self):
        result = split_pool(100, [0, 5, 5])
        assert result[0] == 0
        assert sum(result) == 100

    def test_zero_pool_returns_zeros(self):
        assert split_pool(0, [1, 2, 3]) == [0, 0, 0]

    def test_all_zero_weights_and_zero_pool(self):
        assert split_pool(0, [0, 0, 0]) == [0, 0, 0]

    def test_all_zero_weights_falls_back_to_equal_split(self):
        """没人有合格时长但池子里有钱：平分兜底，总额依然精确，绝不少发。"""
        result = split_pool(100, [0, 0, 0])
        assert sum(result) == 100
        assert result == [34, 33, 33]

    def test_empty_weights_with_zero_pool(self):
        assert split_pool(0, []) == []

    def test_empty_weights_with_pool_is_rejected(self):
        with pytest.raises(ValueError):
            split_pool(100, [])

    def test_negative_pool_is_rejected(self):
        with pytest.raises(ValueError):
            split_pool(-1, [1, 1])

    def test_negative_weight_is_rejected(self):
        with pytest.raises(ValueError):
            split_pool(100, [5, -1])

    def test_does_not_mutate_input(self):
        weights = [1, 2, 3]
        split_pool(100, weights)
        assert weights == [1, 2, 3]
