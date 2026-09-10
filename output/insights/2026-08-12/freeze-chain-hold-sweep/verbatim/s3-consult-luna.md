# 段 3 敵対相談レポート

## 総括

判定は **BLOCK** です。

- BLOCKER: 4
- MUST-FIX: 4
- NIT: 1
- 本 wave 自身による wall 削減見積もり: **0 秒**
- land: **不可**

pytest、全走、編集、commit は行っていません。

## 所見

| ID | 分類 | 根拠 | 成果物への影響 |
|---|---|---|---|
| B1 | BLOCKER | `plan.md:50-57`, `orchestrator/tests/conftest.py:188-199,239-248`, `orchestrator/tests/test_real_repo_serialization.py:567-615` | 4 function / 5 node は `REAL_REPO_SERIAL_NODES` 外であり、`real-repo` marker を追加すると canonical golden と collection 検査が赤くなる。追加しなければ plan の指定自体が実行されない。 |
| B2 | BLOCKER | `brief.md:24-31`, `plan.md:50-71`, `orchestrator/campaign/s1_known_axes_freeze.py:863-879`, `orchestrator/campaign/s8b_holdout_freeze.py:873-880` | t816 の production hold と test skip の対応・positive control が未定義で、production が held なのに test が単に緑になる、または逆になる。certified 選択と hold report の意味が一致しない。 |
| B3 | BLOCKER | `handoff/dev-wave-growth-tests.md:103-112`, `tools/pegasus/dispatch_compute.py:57-66`, `orchestrator/tests/test_pegasus_dispatch_compute.py:2540-2577` | growth 側の解除 env は現在の計算ノード allowlist にない。ユーザーが明示解除しても dispatch 先では skip が残り、台帳・JUnit・受理集合が解除状態と一致しない。 |
| B4 | BLOCKER | `plan.md:52-58`, `growth-tests/plan-b.md:37-42,61-67,185` | `correctness_gate` の bool 型と期待値を検査せず、`False` や文字列を台帳へ入れられる。正しさゲートを保留した事実と user-facing report の値が改ざん可能になる。 |
| M1 | MUST-FIX | `plan.md:5,40-43`, `orchestrator/tests/conftest.py:188-199` | 対象 5 node は直列鎖外なので、保留しても受入 wall は短縮されず、受理集合だけ狭まる。これは純損失である。 |
| M2 | MUST-FIX | `plan.md:5,40-46`, `/dev-wave-jobs/.../baseline.xml` | `0.179 秒` は並列 JUnit の per-node 合計であり、与件が無効とした scheduler noise を再利用している。台帳の `measured_seconds` と効果説明が無効になる。 |
| M3 | MUST-FIX | `growth-tests/plan-a.md:74-81`, `plan.md:40-59`, `handoff/dev-wave-growth-tests.md:114-118` | growth wave の T793 entry と本 wave の 4 entry を統合した独立 manifest がなく、wave 間の漏れ・重複・同一 production 検査点の部分保留を検出できない。台帳の受理集合が実装者依存になる。 |
| M4 | MUST-FIX | `growth-tests/plan-b.md:133-164`, `orchestrator/tests/conftest.py:239-248` | 台帳整合検査は全 collected item を走査するため全体で O(T+H) であり O(1) ではない。テスト数の増加に比例して collection overhead が増える。 |
| N1 | NIT | `plan.md:40-43,54`, `growth-tests/plan-b.md:59` | `basename::function` は parametrize suffix を捨てるため、non-prefix の 2 node は台帳上 1 entry になる。受理集合は一致するが、ユーザー向け node 別一覧と `measured_seconds` の粒度が曖昧になる。 |

## wall 効果

対象 4 function の baseline 内訳は、計画値では次の合計です。

- duplicate: 0.011 秒
- unchanged history: 0.045 秒
- non-prefix: 0.041 + 0.041 秒
- delete/recreate: 0.041 秒
- 合計: 0.179 秒

ただし、これらは `@real-repo` 直列鎖に属していません。したがって本 wave が除く直列鎖コストは **0 秒**、wall 削減見積もりも **0 秒**です。baseline wall は 186.38 秒のままです。

growth wave handoff が報告する次の候補は `test_codex_reasoning_ab` の約 147.6 秒 node ですが、与件の per-node 雑音規則により上限の証拠には採用できません。本 wave の 4 件を保留しても、critical path は変わりません。

既存の `test_s8b_oracle_driver.py:624-677` の 6 function / 11 node 固定メタテストとは直接衝突しません。今回の 4 function はその consumer 集合外です。

## 総括

本 wave の現 plan は、直列鎖外のテストを保留して受理集合だけを狭め、wall を短縮しません。さらに、t816 の production hold、growth の test skip、解除 env、共有台帳の正しさが接続されていません。

したがって、B1-B4 と M1-M4 を解消し、3 wave 統合後の exact hold manifest と解除手順を確定するまで land 不可です。