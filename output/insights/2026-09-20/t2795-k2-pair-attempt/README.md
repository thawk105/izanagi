# [T-2795] K2 手動 loop の同 job pair を初投入した — 候補 10 の再評価だけ成立、stock は one-shot claim で認可前に停止し pair 不成立 (STOCK 性未確認、4 巡目未投入) (2026-09-20)

`authority: none` / `default_effect: no-state-change`

**種別:** 投入 1 job (D2172 項 3 (i) の pair、認可済み) と記録。**実装差分ゼロ** (Codex 実装子なし。glue は job root、repo 外)。
段 2・3 は省略 (軽量版)、段 4 前に read-only codex 相談 2 本 (診断への攻撃)、段 6 read-only レビュー 1 本。逐語は `reviews/`。

- 日付: 2026-09-20 (JST)
- wave: `dev-wave-t2795-k2-pair`、branch `worktree-dev-wave-t2795-k2-pair`、着手時 local main `482f19b88dbbe255fc2bb0dcc95b14c1681c1a83` → 開始直後に
  `6a3e1580903434c734f050ed31738ade76d187e9` へ ff-only (T-2304 の land 後処理 2 commit + fold)。submit-tree もこの SHA
- 依頼: `verbatim/T-2795-pair-origin.md` (ユーザー、dev-wave 引数の逐語)。裁定 = D2172 項 3 (i) (pair を 1 job) + (iv) (4 巡目を 1 job、成立が条件)、
  D2183 (launcher 契約)。停止規則 = 「STOCK 成立を最初に確認し、成立しなければ対照成立と認定せず報告して止める (再投入で救済しない、launcher 改修は scope 外)」
