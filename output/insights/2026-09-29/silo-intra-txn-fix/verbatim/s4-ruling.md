# 段 4 裁定 — silo-intra-txn-fix、2026-09-29 22:15 JST

入力: 段 1 brief (`s1-brief.md`)、段 3 相談 (`consult-a.md`、rc=0、check_codex_output rc=0)。段 4 直前の再走査: local main 8fe87f852 のまま、gitlink 68106660 のまま、[T-2905]・[T-2885] の新しい fragment・裁定なし。

## 所見の裁定

| ID | 裁定 | 採否 | 反映 |
|---|---|---|---|
| S1 (棚卸しの重ね順) | real | 採用 | R8 |
| S2 (「当たる」≠意味の保存、V26・V27) | real | 採用 | R8・R9 |
| S3 (INSERT/DELETE/scan は未修正) | real | 採用 (修正は 2 か所のまま、限界として明記) | R3 |
| S4 (D297 の 2 結果の名称と範囲) | real | 採用 | R4 |
| S5 (not-exercised を合格にしない) | real | 採用 | R5 |
| S6 (計装の F 向け再配置) | real | 採用 | R6 |
| S7 (先例 script の固定 OID) | real | 採用 | R7 |
| S8 (F が変わった場合・引継ぎ材料) | real | 採用 | R10・R11 |

## プラン v2

- **R1 土台と commit:** 土台 = F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` (branch `izanagi-tpcc-v3-silo-mocc-fmt`)。commit 直前に同 ref が F のままか・[T-2854] の前進先が F のままかを再確認し、変わっていたら commit せず停止して記録する。新 branch `izanagi-silo-intra-txn-fix` に 1 commit。file 変更と message は Codex author、commit は親 (`commit -F`)。trailer は 3 行 (Codex author・Codex reviewer・Claude manager、F と同形式)、commit 前に本裁定と行単位で照合する (F1040)。commit は段 6 レビューとその fix の後、計算の前。
- **R2 `#line`:** 値は変えない (相談も妥当と確認)。`ERR` の展開値 106・690 は不変 (親 probe `probe/line_probe.log`)。
- **R3 修正の範囲:** patch と同じ 2 か所だけ (read の探索順、update の 2 度目で `body_` を置換)。INSERT・DELETE の要素への 2 度目の update、`scan` の読み集合優先は未修正の限界として一次資料と上流説明文に書く。
- **R4 D297 (事前登録):**
  - (a) 「値変更の期待拒否」: F → 修正 tip、`--expect-paths cc/silo/transaction.cc`、header 4 引数あり ([T-2854] と同じ起動)、GCC 11・12。期待 = 両方 rc=1、stderr が `TRACE=0 正規化 preprocess 出力が不一致: path='cc/silo/transaction.cc'` を含む (= expect-paths は通過し、最初の不一致が Silo の正規化前処理)。
  - (b) 「補助証拠」: 合成 P′ (親 = pin 68106660、tree = pin + 修正案 patch) → P″ (親 = P′、tree = 修正 tip の tree)。`--expect-paths` なし、header 4 引数あり、GCC 11・12。期待 = 両方 rc=0 (C → F の pass と同型)。保証の名は D297 のまま「選定した macro context における TRACE=0 正規化前処理出力と include 活性の同一性」、pin + 同じ修正と修正 tip の間に限る。後続 gitlink 前進の判定そのものではない (後続 wave が実際の旧新 tip で定義し直す)。
  - (b) が拒否したら記録して原因を調べ、push 依頼には結果をそのまま添える (結果を見て基準を変えない)。
- **R5 trace 実測 (事前登録):** 1 job、F + 計装 (対照) と 修正 tip + 計装 の 2 build × W-rmw・W-blind (U0 と同じ flags・1 秒)。
  - 対照: 到達可能性 pass、D1 a・b1・b2 = 0、D2b は各 workload で (i)+(ii) の違反 ≥1。(i)(ii) の発生条件が両方 0 の workload は判定不能。判定器の verdict は診断として記録。
  - 修正: 到達可能性 pass、D1 = 0、D2b (i)・(ii) とも違反 0 **かつ** 各条項の発生条件 ≥1 (not-exercised は合格にせず判定不能)、判定器 serializable・certified・取引数 = commit 件数。
  - 判定器の `--ccbench-root` は binary を build した計装済み checkout。
