import os
import glob
from pydub import AudioSegment
from pathlib import Path
import logging as lg
from logging.config import dictConfig

audio_dir = 'data'  # Path where the videos are located
extension_list = ('*.mp4', '*.flv')


logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': lg.DEBUG}
        },
    root = {
        'handlers': ['h'],
        'level': lg.DEBUG,
        },
)

dictConfig(logging_config)



def main():
    # clean bad files
    # TODO Remove files starting with '.' or '_'

    for file in Path(audio_dir).rglob('.*'):
        file.unlink()
        logger.debug(f'removed file: {file}')

    audio_wma_files =Path(audio_dir).rglob('*.WMA')
    for audio_file in audio_wma_files:
        new_file = audio_file.parent / f'{audio_file.stem}.mp3'
        if not new_file.exists():
            logger.debug(f'try to convert {audio_file}')
            AudioSegment.from_file(audio_file).export(new_file, format='mp3')
            logger.debug(f'convert {audio_file} to {new_file}')

    # Get list of relevent files
    ffjpg = sorted([f for f in p.iterdir() if (f.suffix in ['.jpg']) ])
    ffjpg[-1], ffjpg[-2] = ffjpg[-2], ffjpg[-1]  #switch mavtir and haftara
    ffmp3 = sorted([f for f in p.iterdir() if (f.suffix in ['.mp3']) ])

    #create pairs
    video_pair = [i for i in zip(ffjpg, ffmp3)]

        # for video in glob.glob(extension_list):
        #     mp3_filename = os.path.splitext(os.path.basename(video))[0] + '.mp3'
        #     AudioSegment.from_file(video).export(mp3_filename, format='mp3')


if __name__ == '__main__':
    logger = lg.getLogger(__name__)
    main()
    print('Done')
