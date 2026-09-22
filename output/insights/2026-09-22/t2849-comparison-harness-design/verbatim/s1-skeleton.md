# 設計骨子 (段 2 plan の代わり、親起草) — [T-2849] 5 手法比較基盤

brief (`brief.md`) の (P1)〜(P10) を節に展開した骨子。値・file:line は `facts.md` に出所つきで置く。

## 1. 位置づけと主張の射程

- 目的: EA&B の比較 (差分分析 §3 の仮説 1・2) を、同じ口・同じ初期条件・同じ費用単位で取る基盤の設計。本 wave は設計だけ。
- 比較 A (同じ空間内の探索法比較) と比較 B (LLM×C++ の空間拡張) を分ける (D2214 §5)。本基盤の 5 手法比較は比較 A。
- 主張しない: LLM の必要性、非 LLM 生成器一般への優越、有限空間の結果のコード合成一般への拡張 (差分分析 §4 P2 注意、D1067)。

## 2. 口の型 (P1)

- 層: 生成器 → 候補文書 → 共通評価 → 観測記録 → 生成器。
- 生成器の契約: `ask(space, seed, history) -> candidate` / `tell(observation)`。入力は空間定義・seed preimage・自系列の観測だけ。他系列・他 arm・floor・偵察結果を読まない。1 回の ask が A を 1 消費する。内部の選び直し (BO の獲得関数最大化、進化の変異の型検査、random の棄却抽出) は測定を使わない決定的計算に限り A を消費しない。LLM は 1 回の役割呼び出し = 1 ask で、隠れた再生成をしない (B-5 §3.1)。
- 候補文書: 既存の閉じた proposal schema (planner / coder / prior_critic_reverse)。機械生成は B-5 の `machine_proposal_document` と同形。由来は proposal に入れず、台帳の arm と build admission (`MACHINE_GENERATED` / `CODER_AUTHORED`) で記録する。
- 共通評価: `p3_s4_loop --run-iteration` → 文法・帰属整合・検疫 → Tier0 (D2215) → `run_campaign` / `pipeline.evaluate` (trace build で verify、trace-disabled build で bench)。手法によって経路を変えない。
- 観測記録: 1 つの producer が WAL / sidecar / tier0.json から作る (P5)。
- 系列 runner: B-5 の `run_series` / `SeriesLedger` の形を arm 汎用に広げた兄弟 module (B-5 の file は変えない)。
- 現状の結合 (実装単位): `--machine-generated-proposal` は `--b5-slot` 必須で、slot key は B-5 接頭辞必須。loop の genome は silo 固定。

## 3. 空間 (P2) と各手法の支持集合 (P3)

| 空間 | 候補表現 | 実在 | random | sweep (座標探索) | BO | 進化 | LLM |
|---|---|---|---|---|---|---|---|
| S1 silo backoff | 整数 1..1000 (µs) | 実在 | B-5 log-uniform | B-5 sweep-matched (1 次元の座標探索 = 格子の順序) | log v 上の GP-EI、獲得は 1000 点の全列挙 | log v 上の変異 (+ 交叉なし) | K2 手動 loop (B-5 §4.1) または知識なし版 |
| S2 MOCC backoff | 同上、genome は MOCC | pin 前進待ち | S1 と同じ | 同じ | 同じ | 同じ | 同じ |
| S3 policy IR | D2214 の型付き有限 IR | C 段以後 | 型付き木の生成 (固定分布) | template の座標 | template の座標上の GP-EI (混合 kernel) | 型を保つ subtree 変異・交叉 | LLM×IR (D2214 §4) |

- S3 で sweep / BO の支持集合は template の像 (IR の部分集合)。B-5 §2 の「共通なのは受理集合、支持集合は生成器ごとに違う」を踏襲して明示する。
- 比較 B の LLM×C++ は本基盤の同じ口を通すが、5 手法比較の族には入れない。

## 4. BO / 進化の実装の出所 (P4)

- repo に BO・進化の実装は 0 件、login の python3 3.10.12 で import できる外部 package は numpy 2.2.6 だけ (scipy / sklearn / optuna / skopt / botorch / torch / smac / nevergrad / deap は無い)。
- BO: EGO (Jones, Schonlau, Welch 1998) の GP-EI を標準ライブラリで再実装。kernel・超パラメータの決め方・初期 design は凍結定数。
- 進化: S1/S2 は (1+λ) または (μ+λ) の実数 (log) 変異、S3 は型付き GP (Montana 1995) の subtree 変異・交叉の再実装。
- 名乗り: 「〜の再実装」と書き、元の実装の移植・同一性は主張しない。Polyjuice の EA の再現とは呼ばない (方策表と IR が別物)。

