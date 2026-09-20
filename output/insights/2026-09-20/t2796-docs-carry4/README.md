# [T-2796] + [T-2794] + [T-2785] + [T-2407] — 裁定済み docs 追記 4 件と next-tasks command の 1 行是正を 1 wave で着地する (2026-09-20)

authority: none / default_effect: no-state-change。可変状態の正本は worklog 末尾と現行 phase doc。
wave: `dev-wave-t2796-docs4` (branch `worktree-dev-wave-t2796-docs4`、起点 local main `371674ea6`)。
専用 handoff は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2796-docs4/HANDOFF.md`。

## 1. 段 1 brief (親、12:45 JST)

- **研究前進:** 論文の主張・図表は変えない。土台の整備 — 次に K2 手動 loop (T-2795 の pair 投入・4 巡目)、B-10 の第 3 cohort、
  P3 段 4 の job 投入を login から行う者が、実測済みの rc=2 (3 ノード 1 投入の空振り、T-2794) と記述どおりに動かない手順 (T-2796 /
  T-2785 / T-2407) を踏まないようにする。完了判定 = 4 文書の該当箇所が実コード・一次資料と一致し、review 1 本の must-fix が 0 で land。
- **scope:** (1) `docs/phase3-s4b-runbook.md` T-2783 追補 手順 1 に login の直呼び形を足す (CLI 相当の 4 照合を省略させない)。
  (2) `docs/b10-backoff-static-tail-submission.md` §1 に hydrate 済み staging の前提を足す。(3) `docs/pegasus-runbook.md` §7.3 の
  `--merge-message-file` 記述 3 箇所を現行機構に揃える。(4) `tools/pegasus/README.md` §7 投入手順に submodule の PIN checkout を足す。
  (5) branch `worktree-next-tasks-cmd-mergebase-fix` (tip `ac0e5d4be`、`.claude/commands/next-tasks.md` 2+/1-) を merge で取り込む。
  scope 外 = 経路改修・新 gate・投入 script 側の検査追加・他 docs の一般化。実装面差分ゼロ (変異 matrix 免除)。
- **確定済み裁定:** D2172 項 9 (T-2796 / T-2794、AI 実施、CLI 相当の照合を省略させない書き方、経路改修・新 gate 含めず)、
  D1777 (T-2407、submodule を対象 PIN へ checkout する手順を足す)。T-2785 は entry 1659 起票の P3 (docs のみ、F588 型の消し忘れ) で
  裁定不要。(5) は skill-self-improvement の next-tasks 終端 (誤った既存命令の実測是正) で commit 済み、check_docs・provenance 通過済み。
- **brief 前の実測 (一次資料との一致):** T-2796 = `p3_s4_loop.py` で `_admit_env_contract(resolved_site)` が `if a.emit_planner_context:`
  より前、受理 site は `{OTHER, PEGASUS_COMPUTE}` のみ (login 拒否は実コードどおり)。CLI emit 経路の中身 = `_prepare_knowledge_campaign`
  (identity 束縛 + `knowledge_manifest.write_receipt` + K2 射影) → `planner_context_payload`。T-2794 = job body `b10_backoff_grid.sh` が
  staging root 配下の gflags / glog の pinned-clean を要求し無ければ `fail 2` (attempt 1 の 5 秒 rc=2 は entry 1690)。T-2785 =
  `dev_wave_wait.py` の `--merge-message-file` は任意、省略時は self-report (`role=integrator`) を使う。止まるのは指定 path が file で
  ないとき claim 前 `stage=merge-message-preflight` rc=2 と、behind 判明後に message 検証 (`AI-Agent:` 行) が落ちたとき
  `stage=merge-message` rc=70 の 2 経路。T-2407 = job body が CCBench HEAD と `p3_s4_loop.PIN` の exact 一致を検査する。
- **新事実 (裁定を覆さない):** PIN は 2026-09-10 `55d0f2399` で `511c9538e` へ前進し、main の gitlink と一致済み。D1777 が理由に
  挙げた「gitlink と PIN の不一致」は現行 main では成立しないが、§7 に submodule の checkout 手順が無い状態は不変で、専用 checkout の
  submodule が未初期化なら job body は rc=2 (`CCBench source root is unavailable`) — 手順追加の意味は残る。追記は不一致の有無に
  依存しない書き方にする。T-2785 の carry は「止まるのは `stage=merge-message` のみ」と書くが、指定 path 不在の preflight rc=2 も
  ある — 現行機構どおり 2 経路を書く (`(P1)` 親の provisional 裁定、review の攻撃対象)。
- **不変条件:** 対象 4 文書は凍結 pin・exact pin の対象外 (`check_docs.py` の pin 表に無し。`test_b10_backoff_grid_submit.py` は §2 の
  fence だけを読む)。`tools/pegasus/README.md` は admission drift 検査の対象 — 新しい `tools/pegasus/` path は書かない。
  `.claude/commands/next-tasks.md` は byte 予算 27,100 (取り込み後 27,060)。
- **成果物:** 4 文書の差分 + merge commit 1 + 本 README (brief・review 逐語・対応表) + worklog fragment。decisions fragment は不要
  (裁定済みの実施、新判断なし)。
- **分割方針 (軽量版):** 段 2・3 省略、親が docs を直接編集、段 6 に read-only review 1 本 (一次資料から事実を再抽出する docs-only の型)。
  実装子ゼロ。受入は待ち手経由 1 回、land は共通 operation。
- **受入・実測環境:** login node (pegasus) で check_docs・焦点 test、受入は計算ノード dispatch (待ち手)。

## 2. 段 4 裁定 (親、12:47 JST) と 13:00 の補正

- 軽量版: 段 2・3 省略。plan v2 = §1 の scope そのまま。変異 matrix は「実装面差分ゼロ」を前提に免除。裁定 inbox は 12:30 の第 25 回控えを
  再走査し、本 wave の 4 件に更新なし。review の攻撃対象 = (P1) と、T-2796 の「CLI 相当の照合を省略させない」書き方。
- **13:00 補正 (新事実):** 焦点走 attempt 1 (計算ノード、request `12472.nqsv`、HEAD `d6014c943`) が 838 passed / 3 skipped /
  **1 failed = `orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact` (`assert 27060 == 26950`)**。
  取り込み branch `worktree-next-tasks-cmd-mergebase-fix` は `check_docs` (予算 27,100) と provenance を通していたが、同 test が command
  file の**現物 bytes を独立 literal で pin** している (2026-09-17 `e9a4efeae` で導入) ことは検査していなかった。branch の取り込みは依頼の
  明示項目なので落とさず、pin literal 1 個 (26_950 → 27_060) を Codex `role=author` に追随させた (実装面、D95 決定 1・2)。これにより
  wave の実装面差分がゼロでなくなるため、変異 matrix の免除は成立しない — 先例 entry 1641 (check_docs literal 追随) の形で
  probe → final を走らせる (§5)。依頼文の「実装差分ゼロ・変異 matrix 免除」は前提が崩れたのであって、規律を緩めたのではない。

## 3. 変更の対応表 (一次資料 → 追記箇所、commit `6133b789f` → review 反映 `34017c27f`)

| 件 | 追記箇所 | 一次資料 | 要点 |
|---|---|---|---|
| T-2796 | `docs/phase3-s4b-runbook.md` T-2783 追補 手順 1 (行 139〜151) | `p3_s4_loop.py` L133〜146 / L1597〜1630 / L2965〜3011、`knowledge_manifest.py` L575〜613、round 3 insight 行 29〜54、D2172 項 9 | login では CLI 不可 (`_admit_env_contract` が emit 分岐より前)。直呼びは `k2_critic_diagnosis_from_bytes` → `planner_context_payload`、手順 3 の `k2_next_generation_inputs`。前提 (同じ manifest から受領証・射影、束縛 cfg から identity 再計算) + 4 照合 (受領証正準 bytes / identity preimage / K2 射影 bytes / tripwire)。経路改修・新 gate ではない |
| T-2794 | `docs/b10-backoff-static-tail-submission.md` §1 項 7 | `b10_backoff_grid.sh` L499〜540 (`dependency_policy_contract` の `fail 2`)、entry 1690 (attempt 1)、`tools/pegasus/README.md` §6 | hydrate 済み staging (既定 root `output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/`) を投入元 checkout に用意。投入 script は login で検査しない |
| T-2785 | `docs/pegasus-runbook.md` §7.3 (行 1015〜1027、1096) | `dev_wave_wait.py` L1676〜1682 / L3080〜3110 / L3787 / L3841〜3849 / L217〜221 / L613〜625 | `--merge-message-file` は任意、省略時は self-report (`merge main` + `role=integrator`)。message の事前確認・複製で止まる経路は preflight (rc=2) と merge-message (rc=70) の 2 つ。待ち手用 file の分離は渡す場合だけ |
| T-2407 | `tools/pegasus/README.md` §7 (行 377〜387) | `p3_s4_loop_pegasus.sh` L214〜255、`dev_wave_submodule_init.py`、`.gitmodules`、D1777 | 投入前に submodule を PIN へ checkout。手順 (1) 登録 worktree で tool 初期化 (2) PIN を投入対象 checkout の module から読む (3) 異なれば checkout。superproject は job body の submodule 除外付き tracked-clean 検査を満たす |
| (5) | `.claude/commands/next-tasks.md` 行 173〜174 (merge `d6014c943`) | branch tip `ac0e5d4be`、`/work/1/SFC/tanab/scripts/next_tasks_wave_impl_diff.sh` | 編集面重複検査を merge-base 基準へ。blob は取り込み元と同一 (`ff5fe7afa`) |
| pin | `orchestrator/tests/test_check_docs.py` 行 2560 (commit `30c7b34f0`、Codex author) | 焦点走 attempt 1 の赤 | 現物 literal 26_950 → 27_060。上限 27_100 と plus-one 拒否は不変 |

## 4. 段 6 review (read-only、1 本、gpt-6-astra、12:55〜12:59) — 裁定と逐語

親の裁定: **must-fix 2 / nit 5 = 全部 real で採用、(P1) は refuted (親の 2 経路が正しい) で任意修正を採用**。反映 commit `34017c27f`。

| # | 判定 | 対応 |
|---|---|---|
| 1 | real / must-fix | PIN の読み取りを `(cd "$REPO_ROOT" && python3 -B -c ...)` に固定 |
| 2 | real / must-fix | 4 照合の前に「同じ検証済み manifest から受領証と射影を生成し、束縛した cfg から identity の preimage と ID を再計算して選択 campaign に対応することを確かめる」を置く |
| 3 | real / nit | CLI emit 経路は `planner_context_payload` まで、`k2_next_generation_inputs` は手順 3 |
| 4 | real / nit | `[T-548]` の来歴主張を「現行 job body の前提」へ |
| 5 | real / nit | `knowledge-input.json` は前巡 insight の `materials/`、sha256 保存は「例」、attempt 1 の数値を削除 |
| 6 | real / nit | 「止まるのは 2 経路だけ」→「message の事前確認・複製で止まる経路は次の 2 つ」、旧機構文を削除、待ち手用 file の分離を「渡す場合」に限定。fence は変えない (指定例であって「任意」と矛盾しない、との所見どおり) |
| 7 | real / nit | tool の前提 (ローカル `.git/modules` を指す URL + file transport 明示許可) と「submodule 除外付き tracked-clean 検査を満たす」への言い換え |
| 8 | refuted / nit | (P1) 2 経路は実コードどおり。任意の限定文を採用 |

### 4.1 review 逐語

`output/insights/2026-09-20/t2796-docs-carry4/verbatim/review-1.md (原文 12302 bytes、sha256 `8d32b264cbddabfa…`、行末空白除去 35 行)`


## 5. 実走記録

- 焦点走 attempt 1 (12:50〜12:58、request `12472.nqsv`、HEAD `d6014c943`): rc=1、838 passed / 3 skipped / 1 failed (§2 の pin)。
  他 3 file (`test_b10_backoff_grid_submit` / `test_p3_s4_loop_job_contract` / `test_pegasus_calibration_workload`) は緑。
  13:0x に `tools/pegasus/README.md` の 1 文追加が走行中の tree に重なった (追加のみ、既存 assert 文字列は不変。権威は最終 tip の受入全走)。
- 段 5 author (Codex gpt-6-astra、13:09〜13:11、9 call、115 秒、unit worktree `t2796-unit-pin` base `34017c27f`): 1 literal の差分。
  pytest は login hook で未実走 (親が計算ノードで走らせる)。`check_docs` rc=0。報告逐語は §5.1。
- 焦点走 attempt 2 (13:13〜13:20、request `12479.nqsv`、HEAD `30c7b34f0`): 839 passed / 3 skipped、rc=0 (§5.2)。
- 変異 matrix (独立 clone `mutation-source` main=`30c7b34f0`、`tools/mutation_worktree.py`、dispatch): baseline PASSED・M1/M2 KILLED・M0 SURVIVED・MISMATCH 0 (§5.3)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、main 取り込み後の tip `917b72ee9`): rc=1、rr80 4 件 / rr20 4 件の hit は
  すべて起点 main `371674ea6` に既存の凍結候補 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*`、
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、commit `4d8fb93b7` / `cc82edc8c`) で本 wave の差分外。本 wave が足した file の hit は 0。
- main `947fd160a` (11 commit) を non-ff で取り込んだ (`917b72ee9`)。本 wave の編集 7 file と main の変更 37 file に重なりなし。
- F301 (編集面 path を key に pin している側の数え落とし) の再発として failures fragment を置いた。

