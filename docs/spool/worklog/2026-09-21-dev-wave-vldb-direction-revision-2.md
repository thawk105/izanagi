---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-vldb-direction-revision
seq: 2
title: VLDB 投稿へ向けた研究方針をユーザーとの協議改訂として記録した — EA&B を第一候補、TPC-C 段 1・2 を必須、関数単位のコード空間を開く (正しさゲートは不変)、計算は 1 タスク 2 node 時間以上で都度確認、旧系列の再開を論文の必須経路から外す。差分分析の P0〜P6 と TPC-C 段 1・2 の 9 項を起票 (docs のみ、branch worktree-dev-wave-vldb-direction-revision)
---

## 本文

- 依頼 (台帳 ID 未起票、主題 slug) を軽量版で処理した: 段 1 brief → 記録 (decisions / worklog fragment、roadmap、insight) → 段 6 独立 read-only レビュー 1 本 → 受入 → land。
  実装面の差分ゼロ (docs と insight のみ)。段 2・3 は省いた (設計択一の割れ・正しさ防壁・受理集合の変更なし)。
- 裁定 9 項は {{D:vldb-direction-verdicts}}。一次資料 (差分分析・Codex の独立見解・裁定控え) は repo 外にしか無かったので、
  `output/insights/2026-09-21/vldb-direction/` へ bytes 一致で写した (sha256 は同 README §1)。写しの訂正 1 件 (差分分析の
  `orchestrator/pipeline.py` は現物に無く、YCSB 以外を拒否しているのは `orchestrator/campaign/pipeline.py`) は同 README に記した。
- `docs/roadmap.md` を協議改訂として in-place で改めた (`docs/roadmap-history/README.md` の協議改訂なので版は上げず、history に凍結しない)。
  §1 に「論文の目標と必須経路」節 (EA&B 第一候補・締切・P0〜P6 と TPC-C・必須経路に入れない旧系列)、§2 層 2 に関数単位のコード空間、
  §3.1 Tier 1 に TPC-C 段 1・2、§5 に計算投入の確認ライン、§9 に Phase 3 の段と論文の必須経路の関係、§10 の「制約なしのコード生成」に
  関数単位の空間が当たらない旨を足した。8c の無人自律はシステムの目標として残し、外したのは凍結・批准で止まっている official 系列の再開だけである。
