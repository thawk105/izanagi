## 所見

無し。

## 焦点走に足すべき file

module 名による `orchestrator/tests/` 全走査では、親が把握した次の 6 file が追加集合の全てで、7 本目はありません。

- `orchestrator/tests/test_s8b_oracle_driver.py` — report/judge を import し、generator path と CLI/library 経路を参照する (`:84-85`, `:116-117`, `:4227`, `:5645-5671`)。
- `orchestrator/tests/test_official_perf_closure.py` — 3 module を reviewed file、predicate、guard の AST 閉包に含める (`:69-73`, `:161-171`, `:403-416`)。
- `orchestrator/tests/test_s8b_binding_driftguards.py` — report module を直接 import して検証関数を消費する (`:38`, `:115-212`)。
- `orchestrator/tests/test_s8b_materialization.py` — report の binding key/schema を直接参照する (`:338`, `:429-432`)。
- `orchestrator/tests/test_s8b_oracle_artifacts.py` — 3 source file のトップレベル alias を AST 検査する (`:252-280`)。
- `orchestrator/tests/test_s8c_preregistration_predicates.py` — `s8b_verdict.py` を decoy path として参照する (`:1472-1485`)。実 bytes は読まないが、指定された module-name 閉包には含まれる。

## pin 閉包の再確認

- 現物 hash は report=`30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`、judge=`f3e2fbec0d9dc353dae987aa2f31afeafe178d75e544313fe1af84c06ec1ab3b`、verdict=`16b6974351cdfa2f44518e9b8d4aca4d424641218db32c2f346804cfad27cd8e` で指定値と一致しました。
- report/judge の新 hash は `orchestrator/tests/test_s8b_oracle_manifest.py:87,93` の各 1 hit のみです。`PIN_GATE_SPEC_SHA256` の literal `63cd8278...4202` も `PIN_GATE_SPEC_RAW` から静的再計算した値と一致します。
- report/judge の旧 hashは `output/insights/` の過去記録 3 hitだけです。生きた test・production pin には残っておらず、再 pin 漏れはありません。
- verdict の新 hashは repo 内 literal hit 0 件です。`s8b_oracle_manifest.py:65-73` の `_GENERATOR_SOURCES` に verdict はなく、その他の verdict path 参照にも source-byte hash 機構はありません。
- 追加された 7 test 名は各定義以外に exact hit がありません。conftest、growth/flaky hold、README の自走登録に追加要求はありません。対象 3 file は既に pytest-only allowlist 登録済みです (`orchestrator/tests/README.md:169,172,179`)。
- 所要時間台帳には新 7 node がありませんが、`nodeid_count` は台帳内部の件数だけを検査し、未知 node は既知値から得た fallback cost で扱います (`conftest.py:1390-1399`, `:1534-1554`, `:1594-1622`)。suite 集合の exact hash 登録 (`test_update_acceptance_duration_ledger.py:364-389`) に対象 3 suite は含まれません。

## 総括

- 静的な実装所見はありませんが、焦点走には上記 6 file を追加すべきです。
- 裁定済み library 経路以外の production 入口は見つかりませんでした。driver は従来どおり `launch_validate` を通ります。
- 新しい正例は全て実 g1 で、非 g1 を正例にしていません。非 g1 は後段 reverify が拒否する C-1 と整合します。
- 差分は R/J/V 各 production 1 行と各所有 test、P の再 pin だけです。共有 helper・signature の変更はありません。
- pytest は実行していません。