### 5.1 author 報告逐語

`output/insights/2026-09-20/t2796-docs-carry4/verbatim/author-1.md (原文 1464 bytes、sha256 `9bdb52116e3d2a39…`、行末空白除去 0 行)`


### 5.2 焦点走 attempt 2

13:13〜13:20、request `12479.nqsv`、HEAD `30c7b34f0`、同じ 4 file: **839 passed / 3 skipped、rc=0** (skip は growth hold 3 件)。
attempt 1 の赤 1 件は pin 追随で消え、他の増減なし。

### 5.3 変異 matrix

spec (probe/final 共通の変異 3 件、`make_mutation_spec.py`):

- M0 `m0-equivalent-docstring` (positive): `test_check_docs.py` の対象 test の docstring に目印を足す → SURVIVED 期待 (等価対照)。
- M1 `m1-command-doc-drift-plus-one-byte` (negative): `.claude/commands/next-tasks.md` 行 8 の末尾に 1 byte 足す (27,061 bytes、予算内・literal 不変) →
  `test_next_tasks_command_budget_literal_is_exact` で KILLED 期待 (command 入口の無断変更を現物 pin が捕まえる)。
- M2 `m2-pin-literal-off-by-one` (negative): test の literal を 27_061 にする → 同 node で KILLED 期待 (pin が exact であり `>=` 等でない)。

