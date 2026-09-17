# [T-2761] release handshake 不在検査を環境 path 非依存の候補行検査へ置換 (F1022 の恒久対応)

- 日付: 2026-09-17 / branch `worktree-dev-wave-t2761-handshake-check` (fresh worktree from main 38353207f)
- 実装 commit: `6dcbf6113` (Codex author、`orchestrator/tests/test_pegasus_dispatch_compute.py` 1 file、+46/-3)
- 設計判断: {{D:path-independent-word-absence-check}} (spool fragment seq 2)。失敗の型: F50 再発 + F1022 supersede (seq 3)
- job dir: `/home/SFC/tanab/.claude/jobs/1031d339/` (tmp/wave に prompt・log・spec 生成器 `make_mutation_spec.py`・login probe `login_probe_b4_b5.py`。
  いずれも実装面なので repo へは入れない)

## 1. 依頼 (逐語)

> [T-2761] (P2、F1022) orchestrator/tests/test_pegasus_dispatch_compute.py:2592 の
> test_compute_marker_is_cross_namespace_evidence_without_release_handshake が script 本文へ掛ける "release" not in
> script.lower() を、repo path を除いた本文に対する handshake 構文 (marker を操作する release 行) の不在検査へ変える。
> 着手直前の local main から fresh worktree を作る。Codex author (D95)。変異事前登録 = (a) repo path に release を含む fixture で緑、
> (b) handshake 行を注入した script で赤。着地後に暫定防壁 (wave の slug / branch / worktree 名に release を含めない) が不要になる旨を
> worklog に書く。規律 2 を緩めない。本題の検査置換だけ。追加 gate は scope 外。

## 2. 何を変えたか

由来は T-188 の裁定 FA-4 (`output/insights/2026-07-30/pegasus-compute-node-dispatch/fix-adjudication.md`): 計算ノード側が
submission dir へ marker を書き、親はその実在を永続性の証拠とする。親→job の release handshake は作らない。この不在を
語 1 つ (`release`) の不在で代理していたのが F1022 の穴 (script に埋まる worktree path の `scope-release` に当たった)。

新しい検査 (`orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake`):

1. `_job_script` が埋め込む環境依存の 6 値 (`RESULT` / `PROBE` / `REQUEST` / `MARKER` = submission dir 配下、`REPO` / `DISPATCHER` =
   repo_root 配下) を、「改行 + 代入名= + `shlex.quote(str(path))` の完全表現」で位置限定に各 1 回だけ token へ置換する。置換文字列には
   固定 basename・`tools/pegasus/dispatch_compute.py`・`DC._COMPUTE_MARKER_NAME` を残す (production 定数を隠さない)。job name
   (`#PBS -N izdw-<tmp_path.name[:10]>`) は pytest の node 名由来で環境依存でないので置換しない。
2. 置換の前提検査 (P5): 各検索文字列は出現数ちょうど 1、直後が shell word 終端 (`\n 空白 tab ; & |` または末尾)。崩れたら
   その理由で赤 (厳しくする方向のみ)。
3. 正規化後の本文で `release` (大小無視) を含む行を全件列挙して空を要求する (assert メッセージに該当行)。「marker を操作する
   release 行」に限る狭い同一行共起は、旧検査が拒否していた `RELEASE=1` 単独行・comment・alias 経由の複数行待機を見逃すので
   不採用 (規律 2)。候補行の保守的拒否であって構文解析ではない、と comment に明記。
4. `repo_root` を `[_REPO, Path("/__t2761__/repo release's checkout")]` (ids `repo-current` / `repo-release-path`) で parametrize し、
   path に `release` を含む入力の緑を test 自身が守る (合成 path は空白と `'` を含み `shlex.quote` の表現一致も検査する)。
5. 既存 3 assert (marker 名、`mv` が `selected=""` より前、`"while" not in script`) は文言・位置とも不変。

## 3. 段 1〜4 (brief → plan → 敵対相談 → 裁定)

- **段 2/3 v1 は invalidate した。** 段 1 で条件 dispatch `DW-O13` (gate・検証の新設) を「既存 assert の置換だから非成立」と
  参照節の本文を読まずに判定したが、同節 2 文目「既存 exact 述語の改訂で受理形を増やす場合も新設に当たる」に該当していた。
  段 3 v1 の後に気づき、読み込み契約 (最遅 = 段 2 前) に従い段 2 から再実行した (F50 再発として記録)。v1 成果物は
  `verbatim/v1-invalidated/`、v2 brief は `verbatim/s1-brief-v2.md` (DW-O13 の要求 = 入力 field の所在・実環境の値域・到達可能性を追記)。
