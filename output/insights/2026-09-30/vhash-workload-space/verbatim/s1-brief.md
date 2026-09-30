# 段 1 brief — dev-wave vhash-workload-space (md_29)

wave worktree (子が読む repo): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space  (起点 main 4f412c67b)
依頼の逐語: /work/1/SFC/tanab/tmp/vhash-2026-09-29/md_29.txt と common.txt (読めなければ即停止)

1. **研究前進:** VHash 論文の「提案が Cicada に勝てる負荷の範囲」を、計器 (instr-cicada-version-lifetime.patch) で H1 (hot 配置)・H2 (前進 C)・H4 (GC 接続 E) の**伸びしろの上限**として多次元にふるい分け、第 2 段 (機構を比較相手と直接比べる別 wave) の候補領域 3〜5 個を決める。完了判定 = 登録済み手順の全点を測り、軸ごとの地図・候補領域・限界を一次資料 `output/insights/2026-09-30/vhash-workload-space/README.md` に図 (生成器付き) で書く。
2. **scope (実装面、Codex author):** (a) driver `orchestrator/campaign/vhash_cicada_vlife.py` に新条件族を足し、条件ごとに record 数・1 tx 操作数・thread 数・値の大きさ (CMake `CCBENCH_VAL_SIZE`、build ごと)・genome を渡せるようにする。既存条件族 (A/B/R/S/T) の flag・build・挙動は変えない。(b) 計器 patch に abort 理由別の計数と、生存 bytes の見積りに要る値 (sizeof 等) の echo を足す。既定 build の inert (正規化 objdump・rodata 一致、nm/strings) は維持。(c) test。(d) 作図・集計の生成器 `tools/plotting/` 配下の新 file。
3. **所有外 (読むだけ):** docs/vhash-evaluation-preregistration-draft.md、patches/cicada-forwarding-*・vhash_forwarding_prototype.py、patches/cicada-ro-gcflag-*・tools/vhash_forwarding_model/、patches/cicada-vhash-hot-block-*、patches/cicada-interval-gc-*、patches/instr-cicada-trace*.patch、external/ccbench (gitlink も)、docs/paper-story-vhash/。
4. **確定済みの裁定・事実:** 比較相手は md_11 の観測最良 (D2302)。最良は負荷で変わる: 10 操作 = BEST {BACK_OFF 0, INLINE_VERSION_OPT 1, PROMOTION 0, REUSE 1, WLO 0} (driver の TUNED_GENOME)、100 操作 = BEST100 {BACK_OFF 0, OPT 0, PROMOTION 0, REUSE 0, WLO 0} (md_11 §1)。既定 = {BACK_OFF 1, OPT 0, PROMOTION 1(OPT=0 では無効), REUSE 1, WLO 0}。T-2933 (比較相手に ro-gcflag 修正を入れるか) はユーザー確認待ち。W5 (読み後に待つ型) と TPC-C は後段に回す (依頼)。md_18 (区間 GC) の一次資料は main に未着地。
5. **不変条件:** 計器入り build の throughput を性能値に使わない (絶対規律 1)。正しさの主張をしない。合計 2 node 時間未満 (計測・smoke・焦点走・変異を含む)、超えるなら投入前に見積りを書いて停止。条件は複数ノードへ割る。手順は結果を見る前に一次資料の冒頭へ書いて commit し、以後変えない。全点を報告する (負ける領域も)。

## 親の provisional 裁定 (攻撃対象)

- (P0) md_28 (偏りの掃引、/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_28.txt) を本 wave に含める: skew 0.9・0.95・0.97・0.99 (0.995・0.999 を足すかは段 4) × rr × {通常, 操作数が多い長い tx}、両 genome、record 100 万、熱いキーの数 (zipf の式から解析的に) と**熱いキー上位の版の列の長さ** (計器拡張: 走行末に上位 key の鎖長を数える)、abort 理由。前進の実際の成功率は測らない (上限=候補率のみ)。
- (P1) 点の選び方: 2 層。層 S = skew {0.5,0.6,0.7,0.8,0.9,0.95,0.97,0.99} × 読み比率 rr {5,50,95} × 長い tx {なし, batch 1000 操作 update} の格子 48 点 (他軸は中心値)。層 O = 9 軸 (skew {0.6,0.9,0.99}・rr {5,50,95}・record {1万,10万,100万}・操作数 {10,100,1000}・長い tx {なし, batch 1000 操作 update, 10 ms 待つ ro}・ro 比率 {0,50,95}%・値 {4,100,1000} B・thread {12,24,48}・gc_inter_us {10,1000,100000}) の L27 直交表 (強さ 2) を列割付を変えて 2 本 = 54 点。中心値 = record 100 万・操作 10・長い tx なし・ro 0%・値 4 B・thread 48・gc 100。
- (P2) genome: 全点を既定と「その負荷の最良」(操作 10 → BEST、操作 ≥ 100 → BEST100) の 2 通りで測る。gc_inter_us は軸なので最良の gc には固定しない。反復 2。
- (P3) T-2933 の 2 場合: stock の観測値と、md_15 の反実仮想分解 (ro commit が mainte と同じ timer 条件で flag を上げたとしたらの時刻 cf) から出す「ro-gcflag 相当」の境界の遅れを分けて記録する。md_22 の variant は測らない (所有外)。
- (P4) 伸びしろの述語 (ふるい分け用、結果前に固定): H1 大 = 全 read に占める位置 ≥ 1 の割合 ≥ 10% または update read の位置 ≥ 1 ≥ 5%。H2 大 = update read のうち「位置 ≥ 1 かつ楽観的候補あり (K=1)」の割合 ≥ 1%、かつ abort 率 ≥ 5%。H4 大 = 境界年齢 p50 bucket ≥ 1024 µs かつ論理生存版数 ≥ 1.1 × record 数。
- (P5) 候補の選び方: H 別スコアの上位 10% の点に共通する水準の組を領域とし、各 H から 1 個以上、計 3〜5 個。現実の用途との対応 (YCSB 既定の zipf 定数、TPC-C・CH-benCHmark の長い ro 等) は原典で確かめた範囲だけ書く。
- (P6) record 数軸は負荷の「熱さ」の軸として扱い、1 万・10 万は L3 に収まる (絶対規律 4 の calibrator の N とは別の目的) と明記する。100 万は md_2 の calibrator 値。
- (P7) 生存 bytes は論理生存版数 × (版 1 個の bytes の見積り) とし、物理メモリ量とは書かない。
- (P8) 予算: 1 走 ≈ 5 s (md_15 実測: 258 走 / 4 job / 1,237 s、build 込み)。(48 + 54) 点 × 2 genome × 2 反復 = 408 走 ≈ 2,050 s + build (値 3 × genome 3) を 5〜6 job に割る。計測 ≈ 0.6〜0.8 node 時間、smoke・焦点走・変異を足して < 2。

## 分割方針

単位 A = 計器 patch + driver + test (schema が結合するので 1 子)。単位 B = 作図・集計の生成器 (driver の raw schema を入力に、A と所有素集合で並列)。受入・計測は Pegasus (docs/pegasus-runbook.md)、計測木は checkout ごとに dispatch_compute --task generic。
