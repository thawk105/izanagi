## 所見

1. **主張:** v4 の「report 全体一致」は Python の `dict ==` による値比較であり、JSON 上は異なる `bool` と `int` を同一と扱うため、完全一致検査が骨抜きになる入力がある。正規 report の `cells[0]["correctness"]["legacy_repetitions_observed"]` は整数 `1` だが、これを `True` に差し替えても `True == 1` のため `report == expected` は真になる。既存 cells 検査は nested correctness の型を検査せず、`_canonical_json` は成果物へ `true` として保存する。
   - **file:line:** `orchestrator/campaign/paper_story_a2_certification.py:4537`、`:4335`、`:2661`、`:225`。新規テストは `orchestrator/tests/test_paper_story_a2_certification.py:3010`、`:3024`、`:3039`。
   - **成果物・受理集合への影響:** 正の acquisition に対し、再導出 report が整数 `1` を持つのに、certified 成果物の `certification.json` が boolean `true` を持つ forged report を受理・publish できる。旧集合からの拡大ではないが、裁定が要求した「report 全体一致」による縮小が未達である。既存3負例は Python 上で確実に不等な値しか使わないため、この壊れ方でも緑になる。規律2の正しさゲートに触れる。
   - **提案する対処:** v4 の同じ比較箇所だけを `_canonical_json(report) == _canonical_json(expected)` のような canonical JSON byte 比較にし、上記 `1 → True` の負例を追加する。新しい一般 gate ではなく、裁定済みの全体一致を JSON 型込みで実装する修正である。
   - **自己判定:** **real**。

2. **主張:** 新設・変更された4テストは、validator の `return canonical_full_evidence` を `return evidence` に弱めてもすべて緑になる。3負例は return 到達前に不一致で停止し、正例は最初から canonical evidence を渡すため、返却 evidence の由来を観測していない。
   - **file:line:** `orchestrator/campaign/paper_story_a2_certification.py:4541`、`orchestrator/tests/test_paper_story_a2_certification.py:2432`、`:3020`、`:3035`、`:3055`。
   - **成果物・受理集合への影響:** 現行実装自体は正しく canonical evidence を返している。しかし上記変異では、正規 report と正規 `acquisition_path` に、`acquisition_bytes` などだけを差し替えた evidence dict を渡すと、再導出比較には通り、渡された非 canonical bytes が certified 成果物へ格納される。これは裁定 P4 の「拒否せず canonical bytes へ置換」を失う退行である。
   - **提案する対処:** 正規 report と、receipt byte member だけを改変した evidence copy を `materialize` へ渡し、生成された receipt が disk から再読した canonical bytes と一致する正例を追加する。bytes 不一致の拒否は要求しない。
   - **自己判定:** **real（テスト防壁の欠落。現行 production コードの欠陥ではない）**。

## 破れなかった箇所

- plan v2 の1〜6は、上記の JSON 型込み一致問題を除けば差分へ反映されている。既存の identity、schema chain、request IDs、固定 field、cells、historical/indeterminate 検査は渡された `evidence` に対して残り、再読はそれらの後ろにある。
- legacy v3 full は追加条件を通らず従来の `return evidence` へ進む。legacy v1 partial・v2 partial のコードには差分がなく、既存期待値の緩和・反転・削除もない。
- `_canonical_full_report` と旧 `_collect_command` full else 枝について、production の有効入力で report が変わる例は見つからなかった。driver 非0、manifest 無効、`collect_results` 成功、列挙された例外 tuple、`AuthorityError` 伝播、成功時の `source_commit` 付加はいずれも同じ条件・引数・例外境界である。
- `_collect_command` では既存 authority gate が残り、helper 冒頭にも同じ gate がある。後者は evidence を変更しないため、通常の同一 evidence では二重呼出しによる report 差はない。
- `expected` が `report` と alias して恒真になる経路はない。production CLI で安定した disk から同じ report が再生成される構成上の恒真性は裁定どおりで、直接 `materialize` と二回読み間の変更には検査が効く。
- 新規3負例では偽造は fixture 完了後に行われ、fixture が偽造を上書きしていない。対象となる `validate_acquisition_bundle`、`_canonical_full_report`、`materialize` 自体も stub されていない。

## 総括

v4 再読・再導出の配置、既存検査の維持、legacy/partial 不変、collector 切り出しは裁定どおりである。  
ただし Python equality により JSON 型の異なる forged report を certified 成果物として受理できるため、現状は要修正。  
加えて canonical evidence を成果物へ使う退行を新規テスト群が検出できない。  
pytest は指示どおり実行せず、指定資料と現物による静的検査のみで判定した。