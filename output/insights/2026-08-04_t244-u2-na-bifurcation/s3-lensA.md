## A-B1 — 実装 witness を空実装と恒真テストで偽装できる

- **主張:** status を決めるのは申請者ではなく承認者だが、承認者へ渡す「実装 path・検査 ID・検査結果」の意味的充足が定義されていない。したがって申請者が作った形だけの witness を人間が追認する構造である。

- **根拠:** 判定者は cap-lift を承認する人間で、申請者の宣言は入力にすぎない点は明確である一方、要求は path・検査 ID・結果の列挙までである。[s2-plan.md:43–53](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:43>) [s2-plan.md:74–80](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:74>)。D138 が要求する本質は事前登録仮説、`B \ C_exact ≠ ∅`、反証時 seal、閉じた witness 和であり、単なる実装存在ではない。[docs/decisions.md:6744–6758](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6744>)。しかも申請 artifact/schema は存在せず、人間 gate のままである。[brief.md:33–43](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:33>)

  最小攻撃手順は次のとおり。

  1. `p6_contract.py` に空の `handle()`、常に `None` を返す cycle/integrity adapter、未知 kind だけ例外にする分岐を置く。
  2. `test_positive_calibration` / `test_negative_calibration` を `assert True`、adapter テストを `assert callable(...)`、未知 kind だけ `raises(...)` にする。
  3. この path と test node ID、passing result を「閉じた実装面」として提出し、generalized cut は主張しないと宣言する。
  4. 承認者が `NOT_CLAIMED` と認定した後、定数と境界テストを更新する。実際の還流機能は一度も発火しない。

- **反証されうる条件:** 新 D が、各 witness ID に D138 の意味的 oracle、正負 calibration の具体的反例、非空 marginal-effect 変異、対象 revision の hash、独立検査者を要求し、空 handler／恒真 assert を必ず拒否するなら本所見は誤りとなる。

- **成果物影響:** certified 選択の探索範囲と invocation 受理集合が多世代へ拡大し、proof chain は空実装の test ID を参照し、試行台帳には実効還流ゼロの追加 generation が記録される。

## A-B2 — 一裁定の直通路はプランで塞いだが、限界効果ゼロの cap-lift は残る

- **主張:** 親 brief の三分法をそのまま使えば、「座標／generalized cut を採らない」という先行裁定だけで P6 を `NOT_TRIGGERED_BY_RULING` にできる。段 2 プランはその直接路を閉じたが、実装済み `NOT_CLAIMED` を global cap-lift の免責にするため、効果ゼロの解除はなお可能である。

- **根拠:** 親の P1 は第三種を条件付き義務一般へ導入しており、P4 自身もこの P6 迂回を認めている。[brief.md:21–31](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:21>)。プランは `NOT_TRIGGERED_BY_RULING` を P4 限定にし、P6 では実装確認を先行させるので、この「裁定一つだけ」の攻撃は閉じる。[s2-plan.md:16–19](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:16>) [s2-plan.md:49–53](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:49>)。

  しかし D138 の定理では exact-only の受理集合への限界効果はゼロであり、非ゼロには未実測候補を禁じる帰納段が必要である。[docs/decisions.md:6726–6741](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6726>)。ユーザーも帰納段を踏み、還流放棄で T-244 を閉じないと裁定済みである。[docs/worklog.md:1115–1125](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:1115>)。それでもプランは P6=`NOT_CLAIMED` を cap-lift 成功扱いにする。[s2-plan.md:67–70](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:67>)

  親 P4 の「還流の実効性 > 0」は、D138 の `B \ C_exact ≠ ∅` と receipt に結び付ければ穴を塞ぐ。しかし現状の定性的な「支える」では自己申告となり、厳密に解すれば P6 以外に非ゼロ効果を作る義務がないため永久 FAIL になる。プランはこの条項自体を落としている。[s2-plan.md:157–161](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:157>)

- **反証されうる条件:** `NOT_CLAIMED` が global cap-lift の免責ではなく個別 run の状態に限定され、`generations>1` の各 run が `B \ C_exact ≠ ∅` を持つ署名済み receipt を要求する、または U3 は cap-lift を拘束しないとの追加裁定があれば本所見は誤りとなる。

- **成果物影響:** global cap は開く一方で candidate 受理集合は exact-only のまま一点も狭まらず、certified 選択・proof chain・試行台帳だけが「有効な還流あり」と誤読可能な多世代形へ変わる。

## A-B3 — 判定規則が承認記録から proof chain まで結線されない

