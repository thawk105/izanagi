## 合成の判定

merge 後も両変更は意味的に共存できており、新規の合成不具合は認めない。

- fan-out は scheduler を検証して必要 host 数を `nodes - 1` として確定し（`orchestrator/campaign/paper_story_a2_certification.py:298-315`）、`run_workload` 冒頭で検査後（同:3431-3432）、そのまま `run_campaign` へ渡される（同:3567-3585）。生成された raw evidence は同:3590-3599、acquisition からの抽出は同:1823-1854、full collector は同:4808-4824、最終的な `collect_results` 呼出しは同:4789-4794であり、経路上の上書きや迂回はない。
- scheduler は `load_policy` で exact shape と型を検査される（同:401-413）。protocol preimage から scheduler を外す設計（同:318-329）も、submission の `-b <nodes>` 検査（同:1328-1336）と report の policy bytes/hash 照合（同:4476-4488）が残るため、例えば旧 `-b 1` receipt を現行 `nodes=5` policy で受理することはない。
- T-2366 の検査は、渡された evidence に対する既存検査（同:4462-4550）の後、acquisition 再読込（同:4551-4557）、full receipt chain 検査（同:4558-4562）、report 再導出（同:4563-4566）、一致判定と拒否（同:4567-4570）、canonical evidence の返却（同:4571）まで残っている。返却値は `materialize` が受け取り（同:4575-4578）、再読込した receipt bytes を出力する（同:4597-4605）。
- 例外の責務も維持されている。host 形式・個数は `CertificationError`、再読込 receipt chain の交差は `SchemaChainError`、source/manifest authority 不足は `AuthorityError`（同:175-184, 298-315, 4558-4562, 4769, 4795-4802）。
- production helper の重複定義・import 重複・到達不能化はない。test 側も `_partial_materializer_forgery_case` と `_full_materializer_forgery_case` は別名で隣接し（`orchestrator/tests/test_paper_story_a2_certification.py:3033-3057`）、新規5 node はすべて一意（同:3060-3154）。fan-out の個数検査、CLI 伝播、実 run 伝播もそれぞれ同:2015-2048、4544-4568、4958-5109に残る。AST inventory でも重複 test/fixture/helper/import はなかった。

受理集合について merge 起因の新規拡大はない。既知の `dict ==` による `1` と `True` の同値受理は production 同:4567 に残るが、これは `ruling-stage6.md:9` で real・scope 外と明示済みで、T-2429 との合成によるものではない。

## 所見

なし。

## 総括

T-2366 の再読込・再導出・receipt chain・canonical evidence 返却はすべて存続している。  
T-2429 の host 検査と `run_campaign` への fan-out 伝播も存続している。  
helper、import、fixture、test 名の衝突や、新規の受理集合拡大は認めない。  
pytest は指示どおり実行せず、指定4ファイルだけによる静的監査とした。