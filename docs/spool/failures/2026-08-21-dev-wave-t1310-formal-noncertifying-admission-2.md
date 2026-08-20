---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t1310-formal-noncertifying-admission
seq: 2
---

## 新規

### {{F:mutation-harness-dispatch-collection-infra-failure}}. 変異harnessのcollection段階でPegasus dispatch自体がインフラ的に失敗した [手順漏れ]

- 事象: [T-1310] wave で `tools/mutation_harness.py --runner-mode dispatch` を2回投入したが、
  いずれも collection 段階の Pegasus dispatch が `receipt scheduler_logs.stdout.path がない`
  というインフラエラーで rc=16 になり、harness が fail-closed で abort した
  (`pytest collection が正常完了せず、期待 node の実在を証明できない`、作業ツリーは無害・
  実害なし)。queue 自体は ENA=ENA・STS=ACT で利用可能 (待ち48〜51・実行101〜103) であり、
  単純な queue 混雑ではなかった。
- 根本原因: collection 段階の dispatch job で scheduler 側の receipt 処理が完走せず、
  `scheduler_logs.stdout.path` field が欠落した (未確定: collection dispatch 特有の短時間・
  高頻度形状がこの経路を踏みやすい可能性があるが、本 wave では原因の深追いはしていない)。
  F431/F432 とは異なる原因 (pytest 自体の collection ERROR や出力切り詰めではなく、
  dispatch インフラそのものの一時的失敗) による、同じ症状 (harness が collection 段階で
  abort する) の3件目。
- 恒久対応: 既存 memory `mutation-harness-collection-error-needs-manual-verify` の代替手順
  (Edit → `tools/run_tests.py` 実走 → `git checkout --` 復元、を変異ごとに手動反復) を適用し、
  7変異すべてを KILLED・期待 node 完全一致で検証した。3回目の自動 retry はせず、2回連続の
  同一失敗で手動検証へ切り替えた判断が有効だった。
- 再発検知: 次に `mutation_harness.py --runner-mode dispatch` を投入して同じ
  `receipt scheduler_logs.stdout.path がない` エラーが出た時点で顕在化する
  (lint 化は未実装、目視)。

### {{F:acceptance-inflight-worktree-write-near-miss}}. 受入投入後の待機中にworktreeへfragmentファイルを書きかけた near-miss [手順漏れ]

- 事象: [T-1310] wave で受入全走 (`tools/dev_wave_wait.py acceptance`) を投入した直後、
  待機を有効活用しようとして decisions/failures の spool fragment 2 件を worktree 内へ
  作成した (untracked file)。作成後に「受入 command が返った後、child rc を評価する前に
  postrun-clean / index flag / fingerprint 比較を行う。木が変わっていれば rc=70 が child rc
  に優先する」(`docs/pegasus-runbook.md` §7.3) という制約に気づき、直ちに repo 外へ退避して
  tree を clean へ戻した。受入 command (`tools/run_tests.py`) 自体は投入から4分程度しか
  経過しておらず、実際に postrun-clean が走る前に是正できた可能性が高いが、確証はない
  (受入自体は別 attempt で `verdict=child-green`、`pre_fingerprint`/`post_fingerprint` の
  `diff_bytes: 0` で無事完走した)。
- 根本原因: 「長時間待機中は独立な解析・検証・合成・文書を進める」という一般則
  (CLAUDE.md 作業の進め方 9) を、受入全走という**特殊な待機**(投入後の tree 不変が受入の
  成否条件そのもの)に無条件で適用した。一般則の例外条件が明示されていなかった。
- 恒久対応: 未着手 (本 wave の scope 外)。候補は「受入投入後は明示的に release されるまで
  worktree 内・repo 内 (spool fragment を含む) への書き込みを禁止する」を `DW-O18`/
  `docs/pegasus-runbook.md` §7.3 のいずれかへ明記すること。dev-wave 改善候補として段8で
  裁定する。
- 再発検知: 次に受入投入後の待機中に repo 内書き込みを行い、postrun-clean 由来の rc=70 が
  観測された時点で顕在化する (lint 化は未実装、目視)。

## 再発

### F50

- **再発: 2026-08-21** — [T-1310] wave (背景 job + worktree 隔離) で、段1 brief 直後に専用
  handoff を worktree 内 `docs/handoff/` へ誤って作成した (untracked file)。加えて、条件13
  (`DW-O13`、gate・検証を新設する可能性、最遅読了=段2プラン前) の発火判定も段2着手前に
  能動チェックせず、段2完了後に気づいた (DW-O13 が要求する実質的検証 — 入力の実在確認 — は
  段2 codex プラン自体が実コードの file:line 引用で徹底していたため、段2への巻き戻しはせず
  実質的に満たされていると判断した)。段4裁定完了直後に `tools/check_wave_startup.py` を
  実行して初めて handoff 誤配置と HEAD が local main から60 commit 遅れていることの両方を検出し、
  是正した (repo外への移動+`--external-handoff`再検査、`git merge --ff-only`、実害なし)。
  過去3回 (2026-07-29, 2026-08-03, 2026-08-19) の再発、特に直近 (2026-08-19) と同じ
  「wave 開始時に条件 dispatch 表そのものを能動的に辿らない」という根本原因が今回も再現した。
  F50 の恒久対応 (dispatch 前倒し・条件表20番の文言是正・`dev-wave-bg-worktree-startup-checks`
  立ち上げ3点検査 memory) は 2026-08-19 時点で既に適用済みだったにもかかわらず、4回目の
  再発が起きたことは、**恒久対応が「読むべき節を知っていること」に依存しており「読むべき
  タイミングで実際に読む」ことを機械的に強制していない**構造的限界を示す。
