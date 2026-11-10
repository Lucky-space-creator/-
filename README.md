# 笔试题 · 需要 GitHub 链接的题目

本仓库包含三份要求提交 **GitHub 链接 / Git 仓库**的作业。另外三道题（爬虫、Python 流式 API、
基础模型自动标注）的提交形式是 CSV、演示代码和压缩包，不在本仓库内，已单独打包。

| # | 题目 | 目录 | 提交要求 | 状态 |
|---|---|---|---|---|
| 1 | 前端：还原 Figma 设计稿 | [`01-frontend/`](01-frontend) | *Submit a GitHub Link* | ✅ |
| 2 | 后端：Spring Boot 3.2.0 + Spring Security | [`02-backend/`](02-backend) | *Submit a GitHub link* | ✅ |
| 6 | 分账 Bug：总额不守恒 | [`06-pool-split/`](06-pool-split) | *压缩包或 Git 仓库*（此处以仓库形式提交） | ✅ |

每个目录统一为 `code/`（实现）+ `docs/`（答案说明）。

---

## 01 · 前端

用原生 HTML/CSS/JS 还原设计稿的「Finish! Upload Your Resume」页面，无构建步骤、无依赖。

```
01-frontend/code/index.html · styles.css · app.js · assets/illustration.png
01-frontend/docs/ANSWER.md        设计对照表、实现说明、已知差异
01-frontend/docs/assets/*.png     桌面 / 已选文件 / 平板 / 手机 四张截图
```

打开方式：直接双击 `code/index.html`，或 `python -m http.server 5500 -d code`。

已实现：拖拽与点击上传、类型白名单与 10 MB 校验、文件名与大小回显、hover/active/focus 态、
≤900 px 单列响应式、可访问性（`role="button"`、`aria-live`、`aria-current`）。

## 02 · 后端

Spring Boot **3.2.0** + Spring Security 6.2 + JJWT，JWT 无状态认证。

```bash
cd 02-backend/code
mvn test          # 5 个集成测试，全部通过
mvn spring-boot:run

# 1) 无 token 访问受保护接口 -> 401
curl -i http://localhost:8080/api/hello

# 2) 用户名密码登录（test / 123456）-> 拿到 JWT
curl -X POST http://localhost:8080/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"123456"}'

# 3) 带 token 访问 -> "Hello World"
curl -i http://localhost:8080/api/hello -H "Authorization: Bearer $TOKEN"
```

`docs/ANSWER.md` 里有接口契约、安全设计的取舍（为什么用 JWT 而不是 session）、测试覆盖清单和生产化缺口。

## 06 · 分账 Bug

题目给的 `split_pool` 用 `round()` 逐项取整，导致所有人拿到的钱加起来不等于池子总额。

```bash
cd 06-pool-split/code
pip install pytest

pytest -v test_pool_split.py                                          # 修复后：21 passed
POOL_SPLIT_MODULE=pool_split_original pytest -v test_pool_split.py    # 原始版：13 failed
```

| 输入 | 返回 | 实际和 | 应有和 |
|---|---|---|---|
| `10000, [1,1,1]` | `[3333, 3333, 3333]` | 9999 | 10000 |
| `100, [1]*6` | `[17]*6` | 102 | 100 |
| `1, [1,1,1]` | `[0,0,0]` | 0 | 1 |

修复用最大余数法 + 纯整数运算；两次运行的完整输出在 `06-pool-split/code/output/`，
问题 1/3/4 的书面说明在 `06-pool-split/code/README.md`，技术分析在 `06-pool-split/docs/ANSWER.md`。

---

## 环境

* 前端：现代浏览器即可，无依赖
* 后端：JDK 17 + Maven 3.9（`mvn test` 在本机跑通：5/5）
* 分账：Python 3.10+，仅测试需要 `pytest`

所有结果均为本机真实运行产出，未使用占位数据。
