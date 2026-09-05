# [T-2298][T-2273] 受入全走の最遅 shard を 5 分以内へ
- 目的: certified_evidence の lock を seed 排他→読み手共有/書き手排他へ変え (T-2298)、shard-0 の律速の内訳を先に測る (T-2273)。
- 状態: 作業中
- 最終更新: 2026-09-04 22:20 JST
- 基準コミット: 1b7822110c54536f82ecab8d058d7a9253bfd3ce (local main、fresh worktree `worktree-dev-wave-t2298-certified-evidence-lock`)
- job dir: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/
- worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock (locked by session)

## 段 1 brief

### scope
- (1) T-2298: `orchestrator/tests/test_p3_b4_raw_record_producer.py::certified_evidence` (1178-1239) の
  lock を「seed 生成だけ排他、以後は読み手 LOCK_SH / 書き手 LOCK_EX」へ変える。17 consumer の期待値は変えない。
  書き手は現物で M17 (`on_receipt` を一時上書き) と M18 (`role_file` を symlink へ差替) の 2 件。
- (2) T-2273: shard-0 律速の内訳を先に測る (実装しない)。測定 2 本:
  - M-A: 受入 shard-0 の「wall − 最大 worker 占有」= 95〜207 秒の正体 (lock 待ち / collection / teardown)。
  - M-B: t080 stub-free e2e (145〜153 秒/node、ledger 55 秒) の phase 内訳 (copytree / output copy / submodule add / git add+commit / receipt 発行 / verify)。
- (3) T-2297 は main 未 fold (conftest 2004 は group marker を全 resource node へ付ける)。→ (1)(2) だけ。
- scope 外: 新規 gate・台帳・framework、`test_s8b_floor_campaign.py` の編集 (t2262 稼働中)、恒久 skip・被覆削減。

### 確定済みユーザー裁定
- D1618 (T-2297 承認、shard affinity 全 node 保持、読み手だけ外す形は不可、lock 意味論に正例・負例)。
- D1620 (5 分の測定面 = canonical 起動の receipt の最遅 shard wall、queue 待ち別欄)。
- D1594 (排他は lock、xdist group で代用しない)。D95 (実装面は Codex author)。規律 2。

### brief 前の実測で覆った前提 (段 4 で再裁定)
- (P1) 引数「既存 real_repo_fixture_lock を使う」: 同 fixture は resource ∈ {parent, ccbench} の git common-dir を
  key にする lock であり、b4 evidence の共有 tmp とは別資源。流用は資源の取り違え。**provisional 裁定: fixture 自前の
  `fixture.lock` を残し、mode を LOCK_EX(seed)→LOCK_SH(reader)/LOCK_EX(writer) に変える。攻撃対象。**
- (P2) 「258.1 秒の直列」: ledger 由来。当日 21:16 の junit (setup+call+teardown 込み) では 17 consumer の合計 ≈ 82 秒、
  最大 3 本が 16〜19 秒、他は 0.7〜7 秒。鎖は存在するが 258 秒ではない。実装の価値は worker-time と tail の削減。
- (P3) D1593「鎖 1 = real-repo group 303.7 秒が 1 worker 直列」: conftest 2061 の `_strip_real_repo_loadgroup_suffix`
  (commit 5ac638955、2026-08-26) が process-memo 4 node 以外の `@real-repo` suffix を剥がすため、xdist は group 化しない。
  shard-0 report.json の group_to_workers で real-repo は 26+ worker に散っている。**D1593 の鎖 1 は裁定時点で既に不在。
  T-2297 (D1618) の実装対象も現物と食い違う。** 本 wave の scope 外だが裁定パッケージとして報告する。
- (P4) shard-0 の wall 分解 (当日 9 走): wall 251〜412 秒、最大 worker 占有 149〜234 秒 (2 item)、shard 1/2 の
  wall−占有 は 57〜73 秒で一定、shard-0 は 95〜207 秒。占有は setup/call/teardown の和なので
  `pytest_runtest_protocol` wrapper 内の real-repo lock 待ちは占有にも junit にも出ない。→ M-A で測る。
- (P5) t080 e2e は build でも直列性検査でもなく、orchestrator 全体 + output の copytree、CCBench submodule add
  (clone)、git add -A/commit、verify (git 走査) の filesystem/git 仕事。→ M-B で phase を測る。

### 不変条件
- 17 consumer の assertion・期待値・受理集合を変えない。skip/deselect/case 縮小/timeout 緩和で短くしない。
- 書き手 (M17, M18) は必ず LOCK_EX。読み手は LOCK_SH。seed 生成は LOCK_EX + 生成後の再確認 (double-check)。
- lock の意味論に正例 (読み手 2 者同時成立、seed 済みなら読み手は排他を取らない) と負例 (読み手保持中に書き手 NB は失敗、
  書き手保持中に読み手 NB は失敗、writer 未宣言のまま共有 path を書く test は無い = 書き手集合の pin) を付ける。
