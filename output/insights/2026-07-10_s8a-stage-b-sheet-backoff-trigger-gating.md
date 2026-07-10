# 軸定義シート — silo-backoff-trigger-gating (段 8a 段階 B、独立再導出)

**位置づけ:** axis-proposer n=1 の採用提案 1 (人間 gate 決着 = worklog 2026-07-10 (16)) の
軸オンボーディング段階 B 入口シート (axis-onboarding §2)。**各欄は提案の転写ではなく、
pinned HEAD (d706650) の実コード裏取りによる信頼中核の独立再導出** (axis-onboarding §2 の
LLM 由来規定、規律 6)。提案原文 = `output/insights/2026-07-10_s8a-n1-proposal-and-scoring.json`
proposals[0] (untrusted データ)。照合用 provenance 三点セット = 同 `-provenance.json`。

**実コード裏取りの参照行はすべて external/ccbench @ d706650 (CURRENT_PIN) のもの。**

**改訂 (2026-07-10): 3 レンズ敵対レビュー (workflow wf_5aeaba58-dc5、verdict = 全レンズ
adopt-with-conditions) の裁定を反映済み。** D47 必須検査 3 点 = 全 PASS。反映内容と実装
着手前の必須条件は D48 が正本。初版からの主な変更: 記録偽装遮断の執行主体の訂正 (AUD-1
must-fix)・骨格の #if 囲みによる stock inert 化 (F1)・sentinel リセット契約 (AUD-2/F6)・
構文契約の絞り込み = 偵察空間との一致 (AUD-3/F2 統合)・要因記録 positive control の必須
昇格 (AUD-4)・「差分」節の誇大主張訂正 (LT-1)。

---

## シート本体

**軸名:** silo-backoff-trigger-gating

**変異型:** コード片 (gate 述語。スカラー値なし — ただし縮退リスクは「reward hack 仮説」欄)

**SOURCE_REL:** `cc/silo/transaction.cc` — EVOLVE_BLOCK_SOURCES 内 = 既開通
(`orchestrator/campaign/source_digest.py` の `EVOLVE_BLOCK_SOURCES` で確認)。
**要因記録を transaction.cc ファイルスコープに置く設計 (下記) により ALLOWLIST 拡張の
先行タスクは不要。** TxExecutor メンバ追加に逃げると `cc/silo/include/transaction.hh`
(境界外) の改変 = +1 セッションの独立レビューが要る — 本シートは前者を採る。
**identity 面の注記 (レビュー F1):** 要因記録を無条件 (両ビルド共通) で足すと pinned
baseline に対して inert でなくなり、stock genome の `src_token="stock"` 正規化が壊れる
(`source_digest.resolve` は working-tree と baseline の一致時のみ STOCK を返す)。対策 =
**骨格全体 (enum 定義 + 記録 store + gate) を `#if CCBENCH_BACKOFF_TRIGGER_GATING` で囲み、
stock (フラグ 0) では preprocess 後に原文と同一 = inert にする** (D48 必須条件)。PIN 前進は
不要。記録コストは variant 側だけに乗る自己ペナルティ (正直側) で、退化点 (空集合) も
真の BACK_OFF=0 相当になる。

**マーカー ID:** silo-backoff-trigger-gating

**hole の位置と骨格:**
- hole (coder の編集面) は 1 箇所: `TxExecutor::abort()` 末尾の `#if BACK_OFF` ブロック内
  (transaction.cc:42-52)、`Backoff::backoff(FLAGS_clocks_per_us)` 呼出 (:47) を gate する
  **述語式のみ**。骨格 = `#if BACKOFF_TRIGGER_GATING` (合成枝 = 述語付き呼出) / `#else`
  (stock = 無条件呼出を逐語温存) / `#endif`。
