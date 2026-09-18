# [T-2498] guard_bash の重量判定を script-executor の内側実行対象へ層ごとに適用する (D1891)

`python3 -m cProfile / profile / pdb / trace / runpy / coverage run` を挟んだ pytest 起動が Pegasus login
判定を素通ししていた穴を、D1891 の裁定どおり「既存 parser が抽出した内側の実行対象へ同じ重量判定を適用する」
形で閉じた。wrapper module・option の列挙は足していない。

- wave branch: `worktree-dev-wave-t2498-executor-recurse`
- 実装 branch (D427 の第 2 worktree、base = 有効化前 commit d92800f49): `impl-dev-wave-t2498-guard`
- base: `38353207f` (着手時の local main)。段 7 前に local main `d2ebef7a4` を merge (`339ef718d`)
- 実装 commit (実装 branch、そのまま着地): `f0abd7f60` (docs 同期)、`1f0594712` (単位 A、guard_bash.py)、
  `ddb6b760f` (fix A2、反復化)。wave 側 (作業時の SHA): `f94fde871` (単位 B、test)、`abee732be` (fix B2、test 3 関数)、
  `301dab228` (README)、`524adc529` / `488223a08` (記録)。作業時の merge: `4b9f1c631`、`d5c4b45f7`
- **着地形 (F266 対応、下記「手順」参照):** main `d2ebef7a4` を第 1 親とする 1 つの merge `954dd6680` (差分は
  hooks/guard_bash.py だけ) の上に、wave 側 5 commit を cherry-pick (`3000a9031`、`bbe8964d2`、`4c036a5d9`、
  `bbc9e08ee`、`444f5e36c`) + 本追補。tree は作業時の tested tip `488223a08` と同一 (git diff 空)。
- `hooks/guard_bash.py` の最終 blob: `7076a4ad7`、`orchestrator/tests/test_hooks.py`: +123 行 (9 関数)

## 着手前の実測 — 何が開いていたか

現行 main (38353207f) の `decide(cmd, root, site="PEGASUS_LOGIN")` 直呼び:

- DENY: `python3 -m pytest -q` (interpreter の baseline 重量対象)
- ALLOW (素通し): `-m cProfile -m pytest`、`-mcProfile -mpytest`、`-m profile -m pytest`、`-m coverage run -m pytest`、
  `-m pdb -m pytest`、`-m trace --trace --module pytest`、`-m runpy pytest`、`-m cProfile -m cProfile -m pytest`、
  `-m cProfile -m cmake --build build`
- 機序: `_script_executor_targets` が repo 外 module (`pytest`) を空に落とし、`_python_pytest_args` が最初の `-m`
  (cProfile) しか見ない。`-qmcProfile -m pytest` (密着) は baseline の first-token 判定が `pytest` を拾って
  旧版でも DENY。

## 実装

- 共有 prefix `_script_executor_arguments` (coverage の `run` 副命令と option 表の選択) と抽出器
  `_script_executor_program` (`(kind, value, rest)` または None。multi-target の pydoc / doctest / unittest は
  対象外、module 名は `_PYTHON_MODULE_RE` に一致するときだけ、help / `trace --report` / program 不在は None)。
- `_heavy_segment_violation(…, peel_executors=True)` の入口だけが層を剥き、剥いた各層の合成 segment
  (module: `[raw_head, "-m", value, *rest]`、script: `[raw_head, value, *rest]`、`-` 始まりは `--` 補完) に
  `peel_executors=False` で同じ全 gate を当てる。位置は shell command-string 再帰の直後、sanctioned 早期許可の前。
  **反復で深さ上限なし** (各層の引数は前層の正規形 args の真の suffix)。
- `_script_executor_targets` の返り値は不変 (実装子が 5,302 入力で一致を実測、レビュー A が 5,577 入力で 0 差)。

## 段 6 が見つけたもの

