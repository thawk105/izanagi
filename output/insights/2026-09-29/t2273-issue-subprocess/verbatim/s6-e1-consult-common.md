## 事実 (親の実測、2026-09-29 07:3x JST)

- 事前登録 (`/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/s4-ruling.md`「計測の事前登録」2〜6) は前 wave (a) の計測 probe をそのまま使い、E1 を「A/B の login collection 差が本 wave の追加 node だけ、かつ A/B 共通 node の 3 shard への割付が完全一致」と定めた (移植元の判定式、`/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/probe/t2273is_ab_analyze.py` の `e1_pair_check`、238 行付近)。land 判定量は shard-0 の W_0 の対差 (3 対すべて正、対率中央値で区分 i/ii/iii)、5 分判定は B の W_max 中央値、W_1・W_2・pre・post・O_max は補助量で判定に使わない。
- 系列は 01-A、02-B の 2 走が rc=0 で完了し (infra 失敗なし)、03-B の投入前の事前チェックが「対 1 が E1 不成立で系列無効」として停止した。**親は W の値をまだ見ていない。**
- E1 不成立の中身: collection 差は B only = 新設 8 node ちょうど・A only = 0 (成立)。**shard-0 の共通 node 集合は A/B で完全一致 (4,302 件)**、新設 8 node はすべて B の shard-1。shard-1 と shard-2 の間で分割が変わっている (A shard-1 11,427 件 / shard-2 12,242 件、B shard-1 10,849 件 / shard-2 12,820 件。A shard-1 から 5,189 件が B shard-2 へ、A shard-2 から 4,611 件が B shard-1 へ)。shard 割付は所要時間台帳の重みによる決定的な分割で、B には台帳に無い新設 node が加わるので、A/B の木で決まる性質であり残り 2 対も同じ理由で不成立になる。
- 受入の shard は別々の計算ノードの別 job で、共有 base の builder (発行 child を含む) は shard ごとの xdist session 内で作られる。W_0 は shard-0 の worker 占有の最大。
- 前 wave (a) では新設 1 node で E1 が成立した (分割が変わらなかった)。

## 選択肢

- (1) erratum: E1 の割付一致の要求を「land 判定量を決める shard-0 の共通 node 集合の完全一致」に限定し、collection 差の条件はそのまま。W_1・W_2 は shard の構成が A/B で違うので対差を「同じ node 集合の比較」と呼ばず、各走の値を並べるだけにする。01-A・02-B をそのまま対 1 とし、系列を続ける。
- (2) E1 を維持し、この系列は無効 (undetermined) とする。land 判定を得るには、新設 node を所要時間台帳へ登録する等で分割を揃えた B を作り直して系列をやり直す (B の実装 commit が変わり、計算が 1.5 node 時間以上増える)、または land しない。
- (3) その他 (あなたが示す)。
