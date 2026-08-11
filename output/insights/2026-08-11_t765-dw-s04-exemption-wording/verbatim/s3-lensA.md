結論は **NO-GO**。静的検査のみで、pytest・変異実走は行っていない。

## 具体 wave の突合せ

ここでは現行の確定解釈を `C∧Z` とする。`C` は当該 wave の段 4 で「実装しない」と裁定して `4→7→8→9` を選ぶこと、`Z` はコード・テスト・実行可能 probe / harness / script・機械設定の差分がゼロであること。

| 具体 wave | C | Z | 現行 `C∧Z` | 推奨文 | 判定 |
|---|---:|---:|---|---|---|
| 段4で実装すると裁定したが、no-op・revert等で最終実装差分ゼロ | 偽 | 真 | 非免除 | 通常読みでは非免除 | 差なし |
| docs-only 書換え、通常経路と段6レビューを選択 | 偽 | 真 | 非免除 | 意図は非免除。ただし過去の「実装しない」裁定を「受けた」と読めば免除可能 | **拡大余地** |
| docs-only で段4から「実装しない」経路。実装面は元からscope外 | 真 | 真 | 免除 | 因果読みでは「裁定を受けてZになった」でないとして非免除にも読める | **縮小余地** |
| 実装全体を別 wave へ委譲し、当該段4で明示的に「実装しない」 | 真 | 真 | 免除 | 免除 | 差なし |
| 一部だけ別 wave へ委譲したが、当該 wave は通常経路 | 偽 | 真 | 非免除 | 委譲裁定を「受けた」と拾えば免除可能 | **拡大余地** |
| 「実装しない」裁定後、実行可能 script / probe / 機械設定だけ変更 | 真 | 偽 | 非免除 | P1のコード・テスト限定解釈では免除可能 | **拡大** |
| 本 T-765。docsを書換え、C=false予定 | 偽 | 真 | 非免除 | 不採用案(a)への先行裁定を拾う／自己裁定を変更すれば免除可能 | **自己適用余地** |

## 所見

### A1 — `裁定を受けて` は連言ではなく第三の関係を追加する

severity: blocker

主張: 推奨文の述語は単純な `C∧Z` ではない。因果・時間関係 `R` を要求する `C∧Z∧R` とも、当該段4以外の先行・部分裁定を拾う `C_external∧Z` とも読める。プランの「どちらでも二事実は必要だから集合不変」は、必要性と十分性を取り違えている。

file:line 根拠: [s2-plan.md:26–44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:26)、[brief.md:25–26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:25)、[dev-wave.md:48–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:48)

成果物影響: 拡大側では、現行が非免除とする wave が変異台帳の事前登録・kill 行なしで受理集合へ入る。縮小側では、現行免除 wave に不要または帰属不能な matrix を要求し、受理集合を狭めるか虚偽の証拠行を作る。

推奨対応: 推奨文を不採用にし、因果を含まない独立属性として書き直す。例えば `免除は「実装しない」裁定済み・実装面差分ゼロの wave の変異 matrix だけ。` は101 bytes、L1は10,624である。これも段4で「裁定済み」が当該 wave の裁定を指すと明示して再レビューすること。

### A2 — P1は一次資料より狭く、免除を実装面変更へ漏らす

severity: blocker

主張: docs差分をZ判定から除く実績はあるが、「実装差分＝コード・テストだけ」は裏が取れない。一次契約は実行可能 probe / harness / script・機械設定も実装面に含める。プラン自身もP1の不完全さを認めている。

file:line 根拠: [brief.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:42)、[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:67)、[dev-wave.md:34–37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34)、[T-642 README.md:5–10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-08_t642-dw-s04-acceptance-scope/README.md:5)

成果物影響: script・probe・harness・機械設定だけを変更した wave がZ=trueと誤分類され、変更された受入・検証器具を変異なしでlandできる。変異台帳のkill集合が欠け、受理集合が拡大する。

推奨対応: P1を却下し、Zを入口の「実装面」定義へ束縛する。文中も予算内で `実装面差分ゼロ` として、段4記録に全カテゴリを列挙する。

### A3 — 本 wave の自己免除経路が閉じていない

severity: blocker

主張: P2は不変条件でなく「段4で現在のplanを採用する限り」という条件付きである。しかも同じ `DW-S04` を変更したT-642は、段5・6を飛ばさない通常寄りの経路だったのに、実装差分ゼロだけを理由に変異登録なし・matrix免除で完了した。docs-onlyでも「実装しない」裁定に該当させる運用実績もある。

