結論は **NO-GO**。段 2 プランは checker 一般化で scope を広げすぎる一方、現在の `main` 前進、2 個目の `T-179`、worklog `(79)` 衝突を見落としている。

## 攻撃対象 1 — 親 brief の実測値と一般化

### 1. `5 passed`

**仮判定: real / scope 内 / nit**

request `875777.nqsv` が保証するのは、merge 前の `c34f35e` 上で新テストファイルの 5 node が通ったことだけである。内容も主要 trial test は `_fake_drive()` と `_fake_preview()` を注入しているため、実 `_preview()`、`drive_iteration()`、build、legacy+S2、bench を通していない。[test_p3_autonomous_workload_trial.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:22) [同:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_p3_autonomous_workload_trial.py:64)

保証しないものは以下。

- merge 後 tree
- full suite、plain-runner meta-test、既存 consumer test
- 実 Claude process
- 実 preview→auditor→drive の結線
- build / verifier / bench / formal oracle
- docs、provenance、現行 `main` との統合

段 1 の focused precondition としてなら正しい。merge 受入へ一般化する読みは refuted。

### 2. `check_docs.py` が 5 ファイル込みで緑

**仮判定: real（その snapshot）/ scope 内 / nit**

現在の staged 5 ファイルで再実行し、`check_docs rc=0` を確認した。ただし対象範囲は非対称である。

- 新 insight は `output/insights/*.md` の placeholder 走査へ入る。[check_docs.py:857](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:857)
- 新 runbook は `phase3-s*-runbook.md` に一致せず living-doc lint の外。[check_docs.py:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:63)
- insight 内の誤った `D99` / `T-179` の意味は checker 対象外。
- `decisions.md`、`phase3.md`、`worklog.md` の merge 後変更は未測定。

新 runbook をメモリ上で `LIVING_DOCS` に加えた静的 probe も `rc=0` だった。したがって、現状の runbook に隠れた lint 違反はない。親の表現は「staged 5 ファイルだけの snapshot」と限定すべきで、merge 後 docs の緑を含意しない。

### 3. 「既存 tracked ファイルの振る舞いを変えない」

**仮判定: real（過大表現）/ scope 内 / must-fix**

既存ファイルの bytes を編集しないことと、既存 consumer の挙動が変わらないことは別である。basename grep が取りこぼす実 consumer がある。

- holdout freeze は basename でなく、全 tracked／untracked 通常ファイルを列挙する。[s8b_holdout_freeze.py:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/s8b_holdout_freeze.py:94) [同:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/s8b_holdout_freeze.py:197)
- plain-runner meta-test は `orchestrator/tests/test_*.py` 全体と README allowlist を走査する。[test_plain_runner_coverage.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/tests/test_plain_runner_coverage.py:44)
- RuleOps inventory は HEAD 上の新 test と insight を自動編入する。[ruleops.md:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/ruleops.md:21)

holdout scan の静的実測は次のとおり。

- 5 ファイル込み: `file_count=4416`, `skew=166`, `rmw=111`
- 5 ファイル除外: `file_count=4411`, `skew=165`, `rmw=110`
- `rr80` / `rr20` conjunction hit は双方 0

したがって frozen bytes と holdout の受理結果は不変だが、再計算 report 値と RuleOps inventory は変わる。正しい不変条件は「既存 tracked bytes と certified acceptance は不変。動的 inventory／scan の対象集合は意図どおり増える」である。

**DW-G05:** 放置すると、holdout search report の `file_count`・軸 count と RuleOps 台帳項目が実際には変わるのに、受入記録がそれらを不変値として主張する。

### 4. DW-O09 pin 閉包

**仮判定: real（探索方法の不足）/ scope 内 / nit**

`git grep -l <basename> main -- '*.py' '*.json'` が証明するのは直接 literal 参照 0 件だけ。glob、directory scan、HEAD inventory、README allowlist を原理的に拾わない。

実際には上記 4 系統の間接 consumer がある。ただし追加調査では、

- holdout conjunction hit 0
- 新 test は実 `__main__` harness を持つため allowlist 変更不要
- staged 5 の `check_docs rc=0`
- RuleOps は固定 pin でなく動的 inventory

だった。よって「既存 byte pin 0」は結果として維持できるが、親の grep だけでは閉包を証明していない。具体的成果物影響は残らないため nit。

### 5. 「既存 pipeline が唯一の経路、再実装なし」

**仮判定: real / scope 内 / must-fix**

限定すれば半分だけ正しい。

- `_preview()` は quarantine と禁止識別子検査を独自に実行する。[p3_autonomous_workload_trial.py:453](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:453)
- その結果が auditor を呼ぶか否かを決める。[同:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:729)
- その後は全 proposal が `drive_iteration()` へ入り、authoritative path が quarantine、syntax、digest、auditor を再検査する。[同:783](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:783) [p3_s4_loop_trigger_gating.py:276](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_s4_loop_trigger_gating.py:276)

