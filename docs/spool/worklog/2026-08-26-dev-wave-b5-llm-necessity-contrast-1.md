---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-b5-llm-necessity-contrast
seq: 1
title: B-5 の 3 アーム同一予算対照を設計し、走らせられない理由を実コード水準で確定した (docs、branch worktree-dev-wave-b5-llm-necessity-contrast、実装面差分ゼロにつき変異 matrix 免除)
---

## 本文

- ユーザー依頼は「B-5 の対照を設計し実走する」。依頼自身が
  「予算単位・停止条件・実行入口が repo に実在するかを段 1 で実測し、無ければ設計と
  事前登録までを成果物にして実走は次段へ送る」という gate を含んでいた。**この gate が発火した。**
- **段 1 実測。** 予算単位は評価回数 (`generation_budget_per_workload`) と bench 実時間
  (`8b-budget-ledger/v2`) が個別機構としては実在するが、3 アーム共通の consumer は無い。
  **停止条件は報告 literal であって強制される gate ではない** — 実 driver は `p3_s4_loop` を
  継承し `converged` / `reverse-exhausted` で止まる。実行入口はランダム変異アームが不在、
  Tier0・3 アーム共通 driver・共通予算台帳・report/統計 consumer も不在。
  LLM 側入口は承認世代数の上限が対照設計の予算より小さく、軸もハードコードされている。
- **走らせられる適格軸がゼロ**であることを確定した。backoff は軸適格性違反、sort は D46 で
  地形なし、trigger-gating は D52 の (c') 事前自認、データ構造水準の軸は 2026-07-28 に
  択 (c) で廃止済み。D52 の休眠解除条件は第 1 項 (非列挙のコード片軸の実体化) の時点で未充足。
  さらに `docs/phase3.md` は、この対照の設計タスク自体が旧 headline を復活させない限り
  休眠だと定めている。
- **段 3 の敵対相談 2 本が独立に同一の核心へ到達した。** ランダム変異を有限の型付き変異契約に
  閉じ LLM を閉じないと「広い空間 vs 有限の部分空間」の比較になり、LLM も閉じると
  完全列挙器が構成できて非列挙条件と衝突する。実装を足しても消えない識別上の三すくみであり、
  この設計が示せるのは「凍結した 2 つの非 LLM 生成器より高い score だった」までで、
  「LLM でなければ到達できない」という必要性ではない。
- 所見は計 17 件で **refuted ゼロ**。親は全件 real と裁定し、実装しない
  (`4→7→8→9`) と決めた。設計を正本化しない境界は {{D:b5-contrast-design-stays-non-binding}}。
- **親の段 1 実測の訂正 5 件を成果物に残した** (消していない) — 停止条件を「実在」と書いたのは
  不正確、データ構造軸を「差し戻し中で裁定待ち」と書いたのは古い正本の読み落とし、
  sweep 棚卸しの取りこぼし、既存予算機構の B-5 互換性の過大一般化、
  「全件検索 0 件」を方法を限定せずに書いたこと。
- **費用の桁を出した。** 3 アーム × 3 workload × 12 系列 × 10 slot を仮定すると
  trace-disabled bench だけで約 12 時間、verifier 側は既存校正値からの外挿で 76〜234 時間、
  直列 wall で 10² 時間級。レコード数自体は規律 4 違反ではなく、系列数・floor・verify の
  乗算が効いている。
- 成果物は非拘束の設計メモ 1 本と逐語一次資料 3 本。実装面の差分はゼロ。

## 次の一手差分

### 新規

- {{T:b5-claim-scope-ruling}} **P1・ユーザー裁定待ち**: B-5 の主張範囲を決める。
  「必要性」のまま残すか、「凍結対照に対する条件付き優越」へ狭めるか、
  D52 の系レベル設計へ戻すか。狭める場合は論文素材 §8 の B-5 欄の文言も変わる。
  根拠 = `output/insights/2026-08-26_b5-llm-necessity-contrast-design.md` §5・§9。
- {{T:b5-eligible-axis-onboarding}} **P2・新規**: B-5 を走らせる前提である
  「非列挙のコード片軸」を 1 本実体化する。現存軸はすべて不適格であり、
  軸オンボーディングが対照実装より先に来る。
- {{T:b5-contrast-runtime}} **P3・新規**: ランダム変異生成器、Tier0、3 アーム共通 driver、
  共通予算台帳、report / 統計 consumer を実装する。中〜大規模。
  {{T:b5-eligible-axis-onboarding}} と {{T:b5-claim-scope-ruling}} の後段。