- **R6 計装 (F 用):** U0 と同じ Q 行・V 行・刻印 (`YCSB::id_` 8 byte、書き手 `((thid+1)<<48)|通し番号`) の意味、置き場は `gate_<thid>.log`。F の writePhase の YCSB 枝 (TPC-C 文脈でない側) の txid を渡し、UPDATE の `memcpy` 直前に**その時点の write set 要素の `body_`** の先頭 8 byte を V に出す (修正後の 2 度目の置換が反映される位置)。RMW の刻印は `val_` を写した後、`update` に渡す器の `id_` へ。全部 `#if TRACE` の内側。F と修正 tip の両方に厳密適用 (`git apply --check`、fuzz なし) で当たり、`#if TRACE` 枝を除くと F・修正 tip と bytes 一致。`cc/silo/transaction.cc` から `Storage::YCSB` を使わない (前方宣言だけ、記憶の型 1)。
- **R7 CI:** format = 修正 tip の clean checkout の全対象 file (`git ls-files -- cc include common` の .cc/.hh/.cpp) に login clang-format 14.0.0 と image :latest の clang-format で `--dry-run --Werror`、F を同じ手順で対照。build = 計算ノードで image :ci ([T-2854] と同じ SIF、sha256 を記録)、bundle head = 修正 tip・親 = F を照合。job script の固定 OID は引数と照合に置き換える。
- **R8 棚卸し (44 本):** Codex author が repo 外の棚卸し script を書き、親が login で実走する。
  - 各 patch の前提 (重ね順) を patches/README と driver の記述から表にし、出典を 1 行ずつ付ける。前提不明のものは単独適用とし「前提不明」と明記。
  - F と修正 tip の各 clean checkout に、前提を当てた後で `git apply --check` (素の apply、driver と同じ) → scratch で実適用。
  - 当たったものは、マクロ未定義での inert 照合: 対象 file を include 行を空行にして `g++ -E -P -nostdinc -x c++` (TRACE=0 と TRACE=1) し、前提だけを当てた土台と比べる。
  - hunk の行範囲が修正の 2 領域 (read の探索ブロック、update の write set 検査) と重なるものを「意味の点検要」として列挙。
  - 分類: A = F・修正 tip とも当たり inert・非重複、B = 当たるが重複 (親が読んで意味を裁定)、C = F で当たり修正 tip で当たらない、D = F でも当たらない ([T-2854] の範囲、前進先で扱う)、E = 当たるが inert 不一致。
- **R9 V26・V27 と C/B/E の扱い:** patches/ は編集しない。V26・V27 は作り直しを起票する (V26 = 修正後の read が write set を先に返すのを旧 tuple payload に戻す変異、V27 = 2 度目の update の置換を old・new どちらとも違う byte にする変異。どちらも既定 OFF inert・発火計数つき)。C・E は作り直しを起票、B は親が読んで意味を記録。変異を外して緑にしない (規律 2)。
- **R10 F が変わった場合:** R1 の再確認で F が動いていたら停止し、その時点の [T-2854] の前進先を brief へ戻して再裁定する (本 wave では F を採用し、採用根拠 = ref 実測と [T-2854] の insight §6)。
- **R11 成果物:** 一次資料に、commit の中身、CI・D297 (a)(b)・trace の結果と生出力の所在、棚卸し表と裁定、push 依頼、上流説明文の英語下書き (短く、上流 master b28f96b6 にも fuzz 0 で当たる事実を添える)。spool: worklog fragment ([T-2905]・[T-2885] 更新、gitlink 前進 wave の起票 = branch 名・SHA・棚卸しの所在・前提 (F への前進の着地・ユーザーの push・GitHub CI 緑)・D297 の扱いの定義が要ること)。
- **R12 変異:** repo の実装面の差分 0 のため変異 matrix は免除 (DW-S04)。修正の検出力は F 対照の D2b 赤 (R5) が担う。受入全走は記録 commit 後に行う。
- **R13 計算:** trace 1 job (約 5 分)、CI build + D297 (a)(b) 1 job (約 20 分)。合計 約 0.4 node 時間、2 node 時間の線の下。

## 段構成

段 5 author 1 本 → 段 6 read-only review 1 本 (過剰・削除レンズを含む 2 レンズを 1 本で) → fix → commit → 計算 2 job と棚卸し → 段 7 記録。
