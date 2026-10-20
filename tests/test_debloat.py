"""Testes do debloat com um adb falso: sem TV, sem rede, sem alterar nada real."""
import fnmatch, os, pathlib, shutil, subprocess, tempfile, unittest

repo = pathlib.Path(__file__).resolve().parents[1]
script = repo / 'tools/debloat/tvretro-debloat.sh'
fake = repo / 'tests/fake-adb.sh'
lists = repo / 'tools/debloat/lists'
TVRETRO_HOME = 'com.carlos.tvcasa/com.ansub.tvhome.MainActivity'
PKGS = [
    'com.android.systemui', 'com.android.settings', 'com.google.android.gms', 'com.android.vending',
    'com.google.android.inputmethod.latin', 'com.android.bluetooth', 'com.google.android.tv.inputplayer',
    'com.google.android.videos', 'com.google.android.play.games', 'com.google.android.youtube.tvmusic',
    'com.google.android.leanbacklauncher.recommendations', 'com.android.egg',
    'com.netflix.ninja', 'com.carlos.tvcasa', 'com.google.android.tvlauncher', 'com.mitv.tvhome',
    'com.fabricante.anuncios', 'com.fabricante.tv'
]

def entries(path):
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(line)
    return out

class Env:
    def __init__(self, home='com.google.android.tvlauncher/.Home', persistent=(), steal=()):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix='tvretro-debloat-'))
        self.state = self.tmp / 'state'; self.state.mkdir()
        self.work = self.tmp / 'work'; self.work.mkdir()
        bindir = self.tmp / 'bin'; bindir.mkdir()
        (bindir / 'adb').symlink_to(fake)
        (self.state / 'packages').write_text('\n'.join(PKGS) + '\n')
        (self.state / 'home').write_text(home + '\n')
        (self.state / 'persistent').write_text('\n'.join(persistent) + '\n')
        (self.state / 'steal').write_text('\n'.join(steal) + '\n')
        (self.state / 'home_extra').write_text('com.google.android.tvlauncher/.Home\n')
        (self.tmp / 'apps.txt').write_text('# meus apps\ncom.netflix.ninja\n')
        self.env = dict(os.environ, PATH=f'{bindir}:{os.environ["PATH"]}', FAKE_ADB_DIR=str(self.state),
                        APPS_FILE=str(self.tmp / 'apps.txt'), WAIT='0')
    def run(self, answers='', *args):
        return subprocess.run(['bash', str(script), '--tv', '192.0.2.10', *args], input=answers, text=True,
                              capture_output=True, env=self.env, cwd=self.work, timeout=60)
    def disabled(self):
        return set((self.state / 'disabled').read_text().split())
    def logs(self):
        return sorted(self.work.glob('tv-changes-*.txt'))
    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

