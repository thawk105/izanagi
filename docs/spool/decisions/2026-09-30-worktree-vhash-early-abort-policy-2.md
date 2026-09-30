---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: worktree-vhash-early-abort-policy
seq: 2
---

## {{D:vhash-early-abort-policy}}. 構成 E の早期 abort は「前進を試し、前進できず commit できないと確定したときだけ abort」(方策 c) を推す。確定の判定は committed / deleted の witness だけで言う

**決定:**
1. 「abort が決まっている」の判定 D は、read-only でない tx の read set の各要素について、既読版より新しく自分の現在の ts より古い committed / deleted の版が版列にあること、とする。pending は含めない。既読版に辿り着けなければ偽 (abort しない側)。D は共有状態を書かない。
2. 構成 E の組み合わせとしては方策 c (E-max を試し、要求が `no_room` を返したときだけ D を評価し、真なら abort) を推す。方策 b (前進せず、待機 slice ごとに D を見て abort) は単独では採らない。
3. md_21 §4.3 の「成功前の `no_room` = abort が決まっている」という読みは使わない。`no_room` の上端は pending も含むので確定ではなく、確定は D で言う。
4. 主張の範囲は、現行 genome (INLINE_VERSION_PROMOTION=0)、read-only でない tx、前進成功後の遷移は W* を仮定、小モデルの有限範囲、とする。

**理由:**
- 同時刻の計測 (skew 0.6 / 0.8 / 0.9 / 0.95、3 rep) で、同じ rep 内の差の中央値 c − E-max は 0.6 で −0.07 ms、0.8 で −1.8 ms、0.9 で −2.9 ms、0.95 で −4.1 ms。E-max が効かない高い偏りで回収境界の遅れが縮む。b − E-hb は −0.2〜−1.8 ms に留まる。回収境界は長い thread の下限の最小で決まり、上書きされていない試行は b では前進しないので境界を押さえ続ける。c は前進できる試行を前進させ、前進できず確定した試行を終える (一次資料 §5.1)。
- D の健全性は小モデル (validation を D と独立に保存 pointer から辿る写し、GC の切り離しと再利用を含む) の 2 tx 全列挙・3 tx 予算内列挙で違反なし、壊した判定 2 種は validation 成功までの反例を出す (一次資料 §3.1)。
- read-only + promotion 有効の構成では、保存した later_ver_ の pending が abort した後に D 真でも commit できる列がある (段 3 相談 A)。現行 genome の外なので D の対象から外し、範囲を明記する。
- 正しさ検査 (最良 genome の trace build、8 run) で巡回 0・保持版の変化 0・「D が真だったのに commit した」試行 0 (上限 indeterminate、一次資料 §7)。

**却下した選択肢:**
- `no_room` をそのまま abort の条件にする — pending を含む上端なので commit できる tx を殺しうる。実測でも成功前の `no_room` のうち D が偽の例がある。
- b を単独の方策として推す — 回収境界の遅れがほとんど縮まない (上記)。
- 早期 abort を AggressiveGC の代わりに位置づける — AggressiveGC は必要とされうる版を回収して tx を殺す提案で、本方策は commit できる tx を失わない代わりに、上書きされていない長い tx が押さえる分は残す。役割が違う (一次資料 §9)。
- 実機の shadow 照合 (「D が真だったのに commit」= 0) を D の健全性の証拠に数える — 壊した判定 (pending を含める) が実機で到達せず、照合の検出力を示せなかった。健全性の主張は小モデルに置く。
