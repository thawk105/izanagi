# erratum — 変異 1 巡目の MISMATCH 11 件 (DW-M02: 初回結果は消さない)

`mutation-spec.json` (sha256 `0fc9e8e53ab18f223c7e60b9460fe17cb1c4d5d3192c760c3dd97445961f10a4`)
による 1 巡目は **MISMATCH 11 / KILLED 3 / SURVIVED 0** だった。台帳は `mutation-ledger.json`。

**SURVIVED が 0 件なので、14 件すべてに検出力はあった。** 外れたのは期待失敗 node の集合であり、
harness は `failed_keys == expected_keys` の**厳密一致**で KILLED を判定するため MISMATCH になった。

## 機序 1 — 期待 node の予測不足 (verifier 側)

`Integrity.clean()` の witness 連言は、direct verifier・serializer・CLI・pipeline の複数層から
同時に観測される。1 変異が 4〜9 node を落とすため、1〜2 node だけを登録した spec は一致しない。
2 巡目は 1 巡目台帳の `failed_nodes` から実測で再導出した。

## 機序 2 — `pipeline.py` の一時変異が無関係な 26 件を赤にする (帰属の過剰決定)

`orchestrator/campaign/pipeline.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の 8 path の
1 つで、`contract_loader_binding.verify_live_contract_loader_binding` が **disk bytes と記録 commit の
blob** を照合する。変異 harness が同 file を一時変異させると照合が破れ、campaign lock を作る
`test_campaign.py` の identity/loop 系テスト約 26 件が `IdentityMismatch`
(`orchestrator/campaign/ident.py:371`) で落ちる。**これは変異した guard の実効性とは無関係である。**

M09 の 1 巡目 `failed_nodes` は 34 件だが、うち 32 件がこの巻き添えだった。これを
`expected_nodes` に含めて KILLED を名乗ると、「guard を外したから赤くなった」という証拠にならない
(診断が別の失敗に置き換わる形)。

**対策:** spec を 2 本に分け、`pipeline.py` を触る 6 変異は runner を witness/run_trace の control
node 14 本だけに絞った。期待 node は 1〜4 件へ縮み、単一理由性が回復した。加えて
**drift control** (`M15-drift-control-comment-only` = `pipeline.py` の comment だけを変える意味的
no-op) を足し、絞った範囲が drift の影響を受けないことを **SURVIVED** として実測した。
この control が SURVIVED したことで、spec B の 6 件の kill は変異そのものへ帰属する。

## 起動前検査で止まった 2 回 (harness の fail-closed が効いた)

1. 期待 node `test_pipeline_nonzero_batch_commits_rejects` が pytest collection に実在しない
   (実際は `..._with_structured_wal`)。**2 時間の走行前に停止した。**
2. drift control の `category` に `control` を書いた。許容値は
   `negative` / `positive` / `both-layers` の 3 つ。

## 教訓 (段 8 の候補へ回す)

- 期待 node は fix 後の collection から再導出する。**存在検査では代替できない。**
- **enforcement source closure の 8 path を変異させる wave では、runner 範囲を drift 非感受な
  node へ絞り、drift control を 1 件置く。** さもないと kill が過剰決定になる。
