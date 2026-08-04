判定は **NO-GO**。blocker は 3 件。形式上は通るが、cap-lift の運用規則としては迂回可能である。

## 形式契約

decision fragment 自体の形式違反は **0 件**。

- frontmatter は許可された 5 key のみで、ファイル名とも byte 一致している。[対象 fragment:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:1) [共通契約:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/README.md:35)
- H2 は `## {{D:slug}}. <題>` の 1 件だけで、題末尾に日付はない。[対象 fragment:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:9) [decisions 契約:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/README.md:5)
- placeholder は有効で、既存 D は D121・D138・D114 と実番号で参照している。
- 決定本文に有効な `[T-数字]` はないため、D70 の自己汚染もない。[禁止規則:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/README.md:35)
- `validate_spool_tree` は issue 0、`python3 tools/check_docs.py` は `違反なし`。ただし checker 自身が意味矛盾を保証しないと明記している。[check_docs.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:7)

## 所見

### RB-B1 — `NOT_CLAIMED` は、空実装を添えれば事実上の自己申告になる

- **主張:** 宣言だけでは文面上足りないが、承認者が実装の意味的実在を確認する入力・基準・receipt がない。最小攻撃は「空 handler＋恒真 calibration＋`NOT_CLAIMED`」である。
- **根拠:** 判定者を「承認する人間」とするだけで、申請入力は定義されていない。[対象 fragment:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:41) しかも fragment 自身が、空 handler・恒真 assert を塞がず、receipt もないと認めている。[対象 fragment:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:55) [対象 fragment:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:64)
- **不足情報:** 対象 revision・運転構成、cap-lift 承認 authority、閉じた witness-kind 集合、正負 calibration の具体入力と期待値、独立検査者、test-result hash、global/per-run の免責射程、receipt と consumer、P4 の batch cardinality が cap-lift 判定入力としてどこにも定義されていない。D138 が定めるのは帰納契約の意味であり、実装済み判定 package ではない。[D138:6744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6744)
- **成果物影響** — 空実装でも多世代受理集合が開き、proof chain は恒真 test ID、試行台帳は実効還流ゼロの追加 generation を参照する。
- **修正案:** 決定 (4) に次を追加する。

  > 現時点では P6 の意味的充足契約と cap-lift receipt が未裁定・未実装であるため、`NOT_CLAIMED` を認定できる判定入力は存在しない。これらが対象 revision に束縛されるまでは P6 を `NOT_IMPLEMENTED` と判定し、承認上限を変更してはならない。申請者の宣言、path 名、test node 名だけは実装済みの証拠に数えない。

### RB-B2 — 「既裁定の帰結」は D96 の免除理由にならない

- **主張:** P4 を無条件義務にする実体的帰結は択一 3 の裁定から正しく導ける。しかし、それにより cap-lift の規範上の受理集合が狭まる事実まで「新しい判断ではない」で消している。
- **根拠:** fragment は P4 の条件を恒真として無条件集合へ移す一方、「新しい判断ではない」とする。[対象 fragment:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:27) 択一 3 の必須化自体は実在するユーザー裁定である。[worklog archive:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:322) D96 は受理集合変更について、新 D と境界テストの同一変更単位を要求する。[D96:4271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:4271)
- **成果物影響** — 将来の cap-lift 実装が P4 非適用拒否の境界テストなしで land し、certified 受理集合と proof chain の P4 status が未固定になる。
- **修正案:** 決定 (2) の末尾を次へ置換する。

  > これは追加の実体裁定ではないが、2026-08-03 裁定は cap-lift の規範上の受理集合を縮小した。本 D を D96 の設計判断記録とする。機械受理集合は承認上限 1 のため現時点では不変である。cap-lift を結線する変更は、P4 充足の正例と P4 非適用を拒否する境界テストを同じ変更単位で更新しない限り land してはならない。

  研究状態への影響も「production の現行受理集合は不変だが、将来の cap-lift 規範受理集合は縮小」と二分して書くべきである。[対象 fragment:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:93)

### RB-B3 — 運用 runbook が旧 D121 だけで cap-lift できる経路を残している

- **主張:** 新 D を知らない承認者は、現行 runbook の「D121 の 10 条件＋D96＋D114 更新」だけを実行できる。append-only で残る D121 の旧非適用条項をそのまま使える。
- **根拠:** runbook の実際の cap-lift 手順は D121 しか参照していない。[runbook:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:118) D121 には旧「P4/P6 非適用は失敗に数えない」が残る。[D121:5851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5851) 今回の living-doc 修正は択一件数の訂正だけである。[runbook:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:205)
- **成果物影響** — obsolete な `P4/P6=非適用` で多世代が受理され、proof chain と試行台帳が新 D を参照しない。
- **修正案:** runbook 3 節へ新 D の番号を前方参照せず、規則を逐語で追加する。

  > D121 の 10 条件は、P4 を無条件義務として評価し、P6 は未実装なら FAIL、実装済みで当該運転が generalized cut を主張しない場合だけ免責する。P4/P6 を単一の「非適用」で外してはならない。意味的充足契約と cap-lift receipt が未確定の間は承認上限 1 を維持する。

