# GitHub 发布步骤（照着做即可）

## 一、仓库信息

- **仓库名**：`social-game-ops-analysis`
- **简介（Description）**：社交游戏运营数据分析：SQL 指标体系 + 漏斗 + AB 实验（Python / SQLite）
- **Topics**：`data-analysis` `sql` `ab-testing` `python` `pandas` `matplotlib` `sqlite` `game-analytics` `portfolio`

## 二、先在 GitHub 建空仓库

1. 打开 github.com → 右上角 `+` → New repository
2. Repository name 填 `social-game-ops-analysis`
3. 选 Public（作品集建议公开）
4. **不要**勾选 "Add a README file"（本地已经有了，勾了会冲突）
5. 点 Create repository

## 三、本地推送（PowerShell 里执行）

```powershell
cd "C:\Users\86138\Documents\deepseek-harness\default-workspace\projects\social_game_ops"

git init
git add .
git commit -m "feat: social game ops dashboard + AB test analysis"
git branch -M main

# 把下面的 <你的用户名> 换成你的 GitHub 用户名
git remote add origin https://github.com/wen040555/social-game-ops-analysis.git
git push -u origin main
```

第一次推送会弹窗让你登录 GitHub，按提示授权即可。

## 四、如果没装 Git

两个办法：

1. 装 Git：https://git-scm.com/download/win ，一路下一步，然后重跑上面的命令。
2. 不装 Git：在 GitHub 仓库页面点 `Add file` → `Upload files`，把这些拖进去：
   - `README.md`
   - `src/`（整个文件夹）
   - `images/`（整个文件夹，README 里的图靠它显示）
   - `社交游戏运营数据分析报告.pdf`
   - `.gitignore`

   `data/` 和 `output/` 可以先不传，README 里写了怎么重新生成。

## 五、确认 README 显示正常

打开仓库首页，应该能看到：

- 顶部的报告首页截图
- 指标表和 AB 实验结果表
- 四张图（DAU、留存、漏斗、AB）
- 目录结构、快速开始、指标口径

如果图片显示不出来，检查 `images/` 是否上传、文件名大小写是否一致。

## 六、把链接用到求职里

- 简历「项目经历」里加一行：`项目代码与报告：https://github.com/wen040555/social-game-ops-analysis`
- 网申的「作品链接」栏填这个仓库地址
- 发邮件时附一句：`项目代码与完整报告见 GitHub：...`

## 七、可选：加开源协议

在仓库页面点 `Add file` → `Create new file`，文件名填 `LICENSE`，内容用 MIT 协议模板即可（GitHub 创建时会提示 choose a license template）。

## 八、注意

- `data/` 和 `output/sql_results/` 已被 `.gitignore` 排除，别人 clone 后运行 `python src/gen_data.py` 就能复现（随机种子固定为 42，结果一致）。
- 报告 PDF 和 `images/` 一定要提交，面试官往往只看首页。
- 仓库名、简介、Topics 建议按上面写，关键词对搜索和 HR 浏览都友好。
