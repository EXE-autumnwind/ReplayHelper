# ReplayHelper

ReplayHelper 可以利用[ServerReplay](https://modrinth.com/mod/server-replay)Mod，以 `.mcpr` 格式为每位玩家单独录制并自动切断。

## 功能特点

- **自动录制**：无需手动操作，插件会自动记录所有玩家。
- **排除假人**：插件会排除以_fake结尾的玩家
- **自动裁切**：插件每两小时会自动裁切录像

## 注意事项
- 插件依赖于[ServerReplay](https://modrinth.com/mod/server-replay) Mod，如果缺失插件无法工作
- 插件只能运行在[MCDR](https://mcdreforged.com/)服务器上

## 使用教程

 **安装插件**：将插件文件放置在MCDR服务器的插件目录下，并重新启动服务器。

### 指令

> `!!rp <玩家ID> start` 开始某人的录像

> `!!rp <玩家ID> stop` 停止某人的录像

> `!!rp <玩家ID> cut` 裁切某人的录像
