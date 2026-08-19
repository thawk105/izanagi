---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-orphan-branch-carry-sweep
seq: 2
---

## 新規

### {{F:carry-stub-cross-id-drift}}. worklog carry stub は、実装・解決が別ID/別waveのprovenanceでlandした後も自動更新されない [ドリフト] [手順漏れ]

- 事象: 2026-08-20の棚卸しで、carry上「新規」「未実装」「未land」と表示されていた
  [T-1419]/[T-1183]/[T-949] の3件が、実際にはすべて既にmainへland済みだったと判明した。
  [T-1183] は origin (entry578) とは別ID ([T-1140]/[T-330]、commit `6eb77ef9`) の実装で
  満たされ、[T-949] は origin (entry510) の裁定 (cherry-pick -x) とは異なる、より後発の
  直接ユーザー指示による branch 破棄+選択的資産保全 (commit `505accdb`) で解決していた。
  いずれの closing commit も、閉じたはずの carry ID 自体を引用・更新しなかった。
- 根本原因: `docs/spool/README.md` の fold 機構は「触れなかった active な T は自動的に carry
  する」設計であり (D70 保存則)、これは脱落を防ぐには効くが、**当該IDへ言及しないまま
  別ID・別waveの成果がその実体を満たしてしまうケースを検出しない**。carry stub の文言は
  「最後にそのIDへ言及したentryの文言」を機械的に運ぶだけで、指す作業が実際に未完了かは
  検証しない。
- 恒久対応: memory `carry-stub-can-outlive-landed-implementation` — 次タスク選定・裁定復唱で
  P1候補を最終候補に選ぶ前に、(a) 対象fileへの直接grep、(b) `git log --all
  --grep='[T-ID]'`、(c) 対象branch名が non-merged 一覧に見えるか、のいずれかで実体確認する。
  機械lintは未実装。
- 再発検知: 現状は目視 (実体確認の手順) のみ。ID単位で closing commit との対応を機械検査する
  lint は無く、次に同型が見つかった場合の再発記録がその lint 化の着手判断材料になる。
