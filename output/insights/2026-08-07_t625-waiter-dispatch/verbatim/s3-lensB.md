静的レビューのみ実施した。read-only 制約のため pytest / `check_docs` は未実走である。

## Real 所見

### R1 — 待ち条件作成が発火集合から脱落している

- 主張: 計画の条件 24 は、`DW-C00` 第3条が実際に決まる「待ち条件の作成・変更」を覆わない。元の第3案には「待ち条件作成」が含まれていたが、裁定控えと段2プランで脱落した。待ち条件を先に組み立て、後で待ち手を生成する経路では再読が手遅れになる。条件行には少なくとも「待ち条件の作成 / 変更」を戻す必要があるが、裁定逐語を変えるため段4でユーザー再裁定が必要。
- 根拠: `docs/dev-wave/core.md:17-18`、`output/insights/2026-08-07_t597-dev-wave-budget/s6c-review.md:46-54`、`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:345-349`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:23-27`
- 成果物影響: `check_docs` の受理集合に「条件24は存在するが、生産者の死を含まない待ち条件を先に確定できる入口」が残り、対策済みと受理された wave でも無音待機を再発できる。
- 深刻度: blocker

### R2 — guard mutation は発火条件を一切守らない

- 主張: 提案テストが守るのは行24の存在と参照先だけで、変更の本体である発火条件セルではない。「通知処理」や「待ち条件作成」を削っても checker は受理する。段4では、発火条件 literal の pin と該当句を落とす mutation を追加するか、少なくとも「構造 guard に限定し、実効性は敵対レビューだけが担う」と受入主張を狭める必要がある。
- 根拠: `tools/check_docs.py:3147-3152,3179-3189,3894-3907`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:109-116`。意味保存を人間レビューへ委ねる現行方針は `docs/skill-self-improvement.md:83-84`。
- 成果物影響: `check_docs` の受理集合は、key/reference が正しくても発火条件が恒偽・不足・過剰な入口を引き続き含む。
- 深刻度: must-fix

### R3 — 効果を後から確認する成果物 field がない

- 主張: 現行 handoff、worklog、task-run、supervisor receipt のいずれにも、条件24の読了、条件数、待ち手生成数、producer-death 束縛、停止後の孤児数を記録する必須 field がない。brief の「worklog / 試行台帳から欠落する」は原因説明であり、変更後の観測手段ではない。最小案は canonical worklog の本文へ、条件ごとに `waiter_audit: producer=<id> condition=<digest> waiter=<id> creates=1 notifications=<n> death_bound=yes orphan_after_stop=0 evidence=<path>` を残すこと。恒久義務化は本 wave の3ファイル外なので、scope 外の裁定パッケージ候補とする。
- 根拠: `docs/handoff/README.md:15,22-36`、`docs/spool/worklog/README.md:17-21`、`tools/task_runs/schema.py:314-332`、`tools/dev_waves/schema_v2.json:7-20,21-119`
- 成果物影響: 実装前後で worklog・task-run・supervisor receipt の値が変わらず、「条件24が読まれ、三条が守られた」という台帳上の比較ができない。
- 深刻度: must-fix（scope 外・裁定パッケージ候補）

### R4 — key 件数の一般化が不正確

- 主張: 「空き key は24のみ」「既存23条件」は不正確。現行は22行で、07は欠番、25以降も未使用である。正しい結論は「07は裁定により再利用不可で、最大使用23の次の単調増加 key が24」。採用 key 自体は妥当。
- 根拠: `.claude/commands/dev-wave.md:84-105`、`tools/check_docs.py:371-374,497-505`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s1-brief.md:30,34`、同 `s2-plan.md:7-13`
- 成果物影響: key 24 の採用結果と受理集合は変わらない。brief の計数表現だけの誤り。
- 深刻度: nit

## Speculative 所見

### S1 — 「通知処理」が広すぎる可能性

- 主張: 「通知処理」が先行する producer / 待ち手に限定されていないため、あらゆる通知で `DW-C00` を読む解釈が可能で、L2を実質常読にする恐れがある。R1の修正時に「これらに関する通知処理」と限定するのが安全。
- 根拠: `docs/dev-wave/core.md:7-9`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t625-waiter-dispatch/s2-plan.md:23-25`
- 成果物影響: 現行成果物には読了回数 field がなく実害を測れないため、受理集合・台帳値への確定影響は示せない。
- 深刻度: nit

## 独立検証で成立した点

- `DW-C00` は共通 dispatcher 内では wave 開始だけに存在し、条件 dispatch にはない。`.claude/commands/dev-wave.md:60,80-105`
- 条件01との形式上の競合はない。`DW-O01` の codex job は背景 producer であり、読み込み契約は操作直前の条件再評価を要求するため01と24の双方が成立する。非Codexの land loop を覆う必要があるため、01への統合より別行維持が妥当。`.claude/commands/dev-wave.md:21-24,84`、`docs/dev-wave/operations.md:6-12`
- Codex Skill は条件表を複製せず共通 dispatcher と操作直前再読へ委譲しており、同期編集は不要。`.agents/skills/dev-wave/SKILL.md:14-15,21-23`
- `tools/dev_waves` の内側の wave は `/dev-wave` を起動するため同じ入口へ届く。外側 supervisor は別のコード経路だが、現行は単一 poll/selector と producer 死亡・停止処理を持つため、本 waveへコード変更を広げない。`tools/dev_waves/daemon.py:1185-1189,1267-1280,1345-1364`、`tools/dev_waves/worker.py:456-495,574-578`
- command 編集は自己改善契約の第3条件に該当する。dispatch の発火命令は常読入口に必要で、非Codex producer を条件01や reference 自身では発火できない。`docs/skill-self-improvement.md:39-50`

## 総括

blocker は1件あり、待ち条件作成への dispatch 脱落で三条目が届かない。  
現プランのままの採用は NO-GO。  
段4で条件文の再裁定と、発火条件を guard 対象にするかを決めて plan v2 を作るべき。  
観測義務は scope 外の裁定パッケージへ返す。  
テスト・checker は未実走。