import inspect
import sys
from pathlib import Path
from typing import Iterable, Optional

from environs import Env
from pydantic import BaseModel


class FFmpeg(BaseModel):
    # TODO render too slow
    video_params: dict = dict()
    # video_params: dict = dict(hwaccel_output_format='cuda')
    create_params: dict = {
        'acodec': 'aac', 'vcodec': 'libx264', 'maxrate': '2000k', 'shortest': None, 'f': 'flv', 'bufsize': '6000k',
        'b:v': '2000k', 'b:a': '128k', 'ar': '44100', 'framerate': '30', 'g': '30', 'preset': 'ultrafast',
    }
    stream_params: dict = dict(f='flv', codec='copy')


class TG(BaseModel):
    chat_id: Optional[str]
    token: Optional[str]


class VK(BaseModel):
    group_id: str
    access_token: str


class Config(BaseModel):
    stream_url: str
    stream_key: str
    pray_top: Optional[int]
    stop_after: Optional[int]
    video_file: str
    audio_path: str
    tmp_path: str  # TODO virtual drive
    threads: int = 1
    stream_cmd: Optional[str]
    debug: bool
    tg_: TG = None
    vk_: VK = None
    _ffmpeg: FFmpeg = FFmpeg()
    _in_file: str = 'input.txt'


def script_dir():
    return Path(inspect.currentframe().f_back.f_code.co_filename).parent.resolve()


def conf_by_model(env, model, with_prefix=False, check_fields: Iterable = None):
    prefix = f"{model.__name__.upper()}_" if with_prefix else ''
    conf = model(**{key: env(prefix + key.upper())
                    for key in model.__fields__.keys()
                    if not key.endswith('_')})
    if check_fields:
        if not all([getattr(conf, field, False) for field in check_fields]):
            conf = None
    return conf


def read_config() -> Config:
    env = Env()
    cur_path = script_dir()
    env.read_env(str(cur_path / '.env.example'))
    env.read_env(override=True)

    # считать конфиг из параметра запуска поверх стандартного
    if len(sys.argv) > 1:
        env.read_env(str(cur_path / sys.argv[1]), override=True)

    conf = conf_by_model(env, Config)
    conf.tg_ = conf_by_model(env, TG, with_prefix=True, check_fields=('chat_id', 'token'))
    conf.vk_ = conf_by_model(env, VK, with_prefix=True, check_fields=('access_token', 'group_id'))

    conf._ffmpeg.create_params['threads'] = conf.threads
    Path(conf.tmp_path).mkdir(parents=True, exist_ok=True)
    return conf