走行 (独立 clone `mutation-source`、main = `30c7b34f0fc6ee7289b2328011d57d9cc7d449d7`、`tools/mutation_worktree.py` → `mutation_harness.py`、
`--runner-mode dispatch`、runner `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py -q -rf`):

- probe (13:14〜13:22、spec sha `00ddd71d…`、全件 SURVIVED 登録で観測 node を採取): baseline PASSED、M0 SURVIVED、M1 / M2 は
  `test_next_tasks_command_budget_literal_is_exact` 1 node で赤 (MISMATCH = 観測)。`mutation-probe-results.json` は job dir のみ (194054 bytes、sha256 `99efef276214490682a78dd2c83f3d7affda0927a52c568e1c163d02c013a32e`)。
- final (13:24〜13:31、spec sha `8ba24ef5…`): **baseline PASSED (rc=0、37.504 秒)、KILLED 2 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、matching 3/3**。

| 変異 | 種別 | 期待 | 結果 | 赤 node |
|---|---|---|---|---|
| `m0-equivalent-docstring` | positive | SURVIVED | SURVIVED | — |
| `m1-command-doc-drift-plus-one-byte` | negative | KILLED | KILLED | orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact |
| `m2-pin-literal-off-by-one` | negative | KILLED | KILLED | orchestrator/tests/test_check_docs.py::test_next_tasks_command_budget_literal_is_exact |

