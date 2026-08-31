---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2060-current-closure-unknown
seq: 1
---

## 新規

### {{F:new-report-field-invalidates-saved-artifacts}}. 成果物へ新 field を足すと、保存済み成果物との byte 比較が壊れる [ドリフト] [手順漏れ]

- 事象: 歴史 Layer 3 report へ top-level field を 1 つ足したところ、
  `autonomous_trial_completeness.py` の「保存済み report と `build_report` の再構築を
  `_canonical_bytes` で byte 比較する」経路が、**同 field を持たない保存済み report をすべて
  拒否する**状態になった。`output/campaigns/` の保存済み report 7 件はいずれも同 field を持たない。
  段 6 の敵対レビュー 2 本はどちらもこれを指摘せず、親がレビュー B の「焦点走の漏れ」を追跡して
  実測で発見した。
- 根本原因: producer に field を足す変更を、**同じ producer の出力を過去分と突き合わせる
  consumer の互換層まで閉じずに**行った。当該 consumer には既に
  `include_epoch` / `include_verifier_assessment_basis` という legacy omission の正規化機構が
  あり、**新 field はそこへ登録されていなかった**。
- **テスト色では見えない型である。** テスト内で保存済み side を同じ producer で作れば両側に
  field が付いて緑になる。壊れるのは実成果物だけであり、焦点走も受入全走も緑のまま通りうる。
- 恒久対応: 既存の legacy omission 正規化と同型の flag を 1 つ増やし、保存済み側に field が
  無ければ両側から落とし、有れば厳密比較を維持した。回帰は
  `orchestrator/tests/test_autonomous_trial_completeness.py` の正例・負例 2 node が守り、
  変異 `M3-PERSISTED-COMPARISON-NORMALIZATION-REMOVED` が同 1 node だけで KILLED になることを
  実測した。
- 再発検知: producer の出力 shape を変える wave では、その出力を**過去分と突き合わせる
  consumer**を参照関係で引き、legacy omission の正規化機構があるなら新 field を登録したかを
  確認する。保存済み実成果物を 1 件開いて top-level key を数えるのが最も速い。

### {{F:acceptance-depends-on-expiring-home-sessions}}. 受入全走が、保持期限で消えるホーム配下の実 session に依存していた [テスト代表性] [手順漏れ]

- 事象: [T-2060] の受入全走が `21 error, 5 failed, 19043 passed, 67 skipped` で赤になった。
  赤は全件 `orchestrator/tests/test_codex_reasoning_ab.py` で、本文は
  `session 019fac6b-... rollout count is 0, expected 1` (21 件) と
  `FileNotFoundError: /home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-...jsonl`
  (5 件のうち 4 件) である。
- 根本原因: 同 test file は `_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")` と
  **repo 外のホーム配下 directory を絶対 path で焼き込み**、2026-07-29 の実 rollout を読む。
  この directory は Codex 側の保持期限で失効する。実測すると
  `/home/SFC/tanab/.codex/sessions/2026/07` は**空**で、親 `2026/` の mtime は
  **2026-09-01 00:54:20 JST** — 当日の受入投入 (01:52) の約 1 時間前に 07 が削除されている。
  残るのは `08` (31 日分) と `09` だけで、**日ごとに失効が進む**。
- **これは特定 wave の問題ではない。** 期限切れ以降に受入全走を投げるすべての wave が
  同じ赤を受け取る。00:54 より前に着地した wave が緑だったのは、失効前だったからである。
- 恒久対応: **未定 (ユーザー裁定待ち)。** 親は次のいずれも行わなかった —
  テストの弱体化、`flaky_test_holds.py` への登録 (DW-O18 は main 既存 F を証拠に要求し、
  本件に該当する F は存在しない)、決定的な赤に対する受入再走 (lease 窓を捨てるだけである)。
- 再発検知: 受入の赤が `test_codex_reasoning_ab.py` に集中し、本文が
  `~/.codex/sessions` の path を含むなら、まず当該日の directory の実在を確かめる。

## 再発

### F1

- **再発: 2026-09-01** — [T-2060] wave の親が、進捗報告 4 件と handoff の最終更新に書いた JST 時刻を
  1 度も `date` で実測せず、子の投入からの経過を体感で足して書いた。ユーザーの「待ちすぎていないか」
  という指摘を受けて初めて `date` を実行し、直前の報告に書いた「00:28」が実測 00:21 より
  7 分先行していたことが判明した。同報告が説明している段 5 実装子の投入は job log の mtime で
  00:19 であり、報告時刻は実際より 7〜9 分進んでいた。2026-08-23 の再発が定めた
  「時刻を書く 1 回ごとに `date` を実行する」を、**wave の途中からではなく最初から一度も
  実行しなかった**点が新しい。原因は、wave 開始時に時刻を測る手順を起動列へ入れず、
  最初の報告の時点で推定値を書き、以後それに加算したことである。恒久対応は変更なし。
  **時刻を書く 1 回ごとに `date` を実行する。過去の推定値への加算は実測ではない。**
