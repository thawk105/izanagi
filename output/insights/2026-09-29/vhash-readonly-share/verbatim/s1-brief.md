# 段 1 brief — md_15 read-only tx が深い版探索と GC の遅れの主因か (2026-09-29 14:23 JST 起草、base 035fc11fa)

**研究前進:** VHash 論文 2 版目の H1 (hot 配置) と U0 (GC 接続) の伸びしろの所在を決める。md_2 §0.2・§0.6 の観測「深い探索は read-only (ro) tx 由来」「ro commit は公開を進めない」を、ro 比率を独立軸にした格子で確かめ、(1) 深い探索のうち ro 由来の割合、(2) 回収境界の遅れの ro 由来 / 長い update tx 由来の分解、(3) 上限・一次見積り 2 つ、を図 4 枚 + 一次資料 `output/insights/2026-09-29/vhash-readonly-share/README.md` にする。完了判定 = 一次資料に条件表・結果前に固定した定義・分解・見積り・図・限界・確かめた/確かめていないが揃い、全数値が raw JSON と照合できる。

**確定済み (原典ソース・md_2 の実測):**
- Cicada (gitlink 68106660) の GC: `begin()` は ro/update を問わず `rts_ = MinWts − 1` を `ThreadRtsArray[thid]` に、`wts_` を `ThreadWtsArray[thid]` に書く (transaction.cc 38〜43)。leader (thid 0) は各 tx の先頭 `leaderWork()` で、全 thread の `GCFlag` が 1 のときだけ MinWts・MinRts を公開し flag を下ろす (util.cc 281〜323)。flag は `mainte()` の中で `gc_inter_us` 経過後にだけ上がる (transaction.cc 883〜888)。`mainte()` は update commit (954) と abort (767) から呼ばれ、ro commit (934〜937) からは呼ばれない。
  → 短い ro tx の GC への影響は「flag を上げない = 公開頻度」経由で、rts slot の値は update tx と同じ。ro が読む snapshot の古さ ≒ 公開の遅れ (循環)。
- `ronly_ratio` flag は common.hh 64/92 に宣言だけあり未使用。ro 比率は現状 `ycsb_rratio`^10 で間接に決まる (ycsb.hh 55〜79)。
- md_2 計器 (patch sha256 fbe86f3a…): ro read の位置 (site 1)・`readonly_deep[5]`・公開ごとの境界年齢/公開間隔の 2 倍刻みヒストグラムはある。ro read の forwarding 候補は数えていない (ro は L/U 追跡外、patch 400〜405 行)。平均の元になる厳密和は無い。
- condition gate の VLIFE 分岐 witness 数は transaction.cc 33 / transaction.hh 9 (condition_meaning_gate.py 527・557)。新 macro は登録簿の連鎖 (DEFINE_SPECS、screening_driver `_CONDITION_DEFAULTS`、test_p3_s4_loop の allowlist、materializer 登録) が要る (memory: condition gate は owner TU の前処理だけを見る)。
- `patches/ledger.json` は D18 第 4 類 ability probe 専用で entry 数 1 固定 (md_2 §9)。

**親の provisional 裁定 (攻撃対象):**
- (P1) 計器拡張は既存 `IZANAGI_CICADA_VLIFE` / `IZANAGI_CICADA_LONGTX` の下だけ。新 macro は作らない。分岐は owner TU (transaction.cc) と transaction.hh に置く。
- (P2) ro 比率の制御: patch 内で定義する実行時 gflag (例 `izanagi_ronly_pct`、既定 −1 = stock 生成のまま = md_2 と同一動作)。0〜100 のとき、新しい tx の初回 `begin()` で確率 r% で全 op を READ に、それ以外は少なくとも 1 op を write (ycsb_rmw に従う) に置き換える。retry では置き換えない。長い worker (thread 1、待機型) の tx 種別を別 flag (例 `izanagi_long_kind`: 0 = 生成のまま / 1 = update 固定 / 2 = ro 固定) で固定する。
- (P3) 条件: YCSB skew 0.9、update tx の op は rratio 50、10 ops、48 worker、N は md_2 と同じ smoke 再計算。ro 比率 r ∈ {0, 25, 50, 75, 95}% × gc_inter_us {10, 1000, 100000} × 長い tx {none, wait1ms-upd, wait10ms-upd, wait10ms-ro} = 60 条件 × 3 反復 + md_2 接続用の anchor 2 条件 (md_2 の B-none-gc10・B-wait10ms-gc10 と同じ flag、stock 生成)。5 job に割り並列投入。見積り ≈ 186 走 × 約 7 s ≈ 22 分 + build 5 × 約 3 分 + smoke 1 本 ≈ 0.7 node 時間 (< 2)。
- (P4) 分解の定義 (結果を見る前に固定):
  - D-F (条件間): Lag = 公開ごとの境界年齢 (now − MinRts) の平均 (µs、厳密和 ÷ 公開回数)。ro 効果(r) = Lag(r, none) − Lag(0, none)、長い update 効果(L) = Lag(0, L) − Lag(0, none)、交互作用 = Lag(r, L) − Lag(r, none) − Lag(0, L) + Lag(0, none)。gc_inter_us ごと。公開回数/秒も同じ形で。
  - D-C (同じ走の中の反実仮想): 公開 k ごとに、各 thread の実際の flag 上げ時刻 raise_i と、「ro commit も mainte と同じ条件で flag を上げたら」の時刻 cf_i (timer 満了後で flag 未上げの最初の commit、種別問わず; 実際に上げたらその時刻) を記録。公開間隔 = [max cf − 前回公開] + Δ_ro + [公開 − max raise] で、Δ_ro = max raise − max cf を ro 由来の待ち、第 1 項を max cf の thread がその時に commit した tx の種別 (ro / 通常 update / 長い update) で帰属。第 3 項は leader の見回り遅れ。
