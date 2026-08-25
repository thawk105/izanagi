---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-paper-story-a1-paired-20260824
seq: 6
---

## 新規

### {{F:family-contract-assumed-one-cli-shape}}. 族へ自動編入する契約が単一 CLI 形状を暗黙前提にしており、別形状の driver が構造的に入れなかった [テスト代表性] [誤前提]

- 事象: `orchestrator/tests/test_p3_exploration_namespace.py` は `orchestrator/campaign/*.py` を
  glob と AST で列挙し、exploration campaign root を作る module を自動的に族へ編入する。
  この族の generic 契約は「subcommand を持たない単一 CLI」「`module._cfg()` が無引数」
  「`module.main([])` を引数なしで呼べる」「実行時 `run_campaign` はちょうど 2 回」
  「`module._assert_single_tenant` が module namespace にある」を**どこにも書かずに**前提していた。
  `paper_story_a1_paired` は `measure` / `materialize` の subcommand を required で持ち、
  必須 option を 9 個要求し、3 workload を巡回し、`p2_2._assert_single_tenant()` を修飾名で呼ぶため、
  driver を置いた瞬間に 4 node が赤になった。前 wave はこれを 4 巡かけて閉じられず land できなかった。
- 根本原因: 族の編入条件 (campaign root を作るか) と、族の検査が要求する形状 (単一 CLI) が
  別々に決まっており、両者の整合を機械検査していなかった。編入は AST で自動、
  形状要求は各 test 本文へ散在という非対称のため、新形状の driver は
  「族に入るが契約を満たせない」状態へ構造的に落ちる。
- 恒久対応: {{D:family-admission-by-contract-registry}}。族の形状要求を既定値のない
  `_DRIVER_CONTRACTS` の必須 field へ集約し、driver ごとに CLI authority mode・
  期待 generator・entrypoint site・3 種の argv factory・呼出し数・期待 campaign ID の
  独立導出を登録する。登録漏れは直接 index の `KeyError` と発見集合との完全一致 assertion の
  両方で落ち、`.get()` の既定契約・名前による除外・`skip` を作らない。
- 再発検知: `test_driver_contract_registry_is_exact` (発見集合と登録集合の完全一致)、
  `test_driver_contract_schema_has_only_required_fields_and_closed_cli_modes`
  (field 集合の exact tuple と全 field の `default` / `default_factory` が `MISSING`)、
  `test_missing_driver_contract_is_hard_failure` (欠落 map を lookup helper へ渡して `KeyError` を要求し、
  hard fail 自体の恒真化を塞ぐ)。事前登録変異 p3c.m06 / p3c.m07 が本走で KILLED。

## 再発

### F28

- **再発: 2026-08-25** ([T-1622] 系列とは別の P3 族契約 wave)。段 5 実装子が事前登録変異
  11 件すべてについて「期待 node は単独 1 件」と報告したが、**実測では 10 件中 4 件で誤りだった**。
  段 6 の敵対レビュー (証拠束縛レンズ) が本走前に、識別子を変える変異は所有外 consumer を含め
  20 node、registry 登録を消す変異は 7 node、他 3 件も各 2 node を落とすと指摘した。
  親は推定を採らず、`DW-M07` の probe 経路 (全件 SURVIVED 期待で登録して観測 node を集める) を
  走らせ、観測値を `expected_nodes` へ焼き込んでから本走した。probe の観測件数は
  レビューの予測と 10 件すべて一致した (M1=2, M2=1, M3=20, M4=1, M5=1, M6=7, M7=1, M8=2, M9=1, M11=2)。
  型は F28 と同じ「事前登録を実測でなく設計・推定から書いた」であり、
  2026-08-16 の再発では親が転記元にしたのが裁定文の対応表、今回は**子の自己申告**である点が
  新しい顕在化である。恒久対応は変更なし (`DW-M08` の完全集合 + `DW-M07` の probe 経路が
  そのまま効いた)。防壁として効いたのは段 6 レビューのレンズに
  「事前登録変異の kill 帰属が成立するか」を入れていたことと、親が子の申告を実測で置き換えたこと。
