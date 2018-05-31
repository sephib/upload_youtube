import os
import glob
from pydub import AudioSegment
from pathlib import Path

audio_dir = 'data'  # Path where the videos are located
extension_list = ('*.mp4', '*.flv')

def main():
    audio_wma_files =Path(audio_dir).rglob('*.WMA')
    for audio_file in audio_wma_files:





        for video in glob.glob(extension):
            mp3_filename = os.path.splitext(os.path.basename(video))[0] + '.mp3'
            AudioSegment.from_file(video).export(mp3_filename, format='mp3')


if __name__ == '__main__':
    main()
