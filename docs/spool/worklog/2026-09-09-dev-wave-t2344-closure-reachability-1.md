---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2344-closure-reachability
seq: 1
title: [T-2344] enforcement source closure の未収載 module を実測した — 到達は実在し、寄与は今の corpus では出ず、候補集合そのものから発行器が抜けていた (docs のみ、branch worktree-dev-wave-t2344-closure-reachability、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **D1513 が求めた実測を行い、裁定パッケージとして返した。収載の可否は本 wave では決めていない。**
  逐語と全成果物は `output/insights/2026-09-09_t2344-closure-reachability/`。
- **引数と carry の数字 3 つが現行と違っていた。** carry と D1513 は「第 1 層 62 path」「残り 69」
  「全 131」と書いているが、現行は 63 / 77 / 140 である。T-2429 (2026-09-08) が
  `verify_fanout_worker.py` を足していた。親が段 1 の前提実測で見つけ、brief に出して段 4 で扱った。
- **測定道具の正例対照を取った。** 閉包を数える probe は、`a94ba713b^` の 24 から 1 段展開して
  T-733 が着地させた 62 tuple と集合一致し (両方向の差集合が空)、同 commit の全展開も 131 / 69 で
  先行 insight と一致した。**順序は一致していない** — probe が sort して返すためで、
  段 3 のレンズ A が指摘した。「bit 単位で再現」とは書かず「集合と件数の一致」に直した。
- **親の測定の誤りを 2 件、自分で見つけて直した。** (1) `co_name` で判定していたため class 本体を
  関数実行に数えており、未収載の実行を 11 本と過大に出していた。`co_flags` で module 本体 /
  class 本体 / 関数を分けたところ 4 本になった。(2) 反実仮想で入口が例外終了した mutant を、
  判定 vector が変わったという理由で C+ に分類していた。判定面へ到達していないので CD が正しく、
  直すと C+ は 2 件から 0 件になった。
- **測定を 1 件撤回した。** 最初に書いた実行到達性 probe は profiler を対象の import より**後**に
  設置しており、import 時の実行を構造的に観測できないまま「未収載の実行 0 件」を出していた。
  段 3 のレンズ A が指摘し、import より前に trace を張る probe の結果へ置き換えた。
- **段 3 の 2 レンズは独立に別の欠陥を挙げ、どちらも real だった。** レンズ A は候補集合から
  発行器 (`s8b_oracle_report.py`、`s8b_abort_reason_contract.py`、`s8b_outcome_stage_contract.py`) が
  抜けていることを挙げ、親が裏取りして本 insight の主要結論に採用した。レンズ B は代償側が
  便益と同じ土俵に無いことを挙げ、epoch churn の名称限定・終端 commit・path 別内訳と、
  tuple 変更の一回限りの非互換の計測を足させた。
- **反実仮想の 0 件は非寄与の証明ではない。** 手元の 50 campaign はすべて拒否され (repository 内 30 は
  `E0 v1-authority-absent`、外部 20 は codec の exact key 集合不正)、受理へ抜ける深い経路が
  1 度も実行されない。この限定は insight の本文に明記した。
- 測定の定義 (到達性 3 層、寄与の 5 分類、入口が止まったら CD) は {{D:closure-reachability-measurement}}。
- 実装面の差分ゼロ。probe はすべて repository の外 (`dev-wave-jobs/` 配下) に置き、
  逐語だけを insight の `verbatim/` へ Markdown で収めた。
- 子は 3 本 (段 2 plan 1、段 3 consult 2)。いずれも rc=0、`check_codex_output.py` rc=0。

## 次の一手差分

### 更新

- [T-2344] **P2・ユーザー裁定待ち**: enforcement source closure をどこまで収載するか。
  D1513 が求めた実測は完了した (`output/insights/2026-09-09_t2344-closure-reachability/`)。
  未収載は 69 でなく 77、発見集合は 131 でなく 140、収載は 62 でなく 63 である。
  未収載のうち 8 本が認証受理 API か freeze / spec 検証経路で関数本体まで実行される一方、
  実行済み分岐を反転する反実仮想 10 か所では受理判定が変わった例は 0 件だった
  (ただし手元の 50 campaign はすべて拒否され、受理へ抜ける経路が実行されない)。
  候補集合が収載 tuple 起点で作られているため、認証成果物を発行する module 自身が集合の外にあり、
  140 へ広げても発行器は束縛されない。発行器起点を含めると候補は 165 (未収載 102) になる。
  選択肢は insight の裁定パッケージに 6 案を並べた。
  成果物影響 = 決めない限り「certified 経路が source-bound」を推移閉包の意味では名乗れない。
  base: 06624088489aa10ca4c6fb3e54408e06e4a5762c7a8151667ba6b97475b1b5a7

### 新規

- {{T:closure-scope-wording}} **P2・新規**: 成果物へ出る保証の文言を実態へ合わせるか。
  `orchestrator/campaign/artifact_admission.py` の `CAMPAIGN_VERIFIER_EPOCH_SCOPE` は
  「curated exact 62 path」「発見集合 131」、`CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` は
  「未収載 69 module」と書いたままで、現行の 63 / 140 / 77 と食い違う。
  この 2 定数は `orchestrator/campaign/s8b_oracle_report.py` が oracle report の
  `identity_scope` / `excluded_scope` へ書き出す。束縛そのもの (exact-63 の key 集合検査) は
  正しく効いているので受理集合は現状のまま正しく、誤っているのは説明文だけである。
  [T-2344] の裁定内容によって書くべき値が変わるので、単独で直すか裁定後に直すかを決める。
  成果物影響 = 材料レポートが、実際に束縛している集合と違う集合を名乗り続ける。
- {{T:exact62-lock-grammar}} **P2・新規**: exact-62 の campaign lock を読む経路を用意するか。
  記録済み lock 48 本を実 decoder 2 本に通したところ、exact-24 の 13 本は歴史 decoder で読めるが、
  **exact-62 の 3 本はどちらの decoder からも読めない**。T-733 が 62 へ広げたときは pre-T733 の
  24 用に歴史 grammar を用意したが、T-2429 が 63 へ広げたときに 62 用が用意されなかった。
  実体は paper-story A-2 の t2364 系列 (rr5・rr50、2026-09-07 記録) と A-6 系列 (rr95、2026-09-08 記録)。
  現時点でこの 3 本を読む consumer は無く (A-2 の図の生成器を実際に走らせて確認した)、影響は潜在である。
  成果物影響 = この 3 本を読む必要が生じた時点で、認証経路と歴史閲覧経路の両方から読めない。
