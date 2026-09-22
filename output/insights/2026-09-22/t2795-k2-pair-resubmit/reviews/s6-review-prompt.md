単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md — 本 wave の insight (レビュー対象の本体)。
- 同 dir の `materials/` (wal-outcomes-pair.json、wal-outcomes-r4.json、epoch-diff-pair.json、epoch-diff-r4.json、planner-input-5.json、planner-context-5.json、coder-input-5.json、
  diagnosis-5.json、planner-prompt-5.md、coder-prompt-5.md、proposal-5.json、round3-loop-state.reconstructed.json、round3-agent-outputs.reconstructed.jsonl)、
  `evidence/attempt-pair-0001/` と `evidence/attempt-r4-0001/` (job.stdout、job.stderr、compute-result.json、reservation.json、masstree-prebuild-receipt.json)、
  `verbatim/` (T-2795-resubmit-origin.md = ユーザー依頼の逐語、planner-5.json、coder-5-response.md、coder-5.json)、`reviews/` (s1-brief.md、s4-ruling.md)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-19/k2-loop-round3/README.md — 末尾の追記節「同 job pair の再投入と 4 巡目 (T-2795、2026-09-22)」(それより前の本文は不変のはず。`git diff 8fd2a2f5c -- <path>` で確認) と、
  4 巡目の入力元になった同 dir の `materials/run-summary.json`、`verbatim/critic-3.md`、`materials/knowledge-input.json`、`materials/coder-input-4.json`、`materials/proposal-4.json`、`layer3_report.json`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/spool/worklog/2026-09-22-dev-wave-t2795-k2-pair-resubmit-1.md — worklog fragment。
  書式正本は同 worktree の `docs/spool/README.md` と `docs/spool/worklog/README.md`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/phase3.md — 項 4 に足したチェック行 1 つ ([T-2795]、2026-09-22)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/docs/decisions.md — D2172 (68490 行〜、項 3 だけ)、D2187 (69385 行〜)、D2194 (69645 行〜、項 2 だけ)、
  D2205 (70351 行〜)、D2211 (70677 行〜、項 1 だけ)、D2212 (70885 行〜、項 4 だけ)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md §1・§4 と
  /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md §1 (比較対象の過去値)。
