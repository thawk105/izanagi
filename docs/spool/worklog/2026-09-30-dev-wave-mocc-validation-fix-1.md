---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-mocc-validation-fix
seq: 1
title: [T-2872] MOCC の validation の隙間を CCBench の 1 commit で直した (f4a5169e、branch izanagi-mocc-validation-fix、F 25898d00 の子) — lock 状態の読みの後に版を読み直して abort、上流 CI 2 本を CI image で手元通過、D297 は意図した修理差分で不合格、事前登録の trace build 112 走で G2 0・class A 0 (同時刻の修正前は G2 8/56)。push は人間の手番、gitlink は不変 (insight のみ、計算 2.19 node 時間、branch worktree-dev-wave-mocc-validation-fix)
---

## 本文

- 正本: `output/insights/2026-09-29/mocc-validation-fix/README.md` (修理の中身、CI 2 本、D297 の読み、trace 実測の表と判定、patch 棚卸しの C/F/X 表、push 依頼と上流への説明文の下書き)。設計判断は {{D:mocc-validation-recheck-fix}}。
- ユーザー確認: 本走の規模を AskUserQuestion で確認し、回答は「投入する (Recommended)」(見積り 本走 2.10 node 時間、wave 全体 約 2.5)。実費は CI build 33 S・D297 9 S × 2・smoke 93 S / 324 S・本走 3,686 S / 3,712 S、計 2.19 node 時間 (request 36270〜36272・36298・36299・36350・36351)。
- 判定 (事前登録 R6、runner の join が機械的に出した値): 判定不能 0、修正後の trace build の G2 0/112 走 (95% 上限 3.2%)、修正後の commit 側 class A 0 件 → 成功。同時刻の修正前 F: G2 8/56 走 (witness 9 件はすべて片側の辺で割り込みと一致)、class A 1,415 件。修正後の再読の不一致による abort は 6,368 件で、arm 別の 1 走あたりでは修正前の割り込み commit (class A + B) と同じ規模だった (trace 無し 159.9 対 167.1 件、trace 有り 16.9 対 17.4 件。別の走どうしの比較)。
- 性能の観測 (主張に使わない): trace 無し・計器無しの commit 数は修正前 7,200,449・修正後 7,241,787 (各 28 走、比 1.006)。
- 段 3 の相談 2 本・段 6 のレビュー 3 本・焦点再レビュー 1 本の real 所見は採用し、1 件は親が refuted とした (D297 判定 script の「両 compiler 合格なら合格と名付ける」枝は親の投げ文どおりで名前も正確)。段 7 の記録レビュー 1 本の should 3・nit 2 (見積りの入力の所在、因果の言い過ぎ、D297 の前進先への一般化、比較単位、採否の書き方) も直した。smoke 1 回目で runner が JSON の真偽値を `-DTRACE=True` にして T arm の trace を止めていた ({{F:bool-define-silently-disables-trace}})。判定は判定不能で止まり (fail-closed)、fix と build 後の compile 命令照合を足して取り直した。
- 親の手順の不備 2 件: 実装子 B の投げ文で先例 job dir の直下の 2 script を subdir 配下と誤記し、子が即停止した (F819 の再発)。投入 wrapper の 1 本目が `{ ...; exit $rc; } > log` の exit で `.done` を書けなかった (結果は log の終端行で確かめ、2 本目で直した)。
- エージェント工数: Codex plan 1・consult 2・author 3 (1 本は上の投げ文誤りで不受理)・review 3・fix 1・focus 1、Explore (sonnet) 1。子木 `.codex/worktrees/moccfix-a`・`moccfix-b` は 2 本とも submodule 初期化の 1 回目が `update-no-fetch` で落ち、同じ引数の再実行で通った (DW-O08)。
- 残置物: job dir `/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/` (道具・X.bundle・計算の全出力)。X の branch は land 後に主 checkout の submodule の git dir へ非 force で取り込む。

## 次の一手差分

### 更新

- [T-2872] **P1・修理 commit は済 → 人間の push と GitHub の CI 待ち → gitlink 前進で完了**: MOCC の read-heavy の G2 の原因 (validation が版の比較と lock 状態の検査を別の load で行う隙間) を CCBench の 1 commit で直した。X = `f4a5169ede52630d9357444e3412ffe9aed7c78f` (branch `izanagi-mocc-validation-fix`、F `25898d00` の直接の子、`cc/mocc/transaction.cc` の 1 hunk: lock 状態の読みの後に版を読み直し、最初の版と違えば abort、`max_rset_` は検査した版から取る)。上流 CI 2 本は CI image で手元通過 (format 213 file rc=0、build rc=0)、D297 は F → X で「不合格 (意図した修理差分)」、trace build の事前登録 112 走で G2 0・commit 側 class A 0 (同時刻の修正前は G2 8/56・class A 1,415)。正本 `output/insights/2026-09-29/mocc-validation-fix/README.md`。
  - 残り (人間): 主 checkout の `external/ccbench` で `git push origin izanagi-mocc-validation-fix` (F の branch `izanagi-tpcc-v3-silo-mocc-fmt` が未 push なら先に)、GitHub の Actions の build・format が緑であることの確認。上流への PR・追加報告は人間の判断 (D16)。説明文の下書きは insight §6。
  - 残り (AI): gitlink 前進は {{T:mocc-fix-gitlink-advance}}。t2849 の read-heavy の値は pin C の上の測定として有効のまま (D2277 項 2、規律 7)。
  base: d8357b954b76d685ba57d93aecb17281364ceab6e5c0cb5285210a14b3c40092

### 新規

- {{T:mocc-fix-gitlink-advance}} **P2・新規 (前提待ち)**: CCBench の gitlink を MOCC 修理込みの tip へ進める wave。前提 = [T-2854] の F への pin 前進が main に着地、ユーザーが `izanagi-mocc-validation-fix` を push、GitHub の CI (build・format) が緑、GitHub から X `f4a5169e` を取得できる。内容 = gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新 (先例 D2150 / D2184)、patch の厳密適用 (F → X で新たに外れる patch は 0 本、insight §5)、修理後の版で測り直すかの提示 (D2277 項 2)。**D297 の扱いを先に決める**: 実測した F → X は TRACE=0 の不一致で rc=1 (insight §3)。前進先の tip も同じ修理差分を含む限り同じ理由で不合格が見込まれる (前進先では未検査)。C → F の合格 (D2293) と F → X の意図した差分の審査を分けて受け入れる形などを裁定する ({{D:mocc-validation-recheck-fix}})。Silo 修理 (`izanagi-silo-intra-txn-fix`) と同じ時期なら、両方を積んだ tip への前進を 1 wave にまとめてよい (force push はしない)。1 タスクの計算が 2 node 時間以上なら見積りを示してユーザー確認。
