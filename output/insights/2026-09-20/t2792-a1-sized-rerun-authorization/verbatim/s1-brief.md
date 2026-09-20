# 段 1 brief — [T-2792] A-1 sized attempt-0002 を exact な認可 record で投入可能にする (択 1、D2172 項 2)

作成 2026-09-20 12:50 JST。起点 local main `371674ea685ecb11e08dbcc31d4bf4f2bed0b20b` (= origin/main)。worktree `.claude/worktrees/dev-wave-t2792-a1-sized-rerun-auth`。

## 研究前進 (1 行)

論文の A-1 sized (balanced5、非認証 lane) の独立再現 attempt-0002 (同 seed・同物理順の反復、attempt-0001 稿の限定 L-A1S-4 = 反復間安定性の観察機会) を、規律 2 由来の rear gate を緩めずに投入可能にする土台。完了判定 = land 後の fresh submit-tree で認可 record を置けば `submit` が qsub まで到達できる状態を、fixture と実 base の複製 (job dir) で示す。投入・測定・稿・図は本 wave に含めない。

## 確定済みユーザー裁定 (変えない)

- D2172 項 2 (2026-09-20、第 24 回 /rulings 項 2、控え `rulings-inbox/2026-09-20-rulings-full24-verdicts.md`): 研究目的 = 同一配置の反復。択 1 を attempt-0002 の 1 attempt 限定で認可。record の形式は本 wave で起草。§6.1 / §6.4 の追補は将来の観測にのみ適用 (erratum の名で正当化しない)。実装条件 = Codex author + 敵対レビュー + 変異負例 (別 attempt 名・別 study・別 source sha・record 不在は拒否) + 既存の intent / attempt root 再使用拒否・先行証拠の完全性検査・公開先 create-only・anomaly 即 reject の保存。非認証 lane のまま。認可 record は「認可者が性能値を見た後の選択」を防ぐ装置とは称さない。
- D2156 (項 1〜5): 先行 attempt の証拠の移動・削除、policy / durable base の変更はしない。D2096 項 5 (3 study 目の枠組みは作らない) は本 wave で触れない。
- 引数: 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## brief 前の実測 (模擬でなく現物)

- 現行 gate `_assert_no_prior_v3_bench_start` (driver 2672〜2919 行) を実 durable base `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement` に read-only 実走: 同 study の `attempt-0002` は `prior attempt reached the bench barrier; group rerun is prohibited` で拒否、別 study は受理 (`verbatim/probe-gate-current.log`)。base 直下は `attempt-0001/` と `attempt-0001.intent.json` のみ。attempt-0001 の source_commit = `d2ebef7a4…`。
- 拒否の発火点は同関数末尾の 2 箇所 (`bench_go_study == study_id or ready 三揃い or bench_start に同 study` / `same_study_intent and (bench-go or ready 三揃いの lexists)`)。前段の corrupt / unsafe の raise (先行証拠の完全性検査) は別の述語。
- base を走査するのは driver 内この 1 箇所のみ (`iterdir()` 3 回のうち base は 1 回、job shell は base を走査しない)。`.intent.json` 以外の suffix と `barrier` を持たない entry は候補にならない。
- 公開先 gate `_exact_materialization_destination` (8264 行): `repo_root / policy.execution.materialization_relative_path` と完全一致・不在・親 dir 実在を要求。sized の公開先 `output/insights/2026-09-13/paper-story-a1-balanced5-sized` は attempt-0001 の leaf (README / receipt / result / .complete) で既に存在 → 現行では attempt-0002 の materialize は必ず拒否。`_run_materialize_v3` (8680 行) は `receipt["roots"]["attempt_root"]` と `args.expected_head` を持つ。
- DW-O09 pin 閉包: driver の現 sha `62c10187…` / blob `8af3ff86…` の出現は attempt-0001 の凍結 leaf と receipts の `working_sha256` / `git_blob_oid` (当時の source binding の記録、live 照合なし) のみ。live な path pin は AST 構造 pin 4 本 (spawn site 数 `test_ccbench_spawn_sites`、`run_campaign` 経路 `test_campaign:13784`、official perf closure 一覧、固定 range の non-touch manifest) で bytes を pin しない。事前登録 README (sha `6047eff0…`) は policy・source 契約 v2・driver 220 行・test で束縛 = 凍結。source 契約 v2 の束縛 4 file (契約・patch・policy・追補 `6093de24…`) は本 wave で変えない。
- CLI subcommand は submit / measure / materialize / complete の 4 本。集合を pin する test は無い。

## scope (変更面の実アンカー)

| # | file | 位置 | 変更 |
|---|---|---|---|
| 1 | `orchestrator/campaign/paper_story_a1_paired.py` | 定数群 (108〜120, 202〜222 行付近) | record の schema 定数と、認可の exact 集合の定数 (P1) |
| 2 | 同 | `_assert_no_prior_v3_bench_start` 2672 行 | `source_commit` を kwarg に追加。record の読取・exact 照合を行い、一致時だけ末尾 2 箇所の拒否を skip (P5)。corrupt / unsafe の raise は不変 |
| 3 | 同 | `_run_submit_v3` 3234 行 | `source_commit=expected_head` を渡す |
| 4 | 同 | `_exact_materialization_destination` 8264 行 / `_run_materialize_v3` 8732 行 | 認可 attempt に限り attempt 別公開先を受理 (P3, P6)。create-only・親 dir 実在は不変 |
| 5 | 同 | `_parser` 8909 行 / `main` | record の producer subcommand (P4) |
| 6 | `orchestrator/tests/test_paper_story_a1_paired.py` | 4185〜4275 行の gate test、2486 行の公開先 test の隣 | 正例 1 + 負例 (別 attempt 名・別 study・別 source sha・record 不在・record 破損 / symlink / file 名と field の不一致) + 公開先の正例・負例 + producer の create-only |
| 7 | `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md` (新規、親) | — | §6.1 / §6.4 の追補 (別版) (P7) |
| 8 | `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` (新規、親) | — | 一次資料 (brief・plan・相談・裁定・レビュー・変異台帳) |