- 同時刻の /rulings 全件 第 30 回 (job dir `rulings-all-20260921d`) との重なり: 21:1x の VLDB 裁定 5 (「T-2812 の択一そのものは保留」) と、
  21:3x の第 30 回への一括承認 (「推奨通りで」、索引 2 = g1 の S' 採用・索引 1 = K2 pair + 4 巡目の認可) が食い違った。第 30 回の記録側が
  ユーザーに 1 問で確認し、ユーザーは 21:37 頃「codexと相談して決めて」と答えた。第 30 回側は Codex 2 レンズで「g1 は保留継続、K2 は委任による
  解決で限定採択、A-1 attempt-0003 は走らせない」と決めた。両 wave は cross-session message で合意し、[T-2812] / [T-2795] は第 30 回側だけが
  更新し本 wave は触れない (base の衝突回避)。本 wave は同じ問いをユーザーへ重ねて出さなかった。
- 旧系列の carry は系列の先頭 3 項 ([T-2724] g1 chain、[T-750] W-4、[T-244] 8c 本走) だけを更新した。8b / 8c・g1・W-4 / W-5 に言及する
  active 項は他にもあるが、系列の再開そのものではなく周辺の道具・検査の項なので触れていない (暗黙 carry)。[T-2724] の entry 1742 時点の次手 (launch validation の
  不整合 2 件) は [T-2810] (D2196) で着地済みだったので、更新文に反映した。
- 見送り台帳 [T-156] の発火条件「TPC-C 級 workload corpus を採るとき」に TPC-C の起票が関わるので、関連記録を 1 行追記した (起票時点では未発火、再評価は TPC-C 段 1 の wave)。
- 段 6: 独立 read-only レビュー 1 本 (codex gpt-6-astra / medium、忠実性と過剰・削除の 2 レンズを 1 本で担う) は NO-GO で、must-fix 1
  (P1 の計算確認が「(3) 以降」に限られ、実装に伴う開発検査を含む wave 合計が漏れる)・should 4 (旧系列 2 項の優先度引き下げが裁定そのものに読める /
  「4〜6 週で組み替える」は分析の提案で裁定ではない / roadmap §9 の Phase 3 との対応が実装方式を固定している / 新規項の資料参照が裸の file 名)・
  nit 1 ([T-156] への追記を「発火記録」と呼ぶと発火時点を誤認させる)、refuted 6 (裁定の写し・新規 9 項の数値・carry の内容・roadmap の規律・
  insight の証跡・fragment 文法) を返した。親は 6 件すべてを real と裁定して直し、焦点再レビュー 1 本は対応表で全件 closed・退行なしの GO。
  費用は codex 2 本 (review 1、focus 1)。
- 記録前の検査: check_docs rc=0、spool_fold --dry-run rc=0、全史 provenance rc=0。三軸語の権威走査 (`s8b_holdout_freeze search`) は rc=1 だが、
  hit は本 wave 以前 (commit `cc82edc8c`、2026-09-17) から main にある official 床値の run dir の 3 file だけで、本 wave の file は 0 件 (非帰属)。
- 受入全走は計算ノードを使う。1 走の上限見積りは 3 shard × 外側 25 分 ≈ 1.25 node 時間で、確認ライン (2 node 時間) 未満として 1 回だけ投入する。
  再投入が要るときは累計を見積もってから判断する。

## 次の一手差分

### 更新

- [T-2724] **P3・論文の必須経路から外した ({{D:vldb-direction-verdicts}} 項 5。優先度 P1 → P3 はそれを受けた親の整理判断)**: 凍結 v2 g1 chain の A/X は着地
  (AI 委任) し、批准 loader は成功した。entry 1742 時点の次手「launch validation の既存不整合 2 件の解消」は [T-2810] (D2196、journal
  allowlist と段階 6 lineage の整合) で着地済み。live launch は現行 policy 照合で拒否のままで、その解き方 (S' / O' / N) は [T-2812] の択一として
  保留が続く。以後の道筋 (runbook §2 P3 の全 gate 受理 → W-4 spec 承認 ([T-750]、ユーザー手番) → W-5) は 8b の official 系列の再開として
  論文の必須経路に入れず、凍結 chain も新設しない。再開するときは [T-2812] の択一の裁定から始める。既存の凍結記録・A/X・批准世代は変えない
  (規律 7)。一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md` §5、`output/insights/2026-09-20/t2810-g1-launch-validation/README.md`。
  base: 5f177848a6f791ef0fb5c86536767b33fecc881d7e546faacaec2ccf663eedea
- [T-750] **P3・裁定済み・実装済み、W-4 / W-5 は論文の必須経路から外した ({{D:vldb-direction-verdicts}} 項 5。優先度 P2 → P3 はそれを受けた親の整理判断)**:
  実凍結 (g1) は 2026-09-20 に AI 委任で発効 (A `a3bf67a8c` / X `70e87c9c9`)。W-4 (spec 承認、P-1) の起動前提「P3 gate-check が active 世代で
  受理」は、launch validation の不整合 2 件が [T-2810] で解消した後も、live の policy 照合の拒否 ([T-2812] の択一、保留) で未達。W-4 / W-5 は
  8b の official 系列として論文の必須経路に入れない。package の P-1 / P-3 の残余は別管理のまま。
  base: 56d83fff63718bbd2ee33fa89c9d26a9fec12364289c0709cb485f26b26bd6e6
- [T-244] **P3・裁定済み (2026-08-15 /rulings 全件、7 件すべて)、8c 本走は論文の必須経路から外した ({{D:vldb-direction-verdicts}} 項 5)**:
  (1) D411 の限定 supersede を**追認**、(2) 開放世代数は **G=2 (安全側)** — 実測代理で中央値 約 997 秒・最悪 約 2275 秒、
  既定 `max_wall_s = 3600` に収まる。代理データであり LLM 応答時間を含まない点は不変、
  (3) P9 の一般閉包は**起票のみ・着手は後**、(4) P1 / P2 残余 / P5 残余 (U-2) は**未充足のまま据え置き**、
  (5) 注入 seam と `drive_iteration()` 直接反復は**保証対象に入れない** (D114 が対象外と明記)、
  (6) planner→coder 3 field の意味的非干渉は**禁止しない** (禁じると planner を決定的 mapper へ
  替える必要があり自律性の実証を損なう)、(7) s8c C11 の artifact 2 件は**作らない**。
  残作業 = (1)(2) を受けた 8c 本走の事前登録と投入。これは 8c の正式系列として論文の必須経路に入れない (無人自律はシステムの目標として残す、
  roadmap §9)。投入するときは node 時間を見積もり、1 タスクの job 合計が 2 node 時間以上ならユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。正本 =
  `dev-wave-jobs/2026-08-14_t244-8c-multigen/s4-ruling.md` §7。
  base: b7c71af48c8c69684028c4da368d8575e36da2d8b07a92801f84b1736b7bbc1b

### 新規

- {{T:vldb-p0-verification-scope}} **P1・新規 (VLDB 差分分析 P0: 検証の意味と容量)**: verifier が何を検出でき、何を判定していないかを確定する。
  (a) 期待結果つきの小さな履歴コーパス (直列化可能な履歴・異常履歴・abort・欠損 trace・初期値・同一キーへの複数操作) と、意味の異なる CC 変異
  20〜40 個で検出力を測る (既存 verifier と、壊した Silo・si の正例を再利用する)。(b) 大きな trace の容量 (balanced 10 秒で 32 GiB、read-heavy
  6 秒で約 81 GiB、ノード上限約 115 GiB) を先に測る。分割するなら境界をまたぐ依存を保ち、時間窓ごとの独立検査を同等と扱わない (検査のメモリ縮小の
  既存項は [T-2351])。(c) 論文全体で「certified は有限の観測履歴に対する判定で、全実行の証明ではない」と統一する。完了 = 検出表・容量の実測表・
  論文用の射程の文。計算: 実 trace 10〜20 本の検証で約 1.3〜2.7 node 時間 (read-heavy・build・準備費は別) — 1 タスクの job 合計が 2 node 時間
  以上になる投入は、見積りを示してユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料
  `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 0。
- {{T:vldb-p1-function-space}} **P1・新規 (VLDB 差分分析 P1: 関数単位のコード空間)**: LLM が関数の本体を書く合成空間を 1 つ開く (候補: Silo の
  abort 後の待機・再試行方策、競合の状態に応じた待機方策)。現行の編集面 (合成枝の中身だけ・#include / 関数 / 型の追加禁止・coder が編集できる
  3 file) を広げてよい ({{D:vldb-direction-verdicts}} 項 3)。正しさゲートは不変 (anomaly は即 reject、trace は compile 時に除去、毎回検証して
  構造化フィードバックを返す)。段取り = (1) 対象関数・designated source・編集面 hook と coder 権限の変更点・Tier0 を計算なしで設計する、
  (2) hook と権限の変更は Codex author が `hooks/README.md` の契約とテストに従って実装する、(3) 最初の生成と評価。測るもの = 有効候補率、
  anomaly で reject された率と壊れ方の分類、最良 certified 候補 vs stock・`p2_2_flag_opt`・調整済み静的 backoff。LLM が生成した候補を verifier が
  捕まえた記録は、差分分析 §0 の grep の範囲では見つかっていない (全数の証明ではない)。計算: (2) の実装に伴う開発検査 (受入・焦点走・変異) と
  (3) の生成・評価を含め、1 タスク (1 本の wave) で投げる job の合計が 2 node 時間以上になる場合は、node 時間と LLM の直列時間の見積りを示して
  ユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P1・§8。
- {{T:vldb-p2-fair-comparison}} **P1・新規 (VLDB 差分分析 P2: 公平な比較基盤と第 2 プロトコル)**: random・sweep (座標探索)・BO・進化探索・LLM を
  同じ候補適用・検証・計測の口に通し、同じ stock・既知最良 `p2_2_flag_opt`・初期候補・観測情報を与える比較基盤を作る。既存研究の探索法を移植したら
  「再実装」と明記する。第 2 プロトコルは trace のある MOCC が第一候補で、X/P 計装の pin 候補化 ([T-2844]、Codex 枠の復帰後) を前提にする。
  有限空間だけで LLM が負けてもコード合成一般の結論にはしない ({{T:vldb-p1-function-space}} が要る理由)。完了 = 5 手法が同じ口で走る基盤と、
  第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload)。計算: 疎通は balanced 相当で検証だけ約 8〜16 node 時間 (準備・build・性能測定は別) —
  見積りを示してユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P2、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 1。