したがって「build/certification の唯一の authoritative path」「受理集合を広げない」は正しい。「再実装なし」「supervisor の全 gate が既存 pipeline だけ」は誤りで、drift 時には余分に reject し得る。formal oracle は通過するのではなく、この探索 path がその受理集合へ参加しない。

さらに、取り込む D106 本文予定の branch D99 `docs/decisions.md:4393-4394` 自身が「迂回・再実装しない」と断言している。heading の再採番だけでは偽記録を main へ入れる。取り込み時補正を追記すべきである。

**DW-G05:** 補正しないと、terminal report／設計台帳が「既存 pipeline と同一の gate 集合」を参照する一方、実体は独立 pre-audit を含み、report の受理経路参照が実装と食い違う。

## 攻撃対象 2 — scope 拡大の判定

### 1. `check_docs.py` の glob 一般化

**仮判定: real（coverage gap）/ scope 外 / nit**

本 wave へ入れてはならない。

- 現 runbook を lint 対象へ仮追加しても `rc=0`。現在の成果物欠陥を直さない。
- `phase3-s*` → `phase3-*` は checker の受理集合を変える。
- D96 は新しい D と境界テストの同時更新を要求する。[decisions.md:4269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/decisions.md:4269)
- D97 はこの義務が開発 harness にも適用される実例である。[decisions.md:4298](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/decisions.md:4298)
- 段 2 は checker test だけを提案し、新しい D を欠いている。
- s8a の過去事例と今回の 8c は同じ docs producer／checker consumer であり、DW-G03 の「異なる producer/consumer で独立 2 件」を満たさない。[core.md:52](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/dev-wave/core.md:52)

書かなかった場合に変わる certified 選択・report・台帳の現行値を示せない。採用したいなら「8c 一件を明示追加するか、全 phase3 runbook へ一般化するか」を新 D＋境界 test 付き裁定パッケージへ返すべきで、本 wave の必須変更ではない。

### 2. `docs/README.md` の地図

**仮判定: real / scope 外 / nit**

地図は 8c を列挙しないが、merge 後の `phase3.md` と D106 から runbook へ直接辿れる。現行 report／台帳の参照は切れない。DW-G05 の一行を書けないため nit。

### 3. `output/README.md` の `autonomous-trials/`

**仮判定: real / scope 内 / must-fix**

これは単なる美観ではない。既定 producer は明示的に `output/autonomous-trials/<trial-id>` を作り、attempt journal、raw envelope、proposal、terminal report を置く。[p3_autonomous_workload_trial.py:1023](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/orchestrator/campaign/p3_autonomous_workload_trial.py:1023) runbook も正式 campaign proof chain との区別を要求している。[runbook:104](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/phase3-8c-autonomous-trial-runbook.md:104)

**DW-G05:** 追加しないと、attempt 台帳／terminal report の既定参照先が成果物地図に存在せず、`output/campaigns/` の正式 proof chain か exploratory journal かを正本から分類できない。

### 4. worklog rotation

**仮判定: refuted / scope 外 / nit**

数値は次のとおり。

- cwd の stale worktree: `95,116 bytes`
- 上限: `100,000 bytes`、違反条件は厳密に `>`。[check_docs.py:89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:89) [同:2155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:2155)
- 空き: `4,884 bytes`
- entry (78) の「次の一手」本文: `8,501 bytes`、top-level ID は 133 件

したがって 8,501 bytes を verbatim carry すれば、少なくとも `103,617 bytes` となり確実に超える。しかし checker は説明全文のコピーを要求せず、ID を compact に sink できるため、entry 完成前に「必ず超える」とは断定できない。段 2 の `約95,116` は正確だが、rotation 必須の推論は未確定だった。

さらに現在の local `main=18d7fc3` では、

- `docs/worklog.md = 87,444 bytes`
- 空き `12,556 bytes`
- entry `(73)` は既に `docs/archive/worklog-phase3-0731-73.md` へ移動済み
- entry `(79)` は cleanup-branches が既に使用済み

である。したがって同 archive を再作成して `(79)` を追加する段 2 手順は現在は完全に refuted。T-207 は `(80)` 以降を使い、完成 bytes を測ってから rotation を判定すべきである。

### 5. `phase3.md` の 8c 節外修正

- 日付 19 行: **real / scope 外 / nit**。日付更新だけでは成果物値・参照を変えない。
- 21–22、27–29、81–82、364 行: **real / scope 内 / must-fix**。bounded unattended MVP が存在するのに「全 loop human-supervised」「8c 未着手・条件付き」と残る。
- 797–804 行: **real / scope 内 / must-fix**。現 MVP は axis-proposer を呼ばないため、「8c 配管が載れば機械検査」と読む現記述は、未実装 gate を有効と見せる。

**DW-G05（状態・順序）:** 放置すると、現行 phase 台帳が取り込んだ terminal report を human-supervised／8c 未着手として参照し、trial の状態と次工程参照が逆転する。

**DW-G05（axis-proposer）:** 放置すると、axis-proposer 不使用の trial report を恒真提案の機械検査済みと解釈でき、report が主張する受理集合が実装より強くなる。

## 攻撃対象 3 — 取りこぼし

