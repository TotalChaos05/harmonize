import pathlib
import shutil
import subprocess
import unittest

from tests import helpers

TMP = pathlib.Path(__file__).parent.joinpath('tmp')


class TestApp(unittest.TestCase):

    def setUp(self):
        try:
            shutil.rmtree(TMP)
        except FileNotFoundError:
            pass
        TMP.mkdir()

    def test_transcodes_flac_to_mp3(self):
        source_dir = TMP / 'source'
        source_dir.mkdir()
        target_dir = TMP / 'target'
        audio_file = source_dir / 'audio.flac'
        helpers.ffmpeg.generate_silence(1, audio_file)

        proc = subprocess.run(
            ['harmonize', str(source_dir), str(target_dir)],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True)
        self.assertEqual(proc.stdout, b'')
        self.assertEqual(
            proc.stderr.decode(),
            (f'Scanning "{source_dir}"\n'
             'Scanned 1 items\n'
             f'Transcoding {audio_file}\n'
             'Processing complete\n'))

        metadata = helpers.ffprobe.get_metadata(target_dir / 'audio.mp3')

        self.assertEqual('mp3', metadata['format']['format_name'])
        self.assertEqual(1, len(metadata['streams']))
        self.assertEqual('mp3', metadata['streams'][0]['codec_name'])
        # mp3 will not be exact duration as input
        self.assertTrue(1 <= float(metadata['format']['duration']) <= 1.1)

    def test_transcodes_flac_to_opus(self):
        source_dir = TMP / 'source'
        source_dir.mkdir()
        target_dir = TMP / 'target'
        helpers.ffmpeg.generate_silence(1, source_dir / 'audio.flac')

        proc = subprocess.run(
            ['harmonize', '--codec', 'opus', str(source_dir), str(target_dir)],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True)
        self.assertEqual(proc.stdout, b'')
        self.assertEqual(
            proc.stderr.decode(),
            (f'Scanning "{source_dir}"\n'
             'Scanned 1 items\n'
             f'Transcoding {source_dir}/audio.flac\n'
             'Processing complete\n'))

        metadata = helpers.ffprobe.get_metadata(target_dir / 'audio.opus')

        self.assertEqual('ogg', metadata['format']['format_name'])
        self.assertEqual(1, len(metadata['streams']))
        self.assertEqual('opus', metadata['streams'][0]['codec_name'])
        # mp3 will not be exact duration as input
        self.assertTrue(1 <= float(metadata['format']['duration']) <= 1.1)

    def test_transcodes_multiple(self):
        source_dir = TMP / 'source'
        source_dir.mkdir()
        target_dir = TMP / 'target'

        for duration in range(1, 4):
            helpers.ffmpeg.generate_silence(
                duration, source_dir / f'{duration}.flac')

        proc = subprocess.run(
            ['harmonize', str(source_dir), str(target_dir)],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True)
        self.assertEqual(proc.stdout, b'')
        self.assertEqual(
            proc.stderr.decode(),
            (f'Scanning "{source_dir}"\n'
             'Scanned 3 items\n'
             f'Transcoding {source_dir}/1.flac\n'
             f'Transcoding {source_dir}/2.flac\n'
             f'Transcoding {source_dir}/3.flac\n'
             'Processing complete\n'))

        for duration in range(1, 4):
            metadata = helpers.ffprobe.get_metadata(
                target_dir / f'{duration}.mp3')

            self.assertEqual('mp3', metadata['format']['format_name'])
            self.assertEqual(1, len(metadata['streams']))
            self.assertEqual('mp3', metadata['streams'][0]['codec_name'])
            # mp3 will not be exact duration as input
            self.assertTrue(duration <= float(metadata['format']['duration']) <= duration + 0.1)  # noqa: E501
