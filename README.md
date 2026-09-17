# SilverFox MoviePilot Plugins

SilverFox 的 MoviePilot V2 个人插件库。

## 插件库地址

```text
https://github.com/silverfoxonline/MoviePilot-Plugins
```

## 插件

### 下载任务标签自定义

根据 Tracker 域名为下载任务添加自定义标签，不依赖 MoviePilot 站点管理。默认支持：

```text
blutopia.cc -> BLU
aither.cc -> AITHER
tracker.beyond-hd.me -> BHD
```

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
