"""Meaningful installer safety checks, isolated from the real user's configuration."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('knowledge_install', Path(__file__).with_name('install.py'))
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'codex'
        self.skills = self.root / 'agents/skills'

    def install(self, **kwargs):
        return installer.install(self.home, self.skills, **kwargs)

    def test_install_and_repeat_are_idempotent(self):
        first = self.install()
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        second = self.install()
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertTrue(first['changed_files'])
        self.assertEqual(second['changed_files'], [])
        self.assertEqual(before, after)

    def test_existing_global_and_unrelated_skill_preserved_and_backed_up(self):
        self.home.mkdir();original=b'# Existing guidance\r\nKeep custom convention.\r\n'
        target=self.home/'AGENTS.md';target.write_bytes(original)
        unrelated=self.skills/'other/SKILL.md';unrelated.parent.mkdir(parents=True);unrelated.write_text('other')
        r=self.install()
        self.assertTrue(target.read_bytes().startswith(original))
        self.assertEqual(Path(r['backups'][0]).read_bytes(),original)
        self.assertEqual(unrelated.read_text(),'other')
        self.assertEqual(len(self.install()['backups']),0)

    def test_conflicting_skill_prevents_global_write(self):
        path=self.skills/installer.NAME/'SKILL.md';path.parent.mkdir(parents=True);path.write_text('User owned')
        with self.assertRaisesRegex(ValueError,'conflicts'):self.install()
        self.assertFalse((self.home/'AGENTS.md').exists())
        self.assertEqual(path.read_text(),'User owned')

    def test_locally_edited_installed_skill_is_not_overwritten(self):
        self.install();p=self.skills/installer.NAME/'SKILL.md';p.write_text(p.read_text()+'\nLocal edit\n')
        with self.assertRaisesRegex(ValueError,'locally edited'):self.install()
        self.assertTrue(p.read_text().endswith('Local edit\n'))

    def test_override_and_duplicate_markers_refused(self):
        self.home.mkdir();p=self.home/'AGENTS.override.md';p.write_text('Authorized override')
        with self.assertRaisesRegex(ValueError,'precedence'):self.install()
        p.unlink();(self.home/'AGENTS.md').write_text((installer.START+'\n'+installer.END+'\n')*2)
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.install()

    def test_changed_managed_block_requires_review(self):
        self.install();p=self.home/'AGENTS.md';p.write_text(p.read_text().replace('Evidence-driven engineering','Existing authorized policy'))
        with self.assertRaisesRegex(ValueError,'review'):self.install()

    def test_unrecognized_metadata_preserved_before_any_write(self):
        owner=self.skills/installer.NAME/'.installation.json';owner.parent.mkdir(parents=True);owner.write_text('{"user": "owned"}')
        with self.assertRaisesRegex(ValueError,'Unrecognized'):self.install()
        self.assertFalse((self.home/'AGENTS.md').exists())
        self.assertEqual(owner.read_text(),'{"user": "owned"}')

    def test_symlink_metadata_is_not_read_or_overwritten(self):
        target=self.root/'external.json';target.write_text('{"private": true}')
        owner=self.skills/installer.NAME/'.installation.json';owner.parent.mkdir(parents=True);owner.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'symlink'):self.install()
        self.assertFalse((self.home/'AGENTS.md').exists())
        self.assertEqual(target.read_text(),'{"private": true}')

    def test_dry_run_has_no_filesystem_side_effects(self):
        result=self.install(dry_run=True)
        self.assertEqual(result['status'],'DRY_RUN')
        self.assertEqual(list(self.root.iterdir()),[])

    def test_symlink_destination_refused(self):
        target=self.root/'external';target.mkdir();self.home.symlink_to(target,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.install()
        self.assertFalse((target/'AGENTS.md').exists())


if __name__=='__main__':unittest.main()
