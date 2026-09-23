単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2860-k2-round4-reflux

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- W = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2860-k2-round4-reflux (repo root)。レビュー対象は `git diff 3886a1fd3..HEAD` の 5 file:
  `W/output/insights/2026-09-23/t2860-k2-round4-reflux/` 一式 (README.md、verbatim/、materials/、layer3_report.json、logs/、reviews/)、
  `W/docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md` (新 results 稿)、`W/docs/paper-story/README.md` (results 表の 1 行と stale 注記の項目 4)、
  `W/docs/spool/worklog/2026-09-23-dev-wave-t2860-k2-round4-reflux-1.md` (worklog fragment、書式正本は `W/docs/spool/README.md` と `W/docs/spool/worklog/README.md`)。
- 段 1 / 4: `W/output/insights/2026-09-23/t2860-k2-round4-reflux/reviews/s1-brief.md`、`s4-ruling.md`。
- 4 巡目の生成・評価の記録と一次資料: `W/output/insights/2026-09-22/t2795-k2-pair-resubmit/` (README.md、verbatim/、materials/、evidence/)。
- 巡 1〜3 の一次資料: `W/output/insights/2026-09-16/t2588-k2-loop-roundtrip/evidence/`、`W/output/insights/2026-09-18/t2746-k2-loop-round2/layer3_report.json` と evidence/、
  `W/output/insights/2026-09-19/k2-loop-round3/` (README.md、layer3_report.json、evidence/、verbatim/critic-3.md)。3 巡稿 `W/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md`。
- 論文ストーリーの規則: `W/docs/paper-story/README.md` の「版の履歴」直後の節・「最新スナップショット以後に確定したこと」・「results 系列」節。凍結版 `W/docs/paper-story/2026-09-22.md` の §8 B-6 項 (「B-6. リーク制御」で検索)。
- 裁定: `W/docs/decisions.md` の D2211 (項 1 だけ)、D2194 (項 2 だけ)。
- repo 外の一次資料 (読取専用、job root J = /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2860-k2-round4-reflux): `J/setup-ao-root.log`、`J/ingest-real.log`、`J/layer3-r4.log`、`J/fix-registered.log`、
  `J/project-r4.log`、`J/project-pair.log`、`J/layer3_report.attempt1.json`、`J/critic-4-transcript.jsonl` (critic 子の transcript。大きいので jq / python で必要部分だけ読む)、
  `J/verbatim/critic-4.md`、glue (`J/*.py`、`J/*.sh`)、写し `J/ao-root/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` (runs/wal.jsonl、runs/agent_outputs.jsonl、loop_state.json、s4_loop_digest.txt、campaign.lock、knowledge_manifest_receipt.json は cat / jq / sha256sum で読む)。
  原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/submit-tree-r4/output/exploration/campaigns/p3-s4-loop-s4-autonomous-b24749ae/` と byte 複製
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922/` (MANIFEST.sha256、pair/、r4/)。原本には絶対に書かないこと。

## 依頼 — 記録の事実照合 (docs-only、計算なし、実装差分ゼロ)

本 wave は critic-4 を 1 回走らせ、planner-5 / coder-5 / critic-4 の AO を写しの campaign dir へ取り込み、層 3 材料レポートを作り、4 巡の results 稿と README の stale 注記を書いた。
次を検査せよ。

1. **数値・識別子の逐語照合。** insight README と results 稿の表・本文の数値 (sha256 と bytes、ao ref、WAL の verdict / commits / aborts / anomalies / median / 反復値 / CV / abort_rate、job 時刻・Elapse・host、
   比 2.493 / 2.366、差 +7.20% / +1.74%、trace abort 率、1 abort あたり commit 数、開示 14 項、source_refs 14 = 10 + 1 + 3、AO 32,549 B など) を一次資料と再計算で照合し、不一致を全て挙げよ。
   巡 1〜3 の表の値は巡 1 の job.stdout、巡 2・3 の layer3_report.json の events と照合せよ。
2. **量化と不在の主張。** 「4 巡とも certified」「同 job stock 対照は巡 4 の 1 回だけ」「実測の還流 3 回 / 診断の還流 2 回」「原本の runs/ は wal.jsonl だけ」「保護 5 file は写し・原本とも不変」
   「2 回の層 3 の差は noise_floor の key だけ」「critic は受領証と lock の本文を読んでいない」「Bash 8 本とも読取り」を一次資料 (log、transcript、JSON 比較) で裏取りせよ。
3. **主張限定の遵守。** critic-4 の attribution を本 wave の結論として書いた箇所、「候補 5 が候補 10 より良い」「固定が適応より良い (一般化)」「診断が効いた」「B-6 が閉じた」「K2 を必須経路に戻す」
   に当たる文言が無いか。逆に必須の限定 (比は記述値・この配線 1 点、stock は BACK_OFF=1、別 job 比較の禁止、原本消失、写しでの取込み、legacy critic で B-4 非適格) が欠けていないか。
4. **論文ストーリー・results 系列の規則への適合。** 凍結版 2026-09-22.md を編集していないか。stale 注記の項目 4 が「当時は真で後続が古くした」型として正しく書かれ、項目 3 との重複・矛盾が無いか、件数表記 (4 件) が正しいか。
   results 稿が「1 file = 1 結果」「一次資料から作る」「3 巡稿を改めない」を守っているか、出所の書き方に版・stale 注記・記録散文を数値の出所にした箇所が無いか。
5. **AO 取込みの妥当性。** 取込みが写しに対して行われ原本が不変であること、写しと原本の同一性の根拠、`--agent-wal-ref` が本走 WAL 全 10 record の canonical ref であること、
   AO の provenance の path、layer3_report.json の agent_outputs / mechanism_hypotheses / artifact_refs / noise_floor が記述どおりかを確かめよ。
6. **fragment の形式。** H2 がちょうど `## 本文` と `## 次の一手差分`、`完了` の `remaining: none` と `base:`、`更新` の `base:`、title の `[T-2860]` が `完了` に置かれていること。
   base digest は `python3 tools/spool_fold.py --base-digest '[T-2860]'` / `'[T-2808]'` (読取専用 lookup) で照合してよい。
7. **過剰・欠落。** repo へ複製してはいけない campaign 成果物 (WAL / lock / digest / loop_state / 受領証 / agent_outputs.jsonl) が複製されていないか。記録に欠けた一次資料は無いか。

各所見は real / refuted、file:line、成果物影響 1 行を付け、must-fix / should / nit に分けよ。実装や新 gate の提案はしない。
書込可能な tmp は無いので静的検査と読取専用コマンドでよい。書込みは禁止 (Bash 経由のリダイレクト・sed -i・tee も禁止)。テスト実測は親が行うので pytest 緑を要求しない。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

markdown。`## must-fix`、`## should`、`## nit`、`## 照合した数値 (一致)`、`## 総括` (GO / NO-GO と理由 3 行以内)。
