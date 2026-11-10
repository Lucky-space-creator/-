# 每日瓜分奖池：Bug 定位、修复与测试

**结论：** 原实现用 `round()` 对每个人**独立**取整，误差不会互相抵消，因此总和不等于池子总额——
你给的 `__main__` 例子本身就是错的：`split_pool(10000, [1, 1, 1])` 返回 `[3333, 3333, 3333]`，
合计 **9999**，少发 1 分。

| 文件 | 说明 |
|---|---|
| `pool_split.py` | 修复后的实现（**提交用**） |
| `pool_split_original.py` | 题目给的原始实现，仅用于复现「测试在未修改代码上失败」 |
| `test_pool_split.py` | 测试（同一份测试可跑在两份实现上） |
| `output/original_run.txt` | 未修改代码的运行输出（**失败**） |
| `output/fixed_run.txt` | 修改后代码的运行输出（**通过**） |

---

## 1. 会出错的输入

三个数：**输入 → 实际的和 → 应有的和**。

| # | 输入 `pool_cents` | 输入 `weights` | 返回 | 实际的和 | 应有的和 | 差额 |
|---|---|---|---|---|---|---|
| 1 | `10000` | `[1, 1, 1]` | `[3333, 3333, 3333]` | **9999** | **10000** | 少 1 分 |
| 2 | `100` | `[1, 1, 1, 1, 1, 1]` | `[17, 17, 17, 17, 17, 17]` | **102** | **100** | 多 2 分 |
| 3 | `1` | `[1, 1, 1]` | `[0, 0, 0]` | **0** | **1** | 少 1 分 |

第 1 组就是题目自带的示例，直接 `python pool_split_original.py` 就能看到：

```
$ python pool_split_original.py
[3333, 3333, 3333]
```

两个方向都会错（少发、多发），说明这不是「补个 +1」能修好的，而是分配方法本身有问题。

**顺带发现的第二个坑：** float 精度。池子在 10^18 分（约 1 亿亿元）量级时，`pool * w / total`
已经超出 double 的 53 位精度，原实现会**多发 25 分**：

```
pool=1000000000000000007, weights=[3,5,7,11]
原: [..., 423076923076923072]  sum=1000000000000000032   ← 多发 25
新: [..., 423076923076923080]  sum=1000000000000000007   ← 精确
```

## 2. 如何改的（细节见 `docs/ANSWER.md`）

用**最大余数法**（Hamilton / Hare quota），全程整数运算：

1. `divmod(pool_cents * w, total)` 取整数部分，先分出去 —— 这部分之和必然 ≤ 总额；
2. 剩下的零头 `leftover = pool - sum(整数部分)`，数学上保证 `0 ≤ leftover < 人数`；
3. 按**余数从大到小**给前 `leftover` 个人各补 1 分（平局：权重更大优先，再按下标先后）。

同三组输入修复后：

```
10000 [1,1,1]        -> [3334, 3333, 3333]  sum=10000  ✅
100  [1]*6           -> [17, 17, 17, 17, 16, 16]  sum=100  ✅
1    [1,1,1]         -> [1, 0, 0]  sum=1  ✅
```

## 3. 测试与两次运行输出

同一份 `test_pool_split.py`，靠环境变量切换被测模块，保证两边的用例**完全相同**：

```bash
# ① 在未修改的代码上运行 —— 预期失败
POOL_SPLIT_MODULE=pool_split_original pytest -v test_pool_split.py

# ② 在修改后的代码上运行 —— 预期通过
pytest -v test_pool_split.py
```

### ① 未修改：失败（退出码 1）

```
======================== 13 failed, 8 passed in 0.25s =========================
FAILED test_pool_split.py::TestReportedFailures::test_docstring_example_underpays_by_one_cent
FAILED test_pool_split.py::TestReportedFailures::test_six_equal_users_overpay_by_two_cents
FAILED test_pool_split.py::TestReportedFailures::test_one_cent_three_users
FAILED test_pool_split.py::TestSumAlwaysEqualsPool::test_exhaustive_small_domain
FAILED test_pool_split.py::TestSumAlwaysEqualsPool::test_exhaustive_four_users
FAILED test_pool_split.py::TestSumAlwaysEqualsPool::test_randomized_many_users
FAILED test_pool_split.py::TestSumAlwaysEqualsPool::test_huge_pool_beyond_float_precision
FAILED test_pool_split.py::TestEdgeCases::test_more_users_than_cents
FAILED test_pool_split.py::TestEdgeCases::test_all_zero_weights_and_zero_pool
FAILED test_pool_split.py::TestEdgeCases::test_all_zero_weights_falls_back_to_equal_split
FAILED test_pool_split.py::TestEdgeCases::test_empty_weights_with_pool_is_rejected
FAILED test_pool_split.py::TestEdgeCases::test_negative_pool_is_rejected
FAILED test_pool_split.py::TestEdgeCases::test_negative_weight_is_rejected
```

典型失败信息：

```
E   AssertionError: sum=9999 != 10000 (result=[3333, 3333, 3333])
E   AssertionError: sum=102 != 100 (result=[17, 17, 17, 17, 17, 17])
```