- 変異 (事前登録、段 4 で確定): (a) 書き手を LOCK_SH にする、(b) 読み手が lock を取らない、(c) M17/M18 の writer 宣言を外す、
  (d) seed 生成の double-check を外す (競合で二重生成)、(e) 読み手が LOCK_EX のまま (旧挙動、性能退行) → 正例で KILLED。
- 測定は計算ノードで行う (pytest は login で hook 拒否)。測定 script は repo 外 (`$CLAUDE_JOB_DIR/tmp`)、commit しない。

### 成果物
- コード: fixture 変更 + writer 宣言 (marker) + 正例・負例テスト (同 file か conftest 近傍)。Codex author。
- insight: `output/insights/2026-09-04_t2298-t2273-shard0-critical-path/` に M-A/M-B の実測と (P3) の反証。
- spool fragment: worklog / decisions (P3 を裁定パッケージへ) / failures (D1593 が現物を読まずに鎖を数えた型)。

### 並列分割
- 段 2: codex plan (read-only) 1 本 (T-2298 の file:line 粒度 plan + writer 集合の現物確認)。
- 段 3: 敵対 1 本 (lock 意味論と writer 閉包の漏れ)。軽量版だが設計択一 (P1) が割れるので省かない。
- 段 5: codex author 1 本 (T-2298)。同時に親が M-A/M-B を計算ノードへ dispatch (実装と独立)。
- 段 6: fix 子 (必要時)、変異 matrix、受入全走 (canonical、K=3)。

### 実測環境
- Pegasus login (pegasus02) から `tools/pegasus/dispatch_compute.py --task generic` で計算ノード gen_S へ。
  受入は `tools/dev_wave_wait.py acceptance` canonical (D1620)。

## dev-wave 改善候補
- (候補 2) 親が測定 job を worktree から dispatch している最中に段 5 の実装子が同 worktree を編集し、
  M-C の p3_b4 file の値と赤 1 件が HEAD のものでなくなった (計測汚染)。「段 5 の子が走る間、親は
  その worktree を cwd にする dispatch を起動しない」を DW-S05-A か DW-M05 近傍へ (段 8 で裁定)。
- (候補 4) 焦点走 3 回目が login 側 local 試行中に MemoryMax へ達し、その最中に親が `git add` した (index の変化で
  `git status` の digest が変わる) ため自動 fallback が止まり rc=16。「run_tests の走行中は index を含め木を触らない」を
  候補 2 と同じ節へ。焦点走 4 回目は木を触らず再投入 (前回 cap 記録で即 dispatch のはず)。
- (候補 3) `.done` の残骸で Monitor が即発火した (M-B 再投入時)。DW-O01 の「既存 .done を消去」を
  再投入 launcher の定型 (`rm -f *.done` を script 先頭) に入れる。本 wave は run-stage6-review.sh で実施済み。
- (候補 1) D1593 の鎖 1 は marker 付与 (conftest 2004) だけを読み、同 hook 末尾の suffix strip (2061) を読まずに数えた。
  「直列鎖を数えるときは group_to_workers / worker_occupancy の現物で確認する」を DW-S01 の実測義務の例として足すか (段 8 で裁定)。

## 完了した中間成果
- クラス 3 起動、DW-C00/C01/STOP/S01/G01-G05、DW-O08/O09/O10/O20、skill-self-improvement 読了。
- 資料: entry 1231/1241/1260、D1593/D1594/D1618/D1620/D95、T-1933 insight、当日 9 走の junit + report.json。
- worktree 作成、submodule 初期化 rc=0。

- 開始 gate rc=0 (22:25 JST)。
- 段 2 plan 子投入 (pid 1022062、job-id s2plan-t2298-1、prompt `prompts/stage2-plan.md`、出力 `artifacts/stage2-plan-out.md`)。
- M-A (全 suite timeline、`measure/run_a.py` + `tl_plugin.py`) を generic dispatch、PBS 977107.nqsv、RUN 中 (22:41)。
  出力は `measure/out-a/timeline-*.jsonl`、`pytest-*.log`。
- M-B (t080 phase 内訳、`measure/run_b.py` + `phase_plugin.py`) を generic dispatch (pid 1060743)。出力 `measure/out-b/`。
- Monitor btts845sp が `measure/a.done` / `measure/b.done` / `logs/stage2-plan.done` を見張る。