- **前提骨格 (人間が一度入れる、coder 不可触): abort 要因の記録。** 現状 abort() は要因を
  知らない — `status_` は 4 値 enum (invalid/inflight/committed/aborted、transaction.hh:24-29)
  で要因を持たず、呼出側 (ycsb.hh:150 の早期 abort / :162 の commit 失敗) も渡していない。
  要因の発生点は**全て transaction.cc 内に閉じる** (実読による全数):
  1. 施錠競合 — `lockWriteSet()` transaction.cc:160-164 (`NO_WAIT_LOCKING_IN_VALIDATION`)
  2. UPDATE 対象 absent — `lockWriteSet()` :185-189
  3. read-set 検証失敗 (tid/epoch 変化) — `validationPhase()` :453-461
  4. read-set 検証失敗 (locked かつ非 own-write) — `validationPhase()` :466-473
  5. node 検証失敗 — `validationPhase()` :478-484
  6. 早期 abort (実行フェーズ): insert の node 版数不一致 :97-99 / scan callback の node
     版数不一致 :726 (`TxScanCallback::on_resp_node`)。read()/read_internal()/update()/
     delete_record() は abort をセットしない (実読で確認 — read の lock spin :255 は待つ
     だけで abort しない)。**YCSB は insert/scan を発行しないため、計測 workload では要因は
     {施錠競合, read-vali ×2, node-vali(≈0), absent(≈0)} に集中する。**
- 記録の実装 (レビュー裁定反映): transaction.cc **ファイルスコープの thread_local 変数**
  (要因 enum)。TxExecutor はスレッドごと 1 個 (`thid_` 保持、worker 1:1 は ycsb.hh:97-170
  で裏取り済み) なので意味論が一致し、EVOLVE_BLOCK_SOURCES 内で完結する。
  - **store は 7 代入点すべてに置く** (:98/:162/:187/:458/:470/:481/:726 — YCSB 不発の
    insert/scan callback も含める。thread_local は tx/retry を跨いで永続するため、将来の
    workload 拡張で stale 参照 (misattribution) を起こさないための全数計装、レビュー F6)。
  - **begin() で要因を sentinel「未記録」に fail-safe リセットし、gate は sentinel を
    stock デフォルト (= backoff する) として扱う契約にする** (レビュー AUD-2)。app 層で
    `status_=aborted` を代入する非 YCSB workload (tpcc.hh:61-84 / bomb 系) では要因が
    未記録のまま abort() に到達するが、sentinel 契約により stock 挙動 (待つ) に落ちる。
  - **要因記録は gate 述語が perf ビルドで読む CC-native メタデータであり `#if TRACE` に
    入れてはいけない** (入れると perf ビルドで gate が壊れる。規律 1 の「CC 本来のもの」側)。
  - **骨格全体 (enum + store + gate) を `#if CCBENCH_BACKOFF_TRIGGER_GATING` で囲む**
    (SOURCE_REL 欄の identity 注記、レビュー F1)。stock では preprocess 後に原文一致 =
    inert。variant ビルドでは両 (TRACE on/off) ビルドに同一に入るため diff-of-diffs
    (`assert_trace_diff_matches_head`) とも整合する。
- **記録を骨格の専権 (coder 不可触) にするのが本軸の設計の要** — coder が記録を触れると
  「要因を偽装して gate の見かけを整える」経路が開く (reward hack 欄)。

**構文契約 (レビュー AUD-3/F2 の統合裁定で絞り込み):** gate 述語が読めるのは**骨格が定義
する要因 enum とコンパイル時定数のみ**。straight-line・副作用なし (要因記録への書込は骨格の
専権)。**明示禁止: `thid_` (per-thread 優先 gate = fairness hack、ギャラリー型 15 系) /
`result_` 系カウンタ (run 自身の fitness 信号への適応 = 型 12 入力隔離の破れ + 適応制御
ループ汚染) / read_set_・write_set_・node_map_ (gate 点 :47 では :38-40 で clear 済み —
読むと空コンテナの silent 縮退)。** この絞り込みにより偵察の列挙空間 (要因部分集合) と
coder の変異空間が一致し、偵察の生死判定が「部分空間の下界」問題 (レビュー F2) を持たなく
なる。メンバ読取への契約拡張は本シートの改訂 = 段階 B 差し戻し (再レビュー) を要する。
閉じた領域制約 (D23 道 Y: #include 追加・新規関数/マクロ/型定義の禁止・非決定ビルトイン
禁止) は既存 2 軸と同一。

**stock の動作:** `BACK_OFF=1` のとき abort() 末尾で要因不問に `Backoff::backoff()` を発火
(transaction.cc:47)。待機量は全スレッド共有の atomic `Backoff_` を leader が勾配法で適応更新
(backoff.hh:44-92 `update_backoff`、:94-108 `backoff` の spin 待機、transaction.cc:704-709
`leaderWork` → `leaderBackoffWork`)。**gate は呼出の有無のみに触れ、待機量の決定
(= magnitude 軸の hole、backoff.hh 内 EVOLVE-BLOCK) と適応更新には触れない** —
既存軸との直交性の根拠。