### ② 修改后：全部通过（退出码 0）

```
test_pool_split.py::TestEdgeCases::test_does_not_mutate_input PASSED     [100%]
============================= 21 passed in 0.19s ==============================
```

完整输出见 `output/original_run.txt` 与 `output/fixed_run.txt`（就是上面两次命令的原样重定向）。

**覆盖范围**（对应可选问题 1）：不是手写几个样例，而是

* **穷举**：池子 0–120 分 × 3 人权重 0–4 → 15 125 组；再加 4 人（池子 0–60 × 权重 0–3）；
* **随机**：固定种子 500 组，池子最大 10^7、人数最多 50；
* **极值**：10^18 量级、1 分钱分给 1000 人、权重全 0、空列表、负数；
* **性质断言**：每人只能拿到 `floor` 或 `floor+1`（没人能多拿 2 分）、结果可复现、不改入参。

穷举的价值很直接：`pool=100, weights=[1,2,3]` 这种「刚好整除」的样例永远是过的，
问题只出现在特定余数组合上，人眼很难挑。

## 4. AI 使用说明

**用了**（WorkBuddy / Claude 类 AI 助手），过程如下，没有直接复制粘贴交付。

| 环节 | 内容 |
|---|---|
| 提出的问题 | ①「这段 `split_pool` 为什么会违反总额守恒？给一组能复现的具体输入」②「如何保证任意输入下 `sum == pool`？」③「设计一组能在旧代码上失败、在新代码上通过的测试」 |
| 得到的回答 | ① 逐项独立取整的误差不会抵消，两个方向都会错；② 建议最大余数法（先整除、再按余数补零头）；③ 建议用性质断言代替样例断言 |
| 是否直接采用 | **思路采用，实现改了三处**：<br>· 它建议「权重全 0 时抛异常」——我改成**平分兜底**，否则这条硬规则（总和必须等于池额）在最极端输入下就守不住；<br>· 它给的示例仍是浮点除法，我改成 `divmod` 纯整数运算（顺带修掉 10^18 量级少发/多发 25 分的问题）；<br>· 平局规则显式定为「余数 → 权重 → 下标」，让结果是确定的、可对账的 |
| 如何确认其正确 | ① **实测** AI 的说法：`round(2.5) == 2`、`round(0.5) == 0`（Python 是银行家舍入，不是四舍五入），确认「独立取整」的判断成立；② 在原始代码上跑同一套测试，**确实 13 项失败**（若全过说明测试没覆盖到问题）；③ 修复后 **21 项全过**，且穷举 + 随机 + 极值都守住不变量；④ 手工核对明细：`100 分 / 6 人` → `divmod(100,6) = 16 余 4`，前 4 人 17 分、后 2 人 16 分，合计 100，与代码输出一致 |

一句话：**AI 提供的是方向，正确性由「同一测试在旧代码上失败、在新代码上通过」这个可复现的证据来担保。**

## 5. 可选问题的回答

**① 覆盖了多少组输入？有没有比手写样例更不容易漏的写法？**
约 15 000 组穷举 + 500 组随机 + 10 余组边界。比手写样例更可靠的是「不变量 + 枚举」：
只断言 `sum == pool` 这一条性质，然后让机器去枚举输入空间；手写样例只能证明「这几组对」。

**② 多出/缺少的那几分钱给了谁？依据是什么？换一个人可行吗？**
给**余数最大**的人；余数相同时权重更大者优先，再相同则下标小者优先。
依据是最大余数法：它让每个人的实际所得与「精确值」的偏差都小于 1 分，且总量精确。
例：`10000 / [1,1,1]` → 每人 3333 余 1，三人余数相同 → 下标 0 补 1 分 → `[3334, 3333, 3333]`。
**换人可行**，只要规则是确定且可解释的（比如改成「按下单时间先后」），但必须**固定并写进对账文档**——
否则同一天的数据重算两次可能得到不同结果，这才是真正的风险。

**③ 这段代码还有其他会出错的输入吗？**
有，至少三类：
* `weights = [0, 0, 0]` 且池子不为 0 → 原实现 `ZeroDivisionError`（严格说是崩溃，不是算错）；
* `weights = []` 且池子不为 0 → 同样 `ZeroDivisionError`；
* 负数权重 → 会算出负数金额（给人倒扣钱）；
* 超大金额（> 2^53 分）→ float 精度丢失，实测多发 25 分。

**④ 为什么不用 `decimal` 或整数名额分配后再换算？**
`Decimal` 只能解决精度，解决不了「取整后总和必须精确等于池额」这个组合问题；
真正要的是「份额 + 余数再分配」这套规则，用整数就够了，也更快、更好审计。

---

## 运行方式

```bash
pip install pytest

cd code
pytest -v test_pool_split.py                                    # 修复版：21 passed
POOL_SPLIT_MODULE=pool_split_original pytest -v test_pool_split.py  # 原版：13 failed
```

Windows PowerShell 写法：

```powershell
$env:POOL_SPLIT_MODULE="pool_split_original"; pytest -v test_pool_split.py
```