scope 外: 投入・測定・results 稿・図・`docs/paper-story/README.md` の表、job shell、policy / 契約 / 事前登録 / 追補 `6093de24…` の bytes、pilot 経路、formal lane、trial registry、D2096 項 5。

## 不変条件 (DW-G05: 放置時の成果物影響を 1 行で)

- I1 規律 2: record 不在・不一致の attempt は従来どおり拒否 (受理集合は「定数 1 件 × 一致 record」だけ広がる)。緩めると測定済み workload の再投入で結果選択が可能になる。
- I2 先行証拠の完全性検査 (corrupt / unsafe の raise) は record の有無に関係なく走る。
- I3 intent / attempt root / 受領証 namespace の再使用拒否、公開先 create-only、anomaly 即 reject は 1 byte も変えない。
- I4 凍結物 (事前登録 README、policy、契約 v2、追補 `6093de24…`、attempt-0001 の leaf 4 file・receipts・稿・図 9) の bytes 不変。attempt-0001 の判定・lane・限定は動かない。
- I5 record は源 sha を exact に持ち、`submit` の `expected_head` と `materialize` の `expected_head` の両方で照合する。
- I6 非認証 lane のまま (formal=false / promotion_prohibited=true / result_authority は不変)。

## provisional 裁定 (攻撃対象)

- (P1) 認可の exact 集合は driver の定数 1 件 `(study_id = sized, attempt 名 = "attempt-0002", decision = "D2172", item = 2, decided_on = "2026-09-20")` に固定し、record はこれと完全一致したうえで `source_commit` を供給する。record だけを権威にする (定数無し) 案は「1 attempt 限定」を人手に委ねるので採らない。将来の attempt-0003 は新しい裁定 + 定数の追加 (diff に現れる) を要する。
- (P2) record = `<durable base>/<attempt 名>.authorization.json`、schema `paper-story-a1-paired-rerun-authorization/v1`、key 集合 exact = `{schema_version, study_id, attempt_root, source_commit, decision: {id, item, decided_on}, authorization_sha256}` (self digest は intent と同型 `_submission_intent_digest` 流用)。file 名 stem = `attempt_root` の basename = current_attempt.name を要求。symlink / 非 regular file は unsafe。
- (P3) 認可 attempt の公開先 = `<materialization_relative_path>-<attempt 名>` の兄弟 dir (例 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002`)。attempt-0001 の leaf dir に書き足さない (§6.1 の「pilot の公開先には何も書き足さない」と同型)。代替 = leaf 配下 `…/attempt-0002` (§7 の例。leaf の存在に第 2 attempt の公開が依存するので不採用の見込み)。
- (P4) record の producer = driver の subcommand `authorize-rerun --study-id --attempt-root --expected-head --decision D2172 --decision-item 2 --decided-on 2026-09-20` (create-only `_exclusive_write`、定数照合、intent / attempt root / record の不在要求、policy の base 直下であること)。手書き JSON は key 集合と self digest を誤りやすいので採らない。
- (P5) gate の解除範囲 = 末尾 2 箇所の `group rerun is prohibited` だけ。record の有無に関係なく先行証拠の走査・完全性検査は全部実行する。record の照合は走査の前に行い、不一致 record (別 attempt 名・別 study・別 source sha・破損) は「無視」ではなく **拒否** (理由を分けた message)。
- (P6) materialize は attempt 名が定数の attempt 名で、かつ base の record が exact 一致するときだけ (P3) の兄弟公開先を受理。record が無い / 一致しない attempt は従来の exact leaf のみ (既存 leaf は create-only で拒否)。
- (P7) 追補 (別版) は `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`。§6.1 追補 = 認可 attempt の公開先規則 (P3)、§6.4 追補 = 認可 record を持つ attempt は再走理由の列挙外の「独立の観測 attempt」。閉じた列挙・「性能の出力は再走を正当化しない」・既存凍結物・attempt-0001 の判定は不変。source commit 経由で束縛し、契約 JSON / policy に sha を足さない (凍結 bytes に触れない)。

## 成果物の形

- 実装 commit (Codex author trailer) = driver + test。成果物 commit (親) = 追補 README。記録 commit (親) = insight + spool fragment (worklog / decisions)。
- 変異 matrix (独立 clone、計算ノード): M0 等価対照 1 + 負例 (record 不在で受理 / 別 attempt 名で受理 / 別 study で受理 / 別 source sha で受理 / 定数不一致 (decision) で受理 / 完全性検査 skip / 公開先 create-only 解除 / 兄弟公開先を record 無しで受理 / producer の create-only 解除)。
- 実 base の複製 (job dir、attempt-0001.intent.json + barrier/**) に record を置いて gate が受理・置かずに拒否の両方を親が実走 (実データ dogfood)。実 base には書かない。

## 受入・実測環境

- test 自走は login (self-harness) + 計算ノード焦点走 (dispatch)。受入は `tools/dev_wave_wait.py acceptance --lease-optional`。変異は計算ノード dispatch。所在 = worklog、機体固有 = `docs/pegasus-runbook.md`。

## 並列分割

- 段 2 plan: read-only codex 1 本 (file:line)。段 3 consult: 1 本 2 レンズ (A 正しさ境界・規律 2 の受理集合、B 実効性・過剰・削除)。段 5 author 1 本 (driver + test)。段 6 review 2 本 + fix。docs (追補・insight) は親。