## 5. 揃えるもの (P5・P6)

- 観測記録の field: 候補 identity、A / B、段ごとの結果 (文法・検疫・Tier0・build・verify・bench)、anomaly の構造化 digest、throughput の session median と CV、leading indicators、時間。
- 非 LLM 手法が使うのは fitness (certified の session median) と有効性の分類だけ。LLM の射影 (whiteboard 5 field、critic 診断 D2155) は同じ記録から作る。
- 知識: 主比較は全 arm 知識なし (K0)。K2 の知識射影つき LLM は別の構成として分けて呼ぶ (B-5 は K2 のまま)。
- stock: 系列開始 stock (同機体・同 job) と block stock。全 arm へ観測として渡す。
- exact reference: `p2_2_flag_opt` (`BACK_OFF=0`) と調整済み静的 backoff を block ごとに測る。全 arm へ参照水準として渡す場合は「既知結果を条件とする探索」の構成と明記し、渡さない構成と分ける。空間の点としては扱わない。
- 空間内の初期候補: 空間ごとの固定列 (S1: 静的 5 / 10 µs など、S3: D2214 §5 の seed) を全系列の最初の k 評価として測り、B の外に置く。手法固有の初期化 (BO の初期 design、進化の初期個体群の残り) は B から払う。

## 6. 費用の計上単位 (P7)

- 論理: A (ask 回数)、B (pipeline 投入)、session (論理 / 物理)、endpoint 再計測、stock。
- 重複: 同じ identity の再提案は A・B を消費して fresh に測る (B-5 §2)。系列内の一意 identity 数を別に数える。
- compile 失敗: Tier0 の compile 失敗は A だけ (費用欄には compile 時間を入れる)。pipeline 内の build 失敗は B。
- anomaly reject: B を消費。
- 機械故障の retry: B-5 §3.3 の規則 (追加 2 回まで、論理 slot は同じ、物理費用は全件記録)。
- 物理: slot ごとの job Elapse、LLM 役割の wall、親の待機、人間の介入回数を別欄。
- 比較の揃え方: 評価数で揃える (B 同一) と費用で揃える (node 秒、LLM wall は別軸) の両方を [T-2850] が切れるよう、各 event に時刻を残す。

## 7. B-5 の再利用範囲 (P8)

- そのまま使う: 台帳 event schema、slot の結果分類 (`classify_slot`)、A/B と retry と品質欠測の規則、Tier0 契約、endpoint 選択と N_eval 再計測、block stock と fallback の意味、S1 の random / sweep 生成器 (preimage の名前空間だけ変える)、LLM arm の親運用 (D2216)、共通 walltime の決め方 (D2217)。
- 変える必要があるもの: ARMS の 3 固定、値の文法 (1..1000) と値による endpoint 同一性、B-5 接頭辞の slot key、`machine_proposal_document` の arm 制限。
- 使わないもの: B-5 の判定規則 (LLM 対 2 baseline の対差 permutation) と cohort。B-5 の標本と新しい比較の標本を混ぜない。

## 8. MOCC の差し込み口 (P9)

- 前提: T-2858 (人間の push → pin 再承認の提示 → gitlink / CURRENT_PIN 更新の別 wave)。それまで S2 は無効。
- S2 の空間: backoff 値。MOCC は `include/backoff.hh` を include し、`BACKOFF_FIXED` は全 protocol 共通の define。温度述語 hole は proof-only (D2134 項 9) で使わない。
- 差し込むときに要るもの: genome の protocol 化 (loop の silo 固定)、MOCC の動作点の較正 (calibrator)、MOCC の既知最良 (MOCC_SPACE 8 genome の全列挙、計算は事前確認)、X/P つき certified の射程確認 (現実績は tuple 200・1 秒・1/4 thread)。
- 疎通 (T-2849 の完了条件: 20〜40 候補 × 3 workload) は本 wave では投入しない。見積りは起票の約 8〜16 node 時間 (検証のみ) を引用する。

## 9. 実装単位 (後続 wave、本 wave は実装しない) (P10)

1. 機械生成 proposal の slot を B-5 接頭辞から外す (名前空間つき slot)。
2. 兄弟 series runner と arm 汎用の台帳 (B-5 schema の上位互換)。
3. 観測記録 producer。
4. 生成器 5 種 (S1 から)。
5. genome の protocol 化 (S2 用、T-2858 後)。
6. S3 adapter (T-2857 C・D 段の後)。

新しい gate・検査・台帳は足さない。
