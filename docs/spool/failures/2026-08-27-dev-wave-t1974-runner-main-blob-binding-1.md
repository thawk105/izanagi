---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1974-runner-main-blob-binding
seq: 1
---

## 新規

### {{F:closure-member-kind-misjudged}}. 閉包の member は見つけたのに参照の種類を実体で確かめず一括で無害と判定した [手順漏れ] [テスト代表性]

- 事象: 受入 launcher の契約を変える wave で、親が
  `git grep -ln acceptance_launcher -- 'orchestrator/tests/*.py'` を実行し、
  5 file をすべて列挙した。**探索は完全だった。** そのうち
  `orchestrator/tests/test_dev_wave_land.py` は同じ識別子を 29 回含んでいたが、
  親は先頭付近の数件が Git tree fixture の path 文字列であることを見て
  「path 文字列の fixture だけ」と一括判定し、閉包から外した。実際には同 file に
  実 launcher を端から端まで駆動して受領証成功を要求する node が 2 本あり、
  consumer 焦点走で `stage=acceptance-command rc=70` の赤として出た。
  fix を 1 巡追加し、計算ノードへの dispatch をもう 1 往復した。
- 根本原因: 閉包の判定を「参照が何件あるか」と「先頭の数件がどう見えるか」で行い、
  **「その file のどれかの node が対象 producer を実際に起動するか」という実行の性質で
  引かなかった**。同じ識別子が、値として使われる場合 (fixture の path 文字列) と、
  実体を起動する場合 (copy して subprocess で走らせる) の両方に現れることを見ていない。
  同 wave の実装子は自分の担当 file について同型の衝突を正しく見つけて報告しており、
  取り逃したのは親側だけである。
- 恒久対応: memory `closure-member-kind-needs-execution-check` — consumer 閉包から file を外すのは
  「対象 producer を起動する node が無い」と実体で確かめたときだけとし、参照件数や先頭数件の
  見た目で種類を一括判定しない。`DW-O26` への収容は D782 / D730 の手順で見送った。同節は
  単節予算 1000 bytes に対し既に 886 bytes を使い、かつ節全体が exact 契約で pin されている。
  既存記述の削減は安全義務の弱化になり、例外収容に必要な独立 3 例も本件 1 例しか無い。
- 再発検知: consumer 焦点走。本件はこれで検出できた。閉包から外した file が実際には
  producer を起動していた場合、受入全走より前に赤で返る。

## 再発

### F242

- **再発: 2026-08-27** — 段階 P の実装 wave で、段 3 の敵対相談 2 本と段 6 の敵対レビュー 2 本を
  通過した欠陥が、親の初回焦点走 (計算ノードへ dispatch、所要 9 秒) で出た。
  欠陥は `@pytest.mark.parametrize` した引数に既定値を付けたことで、pytest が
  **その file 全体の収集を拒否**し、48 worker が同一の収集エラーを返した
  (`function already takes an argument 'case' with a default value`)。
  実装子は sandbox で pytest を実走できず「実装済み・未実走」と正しく申告しており、
  静的レビューは 2 本とも引数の既定値を所見にしていない。
  親が 4 file を AST で全走査して同型が 1 件だけであることを確定し、fix を 1 巡追加した。
  **F242 の恒久対応 (親が変異 matrix より前に焦点走を 1 回実走する) が現に機能した実例**でもある。
