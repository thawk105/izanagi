結論は **NO-GO** です。現案は「意味検査」ではなく、同一 commit で弱体化でき、期待値を変えなくても迂回できる token-presence lint です。

### 1. 必須 token は参照 edge を検査していない

確度: **high** / 判定: **real**

根拠: plan は `docs/failures.md` と `F26` を別々の必須要素にしています（[s2b-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:25)、[s2b-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:28)）。現 command では F26 が見出し等に残ります（[cleanup-branches.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/.claude/commands/cleanup-branches.md:29)）。plan 自身も無関係な可視段落への token 移動で通ると認めています（[s2b-plan.md:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:136)）。

具体的な迂回差分は次です。期待 literal 一覧は変更不要です。

```diff
-`git submodule update --init external/ccbench` で復元する。正本は `docs/failures.md` F26。
+`git submodule update --init external/ccbench` で復元する。

-## 6. スキル自己改善 (発火条件つき)
+## 6. スキル自己改善 (`docs/failures.md`)
```

F26/F51、可視な `docs/failures.md`、path 実在性、全 F heading 到達性がすべて残る一方、F26→台帳の edge は消えます。したがって草稿の「F173 の攻撃をちょうど殺す」は偽です（[package-draft.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/package-draft.md:42)）。

親の裁定変更: **現行 (a) を却下し、採るなら command の F26→`docs/failures.md` という同一行・同一 edge だけへ局所化し、token 移動負例を追加する。**

### 2. 無限後退への反論は、監査上の見やすさしか増やさない

確度: **high** / 判定: **real**

根拠: plan は checker と test に独立 literal を置きますが（[s2b-plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:99)）、両方とも同じ commit で編集できます。現行テストにも既に command 全文コピーがあり（[test_check_docs.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:318)）、安全文の削除は test 側の diff にも露出します（[test_check_docs.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:355)）。

協調攻撃の diff は、概念的に次だけです。

```diff
-command 本文と synthetic copy から F26 edge を削除
-checker の required edge/token を削除
-test 側の独立期待値・負例 parameter を削除
+command / Skill の SHA-256 期待値を再同期
```

新案は「契約を弱めた」という意図を見やすくしますが、現行も safety line の削除を source と全文 fixture の双方へ表示します。差はレビュー時の顕著性であり、不変 trust root の新設ではありません。

親の裁定変更: **機械化を「協調改変を防ぐ防壁」ではなく「非協調 drift の検出と diff の顕在化」に格下げし、人間レビューを最終 trust root と明記する。**

### 3. F26 pointer は既存契約の欠落補修として扱える

確度: **high** / 判定: **real**

根拠: `check_docs.py` は既に非 dev-wave command に `docs/skill-self-improvement.md` への到達性を要求しています（[check_docs.py:4105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4105)、[check_docs.py:4107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4107)）。この検査も同一 commit で削除可能ですが、それでも通常 drift を捕える既存契約として有用です。

したがって整合する結論は「mutable lint は全部無意味」ではなく、「人間レビュー下の構造契約として有用」です。F26 edge もその局所的な欠落補修にできます。全 path・全 F ID・Skill 側まで扱う専用関数が必要だという plan の結論（[s2b-plan.md:105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:105)）は導けません。

親の裁定変更: **既存 command 契約へ cleanup command 固有の可視 F26 edge を 1 件足す局所修復に縮める。**

### 4. `a-narrow` と正本の衝突自体は成立しない

確度: **high** / 判定: **refuted**

根拠: 正本は lint の責務を構造に限定し、文言・意味を敵対監査と人間レビューへ残しています（[skill-self-improvement.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/skill-self-improvement.md:83)、[skill-self-improvement.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/skill-self-improvement.md:84)）。D227 が禁じるのは機械化を既存 prose の削除根拠にすることです（[decisions.md:10628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/decisions.md:10628)）。既存 prose を残したまま address edge を補助検査する狭い読みは成立します。

