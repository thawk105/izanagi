---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2650-masstree-config-h
seq: 1
title: [T-2650] 床値 campaign の condition gate へ prebuild 済み masstree を供給し、実 compiler の正例・負例で裏を取った (コード + テスト、branch worktree-dev-wave-t2650-masstree-config-h、変異 matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- official 床値 campaign が 3 走行とも止まっていた原因は `BACKOFF_FIXED` の供給失敗ではなく、
  **Masstree の autoconf 生成 header `config.h` が condition gate の前処理時点で存在しないこと**
  だった。gate は使い捨て build dir へ configure を掛けるだけで build しないため、
  build 時生成物である `config.h` に当たらない。床値 campaign は masstree の prebuild を
  既に持っていたが、その入力を gate の configure へ渡していなかった。設計判断は
  {{D:floor-gate-offline-supply}}。
- **同型の欠陥は段 4 loop 経路で解決済みで、生成器と pin test が既にあった。** D1495 が
  「job script 側で解けたが condition gate の supply arm は preprocess で止まったまま」と
  記録していた残余が、床値経路にだけ残っていた。新しい共通層は作らず再利用した。
- **段 3 の敵対 2 レンズが親 brief の前提 (P1-d)「生死確認は既存実測を継承する」を refuted した。**
  配線の argv 一致 test は `config.h` が実際に読めることを何も証明しない。裁定で完了判定を
  改め、実 compiler・実 CMake の正例・負例を必須にした。判断は
  {{D:floor-gate-supply-liveness-control}}。gflags/glog を要さない既存 fixture で足りた。
- 段 6 のレビューが**負例の単一理由性の弱さ**を指摘した。当初の負例は reason code と detail の
  `"config.h"` 部分一致しか見ておらず、原因を特定できていなかった。同じ
  `capture_define_inputs` の結果を再利用して **configure 引数を 1 bit も変えずに** header だけを
  置き直すと green へ戻る対照を足して閉じた。
- **段 3 のレンズ A が親自身の一般化を反証した。** 親は現行 worktree の cell 構成
  (12 cell、うち `sort_best` 2 件) から「過去 3 走行でも prebuild は走った」と一般化していた。
  走行時 commit `c185b9fd4` と現行 main で freeze 2 file の diff がゼロ、判定条件行も同一である
  ことを実測して閉じた。ただし prebuild 完走の直接の受領証は job 終了で消えており未照合である。
- **不採用にした所見**: `prepare_kwargs.get("dependency_prefix", "")` を固定値へ明記する案
  (レビュー B、低)。成果物影響が無く、将来 prefix が実在したとき黙って落とす向きの危険と
  引き換えになるため scope 外とした。
- **エージェント工数**: 段 5 実装子は `max_model_calls` 上限 (200 call) で、段 6 fix 子は
  wall clock 上限 (3600 秒、130 call) で、いずれも**報告を書けずに SIGTERM で落ちた**
  (`f45_missing_output`)。編集自体は両方とも完了しており、親が現物を検収して受理した。
  fix 子の wall 超過は、親が 15692 行の test file の全走を 2 本要求したのが直接の原因である。
- **到達範囲**: official 床値 campaign が実機で cell build 段を越えたことは**本 wave では
  確認していない**。実機再投入を要する別タスクであり、本 wave の緑を実機通過と読み替えない。
  判定規則・reason code の定義・sort 限定の build 注入は変えていないが、依存欠落による
  **検査不能**を解消したので「受理結果まで不変」ではない。

## 次の一手差分

### 完了

- [T-2650] 供給の配線と実 compiler の正例・負例を着地させた。official 床値の実機再投入は
  {{T:floor-official-rerun-after-supply-fix}} へ分けた。
  remaining: none
  base: 9e49716cfc9304bfe92c345a64ac6f9e304a8ceee739d80f434ced9be006f971

### 新規

- {{T:floor-official-rerun-after-supply-fix}} **P1・新規**: 本 wave の供給修正を載せた main で
  official 床値 campaign を再投入し、cell build 段を越えるかを実機で確かめる。越えたら
  試行台帳側 gate の実値域を取得する。越えなければ、止まった段と reason code を
  `output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §4 と同じ粒度で記録する。
- {{T:floor-nonsort-campaign-config-h-gap}} **P2・新規**: 非 sort 単独の床値 campaign には
  同じ `config.h` 欠落が残る。prebuild も dependency binding も作られないためである
  (段 6 のレンズ B が行番号で確定)。prebuild の発火条件を広げるか、gate 側で別経路を持つかは
  未裁定なので、択一を立てて諮る。