- v1 の所見で v2 brief に取り込んだもの: 正規化で production 定数を隠さない (lensA-1)、alias 3 行の反例 (lensA-4)、A の期待 `{R}`
  の環境条件 (lensB-1)、位置限定置換 (lensB-3)、`while` は scope 外 (両者)。
- 段 3 v2 の主要所見と裁定 (`verbatim/s4-adjudication.md` の表): needle が shell word の接頭辞にも当たる反例 (`/__t2761__/rele` +
  template `ase`) → P5 に word 終端検査を追加 (must-fix 採用)。B/B2 の即抜けを file 実在でなく非空変数へ (採用)。「B2 は狭い定義なら
  生存」の断定を削除 (採用)。AB の R は path 由来の冗長赤 (採用)。旧 HEAD arm を追加登録 (採用)。dispatch blob 検査で production
  変異が止まる懸念は refuted (起動時 1 回)。
- **runner 経路の制約:** harness は container の `dispatch_compute.py` 経由で計算ノードへ投入するので、`_job_script` へ本物の待機を
  注入すると dispatch 自体が hang する (DW-M07)。負例は実行時に即抜ける until 行 (`|| -n "$MARKER"`) にし、marker 定数の改名 (B4) は
  runner の marker 収集を壊すので matrix から外して login probe で補助証拠にした。

## 4. 段 5〜6 (実装 → レビュー)

- author (Codex `gpt-6-astra` / medium、`verbatim/s5-author.md`): 裁定どおり実装。hook が login node の pytest を拒否したため未実走報告
  → 親が焦点走。
- 親の焦点走 (すべて `tools/run_tests.py` の自動 dispatch、計算ノード): 対象 2 node = **2 passed** (request 4017、4.59 s)、
  file 単独 = **339 passed** (request 4038、25.62 s)。log は `verbatim/focus-run-*.txt`。
- login probe (`verbatim/login-probe-b4-b5.txt`、dispatch なし・script 実行なし、test 関数を直接呼ぶ): 対照 (現 repo path・合成 release path)
  緑 / **B4** = `DC._COMPUTE_MARKER_NAME` を `compute-visible.release` に差し替え → 行リスト `['MARKER=<SUBMISSION>/compute-visible.release']` で赤
  (正規化が定数を隠さない) / **B5** = `repo_root=/__t2761__/rele` + REPO 値直後に `ase` 連結 → `normalization needle is not word-terminated`
  で赤 (境界反例を P5 が拒否)。
- 段 6 レビュー 2 本 (`verbatim/s6-reviewA.md` / `s6-reviewB.md`): B は must-fix なし (anchor 一意・単一理由・runner 安全・probe 妥当性を
  すべて refuted)。A は must-fix 1 = 「改行を含む basetemp に `REPO=<repo path>` が埋め込まれると P5 の出現数が 5 になり偽赤」。
  親裁定: real / nit / 不採用 — 改行入りの一時 dir path に自 repo path が埋め込まれる環境は現実に生じない仮想リスク (旧検査の偽赤は
  普通の dir 名の語で起きた)、是正には代入位置の parser が要り「本題の検査置換だけ」を超える (DW-G05)。**既知の限界**として D に記録。
  fix 子は起動していない。
- 全史 provenance 監査 (実装 commit 後、request 4054): 11,076 件、新規違反なし。

## 5. 変異 matrix

container は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2761-handshake-check/` 配下の detached worktree 2 本 (`mutation-tree` @6dcbf6113、
`mutation-tree-old` @38353207f、path に `release` 無し)。`tools/mutation_harness.py --runner-mode dispatch --detached` を直接当て、runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf -p no:cacheprovider`、D612 の
queue-wait / grace 上書き 1800 / 600。spec と台帳は本 dir の `mutation-spec-*.json` / `mutation-ledger-*.json`。

