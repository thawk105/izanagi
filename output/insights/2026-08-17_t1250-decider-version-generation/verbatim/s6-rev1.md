## R1

**主張:** 事前登録した M01・M02・M05 の期待失敗 node 集合は実際の mutation harness と一致しない。さらに g4 変異は履歴検査に先に遮られ、新設関数 1 の版 assert の検出力を証明できない。must-fix。

**根拠:** candidate fixture は固定 HEAD を親として、変異済み worktree を子 commit にする。[test_s8c_preregistration_invariant.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:90) [test_s8c_preregistration_invariant.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:93)

harness も固定 HEAD の bytes を worktree に変異させてからテストを起動する。[mutation_harness.py:1747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/mutation_harness.py:1747) [mutation_harness.py:1789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/mutation_harness.py:1789)

したがって、着地後 HEAD に既に存在する g4 を変更する M01・M02・M04・M05 は、親と candidate で g4 の blob OID が異なる。履歴検査は同一世代に複数 OID を見つけた時点で `generation-mutated` を送出する。[s8c_preregistration.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1425)

関数 1 はそれを report の freeze invalid に変換し、版比較へ到達する前の `condition_freeze_valid` で失敗する。[s8c_preregistration.py:1683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1683) [test_s8c_preregistration_invariant.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:171)

同じ理由で既存 `test_candidate_freeze_matches_contract_and_generation_chain` も失敗する。[test_s8c_preregistration_invariant.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:132) これは M01・M02では未登録の失敗 node、M05では既存テストと関数 1 の双方が未登録の失敗 nodeになる。[s4-adjudication.md:116](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s4-adjudication.md:116) [s4-adjudication.md:120](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s4-adjudication.md:120)

静的に予測される集合は次のとおり。

| 変異 | 関数 1 | 関数 2 | 既存 candidate 検査 |
|---|---|---|---|
| g4 schema v1・版削除 | line 171、履歴 mask | line 230 | line 132 |
| g4 `decider_version` 変更 | line 171、履歴 mask | line 231 | line 132 |
| g4 `supersedes` 変更 | line 171、履歴 mask | line 228 | line 132 |
| doc 追記取消 | line 171、protected mismatch | 失敗しない | line 132 |
| §6 と g4 hash の整合的変更 | line 171、履歴 mask | line 208以降 | line 132 |
| `DECIDER_VERSION` のみ bump | line 184 | line 231 | 失敗しない |

**成果物への影響:** このままでは M01・M02・M05 が `KILLED` でなく `MISMATCH` になり、変異台帳と受入 proof chain は新設版検査の検出力を証明できず、certified な着地集合へ入れられない。

**推奨対応:** 期待 node の追加だけでは mask を追認するため不十分。`DECIDER_VERSION` 単独 bump を登録して、freeze valid のまま関数 1 の版比較へ到達させる。g4 field の検査は、g4 が初めて導入される synthetic history、または関数 2 だけを対象にした独立変異で検証する。M01・M02・M05 の事前登録には erratum が必要。

## R2

**主張:** 関数 2 は世代番号の固定自体ではなく、歴史的 g4 を現在の可変定数へ比較しているため、正当な g5 の判定器版 bump を機械的に拒否する。must-fix。

**根拠:** g4 の schema と版を、歴史的 literal ではなく現在の `SCHEMA_VERSION`・`DECIDER_VERSION` と比較している。[test_s8c_preregistration_invariant.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:230)

producer は新世代 record に現在の両定数を記録する。[s8c_preregistration.py:1817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1817) 条件の意味を変える正当な g5 では `DECIDER_VERSION` を v2 へ bump し、g4 は不変の v1 のまま残す必要がある。その状態で line 231 は必ず失敗する。

g3・g4の番号固定と contract hash の比較は正しい。これを tip 相対の g4・g5比較にすると、正当に変えた条件 hash の相異を拒否するため、そちらも不適切である。

**成果物への影響:** 正当な g5 発行時に受入集合が空になり、activation report の `freeze_generation`、certified 選択が参照する事前登録世代、レポート・台帳の版参照を g5へ進められない。

**推奨対応:** g4 の歴史的事実として、line 230・231をそれぞれ literal `"s8c-prereg-condition-freeze/v2"`、`"s8c-decider/v1"` に固定する。g3・g4の継続性比較は番号固定のまま維持し、現行 tip と現行定数の照合は関数 1だけに担わせる。

## R3

**主張:** 新しい `report.effective is False` は将来の正当な発効時に更新が必要な temporal assert だが、既存同型 assert と受理集合が完全に重複する。nit。

**根拠:** 新設 assert は [test_s8c_preregistration_invariant.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:188)、既存 assert は [test_s8c_preregistration_invariant.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:276) にある。発効値は freeze、版一致、§5、12条件の conjunction で導出される。[s8c_preregistration.py:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1753)

**成果物への影響:** nit。現時点の受理集合への追加影響はない。将来の正当な発効手続きで更新対象が1箇所増えるだけで、既存 assert が既に同じ発効状態を拒否する。

**推奨対応:** 今回の「版束縛だけで偶発発効しない」という裁定を優先するなら維持してよい。将来の発効作業では両 assert を同時に再裁定する。重複負債を避けるなら、裁定を更新したうえで新設側を除く。

## 恒真性・弱体化の確認

`section6_condition_hashes` は JSON の list of dict を検証後、各 record ごとに独立した `tuple[tuple[int, str], ...]` へ変換する。[s8c_preregistration.py:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1090) [s8c_preregistration.py:1124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1124) 関数 2 は別々の g3・g4 bytes をロードして比較しており、同一入力から導いた同一値の自己比較ではない。12件の長さ assert は loader と重複するが恒真化の原因ではない。

差分はテスト追加だけで、既存期待値の反転・緩和・skip・削除はない。legacy parametrize は `(1, 2, 3)` のままである。[test_s8c_preregistration_invariant.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:234)

pytest は実走していない。上記は `dev-wave` の変異 mask と完全失敗 node 契約に沿った静的結論である。

## 総括

must-fix:

- R1: g4変異が履歴不変検査に mask され、M01・M02・M05の期待 node 集合と検出力証明が成立しない。
- R2: g4を現在の `DECIDER_VERSION` に比較するため、正当な g5版 bumpを拒否する。

nit:

- R3: `effective is False` は既存 assert と受理集合が重複し、将来の更新箇所だけを増やす。