## 検証した範囲

指定された 6 資料を全文読了した。現行 worktree は clean であり、次を静的に照合した。

- `tools/codex_reasoning_ab.py` の snapshot 束縛、price version 一様性、cost 三分類、例外集約、軸集約、`valid`・`experiment_complete`・成果物書込経路
- `tools/t189_price_snapshot.py` の closed schema、SKU、単価、token mapping
- `orchestrator/tests/test_codex_reasoning_ab.py` の cost fixture、完全一致比較、凍結 literal、一様性検査、提案対象テスト
- worktree 全体で `normalized_cost`、`normalized_cost_axis_ledger`、`comparability`、`basis_key`、`accounted_total_key` の実参照を検索
- pytest は実行していない

## 所見 (重大な順)

1. **[重大・正しさ境界] 非 gate と受理集合不変の回帰検査が不足している。** 根拠: `s2-plan.md:104-114,124-136`、`tools/codex_reasoning_ab.py:10384-10393,10505-10513,10713-10725`、`orchestrator/tests/test_codex_reasoning_ab.py:15777-15832,15886-15940`。`not-incurred` テストは `valid`・`failure_reasons`・`experiment_complete` を検査せず、他の不一致テストも `experiment_complete`・`decision` を検査しないため、`not-incurred` で reason を足す変異や比較不一致を新 gate にする変異が生存し、受理集合または成果物の certified な完了状態が変わる。

2. **[高・整合実効性] axis の `accounted_total_key` が最終集約 count の複製であることを、複数試行の同一 axis で検査していない。** 根拠: `tools/codex_reasoning_ab.py:9795-9801,10094-10139`、`orchestrator/tests/test_codex_reasoning_ab.py:6519-6553,15587-15638`、`s2-plan.md:118-132`。fixture の 2 slot は `requested_model` が異なるため各 axis は常に 1 行であり、最初または最後の per-attempt vector を axis へ写す誤実装でも提案テストが通り、複数試行 axis の比較可能性値が誤る。

3. **[中・整合実効性] no-float 検査と既存 top-level `rounding` の不変検査が提案した取付位置に届かない。** 根拠: `s2-plan.md:67-76,138-139`、`tools/codex_reasoning_ab.py:10040-10050,10063-10093`、`orchestrator/tests/test_codex_reasoning_ab.py:15968-16008`。`comparability` は集約側で後付けする計画だが M03 は `_normalized_cost_for_attempt` の直接返値だけを walk し、M04 は既存 `rounding` object 自体を検査しないため、nested `decimal_places` を `8.0` にする変異や既存 top-level `rounding` を壊す変異が生存し、成果物の JSON 型または既存 field が変わる。

4. **[中・整合実効性] 動的な比較範囲値の帰属を固定するテストがない。** 根拠: `s2-plan.md:83-89,118-122`、`tools/codex_reasoning_ab.py:9297-9307`、`orchestrator/tests/test_codex_reasoning_ab.py:6519-6553,15591-15596`。提案テストは全て `benchmark_task_id="alpha"`、`stage="stage-1"` なので、helper がこれらを hard-code しても通り、別 task または stage の成果物で `basis_key` が衝突して参照範囲が変わる。

5. **[nit・参照整合] 親 brief の test anchor だけが不正確である。** 根拠: `brief.md:47-57`、`orchestrator/tests/test_codex_reasoning_ab.py:15565-15650`。`:15650` は cost テスト群の起点ではなく最初のテスト内の代入であり、helper の起点は `:15565`、最初の cost test は `:15641` である。放置しても成果物値・受理集合は変わらず、参照精度だけが落ちるため nit とする。

## プランのうち妥当と確認できた点

- 親 brief の production anchor 6 件は現行行番号と一致した。誤りは test anchor だけだった。
- プランの変更対象およびテスト対象の行番号は、現行関数・各テストの内容と対応している。
- snapshot path、SHA-256、version、excerpt の literal は `tools/codex_reasoning_ab.py:174-188`、closed な実 bytes 束縛は `:9107-9160`、全 slot 一様性は `:9202-9215`、非 null cache 拒否は `:9262-9267` に実在する。
- 凍結 bytes は `orchestrator/tests/test_codex_reasoning_ab.py:6568-6583`、null と frozen の混在拒否は `:6947-6983` でも独立に固定されている。計画どおり編集範囲を限定すれば、これらの凍結境界へ手を入れる必要はない。
- cost は frozen version、material descriptor、検証済み snapshot が揃う場合だけ生成され、null、legacy、descriptorless 経路では出ない。プランの現行挙動説明は実コードと一致した。
- malformed cost の `ValidationError` は `tools/codex_reasoning_ab.py:10069-10092` で `unavailable` と failure reason に変換され、`:10713-10714,10763-10772` で `valid` と `experiment_complete` へ波及する。観測不能だけでは reason を足さない現行分類も確認した。
- `normalized_cost` と `normalized_cost_axis_ledger` の名前による実参照は producer 本体と `orchestrator/tests/test_codex_reasoning_ab.py` だけだった。別の schema validator、receipt、manifest、golden、digest consumer は repo 内検索では見つからなかった。
- `manifest_sha256` は入力 manifest bytes の digest であり、出力 dict の digest ではない (`tools/codex_reasoning_ab.py:10763-10769`)。追加 field はこの値へ入り込まない。
- additive field で直接赤になる既存の完全一致 golden はない。完全一致に近いものは `orchestrator/tests/test_codex_reasoning_ab.py:9329` の verify と aggregate が同じ producer から作る `resource_ledger` 同士の比較、および `:15708-15741` の `components` sub-dict 比較であり、いずれも sibling の `comparability` 追加とは衝突しない。
- `certification_scope` の certified report field は引き続き `valid` だけである (`tools/codex_reasoning_ab.py:11469-11488`)。プランの編集範囲から独立している。

## 判断できなかった点と、その理由

- 実装前のため、helper が本当に `ValidationError`、`KeyError`、`TypeError` 等を送出せず、fresh tree だけを返すかは確認できない。これは実装差分で再検証が必要である。
- repo 外に保存された既存 report、receipt、golden、または外部 consumer が raw stdout bytes を hash・完全一致比較しているかは検索できない。CLI の canonical stdout bytes 自体は field 追加により必ず変わる (`tools/codex_reasoning_ab.py:12538-12544`)。
- pytest は指定どおり実行していないため、既存テストまたは提案テストを緑とは判定していない。
- 比較対象を同一 report 内だけに限定するか、別 generation の report 間にも広げるかは資料から一意に確定できない。後者を許すなら、現在案の `comparison_scope` は manifest または generation identity を持たないため別途意味論検証が必要である。

## 総括

提案した additive な取付位置自体は、凍結 snapshot、price version 一様性、既存 cost 値、manifest digest、certification scope から分離できる。repo 内 consumer や完全一致 golden との直接衝突も見つからなかった。

ただし、現状のテスト案では「受理集合を変えない」「比較宣言を gate にしない」「axis の最終 count を複製する」「既存 rounding と JSON 型を保つ」という中心主張への変異帰属が成立しない。所見 1 から 4 を補うまでは、プランの非変更論証を実コードに対して十分とは判定できない。