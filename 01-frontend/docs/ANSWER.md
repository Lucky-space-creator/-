# 前端题 ——「Upload Your Resume」最后一步

**实现文件：** `code/index.html`、`code/styles.css`、`code/app.js` —— 无构建步骤、无任何依赖。

```bash
# 最简单的方式：直接打开文件
start code/index.html          # Windows
# 或者起个静态服务（只是为了让页面有一个 http 源）
python -m http.server 5500 -d code
```

| 截图 | 文件 |
|---|---|
| 桌面端 · 空状态 | `assets/desktop-default.png` |
| 桌面端 · 已选文件 | `assets/desktop-selected.png` |
| 移动端 390 px | `assets/mobile.png` |
| 平板 834 px | `assets/tablet.png` |

---

## 1. 设计稿的要求与落点

Figma 文件（`node-id=0-1`）是一个三步套流程，这一屏是**最后一步**，旁边的批注框列出了评分标准：

| 设计要求 | 对应实现 |
|---|---|
| 页面结构与布局正确 | 纯白页面，文案在左栏顶部，插图贴齐底部边缘，上传卡片在右侧 |
| 样式还原度：字号、颜色、按钮样式、图标位置、圆角、阴影 | `:root` 里的 token；颜色取自设计稿采样（见第 2 节）；卡片圆角 18 px、虚线框 4 px、按钮 6 px |
| HTML 语义化与结构清晰 | `main > section > h1/h2`、真实 `<form>`、`<input type="file">`、`<ol>` 步进器、`aria-*` 属性 |
| 点击上传区打开文件选择框 | `app.js` → `openPicker()`（同时支持键盘 `Enter` / `Space`） |
| hover / active 状态 | `.dropzone:hover`、`.is-dragover`、`.btn:hover`、`.btn:active`、`:focus-visible` 焦点环 |
| 响应式：小屏自动改为上下结构 | `@media (max-width: 900px)` → 单列；420 px 以下按钮占满一行 |
| 显示上传文件名 | `#file-name` 替换掉虚线框内的提示文案，显示文件名 + 大小 |

## 2. 与设计稿的还原对照

设计稿是以截图形式提供的，所以下表的数值是**从截图里量的**（颜色做像素采样，尺寸按比例换算），
不是从 Figma 的 inspect 面板里抄的。

| 设计元素 | 实现值 |
|---|---|
| Finish 按钮 | `#2360FF`，白色 14 px 字，高 42 px，圆角 6 px |
| Last step 按钮 | `#7FB0F8`（浅蓝底白字）—— 是**实心**次要按钮，不是描边按钮 |
| 上传区 | 填充 `#F2FAFF`，1.5 px 虚线 `#7FA6F0`，圆角 4 px，云朵+箭头图标 `#2C63F3`，两行居中的 11.5 px `#A3A8B0` 文案 |
| 卡片 | 白底、圆角 18 px、柔和阴影，标题「Upload file」20 px / 600 |
| 步进器 | 三个 18 px 的 `#4B7BFF` 圆点，各带一个白色对勾，`#C9D8FF` 轨道两端超出圆点 |
| 布局 | 左栏 300 px，间距 96 px，卡片 584 × 542 px（高宽比 0.93，设计稿为 0.88） |
| 文案 | 「Finish!」「Upload Your Resume」、说明段落、「Upload file」、两个按钮、上传区提示 —— 均照抄设计稿 |

**关于插图：** 用的是设计稿原图，不是我重绘的。做法是从提供的设计稿截图中裁切（`assets/illustration.png`，
630 × 544，约为实际显示尺寸的 2 倍），并把 Figma 画布底色 `rgb(248,251,249)` 归一为纯白，
否则页面上会露出一块灰色方块；然后按普通静态资源引用即可。如果能拿到矢量导出件，
把该文件换成 `illustration.svg` 并改一下 `<img src>` 就完事 —— 布局代码不关心插图是什么格式。

**有一行文案仍是推断的。** 提供的截图里，Figma 的协作者头像挡住了段落第二行，只能看到
「…then click ▢ step」。我补成「…then click Next step」——与可见的结尾和向导语境都对得上，
但这一屏的按钮写的是 *Finish*，两者本身就不一致。建议找文案负责人确认一下。

因此尺寸是**按比例还原**而非精确对齐：截图是 29% 缩放的画布，绝对字号是由元素间比例反推的，
与原始设计大约有 ±2 px 的偏差。所有数值都集中在 `:root` 和各个组件块里，对着真实文件校正大约 10 分钟。

## 3. 实现说明

**刻意不用框架。** 这一屏是一个静态视图 + 三个交互。用 `create-react-app` / Vite 脚手架，
为了约 150 行原生 JS 要引入 ~40 MB 的 `node_modules` 和一套构建流程，不划算。
如果团队要组件化，这段结构可以 1:1 映射成 `<ResumeUploader>`，迁移是机械工作。

**拖拽上传里几个常被忽略的点：**

* `dragenter` / `dragleave` 会在每个子节点上触发，朴素的写法会让高亮疯狂闪烁 —— 用深度计数器解决。
* 文件拖到上传区外面，浏览器会直接打开该文件；在 window 上挂 `dragover` / `drop` 并
  `preventDefault()` 才能拦住。
* 一次拖入多个文件时，明确用 toast 提示「只取第一个」，而不是悄悄取 `files[0]`。

**校验放在 UI 提交之前**，不是等提交后才报错：扩展名白名单（`pdf/doc/docx/png/jpg/jpeg`）、
≤ 10 MB、非空文件。错误渲染在 `role="alert"` 的段落里、上传区转红；同时**清空已选状态**，
避免出现「字段看起来已填好、实际拿着一个非法文件」的情况。

**可访问性：** 上传区是真正的 `role="button"` + `tabindex="0"`，`aria-label` 会切换成
「已选择文件 X，点击可替换」；文件名通过 toast（`role="status"`）播报；焦点环显式声明
（`:focus-visible`）；`prefers-reduced-motion` 下关闭过渡动画；步进器暴露 `aria-current="step"`
并带仅供读屏的文本。

**状态模型**（唯一数据源是 `selectedFile`）：

```
空 ──选择合法文件──▶ 已选 ──再选合法文件──▶ 已选（被替换）
  ▲                      │
  └────选择非法文件───────┘  （显示错误，并清空已选）
```

## 4. 后续可做

1. **换成矢量导出件**：如果 Figma 能给 `illustration.svg`，直接替换 —— 现在的位图是 2 倍裁切，
   在 3 倍屏上会略软。
2. **确认段落最后一行文案**，以及 *Last step* 究竟是「返回上一步」还是「折叠回第 2 步」
   （当前实现调用 `history.back()`，没有历史记录时退化为 toast 提示）。
3. **接后端**：`POST /resume` + `FormData` + 上传进度 + 错误映射 —— 表单已经会派发携带 `File`
   的 `resume:submit` 事件，接上去即可。
4. **加视觉回归**：用 Playwright 在 1440 / 834 / 390 px 三档做截图对比，避免后续改样式时悄悄改坏布局。
