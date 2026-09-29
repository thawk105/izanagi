# 段 4 裁定 — md_2 vhash-cicada-version-measure (2026-09-29 03:5x JST)

入力: brief.md、codex/out/s2-plan.md、codex/out/s3-consult.md (条件付き GO)。main 再走査: 539556aa1 まで新裁定なし、対象 item 未登録。

## 所見の裁定

| 所見 | 判定 | 採否・内容 |
|---|---|---|
| plan: 実 HEAD は 68106660 | real | 採用。patch base = gitlink 68106660686232781bca3be792a750d3e19d7a8a (Cicada 関連 file は 511c9538 と同一)。brief P1 の 511c9538 を訂正 |
| A1 forwarding を read 時点で確定すると後続 read の制約を落とす | 一部 refuted | 評価する機構は paper-story §3.1 の online 判断 (深い read の時点で「前進先でも既読の版が見える」か) であり、前進後の後続 read は前進先 timestamp で行われるので stock 実行の後続 read の U で縛るのは別の問い。read 時点判定を維持する。ただし「各深い read を stock 実行の上で独立に評価し、連続した前進を模擬しない」を限界として一次資料に明記 |
| A2 「上限」と呼べない | real | 採用。名称は「観測時点の楽観的 forwarding 候補率」。外した制約 (後から入る writer、pending の後日確定、write-set・node-set・一意性、先頭 K へ後から入る版) を定義文に列挙。md_2 の「上限の見積り」は「この定義の機構族に対する楽観側の見積り」と限定して書く |
| A3 先頭 8 版の採取で追加走査しない | real | 採用。記録は stock の既存走査が訪れた版だけから取る (位置 ≥ K の read は先頭 K を既に通過している)。全鎖長の標本走査 (brief P5) は削除 |
| A4 境界年齢は実時間でない・負になりうる | real | 採用。(a) timestamp 空間の境界年齢 = (leader rdtscp − (MinRts>>8))/clk、負値は別計数、(b) 公開間隔 = 公開ごとの rdtscp 差 (実時間)、(c) 回収時の版年齢も timestamp 空間と明記 |
| A5 生存版数・保持時間の意味 | real | 採用。名称「鎖に接続された論理版数 = 初期 N + install 成功 − GC 切離し」。build option (REUSE_VERSION=1、INLINE_VERSION_OPT=0 等) を raw に固定。物理メモリ量ではないと明記 |
| A6 read-only 率・公開間隔を条件別に | real | 採用。read-only 試行数・commit 数を worker 別に、公開間隔分布を条件別に記録 |
| A7 長い tx の回数・操作数・abort・継続時間 | real | 採用。長い tx (worker 1 または batch worker) と短い tx を分けて試行数・commit 数・abort 数・実行操作数・継続時間 (begin→commit/abort の rdtscp) を記録。batch 型は thread_num=47 + batch_th_num=1 で総 48 worker にそろえる |
| A8 witness を gitlink preimage で実測・共有 header | real | 採用し強化: **共有 header include/ycsb.hh は触らない**。長い tx の手続き生成は Cicada の TU (ycsb_cicada.cc 等) の macro 内に閉じる。前処理比較は Cicada の touched TU 全部、`.text` 比較は smoke で stock と既定 patch |
| A9 hook は管轄外 None | real | 採用。登録簿追加なし。実投入が probe を兼ねる |
| B1 登録面の縮小 | refuted | 前例 (silo_policy_coverage.py) どおり materializer 登録と condition gate (DefineSpec) を残す。既存策の流用を優先 (DW-G05)。driver は smoke / measure の最小機能に絞る |
| B2 壊れた delay macro の build 省略 | refuted | stock の欠陥を insight に書く根拠として compile 成否だけ記録 (cicada TU の再 compile のみで安価) |
| B3 条件を段階化 | real (一部) | smoke 後に所要を再計算し、2 node 時間未満なら A・B 両 workload を並列投入、超えるなら A のみ |
| B4 calibration は短い maxrss probe | real | 採用。stock build、rratio 100 (版を作らない)、extime 1 の maxrss を N∈{1M,2M,4M} で測り、maxrss > 4×L3 の最小 N。4M でも未達なら「基準未達」と記録し N=4M を使わず 1M (論文 §7.2) を使って理由を一次資料に書く |
| B5 表現の強さ | real | 採用。「stock の YCSB は batch worker の操作数を変えず、既存 delay 分岐は未定義識別子を参照する」「read-only の snapshot は 1 試行中固定、retry で取り直す」 |