- **主張:** 本 wave が実際に変更するのは decisions/worklog の規範だけである。cap-lift receipt が存在しないため、runbook・事前登録・proof chain・台帳・材料レポート・機械 gate のどこからも新判定を再検証できない。

- **根拠:** プラン自身が追加更新 0 件、機械 gate/status field なしとする。[s2-plan.md:55–59](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:55>) [s2-plan.md:112–123](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:112>)

  | 層 | 現状 | 本 wave の到達範囲 |
  |---|---|---|
  | 承認手続 | 申請 artifact/field 自体がない。[brief.md:33–35](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:33>) | 人間向け規範だけ |
  | runbook | 「10 条件＋D96＋定数・境界テスト更新」までで、status/witness receipt はない。[runbook:118–121](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:118>) | scope 外 |
  | 事前登録 | T-244 裁定・D114 改訂・再事前登録だけを要求する。[preregistration:69–72](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:69>) | scope 外 |
  | proof chain | completeness は report budget と可変な producer 定数を比較するだけ。[autonomous_trial_completeness.py:394–418](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:394>) [同:998–1004](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:998>) | scope 外 |
  | 試行台帳/report | `run-start` と report は budget を持つが approval revision/status/receipt hash を持たない。[producer:1158–1184](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:1158>) [同:1611–1621](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:1611>) | scope 外 |
  | 材料レポート | 前 wave 自身が Layer3、WAL replay、critic digest 等を将来の consumer 取り残しとして列挙している。[README.md:452–469](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-03_t244-p6-contract/README.md:452>) | scope 外 |
  | 機械 gate | producer は共有定数と `>` 判定、consumer も同じ定数を読む。[producer:247–256](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:247>) | scope 外 |

  **裁定パッケージ候補:** `(a)` revision・P1〜P10 status・ruling ref・witness/test-result hash を持つ cap-lift receipt、`(b)` runbook/事前登録への必須 receipt 手順、`(c)` journal/report/Layer3 の receipt hash 結線、`(d)` `generations>1` を receipt 検証なしでは拒否する producer＋completeness gate。

- **反証されうる条件:** 新 D が「これは規範の起草だけで穴を運用上閉じたとは主張せず、上記裁定パッケージが実装されるまで上限 1 を変更禁止」と明記するなら、現在 wave の過大主張という部分は解消する。

- **成果物影響:** 定数変更だけで多世代 report・proof chain・Layer3・試行台帳が受理され、承認根拠を失ったまま将来の certified 選択集合が広がる。

## A-M1 — 無条件義務の NA 回避は原文上は禁止だが、status 語彙の射程が曖昧

- **主張:** D121 原文は P4/P6 だけを条件付きとし、P1・P2・P3・P5・P7・P9・P10 を明示的に無条件としているため、これらを「非適用」とする経路は許していない。ただし新 D の「5 値を固定する」という無主語の書き方は、その禁止を再び曖昧にする。

- **根拠:** D121 は10条件を前提としたうえで、P4/P6のみを条件付きとし、直後に無条件集合を列挙する。[docs/decisions.md:5842–5854](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5842>)。一方、プランの status 語彙条項は一般形だが、後段の表は P4/P6 だけである。[s2-plan.md:37–47](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:37>) [s2-plan.md:65–70](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:65>)。最終 D では無条件集合を `{SATISFIED, FAIL}` のみに閉じるべきである。P8 は10条件中の別個の保存義務であり、今回の三分法へ混ぜてはならない。

- **反証されうる条件:** 最終 D が5値の定義域を明示的に P4/P6へ限定し、無条件集合は `SATISFIED` 以外すべて FAIL と逐語化すれば本所見は解消する。

- **成果物影響:** 誤読で無条件義務を1件でも NA にできると、cap-lift の受理集合が未実装状態まで広がり、proof chain と試行台帳が欠落義務を免責済みとして参照する。

## A-M2 — 親の前提実測 (2) は不完全、(5) の一般化は実測ではない

- **主張:** 5件中、(1)・(3)・(4)とP6限定の(5)は再現した。(2)の核心「P1〜P10 evaluatorなし」は正しいが、「定数と validator だけ」は consumer gate・境界テストを落としており、(5)をP4へ広げる部分は新しい設計判断である。

