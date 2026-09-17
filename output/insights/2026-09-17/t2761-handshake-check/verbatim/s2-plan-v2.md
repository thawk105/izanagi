## 変更面 (file:line 表)

行番号は変更前を指す。変更対象は test ファイルだけとする。

| file:line | 実装内容 |
|---|---|
| `orchestrator/tests/test_pegasus_dispatch_compute.py:12` | `import signal` の前に `import shlex` を追加 |
| 同 `:2579` 直前 | `repo_root` の parametrize を追加 |
| 同 `:2580` | signature に `repo_root` を追加 |
| 同 `:2583` | `_job_script` への引数を `repo_root=repo_root` に変更 |
| 同 `:2592` | 旧 release assert を、6 値の正規化・置換前提検査・release 候補行の不在検査へ置換 |
| 同 `:2590–2591,2593` | 既存 3 assert の文言と相対位置を維持。`while` は元の `script` を検査 |
| `tools/pegasus/dispatch_compute.py:866–872,887–892` | 読取・変異 anchor の参照のみ。恒久変更なし |

## 正規化の検索/置換表

以下の順序で test 内の `normalizations` に定義する。`tmp_path` は当該呼出しの `submission_dir` と同じ値である。

| 値 | 検索文字列の Python 式 | 置換文字列の Python 式 |
|---|---|---|
| RESULT | `"\nRESULT=" + shlex.quote(str(tmp_path / "result.json"))` | `"\nRESULT=<SUBMISSION>/result.json"` |
| PROBE | `"\nPROBE=" + shlex.quote(str(tmp_path / "interpreter_probe.py"))` | `"\nPROBE=<SUBMISSION>/interpreter_probe.py"` |
| REQUEST | `"\nREQUEST=" + shlex.quote(str(tmp_path / "request.json"))` | `"\nREQUEST=<SUBMISSION>/request.json"` |
| REPO | `"\nREPO=" + shlex.quote(str(repo_root))` | `"\nREPO=<REPO>"` |
| DISPATCHER | `"\nDISPATCHER=" + shlex.quote(str(repo_root / "tools" / "pegasus" / "dispatch_compute.py"))` | `"\nDISPATCHER=<REPO>/tools/pegasus/dispatch_compute.py"` |
| MARKER | `"\nMARKER=" + shlex.quote(str(tmp_path / DC._COMPUTE_MARKER_NAME))` | `"\nMARKER=<SUBMISSION>/" + DC._COMPUTE_MARKER_NAME` |

**改行＋代入名から始める P2 を採用する。** 同じ path が別用途で出現しても巻き込まず、引用符を含む生成済みの値全体に一致させる。検索文字列に値の後の改行は含めない。これにより、B3 のように代入行の末尾へ追加された構文を残す。行全体の削除、path の全域置換は行わない。

固定 basename、dispatcher の固定 suffix、production の marker 定数は置換後にも残る。`#PBS -N` は、本 test の通常の `tmp_path` 命名では環境依存部分に当たらないため正規化しない。

P5 は採用し、各置換の直前に次を置く。

```python
assert script.count(needle) == 1, f"normalization needle must occur once: {needle!r}"
```

これは正規化対象の欠落・重複を検出する前提検査である。production に受理条件を追加せず、production の受理集合にも触れないため、scope 外の「追加 gate」には当たらない。各 needle は異なる代入名で始まるので、先行する置換が後続の needle を消すこともない。

## 検査本体と parametrize の形

parametrize と signature は次の形とする。

```python
@pytest.mark.parametrize(
    "repo_root",
    [_REPO, Path("/__t2761__/repo release's checkout")],
    ids=["repo-current", "repo-release-path"],
)
def test_compute_marker_is_cross_namespace_evidence_without_release_handshake(
    tmp_path, repo_root,
):
```

`_job_script` の `repo_root=_REPO` を `repo_root=repo_root` に変更し、他の引数は維持する。合成 path の実在は不要である。

静的確認で、合成 path の `shlex.quote` 結果は次の文字列だった。

```text
'/__t2761__/repo release'"'"'s checkout'
```

検索式にも production と同じ `shlex.quote(str(...))` を使うため、`'` の `'"'"'` 表現を含めて一致する。

正規化・検査ブロックの逐語案は次節の **A の old** に示す。説明コメントは次の内容とする。

```python
# 環境値を除いた本文の release 候補行を保守的に拒否する。
# FA-4 の release handshake 不在の代理検査。
```

検査本体は指定どおりとする。

```python
release_lines = [line for line in normalized.splitlines() if "release" in line.lower()]
assert not release_lines, release_lines
```