同梱 (`mutation/`): `mutation-spec-probe.json` (1693 bytes、sha256 `00ddd71dd56902e4…`)、`mutation-spec-final.json` (1897 bytes、sha256 `8ba24ef5926b3ea6…`)、`mutation-final-results.json` (173419 bytes、sha256 `0e765c6f6bb72366…`)、`mutation-final-attempts.json` (6214 bytes、sha256 `30f18476a1f29a9b…`)。
両変異は同一 node で殺しており、それぞれ「command file 側の drift」「test literal 側の drift」を単一理由で拒否する (DW-M03)。
M0 の生存は harness の正例 (等価変異を殺していない)。

## 6. 限界・言わないこと

- 4 件の追記は手順書の記述を実コード・一次資料に揃えたもので、経路・gate・投入 script は変えていない。追記の照合義務 (T-2796 の 4 照合) は
  親の手順義務であり、機械が発火する gate ではない。
- T-2407: PIN と gitlink は現行 main で一致しているが、追記はその事実に依存しない。D1777 の理由文 (不一致で rc=2) は現行に写していない。
- T-2785: 2 経路のほかに merge / provenance で止まる経路は別にある (runbook の同節に既載)。「止まるのは 2 つだけ」とは書いていない。
- 変異 matrix は pin literal と command file の 2 層を 1 node で見る最小構成であり、`check_docs.py` 側の予算 literal (27_100) の変異は含めない
  (本 wave が触っていない)。