- **レビュー A (NO-GO → fix):** (1) `-m cProfile` を 1,100 層重ねた 13 KB の入力で段 5 の再帰実装が
  `RecursionError` になり、`main()` の例外経路 (防護 path を含まない入力は rc 0) が後続 segment の `pytest -q` を
  検査せず**許可**する — `decide()` の戻り値だけを比べる反転検査では捉えられない実入口の deny→allow。
  親が再現 (1,100 層: EXC、300 層: DENY、旧版は両方 DENY)。→ fix A2 で層剥きを while 化 (F709 の型)。
  (2) script 形 (`-- -m pytest`、`/tmp/safe.py -mpytest`) が合成後の既存 residual で新たに拒否される。直接形は
  旧版でも拒否 (包み形だけが穴だった)。→ 契約を「内側 segment は直接形と同じ判定」と固定し、fix B2 で包み形と
  直接形の受理 bit の一致 test (7 組、値は pin しない) を足した。
- **レビュー B (GO):** M8 (層剥きを sanctioned 早期許可の後へ) は corpus 上 SURVIVED 対照だったが非等価 —
  識別入力 `python3 -m cProfile tools/run_tests.py -m pytest -q` (現物 D / M8 A) を見つけた。→ fix B2 で専用 test を
  足し M8 を KILLED 期待へ。M4 は過剰拒否 + 2 重 wrapper 素通しの 2 理由、M6 / M7 は既存 test が守る。
  内側の `-h` / `--co` が非実行と扱われないのは既存 `_pytest_nonexecuting` の境界 (直接形も同じ) → backlog。
- **焦点再レビュー (GO):** A1 / A2 / B4 closed。新規 must-fix なし。

## 実測 (すべて親が実行)

| 検査 | 結果 |
|---|---|
| 単位 B の新 test を段 5 前の guard へ (計算ノード 4913.nqsv) | 3 failed (負例) / 3 passed (正例) = 新 test が変更前 HEAD で差分を検出 (DW-M08) |
| 統合後焦点走 (login、xdist) | 762 passed / 41 failed / 1 skipped。41 件は全部 `test_codex_worker_launch` の F57 型 (evidence 猶予 1.0 秒、`codex_exit_code=-15`) |
| 同 file 単独を計算ノードへ (4914.nqsv) | 211 passed / 9.03 秒 → 41 件は非帰属 (DW-O18) |
| fix 後焦点走 5 file (計算ノード 4929.nqsv) | **806 passed / 1 skipped / 0 failed、81.4 秒** |
| D428 反転検査 (fix 前、corpus 345 × 4 site) | deny→allow 0、allow→deny 54 |
| D428 反転検査 (fix 前、拡張 corpus 383 × 4 = 1,532、例外を別枠) | deny→allow 0、**例外 6** (深い 1,100 層 × 3 case × LOGIN/SUSPECT、旧版は例外なし) |
| D428 反転検査 (fix 後、同 corpus、`d428-inversion-final.json`) | **deny→allow 0、例外 0**、allow→deny 90 (45 command × LOGIN/SUSPECT、OTHER/COMPUTE は 0) |
| 変異 probe (段 5 tip、10 走) | baseline PASSED、観測 node は両レビューの予測と一致 |
| 変異 probe (fix 後 tip、11 走) | baseline PASSED、M1〜M9 全部赤、M8 は `precedes_sanctioned_allow` だけ (単一理由) |
| **変異本走 (最終 tip 301dab228、11 走、計算ノード、`mutation-final-result.summary.json`)** | **baseline PASSED (28.1 秒)、9/9 KILLED で期待 node と観測 node が完全一致 (matching 10/10)、等価 M0 SURVIVED、MISMATCH 0、TIMEOUT 0** |

allow→deny 45 command の内訳: 重量 module 形 (pytest / cmake / ycsb_silo.exe / perf を内側 module に持つ、
綴り差・env・nice・bash -lc・2〜3 重 wrapper 込み) が大半、script 形 7 件 (`-- -m pytest`、`/tmp/safe.py -mpytest`、
`-- -W pytest`、`-- pytest -q`、`pytest -q`、`tools/run_tests.py -m pytest -q` ×2、いずれも直接形も拒否)、
`-m pytest -h` / `--co` 2 件 (既存境界)、深い 1,100 層の `-m pytest` 1 件。

