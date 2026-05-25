# Output Pro Filter 综合输出拦截器

这是一个为 AstrBot 设计的高级输出管道处理器插件，提供重复发言拦截、敏感词/错误堆栈报错拦截与删除、以及管理员实时私聊通知三大核心功能。

## 🌟 核心功能

### 1. 重复发言拦截 (Repeat Filter)
- **原理**：基于 `on_decorating_result` 过滤器，在输出结果装配阶段对当前 Session 的上一次发言进行比对。
- **空白忽略**：支持开启 `repeat_ignore_whitespace`，忽略所有空格、制表符、换行等空白字符差异，防止微小格式差异绕过拦截。
- **自定义反馈**：可设置 `repeat_block_notice`。若配置为空，则直接触发静默拦截（完全吞掉重复回复，不产生任何系统提醒）。

### 2. 敏感词与错误拦截 (Word & Exception Filter)
- **仅删除模式 (`filter_delete_words`)**：在输出链中全局擦除匹配的内容，而保留剩余的正常文本。
- **整条拦截模式 (`filter_block_words`)**：
  - 默认拦截 `Traceback`, `Exception`, `请求失败` 等底层 LLM 或 API 异常堆栈，避免给用户返回不友好的系统报错。
  - 一旦触发，整个回复将直接被替换为温馨提示（`filter_block_notice`），如 `哎呀，系统刚才打了个盹...`。

### 3. 管理员即时推送 (Admin Notification)
- 当输出触发敏感词或错误拦截时，插件会自动解析当前会话来源（私聊或群聊）以及触发用户。
- 自动私聊推送详细拦截报告至 `Context` 配置中的 `admins_id`（通常为姐姐的 QQ 号），方便管理员掌握机器人的运行状态。

---

## 🛠️ 配置说明 (`_conf_schema.json`)

你可以直接在 AstrBot 的 Web 管理面板中进行图形化配置，所有配置项均配备了详细的 `hint` 释义：

| 配置项 | 类型 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `enable_repeat_filter` | `bool` | `true` | 是否启用重复发言拦截。 |
| `repeat_ignore_whitespace` | `bool` | `true` | 比对时是否忽略空白差异。 |
| `repeat_block_notice` | `string` | `""` | 重复发言被拦截时的提示词（为空则静默拦截）。 |
| `enable_word_filter` | `bool` | `true` | 是否启用内容敏感词与系统报错过滤。 |
| `filter_delete_words` | `list` | `[]` | 仅做删除处理的关键词列表（擦除不拦截）。 |
| `filter_block_words` | `list` | `["请求失败", "错误信息", "Traceback", "Exception"]` | 触发拦截整条回复的关键词列表（防止把系统报错吐给用户）。 |
| `filter_block_notice` | `string` | `"哎呀，系统刚才打了个盹..."` | 触发整条消息拦截时的用户端占位符。 |
| `enable_admin_notify` | `bool` | `true` | 触发拦截时是否向管理员 QQ 推送详细日志。 |

---

## 🎮 指令系统

所有管理指令均被绑定到了管理员权限（需在全局配置中成为管理员），前缀为 `~`：

- `~加输出拦截词 <词>`：将指定敏感词或错误标记追加到拦截词库中。
- `~加输出删除词 <词>`：追加到仅删除名单。

---

## 💎 开发与协议
- **作者**: gabriel
- **版本**: v1.0.0