- (P5) 見積り (a): ro read で位置 ≥ K のもののうち、観測した鎖の先頭 K 版内に committed 版 v があって max(wts(v), L, rts+1) < min(e(v), U) を満たす割合 (md_2 の update 側と同じ式、L/U を ro tx でも追跡)。後から入る writer・pending の後日確定・read set 検証の費用を無視した楽観の上限。固定 snapshot 必須の ro の割合 f を与えたときの避けられる割合 = (1 − f) × 候補率 (tx 独立を仮定) として f の関数で書く。見積り (b): Δ_ro の平均 ÷ 公開間隔の平均 = 公開時刻の前進の一次見積り (公開が早まる → snapshot が新しくなる、の feedback を含まない。上下限と書かない)。
- (P6) 追加の直接計測: ro tx の snapshot 年齢 (begin での now − rts_ の µs ヒストグラム + 和) を「古さ」軸の実現値として出す。
- (P7) driver は md_2 の `orchestrator/campaign/vhash_cicada_vlife.py` を拡張 (新条件 ID を足し md_2 の 24 条件は残す、JSON は field 追加 + schema_version 2)。作図は新規 `tools/plotting/plot_vhash_readonly_share.py`。`patches/ledger.json` は触らず `patches/README.md` の既存 entry を更新 (md_2 と同じ理由、依頼文との差は一次資料に書く)。

**不変条件:** 計器入り build の throughput は性能値に使わない (規律 1)。既定 build (両 macro 未定義) は stock と `.text`・`.rodata` 一致 (smoke witness を新 patch で取り直す、D20)。gflag 既定の VLIFE build は md_2 と同じ生成 (anchor 条件で md_2 の値と並べる)。正しさ主張をしない (Cicada は検査器未対応)。md_2 の raw・図・README を書き換えない。所有外 (`patches/cicada-forwarding-*`、`orchestrator/campaign/vhash_forwarding_prototype.py`、`tools/vhash_forwarding_model/`、`docs/paper-story-vhash/`、external/ccbench の gitlink) を編集しない。合計 2 node 時間未満。md_11・md_14 と同じノードで計測しない (gen_S は 1 request = 48 CPU の logical host、run ごとの競合 probe、host 名を記録)。

**DW-O09 閉包 (main 035fc11fa で `git grep`、変更前 sha256 patch fbe86f3a… / driver 6610cafa… / plot 19363b51… / test 87ffc532… と path・macro 名):**
- sha の hit は md_2 一次資料 README 120 行 (歴史記録、書き換えない) だけ。md_2 の raw JSON (gz) も当時の patch sha を持つが歴史記録で再発行しない (規律 7)。
- 件数・文字列 pin (同時に直す候補): `orchestrator/campaign/condition_meaning_gate.py` 83〜90・380〜385・527〜528・557〜560、`orchestrator/tests/test_condition_meaning_gate.py` 48〜49・108〜112・439・492・1550・1596・3519、`orchestrator/tests/test_p3_s4_loop.py` 8555〜8556 (patch 内の裸 `IZANAGI_*` token の許可集合)、`orchestrator/tests/test_ccbench_spawn_sites.py` 81〜84 (driver の起動箇所数)、`orchestrator/tests/test_p3_build_authority_cli.py` 161・182、`orchestrator/campaign/materializer_admission.py` 108、`orchestrator/campaign/screening_driver.py` 73〜74、`orchestrator/tests/test_vhash_cicada_vlife.py` 107・124〜128・365〜366・400 (patch 文字列の分割位置)、`patches/README.md` 14・845〜869。
- DW-O10: producer (driver) の出力 JSON は field 追加になるが、既存の凍結成果物は無く md_2 raw は再生成しない。producer が書く file 種は raw JSON 1 種 (smoke/measure) で不変。

**成果物:** patch 更新 + README entry、driver + test 更新、作図 (新規)、登録簿の件数更新、一次資料 (条件表・定義・分解・見積り・図・限界)、spool fragment (新規 item)。

**分割:** 実装は Codex author 1 単位 (patch・driver・test・作図は bytes 契約で結合)。段 2 plan 1 本、段 3 consult 1 本 (正しさ境界と実効性・過剰の 2 レンズ兼務)、段 6 review 1 本 + 焦点。実測環境 = Pegasus gen_S (dispatch_compute.py --task generic、md_2 と同じ経路)。受入全走は段 7 後。
