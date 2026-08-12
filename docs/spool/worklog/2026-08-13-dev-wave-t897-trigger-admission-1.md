---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t897-trigger-admission
seq: 1
title: trigger 軸の semantic admission を build gateway で必須化した (コード + docs、branch worktree-dev-wave-t897-trigger-admission)
---

## 本文

- ユーザー裁定 (2026-08-12 第 6 束) の **(b)** を実装した。binding を省略する 5 経路が
  materialized predicate の exact 検査へ到達しないまま build へ進む穴を、gateway 側で閉じた。
  設計判断は {{D:trigger-axis-gate-validates-bytes}} と
  {{D:frozen-skeleton-identity-is-in-the-language}}。
- **段 3 レンズ A が第 1 位に推した案は、親が段 4 で実測して実装不能と判定した。**
  characterization と candidate を typed に分離するには生成器登録簿へ member を足す必要があるが、
  登録簿は受入方針 preimage に含まれ、方針ハッシュは全 admission receipt の field である。
  member 1 つで過去・現在の全 receipt の SHA が変わる。
- **hole の初期値は「33 番目の候補」ではなく骨格の単位元である。** 生成器の 32 述語は要因 8 種の
  うち 5 種と番兵しか覆わず、残り 2 種で全ビット立てと初期値の意味が食い違う。その 2 種が発火しない
  ことこそ characterization driver の測定対象なので、代替は循環になる。
- **段 6 で自前 C++ 字句解析を撤去した。** 敵対レビューが静的追跡で両方向の誤り (raw string と
  行継続で偽 block を受理し、かつ正当な source を過剰拒否) を実証した。実装は 158 行から 80 行になった。
  残存限界 3 件 (block のコメント化・block 外の再代入・ABA 窓) は裁定パッケージへ返す。
- fix 前の焦点走の赤 2 件は、`test_campaign.py` の fixture が凍結 template ではなく手書きの最小
  block を書いていたことが原因だった。**期待値を 1 文字も変えず fixture の入力を直して**解消した。
- 変異の事前登録 11 件のうち 3 件は実装形に anchor が無く、単独帰属が成立しなかった
  ({{F:mutation-preregistration-anchors-absent-in-implementation}})。10 件へ差し替えた。
  1 巡目は正例 control の期待 node 過少申告で MISMATCH
  ({{F:mutation-expected-nodes-underdeclared-again}})、erratum を残して 2 巡目で
  **10/10 KILLED・MISMATCH 0・SURVIVED 0・rc=0**。
- **段 3 レンズ A の初回投入は上流分類器に拒否され 1,047 秒と 38,330 output token を失った**
  ({{F:adversarial-prompt-shape-not-just-framing}})。防御目的の明記だけでは足りず、
  依頼の**形**を変える必要があった。
- 変異 harness の起動前検査で 3 回止めた (試行番号の対指定漏れ、変異走行に必須の失敗ノード出力
  option の欠落、1 巡目の試行記録の上書き防止)。**いずれも走行ゼロ・ツリー無変更**で、
  誤った条件の測定値を掴む事故には至っていない。
- 段 5・段 6 の実装子と fix 子は計算ノードへ投入できず pytest を 1 度も実走できなかった。
  両者とも「実装済み・未実走」と申告し緑を騙らなかった。**実測はすべて親が取った。**
- peer 2 セッションから main の恒久赤 (octopus merge 由来) の周知を受け、`git log --format='%h %p'`
  で親 4 つを自ら確認した。受入結果への反映は自分の走行で当該 node を実測してから行う。
- 逐語・裁定パッケージ (RP-1〜RP-5) = `output/insights/2026-08-13_t897-trigger-admission/`。

## 次の一手差分

### 完了

- [T-897] build gateway の trigger 軸 semantic admission を実装した。裁定 (b) のとおり、
  binding 省略 5 経路が exact 検査へ到達しないまま build へ進む穴を閉じた。
  変異 10/10 KILLED、焦点走 826 passed。残存限界と scope 外 real 所見は RP-1〜RP-5 で返す。
  remaining: none
  base: f4f38cc466b6f8a972c7d688aaab6066179d9bab4caeaa311d030d8ec01ea2d5

### 新規

- {{T:trigger-gate-block-outside-cpp}} **P2・新規・ユーザー裁定待ち (RP-2)**:
  trigger 軸 gate は block の bytes だけを検証し、block 外の C++ 意味論は検証しない。
  凍結領域を post-END の gate 呼出しまで拡大すれば block 外の再代入だけは閉じられる。
  親の推奨は拡大 (C++ 字句解析を必要としない)。
- {{T:s8b-binary-store-admission-binding}} **P2・新規・ユーザー裁定待ち (RP-4)**:
  S8b の content-addressed binary store が admission receipt を束縛しない。
  resume と oracle 実走前の検査は store の存在と SHA だけで、admission 未証明の既存 binary でも
  hash が一致すれば floor の測定値・manifest・oracle report に使われる。親の推奨は起票。
