# [T-2406] 段 4 loop の job body へ gflags/glog 供給経路を移植する (D1773)

dev-wave `dev-wave-t2406-s4loop-gflags` (branch `worktree-dev-wave-t2406-s4loop-gflags`、base = local main
`34af5a571`、2026-09-08 06:47〜) の一次資料。裁定 D1773 (ユーザー裁定、/rulings 全件 第 14 回) を実装した。

## 何をしたか

| 項目 | 値 |
|---|---|
| 依頼 | `tools/pegasus/p3_s4_loop_pegasus.sh` へ `tools/pegasus/floor_scoping.sh` の gflags/glog prologue をそのまま移植 (D1773 (a)〜(d)) |
| 統合 commit | `96b8d0c2f` (job body + 契約テスト、Codex author gpt-5.6-sol xhigh / 親 integrator) |
| fix commit | `a173f0ab5` (契約テストの受理集合 4 穴 + README §7、Codex author / 親 integrator) |
| 変更 file | `tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`、`tools/pegasus/README.md` |
| 不変 | `tools/pegasus/policy.json` (whole-file golden で pin)、`tools/pegasus/admission_registry.json` (分類不変)、hooks、buildcache、driver |
| 段構成 | 全 9 段 (契約テストの受理集合が変わるため軽量版にしない、DW-C00) |

## 裁定の適用

- (a) policy 依存の新設: job body が `policy.json` の `gflags_source_path` / `gflags_expected_head` /
  `glog_source_path` / `glog_expected_head` を `"$PY" -I -B` の heredoc で読み、HEAD exact 一致・clean を検査する。
- (b) provenance file を作らない: 移植元の `$PROVENANCE_DIR/*` と `cmake-prefix-path.json` は落とし、6 command の
  stdout/stderr は job の `-o/-e` へ流す。receipt の schema と key 集合は不変。
- (c) 契約テストと registry を同じ commit で: 契約テストの required fragment / stage-order marker / refusal /
  fragment mutant / whitelist / 正例負例を統合 commit に含めた。registry は分類・reason・gate・evidence に変えるものが
  無く**不変**とした ((c) は「変える場合は同じ commit」と読む。段 3 レンズ A の nit として記録)。
- (d) `CMAKE_PREFIX_PATH` を driver 本走まで: `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` を
  masstree 事前構築の前に置き、以後 unset しない。契約テストは export 後の `unset` / `export -n` / `env -u` を拒否する。

裁定の範囲内の適応 (段 3・段 4 で裁量と判定): `fail 2` → 本 job body の `refuse` (rc=2 境界は同じ、message 8 個は同文)、
`$TOOLS/policy.json` → `$repo/tools/pegasus/policy.json`、事前構築へ同じ 2 root を semicolon 区切りの
`dependency_prefix` としても渡す (F813 型の欠落を塞ぐ、decisions fragment `s4-loop-prefix-contract-exact-three-lines` (番号は fold が付ける))。

## 計算ノードでの生死確認 (job `983020.nqsv`)

