# runstreak-warmup
# RunStreak 每日预热（避免 Azure 冷启动）

每天奥克兰时间早上 8:00 自动打开一次 [runstreak.sheng.nz](https://runstreak.sheng.nz/)  
并完成登录流程，让 Azure 后端保持"热身"状态，这样后续真人访问时就不会碰到  
1~2 分钟的冷启动延迟。

> 本方案**只做登录访问、不写入任何跑步记录**，纯粹用于预热后端。

## 工作流程

GitHub Actions 在定时触发后：

1. 启动一个 Ubuntu 环境 + 无头 Chromium
2. 打开网站首页
3. 点击首页的 **MSA Marker Demo** 按钮（会自动填入 test 账号并弹出登录框）
4. 在登录框内点击 **Sign In** 完成登录，进入 dashboard
5. 等待 dashboard 完全加载（含冷启动缓冲），后端即被预热

## 文件说明

| 文件                                   | 作用                         |
| ------------------------------------ | -------------------------- |
| `warmup.py`                          | Playwright 预热脚本，执行完整登录流程   |
| `.github/workflows/daily-warmup.yml` | 每天定时触发的 GitHub Actions 工作流 |

## 部署步骤

1. 把这个仓库（含 `warmup.py` 和 `.github/workflows/`）推送到你的 GitHub 仓库。
2. 进入仓库 **Settings → Actions → General**，确认  
   `Allow all actions and reusable workflows` 已开启。
3. 在 **Actions** 标签页里，手动触发一次 `RunStreak 每日预热` 验证能跑通（用 `workflow_dispatch`）。
4. 之后每天会自动运行，无需人工干预。

## 时区与夏令时（重要）

GitHub Actions 的 `cron` 使用 **UTC**，且不能自动切换新西兰夏令时。当前工作流里  
写的是冬季时间：

- **冬季 NZST（UTC+12）**：奥克兰 08:00 = UTC 20:00 → `0 20 * * *`（当前生效）
- **夏季 NZDT（UTC+13）**：奥克兰 08:00 = UTC 19:00 → 需改为 `0 19 * * *`

新西兰夏令时大致区间：**每年 9 月最后一个周日 → 次年 4 月第一个周日**。  
进入夏令时时，请手动把 `daily-warmup.yml` 里的 cron 从 `0 20 * * *` 改成 `0 19 * * *`，  
次年转回冬季时再改回来。

## 本地测试

```bash
pip install playwright
playwright install chromium
python warmup.py
```

退出码：成功为 `0`，失败为 `1`（可在 CI 中据此报警）。
