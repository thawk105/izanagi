---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: worktree-t338-between-run-floor
seq: 1
---

## {{D:t338-gate-unit12-opaque-capability}}. 投入gate 単位1/2は opaque capability sealing + freeze/thaw で構造的整合性を保証する

**決定:** D509 決定(6)(7)が確定した単位1(manifest/binding/Git基盤)・単位2(受領証IO/schema)の
実装で、段3敵対相談・段6敵対レビューが発見した3件の脆弱性を踏まえ、次の3パターンを
`orchestrator/submission_gate/` の設計規約として固定する。

1. **既存 `orchestrator/preregistration/blobref.py` は一切変更しない。** D509 決定(6)の
   「衛生化Git実行面を公開helperへ抽出して使う」は、wrapper化ではなく**独立実装として複製する**
   形で満たす。既存 `blobref._git`/`_git_env`/`_GIT_EXECUTABLE`/`MAX_BLOB_BYTES` を直接
   monkeypatchする既存test (`test_t139_blobref_git_trust.py` 等) と、4種の異なる例外型
   (`BlobResolutionError`/`InvalidBlobRefError`/`BlobDigestMismatchError`は非subclass関係) を
   壊さないことを、抽出の再利用性より優先する。
2. **将来 (単位3以降) が公開してはいけない値を持つ型は、単純なpublic dataclassにしない。**
   `_PreregBinding`・`ApprovedManifest`はどちらもmodule-privateなcapability tokenを
   keyword-only必須引数として要求し、`type(self) is not <Class> or token is not <TOKEN>` を
   `__init__`/`__post_init__`で検査する。これは「型が合っていれば正当」という偽陽性
   (callerが直接構築した偽の manifest/binding を受理する) を防ぐ。Pythonの private名は
   importされれば偽造できるという限界はあるが、それでも型検査だけの実装より安全である。
3. **digest固定後に内容を書き換えられる可変構造 (dict/list) を外部へ渡さない。** JSON parse結果
   (`ReceiptDocument.value`)・schema document (`ReceiptSchema.document`) は
   `MappingProxyType`/`tuple`へ再帰的に凍結して保持する。ただし `jsonschema.Draft7Validator`
   (この環境は3.2.0) はexact `dict`/`list`型でしか instance を認識しないため、
   検証の**直前にだけ**再帰的に「解凍」した可変コピーを作って渡し、格納側は凍結のまま保つ。

**理由:**
- 段3敵対相談(正しさ境界レンズ)が、`blobref.py`のwrapper化案が既存consumerの例外契約を
  壊しうると指摘した。段6独立コードレビューが、`ApprovedManifest`が偽造可能な単なる
  public dataclassであること、`ReceiptDocument.value`が凍結を謳いながらdict実体を晒すことの
  2件を実際にfile:lineで示した。
- fixで凍結を追加した直後、fix後の焦点再レビューが「正当な受領証がjsonschemaのexact型判定
  (`isinstance(x, dict)`)と衝突して誤って拒否される」という新規regressionを検出した
  (両立しないconflicting requirementではなく、検証直前の解凍で両立する)。

**却下した選択肢:**
- `blobref.py`を互換wrapper化して`read_pinned_blob`を再利用する — D509決定(6)の文言には近いが、
  4種の例外型をすべて保持するwrapperは既存consumer 2件・既存test 3件の例外契約を精査せずには
  安全と言えず、独立実装のほうが低リスクで同等の再利用効果 (ゼロから設計しない) を得られる。
- `ApprovedManifest`/`_PreregBinding`を型検査だけで閉じる (token検査を持たない) —
  D509決定(5)(8)が避けた「自己申告を信用する恒真相当」の再発になる。
- 受領証・schemaを凍結しない (mutableなまま保持する) — digest固定後に呼び手が
  `document["properties"]`等を書き換えられ、pin検証の意味が失われる。