- {{T:vldb-p3-search-replicates}} **P1・新規 (VLDB 差分分析 P3: 探索の独立反復と費用・成果の曲線)**: 手法ごとに探索を独立にやり直し
  (候補を測り直すこととは別)、費用と成果の曲線を取る。候補評価数を揃えた比較と経過時間を揃えた比較を分け、有効候補率・最初の有用候補までの時間・
  検証時間・node 時間・人間の介入を記録する (複製候補・compile 失敗も費用に含める)。規模の案 (Codex): 試走 = 2 プロトコル × 2 課題 × 5 手法 ×
  3 独立探索 × 8 候補 = 480 候補評価 (B-5 からの換算で約 68 node 時間)、本比較 = 3,600 候補評価 (約 510 node 時間、LLM は直列で約 120〜156 時間)。
  本比較の規模は試走の探索間分散から決める。既存の有限空間での LLM / random / sweep の対照 [T-2797] (B-5、D2200 項 1 の段階認可) との関係は
  本項の設計で整理する。前提 = {{T:vldb-p1-function-space}} の空間と {{T:vldb-p2-fair-comparison}} の基盤。計算: 試走・本比較とも、それぞれ
  node 時間と LLM の直列時間の見積りを示してユーザー確認後に投入し、一括承認にしない ({{D:vldb-direction-verdicts}} 項 4)。一次資料
  `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 2。
- {{T:vldb-p4-holdout-transfer}} **P1・新規 (VLDB 差分分析 P4: 未知条件への転移と再現)**: 生成・選択に使わない条件 (read/write 比・競合・
  スレッド数・トランザクション長・アクセス集合の重なり) を結果を見る前に留保し、stock・強い静的設定・各手法の選択結果を比べる。主要結果は別日・
  別割当てで追試し、同等幅と信頼区間は事前に決める。既知最良 `p2_2_flag_opt` を外さず、CCBench 既定比の大きな数字を主結果にしない。
  前提 = {{T:vldb-p3-search-replicates}} の選択結果。規模の例: 2 プロトコル × 27 条件 × 6 候補 × 8 反復 = 2,592 run ≈ 54 node 時間 (検証・較正・
  別日追試は別)。計算: 見積りを示してユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P4、
  `output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 3。
