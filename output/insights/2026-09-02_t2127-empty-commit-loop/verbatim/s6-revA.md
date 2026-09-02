## 受理集合の検査

静的検査では受理集合の拡大は見つからなかった。

- `_inspect_campaign` が返した campaign 全体の `records` を、そのまま新 helper に渡している (`orchestrator/campaign/artifact_admission.py:1302,1313-1316`)。
- helper は同じ `records` オブジェクトを内側の `require_persisted_certified_commit` に渡す (`orchestrator/campaign/artifact_admission.py:777-783`)。segment、window、variant 単位への縮小はない。
- 従来の証拠探索 `records[:commit_index]` と receipt 完全一致も不変 (`orchestrator/campaign/artifact_admission.py:703-709,761-768`)。
- `CertifiedCampaignView.__post_init__` の追加条件は型、非負、件数一致という追加拒否だけ (`orchestrator/campaign/artifact_admission.py:376-395`)。
- `require_certified_commit_evidence` は既存の exact 型検査を先に通し、0 件だけを追加拒否する (`orchestrator/campaign/artifact_admission.py:1359-1377`)。

## 恒真な保証の検査

件数一致検査は、production 発行経路では同じ records から二重導出されるため恒真であり、独立した証拠検査ではない。

実装はこれを独立防壁として扱っていない。class docstring は view 自体が commit の存在を保証しないと明記し (`orchestrator/campaign/artifact_admission.py:331-335`)、実際の証拠検証は scan 内の単数 helper 呼出 (`orchestrator/campaign/artifact_admission.py:772-785`)、存在保証は consumer helper (`orchestrator/campaign/artifact_admission.py:1368-1377`) が担う。追加 test 名も snapshot 件数不一致の検査として記述されている (`orchestrator/tests/test_artifact_admission.py:1750-1754`)。

独立した証拠検査と誤認させるコメント、docstring、test 名は見つからなかった。

## テスト弱体化の検査

既存期待値の反転、緩和、削除、skip、xfail 化は見つからなかった。

裁定指定の Layer3 4 test は名前と命題を維持し、共通 `_certifying_campaign` が正当な `build_done`、`verify_done`、receipted commit を追加している (`orchestrator/tests/test_layer3_report.py:245-298,1882-1912,1940-1958,1990-2020,3286-3330`)。

追加された contract SHA は fixture lock の authority から取得した値であり (`orchestrator/tests/test_layer3_report.py:280-292`)、validator 自己 SHA や揮発的な期待 payload の固定値ではない。

## 2 命題の独立性の検査

MF-4 の二命題は静的には独立している。

- admission 命題は既存 `test_persisted_commit_gate_accepts[no-commit-campaign]` が production admission の成功と count 0 を直接確認する (`orchestrator/tests/test_artifact_admission.py:1310-1379`)。
- helper 命題は production admission を使わず private zero-count view を構築する (`orchestrator/tests/test_artifact_admission.py:1686-1721`)。
- private view の構築は `pytest.raises` の外で完了し、raises 範囲は helper 呼出だけ (`orchestrator/tests/test_artifact_admission.py:1724-1733`)。

したがって admission の誤拒否を helper の拒否として取り違える経路はない。

## 変異事前登録との対応

| 変異 | 静的対応 |
|---|---|
| M1 | 一意な内側呼出は `artifact_admission.py:779-783`。kill node は `test_artifact_admission.py:1212-1294` に実在。 |
| M2a | filter は `artifact_admission.py:778`。除去時は非 COMMIT が単数 helper の型拒否へ入り、正例 node `test_artifact_admission.py:1174-1192` が落ちる。 |
| M2b | 件数加算は `artifact_admission.py:784`。全 records 件数化は `artifact_admission.py:389-395` の snapshot 整合で検出される。 |
| M3 | 投影位置は `artifact_admission.py:1313-1333`。count 1 固定は no-commit admission node `test_artifact_admission.py:1310-1379` が検出する。 |
| M4 | exact int 条件は `artifact_admission.py:380-384`、node は `test_artifact_admission.py:1736-1742`。ただし RA-01 の重複拒否がある。 |
| M5 | snapshot 一致条件は `artifact_admission.py:389-395`、private mismatch node は `test_artifact_admission.py:1750-1754`。 |
| M6 | zero 条件は `artifact_admission.py:1372-1376`、private helper node は `test_artifact_admission.py:1724-1733`。 |
| M7 | replay 配線は `orchestrator/campaign/replay.py:184-187`、consumer node は `orchestrator/tests/test_bench_first_real_wal.py:359-391`。 |
| M8 | Layer3 配線は `orchestrator/campaign/layer3_report.py:742-752`、consumer node は `orchestrator/tests/test_layer3_report.py:1915-1937`。 |
| M9 | admission branch は `artifact_admission.py:1312-1334`。no-commit admission nodeに加え、zero-commit probe view を使う `p3_b4_wiring_probe.py:1453-1497` と positive baseline test `test_p3_b4_wiring_probe.py:1026` が実在する。 |

RA-01

- 主張: M4 の kill node は変異を殺すが、`True` 入力が後段の件数一致検査でも拒否されるため、事前登録が求める単一理由性を満たさない。
- 根拠: `orchestrator/tests/test_artifact_admission.py:1740-1742` は `(True, IntSubclass(0))` を一つの loop で順に検査する。exact int 検査を削除すると、最初の `True` は snapshot count 0 との不一致により `ValueError` となる (`orchestrator/campaign/artifact_admission.py:389-395`)。そこで test が終了するため、実際に受理される `IntSubclass(0)` には到達しない。
- 誤っていた場合に何が壊れるか: M4 の赤を exact 型境界の受理集合検査と評価できず、後段 mismatch による例外型の違いを mutation kill と誤認する。変異 matrix の単一理由性が成立しない。
- 親が何を測れば決着するか: M4 だけを適用して当該 node を実走し、最初の失敗が `True` に対する snapshot mismatch の `ValueError` であることを確認する。さらに `True` と `IntSubclass(0)` を別々に実行し、後者だけが構築を通ることを確認する。
- 判定: must-fix。

## constructor 波及の検査

AST で constructor 呼出を全数検索し、6 箇所すべてが必須 field を渡していることを確認した。

- production: `orchestrator/campaign/artifact_admission.py:1328`
- test support: `orchestrator/tests/commit_receipt_support.py:196`
- T1286 tests: `orchestrator/tests/test_t1286_commit_receipt.py:431,534`
- admission tests: `orchestrator/tests/test_artifact_admission.py:1714,1770`

test 側の既存 call site はすべて fixture の records から件数を導出している。未追従 call site は見つからなかった。

## 総括

静的検査では、production の受理集合拡大、証拠母集合の縮小、exact 型境界の弱化、既存テストの弱体化、constructor の追従漏れは見つからなかった。

must-fix は RA-01 の M4 mutation test の単一理由性だけである。pytest は実行しておらず、緑は主張しない。新規 node の duration ledger 追記も親の実測後に残っている。