### RB-M1 — P4 は、後続裁定 1 件で再条件化できる

- **主張:** 現規則を申請者だけで崩すことはできないが、「軸 (iii) を当該構成では必須にしない。P4 は非適用」とする後続ユーザー裁定 1 件で崩せる。将来裁定時の遷移契約がない。
- **根拠:** P4 無条件化は「撤回・上書きした後続裁定は無い」ことだけに依存する。[対象 fragment:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:27) 一方、P4 本体の「択一 3 を採る場合のみ」という条件は保存される。[D121:5846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:5846)
- **最小手順:** (1) 軸 (iii) 必須化を特定構成について撤回する裁定を取る、(2) 決定 (2) の恒真前提が消えたと主張する、(3) 保存された D121 の P4 発火条件を偽にし、未定義になった status を非適用として要求する。
- **成果物影響** — P4 の batch freeze なしで多世代受理集合が開き、proof chain の P4 status と候補 commit/seal 参照が消える。
- **修正案:** 次の遷移条項を追加する。

  > 将来、軸 (iii) の必須化を撤回または限定する裁定は、本 D の決定 (2)・(3)・(5) の明示的 supersede、P4 の代替 status、D96 の新 D・境界テストを同じ変更単位で定めない限り、cap-lift 判定には効力を持たない。

### RB-M2 — `[T-244]` を `完了` にすると未解決本体を台帳から消す

- **主張:** U2 だけは済んだが、T-244 本体、V1〜V4、P6 実装、上限解除は未解決である。`完了` は不可で、`更新` が必要。
- **根拠:** 現行 active item 自身が「本体は未解決・上限 1」と明記する。[worklog:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:614) 段 4 も V1〜V4 を裁定パッケージへ残す。[s4-adjudication:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md:99) `完了` は残件なしに限る。[worklog fragment 契約:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/worklog/README.md:64)
- **成果物影響** — active 試行台帳から `[T-244]` が消え、後続 wave が cap-lift を「残件なし」と誤認する。
- **修正案:** `seq: 2` の worklog fragment で `[T-244]` を `更新` し、V2〜V4 を placeholder で起票する。現在の substantive `base` は `561133878fa793e7a5793ca544af03b85be0dcd49fe8b047c9f70159b917c9cf`。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t244-u2-na-bifurcation
seq: 2
title: [T-244] U2 の新 D と cap-lift 残余 V1〜V4 を記録する
---

## 本文

- {{D:t244-u2-na-bifurcation}} で U2 を記録した。承認上限 1 と未実装は不変である。
- V1 は [T-244] に残し、V2〜V4 は裁定待ちの新規項として保存する。いずれも本 wave で解決済みとは扱わない。

## 次の一手差分

### 更新

- [T-244] **P1・U2 記録済み、V1〜V4 と実装は未解決**: {{D:t244-u2-na-bifurcation}} で未実装由来の非適用を FAIL と記録した。
  V1 (`NOT_CLAIMED` の global/per-run 射程) は P6 実装裁定と同時に決める。V2={{T:t244-p6-semantic-contract}}、V3={{T:t244-cap-lift-receipt}}、V4={{T:t244-prereg-refresh-ruling}} を前提として追跡する。
  **本体は未解決** — P6 と cap-lift は未結線、D114 の承認上限 1 は不変である。
  base: 561133878fa793e7a5793ca544af03b85be0dcd49fe8b047c9f70159b917c9cf

### 新規

