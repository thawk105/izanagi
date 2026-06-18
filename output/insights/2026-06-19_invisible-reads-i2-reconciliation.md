# 発見: invisible reads は read-heavy で効く (phase1 の「write-intensive」は誤帰属) + ablation knob の交絡

- **発見日:** 2026-06-19 (Phase 1 タスク5b, env=linux-baremetal)
- **種別:** Izanagi の **doc 誤記 (I2 の取り違え)** + **計測方法論の交絡** (CCBench のバグではない)
- **重大度:** 中 (タスク5b の検証基準そのもの。docs/phase1.md を訂正、計測の使い方を明確化)
- **還元判断:** 上流 PR 不要 (CCBench のバグでない)。Izanagi 側の doc 訂正で完結
- **検証:** 3レンズ調査 + 敵対的裁定 workflow (`verify-invisible-reads-interpretation`, 4 エージェント
  229k tok) + perf カウンタ実測で機構確認

## 何を測ったか

"invisible reads" は Silo に内在しフラグでない (anatomy §3)。on/off の唯一の手段は MOCC の
`temp_threshold` gflag (大=誰もロックしない invisible、0=全 read が visible read-lock)。
同一 MOCC バイナリで read 比率を振って invisible vs visible の throughput を実測 (1m/48thread/
skew0.9/rmw=false, reps=5):

| rratio(読み%) | invisible tps | visible tps | inv/vis | CV |
|---|---|---|---|---|
| 0   | 2,292,243 | 1,322,901 | **1.733x** | 6.6/5.3% |
| 25  | 805,840   | 658,514   | 1.224x | — |
| 50  | 773,786   | 655,069   | 1.181x | — |
| 75  | 968,061   | 818,017   | 1.183x | — |
| 100 | 9,324,635 | 7,277,139 | **1.281x** | 0.11/0.85% |

素朴に見ると最大倍率は rratio=0 (write-only) の 1.733x。これを「invisible reads は write-intensive
で効く」(docs/phase1.md:145 の I2) と読むと**誤り**。

## 交絡: temp_threshold は write 経路の lock も gate する

MOCC ソース精査 (workflow lens1):
- `temp_threshold` は read だけでなく **update (`transaction.cc:361`) / delete (`:468`) の write-lock
  も gate する** = 温度ベースの「悲観ロック vs OCC」セレクタ。read 専用トグルではない。
- **rratio=0 では READ op が 0** (`include/ycsb.hh:65`, op=READ iff rnd%100<rratio)。よって read-lock
  分岐 (`:198-204`) は構造的に一度も実行されない。1.733x は invisible reads では**ありえない**。
- 正体: temp_threshold=0 だと write-only でも全 write が `lock(tuple,true)` を呼び、CLL violation
  検出ループ (`:642-663`)・trylock 失敗 abort (`:672-733`)・RLL 再取得 (`:736-783`) のコストを毎 write
  払う。temp_threshold=100000 だと validation 時の write-set lock (`:895`) 1回に減る。
- つまり rratio=0 の 1.733x は **temperature-gated 悲観 write-locking の有無** (別最適化, anatomy [B]
  系) の効果であって、invisible reads (read 可視性, anatomy [A]①) ではない。anatomy §3:117 の警告
  「mocc は read 可視性以外も異なる」の、**同一バイナリ gflag 内**版。

## クリーン点 = rratio=100 (read-only): invisible reads は ~1.28x、read-heavy

- rratio=100 は WRITE op が 0 なので write-lock 分岐 (`:361`) が不発 → 両 arm の差は **read 経路だけ**に
  局在 (visible shared read-lock vs OCC re-read `:218-265`)。同一バイナリの gflag 差なので abort/RLL
  機構は byte-identical (silo-vs-mocc 比較でないので anatomy の警告は噛まない)。
- 効果 **≈1.28x** (9,324,635 vs 7,277,139 tps)、CV 極小 (0.11/0.85%)。
- **機構を perf で確認** (per-transaction 正規化, trace-disabled build): visible は invisible より
  cache-misses が **+32%/txn** (35.6 vs 27.0), cache-references +16%/txn, LLC-load-misses +16%/txn。
  visible read-lock は共有 rwlock 語への atomic RMW で hot(Zipf) key の cacheline を並行 reader 間で
  bouncing させ coherence traffic を増やす。invisible read はこれを回避。→ **1.28x は lock-semantics
  由来の coherence コストであって単なる帯域節約ではない** (敵対的 dissent #2 を perf で解消)。

## I2 の裁定 (docs 訂正)

- **roadmap.md:94「read-heavy phase での cache 汚染削減」が正しく、phase1.md:145「write-intensive で
  効く」は誤り。** 両者は別機構を捉えており統合でなく**訂正**が要る: phase1 は rratio=0 の大倍率を見た
  が、それは invisible reads でなく write-path locking の効果という取り違え。
- CCBench 論文 (Tanabe et al., VLDB 2020) は invisible reads を CPU-cache 最適化 (キャッシュライン汚染
  削減) に分類 → read-heavy 寄りが論文に忠実 (workflow lens2, confidence high)。

## 残る限界 (正直に記録, dissent)

- rratio=100 は read-only = read-write 衝突/abort が皆無の無競合領域。1.28x は「共有 read-lock の
  coherence overhead 上限」であって、read-lock が writer を block/abort する実混在ワークロードでの
  benefit とは別。中間点 (25/50/75 が 1.18-1.22x, 50 が谷の非単調) はその混線の指紋で、混在の真の効果
  は単一値にできない可能性。→ **invisible reads の効果は「rr100 を on-mechanism anchor、rr0 と中間点は
  off-mechanism」として曲線全体で報告するのが安全。**
- 中間点は CV 未報告 (安定性未検証) なので結論はそれらに依拠していない。

## タスク5b への含意

- invisible reads の効果計測には **rratio=100 (read-only) のみ**を使う。rratio=0 は temperature-gated
  write-locking、中間は read/write lock 混線で off-mechanism。
- この一件は**評価パイプラインが「もっともらしいが誤った帰属」を露出できた**実例 (gflag 内交絡を
  コード + perf + 敵対的検証で剥がした)。タスク5 の完了条件「評価パイプラインが信頼できる」の傍証。
