import threading
import time
import os
import json
from typing import Dict, Any
from mcdreforged.api.all import *

CONFIG_FILE = 'config.json'
DEFAULT_CUT_TIME = 120

player_timers: Dict[str, threading.Timer] = {}
config = {
    'cut_time_minutes': DEFAULT_CUT_TIME
}

HELP_MESSAGE = """
Replay helper - 回放管理插件
§6!!rp help§r - 显示此帮助菜单
§6!!rp <玩家> start§r - 开始录制并重置计时器
§6!!rp <玩家> stop§r - 停止录制并取消计时器
§6!!rp <玩家> cut§r - 剪切回放并重置计时器
    该插件由EXE_autumnwind编写
""".strip()


def is_fake_player(player: str) -> bool:
    return player.lower().endswith('_fake')

def get_config_path(server: PluginServerInterface) -> str:
    if hasattr(server, 'get_data_folder'):
        return os.path.join(server.get_data_folder(), CONFIG_FILE)
    return os.path.join('plugins', 'replay_helper', CONFIG_FILE)

def load_config(server: PluginServerInterface):
    global config
    config_path = get_config_path(server)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    if not os.path.exists(config_path):
        save_config(server)
        return
    
    try:
        with open(config_path, 'r', encoding='utf8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError("配置文件为空")
            loaded_config = json.loads(content)
            
            if isinstance(loaded_config, dict) and 'cut_time_minutes' in loaded_config:
                if isinstance(loaded_config['cut_time_minutes'], int) and loaded_config['cut_time_minutes'] > 0:
                    config.update(loaded_config)
                else:
                    raise ValueError("无效的裁切时间配置")
            else:
                raise ValueError("缺少必要配置项")
    except Exception as e:
        server.logger.warning(f"加载配置文件失败({e})，使用默认配置")
        save_config(server)

def save_config(server: PluginServerInterface):
    config_path = get_config_path(server)
    try:
        temp_path = f"{config_path}.tmp"
        with open(temp_path, 'w', encoding='utf8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        if os.path.exists(config_path):
            os.replace(temp_path, config_path)
        else:
            os.rename(temp_path, config_path)
    except Exception as e:
        server.logger.error(f"保存配置文件失败: {e}")

def reset_timer(server: PluginServerInterface, player: str):
    if is_fake_player(player):
        return
        
    if player in player_timers:
        player_timers[player].cancel()
    
    def timer_callback():
        cut_player_replay(server, player)
    
    timer = threading.Timer(config['cut_time_minutes'] * 60, timer_callback)
    timer.daemon = True
    timer.start()
    player_timers[player] = timer

def cut_player_replay(server: PluginServerInterface, player: str):
    if is_fake_player(player):
        return
        
    def _cut_operation():
        try:
            server.execute(f'replay stop players {player} true')
            time.sleep(2)
            server.execute(f'replay start players {player}')
        except Exception as e:
            server.logger.error(f"error: {e}")

    threading.Thread(
        target=_cut_operation,
        name=f"ReplayCut_{player}",
        daemon=True
    ).start()

def start_player_replay(server: PluginServerInterface, player: str):
    if is_fake_player(player):
        return
        
    try:
        server.execute(f'replay start players {player}')
    except Exception as e:
        server.logger.error(f"error: {e}")

def show_help(server: PluginServerInterface, source: CommandSource):
    source.reply(HELP_MESSAGE.format(cut_time=config['cut_time_minutes']))

def cut_replay(source: CommandSource, ctx: Dict[str, str]):
    if source.is_player and not source.has_permission(3):
        source.reply('§c权限不足')
        return
    
    player = ctx['player']
    if is_fake_player(player):
        source.reply(f'§c{player}应该是假人罢，已中止replay录像')
        server.say(f'§c{player}应该是假人罢，已中止replay录像') 
        return
    
    server = source.get_server()
    cut_player_replay(server, player)
    reset_timer(server, player)

def start_replay(source: CommandSource, ctx: Dict[str, str]):
    if source.is_player and not source.has_permission(3):
        source.reply('§c权限不足')
        return
    
    player = ctx['player']
    if is_fake_player(player):
        source.reply(f'§c{player}应该是假人罢，已中止replay录像')
        server.say(f'§c{player}应该是假人罢，已中止replay录像') 
        return
    
    server = source.get_server()
    start_player_replay(server, player)
    reset_timer(server, player)

def stop_replay(source: CommandSource, ctx: Dict[str, str]):
    if source.is_player and not source.has_permission(3):
        source.reply('§c权限不足')
        return
    
    player = ctx['player']
    server = source.get_server()
    
    try:
        server.execute(f'replay stop players {player} true')
    except Exception as e:
        server.logger.error(f"停止回放时出错: {e}")
    
    if player in player_timers:
        player_timers[player].cancel()
        del player_timers[player]

def set_cut_time(source: CommandSource, ctx: Dict[str, Any]):
    if source.is_player and not source.has_permission(3):
        source.reply('§c权限不足')
        return
    
    minutes = ctx['minutes']
    if minutes <= 0:
        source.reply('§c时间必须大于0分钟')
        return
    
    server = source.get_server()
    config['cut_time_minutes'] = minutes
    save_config(server)
    source.reply(f"§a已设置自动裁切间隔为 {minutes} 分钟")

def on_player_joined(server: PluginServerInterface, player: str, info: Info):
    if is_fake_player(player):
        server.logger.info(f'{player}应该是假人罢，已中止replay录像')
        server.say(f'§c{player}应该是假人罢，已中止replay录像') 
        return
        
    try:
        start_player_replay(server, player)
        reset_timer(server, player)
    except Exception as e:
        server.logger.error(f"错误: {e}")

def on_player_left(server: PluginServerInterface, player: str):
    if is_fake_player(player):
        return
        
    if player in player_timers:
        try:
            player_timers[player].cancel()
            del player_timers[player]
        except Exception as e:
            server.logger.error(f"错误: {e}")

def on_load(server: PluginServerInterface, old):
    try:
        load_config(server)

        server.register_event_listener('player_joined', on_player_joined)
        server.register_event_listener('player_left', on_player_left)
        root_node = Literal('!!rp').\
            runs(lambda src: show_help(server, src)).\
            then(
                Text('player').
                then(Literal('cut').runs(cut_replay)).
                then(Literal('start').runs(start_replay)).
                then(Literal('stop').runs(stop_replay))
            ).\
            then(
                Literal('set').
                then(
                    Literal('cuttime').
                    then(Integer('minutes').runs(set_cut_time))
                )
            )
        
        server.register_command(root_node)
        server.register_command(Literal('!!RP').redirects(root_node))
        
        server.logger.info(f'当前自动裁切间隔: {config["cut_time_minutes"]}分钟')
    except Exception as e:
        server.logger.error(f'插件加载失败: {e}')
        import traceback
        server.logger.error(traceback.format_exc())
