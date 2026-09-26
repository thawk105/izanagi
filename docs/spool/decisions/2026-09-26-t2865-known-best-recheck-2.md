---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: t2865-known-best-recheck
seq: 2
---

## {{D:silo-policy-known-best-recheck}}. 既知最良 (静的 10 µs) を 3% 超えた silo-function-policy の IR 3 点を別 job で 1 回ずつ再測し、計測前に固定した判定規則で 3 点とも「再現」とした

**決定:** D2243 項 1 (論文でこの 3 点を既知最良超えとして書く前に別 job 再測) を実施した。記録の正本は `output/insights/2026-09-26/t2865-known-best-recheck/README.md`、段 3・段 4・段 6 の逐語は同 dir の `verbatim/`。

1. **機構:** 既存の偵察 driver (`silo_policy_recon.py run --phase compare --job <0|1|6>`) をコード変更なしで、1 job 1 ノードの generic dispatch で 3 本投げ直した。job の中身は D2240 の compare job と同じ (対象点 + 同 job の相方 IR 1 点 + abort0・stock・`B0-L-W0`・fixed10、実行順も同じ)。相方点は判定に使わない。
2. **判定規則 (計測前に insight §1 として commit):** 束縛 (case 列・IR 本文 sha256 と因子・対照 genome・fixed10 の実効 define・workload・source evidence・別 job の識別) が不成立なら判定不能、束縛成立後に対象点の verify / trace0 失敗なら失格、他の不適格・high-abort は判定不能、残りは同 job の参照 3 本の中央値の最大に対する比 r' が 1.03 超なら「再現」、以下なら「非再現」。投げ直しは起動前失敗か対象点の行が無い場合だけ 1 回、採用試行は結果を開く前に固定。
3. **集計:** 既存 `compare-aggregate` は 8 job 揃いと現行 PIN 一致を要求するので、driver の関数を import して per-job の照合と比を再利用する repo 外スクリプト (Codex author) で判定した。新 job に当てる前に、元の 8 job で既存集計と 16 点完全一致、負例 3 本が期待どおりであることを確かめた。
4. **結果:** 3 点とも「再現」 — r' は 1.051・1.065・1.073 (D2240 では 1.068・1.069・1.062)。3 job とも最良参照は fixed10。18 方策すべてが両 verify で serializable・trace0 clean。投げ直し 0 本。計測 3 job の Elapse 合計 2,318 秒。

**理由:**
- 判定規則を結果の前に固定しないと、再現の定義を結果に合わせて選べる (規律 3)。分類の優先順位と投げ直しの条件は段 3 相談の must-fix。
- 既存 driver の投げ直しは依頼の「本題だけ」に合い、元の job と同じ構成で比べられる。単点 mode の追加はコード変更になる。
- r' は元の選択に使っていない値で、論文に「別 job 再測でも既知最良を 3% 超えた」と書く根拠になる。

**却下した選択肢:**
- 単点だけを載せる compare mode を driver に足す — コード変更で依頼の範囲外。相方点を判定から外せば足りる。
- 元と新の比を平均して判定する — 元の値は選択に使った値で、選択の上振れを判定へ戻す。
- 5 rep の完全分離 (最小 > fixed10 最大) を主判定に入れる — 論文の記述より強い条件になる。補助指標として記述した (3 点とも成立)。

**限定:** 各点 1 回の再測で、統計的な優位・16 点の選択全体を補正した有意性・別 workload への転移・fixed10 以外の静的値との比較については何も言わない。対象点の job 内位置は元と同じなので、位置や job 内の交絡から独立した再現ではない。CCBench は元 `e9e477ca`、再測 `68106660` (確認した差分は `cc/mocc/transaction.cc` だけ)。点 ID・比は段階 E / F の coder・planner の入力へ流さない (手順書 §3-D)。診断 build は NON_ADMISSIBLE。