ただし草稿の「意味検査の機械化」（[package-draft.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/package-draft.md:24)）はこの読みではありません。

親の裁定変更: **この懸念が real ではないため a-narrow 自体の撤回は不要。ただし名称を「address edge の構造 lint」へ直し、意味保証の文言を全削除する。**

### 5. M3 は二つの実測 gate に限定すべき

確度: **high** / 判定: **real**

根拠: provenance は実装面 path に Codex author がいるかを検査するだけで（[check_ai_provenance.py:1056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_ai_provenance.py:1056)、[check_ai_provenance.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_ai_provenance.py:1072)）、意味欠落は見ません。ただし親が checker/test を直接変更した commit は author 境界で拒否され得ます（[check_ai_provenance.py:1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_ai_provenance.py:1101)）。

射程は次のとおりです。

| 層 | 射程 |
|---|---|
| Claude command | 対象 |
| Codex Skill | command を全文読むため対象（[SKILL.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/.agents/skills/cleanup-branches/SKILL.md:14)） |
| 他 command / Skill | 対象外 |
| hooks | 意味検査なし。ハーネス自体も防護外（[hooks/README.md:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/hooks/README.md:212)） |
| provenance | author 境界のみ |
| land | fold 時に同じ `check_docs.py` を再実行するだけ（[dev_wave_land.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/dev_wave_land.py:1795)） |

よって authorized Codex-author 経路なら独立した意味防壁は見当たりませんが、provenance・hooks・land が緑だったという実測ではありません。

親の裁定変更: **M3 を「working tree 上で `check_docs` と `test_check_docs.py` が緑」に限定し、land 可能性は authorized-author 条件付きの静的結論として分離する。**

### 6. `DW-G03` に対して scope が広すぎる

確度: **high** / 判定: **real**

根拠: `DW-G03` は単発事故を局所修復とし、族一般化には独立 2 例を要求します（[core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/dev-wave/core.md:57)）。brief 自身も実害 1 件と認めています（[s1-brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s1-brief.md:20)）。

それにもかかわらず plan は未破損の audit helper、F51、Skill→command、Skill→self-improvement、全発見 path/F ID まで恒久検査します（[s2b-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:25)、[s2b-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:28)）。command と委譲 Skill は独立 2 例ではなく同じ upstream incident の producer/consumer です。

親の裁定変更: **F173 で壊れた command→`docs/failures.md` F26 edge だけを候補に残し、F51・helper・Skill・全 path/F lint は 2 例目まで却下する。**

### 7. `DW-G05` 上は must-fix ではなく nit/backlog

確度: **high** / 判定: **real**

根拠: `DW-G05` が要求するのは成果物、すなわち certified 選択・レポート・台帳の値・受理集合・参照への影響です（[core.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/dev-wave/core.md:67)）。書けなければ明示的に nit/backlog です（[core.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/dev-wave/core.md:69)）。

plan は三成果物の値が変わらないと認めた後、「AI 作業手順の受理集合」へ対象を差し替えています（[s2b-plan.md:140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:140)）。これは列挙された成果物ではありません。「単独 wave の根拠が弱い」（[s2b-plan.md:150](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-pin-semantic-gap/s2b-plan.md:150)）ではなく、規範上は backlog と明記すべきです。

親の裁定変更: **(a)/(b) とも must-fix から外して backlog に置き、追加 review wave・単独実装を起動しない。**

静的検証のみで、pytest・`check_docs`・provenance・land は実行していません。ファイル変更もありません。

## 総括

**NO-GO。** 現行 (a) は token 移動だけで迂回でき、同一 commit の contract 弱体化にも耐えない。  
F173 の 1 件から Skill・全 path・全 F ID へ広げる案は `DW-G03` 違反。  
三成果物への影響がないため `DW-G05` 上は must-fix ではなく backlog。  
再裁定するなら「command の F26 address edge だけを守る局所的・補助的 lint」に縮めるべきです。