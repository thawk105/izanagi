静的敵対レビュー結論: 現推奨案は NO-GO です。`受けて` が同一 wave の条件を固定せず、曖昧さが残ります。編集・pytest・実測はしていません。

### 所見1

severity: blocker

主張: 推奨文の `裁定を受けて` は論理積ではなく、主語・時系列・因果を曖昧にする。

file:line 根拠: [s2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:26)、[s2-plan.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:44)、[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/dev-wave/core.md:79)、[dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:49)

「wave が裁定を受け、その後ゼロ差分になった」「親が裁定を受けた結果、別のゼロ差分 wave を免除する」「裁定とゼロ差分に因果・時系列が必要」の読みが残る。プラン自身も `て` の時系列・因果性を認めているため、「曖昧さのない」条件を満たさない。

成果物影響: 誤った wave または Z 単独の wave の変異 matrix が免除され、変異台帳の kill/receipt 参照が欠落する。次文が残る限り受入全走の直接免除は起きないが、検証証拠なしの wave が受理記録へ入る。

推奨対応: 同一 wave への係りを受動態で固定する。

`免除は「実装しない」と裁定された実装差分ゼロの wave の変異 matrixのみ。`

これは UTF-8 100 bytes です。

### 所見2

severity: must-fix

主張: 次点案の `「実装しない」裁定かつ実装差分ゼロの wave` も安全な fallback ではない。

file:line 根拠: [s2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:48)、[s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:55)

`かつ` は「裁定」と「wave」を並列するだけで、裁定条件が同じ wave に掛かることを保証しない。`裁定` を独立した判定、`実装差分ゼロの wave` を別対象と読む余地が残る。

成果物影響: C 条件が別 wave の裁定に結び付くと、変異 matrix の免除集合と台帳参照が分岐する。

推奨対応: 次点案として採用せず、所見1の受動態案へ統一する。

### 所見3

severity: must-fix

主張: brief の P1 は `実装差分` の定義をコード・テストに狭めている。

file:line 根拠: [brief.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:42)、[dev-wave.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:34)、[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:67)

正本の実装面には probe、harness、script、機械設定も含まれる。P1 のままだと、それらに差分があっても `Z=true` と誤判定できる。

成果物影響: 将来 wave の変異台帳から必要な検証行が欠落し、検証不足の契約変更が受理集合・certified 参照へ流入する。

推奨対応: P1 と段4記録では、実装面全体を `実装差分` の判定対象とする。今回の wave は「docs 本文以外の実装面差分なし」と限定して記録する。

### 所見4

severity: must-fix

主張: 親 brief の「T-786 の段2が (ii) を採った」は一次資料より強い。

file:line 根拠: [brief.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:19)、[T786 s2-plan.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-11_t786-docs-budget/verbatim/s2-plan.md:3)、[T786 s2-plan.md:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/output/insights/2026-08-11_t786-docs-budget/verbatim/s2-plan.md:190)、[worklog.md:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/docs/worklog.md:1776)

T-786 段2は一般化案を候補として提示したが、同時に「非等価」「安全裁定まで確定不可」と明記している。段3レンズAが blocker 判定した、という後半は正しい。

成果物影響: 現在の受理集合の数値は直ちには変わらないが、brief・insight・worklog の authority が食い違い、段4が「既に採用された読み」を前提に誤裁定する参照分岐が生じる。

推奨対応: 「(ii) を採った」ではなく、「(ii) に基づく一般化案を候補提示したが、段2自身が非等価と認め、段3Aが blocker とした」と訂正する。

### 所見5

severity: must-fix

主張: P2 の `C=false` は、docs 編集だけでは確定しない。

file:line 根拠: [brief.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:43)、[s2-plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:89)、[dev-wave.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:35)、[dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t765-exemption-wording/.claude/commands/dev-wave.md:49)

C は「docs を編集したか」ではなく、段4で `実装しない` 経路を裁定したかで決まる。docs-only の親編集自体は正本で許可されている。焦点レビューを計画したことも C=false の証明にはならない。

成果物影響: `4→7→8→9` と通常経路の記録が誤り、変異台帳の有無・受入 receipt の参照が不一致になる。

推奨対応: 段4で C=false を明示裁定し、その根拠を「本 wave は規範文を置換する通常経路」と記録する。docs-only であることだけを根拠にしない。

### 所見6

severity: nit

主張: より安全な受動態案は、プランの101 bytes案より1 byte短い。

file:line 根拠: [s2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/s2-plan.md:26)、[brief.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t765-exemption-wording/brief.md:33)

`免除は「実装しない」と裁定された実装差分ゼロの wave の変異 matrixのみ。` は100 bytesで、L1 は `10,623 / 10,625`、余白2 bytesになる。

成果物影響: 受理集合・台帳・参照は変わらず、L1値だけが10,624から10,623へ下がる。

推奨対応: `だけ` より `のみ` が許容されるなら、この100-byte案を採用する。

## 攻撃したが破れなかった面

- UTF-8算術は正しい。現行83 bytes、推奨101 bytes案はL1 10,624、次点95 bytes案はL1 10,618、104-byte変異はL1 10,627で上限超過。
- 次文の「受入全走は免除せず」は維持され、`4→7→8→9`、`DW-M01`〜`DW-M08`、通常段6の受入義務との直接矛盾は見つからない。
- `docs/skill-self-improvement.md:48`〜`50`の安全義務を予算理由で弱める変更や、新しい機械 gate・定義の持込みは確認できない。
- `matrix` を免除対象とし、受入全走を除外しない構造自体は破れなかった。既存 checker が本文意味を pin しない点も、プランは semantic mutation の KILLED と誤記していない。

## 総括

blocker あり。最も危険なのは `受けて` が裁定条件を同一 wave に束縛せず、免除範囲を再び誤読可能にする点です。  
算術と次文の非免除は破れませんでしたが、文面・P1/P2・T-786の履歴記述を修正してから段4へ進むべきです。