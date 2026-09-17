# [T-2761] 段 4 裁定 (親) — プラン v2 への修正と変異事前登録の確定

裁定 inbox 再走査: wave 開始後の main 更新なし (38353207f のまま)、`docs/spool/` に本 T の fragment なし、T-2761 を止める裁定なし。

## 所見の裁定 (段 3 v2)

| 所見 | 裁定 | 採否 | 反映 |
|---|---|---|---|
| A-1 needle が shell word の接頭辞に当たる (`/__t2761__/rele` + template `…ase` → 旧拒否・新受理) | real / must-fix / scope 内 | 採用 | P5 に word 終端検査を足す (下記) |
| A-2 固定 basename・suffix・marker 定数の改名は隠れない | refuted | — | 説明に残す |
| A-3 quote 表現・行末構文・別行は過剰除去されない | refuted | — | — |
| A-4 P5 の説明「production の受理集合に触れない」は不正確 | real / nit | 採用 | 説明を「正規化の前提が崩れた入力を保守的に拒否する同一検査内の前提確認 (厳しくする方向のみ)」に直す |
| A-5 「B2 は狭い定義なら生存」は定義不足 | real / must-fix (説明) | 採用 | 断定を削除。B2 は alias 形を広い検査が拒否する証拠にとどめる |
| A-6 / B-2 B/B2 の即抜けが file 実在に依存し hang 経路を作る | real / must-fix | 採用 | 脱出条件を非空変数 `-n "$MARKER"` (B2 は `-n "$gate"`) にする |
| A-7 即抜け変異は静的な候補行検出の証拠であって待機動作の検出ではない | real / nit | 採用 | 台帳にその旨を書く |
| A-8 / B-3 既存 3 assert が先に赤にしない・runner 正常経路は壊れない | refuted | — | B/B2/B3 の traceback を保存し赤理由を確認する |
| A-9 / B-4 A の `{R}` は環境条件つき | real / must-fix (手順) | 採用 | probe 走で R の失敗本文から実効 REPO / tmp_path を記録し、C 緑を確認して本走の期待集合を確定する |
| B-1 dispatch blob 検査で production 変異が止まる | refuted (起動時 1 回、MH:3122) | — | — |
| B-5 A/AB を DW-M08 の新旧両走と同一視できない | real / must-fix (整理) | 採用 | 旧 HEAD (38353207f) の別 container に修正版 B を当てる旧 arm を追加登録 (期待 = 旧 node 1 件)。新旧両走の位置づけは「偽赤是正」として台帳に書く |
| B-6 AB の R は path 由来の冗長な赤 | real / must-fix (帰属) | 採用 | AB の handshake 検出証拠は C のみ、R は冗長赤と明記 |
| B-7 spec JSON の形 | refuted (登録素材) | — | 最終 spec は exact key (`file`/`old`/`new`、`expected_nodes` は文字列配列) |
| B-8 B4 の process 内差替えは効く (`DC:846` が module global を読む) | refuted | — | B4 probe は plan v2 の形で実施 |
| B-9 plan v2 の file:line は現物と一致 | refuted | — | — |
| A-10 / B-10 `while` の同型偽赤は残る | real / nit / **scope 外** | 裁定パッケージ候補 | 完了条件は release 検査に限定。撤去できる暫定防壁は「wave 名に release を含めない」だけ |

## プラン v2 の修正 (= プラン v2.1、author はこれを実装する)

1. **P2 (6 値の位置限定置換)** はプラン v2 の検索/置換表どおり。
2. **P5 (前提検査)** を次の 2 段にする。各 needle について
   - `assert script.count(needle) == 1, f"normalization needle must occur once: {needle!r}"`
   - `end = script.index(needle) + len(needle)`; `assert end == len(script) or script[end] in "\n \t;&|", f"normalization needle is not word-terminated: {needle!r}"`
   その後 `normalized = normalized.replace(needle, replacement, 1)`。
   説明 comment: 「正規化の前提 (値がちょうど 1 回、shell word として完結) が崩れた入力は保守的に拒否する。厳しくする方向だけで受理を増やさない」。
3. **P1 (検査本体)**: `release_lines = [line for line in normalized.splitlines() if "release" in line.lower()]` / `assert not release_lines, release_lines`。
   comment: 「環境値を除いた本文の release 候補行を保守的に拒否する (FA-4 の release handshake 不在の代理検査。構文解析ではない)」。
