---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: t2851-unseen-transfer-runner
seq: 1
title: [T-2851] の残り (2) 未知条件への転移の実行器と解析器を実装した — 26 cell / TPC-C 段別 12 cell の展開、§5 の順序、候補凍結と M、cohort 2 の別日・hostname・再投入、検証 3 値、§9 の欠測と n_eff、§6 の同時区間と分類。計算ノードの錨の生死確認で検証が certified に届かない欠陥を見つけて直した (コード + test + insight、branch worktree-t2851-unseen-transfer-runner)
---

## 本文

- 依頼 (ユーザー、2026-09-23): 事前登録 v1 §11 の欠ける部品と TPC-C 版 §5 の置換を新しい module に実装する。pipeline.py と calibrator/runner.py は呼ぶだけ、
  MOCC の参照・対象探索群・候補凍結は入力として受け取り選定を先取りしない、留保条件で生成・選択を動かさない、発効前なので計算ノードで留保 cell を実行しない、
  test は fixture と学習条件側の最小走、規律 2 を緩めない、仮想リスク向けの gate・検査・台帳・一般化は scope 外。途中で中断があり、2026-09-26 にユーザーの「続けて」で再開した。
- 実装: `orchestrator/campaign/t2851_transfer_runner.py` と `t2851_transfer_analysis.py`、test 2 本。設計判断は {{D:t2851-transfer-runner-contract}}、記録は
  `output/insights/2026-09-26/t2851-transfer-runner/README.md` (段の経過、実装上の選択、生死確認の実測、裁定の逐語)。
- 段 6: review 2 本は両 NO-GO (単位 A/B の JSON 契約の不一致、M の系列重複、参照どうしの比較の欠落ほか)。fix 3 巡・焦点再レビュー 3 巡 (NO-GO → GO → GO)。
  不採用: binary 内容 sha256 照合の削除 (v1 §5 の同一 build の束縛)、walltime と verifier 全量の削除、TPC-C の認定経路への接続 (裁定時点で未着地)。
- 計算ノード (Pegasus gen_S、generic dispatch) で錨 wh-base だけの生死確認を 4 回 (job Elapse 計 719 秒)。1・2 回目は使い捨て driver の build 経路と repo root の誤りで失敗、
  3 回目は job 成立 (32 block・使えない走 0・単独性の両端成立) だが **検証が indeterminate** — `verify_trace_dir` に `ccbench_root` を渡さず証明面が unavailable で、
  YCSB は certified に到達できなかった。review・焦点・fixture test はいずれも検出せず (F649 の再発として failures へ追記。親が実装子 prompt で verifier の fixture 化を許していた)。
  fix 3 巡目の後の 4 回目は certified。留保 cell は 1 走もしていない。
- 変異 matrix: M1〜M13 (M13 は fix 3 巡目の前に追加登録)。結果は insight §4。
- 中断中の並走: 同じ引数の重複 wave (2026-09-23 22:03 投入) は先方が譲って停止 (成果物 0)。T-2858 の CCBench pin 前進 (68106660) は受入前の main 取り込みで入れ、新 module は pin を参照しない。

## 次の一手差分

### 更新

- [T-2851] **P1 (VLDB 差分分析 P4: 未知条件への転移と再現)**: 事前登録 v1 `docs/unseen-condition-transfer-preregistration.md` (YCSB) と、TPC-C 版
  `docs/tpcc-unseen-condition-transfer-preregistration.md` (段 1・段 2 の錨と留保 20 条件、D2228) を作り、どちらも留保の効力は着地時点で生じる
  (D2223)。TPC-C の探索群の学習条件は同書 §2.1 の段ごとの錨 2 点の部分集合にし (外れるなら生成の開始前に別の登録が要る)、TPC-C の留保条件の値・結果・
  それから作った指示や設定を生成器・選択へ入れず、段 1 の留保の情報を段 2 へ渡さない。実行器と解析器 (`orchestrator/campaign/t2851_transfer_runner.py`・
  `t2851_transfer_analysis.py`、{{D:t2851-transfer-runner-contract}}) は着地済み。残りは 2 つ。(1) 測定の発効: YCSB は対象探索群 ([T-2850] の選択結果) の名指し、
  全手法・全独立探索の候補凍結記録 (実行器の凍結入力の形)、MOCC の扱いの 3 択、発効束 (v1 §13.1) の実値 (実装上の選択 = block 1..32・環境値・trace の CCBench source root の確認を含む) を揃え、
  凍結した候補数で費用を見積もり直してユーザーの計算確認を取り、決定に記録する (v1 §12 の試算は 1 cohort の性能だけで約 9.5〜616 node 時間、検証は約 19〜64 node 時間、
  cohort は 2 つ。D2212 項 4)。TPC-C は段ごとに別の発効で、段の認定経路の存在と実行器への接続 ({{T:t2851-tpcc-verify-wiring}})、強い参照の 3 択 (固定できなければ記述専用)、
  ロード時間の実測単価での見積りが加わる (TPC-C 版 §3.3・§4・§8・§9.1)。(2) 性能 2 cohort と検証の実施。前提 = [T-2850] の選択結果と TPC-C の探索の結果。
  一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P4、記録 `output/insights/2026-09-22/t2851-transfer-prereg/README.md`、
  `output/insights/2026-09-23/t2851-tpcc-transfer-prereg/README.md`、`output/insights/2026-09-26/t2851-transfer-runner/README.md`。
  base: b4ee96d7c9a2a8f11173eb5d29850175e7b90d15969b5fe7069ea8c1f8648a5b

### 新規

- {{T:t2851-tpcc-verify-wiring}} **P2 ([T-2851] の TPC-C 側の前提)**: 実行器の TPC-C 検証は現在常に indeterminate (認定経路なし) を記録する。段 1 の認定経路
  (2026-09-26 時点の main で `pipeline._run_trace` が 57:43 の trace を許す) を発効時に固定し、実行器の verify へ接続する。TPC-C の build 経路 (buildcache は YCSB target 固定) と
  TPC-C 用の単独性確認の実機確認も同じ単位。発効の前に、錨の cell だけで生死確認する (留保 cell は発効まで走らせない)。記録 `output/insights/2026-09-26/t2851-transfer-runner/README.md` §2・§5。
