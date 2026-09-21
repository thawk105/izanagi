# [T-2830] B-5 本走前の実装 — B-5 mode の node-local bench lock と、試走 launcher の job ごと submit-tree

- 日付: 2026-09-21 / branch `worktree-dev-wave-t2830-b5-node-local-lock` / base = local main `d99c556df` ([T-2795] 修復 wave の land を含む)
- 依頼: `verbatim/T-2830-origin.md` / 一次資料: `output/insights/2026-09-20/t2797-b5-contrast/README.md` §6・§8、D2199、D2200 項 1
- 実装: Codex author 2 本 (A1 = job body + 契約 test、A2 = launcher + test)。親は統合・README・記録

## 0. この wave が主張すること・しないこと

**主張すること:**

- B-5 mode の job body は driver 起動の直前に `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を設定し、B-5 driver (と環境を継承する slot の subprocess) が
  job 固有の node-local path を bench lock に使う。非 B-5 の 3 経路 (proposal 単独 / proposal + pair / fixture) の driver argv と環境は変わらない。
  test は実 shell harness の fake driver が観測した環境で固定した。
- 試走 launcher は arm ごとの検証済み checkout を `IZANAGI_S4_REPO_ROOT` と qsub の cwd の両方に使い、4 job が CCBench と build cache を共有しない
  配置で投入できる (D2200 項 1 (6))。

**主張しないこと:**

- **実機で lock の待ちが消えた・総 wall が縮んだ、とは言わない。** test が見るのは shell → driver の環境伝播までで、実際の flock 取得・待ち・性能は
  測っていない。効果の実測は本走 (または次の試走) の台帳でしか得られない。
- **B-5 本走が投入可能になった、とは言わない。** launcher は試走形 (write-heavy / series 1 / block 1 / 4 job、53 論理 session ≤ 60) に固定のまま。
  本走 (108 系列) 用の launcher、全 arm 同一 walltime、Tier0、事前登録 §12 の発効束は D2200 項 1 が列挙する別の AI 手番で、本 wave の scope 外。
  本走は未認可で、本 wave は何も投入していない。
- job 固有 lock は同じノードの別 process とは排他しない (machine-wide 排他からの縮小)。job 間の単独性は gen_S の割当てに依り、専有は保証外
  (`docs/pegasus-runbook.md` §1)。B-10 / A-5 と同じ限界。
- 試走 (β) の記録 (job body sha 9ef925d6… の `reservation.json` 4 件など) は当時の事実として保持し、無効にしない (規律 7)。

## 1. 置いたもの

| file | 差分 | 内容 |
|---|---|---|
| `tools/pegasus/p3_s4_loop_pegasus.sh` | +1 | B-5 分岐内、`b5_rc=0` と B-5 driver 起動の間に `export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` |
| `tools/pegasus/b5_contrast_launch.py` | +17 / −10 | `launch(jobs, trees_by_arm, ...)` (tree を command ごとに保持し env と cwd に使う)、CLI `--repo-root-<arm>` 4 本必須、docstring |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py` | +24 | fake driver が `TMPDIR` / `IZANAGI_BENCH_LOCK` を JSON lines で記録 (harness は外部の lock 値を除去)、B-5 は job 固有 path の完全一致、非 B-5 (default / pair) は未設定を assert |
| `orchestrator/tests/test_b5_contrast_launch.py` | +44 / −30 | 4 tree の fixture、argv / env の完全一致、submit の `(argv, cwd)` 照合、main の 4 引数と validator の呼出し順 |
| `tools/pegasus/README.md` | +12 / −5 | B-5 launcher の 4 checkout 手順と実行例、B-5 mode の lock 行と限定 (親) |

commit: 統合 `204eb77e6` (Codex author 2 本の所有 path 限定 patch + 親の README)、docs `092238a4c` (README の短縮、段 6 レビュー B)。

## 2. 契約 (段 4 裁定、`verbatim/s4-adjudication.md`)

- (P1) lock の適用範囲 = **B-5 mode 限定** (B-5 分岐内、driver 起動直前)。両レンズが支持。
- (P2) launcher = **job ごとの submit-tree** — D2200 項 1 (6) のユーザー裁定 (wave 開始後の 09:10 に land、段 4 直前の inbox 再走査で取り込んだ)。
- (P3) tree の供給と検証 = **呼出し側** (`main`) が 4 本を既存 `validate_submit_tree` で検証し、launcher は arm → tree の配線だけを持つ。
- 足さないもの: 4 path の重複・common repo 一致の拒否、argv の NUL bytes 記録、継承値専用 test、lock 行の新しい静的 pin。

