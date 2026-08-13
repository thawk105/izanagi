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
- **受入 1 回目 (tip `6d08a26b`): 1 failed / 10545 passed / 65 skipped (128.34 秒、request 908872.nqsv)。**
  赤は `test_p3_autonomous_workload_trial.py::test_origin_public_result_distinguishes_partial_from_completed`
  1 件で、**本 wave の差分に帰属しない**。根拠は 3 つ — (i) 単独再走は `1 passed` (3.19 秒)、
  (ii) 例外は `reflux_formal_consumer.py` の process 全体で共有される replay cache が投げる
  `FormalReceiptError` で、本 wave は同 module を 1 行も触っていない、
  (iii) 同 module は数時間前に main へ着地した別 wave の新規実装である。
  peer 2 セッションが周知した octopus merge 由来の恒久赤は**出なかった** (main の前進で解消)。
- **main 取り込み merge が provenance 監査で新規違反 1 件になった。** 実装面で両側が触ったのは
  `test_campaign.py` の 1 file だけで、3 方向結合の結果が両親のどちらとも異なるため checker が
  実装面著作と判定した。`git diff-tree --cc` は実質空で結合による新規著作はない。
  **ユーザー裁定 (2026-08-13) により既知違反として登録した** (同型の 8 件目)。
  waiver ではなく登録を選んだのは、`AI-Agent-Waiver` が「Codex 不可用時」の免除であり、
  本件は「merge に実装を書いた主体が存在しない」という別事象だからである。
  登録後の監査は rc=0 / known-violations=39 / 新規違反なし。
- **受入を 3 回実測した。** 1 回目 (tip `6d08a26b`) 1 failed / 10545 passed / 65 skipped、
  2 回目 (`0a438137`) 4 failed / 10542 passed / 65 skipped、
  3 回目 (`3bfd0adc`、request 908886.nqsv) 1 failed / 10545 passed / 65 skipped (111.30 秒)。
  **本記録を足した tip では land 直前にもう一度走らせる** (land は tested tip と wave HEAD の
  完全一致を要求するため。`dev_wave_land.py` の `wave_head != tested_tip` 検査)。
  **本 wave に帰属した赤は 2 回目の 1 件だけで、修正済みである** — 既知違反登録に対し
  台帳 literal を二重に持つメタテスト 2 本が追随していなかった。
  親が名指ししたのは 1 本で、2 本目は実装子が自ら洗い出した。焦点走 283 passed / rc=0。
- **`test_codex_worker_launch.py` は全走の並列負荷下でのみ落ちるフレーク族である。**
  3 回の受入で落ちた node は毎回異なり (1 回目 0 件、2 回目 3 件、3 回目 1 件)、
  いずれも単独再走で緑 (実測: 2 回目分 9 passed / 3.26 秒、3 回目分 1 passed / 3.10 秒)。
  失敗述語も `metering_status` 系と `process_group_residual` / `termination_verified` 系で
  回ごとに異なる。本 wave は同 file を 1 行も触っていない。
  1 回目の `test_p3_autonomous_workload_trial.py` の赤も 2・3 回目では再現しなかった。
- 受入を 3 回要したのは、(i) main 取り込み merge の provenance 裁定が 1 回目の後に確定したこと、
  (ii) 親が fix 子へ「監査ツール本体を走らせよ」とだけ指示し、**そのツールの test file を
  指定しなかった**ことによる。二重管理された台帳では本体が緑でもメタテストが赤くなる。
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
- {{T:formal-consumer-replay-cache-leak}} **P2・新規**: `reflux_formal_consumer.py` の
  `_OPERATION_REPLAY_CACHE` は module 変数で process 全体に残り、並列受入全走で同じ
  `operation_id` が別 payload と再利用されると `FormalReceiptError` を投げる。
  `test_p3_autonomous_workload_trial.py::test_origin_public_result_distinguishes_partial_from_completed`
  が全走でのみ赤くなり単独では緑になる (実測)。test 間で cache を隔離するか、
  fixture で明示的に初期化する必要がある。
- {{T:s8b-binary-store-admission-binding}} **P2・新規・ユーザー裁定待ち (RP-4)**:
  S8b の content-addressed binary store が admission receipt を束縛しない。
  resume と oracle 実走前の検査は store の存在と SHA だけで、admission 未証明の既存 binary でも
  hash が一致すれば floor の測定値・manifest・oracle report に使われる。親の推奨は起票。
