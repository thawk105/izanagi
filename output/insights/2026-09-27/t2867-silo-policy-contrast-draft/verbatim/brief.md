# 段 1 brief — [T-2867] silo-function-policy 軸の LLM 対 非 LLM 生成器の対照 (事前登録の草稿と見積り)

- 起点: local main `ad114fba0`、branch `worktree-dev-wave-t2867-llm-contrast`、開始 gate rc=0 (2026-09-27 14:4x JST)。
- 研究前進: VLDB 差分分析 P2 (公平な比較基盤) の「なぜ LLM か」の図を、列挙し尽くせない関数単位の空間で取る事前登録を用意する (D2259 が B-5 v2 の代わりに指した後継)。完了判定 = 草稿 + 見積り + D2258 流用可否の表が main に着地し、発効の確認事項がユーザーへ出ている。
- 確定済みの裁定: D2214 (軸・受理契約・最小 3 arm = 非 LLM×IR / LLM×IR / LLM×C++、比較 A・B の区別、非 LLM は IR 上で型を保つ)、D2256 (段階 E の driver・coder 入力の firewall)、D2258 (B-5 v2 実行契約)、D2259 (B-5 v2 見送り、本軸で取り直す)、D2212 項 4 (2 node 時間以上は確認)、D2249 追加項 (時間帯の block を入れない、同時刻対照と系列の対づけは別物で残す)。
- scope: docs だけ。(1) 新しい事前登録草稿 `docs/silo-policy-generator-contrast-preregistration.md` (未発効と明記)、(2) insight `output/insights/2026-09-27/t2867-silo-policy-contrast-draft/README.md` (D2258 流用可否の表・見積りの計算・既知結果の閲覧)、(3) `docs/README.md` の 1 bullet、(4) spool fragment (worklog・decisions)。計算は投入しない。
- 編集禁止: `orchestrator/campaign/p3_s4_loop_policy.py`、`tools/pegasus/` (T-2865 所有)。コード・テスト・agents は変更しない (実装面ゼロ → 段 5 なし、変異 matrix 免除、受入全走は免除しない)。
- 不変条件: 規律 2 (全 arm の全候補に legacy + 性能構成の verify、anomaly 即 reject、bench 前に検査完了、B を消費) を草稿で緩めない。coder 入力の firewall (段階 D の projection.json の二値と射程文のみ、D2240・D2250 の点 ID・比・順位を流さない) を保つ。
- 既存被覆: 本軸の対照の事前登録は無い (docs/*preregistration* を確認)。設計 §5・§6 に比較 A/B と最初の比較試走の規模案 (3 arm × 3 系列、149 session) があるが、判定規則は無い。純増 = 判定規則つきの登録と実測単価ベースの見積り。

## 親の provisional 裁定 (攻撃対象)

- (P1) arm は 4: LLM×C++、LLM×IR、random×IR、evo×IR ((1+1) 型の山登り、初回は random と同じ生成器)。random だけでは「巨大文法上の乱択は藁人形」の査読に耐えない (差分分析 P2 が進化探索を比べる手法に挙げる)。比較族は LLM 2 arm × 非 LLM 2 arm の 4 比較、Holm。
- (P2) workload は write-heavy だけ (driver の較正動作点が write-heavy 固定、段階 D・小比較も write-heavy)。主張も 1 workload に限る。
- (P3) n = 12、B = 10、A = 30、N_eval = 5 (B-5 から継承。n = 8 は 4 比較の Holm 初段で 8/8 全勝しか通らない)。
- (P4) 実行契約は D2258 の形 (1 評価 1 job、job 1 = 系列開始 stock + 評価 1、score job、429 は構造化 field だけで保留、途中死は止める) を規則として継承する。ただしコードとしては流用できない部分が多い (p3_s4_loop argv・backoff 値文法・K2・planner への結合)。
- (P5) LLM の原提案 1 の入力の baseline は、系列開始 stock ではなく先行の参照 job (batch 1) の stock 5 session の中央値を使い、LLM の待ちを全部計算ノードの外へ出す。系列開始 stock は同時刻対照として job 1 に残す (D2249 追加項)。
- (P6) LLM 親は原提案ごとに新しい `claude -p` session (resume しない)。driver が自系列の履歴を coder 入力に載せるので記憶は要らず、cache read の機会ごとの増加 (B-5 で 1 機会 +0.45 M) を止める。
- (P7) 既知最良 (静的 10 µs、元の適用方法) と stock を参照 job で測り、記述統計として endpoint と並べる (判定族には入れない)。

## 段 1 の改訂 (同日、草稿着手前。比較基盤の既存裁定 D2220・D2233 と T-2850 事前登録を読んだ後)

- 既存被覆の追加: D2220 (5 手法比較基盤の 4 契約・R0・K0・共通初期点・S3 を足す条件 §10) と `docs/search-repetition-trial-preregistration.md` (S1 の試走、S3 は追補で足す) が本件の上位にある。純増は S3 での判定規則つきの登録。
- (P1 改) arm は 4 のまま。比較族を 2 つに分ける: 族 A (同じ IR、LLM×IR 対 random×IR・evo×IR)、族 B (空間拡張、LLM×C++ 対 random×IR・evo×IR)。それぞれ Holm α = 0.05。LLM×C++ 対 LLM×IR は記述だけ (比較基盤 §10「LLM×C++ は比較 B で 5 手法の族に入れない」)。進化の方式は比較基盤 §6.4 の候補 (型付き GP の subtree 変異) の最小形 (1+1) で、親は初期点を含む自系列の最良。
- (P5 改) 系列開始 stock に加えて共通の初期点 k = 2 (新骨格内の静的 5 µs・10 µs、D2214 insight §5、D2220 §4.5) を job 1 で測る。job 1 = stock + 初期点 2 とし、評価 1 は job 2 に回して LLM の待ちを全部 node の外へ出す (初期点が同 job の対照を担うので D2258 項 1 の「stock と評価 1 を同 job」は継承しない)。LLM の baseline は系列開始 stock (D2220 §4.3)。
- (P8) 情報構成は R0 (参照値を生成器へ渡さない)。LLM は K0 (知識射影なし)。ただし driver の coder 入力に段階 D の二値と射程文が入る (D2256 項 4) ことを LLM 構成の一部として開示する。
- (P9) 政策 driver の停止 (MAX_ITER = 10・MAX_WALLTIME_S = 3600 s、preview 拒否も反復を消費) は A = 30 / B = 10 と噛み合わないので、系列の予算は対照の台帳が持つことを発効前の実装前提に書く (driver は T-2865 所有、本 wave は編集しない)。

## 成果物の形と分割

- 草稿は B-5 v1 の構成 (§0〜§14) に倣い自己完結で書く (v2 は発効していないので差分登録の土台にしない)。見積りは出所列 (実測 / 換算 / 試算 / 契約上限) を分ける。
- 子の分割: 実装面が無いので段 2・3・5 は省く (DW-C00 軽量版)。設計択一が割れるので、段 6 で codex read-only の敵対レビューを 2 本並列 (A: 統計・公平性・規律 2 と firewall、B: 過剰・削除と一次資料との事実照合)。受入全走は記録 commit 後に 1 回。
- 受入・実測環境: Pegasus の受入 (`tools/dev_wave_wait.py acceptance`)、所在は worklog 末尾、機体固有は runbook。
