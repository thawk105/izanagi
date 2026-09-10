## 所見ごとの対応表

| 所見 ID | 判定 | 根拠 (file:line) |
|---|---|---|
| レビュー A（0 件維持） | `closed` | fix の production 変更は 0 件。追加は mutation 対応表と M7 専用 test のみ。[test_codex_reasoning_ab.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:65)、[同:13660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13660) |
| RB1 | `closed` | 専用 test 本体の assert は 1 個。[test_codex_reasoning_ab.py:13697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13697)。spy は受領値を記録後、実 loader へ全引数を委譲する。[同:13671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13671)、[同:13681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13681)。M7 対象は loader 呼出境界。[codex_reasoning_ab.py:11207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11207) |
| RB2 | `closed` | M8 の production reason と診断 test は fix 前から不変。[codex_reasoning_ab.py:9394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9394)、[test_codex_reasoning_ab.py:13749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13749)。fix 前後で production patch 部分の SHA-256 も一致。 |

## RB1 の単一理由性

静的には M7 の帰属が成立しています。

- 専用 test 関数内の assert は 13697 の 1 個だけです。AST でも 1 個と確認しました。
- 共有 fixture 内には別途 `assert schedule_reasons == []` がありますが、これは fixture 構築中の [test_codex_reasoning_ab.py:13537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13537) です。fixture は `_replay_manifest` を呼ばないため、M7 の変更によってこの assert が先に赤になることはありません。
- M7 では `_replay_manifest` の loader 呼出引数だけが組込み manifest に変わります。spy は呼出前に値を記録し、実 `_load_adjudication` へ委譲します。
- 組込み manifest は POS/NEG、外部 fixture は alpha/beta なので digest は異なります。[codex_reasoning_ab.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:265)、[test_codex_reasoning_ab.py:13218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13218)
- 実 loader は digest 不一致を例外ではなく reason として蓄積します。[codex_reasoning_ab.py:9266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9266)。verdict 検査と slot dimension 検査の `ValidationError` も捕捉されます。[同:9322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9322)、[同:9928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9928)
- loader 後の `_replay_manifest` は verdict 内容を参照せず、reason を追加して返ります。[同:11215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11215)。したがって M7 固有の内部例外が最終 assert を先取りする経路は見つかりません。
- spy の既定値 `TOOL.TASK_MANIFEST` は M7 を隠しません。M7 は keyword を削除せず、組込み manifest を明示的に渡す変異なので、既定値は使われません。[test_codex_reasoning_ab.py:13678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:13678)

## 回帰検査

fix 前後の差は次の範囲だけでした。

- mutation 対応表から M7 を既存 node との共同所有から外し、専用 node へ付け替え。
- M7 専用 test を 1 本追加。
- 差分は正味 43 行。既存 test 本体と production の変更はありません。
- fix 前後の production patch 部分は同じ SHA-256 `c874b66bce597ead0f6ab246046fd08df57d6f00450a9f96d89e7a89411f9a88` でした。
- 現在の tracked `git diff` は提示された post-fix patch と同じ SHA-256 `f82a6efdb66f67bfaeefc53fce19ed2966c55fdf57c1d95f17372496a8583809` です。
- assert 削除、期待値反転、skip、xfail、approx、既存 test 削除はありません。
- `git diff --check` は無出力、対象 2 ファイルの AST parse は成功しました。
- 未追跡の `output/insights/2026-08-27_t1434-adjudication-task-oracle/` は tracked patch の外に残っています。fix 報告では開始時から存在したものとされています。

RB2 については、pre-fix の M8 test と production hunkが post-fix でも同一です。親裁定どおり、診断 sensitivity pin のままです。

## 残る所見

**無し。**

所見なしと判断した範囲は次のとおりです。

- fix 前後 patch の全差異。
- 現在の tracked worktree と post-fix patch の一致。
- M7 専用 test の assert 数、spy の委譲、既定値、外部 manifest の識別性。
- M7 変異時の `_load_adjudication` と、その後の `_replay_manifest` の制御経路。
- M8 の production reason と malformed-dimensions test。
- production 全 hunk、既存 test の期待値、skip・xfail・approx・削除の有無。
- growth-hold 登録と完全収集検査。新 node は既存 hold 台帳の対象を変更しません。
- real-repo fixture 閉包、receipt memo、oracle environment の静的 inventory。新 node は対象 fixtureや consumer APIを追加していません。

pytest は実走していません。緑とは報告しません。Web は使用していません。

## 総括

**GO**

RB1 は単一理由の M7 境界 pin として閉じています。RB2 は裁定どおり無変更です。新しい must-fix 所見はありません。