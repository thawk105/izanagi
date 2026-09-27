# 段 1 brief — dev-wave-t2207-closure-unresolved (親、2026-09-27 JST)

起点: local main ad114fba0 (worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2207-closure-unresolved、開始 gate rc=0)。
依頼逐語: artifacts/request.md。一次資料: artifacts/{D1539-D1540,D1501-D1502,D2260,t2155-insight-README,t2207-origin}.md。

研究前進: certified build の正しさ gate 被覆 (patch 追加 define × build sink の交差検査、orchestrator/tests/test_ccbench_spawn_sites.py) が「証明なしの到達不能」を被覆 domain から外している事実を正す (D1539・D1502)。論文の図表は動かない。完了判定 = D1539 の意味で proven-unreachable の根拠から「動的入力下の部分 inventory の不在」が消え、既存テスト全緑で land。

確定済みユーザー裁定:
- D1539 (2026-09-03): 設定式が動的入力に依存するとき、部分 inventory に無いことを proven-unreachable の根拠にせず unresolved へ倒す。受理集合を狭める向き。
- D2260 項 2 (2026-09-27 07:52 JST): D1075 と 2026-08-16 第 3 回の [T-734] を取り下げ、[T-733][T-734][T-2344][T-2402] を止める。exact-85 の歴史収載の扱いも行わない。既存の束縛・検査は変えず撤去 wave も起こさない。
- 本依頼 (14:28 JST): (1) T-2207、(2) T-2344 次段 + exact-85/96 再走査と撤去、(3) T-734、T-733 の 69 module 整理。「本題の実装だけ。これ以外の gate・検査・台帳・一般化の追加は scope 外」。

親の実測 (job dir probe_t2207*.log、コード変更なしの計算 + DW-O19 の実編集→復元で一致を確認):
- 現行判定 `_sink_macro_reachability` は source_macros が非空なら即 proven-unreachable。動的依存 (= 既存 `_expression_depends_on_scope_parameter` が真) の buildcache/campaign sink でこれに当たるセルは 16 sink・929 セル。
- 「動的依存なら unresolved」を実編集で入れると、`test_define_sink_cross_product_has_no_unreviewed_ungated_member` の failures が 0 → 715 (12 sink: backoff_extended_sweep×2、backoff_profile、backoff_repro、backoff_sweep、p3_s4_loop×4、paper_story_a1_paired 7295、paper_story_a2_certification、s1_direct_comparison)。残り 214 は既存の繰延べ台帳 entry (b10×2、t2187×2) で deferred。
- 「18 セル」は 9/2 当時 (macro 22 個) の s1 だけの数。現行は macro 61 個で s1 単独でも 57。D1502 は 9/2 に「同じ規則で落ちるセルは repo 全体に 900 件以上」と既に書いていた。

(P0) 親の provisional 裁定・攻撃対象: (2)(3) と T-733 整理は D2260 項 2 (本日、ユーザーが反対意見併記の提示を見て選んだ) と真っ向から逆であり、依頼は同時刻の一括起動 (12 本前後) の写しと見られる。この wave では実装・撤去をせず、食い違いと再開方法を記録するだけにする。
(P1) 親の provisional 裁定・攻撃対象: D1539 を字義どおり入れると 715 セルの赤を解消するのに gate 追加 (production 12 sink) か繰延べ台帳 12 entry が要り、どちらも本依頼の scope 外節に当たる。scope 内で赤を出さずに D1539 を忠実に満たす実装が無いなら、この wave は「実装しない」(段 4→7→8→9) とし、新事実と択を記録する。
(P2) 攻撃対象: 「動的入力」の判定に既存 `_expression_depends_on_scope_parameter` を流用するのが D1539 の意味として正しいか (過剰: 呼び手が閉じた値しか渡さない場合 / 過少: 引数以外の動的入力)。

不変条件: 規律 2 (受理集合を広げない、テスト期待値の反転・緩和・skip 禁止)。実装面は Codex author のみ。依頼 (2)(3) の対象 file (exact-85/96 収載・source gate) は触らない。
成果物: 実装する場合 = test_ccbench_spawn_sites.py の判定 + 正例負例テスト + 件数 pin 更新。しない場合 = insight (新事実・択・推奨) と spool fragment のみ。
分割: 編集 file は 1 本 (上記テスト) で所有は単一単位。受入は計算ノード (run_tests.py dispatch)。
