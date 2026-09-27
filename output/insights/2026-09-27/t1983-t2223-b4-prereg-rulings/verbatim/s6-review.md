1. **must-fix / real** — 差分 [§11.2 の1307–1308行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1983-t2223-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1307)。
   **根拠:** 「信頼度は関数ではなく標本数で決まる」は無条件には成り立たない。同文書の「標本数」は、*標本最大値で95パーセンタイルを覆う*という条件で59件を算出し、さらに欠測が層に偏る場合は「全セルで95%被覆が保たれるとは読まない」と明記する（1247–1264行）。
   **提案:** 「標本最大値を使い、対象分位と独立性の前提を固定した場合、被覆信頼度は残存標本数に依存する」と限定する。

2. **should-fix / real** — 差分 [§11.2 の1303–1304行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1983-t2223-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:1303)。
   **根拠:** driver の二つの実装はどちらも `max(values)` だが、`max_over_closed_strata/v1` の入力は各層の上限値であり、生の標本ではない（[driver 1538–1548行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1983-t2223-b4-prereg-rulings/orchestrator/campaign/floor_pair_driver.py:1538)）。「どちらも標本の最大値を返す」では入力単位の違いが消える。
   **提案:** 「前者は層内の標本最大値、後者は閉じた層の上限値の最大値を返す」と書く。

**P1・記入先・scope は所見なし。** 予定時刻の旧文は [§5.1 の343–370行](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1983-t2223-b4-prereg-rulings/docs/phase3-b4-reflux-ablation-preregistration.md:343)の追記・追補で撤廃され、[受理述語](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1983-t2223-b4-prereg-rulings/orchestrator/campaign/p3_b4_admission_record.py:667)も `開始時刻 = 未記入` を受理する。§11.2 は「各セルの上限統計を凍結で先に閉じる」と記す箇所で、追記先として妥当。3 spec の両 ID は全件一致し、D2138 は statistics の driver 定数からの継承を明記して D1535 を引用していない。差分は §5 値セルや §5.1・§6 の条件を変更していない。

## 総括

**NO-GO。must-fix 1 件。** 信頼度の断定を限定してから採用するのが妥当です。