| id | 層 | 変更 | 期待 | probe 観測 | 本走 |
|---|---|---|---|---|---|
| m0-comment | production | `mv` の前に comment 1 行 | SURVIVED | SURVIVED | **SURVIVED** (注入 diff sha 3df44ec5…、rc=0) |
| a-old-check | test | 新検査ブロックを旧 2 行へ戻す | KILLED `{R}` | `{R}` (C 緑 = 環境条件成立) | **KILLED**、期待=観測 |
| b-handshake | production | `mv` の前に `until [[ -f "${MARKER}.release" \|\| -n "$MARKER" ]]; do sleep 1; done` | KILLED `{C,R}` | `{C,R}` | **KILLED**、期待=観測 |
| ab-old-check-handshake | both-layers | A + B | KILLED `{C,R}` (C = 旧検査の handshake 検出、R = path 由来の冗長赤) | `{C,R}` | **KILLED**、期待=観測 |
| b2-alias | production | `gate="$MARKER"` / `RELEASE_FILE="$gate.release"` / `until [[ -f "$RELEASE_FILE" \|\| -n "$gate" ]]…` | KILLED `{C,R}` | `{C,R}` | **KILLED**、期待=観測 |
| b3-same-line | production | `MARKER=…; until [[ -f "${MARKER}.release" \|\| -n "$MARKER" ]]…` (行末構文) | KILLED `{C,R}` | `{C,R}` | **KILLED**、期待=観測 |
| 旧 arm b-handshake | production @38353207f | 同 B | KILLED `{O}` | `{O}` | **KILLED**、期待=観測、matching 1/1 |

C = `…::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]`、R = 同 `[repo-release-path]`、
O = 旧 HEAD の同名 node (parametrize なし)。

**本走の集計 (新 arm、`mutation-ledger-new-final.json`、spec sha256 `257f4c13…`、repo_head 6dcbf6113):** baseline PASSED (48 s)、
負例 5/5 KILLED で期待 node と観測 node が完全一致 (matching 6/6)、等価 m0 SURVIVED、MISMATCH 0、TIMEOUT 0、全 anchor 出現数 1。
probe 走 (`mutation-ledger-new-probe.json`、spec `f001517f…`) は全件 SURVIVED 登録で観測 node を集め、段 4 の静的予測と完全一致した。
旧 arm (`mutation-ledger-old-final.json`、spec `67d8d30c…`、repo_head 38353207f): baseline PASSED、b-handshake KILLED 1/1。

- 赤理由の確認 (job stdout): b-handshake は `AssertionError: ['until [[ -f "${MARKER}.release" || -n "$MARKER" ]]; do sleep 1; done']`
  (release 候補行 assert、注入行のみ = 単一理由)。a-old-check は旧 assert の `'release' is contained here:` に合成 path
  (`/__t2761__/repo release'"'"'s checkout`) = F1022 の再現。計算ノードの実効 tmp_path は
  `/tmp/pytest-of-tanab/pytest-0/popen-gw35/test_compute_marker_is_cross_n0/`、REPO は container path で、いずれも `release` / `while` を含まない。
- **DW-M08 の新旧両走の当て方:** 本 wave は偽赤の除去であり「新テストだけが検出する差分」は無い。比較証拠は
  ①新 baseline が合成 release path (R) を受理、②旧検査を復元した a-old-check が同 path を拒否 (偽赤の再現)、③handshake 注入 (b) を
  新 (C,R) も旧 HEAD (O) も拒否、の 3 点。旧 arm は別 container・別 spec で実走した。
- 即抜け変異が示すのは静的な候補行検出であって、待機動作 (親死亡で job が待つ) の検出ではない (段 3 A-7)。

## 6. scope 外 (裁定パッケージ候補、実装していない)

- `"while" not in script` (同 test 末尾) は元の script に掛かったままで、repo / submission path に `while` を含むと同型の偽赤になる。
  本 wave の完了条件は release 検査に限り、撤去できる暫定防壁は「wave 名に `release` を含めない」だけ。次の一手に P3 で起票。
- 改行を含む一時 dir path + 自 repo path の埋込みで P5 が偽赤になる経路 (段 6 A-1)。仮想リスクとして記録のみ。
- DW-M08「テスト強化だけの wave の新旧両走」を偽赤是正 wave にどう当てるかの契約整理 (本 wave は §5 の 3 点で満たした)。

## 7. 段 8 (自己改善) の候補と裁定

- (1) DW-O13 の判定を参照節の冒頭 2 文を読まずに行った (F50 再発、routing 1 = failures fragment に記録済み)。dev-wave 入口の条件表の
  文言変更は byte 予算 (入口・reference とも満杯) に入らず、F50 の再発追記で代替。command 入口・段構成・権限の変更なし。

## 8. 工数

codex 子 8 本 (plan 2 (v1 invalidated + v2)、consult 4 (v1 2 + v2 2)、author 1、review 2、fix 0、全段 `gpt-6-astra` / `medium`)。
親の実測: 焦点走 2 (計算ノード)、login probe 1 script (対照 + B4 + B5)、変異 4 走 (旧 probe / 旧 final / 新 probe / 新 final、計算ノード dispatch
2+2+7+7 = 18 run)、provenance full 1 本、受入 1 走 (land 前)。
