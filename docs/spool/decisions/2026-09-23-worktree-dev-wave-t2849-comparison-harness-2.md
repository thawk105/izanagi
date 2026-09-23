---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: worktree-dev-wave-t2849-comparison-harness
seq: 2
---

## {{D:t2849-harness-impl}}. 5 手法比較基盤 (S1) は B-5 の兄弟 module と既存評価入口への最小変更で実装し、K0 LLM は役割定義を改訂して D2220 どおりの入力にし、標準評価経路の trace 保全は env の opt-in で cleanup の前に行う

**決定:** D2220 の実装単位 1〜7 と、再現パッケージの欠け部品のうち標準評価経路の trace 保全口を、次の形で実装した (記録は insight `output/insights/2026-09-23/t2849-comparison-harness-impl/README.md`)。

1. **評価入口は既存の単回評価経路のまま。** `p3_s4_loop` の `--b5-slot` に比較基盤の名前空間 `t2849-harness-v1|` を足し (B-5 の接頭辞の条件は不変)、`p2_2_flag_opt` を測る入口 `--reference-genome` (silo の exact 4 flags、`BACKOFF_FIXED` なし) は `--stock-control` かつ比較基盤の slot に限る。参照の canonical genome は search_config に入り campaign identity を分ける。新しい slot flag・sidecar schema は作らない。
2. **系列制御は B-5 の module を編集せず兄弟 module に置く。** `orchestrator/campaign/t2849_comparison_harness.py` (5 arm・初期点 5・10 µs・A 上限・共有対照・集約) と `t2849_generators.py` (random・sweep・逐次 GP-EI・(1+1)、標準ライブラリだけ)。B-5 の `classify_session`・`classify_slot`・`wal_timing`・`select_endpoint`・重み表・`validate_backoff_value`・`default_runner` を呼ぶ。参照だけは B-5 の分類が `BACKOFF_FIXED` の無い genome を候補扱いして Tier0 を要求するので、同じ証拠の分類から候補専用の Tier0 条件を除いた専用関数にし、stock source の一致を要求する。
3. **K0 LLM は役割定義を改訂する。** planner-v4 と coder-v4-autonomous に、T-2849 比較基盤の K0 arm に限り critic 診断 (`k2_critic_diagnosis`、D2155 の 6 field のまま) と、初期点・投入前拒否の閉じた兄弟 key `t2849_prior_observations` を渡す節を足す。K1・B-4・8c・従来の段 4 loop には適用しない。role adapter は repo の renderer で生成し (D1861)、sha pin は Codex author が追随させる。巡 tool (`tools/t2849_llm_round.py`) は driver が公開する request を読むだけで driver の module を import せず、役割の呼出しは親 session が行う。
4. **trace 保全は env `IZANAGI_TRACE_ARCHIVE_ROOT` の opt-in。** 検証 1 反復の一時 dir を cleanup の前に file ごとに `zstd -T0 -3` で保全し、完了したときだけ inventory を complete にする。保全の失敗は原本を残し、評価結果・例外を置き換えない。未設定なら追加の I/O・subprocess は無い。保全の記録は WAL・proof chain・受領証に入れず、certification の根拠にしない。
5. **bench lock は job body の比較基盤分岐でだけ設定する** (driver 起動直前、`$TMPDIR/bench.lock`、D2209 と同形)。driver 側には置かない。

**理由:**
- 依頼は単位 1〜7 と保全口の本題だけを求め、B-5 の module の編集、新しい gate・検査・台帳・一般化を scope 外とした。既存の単回評価経路を通すことが「手法で経路を変えない」(D2220 項 1) の実体である。
- 段 1 で親は役割定義を変えない暫定案を置いたが、段 3 の相談 2 本がそろって反対し親も real と判定した。設計 insight §2.7 は K2 限定の射影を既に指摘し、K0 への拡張を単位 4 に含めていた。役割定義を変えなければ LLM の入力 (初期点の観測・投入前拒否・critic 診断) と費用が D2220 の構成から変わる。前例 (critic 診断を K2 へ接続した wave、commit `4bd962643`) と同じ分担で改訂できる。
- 保全を既定で有効にすると、検証の全呼出しで I/O と所要が増え、既存 campaign の挙動も変わる。論文根拠の実験だけが作業保管の全量を要する (再現パッケージの見積り insight §7)。失敗を評価の失敗へ変えると、保全口の障害が正しさの判定を置き換えるので、原本を残して結果は通す。
- 参照の入口を `--stock-control` の明示拡張にしたのは、stock と同じ patch・条件 gate・`run_campaign` を通すため (評価の callsite を増やさない)。

**却下した選択肢:**
- 役割定義を変えず、critic 還流と兄弟 key を別の項目へ送る — D2220 の LLM 構成を変え、比較が別構成になる。
- B-5 の module に引数を足して名前空間・arm 集合を一般化する — 依頼が B-5 の module の編集と一般化を scope 外とした。並走の発効束もその file の sha を束縛している。
- 保全を WAL の field や受領証に記録する — proof chain の schema 変更になり、保全の障害が certification に波及する。
- lock を driver と job body の両方に置く — 同じ責務を 2 か所に持つ。