## 3. 段 2〜4 の所見と裁定

- 段 2 plan (`verbatim/s2-plan.md`): P1〜P3 を採用し、`validate_submit_tree` に `previous_trees` (path 重複・common repo 不一致の拒否)、NUL bytes 記録 test、
  継承値 test、lock 行の静的 pin を提案。
- 段 3 相談 A (正しさ境界、`verbatim/s3-consult-A.md`): lock の被覆・規律 2・D2205 の維持は refuted (欠陥なし)。real = job 固有 lock は machine-wide 排他からの
  縮小で probe は原子的な代替保証でない (記述の限定)、59% は flock 待ちの直接測定でない (nit)、common repo 一致の拒否は不要な受入条件 (must-fix)。
- 段 3 相談 B (過剰・削除、`verbatim/s3-consult-B.md`): **brief の (P2) の根拠「lock を node-local にすると build の同時性が上がる」は誤り**
  (build は bench lock の外で走る)。tree 分離は「共有 cache の claim が待機・retry なしで失敗する」機序と D2200 項 1 で残す。`previous_trees`・NUL 記録・
  継承値 test・静的 pin・`launch` 内の git 検証は削れる。
- 段 4 裁定: 上記をすべて採用し、段 2 の追加提案 4 種を入れないプラン v2 を確定。変異 M1〜M9 を事前登録。

## 4. 段 5 実装と段 6 レビュー

- author A1 (`verbatim/s5-author-A1.md`) / A2 (`verbatim/s5-author-A2.md`): どちらも所有 2 file だけを変更、実装済み・未実走 (子は test を走らせない運用)。
  A1 は `bash -n` を hook に拒否され未実施と報告 → 親の焦点走 (`test_job_body_has_valid_stdin_shell_syntax` を含む) で確認した。
- 段 6 レビュー A (正しさ・実効性、`verbatim/s6-review-A.md`): **must-fix 0**。lock path の期待値は job body の `${PBS_JOBID//:/_}` 規則と独立に一致、
  観測の積み上がりなし、既存 3 経路の argv 完全一致と lock 未設定は全 parametrize で覆われる。nit = 変異帰属の補正 (§6 で反映)。
- 段 6 レビュー B (過剰・削除、`verbatim/s6-review-B.md`): **scope 逸脱なし**。nit = test の重複 2 点 (submit の runner 内 env 照合は後段の `(argv, cwd)`
  完全一致と重複、main dry-run の出力全体比較は必要より広い)、`Mapping` → `dict` (任意)、README の短縮、commit message の条件。
- 段 6 裁定: must-fix 0 のため実装の fix 巡は行わない。test の重複 2 点と型注釈は成果物の値を変えない nit として記録のみ (DW-G05)。
  README は親が短縮した (`092238a4c`)。commit message の「非 B-5 は未設定であることを検査する」は、harness が入力の lock 値を除去した条件での検査である。

## 5. 焦点走 (計算ノード dispatch、統合 commit `204eb77e6` の木)

| 走 | 対象 | 結果 |
|---|---|---|
| f1 (request 15058.nqsv) | 12 file — 変更 test 2、consumer 6 (`test_hooks.py`、`test_pegasus_tools.py`、`test_pegasus_calibration_workload.py`、`test_check_docs.py`、`test_ccbench_spawn_sites.py`、`test_plain_runner_coverage.py`)、inventory 4 群 (`test_campaign.py`、`test_official_perf_closure.py`、`test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py`) | rc=0、**2,074 passed / 9 skipped、失敗 0** (test 100.84 s)。skip のうち 3 は `test_check_docs.py` の growth hold |
| f2 (request 15059.nqsv) | 変更 test 2 本の単独走 (DW-O26) | rc=0、**223 passed、skip 0** (test 5.80 s) → f1 の 9 skip は変更 file 以外 |

統合後の `python3 tools/check_docs.py` は違反なし、全史 provenance 監査は 12,363 件で新規違反なし (rc 0)。

## 6. 変異 matrix

事前登録 = `verbatim/s4-adjudication.md` の M1〜M9 (段 4、実装前)。期待 node は DW-M08 の login self-run (`mutation/observe_mutations.py.txt`:
wave 木の統合 commit へ 1 件ずつ注入 → 変更 test 2 file の自走 harness → 復元し HEAD blob と照合、porcelain 0) で集め、
final は独立 clone (main = `092238a4c60aa8361f3652dea7463a6ec4eeb230`) から `tools/mutation_worktree.py --runner-mode dispatch` で走らせた
(spec sha256 e22163fdb77789c772488d24acf8509b3f2e20007b254095aecddf357ad721b5、結果 `mutation/mutation-final-results.json`
sha256 d1d503f727f28944de425aa1a1561b75af9ce7c9b3c12bedf7177a424da0bc63、2026-09-21 05:45〜05:57 UTC)。baseline は PASSED (失敗 0)。

