import re
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain

@register(
    "astrbot_plugin_output_pro_filter",
    "gabriel",
    "综合输出管理插件：包含重复发言拦截、敏感词过滤、错误屏蔽及管理员通知功能。",
    "1.0.0"
)
class OutputProFilter(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.plugin_id = "astrbot_plugin_output_pro_filter"
        self.config = config
        self.last_text_by_session = {}
        self.admins_id = context.get_config().get("admins_id", [])
        self._reload_config()
        logger.info(f"[{self.plugin_id}] 插件已载入")

    def _reload_config(self):
        # 1. 重复发言拦截配置
        self.config.setdefault("enable_repeat_filter", True)
        self.config.setdefault("repeat_ignore_whitespace", True)
        self.config.setdefault("repeat_block_notice", "")
        
        # 2. 敏感词/内容过滤配置
        self.config.setdefault("enable_word_filter", True)
        self.config.setdefault("filter_delete_words", []) # 仅删除
        self.config.setdefault("filter_block_words", ["请求失败", "错误信息", "Traceback", "Exception"]) # 拦截整个消息
        self.config.setdefault("filter_block_notice", "哎呀，系统刚才打了个盹，你可以换个话题或者稍后再试哦~")
        
        # 3. 错误通知配置
        self.config.setdefault("enable_admin_notify", True)
        
        # 加载到实例
        self.enable_repeat = bool(self.config.get("enable_repeat_filter", True))
        self.repeat_ignore_ws = bool(self.config.get("repeat_ignore_whitespace", True))
        self.repeat_notice = str(self.config.get("repeat_block_notice", ""))
        
        self.enable_word_filter = bool(self.config.get("enable_word_filter", True))
        self.delete_words = list(self.config.get("filter_delete_words", []))
        self.block_words = list(self.config.get("filter_block_words", []))
        self.filter_notice = str(self.config.get("filter_block_notice", ""))
        
        self.enable_notify = bool(self.config.get("enable_admin_notify", True))

    def _save_config(self):
        try:
            self.config.save_config()
        except Exception as e:
            logger.warning(f"[{self.plugin_id}] 配置保存失败: {e}")

    def _get_text(self, event: AstrMessageEvent) -> str:
        result = event.get_result()
        if not result or not getattr(result, "chain", None):
            return ""
        parts = [str(c.text) for c in result.chain if isinstance(c, Plain)]
        return "".join(parts)

    def _build_regex(self, words: list) -> str:
        if not words: return ""
        return "|".join([re.escape(str(w).strip()) for w in words if str(w).strip()])

    @filter.on_decorating_result()
    async def process_output_filter(self, event: AstrMessageEvent):
        result = event.get_result()
        if not result or not getattr(result, "chain", None):
            return

        original_text = self._get_text(event)
        if not original_text.strip():
            return

        if self.enable_word_filter:
            block_pattern = self._build_regex(self.block_words)
            if block_pattern and re.search(block_pattern, original_text, re.IGNORECASE):
                logger.warning(f"[{self.plugin_id}] 触发内容拦截: {original_text!r}")

                if self.enable_notify and self.admins_id:
                    sender = event.get_sender_name() or event.get_user_id()
                    session_name = "私聊"
                    if event.message_obj and event.message_obj.group_id:
                        session_name = f"群聊({event.message_obj.group_id})"

                    admin_msg = f"姐姐，刚才在 {session_name} 里，[{sender}] 触发了错误或拦截词：\n内容：{original_text}"
                    for admin_id in self.admins_id:
                        try:
                            await event.bot.send_private_msg(user_id=int(admin_id), message=admin_msg)
                        except Exception as e:
                            logger.warning(f"[{self.plugin_id}] 管理员通知发送失败 admin_id={admin_id!r}: {e}")

                if self.filter_notice:
                    result.chain = [Plain(self.filter_notice)]
                else:
                    result.chain = []
                return

            delete_pattern = self._build_regex(self.delete_words)
            if delete_pattern:
                for comp in result.chain:
                    if isinstance(comp, Plain):
                        comp.text = re.sub(delete_pattern, "", str(comp.text), flags=re.IGNORECASE)

        final_text = self._get_text(event)
        if not final_text.strip():
            result.chain = []
            return

        if self.enable_repeat:
            norm_text = "".join(final_text.split()) if self.repeat_ignore_ws else final_text
            session_id = getattr(event, "session_id", "global")
            if self.last_text_by_session.get(session_id) == norm_text:
                logger.info(f"[{self.plugin_id}] 拦截重复回复: {final_text!r}")
                if self.repeat_notice:
                    result.chain = [Plain(self.repeat_notice)]
                    self.last_text_by_session[session_id] = "".join(self.repeat_notice.split()) if self.repeat_ignore_ws else self.repeat_notice
                else:
                    result.chain = []
                return
            self.last_text_by_session[session_id] = norm_text

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("加输出拦截词")
    async def add_block_word(self, event: AstrMessageEvent, word: str):
        if word not in self.block_words:
            self.block_words.append(word)
            self.config["filter_block_words"] = self.block_words
            self._save_config()
            yield event.plain_result(f"✅ 已添加拦截词: {word}")
        else:
            yield event.plain_result(f"❗ '{word}' 已在拦截词列表中")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("加输出删除词")
    async def add_delete_word(self, event: AstrMessageEvent, word: str):
        if word not in self.delete_words:
            self.delete_words.append(word)
            self.config["filter_delete_words"] = self.delete_words
            self._save_config()
            yield event.plain_result(f"✅ 已添加删除词: '{word}'")
        else:
            yield event.plain_result(f"❗ '{word}' 已在删除词列表中")
