# [T-2761] 段 1 brief v2 (DW-O13 成立による改訂。v1 は invalidate、段 2 から再実行)

- **研究前進:** 土台。F1022 は受入全走を決定的に赤にする穴で、暫定防壁 (wave 名に `release` を含めない) は memory 依存。
  完了判定 = 同 test の **release 検査**が repo path / submission path の語に依らず緑で、handshake 行の注入で赤 (変異で実証)。
  `while` 検査の path 反転は本 wave の保証範囲外 (scope 外、裁定パッケージ候補)。止めている研究は無い (P2)。
- **scope:** `orchestrator/tests/test_pegasus_dispatch_compute.py` の `test_compute_marker_is_cross_namespace_evidence_without_release_handshake`
  1 本の検査置換 (とその入力の parametrize) だけ。production (`tools/pegasus/dispatch_compute.py::_job_script`) は変えない。
  追加 gate・他 test の同型是正・docs の一般化・helper の共通化は scope 外。
- **確定済みユーザー裁定 (引数):** 着手直前の local main から fresh worktree / Codex author (D95) / 変異事前登録 (a)(b) /
  着地後に暫定防壁が不要になる旨を worklog へ / 規律 2 を緩めない / 本題の検査置換だけ。
- **由来 (一次資料):** T-188 の裁定 FA-4: 「計算ノード側が submission dir へ marker を書き、親はその実在を永続性の証拠とする
  (cross-namespace 証拠)。親→job の release handshake は作らない (親死亡で job が待つ形にしない)」。commit a34266d2d で語不在の assert。

## DW-O13 (gate 入力の実在) — 受理形を増やす既存述語の改訂として適用

- **入力の所在 (実成果物の field):** 検査対象は `_job_script` の返り値 (文字列)。環境依存値の埋込み位置は
  `tools/pegasus/dispatch_compute.py` の `RESULT=` (866)、`PROBE=` (867)、`REQUEST=` (868)、`REPO=` (870)、`DISPATCHER=` (871)、
  `MARKER=` (872) の 6 行で、各値は `shlex.quote(str(path))` 形。`#PBS -N` (863) の job_name は `izdw-` + submission_dir.name[:10]
  で、本 test では submission_dir = pytest `tmp_path` (名前 = node 名先頭 30 字 `test_compute_marker_is_cross_n` + 連番) だから
  環境依存でない (親実測: `_pytest/tmpdir.py::_mk_tmp`)。
- **実環境で取りうる値 (実測):** repo_root = worktree 絶対 path (F1022 の実例 `…/dev-wave-cross-protocol-scope-release`、本 wave は
  `…/dev-wave-t2761-handshake-check`)。tmp_path = basetemp (`/tmp/pytest-of-<user>/pytest-N/`) 配下 (ユーザー名・`--basetemp` は環境依存)。
  quote が要る path (空白・`'`) では `'...'` / `'"'"'` 形になる。
- **到達可能性:** 正例 (path に `release`) は F1022 で実到達済み。負例 (template 由来の release 行) は template に現在 0 行で、
  変異注入で到達させる。時間予算の述語は無い。同名識別子の二義化は無い (`release` は語であって field 名でない)。

## 変更面 (実アンカー)

| file:line | 内容 |
|---|---|
| `orchestrator/tests/test_pegasus_dispatch_compute.py:2579-2593` | 対象 test。`:2592` の `assert "release" not in script.lower()` を置換 |
| 同 `:24` | `_REPO = Path(__file__).resolve().parents[2]` (変更しない) |
| `tools/pegasus/dispatch_compute.py:834-916` | `_job_script` (読むだけ) |

## 不変条件

(i) 既存 3 assert (`DC._COMPUTE_MARKER_NAME in script`、`mv "$marker_tmp" "$MARKER"` が `selected=""` より前、`"while" not in script`)
は文言も含め変えない。(ii) 検出力は現行以上: 現行が赤にする「template 由来の release 行」は新検査でも赤 (production の
定数・固定 basename・固定 suffix は正規化で隠さない)。(iii) 環境依存の path 値だけで release 検査は反転しない。(iv) 規律 2:
検査を甘くして通す方向の変更は不採用。

## 親の provisional 裁定 (段 3 v1 の所見を取り込んだ現行案。攻撃対象)

- (P1) **広い定義**: 正規化後の本文を行に割り、`release` (大小無視) を含む行を全件列挙し空を要求 (assert メッセージに該当行)。
  「marker を操作する release 行」はこの部分集合。狭い同一行共起は `RELEASE=1` 単独行や alias 経由の 3 行待機
  (`gate="$MARKER"` / `RELEASE_FILE="$gate.release"` / `until [[ -f "$RELEASE_FILE" ]]`) を見逃すので不採用。
  説明は「handshake 構文を解析した」ではなく「環境値を除いた本文の release 候補行を保守的に拒否する」と書く。