**フラグ名:** `CCBENCH_BACKOFF_TRIGGER_GATING` (0=stock / 1=合成枝。コード片軸 =
SORT_VARIANT 型の on/off。cmake universal 相乗り — silo hole かつ他 protocol に無害な
マクロなので D42 条件 5 の成立条件を満たす)。**E 段 driver の `_BASE` には `BACK_OFF: 1`
の明示が必須** (レビュー F6 — hole は `#if BACK_OFF` ブロック内に居るため、BACK_OFF=0 だと
軸ごと消える。sort driver の `_BASE` と同じ扱い)。

**壊しうる不変条件:**
- serializability: **原理的に不可侵** — gate は abort 決定・状態クリア (read/write/node_map
  clear :38-40) 後の待機有無のみに触れる (`Backoff::backoff` は `Backoff_` を読むだけの純
  spin で共有状態を変えない、backoff.hh:94-108 — レビュー 2 レンズが独立に支持)。ただし
  この主張は「骨格の要因記録 store が abort 分岐の制御フローを変えない」ことに依存する —
  **骨格 patch の中立性レビュー (7 store が純代入・制御フロー不変・commit path 不触) を
  C 段着手前の必須条件に凍結 (D48、レビュー AUD-5/C6)**。
- (残存リスク、レビュー AUD-2) 非 YCSB workload (tpcc/bomb 系) は app 層で
  `status_=aborted` を代入し要因を記録しない。universal フラグでそれらに焼いた場合、
  sentinel 契約 (骨格欄) により stock 挙動へ fail-safe に落ちるが、「gate が効かない」
  だけで気づきにくい。非 YCSB へ軸を広げるときは app 層 abort の計装が先行タスク。
- liveness: gate で待機を失った要因の abort storm / live-lock。特に施錠競合 abort を素通し
  すると、相手が lock 保持中に即時再突入して spin する (NO_WAIT の abort → RETRY ループ、
  ycsb.hh:108-165)。全枯渇は trace-empty abort で fails-closed に捕まるが、部分的な悪化は
  throughput 低下として現れるのみ。
- fairness: 要因が tx クラスと相関する場合 (例: read-heavy な tx は read-vali abort が主、
  write たっぷりの tx は施錠競合 abort が主)、特定クラスにだけ待機を課す偏りを作れる。
- 適応制御ループの汚染 (2 次効果): gate で発火率が変わると leader の勾配推定 (commit tput
  vs Backoff_) の入力分布が変わり、`Backoff_` が別の点に吸着する。magnitude 軸との交互作用
  であり「gate 単独の効果」の帰属を曇らせる (critic 帰属・偵察設計の注意点)。

**verifier の死角:**
- **abort 要因の記録正確性: trace schema (C/R/W/X/P) は abort イベント・要因を一切持たない**
  (trace.hh 実読: C=commit :78-82 / R=read :84-89 / W=write :91-96 / X=lock-coverage 違反
  :117-120 / P=permutation 違反 transaction.cc:432。abort 数は集計行由来で per-abort 行は
  無い)。gate が意図と別の要因で発火する misattribution は serializability 無傷のまま起きる
  ので verify は緑 = 完全な死角。
- 部分 starvation / fairness: sort 軸の死角 2 (D41) と同型。trace-empty (全枯渇) 以外は
  捕まらない。既存の見送り台帳 (phase3.md 残存リスクの Gini 観測点) がそのまま適用される。

**reward hack 仮説:**
- **述語の定数縮退:** 常 false = `BACK_OFF=0` の言い換え / 常 true = stock の言い換え。
  どちらも既存フラグ空間の点の再包装であり「軸を探索した」ことにならない (D44 決定 1(i) の
  軸適格性を事後に破る縮退)。pre-build 検査 (述語が要因 enum を実際に参照するか) を設ける
  かが設計論点 — 構文検査は恒真化リスク (D30) があるため、偵察空間に退化点 (空集合/全集合)
  を明示的に含めて「縮退点の性能は既知」にしておく方が筋が良い可能性。レビューへ。
- **fairness 犠牲:** 多数派 tx クラスの abort だけ素通しし、少数派に待機を集中させて
  見かけの throughput を稼ぐ。G2 は出ない (serializable なまま)。発火条件は sort 軸の
  fairness 観測点と共通 (headline 候補化したとき Gini/max-min 比)。
