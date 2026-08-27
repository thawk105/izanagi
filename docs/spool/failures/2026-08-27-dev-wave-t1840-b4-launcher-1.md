---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1840-b4-launcher
seq: 1
---

## 新規

### {{F:b4-lock-snapshot-and-mutation-oracle}}. certified sink の lock 二重読取と message 差変異が「迂回不能」を偽っていた [TOCTOU] [恒真ゲート]

- 事象: Codex resume の独立 focus が、分類時 markerless / 検証時 marked へ lock を差し替えると G4 未実行の
  COMMIT を受理できること、campaign id が decoded lock でなく directory basename 由来であること、M08〜M10
  が副作用でなく inner G2 の message 差で KILLED していることを現行 bytes から示した。
- 根本原因: 分類と receipt hash が同じ path を別々に読み、campaign 束縛と変異 oracle も「同じ意味の
  1 観測」へ閉じていなかった。
- 恒久対応: 同一 raw lock snapshot、decoded canonical campaign id、明示 absence digest を使う。M08〜M10 は
  副作用 assertion を message より先に評価する。markerless / lockless の正例も同時に固定する。
- 再発検知: gate が file を読む回数を数え、分類値と receipt hash の入力 bytes が同一 object かを見る。
  変異は最初に落ちる assertion が登録した意味かを確認し、message 差だけなら kill に数えない。

### {{F:author-report-working-bytes-mismatch}}. author 報告の WAL fix が working bytes に残っていなかった [手順漏れ] [記録不整合]

- 事象: 2 巡目 author は absence sentinel の import と分岐を変更したと報告したが、親が `rg` と `git diff` で
  再読すると import 無し・`else None` のままだった。validator receipt と成果物は accepted だった。
- 根本原因: Codex output validator と receipt は最終メッセージの構造・来歴を検査するが、報告した各
  anchor が working bytes に実在することまでは検査しない。親も採用前の literal 照合を初回は省いた。
- 恒久対応: author の結論を採用する前に報告した exact anchor を working bytes と diff の双方で再読する。
  本件は 3 巡目を WAL 1 file / 2 anchor に限定して閉じた。
- 再発検知: 報告の file:line と `git diff --name-only` / literal hit の積を親が照合し、片方でも欠ければ未実装。

### {{F:contract-loader-mutation-self-poison}}. enforcement closure file の working-tree 変異が広い runner を一様に汚染した [恒真ゲート] [手順漏れ]

- 事象: resume 初回 M19〜M21 は狙った node に加え最大 124 node が落ちた。`wal.py` /
  `commit_receipt.py` は contract-loader の HEAD blob 束縛 24 path に含まれ、working bytes を変えた時点で
  runner の多くが drift 拒否した。gate の検出力ではない。
- 根本原因: 変異対象と `CONTRACT_LOADER_RELATIVE_PATHS` の交差を事前登録時に確認せず、closure bytes の
  同一性を要求する broad consumer と working-tree mutation を同じ runner に入れた。
- 恒久対応: 元 M01〜M18 は broad runner、closure file を触る supplemental M19〜M21 は対象 3 node だけの
  runner に分ける。初回 21 件は erratum として残し、期待集合へ drift node を追加しない。
- 再発検知: 変異対象を `CONTRACT_LOADER_RELATIVE_PATHS` と交差し、hit があれば broad runner を使わない。

### {{F:non-b4-lock-misclassified-as-malformed}}. valid non-B4 lock を分類不能として全 COMMIT を拒否した [過剰拒否] [テスト代表性]

- 事象: pre-record 全走で s8b oracle driver 20 件が `unknown-abort-reason` / `error` へ倒れた。fake evaluate
  を instrument すると、正規 codec を通った non-B4 lock の identity に `search_config` が無いことを
  B4 classifier が `existing campaign lock cannot classify` と拒否していた。
- 根本原因: 「marker 付き lock の必要 field 欠落は fail-closed」と「valid non-B4 schema は B-4 field を
  持たない」を区別せず、`_b4_classification_fields` を marker 有無の判定前に要求した。
