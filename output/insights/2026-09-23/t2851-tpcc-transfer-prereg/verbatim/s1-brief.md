# [T-2851] の残り (4) 段 1 brief (親、2026-09-23 JST、base local main cadaf3805)

研究前進: EA&B 中心命題の第 3 仮説 (探索時の勝者と未知 workload で採るべき候補は異なる、gap-analysis §4 P4) を TPC-C でも HARKing なしで
検定できる状態にする。D2212 項 2 で TPC-C は必須、v1 (`docs/unseen-condition-transfer-preregistration.md`) §14 は TPC-C の留保を
「TPC-C の生成・探索・選択が始まる前に別の登録で固定する」必須の未完項目とした。完了判定 = TPC-C の学習条件 (錨) と留保条件・不使用義務・
解析規則を固定した別の事前登録が local main に着地し、着地時点で留保が効力を持つこと (D2223 と同じ 2 段の効力)。

scope (変更面): 新規 `docs/tpcc-unseen-condition-transfer-preregistration.md` (本書)、`docs/README.md` へ 1 bullet、spool fragment
(worklog 1 + decisions 1)、insight `output/insights/2026-09-23/t2851-tpcc-transfer-prereg/`。v1 本文は触らない (v1 §13.2: 着地後は既存 bytes を
書き換えない。TPC-C の追加は「追補」の許可範囲 (誤記訂正・発効束の補足) に入らないので、別文書にする)。コード・テスト・runner・phase doc・
稼働 wave の file (T-2854 系の CCBench branch・verifier、T-2850 系) は触らない。T-2850 の選択結果、測定の発効、runner 実装、計算、gate・検査・台帳の追加は scope 外。

確定済みユーザー裁定: D2212 (TPC-C 必須、計算は 1 タスク 2 node 時間以上で都度確認)、D2219 項 2 (段 1 = NewOrder/Payment → 段 2 = 全 5 取引)、
D2223 (留保の効力は着地時点、測定の発効は別の決定)。

不変条件: 絶対規律 1〜7 (性能は trace-disabled、検証は別 build・別 run、anomaly は即失格、規律 2 を緩めない)。D1789 / D1790、hash 自己参照禁止。
v1 の §2.3 の留保条件 (YCSB) と不使用義務は変えない。8b の値は使わない。

実測した前提 (調査子 1 本 + 親の現物検算、CCBench pin e9e477ca):
- TPC-C の実行時引数: `tpcc_num_wh` (既定 1)、`tpcc_perc_payment` 43 / `_order_status` 4 / `_delivery` 4 / `_stock_level` 4 (NewOrder は残差)、
  `tpcc_interactive_ms` 0、共通の `thread_num`・`extime`・`epoch_time`・`clocks_per_us` (`include/tpcc/tpcc_common.hh`、`cc/<p>/include/common.hh`)。
- home warehouse = `thread_id mod 倉庫数 + 1` (`include/tpcc.hh:40`)。明細数 5〜15 (`tpcc_query.hh:98`)、remote 品目 1% (`:111`)、remote Payment 15% (`:163-178`) は
  コンパイル時定数でフラグではない。→ v1 の「txn の操作数」「アクセス集合の重なり」に当たる因子は CCBench 改変なしでは動かせない。
- 段 1 は既存フラグで OrderStatus/Delivery/StockLevel を 0 にでき NewOrder 57 : Payment 43 (設計 README §3.5)。
- repo に TPC-C の性能測定は 0 件。T-2854 の構造検査 (thread 2・extime 1・倉庫 1・段 1 構成、計算ノード 1 走) だけがある。
- orchestrator に TPC-C の学習条件・campaign 定義は無い。trace witness 経路は `ycsb_` 以外を拒否 (`pipeline.py:432-434`)。TPC-C の生成・探索・選択は未開始。
- 段 1 の認定は未完 (verifier は v3 run に `Integrity.v3_existence_unverified` を立てる)、段 2 (T-2855) は未着手。
- Pegasus = 1 socket 48 物理コア HT 無効。

