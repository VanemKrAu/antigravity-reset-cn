# 反重力额度重置 · 中文订阅源

Google Antigravity（反重力）的额度重置公告只有英文，这个项目把它翻成中文，输出成一条 RSS。

**主订阅地址（Cloudflare Workers，每 15 分钟自动更新，推荐使用）**

```
https://antigravity-reset-cn.vanemwalker.workers.dev/feed.xml
```

备份地址（本仓库 GitHub Pages 实现，因新建仓库 Actions 定时任务暂未稳定触发，仅作备份保留）：

```
https://vanemkrau.github.io/antigravity-reset-cn/feed.xml
```

jsDelivr 镜像：

```
https://cdn.jsdelivr.net/gh/VanemKrAu/antigravity-reset-cn@main/feed.xml
```

## 它做什么

- **线上主线（Cloudflare Workers）**：每 15 分钟由 Cron Triggers 拉一次 `agyresets.com/feed.xml` 与 `antigravityreset.online/feed.xml`，使用 Workers KV 缓存翻译结果与最终 `feed.xml`
- 按时间戳（精确到分钟）去重（两个源报道的是同一件事）
- 用 MyMemory 免费接口把推文翻成中文，翻译结果缓存复用，翻过的不再重复请求
- 标题重写成 `11月24日 04:16 · 全体用户 · Gemini + Carbon 额度重置` 这种格式，扫一眼就知道发生了什么
- 正文保留中文翻译 + 英文原文 + 原帖链接，时间全部换算成北京时间（UTC+8）

## 它不做什么

- 不预测下次重置时间
- 不包含你自己账号的 5 小时滚动窗口恢复（那个只能在 Antigravity 应用里的 Usage 页看）
- 不保证翻译多优雅，专有名词做了回改（反重力→Antigravity、双子座→Gemini 之类）

## 本地跑（备份 Python 实现）

```bash
python3 gen.py        # 生成 feed.xml（翻译缓存落在 cache.json）
```

无第三方依赖，只用标准库。

## 数据来源

- <https://agyresets.com/> — 只收重置事件的英文账本，更新最快
- <https://antigravityreset.online/> — 另一个账本，多了分档规则说明，收录略慢

非官方项目，与 Google 无关。