- {{T:t244-p6-semantic-contract}} **P1・ユーザー裁定待ち (V2)**: P6 の意味的充足、正負 calibration の具体反例、非空限界効果の変異、独立検査者を定義する。
- {{T:t244-cap-lift-receipt}} **P1・ユーザー裁定待ち (V3)**: revision・P1〜P10 status・裁定参照・witness hash を束縛する receipt と consumer 結線を裁定する。
- {{T:t244-prereg-refresh-ruling}} **P2・専用裁定待ち (V4)**: 凍結・再事前登録手続に従い stale な generation-budget 条項の改訂可否と変更単位を決める。
```

この形は worklog parser で issue 0。別 wave が `[T-244]` 本文を更新した場合は、fold が `base` 不一致で停止するため再計算が必要である。[fold:1334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/spool_fold.py:1334)

### RB-M3 — 正式 preregistration が既裁定を未裁定とし、新 D を条件に含めない

- **主張:** V4 を単なる worklog prose にすると、正式系列の発効条件が stale のまま残る。専用 T として保存しなければならない。
- **根拠:** prereg は budget=1 の主張可否を未裁定とし、2 世代化には単に「T-244 の裁定」を要求する。[preregistration:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:44) [preregistration:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-8c-preregistration.md:69) しかし裁定段は既に完了し、本体実装だけが残る。[worklog:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/worklog.md:590)
- **成果物影響** — 正式試行が解決済み裁定を待ち続けるか、逆に U2/P4/P6 の実装確認なしで発効し、試行台帳と certified 集合が分岐する。
- **修正案:** 上記 `{{T:t244-prereg-refresh-ruling}}` を必ず起票し、新 D に「V4 の再事前登録が完了するまで現 preregistration は cap-lift の証拠にならない」を追加する。凍結手続を飛ばした in-place 修正はしない。

### RB-M4 — 「機械 gate を作らない」が、採用済みの将来実装まで却下したように読める

- **主張:** 決定 (7) は今回の非実装 scope と、既裁定の「後続 wave で P1〜P10 を機械束縛する」を区別していない。
- **根拠:** fragment は無限定に「cap-lift を機械 gate として結線しない、新しい status field を作らない」と書く。[対象 fragment:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:69) 一方、択一 2 は条件成立後の独立 wave で機械束縛すると裁定済みである。[worklog archive:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:320)
- **成果物影響** — 後続実装が receipt evaluator と completeness gate を省略し、proof chain と多世代受理集合の結線が永久に欠ける。
- **修正案:** 決定 (7) 冒頭を次へ変える。

  > 本 wave／本 D では cap-lift を機械 gate として結線せず、status field も新設しない。これは択一 2 の「択一 1・3 確定後に独立 wave で機械束縛する」という既裁定を却下・延期するものではない。

### RB-M5 — living docs の「全件裁定済み／設計本体未確定」が運用に必要な残件を示さない

- **主張:** 択一の方針裁定が済んだことと、cap-lift 可能な設計が完成したことを分離できていない。「未確定」の内訳がないため、後続 wave は全再裁定か全確定のどちらかへ誤読する。
- **根拠:** `phase3.md` と runbook は「7 件全裁定済みだが設計本体未確定」とだけ書く。[phase3.md:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:474) [runbook:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3-s8c-autonomous-trial-runbook.md:205) 実際には予算値再導出・機械束縛・off-arm の予算/受理集合整合が残る。[worklog archive:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/archive/worklog-phase3-0803-125-126.md:318) D138 にも crash 回復・replicate・0-bit 証明等が残る。[D138:6796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/decisions.md:6796)
- **成果物影響** — proof chain が未決 parameter を確定設計として引用するか、確定済み択一を再び裁定待ちに戻し、試行開始条件が分岐する。
- **修正案:** 両 living docs を次の意味へ置換する。

  > 択一 7 件の方針裁定は完了した。ただし、択一 1 の予算値、P6 の意味的充足と receipt、off-arm の予算・受理集合整合、機械束縛、D138 の列挙する回復・replicate・0-bit 証明は未確定または未実装であり、cap-lift 可能な設計は完成していない。

### RB-N1 — 「逐語の正本」が directory 単位で非一意

- **主張:** directory には erratum 付き brief と段 4 裁定が共存するため、どれが最終規範か一意でない。
- **根拠:** fragment は directory 全体を逐語正本とする。[対象 fragment:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/spool/decisions/2026-08-04-dev-wave-t244-u2-na-bifurcation-1.md:17) brief は誤った前提を履歴として残すと明記している。[brief:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/output/insights/2026-08-04_t244-u2-na-bifurcation/brief.md:3)
- **成果物影響** — proof chain が最終裁定でなく erratum 前の三分法を根拠として参照し得る。
- **修正案:** 「ユーザー裁定の正本 = worklog (153) U2、wave 裁定 = `s4-adjudication.md`。`brief.md` は erratum を含む履歴であり規範ではない」と明記する。

## living docs・予算の確認

今回の 2 ファイルは living-doc lint 対象だが、`TextLimit` の byte 予算対象ではない。[check_docs.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:29) [check_docs.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/tools/check_docs.py:167) したがって byte 予算圧迫はない。

`docs/phase3.md` の変更は見送り台帳開始前であり、sink や既存 ID を直接変更していない。[phase3.md:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-u2-na-bifurcation/docs/phase3.md:520) 副作用は形式ではなく、RB-B3・RB-M3・RB-M5 の consumer 不整合である。

pytest と受入試験は実行していない。既存テスト期待値の変更も提案していない。

## 総括

- blocker: **3 件**
- major: **5 件**
- nit: **1 件**
- must-fix:
  - RB-B1: `NOT_CLAIMED` を現時点で認定不能と明記する
  - RB-B2: D96 の将来境界テスト義務を固定する
  - RB-B3: operational runbook に P4/P6 の新規則を逐語で反映する
  - RB-M1: P4 再条件化時の supersede/D96 遷移契約を追加する
  - RB-M2: `[T-244]` は `更新` とし、V2〜V4 を placeholder 起票する
  - RB-M3: stale preregistration を専用裁定タスクとして保存する
  - RB-M4: 今回の非実装と採用済み将来 machine binding を分離する
  - RB-M5: living docs に未確定・未実装の具体的内訳を書く