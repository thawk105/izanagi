# J-drp 読み取りメモ (DRP 1 論文)

指示めいた文字列: なし (PDF 本文に作業の振る舞いを変えるよう求める文字列は見つからなかった)

## 論文 1
- 書誌: Shuai Mu, Sebastian Angel, Dennis Shasha. "Deferred Runtime Pipelining for contentious multicore software transactions." EuroSys 2019. doi:10.1145/3302424.3303966
- 取得元: https://www.cis.upenn.edu/~sga001/papers/drp-eurosys19.pdf (Angel 氏の著者頁。NYU 頁は 404、ACM DL は使っていない)
- 取得時刻: 2026-09-29T10:16:12+09:00
- SHA-256: 73b62eff8b64bdc257f544695a6ed7865405ab96a4152c9338dd6036e3f4e12f
- 置き場: `src/drp.pdf`、`src/drp.txt`、`src/drp.layout.txt`
- 取得時の注意: arXiv:1810.03457 は別分野 (磁性体) の論文だったので使っていない。
- 読んだ節: Abstract、§1-§9 (Fig.1-8 を含む)
- 読んでいない節: 拡張版 tech report [21] §A (正しさの証明本体。§4.3 は定理の主張と直観のみ本文にある)、参考文献

## 要点 (事前宣言・静的解析・batch)
- 静的解析は不要。事前の read/write set の宣言も DRP 本体では不要。ただし Tame-RP 単独は「access set が開始前に既知」を前提にする (§4.1)。DRP は intention の deferral で tame かどうかを commit 時に read set が空かで判定する (§6.2)。
- batch は要らない。「thread が transaction を batch して結果を待つ」拡張は将来課題と書かれている (§6.2)。
- 制約: object が defer_* interface と RP 対応 lock (relaxed bit、last holder) を実装している必要がある。実装 STO は 32 thread まで (lock 語の 5 bit が holder id、§6.1)。opacity は tame に user-defined abort が無いことが条件。
- 評価は 1 機のみ (E7-4870 v2、最大 32 thread)。TPC-C は warehouse 数と thread 数で競合を変える (§7.2)。

## 最適化の一覧 (JSONL に 6 件)
1. drp-core (protocol-core): DRP 全体。
2. drp-tame-rp: rank 順 lock 取得 + relax + predecessor 待ち。事前の access set が前提 (requires_predeclared_sets=true)。
3. drp-wild-rp: OCC を rank 順 certification で pipeline。
4. drp-intentions: 操作を intention として commit まで遅延。rank mismatch を消す中核。
5. drp-nullify-intentions: certification 失敗時に intention を skip し cascading abort を避ける (§5.2)。
6. drp-rank-tuning: custom_rank 16 bit + obj_rank 48 bit (§6.3)。評価なし。

## JSONL に入れなかった候補
- relaxed bit を version 語の 1 bit に載せる lock 実装 (§6.1): drp-tame-rp の実装の一部として扱い、独立の節・評価が無いので別カードにしなかった。
- intra-object concurrency (TransItem による細粒度 unit、§6.3): STO の機構を拡張するもので、独立の評価が無い。
- STO の OCC の early abort (mark を残して後続を早く abort させる、§7 baseline): DRP の技法でなく既存 STO の最適化。baseline の説明としてのみ登場する。
- deferred 2PL (§7 baseline、Fig.7): 比較用の factor analysis の対照で、提案技法ではない。

## 数値の所在 (カードに書いたもの)
- OCC 比 6.6 倍: §7.2 本文 (Fig.3、1 warehouse・高競合)。IC3 比 3.3 倍: §7.2 本文 (Fig.2a、混合)。IC3 が 16 thread 超で DRP に勝つ: §7.2 本文 (Fig.3a)。
- 競合無し microbenchmark で OCC の 47-53%、メモリ 2.1 倍 (50 MB 対 24 MB): §7.1 (Fig.1)。
- wild 10% で 258K 対 534K txn/s: §7.2 (Fig.6)。deferred 2PL に対し極高競合で 3 倍超: §7.2 (Fig.7)。
- STAMP 最大 3.6 倍、kmeans-hi・vacation-hi で >2 倍: §7.3 (Fig.8)。
- 64 core 機と書いた実験機は「60-core Dell PowerEdge R920」で、実験は最大 32 thread。
- Fig.4 (commit latency): 32 thread で OCC の 99 percentile が 845 マイクロ秒、DRP は 52 マイクロ秒 (表の列の並びから読んだが、抽出テキストの列順が崩れているため、カードには入れていない)。