- 恒久対応: exact dict identity で key 自体が無ければ非 B-4、key が存在して非 dict なら拒否と分けた。
  valid non-B4 lock + matching receipt の正例、非 mapping 3 値と malformed decoded / identity の負例を追加。
- 再発検知: conditional protocol marker の classifier は、marker 不在の各 valid sibling schema を正例に含める。

### {{F:clean-tree-assert-poisons-mutation}}. 作業ツリーの clean を assert する検査が全変異の観測を一様に汚染した [恒真ゲート] [手順漏れ]

- 事象: 変異 matrix 18 件が**全件 MISMATCH** で戻った。増えた失敗 node はどの変異でも同一の 1 件
  `orchestrator/tests/test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`
  だった。baseline は PASSED (赤 0 件) で、変異の注入も anchor も正しい。
  同検査は「作業ツリーの非 output 変更が自 file 2 件だけであること」を assert する。
  一次資料は `output/insights/2026-08-27_t1840-b4-launcher-chokepoint/mutation-ledger-merged-contaminated.json`。
- 根本原因: **変異 harness は固定 HEAD へ tracked file を一時的に注入する。**
  作業ツリーの clean を assert する検査を runner の対象へ入れると、**何を変異させても必ず落ちる。**
  期待 node の完全集合に一様な 1 件が混ざるため、全件 MISMATCH になる。
  さらに悪いことに、**気づかず期待値へ足すと「関門と無関係な赤」を kill の証拠に数えてしまう** —
  `DW-M03` が禁じる「診断文字列だけの赤を kill にしない」に正面から抵触する。
  この検査は本 wave の基点より後に main へ着地したため、着手時点の runner 対象選定では見えなかった。
- 恒久対応: 変異 runner の対象 file 集合から当該検査を外す。**期待値へ足して一致させない。**
  除外の理由と、除外前の観測 (全件 MISMATCH、増えた node が一様に同一) を runner script と
  変異台帳へ逐語で残す。受入全走では外さない (clean な木で走るため発火しない)。
  `DW-M03` の「診断文字列だけの赤を kill にしない」がこの型の判定規則である。
- 再発検知: 変異が**全件 MISMATCH** で、かつ増えた node が**どの変異でも同一**なら、
  変異の失敗ではなく runner 対象の汚染を疑う。増えた node が作業ツリーの状態を assert する
  検査かどうかを最初に見る。

## 再発

### F662

- **再発: 2026-08-28** — pre-record 全走で s1 / s8b の official output root が一括 red 化した。
  `/tmp/.git` は空 directory・無効 repository と確認でき、既定手順の `rmdir` 後に s1 24 passed。
  計算ノードの node-local `/tmp` には login sweeper が届かないため、repo 外の明示 TMPDIR を runner へ渡し、
  s8b 127 passed / 6 skipped、最終全走 18,240 passed / 61 skipped を得た。production gate は緩めていない。

### F644

- **再発: 2026-08-27** — 段 3 の `--lane luna` 側が同型で拒否された。受領証の失敗分類は
  `f45_missing_output`、rollout 終端の `codex_error_info` は `cyber_policy`、
  文面は `This content was flagged for possible cybersecurity risk`。
  31 model call と 22,266 output token を消費して成果物ゼロである。
  発火した文面は「支配点を通さずに標本を作る具体的な呼び方を、関数名と引数の形まで書け」で、
  **恒久対応の 3 点のうち (a) 攻撃→点検は満たしていたが、(b) の「具体的な手順を書かせない」に
  相当する部分を満たしていなかった** — 到達経路の列挙を求めるところまでは通るが、
  実行できる形の呼び方を要求すると拒否される。
  書き直した 2 回目は「公開 API の呼び出し起点から到達する経路を file:line で示せ。
  コードの書き換え案や実行可能な断片は不要である」とし、通過して must-fix 3 件を返した。
  再発検知の手順 (成果物ゼロなら rc を分類する前に終端本文を読む) は機能した。