- 段 2 完了 (22:31、accepted、9 model calls、504 秒、check_codex_output rc=0)。plan は B2 (別 fixture
  `certified_evidence_writer`)、seed EX + double-check + 明示 UN → SH/EX、正負例 5 本 + writer 閉包 AST。
  未証明点 1 件 (producer の共有 path 書込) は親が現物で確認: `campaign_lock` は terminal record 不在時だけ、
  seed は terminal="commit" なので発火しない。artifact/ledger は publication root (tmp_path) 配下。
- M-B は orphan hold (M-A の pending hold) で rc=16。M-A 完了後に再投入する。
- 段 3 lens A (正しさ境界、pid 1194636) / lens B (整合・実効性、pid 1196219) を投入 (22:35)。

- M-A 完了 (22:29、bnode095、wall 487 = collection 119 + test 361 + 7、隠れ待ち 0)。結果は `artifacts/measurements-draft.md` §4b。
- M-B 再投入 (PBS 977142、pid 1291762)。M-C (shard-0 の 111 file、`measure/run_c.py`) を M-B 完了後に自動投入する
  launcher (pid 1403319) を起動。Monitor: bm3gimshb (b.done)、blsy0alnj (c.done)。
- 段 3 完了 (22:47〜22:52、lens A 12 calls / lens B accepted、check_codex_output rc=0)。
- 段 4 裁定を `artifacts/stage4-adjudication.md` に確定 (P1 refuted・自前 lock、P2 台帳値・効果は worker-time、
  P3 は現行 run で反証・D1593 起草時点で strip は祖先、P4 関連のみ、lens A must-fix 2 件採用、変異 a〜g 事前登録)。
- midflight gate rc=0 (22:56)。段 5 author 投入 (pid 1448322、job-id s5author-t2298-1、max-model-calls 400)。Monitor b6iyz9doz。

- 段 5 完了 (accepted、22 calls、対象 file のみ 544+/40-、検査 9 本、`artifacts/stage5-diff.patch`)。
- M-B 完了 (bnode019、5 passed x 2 rep): t080 は build/直列性検査でなく、受領証発行の子 python 30 秒 + git add 7 秒 +
  output 複製 ≈ 10 秒 + verify 2〜12 秒。M-C 完了 (bnode080、shard-0 の 111 file、wall 250 = collection 56 + test 190)。
  M-C は実装子の編集中に走った汚染 (m18 赤 1 件は HEAD 非帰属)。
- 段 6 lens C (pid 1685519) / D (pid 1687542) 投入。Monitor b6a5vn6dh。
- 親の焦点走 (3 file: producer + material_report + auth_experiment、計算ノード) **141 passed / 114 秒、rc=0** (22:54)。
- 変異 spec probe 版 `mutation-spec-probe.json` (a〜g + 等価 1、全件 SURVIVED 期待で観測 node 集め)。anchor 一意性 10/10 OK。
  estimated_run_seconds=200。本走は統合 commit 後 (HEAD blob 束縛)。

- 段 6 lens C / D 完了 (23:2x)。must-fix: MF-1 (両 lens、実 scope 検査が mode を識別しない)、MF-2 (lens C、atomic
  metadata の call edge)。裁定は adjudication 末尾。fix 子 1 本投入 (pid 2103543、s6fix1-t2298-1)。Monitor baw703830。
- 統合 snapshot = `artifacts/stage5-diff.patch` (fix 前)。commit message 案 `commit-msg-impl.txt`。
- probe spec に h / g2 を追加 (anchor 一意性は fix 後に再検査)。insight README 下書き `artifacts/insight-README-draft.md`。

- fix 完了 (MF-1/MF-2 実装済み・未実走、実装本体 5 関数と 17 consumer は sha256 一致で不変)。統合差分 `artifacts/stage6-diff.patch`。
  fix 子の dispatch 試行は rc=16 で hold は残っていない (確認済み)。
- 焦点走 2 回目 (pid 2234045、Monitor b35huuct6) と焦点再レビュー lens E (pid 2241680、Monitor b999k3nf3) を並行投入。
- 変異 runner `run-mutation.sh <spec> <sha> <tag>`。probe spec sha ac9aa84e…e0b091 (12 変異: a a2 b c c2 d e f g h g2 + 等価 1)。

- 焦点走 2 回目 142 passed / 111 秒 rc=0。lens E: MF-1 closed、MF-2 partial (MF-2A/2B) → fix 2 巡目 (最終) 投入 → closed
  (実装本体・17 consumer は AST hash 一致)。最終差分 `artifacts/stage6-diff-final.patch`。変異 i / j を probe spec に追加 (anchor 14/14 OK)。