- {{T:vldb-p5-interventions}} **P1・新規 (VLDB 差分分析 P5: 介入による理由の説明)**: 成功・失敗を代表する少数の課題で、正しい workload 記述 /
  伏せた記述 / 入れ替えた記述、critic あり / なしを比べる。verifier と失敗理由の返却は外さない (規律 2・3。これらの因果効果を直接切り分けられない
  ことは論文の限界として書く)。出力コードは人が読んで、既知候補の再発見・無効変更・機構の変更に分ける。前提 = {{T:vldb-p3-search-replicates}}
  の課題と基盤。規模の案: 追加 120〜240 候補評価 (約 17〜34 node 時間、LLM の直列時間 約 20〜52 時間)。計算: 見積りを示してユーザー確認後に
  投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P5、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 4。
- {{T:vldb-p6-repro-package}} **P1・新規 (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクを要するので、
  実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。LLM の再生成と、保存済み候補の
  再検証・再計測を分け、モデル更新後も後者を実行できるようにする。失敗候補と否定的結果を含めて公開してよい ({{D:vldb-direction-verdicts}} 項 6)。
  provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。最初に、公開する trace の量と保存費を
  見積もる (計算なし)。計算: 主要図の再実行 (Codex 案で実験予算の 10〜20% を仮置き) は、見積りを示してユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。
  一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P6、`output/insights/2026-09-21/vldb-direction/codex-consult-1.md` の優先 5。
- {{T:vldb-tpcc-stage1}} **P1・新規 (VLDB TPC-C 段 1: NewOrder / Payment の正しさ認定)**: TPC-C を必須に入れる改訂 ({{D:vldb-direction-verdicts}}
  項 2。ユーザーの疑義を受けた親の改訂推奨で、反対が無いので進める) の段 1。NewOrder / Payment (CCBench 既定比 45% + 43%、点読み・点書き・insert
  のみで `tx.scan` を使わない) の合成候補を直列化可能性で認定できるようにする。要るもの = trace の表識別子、insert の意味、app 層 abort の計数、
  `orchestrator/campaign/pipeline.py` が trace 取得の前に `ycsb_` 以外の binary を拒否している allowlist の拡張 (table ID を足すだけでは済まない)。
  まず設計と工数の見積り (precheck、計算なし) を行い、実装は Codex author。正しさゲートは不変で、trace は compile 時に除去する (規律 1)。
  本項で TPC-C の corpus が入るときに見送り台帳 [T-156] (selector-8b descriptor への set-size 条件) の発火条件「TPC-C 級 workload corpus を
  採るとき」が成立するので、同項を再評価し、既裁定の「着手前に workload 別の set-size 分布を測る」順序を確認する。計算: 検証走・計測で 1 タスクの
  job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。
- {{T:vldb-tpcc-stage2}} **P1・新規 (VLDB TPC-C 段 2: 全 5 取引への拡張)**: {{T:vldb-tpcc-stage1}} の後に、Delivery / OrderStatus / StockLevel
  (各 4%、`tx.scan` の範囲読みを使う) を含む全 5 取引へ認定を広げる。範囲読みを述語読みとして扱い、範囲への insert との依存 (phantom) を検出する
  verifier 拡張が要る (現行 verifier は predicate / phantom を保証しないと roadmap §3.1 が宣言している)。設計と工数の見積りは段 1 の precheck と
  同時に行う (計算なし)。正しさゲートは不変。計算: 検証走・計測で 1 タスクの job 合計が 2 node 時間以上になる投入は、見積りを示してユーザー確認後に
  投入する ({{D:vldb-direction-verdicts}} 項 4)。一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §10、roadmap §3.1。

### 見送り追記

- [T-156] 2026-09-21 関連記録 (TPC-C の起票、未発火): {{D:vldb-direction-verdicts}} 項 2 で TPC-C を論文の必須経路に入れ {{T:vldb-tpcc-stage1}} / {{T:vldb-tpcc-stage2}} を起票した。発火条件「TPC-C 級 workload corpus を採るとき」は段 1 で corpus の実体が入るときに成立するとみなし、再評価はその wave で行う (本記録では再評価しない)。
