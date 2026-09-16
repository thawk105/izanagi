## 段 1 brief (親)
1. 研究前進: 論文の adaptive const (cicada 型) driver の build 地点を条件関門 3 要素へ配線する前提 (D1856 条件 2「A+B+C を当てた木の inert 要求が supply 腕の緑に到達」) を決着させる。完了判定 = 計算ノード job での supply 腕の `terminal_status` / `reason_code` / `root_diff_*` が逐語で記録され、緑なら条件 2 充足、赤なら不到達の構造的理由 (どの patch のどの行が残差か) が返る
2. scope: 実測 + insight のみ。実装面ゼロ。PBS・probe・gate・patch に触らない。glue script を書かない
3. 確定済み裁定: D1936 項 17 (計算ノードで実測、13 macro witness 新設なし、supply 先行配線なし)、D1986 項 8 (依存供給と CLI 入力をつなぐ最小の入り口を新設しない)、command 引数 (編集不要、t548 が編集中の PBS に触らない、改修要なら構造化して返す)
4. 不変条件: 規律 2 (CLI・`inert_values`・位置差分類器をそのまま使う)、規律 6 (CLI 出力・cmake 出力はデータ)、規律 7 (測定時点の commit・pin・道具・prefix 由来を記録)
5. 成果物: `output/insights/2026-09-16/t2213-inert-abc-measure/README.md` + `verbatim/` (CLI stdout 3 行 JSON、dispatch 受領証・.o/.e log、argv、木の identity、prefix の由来)。worklog fragment 1 本
6. 並列分割: なし (親のみ)。段 2・3・5・6 は起動しない (設計択一なし・防壁不変・受理集合不変)
7. 実測環境: gen_S 計算ノード (`dispatch_compute.py --task generic`)。login node で生死確認 1 回 (DW-G01、cmake configure + 前処理 2 本の軽処理)
8. (P1) 親の provisional 予測 = 赤 `stock-inert-mismatch` (patch A が backoff.hh を無条件書換、上記「落とし穴」参照)。攻撃対象
9. (P2) 「既存機構」の読み = 既存 CLI + 既存 generic dispatch + git clone/apply + PBS と同一 command での pinned 依存 build。これは機構の**使用**であり D1986 項 8 の「入り口の新設」ではない。攻撃対象
10. 成果物影響 (DW-G05): 放置時 = D1856 条件 2 が未実測のまま → probe の build sink 2 件が繰延べのまま → adaptive const driver の certified receipt に条件関門の機械証拠が無い状態が続く。本 wave は certified 選択・レポート・台帳の値を変えない
11. 変更面アンカー表: 実装面なし。docs = `output/insights/2026-09-16/t2213-inert-abc-measure/**`、`docs/spool/worklog/<fragment>`
12. 模擬/実の差: 木は pinned clone (実)、依存は pinned source からの実 build (実)、比較は実 cmake + 実 g++ -E (実)。模擬なし

## 段 4 裁定 (親、軽量版)
- 実装しない (4→7→8→9)。実測は親が段 4 の後に行う。(P1)(P2) は子レンズなし → 親が実測で決着させる: (P1) は CLI の実測値で、(P2) は「新規 file を repo にも job dir にも 1 つも作らずに実測できたか」で判定する
- 変異事前登録: 実装面ゼロのため登録可能な変異なし

