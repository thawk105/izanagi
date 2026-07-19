# -*- coding: utf-8 -*-
"""tools/check_workflow_models.py の回帰 + positive control。

lint が恒真 (何を食わせても違反ゼロ) に化けていないことを、NG を必ず出す
positive control で固定する (規律3 の positive control、F9 と同型の防御)。
pytest でも 素の `python3 orchestrator/tests/test_check_workflow_models.py` でも走る。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.join(_REPO, "tools"))

import check_workflow_models as cwm  # noqa: E402


def _kinds(text):
    return [f.kind for f in cwm.scan_script(text)]


def test_model_present_is_clean():
    assert _kinds("await agent('do x', {model: 'sonnet', effort: 'low'})") == []


def test_quoted_key_and_agenttype_are_clean():
    assert _kinds("agent('x', {'model': 'opus', effort: 'low'})") == []
    assert _kinds("agent('x', {agentType: 'verifier', phase: 'V'})") == []


def test_no_opts_is_ng():
    assert _kinds("const r = await agent('x')") == ["ng"]


def test_opts_without_model_is_ng():
    assert _kinds("agent('x', {label: 'a', effort: 'high'})") == ["ng"]


def test_positive_control_cli_exits_nonzero():
    # 恒真ゲート対策: NG 入りファイルで CLI が exit 1 になることを subprocess で固定
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("agent('x', {label: 'a'})\n")
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(_REPO, "tools", "check_workflow_models.py"), path],
            capture_output=True, text=True,
        )
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "NG=1" in proc.stdout
    finally:
        os.unlink(path)


def test_clean_cli_exits_zero():
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("agent('x', {model: 'haiku', effort: 'low'})\n")
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(_REPO, "tools", "check_workflow_models.py"), path],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "NG=0 WARN=0" in proc.stdout
    finally:
        os.unlink(path)


def test_agent_in_strings_and_comments_not_counted():
    text = "\n".join([
        "const p = `please call agent( carefully`;",
        "const q = 'agent(decoy)';",
        "// agent('commented out')",
        "/* agent('block comment') */",
        "agent(p, {model: 'opus', effort: 'low'})",
    ])
    assert _kinds(text) == []


def test_template_interpolation_tracked():
    text = "agent(`verify ${JSON.stringify(flag, null, 2)} end`, {model: 'opus', effort: 'high'})"
    assert _kinds(text) == []
    # ${} の中の閉じ括弧・カンマが引数分割を壊さないこと (NG 側も正しく出る)
    text_ng = "agent(`verify ${fmt(a, b)} end`, {label: 'x'})"
    assert _kinds(text_ng) == ["ng"]


def test_spread_and_nonliteral_opts_are_warn_not_ng():
    assert _kinds("agent('x', {...base, label: 'a'})") == ["warn"]
    assert _kinds("agent('x', opts)") == ["warn"]


def test_regex_literal_content_masked():
    text = "const hit = xs.filter(s => /agent\\(/.test(s));\nagent('x', {model: 'haiku', effort: 'low'})"
    assert _kinds(text) == []


def test_lookalike_names_not_counted():
    assert _kinds("subagent('x'); pipeline.agent('y'); reagent('z')") == []


def test_multiline_real_workflow_shape():
    text = "\n".join([
        "export const meta = { name: 'x', description: 'y' }",
        "const rs = await pipeline(items,",
        "  d => agent(d.prompt, {label: `find:${d.key}`, phase: 'Find', model: 'opus', effort: 'high'}),",
        "  r => parallel(r.list.map(f => () =>",
        "    agent(`Verify: ${f.title}`, {label: `v:${f.id}`, schema: S})",
        "      .then(v => ({...f, v})))))",
    ])
    kinds = _kinds(text)
    assert kinds == ["ng"], kinds  # 2 呼び中、verify 側だけ model 欠落


def test_postfix_division_not_masked_as_regex():
    # 敵対レビュー finding: i++ / n の / が regex 誤認され以降の agent() が消えていた
    assert _kinds("const b = items[i++ / size]; agent('x', {label: 1})") == ["ng"]
    assert _kinds("let z = i-- / n; agent('x', {model: 'opus', effort: 'low'})") == []
    assert _kinds("agent('x', {n: i++ / 2, model: 'sonnet', effort: 'low'})") == []


def test_keyword_named_property_division_not_regex():
    # obj.in / n の in はキーワードでなくプロパティ名
    assert _kinds("let z = obj.in / n; agent('x', {label: 1})") == ["ng"]
    # 本物のキーワード前置は regex のまま (return /re/)
    assert _kinds("function f() { return /agent\\(/.test(s); }\nagent('x', {model: 'haiku', effort: 'low'})") == []


def test_computed_key_is_warn_not_ng():
    # 敵対レビュー finding: computed key は spread と同じく静的判定不能 → fail-open
    assert _kinds("agent('x', {[MODEL_KEY]: 'sonnet'})") == ["warn"]
    assert _kinds("agent('x', {['model']: 'v'})") == ["warn"]


def test_string_literal_then_division_not_regex():
    # codex 監査 finding: "12" / 3 の / が regex 誤認され以降の agent() が消えていた
    assert _kinds('const n = "12" / 3; agent("x", {label: "v"})') == ["ng"]
    assert _kinds("const s = tpl(`a`) / 2; agent('x', {model: 'opus', effort: 'low'})") == []


def test_private_field_division_not_regex():
    text = "\n".join([
        "class C {",
        "  #in = 4;",
        '  run() { const z = this.#in / 2; agent("x", {label: 1}); }',
        "}",
    ])
    assert _kinds(text) == ["ng"]


def test_interpolation_toplevel_comma_not_arg_separator():
    # ${} 内の深度 0 カンマ (comma operator) は引数区切りではない
    assert _kinds("agent(`${left, right}`, {model: 'sonnet', effort: 'low'})") == []


def test_function_declaration_not_counted_optional_call_counted():
    assert _kinds("function agent(prompt, opts) { return null; }") == []
    assert _kinds('agent?.("x")') == ["ng"]


def test_parenthesized_opts_unwrapped():
    assert _kinds('agent("x", ({model: "sonnet", effort: "low"}))') == []
    assert _kinds('agent("x", (opts))') == ["warn"]


def test_finding_line_and_reason_pinned():
    # 診断の行番号・分類・本文を固定 (kinds だけだと位置の取り違えに気づけない)
    (f,) = cwm.scan_script("export const meta = {}\n\nagent('x')")
    assert (f.kind, f.line) == ("ng", 3)
    assert "opts が無い" in f.message


def test_effort_omission_is_warn():
    # codex 監査 finding: model 明示でも effort 省略はセッション effort (xhigh 等) を継承
    assert _kinds("agent('x', {model: 'sonnet'})") == ["warn"]
    # named role (agentType) は frontmatter 両ピンで解決されるため effort 不要
    assert _kinds("agent('x', {agentType: 'verifier'})") == []


def _run_cli(args):
    return subprocess.run(
        [sys.executable, os.path.join(_REPO, "tools", "check_workflow_models.py"), *args],
        capture_output=True, text=True,
    )


def test_warn_only_cli_exits_zero_fail_open():
    # 中核契約: WARN は exit code に影響しない (偽陽性の害を出さない fail-open)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("agent('x', {...base})\n")
        path = f.name
    try:
        proc = _run_cli([path])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "NG=0 WARN=1" in proc.stdout
    finally:
        os.unlink(path)


def test_dir_recursion_and_aggregation():
    # --dir の再帰走査と複数ファイル集計 (NG 累積 + WARN 混在で exit 1)
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "sub"))
        with open(os.path.join(d, "a.js"), "w") as f:
            f.write("agent('x')\nagent('y', {label: 1})\n")
        with open(os.path.join(d, "sub", "b.js"), "w") as f:
            f.write("agent('z', opts)\n")
        proc = _run_cli(["--dir", d])
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "NG=2 WARN=1 (files=2)" in proc.stdout


def test_unreadable_file_is_warn_and_fail_open():
    # 読めないファイルは WARN 扱いで exit code に影響しない
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write("agent('x', {model: 'haiku', effort: 'low'})\n")
        path = f.name
    try:
        proc = _run_cli([path, path + ".does-not-exist.js"])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "読めない" in proc.stderr
        assert "NG=0 WARN=1 (files=2)" in proc.stdout
    finally:
        os.unlink(path)


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                fails += 1
                print(f"FAIL {name}: {exc}")
    raise SystemExit(1 if fails else 0)
