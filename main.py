import os
import glob
from pydub import AudioSegment
from pathlib import Path
import logging as lg
from logging.config import dictConfig
import subprocess
import re

audio_dir = 'data'  # Path where the videos are located
extension_list = ('*.mp4', '*.flv')

logging_config = dict(
    version=1,
    formatters={
        'f': {'format':
                  '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
    },
    handlers={
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': lg.DEBUG}
    },
    root={
        'handlers': ['h'],
        'level': lg.DEBUG,
    },
)

dictConfig(logging_config)


def convert_audio_file(audio_file: Path, audio_format: str = 'mp3'):
    new_file = audio_file.parent / f'{audio_file.stem}.mp3'
    if not new_file.exists():
        logger.debug(f'try to convert {audio_file}')
        AudioSegment.from_file(audio_file).export(new_file, format=audio_format)
        logger.debug(f'convert {audio_file} to {new_file}')


def get_name_alya(alya_file_name:str)->str:
    aliya = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שביעי']
    dict_aliya = dict(zip(range(1,8), aliya))
    aliya_name = dict_aliya[int(re.findall('\d', alya_file_name.stem)[0])]
    if aliya_name:
        return aliya_name
    else:
        pass
        # TODO Haftar Maftir


def create_youtube_metadata(_image):
    meta_dict={}
    meta_dict['category'] = 'Music'
    #TODO get ALYA Name for mafit haftara
    aliya_name = get_name_alya(_image.parts[-1])
    meta_dict['title'] = f'נוסח אשכנז -  {aliya_name} - פרשת {_image.parts[-2]}'
    meta_dict['description'] = f'{_image.parts[-1]} קריאה בתורה לפרשת'
    #    meta_dict['description-file'] = None
    meta_dict['tags'] = f'קריאה בתורה, {_image.parts[-2]}'
    meta_dict['privacy'] = 'public'
    #   meta_dict['publish-at'] = None
    meta_dict['recording-date'] = '2017'
    meta_dict['default-language'] = 'he'
    meta_dict['default-audio-language'] = 'he'
    meta_dict['thumbnail'] = _image
    meta_dict['playlist'] = f'פרשת {_image.parts[-2]}'
    meta_dict['client-secrets'] = 'youtube-upload-master/client_id.json'
    # meta_dict['credentials-file'] = None

    return meta_dict


def main():
    # clean bad files
    # TODO Remove files starting with '.' or '_'

    for file in Path(audio_dir).rglob('.*'):
        file.unlink()
        logger.debug(f'removed file: {file}')

    #convert audio files
    audio_wma_files = Path(audio_dir).rglob('*.WMA')
    for audio_file in audio_wma_files:
        convert_audio_file(audio_file, audio_format='mp3')

    # Get list of relevent files
    l = []
    for i in Path(audio_dir).rglob('*.jpg'):
        l.append(i)
        if len(l) > 1:
            if l[-2].parent != l[-1].parent:
                j = l.pop()
                print(f'process: {len(l)}')
                ffjpg = sorted(l)
                ffjpg[-1], ffjpg[-2] = ffjpg[-2], ffjpg[-1]  # switch mavtir and haftara
                ffmp3 = sorted([f for f in l[0].parent.rglob('*.mp3')])
                # create pairs
                if len(ffjpg) != len(ffmp3):
                    print(f'PROBLEM: number of files not equal in {l[0].parent}')
                    continue
                video_pair = [i for i in zip(ffjpg, ffmp3)]
                for _image, _video in video_pair:
                    meta_dict = create_youtube_metadata(_image)
                    # Run subprocess youtube_upload with
                    upload_exe = r'C:\Users\sephi\github\upload_youtube\youtube-upload-master\bin\youtube-upload'
                    args = ''.join([f'\'--{k}\', \'{v}\',' for k,v in meta_dict.items()])
                    subprocess.run([upload_exe, args, _video])
                    logger.debug(f'completed to load {_video}')


                l = []
                l.append(j)
            else:
                pass




    # for video in glob.glob(extension_list):
    #     mp3_filename = os.path.splitext(os.path.basename(video))[0] + '.mp3'
    #     AudioSegment.from_file(video).export(mp3_filename, format='mp3')


if __name__ == '__main__':
    logger = lg.getLogger(__name__)
    main()
    print('Done')