class DebloatTests(unittest.TestCase):
    def setUp(self): self.e = Env(); self.addCleanup(self.e.close)

    def test_lists_are_consistent(self):
        protected = entries(lists / 'protegidos.txt') + entries(lists / 'launchers.txt')
        for line in entries(lists / 'candidatos.txt'):
            pkg, when, desc = line.split('|', 2)
            self.assertIn(when, ('-', 'home'), line)
            self.assertTrue(desc.strip(), line)
            for g in protected:
                self.assertFalse(fnmatch.fnmatchcase(pkg, g), f'{pkg} casa com protegido {g}')

    def test_dry_run_changes_nothing(self):
        r = self.e.run('', '--dry-run', '--launchers', '--tuning')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.e.disabled(), set())
        self.assertFalse(self.e.logs())
        self.assertIn('MODO SIMULAÇÃO', r.stdout)
        self.assertNotIn('pm disable-user', (self.e.state / 'calls.log').read_text())
        self.assertTrue(list(self.e.work.glob('tv-revisar-*.txt')))

    def test_eof_means_no_changes(self):
        r = self.e.run('')
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.e.disabled(), set())

    def test_only_confirmed_items_and_protected_never(self):
        pessoal = self.e.tmp / 'pessoal.txt'
        pessoal.write_text('com.android.systemui|-|NÃO deveria ser oferecido\ncom.netflix.ninja|-|app do usuário\n')
        self.e.env['PESSOAL_FILE'] = str(pessoal)
        # banner s; videos s; play.games n; tvmusic s; egg n
        r = self.e.run('s\ns\nn\ns\nn\n')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.e.disabled(), {'com.google.android.videos', 'com.google.android.youtube.tvmusic'})
        self.assertIn('(protegido, nunca será mexido) com.android.systemui', r.stdout)
        self.assertIn('(mantido: está na sua lista de apps) com.netflix.ninja', r.stdout)
        self.assertIn('(adiado: só depois do TvRetro ser a tela inicial) com.google.android.leanbacklauncher.recommendations', r.stdout)
        log = self.e.logs()[0].read_text()
        self.assertIn('OFF\tcom.google.android.videos', log)
        self.assertNotIn('play.games', log)
        self.assertIn('com.google.android.videos', (self.e.state / 'tvlist').read_text())
        self.assertTrue(list(self.e.work.glob('tv-pacotes-antes-*.txt')))

    def test_all_option_and_home_gated_items(self):
        e = Env(home=TVRETRO_HOME); self.addCleanup(e.close)
        r = e.run('s\na\n')  # banner s; primeiro 'a' = todos
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('com.google.android.leanbacklauncher.recommendations', e.disabled())
        for never in ('com.android.systemui', 'com.google.android.gms', 'com.android.vending', 'com.netflix.ninja',
                      'com.carlos.tvcasa', 'com.google.android.tvlauncher', 'com.mitv.tvhome', 'com.fabricante.tv'):
            self.assertNotIn(never, e.disabled())

    def test_undo_restores_everything(self):
        e = Env(home=TVRETRO_HOME); self.addCleanup(e.close)
        # banner s; candidatos: a (todos); animações s; protetor s
        r = e.run('s\na\ns\ns\n', '--tuning')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(e.disabled())
        self.assertEqual((e.state / 'set_global_window_animation_scale').read_text().strip(), '0')
        self.assertEqual((e.state / 'set_secure_screensaver_enabled').read_text().strip(), '0')
        r = e.run('', '--undo', str(e.logs()[0]))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(e.disabled(), set())
        self.assertEqual(list(e.state.glob('set_*')), [])

    def test_undo_from_tv_list_without_log(self):
        e = Env(); self.addCleanup(e.close)
        e.run('s\ns\nq\n')
        self.assertEqual(e.disabled(), {'com.google.android.videos'})
        r = e.run('', '--undo')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(e.disabled(), set())

    def test_launchers_wait_for_tvretro_home(self):
        r = self.e.run('s\n' + 'n\n' * 4, '--launchers')  # 4 candidatos disponíveis
        self.assertIn('Pulei: o TvRetro ainda não é a tela inicial padrão', r.stdout)
        self.assertEqual(self.e.disabled(), set())

    def test_launchers_skip_persistent(self):
        e = Env(home=TVRETRO_HOME, persistent=['com.mitv.tvhome']); self.addCleanup(e.close)
        # banner s; 5 candidatos n; tvlauncher n (mitv é PERSISTENT e nem é oferecido)
        r = e.run('s\n' + 'n\n' * 6, '--launchers')
        self.assertIn('Mantive com.mitv.tvhome: o sistema o mantém sempre em execução', r.stdout)
        self.assertEqual(e.disabled(), set())

    def test_launcher_disabled_when_home_stays(self):
        e = Env(home=TVRETRO_HOME); self.addCleanup(e.close)
        r = e.run('s\n' + 'n\n' * 5 + 's\nn\n', '--launchers')
        self.assertEqual(e.disabled(), {'com.google.android.tvlauncher'}, r.stdout + r.stderr)

    def test_launcher_safety_net_reenables_if_home_is_stolen(self):
        e = Env(home=TVRETRO_HOME, steal=['com.google.android.tvlauncher']); self.addCleanup(e.close)
        r = e.run('s\n' + 'n\n' * 5 + 's\nn\n', '--launchers')
        self.assertNotIn('com.google.android.tvlauncher', e.disabled(), r.stdout + r.stderr)
        self.assertIn('Reativando com.google.android.tvlauncher por segurança', r.stderr)
        self.assertEqual((e.state / 'home').read_text().strip(), TVRETRO_HOME)

    def test_report_lists_vendor_apps_but_not_protected(self):
        r = self.e.run('', '--dry-run')
        rep = list(self.e.work.glob('tv-revisar-*.txt'))[0].read_text()
        self.assertIn('com.fabricante.anuncios', rep)
        self.assertNotIn('com.android.systemui', rep)
        self.assertNotIn('com.netflix.ninja', rep)

if __name__ == '__main__':
    unittest.main(verbosity=2)
