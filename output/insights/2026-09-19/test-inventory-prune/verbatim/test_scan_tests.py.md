# scanner 自己検査 逐語 — t_inv_scanner/test_scan_tests.py

sha256: 19d696626911629ac7a9cd5db8e1efe22949918bb3f6d74a3cbe0007a0716878

```python
"""Direct self-check; all temporary fixtures stay under the owned directory."""
import ast
import json
from pathlib import Path
from t_inv_scanner.scan_tests import fingerprint, markdown, scan


def test_scan():
    root = Path(__file__).resolve().parent / '.selfcheck_tmp'
    root.mkdir()  # Refuse to touch a pre-existing directory.
    def write(file, text):
        p = root / file
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    try:
        write('docs/decisions.md', '## D2. D1 を撤回\n## D3. maintained\n')
        write('docs/phase3.md', '## 見送り台帳\n- ~~T-7 / B-8~~\n## 次\n~~T-9~~\n')
        write('docs/existing.md', '### Existing\n')
        write('tools/cli.py', "FLAGS = ['--present']\n")
        write('orchestrator/prod.py', 'CONST = 7\ndef run(): pass\n')
        write('orchestrator/tests/conftest.py', "H = frozenset({'test_sample.py::test_a'})\n")
        write('orchestrator/tests/growth_test_holds.py', "H = ['test_sample.py::test_c']\n")
        write('tools/update_acceptance_duration_ledger.py', "_ADD_ONLY_FROZEN_SUITE_PREFIXES = ('orchestrator/tests/test_frozen.py::',)\n_ADD_ONLY_FROZEN_REMOVED_NODEIDS = frozenset({'test_sample.py::test_derived'})\n")
        write('orchestrator/tests/test_sample.py', '''import pytest
import orchestrator.prod as prod
from pathlib import Path
from orchestrator.prod import run as launch
from ..prod import CONST as relative_const
def test_a():
    """docs/handoff/ explanatory prose\n    with another line that is not a path"""
    import orchestrator.absent
    import importlib
    importlib.import_module("tools.absent")
    pytest.importorskip("hooks.absent")
    argv = ["tools/cli.py", "--absent", "--present", "tools/missing.py"]
    text = "### Missing"
@pytest.mark.parametrize("x", [1, pytest.param(1, id="other"), unknown])
def test_b(x):
    """different docstring"""
    assert x == 1
def test_copy(x):
    """another docstring"""
    assert x == 1
@pytest.mark.parametrize("x", [2])
def test_different_decorator(x):
    assert x == 1
def test_synthetic_arg(tmp_path):
    argv = ["tools/missing.py", "tools/cli.py", "--absent"]
    text = "### Missing"
def test_synthetic_write():
    Path("tools/missing.py").write_text("x")
def test_synthetic_raises():
    with pytest.raises(ValueError):
        open("tools/missing.py")
def test_synthetic_match():
    with pytest.raises(ValueError, match="tools/missing.py"):
        fail()
def test_synthetic_message():
    assert "tools/missing.py" in message
def test_mixed_message():
    assert "tools/missing.py" in message
    open("tools/missing.py")
def test_targets():
    launch()
    assert relative_const == 7
    prod.run()
def test_c():
    # D1 T-7 B-8 T-9 F29
    assert True
def test_docs():
    assert Path("docs/existing.md").read_text() == "text"
def test_derived():
    assert prod.CONST == 7
def test_not_pin():
    assert prod.run() == Path("docs/existing.md").read_text()
def test_skip():
    """doc"""
    pytest.skip("why")
@pytest.mark.skip(reason="why")
def test_mark_skip():
    pass
@pytest.mark.xfail(False)
def test_not_skip():
    pass
class TestGroup:
    async def test_async(self):
        assert 12
''')
        write('orchestrator/tests/test_peer.py', '''PIN = "test_sample.py::TestGroup::test_async[param]"
def test_cross_file(x):
    assert x == 1
''')
        write('orchestrator/tests/test_frozen.py', 'def test_frozen():\n    assert 45\n')
        write('orchestrator/tests/test_real_repo_serialization.py', 'N_GOLDEN = {"test_sample.py::test_docs"}\n')
        write('orchestrator/tests/test_excluded.py', 'def test_excluded():\n    assert False\n')
        write('orchestrator/tests/test_broken.py', 'def broken(\n')
        prefix = 'orchestrator/tests/test_sample.py::'
        write('collect.txt', prefix + 'test_b[one]\n' + prefix + 'test_b[two]\n' + prefix + 'TestGroup::test_async[param]\n')
        write('exclude.txt', 'test_excluded.py\n')
        write('orchestrator/tests/acceptance_duration_ledger.json', json.dumps({'duration_seconds_by_nodeid': {prefix + 'test_b[one]': 2.5}}))
        data = scan(root, root / 'collect.txt', root / 'exclude.txt')
        records = {r['qualname']: r for r in data['records']}
        kinds = lambda name, cat: {e['kind'] for e in records[name]['evidence'][cat]}
        assert kinds('test_a', 'A') == {'path-missing', 'module-missing', 'flag-missing', 'docs-heading-missing'}
        assert not any(e.get('literal') == '--present' for e in records['test_a']['evidence']['A'])
        assert any(e['kind'] == 'non-path-shaped-literal' for e in records['test_a']['unresolved'])
        assert kinds('test_b', 'B') == {'duplicate-parametrize-row'}
        assert kinds('test_copy', 'B') == {'identical-body-and-decorators'}
        assert not records['test_different_decorator']['evidence']['B']
        assert records['test_different_decorator']['notes'][0]['kind'] == 'identical-body-only'
        for name in ('test_synthetic_arg', 'test_synthetic_write', 'test_synthetic_raises', 'test_synthetic_match', 'test_synthetic_message'):
            assert not records[name]['evidence']['A'], name
            assert records[name]['suppressed'], name
            assert {e['reason'] for e in records[name]['suppressed']} == {'synthetic-fixture'}
        assert {e['kind'] for e in records['test_synthetic_arg']['suppressed']} == {'path-missing', 'flag-missing', 'docs-heading-missing'}
        assert kinds('test_mixed_message', 'A') == {'path-missing'}
        assert records['test_targets']['production_targets'] == ['orchestrator/prod.py']
        assert records['test_not_pin']['production_targets'] == ['orchestrator/prod.py']
        assert records['test_a']['production_targets'] == []
        assert records['test_b']['nodeid_count'] == 2
        assert records['test_b']['duration_seconds'] == 2.5
        assert records['test_b']['missing_duration_nodeids'] == 1
        assert any('test_peer.py::test_cross_file' in p for e in records['test_b']['notes'] for p in e.get('peers', []))
        assert {e['reference'] for e in records['test_c']['evidence']['C']} == {'D1', 'T-7', 'B-8'}
        assert records['test_c']['evidence']['C'][0]['grounds'][0]['line'] > 0
        assert kinds('test_docs', 'D') == {'docs-pin'}
        assert kinds('test_derived', 'D') == {'derived-value-pin'}
        assert not kinds('test_not_pin', 'D')
        assert records['test_skip']['always_skipped'] and records['test_mark_skip']['always_skipped']
        assert not records['test_not_skip']['always_skipped']
        for name in ('test_a', 'test_c', 'test_docs', 'test_derived', 'test_frozen', 'TestGroup::test_async'):
            assert records[name]['protected'], name
        assert records['TestGroup::test_async']['referenced_by'][0]['file'].endswith('test_peer.py')
        assert 'test_excluded' not in records
        s = data['summary']
        assert s['excluded_files'] == 1 and s['excluded_file_lines'] == 2
        assert s['totals']['nodeids'] == 3 and s['totals']['duration_seconds'] == 2.5
        assert s['unevaluable_parametrize_rows'] == 1
        assert len(s['errors']) == 1 and s['errors'][0]['file'].endswith('test_broken.py')
        assert not s['unmatched_collect_functions']
        md = markdown(data)
        for heading in ('B1 group', 'B2 重複 row 全件', 'C 全件', 'D pin先別', '上位30件'):
            assert heading in md
        assert s['suppressed_functions'] == 5
        assert sum(s['unresolved_by_kind'].values()) == s['unresolved_evidence_count']
        assert sum(s['suppressed_by_kind'].values()) == s['suppressed_evidence_count']
        assert fingerprint(ast.parse('def test_x(x):\n assert x').body[0]) != fingerprint(ast.parse('def test_y(y):\n assert x').body[0])
        print('self-check passed: A/B1/B2/C/D, protections, collection, ledger, errors, exclusions')
    finally:
        for p in sorted(root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            p.rmdir() if p.is_dir() else p.unlink()
        root.rmdir()
```
