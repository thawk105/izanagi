指定の変異 spec を作成しました。

- 出力: [mutation-spec.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/output/insights/2026-08-17_t190-launcher-failure-artifact/mutation-spec.json)
- 変異数: 15件（M01〜M14、P01）
- 1 run 見積り: 360秒
- timeout / hang timeout: 各900秒
- SHA-256: `f4825b976e6ec378d504d346a07ebe66945a428506315846588753f49520cb9a`
- 作成・編集した file: 上記1 fileのみ
- `git log --oneline -3` で修正 commit `0d1d92cd` が現行 HEAD に含まれることを確認済み

`old` の一意性は、書き込み前に候補の完全な複数行文字列を現行 source に照合し、書き込み後にも JSON から各 `old` を再抽出して raw bytes で再検査しました。改行を含む byte exact count は次のとおりです。

- M01: 1
- M02: 1
- M03: 1
- M04: 1
- M05: 1
- M06: 1
- M07: 1
- M08: 1
- M09: 1
- M10: 1
- M11: 1
- M12: 1
- M13: 1
- M14: 1
- P01: 1

対象2 source の CR byte はともに0でした。各変異をメモリ上で適用した後の Python AST parse も全15件成功しています。

expected_nodes の導出

共通 prefix は `orchestrator/tests/test_codex_worker_launch.py::` です。全 node は `grep -n "^def test_xxx"` で実在と一意性を確認しました。

- M01: 正常終了時の `evidence_forced_stop is False` assertion。
- M02: P3 exact-limit の空集合、limit helper の below/exact、site別集合、receipt staging/audit 後の wall-only 集合を検査する5 node。
- M03: production `_attempt_loop` を制御 clock で通し、8 phase の exact duration を比較する node。共通 `note_boundary` の直接単体 test は変異しない設計です。
- M04: `_terminate` の unknown callback と、強制停止 sidecar の `pid_identity_unavailable` を検査する2 node。
- M05: hook属性の `tryfirst=True` と、子 pytest で実際の bundleを要求する live wiring の2 node。
- M06: sentinel/receipt exact bytes、2回退避の内容、copy error omission、critical file優先、live wiring sentinelを検査する5 node。
- M07: 同一 nodeid の2回退避で2 bundleと異なる payloadを要求する node。
- M08: receipt競合で `sealed` と `foreign` の両方を要求する node。
- M09: `path-map.json` を読み、元 receipt pathとの対応を検査する node。
- M10: archive root障害でも元の `LauncherReturncodeMismatch` が残り、`INTERNALERROR` が出ないことを検査する live node。
- M11: launcher送信 signalがある強制停止で主体 flagを `True` と要求する3 node。signalなし負例は `False` のままなので落ちません。
- M12: ValueError型 statと短い malformed statの双方で flagを `True` と要求する2 node。
- M13: `index.jsonl` が1 file、1 recordで正しい nodeidを持つことを検査する node。
- M14: natural-exitの comparisonが `>` であり、exact limitの集合が空であることを検査する2 node。
- P01: writerの `OSError` 後も rc 0、`accepted=True`、receipt exact bytesが不変である正例 nodeを `PASSED` 対象として登録。

単一理由性は全15件で確認できたため、除外した変異はありません。M03は production配線だけ、M10は実 hookの外側例外境界だけを変異させ、レビューで指摘された過剰または恒真的な anchorを避けています。

段6 fix子の完全集合との食い違いはありません。P01については、fix報告の「失敗 nodeは空集合」と整合しつつ、specでは通過を要求する正例 nodeを `expected_nodes` に記録しています。

注意点として、現行 [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact/tools/mutation_harness.py:36) の `EXPECTED_STATUSES` はまだ `PASSED` を受理しません。今回はユーザー指定を優先してP01を `PASSED` としました。親が現行 harnessをそのまま使う場合は起動前に拒否されます。テストおよび mutation harnessは指示どおり実走していません。

## 総括

M01〜M14と正例P01の全15件を、現行 HEADの一意な byte exact anchorと静的に確認した完全 node集合で1本のspecへ記録しました。