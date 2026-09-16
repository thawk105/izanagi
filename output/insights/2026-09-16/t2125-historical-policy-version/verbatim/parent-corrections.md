# [T-2125] 段 3 レンズ A の指摘を受けた親の訂正と再実測

## C1. M4 を全 preimage で測り直した (レンズ A 所見 8 の 1 点目は real)

レンズ A の指摘どおり、最初の M4 は `repo_stock_pin` しか見ておらず、
「今日は発火していない」を preimage 全体へ一般化していた。**測り直した。**

外部 official root 3 つ (`b10-backoff-grid-t2266-formal`、`b10-backoff-grid-t2418-explore`、
`izanagi-measurements`) の v2 lock 20 件について、記録 `build_admission` の 5 field を全部数えた。

| field | 20 件の値 | 現行 |
|---|---|---|
| `schema` | `build-admission-policy/v1` × 20 | 一致 |
| `repo_stock_pin` | `511c953` × 20 | 一致 |
| `coder_authority` | `cli-opt-in` × 20 | 一致 |
| `generator_registry` | 現行 7 member と同じ列 × 20 | 一致 |
| `review_registry` | 現行 3 member と同じ列 × 20 | 一致 |

**結論は変わらないが、根拠が preimage 全体になった。** 20/20 が現行と一致する。

## C2. 認めた指摘 (訂正して先へ進む)

- **M2「版上げは 2 事象」は網羅的でない。** `schema` literal と `coder_authority` literal の
  変更も preimage を動かす。正しくは「preimage の 5 field のどれが変わっても版は上がる」。
- **M10 の見出し「実経路がある」は立証過剰。** status 条件を満たす、までは正しいが、
  `layer3_report.py:966` と `autonomous_trial_completeness.py:4965` が certified admission を
  再実行するため、最終受理まで到達する経路は立証していない。
  **したがって「非認証 status にするから最終 gate は不要」と読んではならない。両方残す。**
- **M9 は「公開 API の直接呼出しでも発火しない」までは言えない。** `wal.py:2821` の `replay` は
  policy 省略を許す。確認できたのは「本 wave の歴史 admission は `_replay` を通らない」まで。
- **M5 の「重複なし」は予定編集面どうしの比較に限る。** 未 commit の編集面は測れていない。
- **行番号の訂正。** M1 の topology 呼出しは `:1368`、policy 引数は `:1370`。
- **brief の「編集面は 1 module」は成立しない。** 旧 stock pin は `build_admission.py:709` でも
  止まるため、`build_admission.py` も編集面に入る。

## C3. 不変条件 4 の文言を訂正する (レンズ A 所見 1 は real)

旧: 「記録された policy をそのまま信じない。記録側にも exact な形を要求する」。

**この文言は形検査を真正性の保護と誤読させる。** 訂正:

> 記録された policy の**形**だけを exact に要求する。形検査は malformed object の受理を防ぐが、
> **記録値が当時実在した policy であることは保証しない。** 歴史閲覧で成立する保証は
> 「記録 policy と記録 receipt が内的に整合する」までであり、
> **「当時承認された generator / authority だった」ことの検証ではない。**
> この限界は成果物の診断 (`classification`) と `current_verifier_conformance = unknown` で
> 表に出す。台帳・追加 gate は足さない (依頼の scope 外)。