file:line 根拠: [brief.md:43–44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:43)、[s2-plan.md:89–93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:89)、[T-642 s4-adjudication.md:5–7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-08_t642-dw-s04-acceptance-scope/verbatim/s4-adjudication.md:5)、[T-642 README.md:3–10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-08_t642-dw-s04-acceptance-scope/README.md:3)、[archive 359:47–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/archive/worklog-phase3-0810-359.md:47)

成果物影響: T-765が自分の変更した免除規則で自分を免除すると、正しさ防壁を変更した最初のtip自身が変異台帳の事前登録・kill証拠なしで受理集合へ入る。今回最も危険な失敗である。

推奨対応: 段4で、文面適用前に `C=false`、通常経路、matrix非免除を変更不能な裁定として固定する。新文を本waveのbootstrap免除根拠に使わず、byte変異は「L1予算だけのkill」、意味等価性は「機械kill不能・敵対レビュー証拠」と分けて記録する。C=trueへ変えるなら停止して再裁定へ戻す。

### A4 — D237を単なる歴史記録として扱うと参照が分岐する

severity: must-fix

主張: T-642逐語は歴史記録だが、D237は現在も索引から引かれるcanonical decisionである。その見出しはZ単独十分条件に見え、T-642の実行記録も実際にZ単独免除だった。プランは両者をまとめて「歴史記録」として残すため、coreのC∧Zとdecision consumerが分岐する。

file:line 根拠: [D237:11131–11145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/decisions.md:11131)、[s2-plan.md:76–85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:76)、[CLAUDE.md:148–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/CLAUDE.md:148)

成果物影響: D237をprecedentとして読む将来managerはC=false・Z=true waveを免除し、coreを読むmanagerとは異なる受理集合と変異台帳を生成する。

推奨対応: D237やT-642を遡及改変せず、新しいdecision fragmentで「D237見出しは十分条件ではない」「現行は当該段4のC∧入口定義のZ」と前向きにsupersedeする。worklog／insightsだけに留めない。

### A5 — pin閉包の結論は正しいが、証拠の一般化がbriefに残っていない

severity: nit

主張: 現snapshotではS04本文のSHA・exact literal pinは見つからず、83→101 bytes、L1 10,606→10,624の算術も一致した。ただしbriefは、DW-O09が要求するkey側検索語とdurable manifestの未発行／再発行要否を記録していない。また現在は `HEAD=afdb499d` に対しlocal mainが `034d7590` まで進んでおり、「tip=main」は既にsnapshot限定である。main差分は今回の対象・checkerを含まないため、現時点の数値は変わらない。

file:line 根拠: [brief.md:31–38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:31)、[operations.md:49–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/operations.md:49)、[check_docs.py:431–438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:431)、[check_docs.py:552–556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:552)、[check_docs.py:3798–3801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/tools/check_docs.py:3798)

成果物影響: 現snapshotでは台帳値・受理集合・参照に差はない。再計測しないままmain側に対象変更が入れば、L1超過または未照合pinでlandが拒否され、記録値だけがstaleになる。

推奨対応: 段4とmain取込み後に再計測し、path側・`DW-S04`／逐語／role-key側検索、durable manifest状態を短く記録する。

## 攻撃したが破れなかった面

- 被免除物と受入全走: 推奨文は `変異 matrix だけ` を維持し、直後の受入全走非免除文を変更しない。ここは攻撃したが破れなかった。
- byte算術: 現行83 bytes、推奨101 bytes、L1 10,624 / 10,625を独立再計算して一致した。L1分類・上限値も一次コードと一致した。
- 義務の消失: `実装差分ゼロ`、`実装しない`、`裁定`、`変異 matrix`、`だけ` はすべて残る。単独で担っていた義務語の削除はない。問題は削除ではなく、`受けて`による関係追加と`実装差分`の未確定な射程である。
- 意味pin不在: 静的検索ではS04本文pinを発見できず、プランも意味変更をKILLEDと称していない。この点は破れなかった。

## 総括

blocker は3件あり、現プランはNO-GO。  
最も危険なのは、T-642の自己免除precedentと条件付きP2により、本T-765自身が変異証拠なしで受理される経路。  
`受けて`案を捨て、実装面定義・当該段4のC・本waveのC=falseを段4で固定する必要がある。