md_11: 比較相手の Cicada を較正し、最良の設定を決める (主 baseline の準備)

最初に同じ directory の common.txt を読むこと。

■ 台帳の項目の探し方
この wave に対応する item はまだ無い。段 9 の main 取り込みの後に docs/worklog.md の「次の一手」で「比較相手の Cicada を較正」を grep し、無ければ新規 item として登録する。

■ 目的
出典メモ §25・§28.1 と最初の版 §9 は、主比較を「最適化と GC 設定を調整した Cicada」とし、「GC 間隔を不適切に大きくした Cicada だけに勝っても不十分」とする。
提案の性能値を意味のあるものにするには、先に比較相手を公平に強くしておく必要がある。2026-09-29 時点で、CCBench の Cicada の最適化フラグ空間
(orchestrator/campaign/genome.py の CICADA_SPACE、2^5) の定義はあるが、Cicada 用の較正 (レコード数・測定のばらつきの幅) の記録は見当たらない。

■ やること
1. 既存の較正の仕組み (calibrator の役割、D19 の within-run / between-run の 2 種の noise floor、既存 protocol の較正記録) を読み、Cicada に同じ手順を当てる。
2. レコード数を calibrator の方針で決める (cache miss 率が飽和する最小、絶対規律 4)。対象 workload は VHash の評価で使うもの (通常の YCSB の read / write 比数種、長い tx の 2 型 = 操作数が多い型・読み取り後に待つ型) に限る。
3. between-run の noise floor を Cicada で実測する。
4. 最適化フラグ (CICADA_SPACE) と gc_inter_us の組を、workload ごとに trace も計器も外したビルドで測り、最良の設定と「最良から floor 以内の設定の集合」を決める。フラグの組み合わせの制約 (genome.py の _cicada_promotion_requires_inline_opt 等) を守る。
5. 図にする (生成器付き): workload 別の設定ごとの throughput、gc_inter_us と throughput。

■ 成果物
- 一次資料: output/insights/<着手日>/vhash-cicada-baseline-tuning/README.md (較正の根拠、条件表、floor、最良設定と同等集合、図、限界)。
- driver が要るなら新規 file (Codex author)。既存の campaign driver は編集しない。
- spool fragment (新規 item を完了または更新)。

■ 所有
自分の一次資料・新規 driver・fragment。patches/ と cc/cicada の改変はしない (stock のまま測る)。tools/vhash_forwarding_model/ は触らない。

■ 注意
- 条件数 × 反復 × 1 条件の所要を先に見積もり、合計 2 node 時間以上なら common.txt 3 のとおり投入せず止める (条件の絞り方の案を添える)。
- 条件は複数ノードへ割って同時に投げる。同時刻の対照を置く。
- md_2 (Cicada の計器入り実測) も計算ノードで走っている。同じノードに同居させない (計測前に単独性を確かめる、runbook の作法)。
- 計測して数値を書く wave なので、段 3 の相談 1 本と段 6 の review 1 本は省かない。