| id | 変異 | final | 失敗 node | 単一理由か |
|---|---|---|---|---|
| M1 | B-5 の lock 行を削除 | KILLED | 10 (B-5 実 shell test 8 + stock-off 2) | 単一 (lock 観測だけ。静的 pin を足していないので他層は落ちない) |
| M2 | 値を `$HOME/.izanagi/bench.lock` | KILLED | 10 (同上) | 単一 |
| M3 | export を `export TMPDIR=$scratch` の直後 (job 全体) へ移動 | KILLED | 8 (非 B-5 の default 6 + pair 2)。B-5 側は緑 | 単一 |
| M4 | `export` を外す (shell 変数だけ) | KILLED | 10 (B-5 と同じ 10) | 単一 |
| M5 | launcher の env 側 tree を `trees_by_arm["random"]` 固定 | KILLED | 3 (dry-run / main dry-run / submit[0]) | 単一 |
| M6 | launcher の qsub cwd を先頭 tree 固定 | KILLED | 1 (submit[0] の runner 内照合) | 単一 |
| M7 | pair の `pair_argv=(--stock-control)` を空配列 | MISMATCH (81 vs 登録 51) | 81 | **過剰決定** (STOCK_PINS の静的 pin・fragment メタ test にも掛かる) |
| M8 | fixture の既定 `:-20` を `:-21` | MISMATCH (76 vs 登録 46) | 76 | **過剰決定** (同上) |
| M9 | proposal 経路の `--isolate-worktree` 削除 | KILLED | 7 (proposal / K2 の default 4 + pair 2 + K2 空白 manifest 1) | 単一 (既存 3 経路の argv 固定の実証、proposal と pair) |
| M10 | fixture 経路の `--isolate-worktree` 削除 (段 6 の差し替え) | KILLED | 3 (fixture の default 2 + `test_fixture_driver_before_prebuild_is_rejected`) | 挙動の検出は fixture 2 本。3 本目は test 自身の前提 (`source.count(fixture_driver) == 1`) が崩れる meta 失敗で、job body を拒否する層ではない |

**erratum (初回結果は消さない、DW-M02):**

- **M7 / M8 は登録から外す。** self-run の観測 (51 / 46 node) の時点で静的 pin とメタ test に掛かる過剰決定と分かり、DW-M01 / M03 に従って
  単一理由の証拠から外すと final 投入前に決めていた (fixture 経路の単一理由は差し替えの M10 が担う)。final spec には診断として残したが、
  期待集合が不完全で MISMATCH になった。**余剰 30 node はすべて parametrize id に空白を含む fragment メタ test**
  (`test_b5_fragment_mutants_have_one_static_failure` 18、`test_registered_fragment_mutants_have_one_static_failure` 8、
  `test_stock_fragment_mutants_have_one_static_failure` 4) で、親の self-run probe の regex `\S+?::\S+?` が空白で切れて取りこぼした。
  検出の欠陥ではなく登録の欠陥で、harness の完全一致比較が fail-closed で捕まえた (F71 型の再発。新しい F は作らず F71 へ再発を追記する)。
  M7 / M8 の final2 は走らせない (単一理由の証拠に使わないため)。
- self-run 1 回目 (14:25 JST) は pytest の ANSI 色付けで `FAILED` 行が regex に一致せず、M1 で「rc=1 だが抽出 0」の fail-closed 停止
  (`mutation/` 外の job dir log)。復元は正常 (porcelain 0、HEAD blob 一致)。`PY_COLORS=0` と ANSI 除去で 2 回目を取り直した。
- M10 は段 4 の事前登録に無く、段 6 で M8 の過剰決定を受けて再照準した差し替え (DW-M03)。

**段 6 レビュー A の帰属予測との照合:** M1〜M6・M9 の予測 node 集合は final の観測と一致した (M5 の検出は単体 exact test ではなく dry-run / submit /
main、M6 は runner 内 assert、M7・M8 は静的 pin と meta にも掛かる、の 3 点の補正も観測どおり)。

## 7. 受入全走・検査

