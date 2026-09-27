# [T-2849] (3) MOCC 疎通の計算確認 (D2212 項 4、逐語)

- 提示: 2026-09-26 22:4x JST (見積り = estimate.md)。回答の受領: 2026-09-27 07:27 JST 以前 (AskUserQuestion の戻り、正確な回答時刻は不明)。
- 問い (逐語): 「MOCC 疎通の本投入の計算確認です (D2212 項 4)。単価実測 3 job (3 workload とも stock が certified・品質 normal) の実測単価で見積りました。1 slot の所要は write-heavy 212 秒 (同時検査)、balanced 346 秒、read-heavy 760 秒 (直列検査) で、費用の大半は read-heavy の正しさ検査です。どの規模で投入しますか。」
- 択: 「20 候補 × 3 workload (推奨)」(約 10〜14 node 時間、中心 12.5) / 「40 候補 × 3 workload」(約 20〜26) / 「write-heavy と balanced だけ」(約 5〜7) / 「今は投入しない」
- 回答 (逐語): 「20 候補 × 3 workload (推奨)」
- 親の解釈: 案 A (18 job・93 slot) の投入の承認。見積り上側 14 node 時間を超えそうなら新しい投入を止めて再確認する。