## 7. 段 9 の組み直し (land rc=26 → main を第一親にした merge で再構成)

- 受入 final-1 (13:38〜13:51、tested main `947fd160a`、tested tip `c2da4de4d`): **child-green、25,602 passed / 69 skipped、red 0 / flake 0**。
- land attempt 1 (13:53): **rc=26 `fold-failed: declared fold verifier が拒否: landed-fold-owned-path`、main 不変** (`main_before == main_after`)。
  job dir の `find-fold-owned.py` (verifier と同じ規則) で区間 7 commit を再現すると、当たるのは merge `d6014c943` だけ — 両親
  (`6133b789f`、`ac0e5d4be`) とも main の祖先でないため verifier が全親との diff を取り、`ac0e5d4be` 側との diff に main のその後の fold
  (`docs/spool/FOLDED.md` の M) が現れる。memory `saved-branch-merged-state-cannot-land` (T-2724、2026-09-20) と同型。
- 対処: 旧 chain を branch `dev-wave-t2796-docs4-retired-chain` (tip `c2da4de4d`) へ退避し、同じ木で wave branch を main `947fd160a` へ
  reset → `ac0e5d4be` を main を第一親にして merge (`69e6483f5`、trusted parent 1) → 旧 chain の最終 blob をそのまま commit
  (docs 4 file `fc9416dde`、pin literal `0b7bd7e95` = Codex author trailer 保持) → 本 README・fragment を組み直し後の SHA で更新して
  記録 commit。docs / test の blob は旧 chain の最終 tip と同一 (`git diff c2da4de4d HEAD -- <path>` が空) なので、焦点走・変異 matrix
  (main=`30c7b34f0`、同 blob) は規律 7 のとおりそのまま成立し、受入だけ取り直す。
- 副作用: 同じ木で branch を reset したため、段 9 の `dev_wave_cleanup.py` は reflog 判定で拒否されうる (memory
  `single-worktree-branch-switch-blocks-cleanup`)。その場合は撤去を `/cleanup-branches` へ引き渡す。
- 旧 chain の commit SHA (§3・§4・§5 に記載の `6133b789f` / `d6014c943` / `34017c27f` / `30c7b34f0` / `917b72ee9` / `c2da4de4d`) は退避 branch
  上に実在し、内容の出所として有効。land される新 chain は `69e6483f5` → `fc9416dde` → `0b7bd7e95` → 記録 commit。