- **要因記録の偽装:** 記録を骨格の専権にすることで遮断する。**執行主体の正確な内訳
  (レビュー AUD-1 must-fix の訂正):** (1) **diff 検疫 (DiffQuarantine)** が coder diff の
  hole 外の削除・挿入を行単位で機械拒否する (`diff_quarantine.py` の OUTSIDE_REGION /
  FRAME_ALTERED、:352-374 — marker 外に散在する骨格 store の改変はここで止まる)、
  (2) **auditor diff_digest 機械 gate** (コード片軸、axis-onboarding §4 — 不一致 =
  AuditorGateFailure)、(3) auditor ギャラリーに記録偽装型 (marker 外の骨格 store 無改変の
  行単位確認) を追加 (C 段、ユーザー承認要)。**guard_write はファイル粒度であり marker
  境界を執行しない** — 遮断の根拠に挙げてはいけない (初版の記述は誤りだった)。
- (参考) 提案原文の reward hack 欄は「abort 率指標だけ良く見せる」だったが、独立再導出では
  上記 3 経路を採る — abort 率は gate で直接操作できない (待機を消すと abort はむしろ増える)。

**positive control 設計 (レビュー AUD-4 で必須に昇格・決着):** gate 自体は**新たな
serializability 不変条件を導入しない** (「壊せない」主張は B レビュー 2 レンズが実コードで
支持 — backoff.hh:94-108 の純 spin) — gate 側の coverage driver は不要。**ただし骨格の
要因記録は「記録の正確性」という新たな検証可能主張を導入する** — trace schema に要因が
載らない以上、misattribution は完全な死角で、誤記録された要因で発火する gate は定数縮退
gate と区別不能になり軸の DoF 自体が未検証になる。よって **C 段の必須 positive control:**
`#if TRACE` 内に要因別 abort 集計を足し (検証専用メタデータなので TRACE 隔離が正しい —
CC-native の記録変数とは別物。規律 1 の両側を 1 軸で使い分ける初のケース)、`ADD_ANALYSIS`
の `local_early_aborts_`/`local_abort_counts_` (ycsb.hh:151-153) と整合検査し、
**misattribution mutation (要因を故意に誤記録する broken patch) で赤になる歯を実走証明
する**。要因記録は単一スレッド決定的実行で観測可能な不変条件なので characterization 型
(axis-onboarding §3-C) が適用できる見込み。

