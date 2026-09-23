# [T-2854] 単位 3 段 6 裁定 (親)

入力: レビュー A `out/s6-review-A-1.md` (正しさ境界・規律 1、GO、所見 0)、レビュー B `out/s6-review-B-1.md` (過剰・削除、GO、should 2)。

| 所見 | 判定 | 処置 |
|---|---|---|
| B-1 裁定 §3 C0 は C・C1'・C3 の 3 checkout を求めるが、probe は C・C3 の 2 本を取り出して tree 照合し、C1' は祖先と raw diff で照合する | real (should、裁定文の誤り) | 裁定文を訂正する (erratum): C0 は「C と C3 を取り出して tree と完全一致で照合し、C1' は祖先 (親 = C、C3 の親 = C1') と raw diff (C..C1' = header 2 file、C1'..C3 = mocc 1 file) で照合」。前 wave も C1 は取り出していない。probe は変えない。insight に実装どおり書く |
| B-2 計算見積り 0.1 node 時間の根拠 (M5m は 21 entry で前処理 84 本、build 対象が mocc) | 疑い (should) | 採用 (記述のみ)。見積りは前例 Elapse 191 秒に基づく暫定値と明記する。walltime 上限 60 分の 1 job でも 1 node 時間で、確認ライン 2 node 時間に届かない。実測 Elapse で再見積りする |
| A: 攻撃不成立 9 項・変異の前提 5 件 | — | 記録のみ |

- fix 子は起動しない (実装面の real 所見なし)。焦点再レビュー不要。
- C3 = `53f6b09757331ac7200f3f6bb5d526a676480fe3` のまま計算 job へ進む。C3 の message の `role=reviewer` 行は本レビュー 2 本 (gpt-6-astra / medium) を指す。