- 一次資料の原本 (読取専用、repo 外、job root = /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/): `startup-gate.log`、`precheck.log`、`setup-submit-trees.log`、
  `hydrate-submit-tree-pair2.json`、`hydrate-submit-tree-r4.json`、`qsub-attempt-pair-0001.stdout`、`qsub-attempt-r4-0001.stdout`、`build-round4-inputs.log`、`wal-outcomes-{pair,r4}.json`、
  `epoch-diff-{pair,r4}.json`、`evidence/attempt-{pair,r4}-0001/` (原文 job.stdout を含む)、`originals-copy-20260922/` (MANIFEST.sha256 と両 campaign の byte 複製)、
  campaign 原本 `submit-tree-pair2/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と `submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/`
  (WAL `runs/wal.jsonl` / loop_state.json / s4_loop_digest.txt / campaign.lock / knowledge_manifest_receipt.json は cat / jq / sha256sum で読む)、各 tree の `output/env/pegasus/claims/*.claim`、
  親の glue (`build_round4_inputs.py`、`build_coder_input_5.py`、`build_proposal_5.py`、`extract_coder_json.py`、`check_stock_variant.py`、`epoch_diff.py`、`ratios.py`、`qsub-submit-pair.sh`)。
- pair 初投入の byte 複製 (比較用、読取専用): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/originals-copy-20260920/campaign/。

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair-resubmit とする。

## 依頼 — 記録の事実照合 (docs-only、実装差分ゼロ、投入 2 job の記録)

本 wave は認可済みの 2 job を投入した: (1) 同 job pair の再投入 (`16269.nqsv`)、(2) 成立を受けた 4 巡目 (`16312.nqsv`、planner-5 / coder-5 の新規生成 1 回 + 同 job stock)。
実装面の差分は無い。レビュー対象は **記録 (insight README / round 3 README の追記節 / worklog fragment / phase3.md の 1 行) が一次資料と一致し、段 4 裁定 (`reviews/s4-ruling.md`)
の停止規則と主張限定を守っているか**である。次を検査せよ。

1. **数値・識別子の逐語照合。** insight §1・§2.3 の表 (job / host / 時刻 / Elapse / driver_rc / campaign id / variant / genome / admission の class・policy・receipt・src_token /
   verify の verdict・commits・aborts・anomaly / bench の median・反復値・CV・settled / perf と trace の abort 率 / WAL・lock・loop_state・digest・受領証・claim の sha256 と bytes) を
   原本 (WAL、compute-result.json、reservation.json、job.stdout / job.stderr、claim file) と突き合わせ、不一致を全て挙げよ。sha256 は `sha256sum` で再計算せよ。
   §3 の比 (2.366 / 2.493)・差 (+1.74% / +7.20% / +1.17% / +1.67%)・百分率 (18.880% / 3.108% / 22.136% / 3.007% / 9.01% / 1.815% / 10.105% / 1.835%) を検算せよ。
   round 3 README の追記節、worklog fragment、phase3.md の行に書いた同じ数値も照合せよ (転記ずれ)。
2. **停止規則の判定の正しさ。** `s4-ruling.md` の 4 条件 (候補 certified ∧ commit、stock certified ∧ commit ∧ BUILD_START `src_token == "stock"` ∧ variant = stock genome の `variant_id`) を
   両 job の WAL で独立に判定せよ。stock genome の variant id は `orchestrator/campaign/p3_s4_loop.py` の stock 経路 (`_run_stock_control_resolved` 付近) の genome 式と
   `variant_id` から確かめよ。判定を job rc や driver の出力行に依存させた箇所が記録にあれば挙げよ。
3. **4 巡目の入力 (択 A) の忠実さ。** `materials/planner-input-5.json` / `coder-input-5.json` の値 (current_perf / baseline、whiteboard、k2_critic_diagnosis、knowledge_input、leakproof_context、
   planner_direction) が round 3 の `run-summary.json`・`critic-3.md`・`knowledge-input.json`・`coder-input-4.json` と `verbatim/planner-5.json` から導けるか、pair 再投入の結果
   (348,883 / 825,490 など) が入力や prompt に**混入していないか**を確かめよ。`planner-prompt-5.md` / `coder-prompt-5.md` の JSON 部分が `planner-input-5.json` / `coder-input-5.json` と
   一致するか、事実開示に誤りや過大がないか。再構成物 2 本の sha256 が記録値 (`917ba3d3…` / `66d3e737…`) と一致するか。`proposal-5.json` が planner-5 と coder-5 の逐語から組まれているか。
4. **主張限定の遵守。** 「候補 5 は候補 10 より速い」「固定 backoff は適応 backoff より良い (一般化)」「critic 診断が効いた」「改善」「4 巡目が 1 巡として閉じた」に当たる文言が記録のどこにも
   無いか。逆に必須の限定 (別 job・別 node、stock 間の揺れ、この配線に限る、stock は BACK_OFF=1 の適応 backoff、派生入力の限定 = sha 一致は確認した data の同一性まで、
   送付 bytes の非照合、critic-4 / AO / 層 3 は未実施) が欠けていないか。
5. **epoch 差の記述。** §4 の表 (campaign ID と preimage、受領証、環境契約・activation、closure の path 数と差 37 / 42 と変更 4 file の名前、旧 lock の厳密 decode 拒否、admission policy、
   build の識別) を `epoch-diff-{pair,r4}.json` と原本 lock・WAL で確かめよ。
6. **依頼の逐語との対応。** `verbatim/T-2795-resubmit-origin.md` の要求 (pair 再投入 1 job、成立時 4 巡目 1 job、不成立なら停止、経路 H、lock 済み tree を動かさない、着手直前の local main から
   新 submit-tree、投入前の node 時間見積りと 2 node 時間の確認ライン、epoch 差と派生入力の限定の開示、規律 2 不変、gate・検査・台帳の追加なし) を記録と job root の実物が満たすか。
   「各 1 回だけ投入」を qsub の stdout と `evidence/` の attempt 数で確認せよ。見積りの記述が D2212 項 4 と第 31 回裁定 (「見積りは job Elapse の実測で出し、2 未満は確認待ちにしない」、
   控え = /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-22-rulings-full31-verdicts.md 項 1) に照らして妥当か。
7. **可逆最小正規化の記述。** 両 `evidence/attempt-*/job.stdout` の原文 / 正規化後の sha256 と byte 数、`diff -w -B` 一致の主張を再計算で検証せよ (原文は job root)。
8. **fragment の形式。** worklog fragment (H2 がちょうど `## 本文` と `## 次の一手差分`、`完了` の `remaining: none` と `base:`、`更新` の `base:`、title の `[T-2795]` が `完了` に置かれている、
   placeholder の綴りが一致、新規 T の書き方) が README の規則に適合するか。base digest は `python3 tools/spool_fold.py --base-digest '[T-2795]'` / `'[T-2808]'` (読取専用 lookup) で照合してよい。
9. **過剰・欠落。** 記録すべき一次資料で欠けているもの、逆に repo へ複製してはいけない campaign 成果物 (WAL / lock / digest / claim / 受領証 / campaign dir の loop_state.json) が
   複製されていないか (再構成物 2 本は campaign dir の外の名前で、D2194 項 2 が置き場所を指定したもの)。

各所見は real / refuted、file:line、成果物影響 1 行 (DW-G05) を付け、must-fix / should / nit に分けよ。実装や新 gate の提案はしない。
書込可能な tmp は無いので静的検査と読取専用コマンドでよい。書込みは禁止 (Bash 経由のリダイレクト・sed -i・tee も禁止)。テスト実測は親が行うので pytest 緑を要求しない。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

markdown。`## must-fix`、`## should`、`## nit`、`## 照合した数値 (一致)`、`## 総括` (GO / NO-GO と理由 3 行以内)。