- 焦点走 3 回目 (pid 2654405、Monitor boqysfkdt) 投入。file は staged 済み、message file の provenance 検査 rc=0。

- 焦点走 3 は rc=16 (親の `git add` で local 試行中の digest が変化、候補 4)。焦点走 4 は計算ノードで 142 passed / 112 秒 rc=0。
- **統合 commit `b47cf3975`** (00:1x JST、message `commit-msg-impl.txt`、trailer 検査 rc=0)。
- provenance full 監査 (pid 2708887、Monitor bs8ydka20) 投入。probe spec sha 7c315414…c188a7、plan-only rc=0 (15 走 / 3000 秒見積)。

- provenance full 監査 rc=0 (8146 件、新規違反なし)。変異 probe 完走 (14 変異、baseline PASSED、負例 13 件すべて観測 node あり、
  等価 1 件 SURVIVED)。台帳 `mutation-ledger-probe.json`。b/e/f は並走 consumer まで赤 (競走依存) → 本走の期待集合は
  lock 検査 10 本に限定し runner を `-k certified_evidence` に絞る (`mutation-spec-final.json`、sha b0987414…dc2c35、
  build は `measure/build_final_spec.py`)。本走投入 (pid 3561074、Monitor bxo1iydix、見積 15 走 / 2250 秒)。

- 変異本走: 13/13 KILLED、等価 1 SURVIVED、14/14 一致、baseline PASSED (HEAD b47cf3975)。台帳 `mutation-ledger-final.json`。
- 受入 (中間走、段 6) 投入 (pid 42487、Monitor bgg99dzug、`logs/acceptance-1-*`)。main は 0679f61f4 (受入が merge する)。
  **走行中は worktree を触らない (pre/post fingerprint)。**

## 未完の作業と次の一手
- 受入 1 (中間) の結果 → 段 7: insight dir (`output/insights/2026-09-04_t2298-t2273-shard0-critical-path/`: README,
  measurements, 変異 spec/台帳、verbatim) + spool fragment 3 本 (draft は artifacts/spool-*-draft.md、base digest は
  merge 後の worklog から `spool_fold.py --base-digest`) → `check_docs` / `spool_fold --dry-run` → docs commit (親 author
  docs scope) → 段 8 → **最終受入 (受入 2) → land** (`dev_wave_land.py`、receipt の tested_main/tested_tip、
  audited-commit = rev-list、landing-wave-tip 不要なら省略) → release → peer message → DW-O28 撤去 → collect_wave_usage。
- 本走 14/14 一致 → (済) 受入全走 (`dev_wave_wait.py acceptance`、canonical、K=3) → 段 7 (insight・fragment 3 本・commit) → 段 8 → 段 9 land。
- 監査 rc=0 → (済) `run-mutation.sh mutation-spec-probe.json 7c3154…c188a7 probe` (detached) → 観測 node から本走 spec →
  本走 → 受入 → 段 7〜9。
- 焦点走 3 緑 → `git commit -F commit-msg-impl.txt` (済) → full 監査 (dispatch) → 変異 probe (`run-mutation.sh <spec> <sha> probe`) →
  本走 spec → 受入 → 段 7〜9。同一 worktree からの dispatch は直列 (hold) なので監査 → 変異 → 受入の順。
- 焦点走 2 緑 + lens E 検収 (済) → 統合 commit (message `commit-msg-impl.txt`、`--message-file` 検査 → `commit -F` → full 監査)
  → 変異 probe (全件 SURVIVED 期待、観測 node 収集) → 本走 spec (KILLED 期待) → 受入 → 段 7〜9。
- 段 6 レビュー検収 → fix (要れば) (済) → 統合 commit (DW-O17) → 変異 probe → 本走 spec (KILLED 期待) → 受入全走 → 段 7〜9。
- 段 5 完了 → 親が対象 file の焦点走を計算ノードで実走 (済) → 段 6 (review 2 本は軽量版で省略可だが、lock 意味論は
  正しさ境界なので 1 本は回す) → 変異 matrix (a〜g) → 受入全走 (`dev_wave_wait.py acceptance`) → 段 7〜9。
- M-B / M-C の結果を measurements-draft へ追記 → insight。
- M-A/M-B の結果を insight へ。M-A は timeline から worker ごとの gap (report にない待ち) を node に帰属する。

## 落とし穴・気づき
- junit の time は setup+call+teardown (junit_duration_report 既定 total)。lock 待ちが fixture 内なら含まれ、
  runtest_protocol wrapper 内なら含まれない。
- dispatch generic は env clean・cwd=repo root。wrapper 自身が PYTHONPATH 等を設定する。
