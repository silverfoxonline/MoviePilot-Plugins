# SilverFox MoviePilot Plugins

SilverFox 的 MoviePilot V2 个人插件库。

## 插件库地址

```text
https://github.com/silverfoxonline/MoviePilot-Plugins
```

## 插件

### SP活动奖励自动领取

自动读取 `https://seedpool.org/events`，发现并逐个检查全部活动，无需填写活动编号。
使用 MoviePilot 中 `seedpool.org` 站点的 Cookie、UA 和代理设置；也可在插件中单独填写 Cookie。
以网页标记的当天可领卡片及其 POST 表单为准，领取后重新读取同一活动核验；已领、未来或过期奖励不提交。
某个活动失败不会阻止其他活动领取。默认 Cron 为 `15 */6 * * *`，按 MP2 时区每 6 小时检查一次，
也可勾选“立即运行一次”。请求失败后在下次运行重新读取状态，不直接重放领取请求。

详情页展示各活动的已领天数、当前月每日状态与奖励，以及最近 100 条执行记录，仅访问本地缓存。
仅有成功或失败结果时发送通知；没有可领奖励时保持安静。不会自动补领网页不允许领取的过期奖励。

版本 `1.0.0`。参考本仓库 BLU 活动奖励插件，适配 Seedpool 的 `/events/{id}/claims` 表单。
离线测试：`python -m unittest discover -s tests -p test_seedpooleventclaim.py -v`。

### 下载任务分类与标签-改版

基于叮叮当的“下载任务分类与标签”2.6，保留原插件功能，并统一以下站点标签：

```text
Aither / aither.cc -> AITHER
BeyondHD / beyond-hd.me -> BHD
Orpheus / orpheus.network -> OPS
Blutopia / blutopia.cc -> BLU
GazelleGames / gazellegames.net -> GGn
```

安装并迁移配置后应停用原版插件，避免两个插件同时处理下载任务。

### 下载任务标签自定义

根据 Tracker 域名为下载任务添加自定义标签，不依赖 MoviePilot 站点管理。默认支持：

```text
blutopia.cc -> BLU
aither.cc -> AITHER
tracker.beyond-hd.me -> BHD
```

插件详情页显示最近 200 条标签写入结果，包括下载器、任务、标签以及成功或失败原因。

### PT站开放注册监控

监测 PT 站注册页面是否开放，并仅在状态变为开放时发送通知。

自定义站点配置示例：

```json
[
  {
    "name": "SeedPool",
    "url": "https://seedpool.org/register"
  }
]
```

原始插件作者：bfjy；当前仓库维护：silverfoxonline。

### Vue-PT监护室

基于 [KoWming 的 Savept 插件](https://github.com/KoWming/MoviePilot-Plugins) v1.1.1，保留原作者署名。v1.1.2 将整页正则匹配改为按 HTML 卡片节点解析，修复抓取站点页面时可能使 MP2 卡死的问题。
