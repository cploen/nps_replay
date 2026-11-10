"""Checks for exact coefficient preservation and effective 45-run assignments."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from prepare_coeff2018_zero_offsets import CONFIG, MATRIX, RUNS, prepare
from submit_elastic_swif import CALIBRATION, configuration, run_numbers

REPO = Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def test_existing_nov05_assignments_unchanged(self):
        runs = run_numbers(REPO/'jobs/sieve_oct29_runs.txt')
        actual = configuration(REPO,runs,CALIBRATION)
        self.assertEqual(len(actual),41)
        self.assertEqual(set(actual.values()),{'5p878','6p117','6p667'})

    def test_four_settings_share_updated_matrix_and_preserve_all_other_terms(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)/'replay'
            files = ['DBASE/NPS/standard_coin.database','DBASE/NPS/standard_coin.kinematics','jobs/sieve_oct29_runs.txt']
            files += [f'PARAM/HMS/GEN/{name}_{setting}.param' for name in ('hmsflags','hcana') for setting in ('5p878','6p117','6p667')]
            files += ['PARAM/HMS/GEN/hcana_fa22.param','PARAM/HMS/GEN/hmsflags_opt2018.param']
            for name in files:
                target = repo/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(REPO/name,target)
            (repo/'DATFILES').mkdir()
            result = Path(temporary)/'beam'
            (result/'matrices').mkdir(parents=True)
            source = result/'matrices/beam.dat'
            source.write_text('! synthetic fixture\n ---------------------\n 0.003 -0.0005 0.0009 0.001 00000\n 1 2 3 4 10000\n 5 6 7 8 00001\n ---------------------\n')
            manifest = result/'manifest.json'
            manifest.write_text(json.dumps(dict(schema='beam_v1',status='complete',outputs={'matrices/beam.dat':hashlib.sha256(source.read_bytes()).hexdigest()})))
            with contextlib.redirect_stdout(io.StringIO()):prepare(repo,source,manifest)
            text = (repo/MATRIX).read_text()
            self.assertIn(' 1 2 3 4 10000\n',text)
            self.assertIn(' 5 6 7 8 00001\n',text)
            self.assertNotIn(' 00000\n',text)
            cfg = json.loads((repo/CONFIG/'fit_manifest.json').read_text())
            expected = {run:setting for setting,runs in RUNS.items() for run in runs}
            self.assertEqual(configuration(repo,sorted(expected),cfg),expected)
            self.assertEqual(len(expected),45)
            self.assertEqual({v['matrix'] for v in cfg['settings'].values()},{MATRIX})
            self.assertEqual(len({v['matrix_sha256'] for v in cfg['settings'].values()}),1)
            self.assertEqual((repo/'DBASE/NPS/standard_coin.kinematics').read_bytes(),(REPO/'DBASE/NPS/standard_coin.kinematics').read_bytes())
            flags = repo/cfg['settings']['4p637']['flags']
            flags.write_text(flags.read_text().replace('hphi_offset = 0.0','hphi_offset = 0.001'))
            cfg['settings']['4p637']['flags_sha256'] = hashlib.sha256(flags.read_bytes()).hexdigest()
            cfg['settings']['4p637']['offsets']['hphi_offset'] = .001
            with self.assertRaisesRegex(ValueError,'Zero-offset test'):
                configuration(repo,[2184],cfg)


if __name__ == '__main__':
    unittest.main()