変異の専属 killer と扱い: M1 (層剥き入口) → 負例 3 + deep + precedes + matches_direct (6 node)、M2 (module 形) → 4、
M3 (coverage run) → `coverage_denied` のみ、M4 (`*rest` 落とし、**2 理由**、単独証拠に数えない) → 4、M5 (script 形)
→ 3、M6 (`_PYTHON_MODULE_RE`、既存 test と冗長) → 既存 `nonexecuting_modes_restore_baseline_allow` + 新規正例、
M7 (multi-target 除外、既存 test が守る) → 既存 pydoc test のみ、**M8 (層剥きの位置) → `precedes_sanctioned_allow` のみ**、
M9 (1 層で打切り) → `module_denied` + `deep_nesting`。M0 (docstring) SURVIVED は harness の生存報告の正例。

## 手順 — D427 の第 2 worktree と launcher

hooks/ は現行 main ではどのツールからも編集できないので、有効化前 commit d92800f49 を base にした第 2 worktree
(`.claude/worktrees/dev-wave-t2498-guard-impl`) で Codex author が書き、親が統合 commit → wave へ `-X theirs` merge →
blob 一致検算 (D427 / D1719)。本 wave で加えた 2 点 (decisions 参照): (1) 親が `AGENTS.md` / `CLAUDE.md` /
`docs/dev-wave/` を現行 main へ同期する docs-only commit (`f0abd7f60`) を先に作る、(2) 起動は現行 `dev_wave_codex.py
--dry-run` の argv で launcher だけ現行版へ差し替える (旧 launcher は現行 argv を受けず、旧 docs 権威は superseded 済み
`gpt-5.6-sol` を導出する。同期後の第 2 worktree で `gpt-6-astra` / `medium` を導出し `validate_installation` findings 0 を
起動前に実測)。

**着地形は F266 が決める。** 作業時は実装 branch を wave branch の途中で 2 度 merge した (`4b9f1c631`、`d5c4b45f7`)。
その形で受入は child-green (24,833 passed) だったが、land は rc=26 `fold-failed: landed-fold-owned-path` で止まった
(main は 1 bit も動いていない)。原因は F266 そのもの — これらの merge は両親とも main の祖先でない (trusted 親 0)
ので land の verifier が両親と差分を取り、旧 base (5 週間前) 以降に main で起きた fold の署名 (FOLDED.md の変更・
fragment の削除) を wave の変更として読む。T-2146 も 1 回目に同じ rc=26 を踏んでいる。対処は F265/F266 の恒久対応
どおり: main から新 worktree を作り、実装 branch を **main を第 1 親とする 1 つの merge** で取り込み (docs 入口は
main 版へ戻す)、その上に wave 側の commit を cherry-pick で積む。受入はこの tip で取り直した。

## 主張の上限 — 何が閉じていないか

- 閉じたのは「既存 parser が抽出できる内側 program」だけ。subprocess の内側・script file 越し・変数展開・
  `python3 -c` は D103 / D105 のとおり原理的に見えない。
- 内側の `-h` / `--co` は既存 `_pytest_nonexecuting` の境界で非実行と扱われない (直接形も同じ、backlog)。
- `main()` の例外経路 (防護対象を含まない入力の例外は rc 0) は変えていない。本 wave は例外を起こさない実装で
  穴を閉じた。この方針の再検討は別の裁定面。
- `trace -m` (短形) は既存 option 表に無いので script 扱いになり、結果として保守的に拒否される。

## 収録物

- `verbatim/` — 段 1 brief、段 4 裁定 v1 / v2、段 5 実装子 2 本、段 6 敵対レビュー 2 本・fix 2 本・焦点再レビューの逐語。
- `mutation-probe-stage5.json` / `mutation-probe.json` / `mutation-final.json` — 変異 spec (段 5 probe、fix 後 probe、本走)。
- `*-result.summary.json` — 変異台帳の要約 (stdout を除く)。
- `d428-inversion-final.json` — 最終形での D428 反転検査の生結果 (runner と fix 前の結果は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2498-executor-recurse/` に保全)。