**偵察の列挙空間:** 要因集合の部分集合 gate = 2^N。記録要因を {施錠競合, read-vali-tid,
read-vali-locked, node-vali, absent} の 5 種とすれば 32 点 (+ 対照)。**全点で述語は enum
membership 判定のみ = UB なし・構成的安全**。構文契約を enum + コンパイル時定数に絞った
(構文契約欄) ため**偵察空間 = coder 変異空間** — 偵察の生死判定が部分空間の下界に留まる
問題 (レビュー F2) は構造的に生じない。stock 対照 = 全集合 (全要因で backoff)、退化点 =
空集合 (骨格の #if 囲みにより真の `BACK_OFF=0` 相当、レビュー F1-b)。
**D 段設計の必須前提 (レビュー F3/F4 で昇格):**
1. 要因別 abort 頻度の事前実測で不感ビットを確定する (YCSB では node/absent ≈0 が予想され
   実効空間が {施錠競合, read-vali} 側に縮む — 縮んだ実効空間の規模で sweep を設計する)。
2. read-heavy の floor 較正 (stock backoff の損 -77% = 本軸の最良ケース側なので必須。
   較正できないなら read-heavy を落とす正当化を明文化する)。
3. 適応 `Backoff_` との連成の扱いを凍結する — gate は発火率を変え、leader の勾配ループが
   待機量を再吸着させるため、素の sweep は連成地形を測る。`BACKOFF_FIXED` (magnitude 軸の
   既存機構) で適応を固定した gate 単独地形の観測を含めるか、`Backoff_` 軌跡を記録して
   分離可能にするかを D 段設計で決める。magnitude 軸との直交性主張は adaptive-off 前提の
   限定を付す。
偵察の縮退の守り (レビュー F5 = 未定欄 2 の決着): 述語の構文恒真検査は第一防壁にしない
(D30 — 恒真化しやすい)。退化点 (空集合・全集合) を列挙に明示的に含めて「縮退点の性能を
既知にする」+ auditor 目視が正当な守り。D46 の器 (`run_sweep` 骨格) に載る — ただし
axis-onboarding §1 脚注のとおり軸定数は C 段成果物に置き、偵察器はそこから import する
(現物 `s6_sort_sweep.py` の E 段 import は踏襲しない)。

**感度を持つ workload:** 全 3 類型を残す (機序上の期待が全類型で異なる = 対照として全部
有意義)。balanced/write-heavy は abort baseline 高 (65.3%/59.7%) = 「相殺が効く要因だけ
待つ」利得側の感度。read-heavy は abort baseline 低 (15.6%) で stock backoff の損が最大
(-77%) = 純損回避側の感度。attribution (a) の診断数値は provenance 三点セットの
projected_input 由来 (recommend 由来でないこと照合済み — 機序閾値リテラルはシートに
載せない)。

**計測動作点:** p2_2 確定動作点 (t48 / 1M レコード / skew0.9) — diagnostics と同一動作点で
地形の連続性を保つ。floor: balanced/write-heavy は D46 で使用実績があるが暫定流用の限界が
指摘済み (`s6_sort_sweep.py` の floor は stock 実測の暫定流用で high-abort 点は判定不能
扱い)。**read-heavy の floor 較正は D 段の必須前提** (未定欄の決着 4、レビュー F4)。

---

## 既存軸台帳との構造照合 (人間 gate 材料の再確認 + B レビュー材料)

| 軸 | hole 位置 | 骨格 | 本提案との関係 |
|---|---|---|---|
| silo-backoff-magnitude | `include/backoff.hh` `backoff()` 内 `now_backoff` 決定 (patches/silo-backoff-fixed.patch) | スカラー値 (待機量) | 別ファイル・別処理段 (待機量 vs 発火条件)。gate は `now_backoff` に不可触 |
| silo-writeset-sort (dead) | `cc/silo/transaction.cc` `validationPhase()` の sort comparator (patches/silo-sort-variant.patch) | コード片 (施錠順序) | 同ファイルだが別関数・別処理段 (施錠順序 vs abort 後待機)。write_set_ に不可触 |

→ hole 位置・骨格とも既存 2 軸と構造的に別。軸内探索の言い換えではない。

## 提案原文との差分 (転写でないことの証跡)

- 提案は要因例に「validationPhase / lockWriteSet の abort 分岐」を挙げるのみ — 本シートは
  全 abort 代入点を実読で全数化し (insert :97-99 / scan callback :726 を含む)、YCSB では
  node/absent 系が実質ゼロという頻度構造まで導出した。
- 提案の reward hack 欄 (「abort 率指標だけ良く見せる」) は採らず、実コードから 3 経路
  (定数縮退・fairness・記録偽装) を独立導出した。
- 記録の実装候補 (thread_local によるファイル内完結 vs メンバ追加 = 境界改変) は提案に
  無い本シートの導出。**(レビュー LT-1 訂正) 「CC-native 経路で持ち #if TRACE 外」の方向性
  自体は提案の safety_argument_hypothesis に既出** — 本シートの独立導出は (i) thread_local
  ファイル内完結 vs メンバ追加=境界改変の実装比較、(ii) 規律 1 の両側を 1 軸で使い分ける
  整理 (要因記録 = CC-native・TRACE 外 / 検証用集計 = TRACE 内)、(iii) diff-of-diffs との
  整合の確認、に限る。
- 偵察列挙空間 (部分集合 2^N・構成的安全・退化点) は提案に無い本シートの導出。

## 未定欄の決着 (2026-07-10 敵対レビューによる。初版の 5 項は全て決着)

1. positive control の要否 → **必須に昇格** (AUD-4)。要因記録の TRACE 側整合検査 +
   misattribution mutation の歯の実走証明を C 段必須とする (positive control 欄)。
2. 定数縮退の pre-build 検査 → **構文恒真検査は第一防壁にしない** (F5、D30 整合)。退化点
   (空集合・全集合) の明示列挙 + auditor 目視で守る (偵察空間欄)。
3. scan callback (:726) の記録 → **含める (7 点全 store)** (F6)。thread_local の stale
   参照を将来 workload でも構造的に防ぐ (骨格欄)。
4. read-heavy の floor 較正 → **D 段の必須前提に昇格** (F4)。較正できないなら read-heavy を
   落とす正当化を明文化 (偵察空間欄)。
5. 早期 abort / commit-fail abort の区別 → 要因 enum は transaction.cc 内 7 点で全数計装
   (区別は enum の要因種別に内包される)。`local_early_aborts_` との照合キー設計は C 段の
   整合検査設計に吸収 (AUD-4 の positive control の一部)。