4. **P3 parametrize**: `[_REPO, Path("/__t2761__/repo release's checkout")]`, ids `repo-current` / `repo-release-path`。signature `(tmp_path, repo_root)`。
5. **P4**: `assert "while" not in script` は元の `script` に対して文言・位置とも維持。既存の先頭 2 assert も維持。
6. `import shlex` を test file の import 群へ追加 (alphabetical: `signal` の前)。
7. 変更しない: production、他 test、`_REPO`、conftest、docs、duration ledger。

## 変異事前登録 (確定。段 6 で author 後の anchor 一意性を再検証)

runner (新 arm): container `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2761-handshake-check/mutation-tree` (実装 commit の detached worktree) で
`tools/mutation_harness.py --runner-mode dispatch --detached`、`-- python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf -p no:cacheprovider`。
D612 上書き `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=1800` / `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`。probe 走 (全件 SURVIVED 登録) → 本走 (期待集合完全一致)。

C = `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]`
R = 同 `[repo-release-path]`
O = `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake` (旧 HEAD、parametrize なし)

| id | category | 層 | old (anchor) | new | 期待 | 単一理由 |
|---|---|---|---|---|---|---|
| m0-comment | positive | production `_job_script` 889-892 | `    "${{PBS_JOBID:-unknown}}" "$host" >"$marker_tmp"\nmv "$marker_tmp" "$MARKER"\n\nselected=""\n` | `mv` の前に `# Publish compute visibility evidence.\n` | SURVIVED `[]` | 等価 |
| a-old-check | negative | test (新ブロック全体、author 後に逐語確定) | 新検査ブロック | `    assert "release" not in script.lower()\n    assert "while" not in script\n` | KILLED `[R]` (C は container / basetemp に release 無しで緑。probe で実測) | 旧検査の path 偽赤 (F1022 再現) |
| b-handshake | negative | production 889-892 | 同 m0 | `mv` の前に `until [[ -f "${{MARKER}}.release" \|\| -n "$MARKER" ]]; do sleep 1; done\n` | KILLED `[C, R]` | release 候補行 (`until` なので while assert は非反応) |
| ab-old-check-handshake | both-layers | test + production | a-old-check の old/new + b-handshake の old/new | | KILLED `[C, R]` | C = 旧検査の handshake 検出、R = path 由来の冗長赤 (単独証拠に数えない) |
| b2-alias | negative | production 889-892 | 同 m0 | `mv` の前に `gate="$MARKER"\nRELEASE_FILE="$gate.release"\nuntil [[ -f "$RELEASE_FILE" \|\| -n "$gate" ]]; do sleep 1; done\n` | KILLED `[C, R]` | release 候補行 (alias 形) |
| b3-same-line | negative | production 871-874 | `DISPATCHER={shlex.quote(str(dispatcher))}\nMARKER={shlex.quote(str(marker_path))}\n\nwrite_failure() {{\n` | MARKER 行末に `; until [[ -f "${{MARKER}}.release" \|\| -n "$MARKER" ]]; do sleep 1; done` | KILLED `[C, R]` | release 候補行 (値だけ置換で行末構文が残る) |

旧 arm (DW-M08 の新旧両走): 旧 HEAD `38353207f` の別 container `…/dev-wave-t2761-handshake-check/mutation-tree-old` に
b-handshake (修正版) だけの spec → KILLED `[O]`。旧 baseline は緑 (旧 HEAD は R node を持たない)。この wave は偽赤の除去
なので「新テストだけが検出する差分」は無く、比較証拠は ①新 baseline の R 受理、②a-old-check の R 拒否、③新旧 b-handshake の
拒否、の 3 点 (台帳に明記)。

login probe (dispatch なし、job dir で実行、repo に入れない):
- B4: `patch.object(DC, "_COMPUTE_MARKER_NAME", "compute-visible.release")` で対象 test 関数を直接呼び、AssertionError の
  行リストに `MARKER=<SUBMISSION>/compute-visible.release` が含まれることを確認 (正規化が定数を隠さない)。
- B5 (A-1 の境界反例): `patch.object(DC, "_job_script", wrapper)` で REPO 値の直後に `ase` を連結した script を返し、
  `repo_root=Path("/__t2761__/rele")` で直接呼ぶ → P5 の word 終端検査で赤 (メッセージ `not word-terminated`) を確認。

## scope 外 (裁定パッケージ候補、実装しない)

- `"while" not in script` の path 反転 (F1022 と同型)。本 wave の完了条件は release 検査に限定。
- DW-M08「テスト強化だけの wave の新旧両走」を偽赤是正 wave にどう当てるかの契約整理 (本 wave は旧 arm を実施して満たす)。

## 変更面と所有

実装子 1 本 (Codex author)。所有 = `orchestrator/tests/test_pegasus_dispatch_compute.py` のみ。docs・production・commit は親。