- **根拠:**

  | 親の実測 | 独立判定 |
  |---|---|
  | (1) 既存 supersede なし | **確認。** D138 はD121を参照してU2を裁定へ返すだけで、改訂していない。[docs/decisions.md:6760–6765](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760>) |
  | (2) cap-lift機械 gateなし | **核心のみ確認。** P1〜P10/receipt evaluatorはない。ただしproducerの3入口 validatorに加え、completenessにも2検査がある。[producer:247–256](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/p3_autonomous_workload_trial.py:247>) [completeness:414–418](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:414>) [同:1003–1004](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/campaign/autonomous_trial_completeness.py:1003>)。CLI literal 1と三入口拒否のテストもある。[test_p3_autonomous_workload_trial.py:357–381](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/tests/test_p3_autonomous_workload_trial.py:357>) [同:674–686](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/tests/test_p3_autonomous_workload_trial.py:674>) |
  | (3) 軸(iii)未裁定 | **確認。** D121が明示的にユーザー裁定へ返し、後段でも未裁定に数えている。[docs/decisions.md:5794–5800](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5794>) [同:5837–5840](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5837>) |
  | (4) decisions.md非byte-pin | **現在の正本について確認。** `FROZEN_MANIFEST` はoutput 23件だけである。[test_frozen_artifacts.py:38–85](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/tests/test_frozen_artifacts.py:38>)。`check_docs.py` はD見出し重複だけを見る。[tools/check_docs.py:3183–3198](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:3183>)。hook testも「80KB超」を見るだけで追記では壊れない。[test_hooks.py:1377–1381](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/orchestrator/tests/test_hooks.py:1377>)。なお歴史的A/B snapshot用の旧hash参照はあるが、現行bytesのfreezeではない。[codex_reasoning_ab.py:84–101](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/codex_reasoning_ab.py:84>) |
  | (5) D138の二分 | **P6について確認。** handler等未実装=FAIL、実装済み非主張だけ免責である。[docs/decisions.md:6760–6765](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6760>)。P4は先行裁定で発火自体が変わる別契約であり、「条件付き義務一般への拡張」は実測でなく本 wave の新判断である。 |

- **反証されうる条件:** 「機械 gate」をP1〜P10の承認 evaluatorだけという狭い意味に明記し、D138からP4への拡張を provisional decision として扱えば、親の一般化問題は解消する。

- **成果物影響:** consumerが共有定数を読む事実を落とすと、定数変更だけでproof-chain verifierの受理集合も同時に緩み、P4への誤一般化は不適切な免責参照を台帳へ残す。

## A-M3 — append-only supersede は可能だが、現行案では旧規則を読む経路が残る

- **主張:** D114・D121・D138との直接矛盾は、限定アンカーを厳密に書けば避けられる。しかしD121本文を編集できず、runbook等も更新しないため、D121だけを部分読みした承認者は旧「非適用は失敗に数えない」をそのまま適用できる。

- **根拠:** D114は上限1と定数＋境界テストという実装変更面を定めるため、新Dをその前段の承認条件として置くこと自体は矛盾しない。[docs/decisions.md:5331–5341](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5331>)。D138のP6二分とも整合する。一方、旧文はD121に残り続ける。[docs/decisions.md:5851–5854](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851>)。プランは引用アンカーを置くが、追加consumer更新を0件とする。[s2-plan.md:61–63](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:61>) [同:112–123](</work/1/SFC/tanab/dev-wave-jobs/t244-u2-na-bifurcation/s2-plan.md:112>)

  新Dの題名と冒頭に「D121決定(7)の当該一文を本D以後は読まない」と置き、旧文の始端・終端、D138決定(5)の確定化、D114への追加承認条件を同時に書く必要がある。runbookと事前登録の参照更新は scope 外なら、少なくとも明示的な裁定パッケージ候補にすべきである。

- **反証されうる条件:** 新Dが検索可能な題名・完全な引用アンカー・優先順位を持ち、全cap-lift consumerが新Dまたはreceiptを参照するなら、読者誤誘導は解消する。

- **成果物影響:** 旧Dだけを根拠にした承認で受理集合が多世代へ広がり、proof chainと試行台帳が新Dではなくobsoleteな`P6=NA`を参照する。

## 総括

**blocker は3件。現プランのまま進めるのは NO-GO** である。

最低限、段4で次を閉じる必要がある。

1. 空実装・恒真テストを拒否する意味的 witness 契約。
2. U2の`NOT_CLAIMED`免責とU3の非ゼロ還流を、global cap／per-run gateのどちらで両立させるかの裁定。
3. scope外の承認receipt・runbook・事前登録・proof chain・台帳・材料レポート・機械gateを、明示的な裁定パッケージとして残すこと。

pytest、`check_docs.py` と受入試験は実行していない。静的読取・検索結果だけに基づく判定である。