## plan v2 (実装子への指示の骨格)

1. patch `patches/instr-cicada-version-lifetime.patch` (base 68106660、`diff -u` 形式 a/ b/)。macro `IZANAGI_CICADA_VLIFE` / `IZANAGI_CICADA_LONGTX`、既定未定義 = stock と Cicada touched TU の論理行正規化前処理が一致 (`#line` で行を戻す)。include/ycsb.hh・common/runner.hh は変更しない。
2. 計器 (VLIFE): site 別 (read-update / read-ronly / blind-write / rmw-latest / precheck / install / readcheck / writecheck) に hop 数と選択版の物理位置のヒストグラム (0..8 は正確、以降 log2 bucket、上限 bucket)。K∈{1,2,3,4,8} ごとに update-tx の深い read 数と楽観的候補数 (判定式: 先頭 K 内の committed かつ非 deleted 版の最古 wts を lo として max(lo, L, ts+1) < U。L = 既読版 wts 最大、U = 既読版の「読んだ時点の直上 committed 版 wts」最小、既読 0 件は別計数)。read-only の深い read は別計数。GC: 公開ごとの境界年齢 (ts 空間、負値別計数) と公開間隔 (rdtscp)、回収版数と回収時年齢 (ts 空間、生成基準と上書き基準)、install 成功数・切離し数。worker 別の長短別 tx 統計。出力 = 終了時 1 行 `IZANAGI_CICADA_VLIFE_JSON {...}` (schema version 付き)。
3. 長い tx (LONGTX): batch worker (thid >= FLAGS_thread_num) は通常 YCSB と同じ分布・読み比で操作数 FLAGS_batch_max_ope。worker 1 は commit() 冒頭の既存位置で FLAGS_worker1_insert_delay_rphase_us 待つ (thid_ 使用)。既存 WORKER1_INSERT_DELAY_RPHASE 分岐は触らない。
4. driver `orchestrator/campaign/vhash_cicada_vlife.py`: `smoke` (stock / 既定 patch / 有効 patch の 3 build、`.text` 比較と izanagi 文字列 0 件、WORKER1_INSERT_DELAY_RPHASE=1 stock compile 成否、N∈{1M,2M,4M} maxrss と lscpu L3、条件 1 つの短い走) と `measure --conditions <ID,...>` (宣言済み条件表から部分集合、N は smoke 出力から受ける、3 反復、raw JSON)。厳格 parse、未知・重複 ID 拒否、既存 raw の上書き拒否、login 拒否 (site policy)。
5. 登録: materializer_admission (NON_ADMISSIBLE)、condition_meaning_gate の DEFINE_SPECS と分岐 witness (+ 在庫 pin テスト更新)。
6. test `orchestrator/tests/test_vhash_cicada_vlife.py` (純関数 + patch 既定の前処理一致) と作図 `tools/plotting/plot_vhash_cicada_vlife.py` (図 3 枚、raw JSON のみを入力、provenance JSON)。

## 条件表 v2 (P6 改)

48 worker、YCSB 10 ops、payload 4 B、extime 3 s、3 反復。workload A = rratio 50・skew 0 (論文 §7.2)、B = rratio 95・skew 0.9。長い tx = {none, wait1ms (worker 1 に 1000 µs), wait10ms (10000 µs), ops1000 (thread_num 47 + batch 1、batch_max_ope 1000)}。gc_inter_us = {10, 1000, 100000}。計 24 条件。

## 変異の事前登録 (DW-M01、実装後に単一理由性を確認し、成立しなければ再照準)

- MUT-1 driver の JSON 行 parse から重複行拒否を外す → 重複拒否 test が KILLED
- MUT-2 K 深部割合の境界を `>= K` から `> K` へ → K 境界 test が KILLED
- MUT-3 patch の計器文 1 つを `#if IZANAGI_CICADA_VLIFE` の外へ出す → 既定前処理一致 test が KILLED
- MUT-4 measure の条件 ID 重複を受理 → 重複 ID 拒否 test が KILLED
- MUT-5 集計で read-only の深い read を forwarding 分母へ入れる → read-only 分離 test が KILLED