固定 SHA `a173f0ab5` の detached checkout (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2406-s4loop-gflags/submit-tree`、
CCBench submodule は `p3_s4_loop.PIN` 028f34d へ checkout) から、README §7 の tagged qsub command で fixture 経路
(`IZANAGI_S4_PROPOSAL_PATH` 無し) を 1 本投入した。`THIRDPARTY_SOURCE_ROOT` は T-2232 初回投入の hydrate 出力を再利用。

| 項目 | 値 |
|---|---|
| Created / Started / Ended | 08:33:33 / 08:33:40 / 08:34:18 (JST、2026-09-08)、Elapse 43S |
| 実行 host | `bnode` (reservation.json、`allocation-qstat.stdout` 参照) |
| `driver_rc` | 1 |
| 通った層 | host gate、sanitize、python3.10 shim、expected HEAD、CCBench PIN、reservation 束縛、claim root、**gflags/glog prologue (policy 読取・HEAD/clean 検査・configure/build/install)**、**masstree 事前構築 (`Could NOT find gflags` を越え receipt を書いた)** |
| 事前構築 receipt | `configure_argv` に `-DCMAKE_PREFIX_PATH=/scr/tanab/p3-s4-loop-pegasus/0_983020.nqsv/gflags-install;/scr/.../glog-install`、`config_h_sha256=e9a4ecd3…` |
| 止まった層 | driver 本走の condition gate: `condition gate rejected P3 S4 loop: supply=preprocess-failed meaning=declared-meaning-observed` (`p3_s4_loop.py:349`、`_require_condition_gate`) |

**D1737 が「実測していない」と留保した「供給経路を足せば job body が最後まで通るか」は、prologue と事前構築については
「通る」、driver 本走については「次の関門で止まる」が答えである。** 次の関門は `condition_meaning_gate` の supply arm
(owner compile command の preprocess) が計算ノードで失敗する型で、本 wave の scope (job body の供給経路) の外であり、
正しさ gate に触るため別途裁定が要る (次の一手 (slug `s4-loop-condition-gate-preprocess-on-compute`、番号は fold が付ける))。gate の失敗詳細 (preprocess の
stderr) は isolate worktree (`/scr`) 側にあり job 終了で消えたので、再現時は gate の証拠を evidence root へ写す形で取る。

evidence: `evidence/attempt-0001/` (compute-result.json、reservation.json、allocation-qstat.stdout、
masstree-prebuild-receipt.json、job.stdout、job.stderr)。**可逆最小正規化 (DW-S07):** `allocation-qstat.stdout` と
`job.stdout` は逐語コピーが `git diff --check` の行末空白に抵触するため、行末の空白 / tab を除去し末尾の空行を落とした
(可視文字不変)。原文は reservation.json の `allocation_qstat_stdout.sha256` と次の値で束縛する —
`allocation-qstat.stdout` 原文 sha256 `ad4e9cecc1230d07a0f23677068c7a49c274b19f57310ac1cd3a5a37a6dd19ee` (3859 bytes、
正規化後 3831 bytes)、`job.stdout` 原文 sha256 `daad407b32ccaa16b6e6b0613b739d6ec4820c80bbc4d409caf817d0b382b237`
(11318 bytes、正規化後 11314 bytes)。復元は各行末へ元の空白を戻す必要があり bytes 一致までは戻せないが、
可視文字列は `diff -w -B` で原文と一致する (実測 rc=0、2026-09-08)。原文は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2406-s4loop-gflags/evidence/attempt-0001/` に残る。

## 段 3 / 段 6 の所見と裁定

段 3 (2 レンズ、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`) と段 6 (2 レビュー、`verbatim/s6-reviewA.md`、
`verbatim/s6-reviewB.md`) の所見は `s4-adjudication.md` / `s6-adjudication.md` に裁定表がある。

- real・採用 (実装済み): TMPDIR / install dir の値束縛、検査面の実行面統一、事前構築への explicit prefix、
  TMPDIR / PATH の順序 marker、export 後 unset の拒否、コメント行の偽 heredoc opener、`CMAKE_PREFIX_PATH` 行の
  exact 3 行 allowlist (`export -n` / `env -u` を含む全形の拒否)、prebuild < driver 2 本、heredoc 内 fragment の
  コメントアウト拒否、README §7 の実測境界と `driver_rc` の説明。
- real・不採用 (scope 外、記録): `printf -v` / `read` / 名前分割 `eval` / 綴り難読化 / 行末コメントで marker を満たす形
  (本 wave 以前からの盲点、D387 の限界として明記)、`command -v` / `realpath` 失敗の生 rc、`-j 48` / 60 秒の bnode 実績
  (今回の実測で prologue は数十秒で完走)、README §7 の qsub 前 `cd "$REPO_ROOT"` と submodule PIN checkout 手順
  ([T-2407] へ持ち越し)。
- refuted: P3 (compiler の一致 — 同じ sanitized PATH で `compilers_for_current_site()` も gcc/g++ を解くので相対一致)、
  parametrize 登録と変異 matrix の混同。

## 変異 matrix

`tools/mutation_harness.py` (`--runner-mode dispatch`、runner = `tools/run_tests.py --force-dispatch
orchestrator/tests/test_p3_s4_loop_job_contract.py -q -rf`)、fix 統合 commit `a173f0ab5` の wave worktree で実走。
probe (全件 SURVIVED 登録で観測 node を採る) → 両層同時変異の追加 probe → 期待 node を埋めた本走、の 3 段。
spec と台帳の要約は `mutation/` (`mutation-spec-final.json` sha256 `a6ea974c…`、
`mutation-final-ledger-summary.json`)。

| 結果 | 値 |
|---|---|
| baseline | PASSED |
| 本走 | 17 変異、**KILLED 15 / SURVIVED 2**、MISMATCH 0、matching 17/17 (期待 node 完全一致)、rc=0 |
| SURVIVED (期待どおり) | m12 (出典コメントの文言変更 = 等価変異、harness の SURVIVED 検出の正例)、m13 (test 側 whitelist を「exact 1〜2 回」へ緩める) |

**m13 の生存は mask である。** fix で足した「`CMAKE_PREFIX_PATH` 行は exact 3 行」の検査が、旧 `prefix_assignments != [allowed]`
を完全に含意する (3 行が exact なら代入行は export 1 本しか残らない) ため、旧検査を緩めても受理集合は変わらない。
DW-M02 に従い両層同時変異 m17 (exact 3 行検査を `[:3]` に緩める + 旧検査を 1〜2 回へ緩める) を probe2 で追加観測し、
本走で KILLED (負例 `export -n` / `env -u` の 2 node) を確認した。2 本目の exact 行だけを足す負例は、さらに
`singleton_order` の回数検査 (第 3 層) が拒否するので、この 3 層は `CMAKE_PREFIX_PATH` 行に対して冗長である
(旧 `prefix_assignments` 検査は dead code に近いが、拒否を弱めないため残した)。

kill node 数が 44〜46 になる変異 (m01〜m04, m06, m09〜m11, m15) は、required fragment の欠落が
`test_registered_fragment_mutants_have_one_static_failure` の全 param (実 job body から派生させる) にも波及するためで、
帰属先の gate は各 1 つ (fragment) である。10〜11 node の変異 (m05, m07, m08, m14, m16) は whitelist / 位置 / unset の
検査に帰属する。

## 受入全走

この記録 commit を含む最終 tip に対して、land の前に `tools/dev_wave_wait.py acceptance` で 1 回走らせる (DW-O18/O26/O27)。
結果は記録 commit の後に確定するため本 README には書かない。受入 receipt (`acceptance-receipt-N.json`、
`tested_main` / `tested_tip` / `verdict`) と land 出力は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2406-s4loop-gflags/`
に残り、要約は wave 終端の報告と worklog エントリ (fold 後) に書く。

## 次 wave の出発点

- 次の一手 (slug `s4-loop-condition-gate-preprocess-on-compute`、番号は fold が付ける): 計算ノードでの condition gate supply arm (`preprocess-failed`) の
  原因を、gate の preprocess argv と stderr を evidence へ写す形で再現し、gflags/glog の include 経路との関係を確かめる。
  正しさ gate に触るので裁定パッケージで返す。
- [T-2407]: README §7 に submodule PIN checkout と qsub 前の `cd "$REPO_ROOT"` を足す (本 wave のレビュー B が同じ欠落を再指摘)。