- job root (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/` (HANDOFF、brief、診断メモ、裁定、glue、submit-tree、campaign 原本)

## 0. 一行で・主張すること・しないこと

**同 job pair launcher (D2183、`IZANAGI_S4_STOCK_CONTROL=1`) を初めて実投入した job `13339.nqsv` (Elapse 74 秒) で、候補 10 (round 3 の
`proposal-4.json` を再評価) は serializable / certified / anomalies 0・median 811,956 tps を得たが、続く stock driver (同 job・同 campaign の 2 起動目) は
`campaign_claim.acquire_claim` の `O_EXCL` (「single-process campaign の one-shot claim leaf」、D464 / D553) で `ClaimError` となり、build にも到達しなかった。
STOCK 成立 (`src_token == STOCK`) は確認できず、pair は不成立。依頼の停止規則どおり再投入せず、4 巡目も投入しない。** launcher の設計 (同 campaign に
2 process) と Pegasus 契約 (reservation 必須 → claim 必須) の整合は本 wave の scope 外で、修復方向を裁定パッケージ (§4) として残す。

**主張する。**

1. pair 試行は 1 job・1 attempt。候補 10 は certified で campaign `p3-s4-loop-s4-autonomous-b24749ae` (新 ID、新 policy epoch) に 5 record の WAL がある (§1)。
2. stock の停止点は `loop._authorize_measurement` → `campaign_claim.acquire_claim` (同 identity の claim を候補 driver pid 2080612 が残したまま終了) で、
   condition gate (stock 形) は正常復帰していた。claim 以外の独立した失敗原因は stdout / stderr に無い (相談 A、§2)。
3. 既存の launcher・claim leaf・環境契約の範囲で、同 job・同 campaign (同 identity・同 WAL) の stock 対照を得る経路は無い (相談 A が code で確認、読んだ範囲は §2)。
4. T-2795 wave の test は実 `run_campaign` を戻すものを含むが site `OTHER` (`linux-baremetal`、`single_process=False`) で claim 分岐に入らず、
   job contract test は代用 python で driver を起動しない。欠落 = 同 durable root・Pegasus 契約での候補→stock 連続起動の結合検査 (§2、F1019 再発)。

**主張しない。**

- **pair が取れた・stock に勝った/負けた・4 巡を閉じた・診断の効果を再現した、とは言わない。** 同 job の stock 対照は依然として無い (critic の R0 は 4 度目)。
- **stock 未測定を stock の性能ゼロ・失格・非 STOCK 判定に置き換えない。** inert (実 compiler で stock source が STOCK token に解決すること) は未測定のまま。
- 候補 10 の再評価値 811,956 tps は「pair 試行における既知候補 10 の追加評価」であり、round 3 の 3 走 (20 / 25 / 10) と同じく**非同時刻・別 tree・別 policy epoch**。
  差を改善・退行・再現性・同等性の根拠にしない。policy epoch が違うことを理由に本走の候補測定を無効化もしない (規律 7)。
- 「実機で 1 job も通さず land した」だけを失敗とは数えない — T-2795 insight §0 は「1 job も投入していない」「STOCK 成立は未測定」を明記し、実装と投入を
  段階化していた。失敗として記録するのは「同 identity・同 WAL への二段起動を設計したが、reservation 必須の実認可経路との整合を検査できず、初投入の stock が
  claim 取得で停止した」こと (F1019 と同型、§5)。
- results 稿 (K2 3 巡稿と同形の単独稿) は書かない。依頼の「1 本まで」は上限であり、pair も 4 巡目も無い本 wave に材料は無い (相談 B)。

## 1. 実測 — job `13339.nqsv` (attempt-0001、pair、投入 1 回)

固定 SHA の専用 submit-tree (`submit-tree-pair`、HEAD `6a3e15809`、superproject tracked clean (submodule 除外)、CCBench を `p3_s4_loop.PIN` = `511c9538…` へ
checkout (gitlink は T-2304 pin 前進後の `e9e477ca…` のまま、D1777 / T-2407 の手順)) から `tools/pegasus/README.md` の K2 正例の形で投入。third-party は
hydrate 既定 staging (5 source)。env: `IZANAGI_S4_STOCK_CONTROL=1`、proposal = round 3 の `materials/proposal-4.json` (sha `bd3e5fd2…`、value 10)、
K2 manifest wal-only (digest `396cd559…`)、`CODER_ROLE=coder-v4-autonomous-k2`、`KNOWLEDGE_CLASSIFICATION=known_result_conditioned_derivative`、`DE_NOVO_CLAIM=false`。

| 項目 | 値 |
|---|---|
| request / `pbs_jobid` / host | `13339.nqsv` / `0:13339.nqsv` / `bnode032` (Created 19:12:26 → Started 19:12:36 → Ended 19:13:45 JST、Elapse **74 秒**、残 walltime 10,726 秒) |
| `driver_rc` (compute-result) | **1** = job body の集約 `p3 S4 pair: candidate_rc=0 stock_rc=1` (候補 0、stock 1) |
| campaign | `p3-s4-loop-s4-autonomous-b24749ae` (新規 WAL、`1 committed / 0 aborted / 0 skipped`)。round 3 の `409e13f8` と違うのは admission policy epoch (T-2304 の pin 前進で `949ddcc2…` → `db6bc9ea…`) が identity に入るため。T-2795 insight §0「identity の維持は約束しない」どおり |
| 候補 variant / genome | `002642c7ac96` / `silo\|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` (round 3 と同 variant id) |
| 候補 admission | class `coder-authored` (authority `cli-opt-in`)、policy `db6bc9ea…`、receipt `d3a481b7…`、source `src_token` = `fec064b1…` (非 STOCK、`ccbench_commit` `511c9538…`) |
| 候補 build | trace `6c87eb2ecf19686e` / perf `7a60310d588b89c7`、いずれも非 cache、build_start 19:13:10 → build_done 19:13:25 (15 秒) |
| 候補 verify | **`serializable` / `certified=true`**、anomalies **0** (commits 522,868 / aborts 121,826、trace build の abort 率 18.9%)、`commit_witness` {522868, 0}、`proof_surfaces` X/P present、I absent、verify_done 19:13:38 |
| 候補 bench | median **811,956 tps**、2 反復 `[817565, 806347]`、run 内 CV 0.977%、`settled=true`、`bench_wall_s` 2.13、perf build の abort 率 9.155% (T-2702 以降の集約) |
| `llc_miss_rate` / `ipc` | null (欠測、`perf_observation.preflight` `status=unavailable` / `rc=2`)。0 でも差なしでもない |
| 候補終端 / 停止判定 | `commit` (fitness 811,956)、`outcome=certified`、`iteration=1`、whiteboard 1 件 (decrease / large / success / delta null; success は certified の意味)、**`continue`** |
| stock | driver 2 起動目 `p3_s4_loop --isolate-worktree --fetchcontent-prebuild-receipt R --knowledge-manifest M --knowledge-classification C --knowledge-de-novo-claim false --stock-control`。stdout は `=== 段 4 stock control (stock_root=…/submit-tree-pair/external/ccbench, isolate_worktree=True) ===` の見出し行だけで outcome 行なし。stderr: `_run_stock_control_resolved` (p3_s4_loop.py:1986) → `run_campaign` (loop.py:517) → `_authorize_measurement` (loop.py:236) → `campaign_claim.acquire_claim` (campaign_claim.py:430) → **`ClaimError: campaign claim は既に 2080612 が所有している`** (直接原因 `FileExistsError` on `output/env/pegasus/claims/p3-s4-loop-s4-autonomous-b24749ae.claim`) |
| claim file (原本) | `{"boot_id":"a0e2a498-…","campaign_identity":"p3-s4-loop-s4-autonomous-b24749ae","created_utc":"2026-09-20T10:13:07.763897+00:00","host":"bnode032","job_id":"0:13339.nqsv","pid":2080612,"proc_starttime":50445791,"protocol_digest":"b24749ae65f2…"}` — 候補 driver が 19:13:07 JST に作成、削除・退避していない |
| WAL / 防護 file (sha256) | WAL 5 record `b5754f98…` (7,062 B)、`campaign.lock` `962ef7d7…`、`loop_state.json` `a8c6a8b6…`、`s4_loop_digest.txt` `8bde66fa…`、受領証 `c42dc712…` (round 3 と同 bytes)。stock 期待 variant `602b4ce9c788` の record は無い |

**投入前検査** (login): submit-tree HEAD = 期待 SHA、`--ignore-submodules=all` の dirty 0 行、CCBench HEAD = PIN、proposal / manifest / staging 実在 (`qsub-submit-pair.sh`)。
attempt dir は `mkdir` だけ (job body 所有)。

**非同時刻の点 (改善・退行の根拠にしない):**

| 走 | 日付 / job / tree / policy epoch | value | median tps | abort 率 (perf) |
|---|---|---|---|---|
| round 1 | 2026-09-16 / `1216.nqsv` / `d97c423bd` / 旧 | 20 | 719,324.5 | 7.75% (代表 rep) |
| round 2 | 2026-09-18 / `4954.nqsv` / `d2ebef7a4` / 旧 | 25 | 687,508.5 | 7.40% |
| round 3 | 2026-09-19 / `10761.nqsv` / `a99425b66` / 旧 | 10 | 815,983.0 | 9.07% |
| pair 試行 (本 wave、候補のみ) | 2026-09-20 / `13339.nqsv` / `6a3e15809` / 新 (`db6bc9ea…`) | 10 (再評価) | 811,956.0 | 9.16% |

同時刻の対照 (stock、または同 job 内の別値) はどの走にも無い。

## 2. 機構 — なぜ stock が止まったか (code、worktree HEAD `6a3e15809`; 相談 A の裏取り込み)

- `loop._authorize_measurement` は `reservation.is_reservation_required(contract.isolation_policy)` のとき必ず `campaign_claim.acquire_claim(claim_root, record)` を呼ぶ。
  Pegasus 計算ノードは `pegasus` 契約 (`single_process=True`) に写像され、claim path は `<out_root>/env/pegasus/claims/<campaign_identity>.claim`
  (identity = `ident.campaign_id(bound_cfg)` = campaign dir 名)。`IZANAGI_EXPLORATION_OUTPUT_ROOT` は claim root と campaign layout の**両方**を動かすので、
  root 切替は D2183 の「同 WAL」を満たさない。reservation 不要契約 (`linux-baremetal`) は Pegasus では選べない。
- `campaign_claim.acquire_claim` は「single-process campaign の one-shot claim leaf」。同 identity path は `_scan_protocol_conflicts` の `excluding_path` で
  除外され、`O_EXCL` で作成し、存在すれば **所有者の生死を見ずに** `ClaimError`。D464 の生存判定 (DEAD は通す) は**別 path の同 protocol digest** に効く。
  release・stale 自動削除・期限切れ回収は意図的に無く、「手動回収だけが裁定済み経路」。D464 の文面は同 identity path の永久拒否を明記していない
  (実装は親の読みどおり、裁定文の射程は相談 A の指摘)。
- D2183 の設計「stock は候補と同じ campaign (同 identity・同 WAL) に `run_campaign` → `pipeline.evaluate` で入れる」は、同 out_root で **2 つ目の process が
  同 identity の claim を取る**形であり、上の leaf と構造的に矛盾する。候補 driver が 19:13:07 に claim を作って終了し (claim は残る)、stock driver
  (同 job、別 pid) が同 path を `O_EXCL` で作れなかった。stock の condition gate (`_require_condition_gate(sub, genome, stock_root=)`) は `run_campaign`
  より前で正常復帰している (traceback が `run_campaign` 内)。
- **test の欠落:** `orchestrator/tests/test_p3_s4_loop.py` の stock 経路 test には実 `loop.run_campaign` を戻すものがある (verify option の伝達、COMMIT・digest 更新・
  再実行時 skip、非 STOCK evidence の admission 拒否) が、共通 fixture は site を `OTHER` に固定し契約は `linux-baremetal` (`single_process=False`) なので
  `_authorize_measurement` の reservation / claim 分岐に入らない。`test_p3_s4_loop_job_contract.py` は実 shell を走らせるが代用 `python3.10` が `-m` 呼出しを
  記録して指定 rc で終わる (実 driver・claim は起動しない)。変異 17/17 KILLED はこの経路の検査ではない。
- 同 out_root・同 identity への再起動 (候補の 2 回目 `--run-iteration` を含む) は、既存 claim が残る限り同じ理由で拒否される。claim の所在は output root に従うので、
  fresh な source tree そのものが機構上の必要条件とまでは code から導けない (K2 loop の毎巡 fresh tree は fresh out_root を伴う運用であり、round 2 / 3 の記録は
  walltime を理由に挙げている。段 6 レビュー should 1)。
- claim 以外の独立した失敗原因は無い: stderr の CMake 警告 (未使用 `CMAKE_C_COMPILER`) は候補側でも出て certified、残 walltime 10,726 秒。
  full / short PIN の admission 問題 (T-2795 §7 の裁定パッケージ候補) は今回の発火原因ではない (claim は admission より前)。

## 3. 相談と裁定 (段 4)

- 相談 A (sol、`reviews/consult-a.md`): P-A (既存経路なし) 支持。訂正 2 点 = stock の condition gate は正常復帰 (親の「未実行」は誤り)、TL は実 `run_campaign` を通すが
  `OTHER` site で claim 分岐に入らない。候補の certified 記録はこの失敗で無効化しない。第 3 の原因なし。
- 相談 B (luna、`reviews/consult-b.md`): P-B (正式停止) 妥当 — 停止理由は「inert 不成立」でなく「STOCK 成立の確認前に claim 取得で停止」。本 wave 可 = 証拠照合・
  記録・停止判断・整合案の比較、不可 = launcher / claim 変更、claim 削除・退避、別 root 投入、4 巡目、STOCK 要件緩和。(ii) は「同 process」だけでは不成立
  (`run_campaign` は呼出しごとに認可)。failures は F1019 再発。results 稿は見送り。記録先に phase / paper-story README / D2183 の事実訂正 / launcher insight の導線。
- 裁定 (`reviews/s4-ruling.md`): 相談所見は全件 real で採用。**正式停止** (DW-STOP: 承認前提を覆す新事実 + 許可範囲で復旧不能)。再投入なし、4 巡目なし、
  launcher / claim 不変、claim file 不変、r4 用 submit-tree は未使用のまま撤去。候補 10 の再評価は保持 (規律 7)。
  やらない理由の最も強い形 = 「DW-STOP『直せる赤で終了しない』が勝つので本 wave で直して再投入すべき」→ 却下 (依頼が launcher 改修 scope 外・再投入禁止を明記、
  claim leaf は排他防壁で受理集合の変更)。

- 段 6 read-only レビュー (`reviews/s6-review.md`、gpt-6-astra、約 5 分): **GO、must-fix 0、should 1、nit 1**。数値・識別子・sha256 (binary の sha を含む)・abort 率の換算・
  claim file・fragment 形式・凍結稿不変・禁止成果物の非複製をすべて一致と判定。should (§2 の「fresh tree は claim でも必然」は断定過多 → 「同 out_root・同 identity の
  再起動が拒否される」に限定) と nit (診断メモの TL 記述に訂正注記) は反映済み (診断メモは末尾に訂正節、本文は当時のまま)。

## 4. 裁定パッケージ (実装せず記録) — launcher と one-shot claim の整合

修復は Codex author + 敵対検証子の別 wave (実装面・認可契約に触る)。推奨と却下候補:

- **推奨 (ii'):** 「1 回の認可・claim の所有期間で候補と stock の両評価を行う driver 設計」。claim leaf は不変。`run_campaign` の認可契約 (取得済み認可の受け渡し) または
  stock 評価の呼出し形を変える。D553 の sink-local `single_process` と D2183 の CLI 排他 (`--run-iteration` と `--stock-control` の排他) への影響を次 wave の段 1 で明示する。
  「同 process にまとめるだけ」では `run_campaign` が呼出しごとに同 path を `O_EXCL` するので不成立 (相談 B)。
- 却下候補 (i): 同 identity path の DEAD 所有者を再取得可能にする (D464 の生存判定を同 path に拡張) — one-shot の受理集合を変え、判定と置換の競合を解く必要がある。
  局所 launcher 修復より防壁への影響が大きい。
- 却下候補 (iii): job body が候補後に claim を rename / 退避 — 自動退避は自動回収と同じ効果で、claim 不在の窓を作る (「手動回収だけが裁定済み経路」に反する)。
- 却下候補 (iv): stock を別 out_root (同 job・別 layout) — D464 の排他保証範囲外で同 WAL を破る。root を変えても identity は変わらないので「別 campaign = 別 ID」とも書けない。
- (v) 保留 (修復・追加計測を認可しない) も択。
- 修復後の pair 再投入 (1 job) と 4 巡目 (1 job) は D2172 項 3 の予算の再提示が要る (ユーザー)。D2172 項 3 の元の認可を撤回する必要は無い。
- 別件 (T-2795 §7 から持ち越し、今回は発火せず): `build_admission.derive_build_admission` の stock-baseline 分岐が full PIN と短縮 `CURRENT_PIN` を exact 比較する点。

## 5. 記録先と failures

- round 3 記録 `output/insights/2026-09-19/k2-loop-round3/README.md` 末尾に「同 job pair の投入結果 (T-2795、2026-09-20)」節を追記 (既存本文は不変)。
- failures: **F1019 への再発追記** (「condition gate を driver へ統合後、実走せず前提の不整合が残った」型。今回は既存 claim leaf を通る新 launcher が実認可経路との整合を
  検査されないまま land し、初投入の stock が claim で停止)。F81 (全テスト緑で実 repo で動かず) / F722 (実 producer を通さない期待側) は補助参照。F1018 は主分類にしない
  (env 入力欠落ではない)。F321 は該当しない (二重投入を通したのでなく claim が拒否した)。恒久修復は未実施 (裁定パッケージ)。
- decisions fragment: 本裁定 (事実 = D2183 の 2 process 設計は Pegasus 契約下の one-shot claim と矛盾、修復方向 = (ii')、本 wave は実装しない)。D2183 の本文は書き換えない。
- worklog fragment: T-2795 を更新 (pair 不成立、裁定パッケージ、修復 wave は AI、再投入認可はユーザー)。
- `docs/phase3.md` 項 4 に 1 行 (pair 試行終了・未達)。`docs/paper-story/README.md` の stale 注記に 1 項目 + results 表 K2 行に追補 (C35 / 3 巡稿の「stock 対照は未達 ([T-2795] 裁定待ち)」は
  「結線済みだが初投入で claim 拒否、対照未達のまま」へ)。`output/insights/2026-09-20/t2795-pair-launcher/README.md` §0 / §7 に日付付き訂正導線 1 行。
- 検査: `python3 tools/check_docs.py` 違反なし、`python3 tools/spool_fold.py --dry-run` = `planned` (3 fragment)、`git diff --check` 緑、三軸語走査
  (`s8b_holdout_freeze search`、rc=1) の conjunction hit は既存の凍結成果物 4 file (`output/env/pegasus/calibration/s8b-floor-official/…` 3 file、
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) だけで本 wave の file に hit 0。受入・provenance 監査の結果は job dir の受領証と land の記録が持つ。
- 段 8 (skill 自己改善) 候補: (1) dev-wave 引数が指した runbook 節名が実在しなかった (正本は `tools/pegasus/README.md`) — next-tasks の出力の path 検証は command 側の
  問題で docs は変えない、候補として記録のみ。(2) DW-G01 (生死実験先行) を「既存 driver への統合」に適用する規律は F1019 の恒久対応に既にあり、今回はその再発 →
  新しい節・命令は足さない (routing 1、既存 F への再発追記で閉じる)。

## 6. 一次資料

- `verbatim/T-2795-pair-origin.md` (依頼)、`reviews/s1-brief.md`、`reviews/diagnosis-pair-0001.md` (親の診断メモ、相談 A の訂正を反映済み)、`reviews/consult-a{-prompt,}.md`、
  `reviews/consult-b{-prompt,}.md`、`reviews/s4-ruling.md`、`reviews/s6-review{-prompt,}.md`
- `evidence/attempt-0001/` — `job.stdout` / `job.stderr` / `compute-result.json` / `reservation.json` / `masstree-prebuild-receipt.json` (無変更複製。原文 sha256:
  `job.stderr`=`d7e06370…`、`compute-result.json`=`0199724d…`、`reservation.json`=`221440de…`、`masstree-prebuild-receipt.json`=`1ed5ea09…`)。
  **可逆最小正規化 (DW-S07):** `job.stdout` は行末空白 2 行 (`-- Found Threads: TRUE  `) が `git diff --check` に抵触するため行末の空白 / tab を除去した (可視文字不変)。
  原文 sha256 `84b63d007288effbc4f62a1a04740b7766bfdf6a32fa9b7f36b126c324644c2d` (12,567 bytes)、正規化後 `f0a96ab5e359a413e0db0755f6bfc3004a5407fe10fcfd5c0d0491411b90fc74`
  (12,563 bytes)。`diff -w -B` で原文と一致 (実測 rc=0)。qstat の写し (`allocation-qstat.stdout`) は行末空白が多いので repo へ写さない (job root にある)。
  `reviews/consult-a.md` も同じ正規化 (総括 4 行の markdown 改行用の行末空白 2 個 ×4): 原文 sha256 `2838aa602824dcf5bcee610714346479a682b8bc04cb0bb4c8a715ebf09c04af`
  (8,055 bytes)、正規化後 `63e9711fb886c7bb8e06c2af1ec5f68355d3c45bb875343ed5bd3add09976763` (8,047 bytes)、`diff -w -B` で一致 (rc=0)。
  `reviews/s6-review.md` も同じ正規化 (行末空白 2 個 ×10 行): 原文 sha256 `97830a584dd61cf74b4fb4f77d9a26dffbb6fe4e7d7f9dc167d8058a1401bb5f` (5,615 bytes)、
  正規化後 `3a4530770a72fdfd4f243a6b6bdf2554504b8eb87dcceeee12787060abd0031e` (5,595 bytes)、`diff -w -B` で一致 (rc=0)。
- `materials/` — `run-summary-pair.json` (WAL / lock / digest / 受領証の sha、variant ごとの record、停止判定)、`wal-refs-pair.json` (canonical ref 5)、`wal-outcomes-pair.json`
  (admission receipt の class / policy / src_token を含む機械射影)。proposal は round 3 の `materials/proposal-4.json` (sha `bd3e5fd2…`) と同 bytes で複製しない。
- **campaign WAL・`campaign.lock`・`s4_loop_digest.txt`・`loop_state.json`・受領証・claim file は repo へ複製していない** (`guard_bash` / `guard_write` の防護対象)。原本は job root
  `submit-tree-pair/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と `submit-tree-pair/output/env/pegasus/claims/`。
- job root の glue (repo 外、実装面ではない): `setup-submit-trees.sh`、`qsub-submit-pair.sh`、`wait-job.sh`、`wal_outcomes.py`、`project_pair_results.py`、`consult-launcher.sh`。
  4 巡目用の `submit-tree-r4` は構築したが未使用 (撤去)。