構文解析を行ったとは説明しない。marker と同一行に出るものへ限定せず、`RELEASE=1`、alias 経由、comment を含め、正規化後の release 候補行を保守的に拒否する。

既存の以下の 3 assert は文言を変えない。先頭 2 本の後に新ブロックを入れ、最後の `while` assert はその後に残す。

```python
    assert DC._COMPUTE_MARKER_NAME in script
    assert script.index("mv \"$marker_tmp\" \"$MARKER\"") < script.index("selected=\"\"")
```

```python
    assert "while" not in script
```

`while` を含む環境 path による反転は、本 wave の保証範囲外のままである。

## 変異 matrix 事前登録 (anchor 逐語・期待 node・即抜けの根拠)

node の略号を次のとおり定義する。

```text
C = orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]
R = orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-release-path]
```

| ID | 変異ファイル | 期待結果 | 期待失敗 node 完全集合 |
|---|---|---|---|
| M0 | production | SURVIVED | `{}` |
| A | test | KILLED | `{R}` |
| B | production | KILLED | `{C, R}` |
| AB | test＋production | KILLED | `{C, R}` |
| B2 | production | KILLED | `{C, R}` |
| B3 | production | KILLED | `{C, R}` |

A の期待には、container の repo path と basetemp に `release` がないという brief の条件が必要である。以下の各ブロックは末尾改行を含む置換文字列とする。

**M0 — 無害な comment の注入**

対象: `tools/pegasus/dispatch_compute.py:889–892`

old:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
```

new:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
# Publish compute visibility evidence.
mv "$marker_tmp" "$MARKER"

selected=""
```

**A — 新ブロックを旧 2 行へ戻す**

対象: 実装後の test 内、既存の marker 順序 assert の直後。正規化部分も含めて戻し、parametrize は残す。

old:

```python
    normalizations = (
        (
            "\nRESULT=" + shlex.quote(str(tmp_path / "result.json")),
            "\nRESULT=<SUBMISSION>/result.json",
        ),
        (
            "\nPROBE=" + shlex.quote(str(tmp_path / "interpreter_probe.py")),
            "\nPROBE=<SUBMISSION>/interpreter_probe.py",
        ),
        (
            "\nREQUEST=" + shlex.quote(str(tmp_path / "request.json")),
            "\nREQUEST=<SUBMISSION>/request.json",
        ),
        (
            "\nREPO=" + shlex.quote(str(repo_root)),
            "\nREPO=<REPO>",
        ),
        (
            "\nDISPATCHER=" + shlex.quote(str(repo_root / "tools" / "pegasus" / "dispatch_compute.py")),
            "\nDISPATCHER=<REPO>/tools/pegasus/dispatch_compute.py",
        ),
        (
            "\nMARKER=" + shlex.quote(str(tmp_path / DC._COMPUTE_MARKER_NAME)),
            "\nMARKER=<SUBMISSION>/" + DC._COMPUTE_MARKER_NAME,
        ),
    )
    normalized = script
    for needle, replacement in normalizations:
        assert script.count(needle) == 1, f"normalization needle must occur once: {needle!r}"
        normalized = normalized.replace(needle, replacement, 1)
    # 環境値を除いた本文の release 候補行を保守的に拒否する。
    # FA-4 の release handshake 不在の代理検査。
    release_lines = [line for line in normalized.splitlines() if "release" in line.lower()]
    assert not release_lines, release_lines
    assert "while" not in script
```

new:

```python
    assert "release" not in script.lower()
    assert "while" not in script
```

**B — marker の release 待機候補を注入**

対象: `tools/pegasus/dispatch_compute.py:889–892`

old:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
```

new:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
until [[ -f "${{MARKER}}.release" || -f "$marker_tmp" ]]; do sleep 1; done
mv "$marker_tmp" "$MARKER"

selected=""
```

**AB — A と B を一つの変異に束ねる**

一つの変異の `replacements` に、次の 2 件をこの順で並べる。

1. test ファイルに、上記 **A の old → new** を逐語で適用。
2. production ファイルに、上記 **B の old → new** を逐語で適用。

独立した A、B の実行結果を合算するのではなく、一つの checkout に両方を適用して一走する。新検査での B と旧検査へ戻した AB がともに `{C, R}` を拒否し、A では環境 path 由来の R だけが失敗するという比較を登録する。旧 HEAD に R node がない点は、parametrize を維持し旧 assert の bytes を復元することで扱う。

**B2 — alias 経由の 3 行を注入**

対象: `tools/pegasus/dispatch_compute.py:889–892`

old:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
mv "$marker_tmp" "$MARKER"

selected=""
```

new:

```text
    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"
