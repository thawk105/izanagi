---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2826-resume
seq: 2
---

## 再発

### F1

- **再発: 2026-09-21 (near miss、2 件)** — [T-2826] の前 wave (entry 1800) の親が、段 5 author の prompt に段 4 裁定 §4 の判定式を**手で要約して**書いた。(1) R8 の候補抽出で裁定の「session の作成時刻」を「dir の mtime を近似に使ってよい」に置き換え、(2) R6 (ii) の予測から「worker の待ちが伸びる」を落とした。再開 wave (`dev-wave-t2826-resume`) は起動引数どおりこの prompt を雛形にして wave 固有値だけを差し替えたため、集計器がその要約どおりに実装された。段 6 の read-only review が must-fix 2 件として捕捉した。親が作成時刻 (stat の birth time) で全 2,207 session を再照合して全セル候補 0、R6 は 3 条件で出し直して的中のままで、結論への実害は無い。転写元が裁定 file の逐語でなく親の要約である点で、2026-09-20 [T-2804] の再発 (裁定の literal を prompt へ手打ち) と同型。一次資料 `output/insights/2026-09-21/t2826-modify-timing-resume/README.md` §8、同 `verbatim/s6-review-out.md` 所見 1・2。恒久対応は変更なし — memory `ruling-literals-in-prompts-point-to-the-file` (判定式・定数・文面は裁定 file を正本と指し、逐語は file から機械的に切り出す) を、前 wave の prompt を雛形に流用する再開 wave にも当て、判定式の節は投入前に裁定 file の逐語と照合する。
