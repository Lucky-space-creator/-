"""
pool_split_original.py —— 题目给出的原始实现（未修改）

保留这个文件是为了让「测试在未修改的代码上失败」这一次运行可以复现：

    POOL_SPLIT_MODULE=pool_split_original pytest -v test_pool_split.py

它与题目附件逐字一致，唯一的差别是模块名，避免和修改后的 pool_split.py 冲突。
"""


def split_pool(pool_cents: int, weights: list[int]) -> list[int]:
    """把 pool_cents 按 weights 的比例分给每个人，返回每人拿到多少分。

    返回列表与 weights 一一对应。
    """
    total = sum(weights)
    return [round(pool_cents * w / total) for w in weights]


if __name__ == "__main__":
    # 一个跑得通的例子：奖池 100 元，三个人权重相同
    print(split_pool(10000, [1, 1, 1]))