gate="$MARKER"
RELEASE_FILE="$gate.release"
until [[ -f "$RELEASE_FILE" || -f "$marker_tmp" ]]; do sleep 1; done
mv "$marker_tmp" "$MARKER"

selected=""
```

**B3 — MARKER 代入行の末尾へ注入**

対象: `tools/pegasus/dispatch_compute.py:871–874`

old:

```text
DISPATCHER={shlex.quote(str(dispatcher))}
MARKER={shlex.quote(str(marker_path))}

write_failure() {{
```

new:

```text
DISPATCHER={shlex.quote(str(dispatcher))}
MARKER={shlex.quote(str(marker_path))}; until [[ -f "${{MARKER}}.release" || -n "$MARKER" ]]; do sleep 1; done

write_failure() {{
```

production の anchor は Python の f-string ソースそのものなので、`${{MARKER}}`、`${{PBS_JOBID:-unknown}}`、`{{` を保持する。生成された shell script では通常の `${MARKER}` 等になる。

B/B2 は、直前の `printf … >"$marker_tmp"` によって実在する一時 marker を OR 条件で検査する。正常な submission dir への書込みが成立した runner 経路では初回条件が真となり、`sleep` に入らない。B3 は同じ行で `MARKER` を代入した後に検査するため、`set -u` 下でも未定義ではなく、非空の path によって `-n "$MARKER"` が真となる。いずれも runner に本物の待機を導入しない形である。

静的に、M0/B/B2 共通の old と B3 の old は現ソース中でそれぞれ **出現数 1** と確認した。A は未実装なので、実装後に old の出現数 1 を確認する。全変異について最終 commit 上で再確認し、置換不成立・複数一致なら停止する。

親の実測は brief の `tools/mutation_harness.py --runner-mode dispatch --detached` と `--force-dispatch` 付き runner に従う。初回 probe の観測 node を保存し、本走では期待集合との完全一致を要求する。M0 の SURVIVED は注入 diff 確認を伴わせ、dispatch 収集失敗や timeout を KILLED と数えない。

## B4 login probe

親が job dir で、**実装後の test** に対して `python3 -B` で実行する補助 probe。repo に保存せず、対象関数を直接呼ぶ。以下は約 10 行の形であり、この段では実行しない。

```python
import runpy
from pathlib import Path
from unittest.mock import patch
ns = runpy.run_path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py")
with patch.object(ns["DC"], "_COMPUTE_MARKER_NAME", "compute-visible.release"):
    try:
        ns["test_compute_marker_is_cross_namespace_evidence_without_release_handshake"](Path("/__t2761__/submission"), ns["_REPO"])
    except AssertionError as exc:
        assert exc.args and isinstance(exc.args[0], list), repr(exc)
        assert "MARKER=<SUBMISSION>/compute-visible.release" in exc.args[0], repr(exc)
        print("B4: release 候補行の検査で定数改名を拒否")
    else:
        raise AssertionError("B4: marker 定数の release が隠された")
```

合成 submission path は文字列化するだけなので、ディレクトリ作成は不要。dispatch も script 実行も行わない。単なる `AssertionError` ではなく、新検査の診断である行リストに正規化後の marker 行が含まれることを確認する。定数差替えは `patch.object` の終了時に復元する。

## 波及と変更しない一覧

- production の `_job_script` は恒久変更しない。上記 production 変異は親の mutation checkout 内だけで適用・復元する。
- 他の `_job_script` 呼出しは変更しない。参照位置は `1063`、`1116`、`2299`、`4080`、`4142`、`5055`、`5340`、`5927`（依頼の 5937 付近）、`6119`、`6616`。
- 他 test、docs、`:24` の `_REPO` 定義、duration ledger は変更しない。
- 共通 helper、追加 gate、他 test への同型是正は追加しない。
- 対象 test は C/R の 2 node になる。brief の調査どおり旧 node の稼働 allowlist はなく、duration ledger の更新も計画に含めない。

## 未確定事項

P1〜P5 に沿った実装案として未決の選択肢はない。ただし、以下は親の実装・実測後に確定する。

- A の実装後 anchor と、全 anchor の最終 commit 上での一意性。
- 無変異時の C/R、B4 probe、変異ごとの失敗 node 完全集合。
- 対象 test、file 単独、受入全走の結果。

この段で行ったのは、資料読取、現ソースの AST parse、引用符表現と既存 anchor 出現数の静的確認だけである。pytest・対象 test の直接呼出し・B4・変異走は実行していない。

## 総括

6 個の環境 path 値だけを正規化し、固定名・marker 定数・行末構文を残した本文から release 候補行を検出する。既存 3 assert を維持し、環境 path の偽赤を除きながら template 由来の release に対する検出力を保つ。ファイル変更はなく、テストの緑は未確認である。