(P1)〜(P9) = 親の provisional 裁定・攻撃対象:
(P1) 錨 (学習条件) は本書が定める (既存の定義が無いため)。段ごとに 2 錨 = 高競合 H (倉庫 1) と低競合 L (倉庫 48 = thread 数、home が thread ごとに別)、
     共通 thread 48・extime 3 s・think time 0。段 1 の構成 = Payment 43・他 3 種 0 (NewOrder 57)、段 2 = CCBench 既定 45/43/4/4/4。錨は 4 点。
     TPC-C の探索群の学習条件は錨の部分集合でなければならず、外れるなら生成開始前に別の登録が要る (v1 §3.2 と同じ)。
(P2) 因子は 3 つだけ: 倉庫数 (競合とデータ量の複合、home 割当ても変わる)、thread 数、取引構成。明細数・remote 比率・think time は動かさない
     (前 2 者はフラグでない、think time は ms 単位の sleep で別の regime になる)。v1 の 5 因子との対応表と欠ける理由を書く。
(P3) 水準: 倉庫 {4 (H に結ぶ), 16 (L に結ぶ)} = 錨の間の内挿 (log2 で 0・2・4・5.58)。thread {12, 24}。段 1 の構成 = Payment {20, 70} (NewOrder 80, 30)。
     段 2 の構成 = 範囲読み 3 取引を各 {1, 10} (計 3% / 30%、Payment 43 固定、NewOrder 54 / 27)。
(P4) 配置 OFAT: 段ごとに 錨 2 + 倉庫内挿 2 + 錨 2 × (thread 2 + 構成 2) = 12 cell、うち留保 10。2 段で 24 cell (留保 20) / protocol。
(P5) 段をまたぐ使用: 段 2 の錨 (既定構成) は段 2 の学習条件であり、段 1 の留保ではない。段 1 で学習した候補を段 2 の cell で測ることは本書の主要族に入れない。
     段 1 の留保と段 2 の留保はともに本書の着地で効力を持ち、段 1 の探索にも段 2 の探索にも入れない。
(P6) 比較対象: R0 = 上流既定の build (Silo は BACK_OFF=1)。TPC-C の既知最良・強い静的設定は無い (p2_2_flag_opt は YCSB で選んだもの)。
     発効の決定で、protocol ごとに v1 の MOCC と同じ 3 択 (参照を錨の測定だけで根拠付きに固定 / 記述専用 / 含めない) を留保条件の結果を見る前に書く。
(P7) 解析規則は v1 §5〜§9 を節名で引いて同じにする (n = 32、δ = ln(1.03)、Bonferroni 同時区間、2 cohort 一致、欠測・単独性・再投入の規則、順序の鍵だけ
     `t2851-tpcc-order-v1|...` に変える)。主要族と M は段ごとに別 (段ごとに発効が別)。v1 の族とも別。1 走の値は binary が報告する全取引の commit throughput。
(P8) 解禁: 段 s の留保 cell での実行は、(a) 段 s の測定の発効の決定、(b) 段 s の対象探索群の全候補の凍結記録、(c) 段 s の verifier が v3 run を認定できる状態
     (存在履歴の検査が入り印が外れていること、段 2 は範囲読み・phantom の検出) の 3 つが揃うまで 1 走もしない。認定できない cell の性能は主張に使わない (規律 2)。
(P9) 既知結果・HARKing: TPC-C の性能測定 0 件、T-2854 の構造検査の条件、設計 README の「倉庫 1・48 thread で Payment に競合が集中」の定性的記述を開示する。
     費用は未測定 (倉庫 48 のロード時間を含め) で、試算の形だけ置き、発効時に見積もり直してユーザー確認 (D2212 項 4)。

受入・実測環境: 計算投入なし。検査は login の `python3 tools/check_docs.py`・三軸走査 CLI・受入全走 (land 前、`tools/dev_wave_wait.py acceptance --lease-optional`)。
分割方針: docs-only 軽量版。段 2 は省き brief を plan とする。設計択一が割れるので段 3 は read-only codex 2 レンズ (A: 条件設計の妥当性 — 錨・因子・水準・
配置・段の境界・TPC-C 実装の事実との整合、B: 留保の漏洩・不使用義務・解禁・HARKing・v1 との整合・過剰)。段 5 は親が本文を書く (実装面なし、変異免除)。
段 6 は read-only review 1 本 (一次資料の事実を再抽出する docs-only のため必須)。
