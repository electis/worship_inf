import glob
import logging
import os
from time import sleep

import ffmpeg
from future.backports.datetime import datetime, timedelta

from bible5 import bible
from conf import read_config
from methods import choice, calc_font, now, insert_line_breaks, get_playing_text

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s',
    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S', handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'infinite.log')),
        logging.StreamHandler()
    ]
)


class Stream:
    def __init__(self, max=3):
        self.num = 1
        self.max = max
        self.conf = read_config()
        self.playlist = self.create_pls()
        self.audio_files = glob.glob(self.conf.audio_path)
        self.audio = None
        self.text = None
        self.creating = None
        self.stream_url = f"{self.conf.stream_url}{'' if self.conf.stream_url.endswith('/') else '/'}{self.conf.stream_key}"

    def create_pls(self):
        in_file = os.path.join(self.conf.tmp_path, self.conf._in_file)
        with open(in_file, 'w') as f:
            for num in range(self.max):
                f.write(f'file {num:07d}.mp4\n')
        return ffmpeg.input(in_file, safe=0, format='concat', re=None, stream_loop=-1)

    def set_next(self):
        self.next = datetime.now() + timedelta(seconds=self.duration)
        self.num += 1
        if self.num > self.max:
            self.num = 1
        return self.num

    def render(self):
        audio = choice(self.audio_files, self.audio)
        text = choice(bible, self.text)
        font_size, max_length = calc_font(text)
        bible_text = insert_line_breaks(text, max_length=max_length)
        pray_y = int(500 - len(text.split('\n')) * (40 / 2 + 4)) if self.conf.pray_top is None else self.conf.pray_top
        playing_text, self.duration = get_playing_text(audio)
        ff_audio = ffmpeg.input(audio, vn=None)
        ff_video_src = ffmpeg.input(self.conf.video_file, re=None, stream_loop=-1, **self.conf._ffmpeg.video_params)
        ff_video = ff_video_src.drawtext(
            bible_text, y=pray_y, fontcolor='white', fontsize=font_size, x="(w-text_w)/2", shadowx=2, shadowy=2
        ).drawtext(
            playing_text, y=1020, fontcolor='white', fontsize=32, x=600
        )

        out_file = os.path.join(self.conf.tmp_path, f'{self.num:07d}.mp4')

        ff = ffmpeg.output(ff_video, ff_audio, out_file, **self.conf._ffmpeg.create_params).overwrite_output()
        # if creating:
        #     creating.wait()
        logging.info(f'start rendering {audio} ({playing_text}) {self.duration}')
        ff.run(cmd=self.conf.stream_cmd or 'ffmpeg', quiet=True)

    def run_stream(self):
        logging.info('run_stream')
        stream = ffmpeg.output(self.playlist, self.stream_url, **self.conf._ffmpeg.stream_params).overwrite_output()
        stream.run_async(cmd=self.conf.stream_cmd or 'ffmpeg', quiet=True)

    def wait_stream(self):
        next = datetime.now() - self.next
        logging.info(f'wait_stream {next}')
        sleep(next.total_seconds())

    def main(self):
        logging.info('proceed_stream')
        self.render()
        self.run_stream()
        while True:
            self.set_next()
            self.render()
            self.wait_stream()


if __name__ == '__main__':
    Stream().main()



def proceed_stream():
    logging.info('proceed_stream')
    conf = read_config()

    for f in glob.glob(os.path.join(conf.tmp_path, '*')):
        os.remove(f)
    in_file = os.path.join(conf.tmp_path, conf._in_file)

    with open(in_file, 'w') as f:
        for num in range(3):
            f.write(f'file {num:07d}.mp4')

    joined = ffmpeg.input(in_file, safe=0, format='concat', re=None, stream_loop=-1)

    stream_url = f"{conf.stream_url}{'' if conf.stream_url.endswith('/') else '/'}{conf.stream_key}"
    creating = None
    text = audio = None
    num = 1
    audio_files = glob.glob(conf.audio_path)

    while True:
        # TODO: 1 create, 2 play, 3 delete
        audio = choice(audio_files, audio)
        text = choice(bible, text)
        font_size, max_length = calc_font(text)
        bible_text = insert_line_breaks(text, max_length=max_length)
        pray_y = int(500 - len(text.split('\n')) * (40 / 2 + 4)) if conf.pray_top is None else conf.pray_top
        playing_text, duration = get_playing_text(audio)
        ff_audio = ffmpeg.input(audio, vn=None)
        ff_video_src = ffmpeg.input(conf.video_file, re=None, stream_loop=-1, **conf._ffmpeg.video_params)
        ff_video = ff_video_src.drawtext(
            bible_text, y=pray_y, fontcolor='white', fontsize=font_size, x="(w-text_w)/2", shadowx=2, shadowy=2
        ).drawtext(
            playing_text, y=1020, fontcolor='white', fontsize=32, x=600
        )

        out_file = os.path.join(conf.tmp_path, f'{num:07d}.mp4')

        ff = ffmpeg.output(ff_video, ff_audio, out_file, **conf._ffmpeg.create_params).overwrite_output()

        if creating:
            creating.wait()
        print(f'{now()} start rendering {audio} ({playing_text}) {duration}')
        creating = ff.run_async(cmd=conf.stream_cmd or 'ffmpeg', quiet=True)

        with open(in_file, 'a') as file:
            print(f'file {out_file}', file=file)
        if num == 2:
            stream = ffmpeg.output(joined, stream_url, **conf._ffmpeg.stream_params).overwrite_output()
            print(f'{now()} start stream')
            stream.run_async(cmd=conf.stream_cmd or 'ffmpeg', quiet=True)

        num += 1
