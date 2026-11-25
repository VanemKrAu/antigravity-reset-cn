# 反重力额度重置 · 中文订阅源

Google Antigravity（反重力）的额度重置公告只有英文，这个仓库把它翻成中文，输出成一条 RSS。

**订阅地址**

```
https://vanemkrau.github.io/antigravity-reset-cn/feed.xml
```

备用（jsDelivr 镜像，国内更快）：

```
https://cdn.jsdelivr.net/gh/VanemKrAu/antigravity-reset-cn@main/feed.xml
```

## 它做什么

- 每 30 分钟拉一次 `agyresets.com/feed.xml` 与 `antigravityreset.online/feed.xml`
- 按时间戳去重（两个源报道的是同一件事）
- 用 MyMemory 免费接口把推文翻成中文，翻译结果缓存在 `cache.json`，翻过的不再翻
- 标题重写成 `11月24日 04:16 · 全体用户 · Gemini + Carbon 额度重置` 这种格式，扫一眼就知道发生了什么
- 正文保留中文翻译 + 英文原文 + 原帖链接，时间全部换算成北京时间

## 它不做什么

- 不预测下次重置时间
- 不包含你自己账号的 5 小时滚动窗口恢复（那个只能在 Antigravity 应用里的 Usage 页看）
- 不保证翻译多优雅，专有名词做了回改（反重力→Antigravity、双子座→Gemini 之类）

## 本地跑

```bash
python3 gen.py        # 生成 feed.xml
```

无第三方依赖，只用标准库。

## 数据来源

- <https://agyresets.com/> — 只收重置事件的英文账本，更新最快
- <https://antigravityreset.online/> — 另一个账本，多了分档规则说明，收录略慢

非官方项目，与 Google 无关。
