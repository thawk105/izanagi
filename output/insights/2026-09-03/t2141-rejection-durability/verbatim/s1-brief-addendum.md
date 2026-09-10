# [T-2141] 段 1 brief への追記 — 親の provisional 前提の訂正

段 2 の投入後、親が実コードで確認して自分の前提を 2 件訂正した。**brief 本文の (P1-a) と (P1-c) は
この追記で上書きされる。** 以下も引き続き検査対象である。

## 訂正 1 — (P1-c)「rejection は publication root 内に置くしかない」は成り立たない

`p3_b4_prerun_issuer.py:362-366` の `_normalize_planned_results` は、planned result artifact path に
**canonical な絶対 path であること以上を要求していない**。publication root の下にある必要は無い。
課される条件は次の 4 つだけである。

- attempt_id 集合が scheduled batch と完全一致すること (`:369-379`)
- path が一意であること (`:380-385`)
- 厳密な祖先衝突が無いこと (`:386-397`)
- issuer の固定 artifact と衝突しないこと (`_reject_fixed_artifact_conflicts`, `:418-440`)

したがって consumer の実入力は「publication root の 3 つの固定 artifact + receipt が名指す
planned path 群」である。rejection 記録を planned path の兄弟に置く設計も選択肢に入る。
どちらが最小かは段 4 の択一とする。

## 訂正 2 — (P1-a) の射程

`assemble_b4_raw_analysis` は manifest の全 row について planned artifact の実在を要求し、
1 件でも欠ければ `INCOMPLETE_SET` で assembly 全体を棄却する
(`p3_b4_raw_record_producer.py:1908-1916`)。

つまり現状の欠陥は「棄却された候補が見えない」だけではない。**1 件棄却されると assembly が
理由を言えないまま丸ごと止まる。** 実験母数そのものは issuer receipt の
`scheduled_attempt_count` と `planned_result_artifacts` から復元できるが、各 absent が
**なぜ** absent か (棄却された / deferred / 未試行) が無いため、material report は
不完全集合の内訳を述べられない。

## 参考 — 既存の report 側の扱い

`p3_b4_material_report.py:673-679` は **その場で観測した** assembly rejection を
`status="rejected"` として projection している。欠けているのは、過去に
`publish_b4_attempt_result` が返した個々の rejection であり、それはどこにも書かれていない。
report 側の非保証 2 件 (`:53-58`) はこの区別を保っている。
