単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md — 本 wave の insight (レビュー対象の本体)。
- 同 dir の `materials/` (run-summary-pair.json、wal-refs-pair.json、wal-outcomes-pair.json)、`evidence/attempt-0001/` (job.stdout、job.stderr、compute-result.json、reservation.json、masstree-prebuild-receipt.json)、
  `reviews/` (s1-brief.md、diagnosis-pair-0001.md、consult-a.md、consult-b.md、s4-ruling.md)、`verbatim/T-2795-pair-origin.md` (ユーザー依頼の逐語)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-19/k2-loop-round3/README.md — 末尾の追記節「同 job pair の投入結果 (T-2795、2026-09-20)」(本文は不変のはず)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/spool/worklog/2026-09-20-dev-wave-t2795-k2-pair-1.md、同 `docs/spool/failures/2026-09-20-dev-wave-t2795-k2-pair-2.md`、同 `docs/spool/decisions/2026-09-20-dev-wave-t2795-k2-pair-3.md` — 3 fragment。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/phase3.md — 項 4 に足したチェック行 1 つ ([T-2795])。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/paper-story/README.md — stale 注記の追加 1 項目 (「K2 手動 loop の同 job stock 対照は…未達のまま」) と results 表の K2 行末尾の追補、件数行「4 件」。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-pair-launcher/README.md — §0 冒頭と §7 に足した「追記 (2026-09-20…)」2 箇所。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/spool/README.md と同 dir の worklog/README.md、failures/README.md、decisions/README.md — fragment の書式正本。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/decisions.md — D464 (19324 行〜)、D553 (22566 行〜)、D2172 項 3 (68552 行〜)、D2183 (69130 行〜) だけ。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/failures.md — F1019 (27738 行〜)、F81 (4418 行〜) だけ。
- 一次資料の原本 (読取専用、repo 外): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/ の `qsub-submit-pair.log`、`qsub-0001.stdout`、`qstat-after-submit-0001.txt`、
  `setup-submit-trees.log`、`hydrate-submit-tree-pair.json`、`evidence/attempt-0001/` (原文 job.stdout を含む)、
  `submit-tree-pair/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` (WAL `runs/wal.jsonl` / loop_state.json / s4_loop_digest.txt / campaign.lock / knowledge_manifest_receipt.json は cat / jq / sha256sum で読む)、
  `submit-tree-pair/output/env/pegasus/claims/p3-s4-loop-s4-autonomous-b24749ae.claim`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/dev-wave/workers.md — DW-S06-A。

repo root は /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair とする。

## 依頼 — 記録の事実照合 (docs-only、実装差分ゼロ、pair 不成立の記録)

本 wave は 1 job を投入し、候補は certified、stock は one-shot claim leaf で認可前に停止して pair 不成立、依頼の停止規則で正式停止した。実装面の差分は無い。
レビュー対象は **記録 (insight README / round 3 README の追記節 / 3 fragment / phase3.md / paper-story README / launcher insight の追記) が一次資料と一致し、
段 4 裁定 (`reviews/s4-ruling.md`) の主張限定を守っているか**である。次を検査せよ。

1. **数値・識別子の逐語照合。** insight §1 の表 (job / host / 時刻 / Elapse / 残 walltime / driver_rc / campaign id / variant / genome / admission の class・policy sha・receipt sha・
   src_token / build sha・時刻 / verify の verdict・commits・aborts・anomalies・commit_witness・proof_surfaces / bench の median・反復値・CV・settled・bench_wall・abort 率 /
   WAL・lock・loop_state・digest・受領証の sha256 / claim file の内容 / stock 期待 variant id) を原本 (WAL、run-summary-pair.json、compute-result.json、reservation.json、
   claim file、job.stdout / job.stderr) と突き合わせ、不一致を全て挙げよ。sha256 は `sha256sum` で再計算せよ。abort 率の百分率換算 (9.155% / 18.9%) も検算せよ。
   round 3 README の追記節と worklog fragment と paper-story README の追補に書いた同じ数値も照合せよ (転記ずれ)。
2. **主張限定の遵守。** 「pair が取れた」「stock に勝った / 負けた」「4 巡を閉じた」「診断の効果」「改善 / 退行 / 再現」「stock は失格 / 非 STOCK」「inert 不成立」に当たる文言が
   記録のどこにも無いか。逆に必須の限定 (STOCK 性未確認・pair 不成立・再投入なし・4 巡目未投入・候補の再評価は非同時刻の追加評価・claim file は削除も退避もしていない・
   condition gate は正常復帰していた・claim 以外の原因なし) が欠けていないか。
3. **依頼の逐語との対応。** `verbatim/T-2795-pair-origin.md` の停止規則 (「成立しなければその走を対照成立と認定せず報告して止める (再投入で救済しない、admission gate の pin
   正規化は裁定パッケージ候補のまま触らない、規律 2 を緩めない)」) と scope 外 (B-5 β・launcher 改修・仮想リスク向け gate) を、記録と裁定が守っているか。「投入は 1 回」を
   `qsub-0001.stdout` と `evidence/` の attempt 数で確認せよ。
4. **可逆最小正規化の記述。** `evidence/attempt-0001/job.stdout` と `reviews/consult-a.md` の原文 / 正規化後の sha256 と byte 数、`diff -w -B` 一致の主張を再計算で検証せよ
   (原文は repo 外の job root)。
5. **fragment の形式。** worklog fragment (H2 2 つ、`更新` の base digest、title の `[T-2795]` が `更新` に置かれているか)、failures fragment (`## 再発` の `### F1019` 見出しと
   `- **再発: 日付** —` の 1 item、新 F を採っていない)、decisions fragment (H2 が `## {{D:slug}}. 題` の形、題末尾に日付なし、本文に有効な `[T-数字]` を例示していない —
   注意: 本文の「D2172 項 3」等の D 参照は可) が各 README の規則に適合するか。placeholder `{{D:k2-pair-one-shot-claim}}` の綴りが 3 fragment で一致するか。
6. **機構の記述の正確さ。** insight §2 の code 記述 (claim path、`O_EXCL`、`_scan_protocol_conflicts` の除外、D464 の射程、`IZANAGI_EXPLORATION_OUTPUT_ROOT` が claim と layout の
   両方を動かす、`OTHER` site の test は claim 分岐に入らない) を `orchestrator/campaign/campaign_claim.py`、`loop.py`、`layout.py`、`env_contract.py`、
   `orchestrator/tests/test_p3_s4_loop.py` の該当箇所で file:line 付きで確かめよ。誤りがあれば挙げよ。
7. **過剰・欠落。** 記録すべき一次資料で欠けているもの、逆に repo へ複製してはいけない campaign 成果物 (WAL / lock / digest / claim / 受領証) が複製されていないか。
   paper-story README の追補が「凍結稿は書き換えない」規則 (同 README の系列規則) を守っているか (稿本文は不変か `git diff --stat` で確認)。

各所見は real / refuted、file:line、成果物影響 1 行 (DW-G05) を付け、must-fix / should / nit に分けよ。実装や新 gate の提案はしない。
書込みは禁止 (Bash 経由のリダイレクト・sed -i・tee も禁止)。テスト実測は親が行うので pytest 緑を要求しない (静的検査でよい)。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

markdown。`## must-fix`、`## should`、`## nit`、`## 照合した数値 (一致)`、`## 総括` (GO / NO-GO と理由 3 行以内)。
