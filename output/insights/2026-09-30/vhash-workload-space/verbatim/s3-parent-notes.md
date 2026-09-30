# 段 3 向け 親メモ (段 2 plan を読んだ後の暫定、攻撃対象)

- (N1) 長い tx の水準は {なし, batch1000U, batch1000R} にする (待つ型 wait10ms* は使わない)。根拠: patch の begin() で thid_ >= thread_num の batch worker は batch_max_ope 操作に伸ばされ (patches/instr-cicada-version-lifetime.patch 付近 317〜335 行)、vlife_long_ に batch worker が含まれ、izanagi_long_kind=2 なら全操作を READ にする (同 347〜365 行)。よって batch_th_num=1・izanagi_long_kind=1/2 で「1000 操作の update / read-only の長い tx を 1 worker が続ける」が既存 flag で作れる。待つ型は依頼が後段に回した W5 (読み取り後に待つ型) と紛らわしいので避ける。
- (N2) md_22 の知見「stock Cicada は read-only を続ける worker 1 本で GC 公開が止まる」から、batch1000R の点は stock では境界の遅れが走行長まで伸びると予想する。T-2933 の 2 場合は plan P3 の指摘どおり「stock 観測」と「時刻分割による機会 (local_flag_opportunity)」を並べ、介入後の値と呼ばない。
- (N3) 操作数軸 {10,100,1000} は全 worker の ycsb_max_ope、長い tx 軸は batch worker 1 本だけ。両者を別軸として持つ。
- (N4) genome: 既定 と「負荷の最良」(操作 10 → tuned = BEST、操作 100・1000 → best100)。1000 操作への best100 は外挿と明記。
- (N5) 候補の選び方の案: 述語の通過点を全件公開したうえで、「領域」= 1 軸または 2 軸の水準の組。領域の採用条件 = (a) その組に属する点の過半で述語通過、(b) 支持点 ≥ 3、(c) 既定・最良の両 genome で (a) が成り立つ、(d) skew を含む領域は隣接 skew 水準でも (a)。H1/H2/H4 それぞれ通過率の高い順に採り、計 3〜5 個。満たす領域が 3 未満なら不足と書く。
- (N6) 極端条件 (1000 操作・100 万 record・1000 B・skew 0.99 など) の 1 走所要と RSS は smoke で測ってから本計測の投入を決める。