- **段 6 の中間受入 (tag final、attempt 1):** 門番付き受入 script (t2288 → t2795 → t2830 の写し、shards 3)。門番は 15:01 JST から他の受入 leader 2 本で閉じ、
  15:48:59 に開いて投入。投入直前に local main `a8ae5f5d6` (25 commit 前進、docs と他 wave の land) を自動 merge (`fa767882b`、競合なし)。
  **child-green、26,964 passed / 69 skipped、赤 0** (tested main `a8ae5f5d618c0de213874dd4f26db343b546b398`、
  tested tip `fa767882b5498e97f2bf93a75afd81482969f651`、16:12:23 終了、受領証 `acceptance-receipt-final-1.json`)。
- この受入は記録 commit の前の tip に対するもの。land は tested tip の後に main の前進 merge しか置けない (`tools/dev_wave_land.py` の RC_AUDIT、
  T-2797 の land rc=23 が先例) ので、DW-O12 に従い段 7・8 の記録 commit を含む tip へ最終受入を投げ直す。**最終受入は本 commit の時点で未実施**で、
  その結果は repo に書き足さず (書けば tested tip からまたずれる)、job dir の受領証と land の記録に残す。
- `python3 tools/check_docs.py`: 統合後・README 短縮後とも違反なし。全史 provenance 監査: 統合 commit 後 12,363 件で新規違反なし (rc 0)。

## 8. scope 外の記録・限界・次の一手

- **起票しない scope 外 (DW-S04: 研究前進・実測欠陥を示せないので insight 記録のみ):**
  - launcher 自身による path 重複の拒否。同じ path を 4 回渡すと共有 cache に戻るが、実測された欠陥はなく、依頼が検査の追加を除外している。
    README の手順 (arm ごとに 4 checkout を用意する) が担う。
  - 段 6 レビュー B の test 重複 2 点 (submit の runner 内 env 照合、main dry-run の出力全体比較) と `Mapping` → `dict`。成果物の値を変えない nit。
- **本走までに残る AI 手番 (D2200 項 1 が列挙、本 wave の外):** 本走 (108 系列) 用 launcher、全 arm 同一 walltime (§3.3)、Tier0 (§3.1)、
  LLM arm の親運用、事前登録 §12 の発効束 (exact model ID の機械記録を含む)。完成した束と倍率・発効 commit・投入は AI が 1 行で再提示し
  ユーザーが承認する (D2200 項 1 (3))。本走の対象 commit は本 wave の land を含む main 以降。
- **効果の実測は未了:** node-local lock で lock 待ちが消えるか、並列 job で総 wall が縮むかは、次の試走か本走の台帳 (performance verify の初回 rep と
  bench 周辺 wall の差) で確かめる。試走では「初回 rep 215〜913 s、2〜5 回目 34〜91 s」「bench 周辺最大約 1,060 s」が lock 待ちの型だった (insight t2797 §6.3)。
- **限界:** job 固有 lock は同一ノードの別 process とは排他しない。gen_S の割当て (48/48) の前提が崩れて同居が起きれば、検知できなければ性能値が汚れうる
  (段 3 相談 A 項 3)。単独性の確認は従来どおり計算ノード上の probe の役割で、原子的な排他の代わりにはならない。

## 9. 一次資料

- 依頼・brief・裁定: `verbatim/T-2830-origin.md`、`verbatim/brief.md` (追補 2 まで)、`verbatim/s4-adjudication.md`
- codex 入出力: `verbatim/s2-plan{-prompt,}.md`、`verbatim/s3-consult-{A,B}{-prompt,}.md`、`verbatim/s5-author-{A1,A2}{-prompt,}.md`、`verbatim/s6-review-{A,B}{-prompt,}.md`
  - **可逆な最小正規化 (DW-S07):** `verbatim/s5-author-A2.md` は原文の 1・13・22 行目末尾に Markdown 改行用の空白 2 個があり `git diff --check` に抵触したので
    除いた。原文 sha256 71296093810010df9b2f857bd0d476a2c7cbbce42347ebbfd840b723e2029a8e (3,030 bytes) → 正規化後 3,024 bytes。
    復元法: 同 3 行の行末へ半角空白 2 個を戻す (可視文字は不変、戻した bytes が原文と一致することを確認済み)。
- 変異: `mutation/` (spec 生成器・self-run probe の写し、観測 node `observed-nodes-m1-m9.json` / `observed-nodes.json`、final spec と結果)
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/` (HANDOFF.md、codex artifact と receipt、焦点走 log `focus-f1.log` / `focus-f2.log`、
  self-run log `observe*.log`、変異の独立 clone と scratch、受入の chain log・受領証)