### 1. local `main` が前進済み

**仮判定: real / scope 内 / must-fix**

最終確認時点で、

- wave HEAD: `c34f35e`
- local main: `18d7fc3`
- `c34f35e..main`: 5 commit
- staged: 指定 5 ファイルのみ

である。段 2 の行番号、archive、entry `(79)`、保存則 source は stale。`DW-STOP` に従い現 plan を invalidate し、最新 main に合わせて brief／plan を再確定しなければならない。rebase で隠してはならない。

なお `main@18d7fc3` では `D106` と `T-221`〜`T-224` は全て 0 hit で未使用。

**DW-G05:** stale plan のまま進めると worklog `(79)` と archive path が衝突し、T-207 の台帳参照が二義化するか、land helper が stale-main で停止して成果物が main から参照不能になる。

### 2. merge commit の provenance

**仮判定: real（条件付き）/ scope 内 / must-fix if triggered**

段 2 の主張は「両親のどちらとも異なる実装 path」に限って正しい。

- 実装面を変える AI 関与 commit は実在する Codex author が必要。[ai-provenance.md:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/ai-provenance.md:51)
- checker は merge の各 parent との差分 path の**積集合**を実装差分とする。[check_ai_provenance.py:612](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_ai_provenance.py:612) [同:618](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_ai_provenance.py:618)
- 新規 3 実装ファイルは第 2 parent と同じなので、それだけでは merge commit の resolution-authored 実装に数えない。
- `tools/check_docs.py` を両 parent と異なる内容へ直せば積集合に入り、merge commit に実在する Codex author が必要。

分け方は以下が正しい。

1. source branch を履歴付き mergeし、merge resolution は docs のみに限定。merge commit は integrator／docs author。
2. checker 変更を裁定した場合だけ、実際の Codex author worker が checker＋test を書き、親が新 D を同じ変更単位へ統合した別 commitにする。

単に merge messageへ架空の `role=author` を足してはならない。

**DW-G05:** 条件成立時に分離／author 帰属を欠くと、その実装 commit が provenance 監査で拒否され、report／台帳が参照する merge tipを監査済み proof chainへ入れられない。

### 3. 「次の一手」保存則

**仮判定: real（機械条件）かつ段 2 の説明は過大 / scope 内 / must-fix**

実装の要求は次だけである。

- source: 前 entry の `### 次の一手` にある top-level item の先頭 ID。[check_docs.py:1170](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:1170)
- sink: 後続 entry **全体**の top-level item 先頭 ID、または `phase3.md` の生きた見送り台帳 ID。[同:1195](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:1195)
- 同じ説明文・同じ意味・`次の一手` 内への配置までは checker は検査しない。

したがって段 2 の「全 ID を entry (79) へ同じ意味で保持」は安全な人間規律ではあるが、機械要件ではない。現在は entry `(79)` が source、T-207 の新 entry `(80)` が sink である。現 entry `(79)` の source ID は 133 件。

**DW-G05:** entry `(80)` が、phase 見送り台帳にもない source ID を落とすと `check_docs` が拒否し、現行タスク台帳からその参照が消える。

### 4. 番号再採番の全数結果

**仮判定: real / scope 内 / must-fix 1 件**

取り込み 5 ファイルと branch 由来 phase 8c hunkの distinct な global ID は、実質的に以下だけ。

- `T-178`: main が当 branch 用に予約・参照済み。同じ意味なので維持。
- `D99`: main では RuleOps。`D106` へ変更必須。
- `T-179`: main では worker resource ledger。`T-221` へ変更必須。
- `H1` / `H2`: main の rr80 / rr20 holdout と同じ意味なので維持。

他の distinct D/T 衝突はない。ただし段 2 が `T-179` の出現を 1 件取りこぼしている。

- insight 127 行
- insight 130 行

段 2 手順は 127 行しか変更しないため、130 行の「`T-179` は…再開する」が main の worker ledger を指したまま残る。[insight:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md:127) [同:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md:130)

また `T-180` / `T-181` は採用する 5 ファイルや phase hunkには出現しない。`T-222` / `T-223` は本文置換ではなく、破棄する branch worklog から再構成する新 follow-up である。

**DW-G05:** 130 行を直さないと operational pilot の再開先が main の別タスク T-179 を参照し、insight の次工程参照が誤る。

## 総括

段 2 プランはそのまま採用不可。最低限必要なのは次である。

- 最新 `main=18d7fc3` 基準で brief／plan を再確定
- worklog は既存 archive を再作成せず、entry `(80)` を使用
- insight の `T-179` を 127・130 行の両方で `T-221` へ変更
- D106 と brief の「再実装なし」を authoritative path／pre-audit に分けて補正
- `phase3.md` の false status と axis-proposer false gate を修正
- `output/README.md` に exploratory `autonomous-trials/` を登録
- checker glob 一般化と `docs/README` 地図拡張は本 waveから外す
- checker変更を将来採るなら、新 D＋境界test＋実在するCodex authorの別commitにする

pytest は実行しておらず、merge 後の受入実測は親が計算ノードで行う必要がある。