- (P2) **位置限定・値だけの置換 (6 値、各 1 回)**: 検索は「改行 + 代入名= + `shlex.quote(str(path))` の完全表現」、置換は環境由来部分だけを
  token にし固定部分を残す: `REPO=<REPO>`、`DISPATCHER=<REPO>/tools/pegasus/dispatch_compute.py`、`RESULT=<SUBMISSION>/result.json`、
  `PROBE=<SUBMISSION>/interpreter_probe.py`、`REQUEST=<SUBMISSION>/request.json`、`MARKER=<SUBMISSION>/` + `DC._COMPUTE_MARKER_NAME`。
  行ごと削除・`str(path)` の全域置換は不採用 (行末に足された handshake を消す)。job_name は環境依存でないので置換しない。
- (P3) **parametrize**: `repo_root` を `[_REPO, Path("/__t2761__/repo release's checkout")]`、id `repo-current` / `repo-release-path`。
  合成 path は実在不要 (`_job_script` は文字列化するだけ)。旧 node を pin する稼働 allowlist は無い (duration ledger は配分 hint)。
- (P4) `"while" not in script` は触らない (元の `script` に対して維持)。
- (P5) 各検索の出現数 1 を assert してから置換する (当たらない・複数当たるを「理由不明の release 赤」でなく正規化前提の破れとして
  赤にする。置換専用の前提検査で、production の受理集合には触れない)。

## 変異事前登録案 (段 4 で確定)

harness は `tools/mutation_harness.py --runner-mode dispatch --detached` を container worktree
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2761-handshake-check/mutation-tree`、path に `release` 無し) へ当て、runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf -p no:cacheprovider`。
**制約: runner は container の `dispatch_compute.py` 経由で計算ノードへ投入するので、`_job_script` へ注入する行は実行時に
即抜ける形 (待機の脱出条件に実在 file `$marker_tmp` / 非空変数を or で足す) にし、本物の待機を注入しない (DW-M07 の自壊)。**

| id | 層 | 変更 | 期待 |
|---|---|---|---|
| M0 | production | `mv "$marker_tmp" "$MARKER"` 直前に comment `# Publish compute visibility evidence.` | SURVIVED |
| A | test | 新検査ブロックを旧 2 行 (`assert "release" not in script.lower()` + while) へ戻す | KILLED `{R}` (container / basetemp に release 無し → C は緑) |
| B | production | `mv` 直前に `until [[ -f "${MARKER}.release" \|\| -f "$marker_tmp" ]]; do sleep 1; done` | KILLED `{C, R}` |
| AB | test+production | A + B (旧検査でも handshake を捕る = 新旧両走の旧側) | KILLED `{C, R}` |
| B2 | production | `mv` 直前に alias 3 行 (`gate="$MARKER"` / `RELEASE_FILE="$gate.release"` / `until [[ -f "$RELEASE_FILE" \|\| -f "$marker_tmp" ]]; do sleep 1; done`) | KILLED `{C, R}` (狭い定義なら生存) |
| B3 | production | `MARKER=...` 行末に `; until [[ -f "${MARKER}.release" \|\| -n "$MARKER" ]]; do sleep 1; done` | KILLED `{C, R}` (行ごと削除への退行検出) |

C = `…::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]`、R = 同 `[repo-release-path]`。
marker 定数を `compute.release` に改名する B4 は runner 経路 (marker 収集) を壊すので matrix から外し、login node の probe
(process 内で `DC._COMPUTE_MARKER_NAME` を差し替えて対象 test 関数を直接呼ぶ) で「正規化が定数を隠さない」を補助証拠にする。
DW-M08 の新旧両走は A / AB で実現する (旧 HEAD の検査 2 行は A の復元 bytes と同一、旧 HEAD には R node が無い)。

## 受入・実測環境

login node で焦点走 (対象 test → file 単独)、変異は計算ノード dispatch (probe 走で観測 node を集め、本走で完全一致)、
受入全走は `tools/dev_wave_wait.py acceptance` (`IZANAGI_ACCEPTANCE_SHARDS=3`)。

## 条件 dispatch の判定

DW-O08/O09/O10 非成立 (test file のみ、凍結成果物に触れない)。**DW-O13 成立 (上記)。** DW-O11 非成立。DW-O19 は変異で成立 (段 6 前に読む)。
