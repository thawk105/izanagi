HEAD `384b7860` を静的レビューした結果です。pytest は依頼どおり未実行です。

1. `[resolved]` protocol/freeze digest canonicalization

- driver は canonical JSON + 末尾改行を hash します（`orchestrator/campaign/s8b_oracle_n_pilot.py:1835-1843`）。
- admission も `_canonical_line()` 経由で同一 bytes になりました（`orchestrator/campaign/s8b_holdout_admission.py:358-370,1886-1907`）。
- freeze の raw bytes hash は loader 側で検証され、R33 admission は canonical freeze hash と raw freeze hash を混同しません（`s8b_freeze_io.py:49-68`, `s8b_oracle_n_pilot.py:605-610`, `s8b_holdout_admission.py:1903-1914`）。
- legacy branch の protocol/schedule 検証も従来の改行付き canonicalization のままです（`s8b_holdout_admission.py:3081-3088,3190-3192`）。

2. `[resolved]` CLI public manifest

- projection は `_R33_MANIFEST_KEYS` と cell projection に限定されています（`s8b_holdout_admission.py:2265-2276,2354-2377`）。`cell_id` や claim/ledger hash は外部 manifest に出ません。
- reserve CLI は receipt 本体でなく `receipt.manifest` を書きます（`s8b_oracle_n_pilot.py:2956-2961`）。
- consume は `authoritative_receipt_sha256` から内部 receipt と public manifest を照合して解決します（`s8b_oracle_n_pilot.py:2168-2188`, `s8b_holdout_admission.py:3443-3464`）。

3. `[resolved]` 同一 manifest の複数指定

- manifest hash の重複拒否は削除され、同一 manifest を3回渡せます（`s8b_oracle_n_pilot.py:2264-2274`）。
- allocation identity の重複検出は残っています（`s8b_oracle_n_pilot.py:2369-2378`）。最終的に allocation index `{0,1,2}` と schedule 396件も完全被覆します（`:2491-2496`）。

4. `[resolved]` recovery の ledger duplicate

- 既存 R33 ledger を identity digest で索引化し、完全一致 duplicate も拒否します（`s8b_holdout_admission.py:2679-2688`）。
- 異なる内容の同一 identity は従来どおり conflicting row として拒否されます（`:2684-2686,2695-2707`）。staged append 内の duplicate 検出も維持されています（`:2455-2461`）。

5. `[partially-resolved]` decision pin checker

- `_OBSERVATION_ROLES` 宣言の exact-one、文字列/comment の masking、source span 束縛は追加されています（`tools/check_docs.py:1453-1548,1555-1588`）。
- 同一 heading に複数 section がある場合も候補を exact-one で拒否します（`tools/check_docs.py:1633-1661`）。
- ただし pending fragment は依然として `docs/spool/decisions/*.md` の任意ファイルを走査し、slug が含まれれば候補にします（`tools/check_docs.py:1706-1727`）。複数 fragment も最初の成功で通ります（`:1765-1773`）。

[real][must-fix] source entry 抽出に残る decoy 経路

`R33_SOURCE_ENTRY_RE` は code mask 後の文字列ではなく raw `source` を再走査しています（`tools/check_docs.py:1569-1575`）。そのため、実際の `_OBSERVATION_ROLES` から `n_pilot_r33` entry を削除し、同じ期待内容を span 内の triple-quoted string に置いても、checker は期待値を返します。文字列自体は mask されるのに、entry 抽出で mask を使っていないためです。

6. `[resolved]` aggregate binary completeness

- `PilotBinary.public_record()` の field 集合と許容集合が一致しています（`s8b_oracle_n_pilot.py:70-80,186-205`）。
- required hash/schema、cache miss、重複 binary を検証します（`:2191-2248`）。
- binary、schedule、sessions が同じ exact 12-cell 集合であることを確認します（`:2434-2449`）。allocation 間の identity 一致と全体 schedule coverage も維持されています（`:2419-2422,2491-2496`）。

protocol 追随も問題ありません。`protocol-r33.json:12` の driver hash は現ファイルと一致し、job script、freeze raw hash、environment contract hash（`:7,14,18-20`）にも追随漏れはありません。legacy `n_pilot` / R=11 経路、opaque manifest、holdout unknownness への新規回帰も確認できません。

## 総括

(a) resolved は **5/6件**（1, 2, 3, 4, 6）。5 は partially-resolved。
(b) 新規 must-fix は **1件**。
(c) 新規 nit/backlog は **0件**。

**注記 (2026-08-20、fix-c commit 33ae1f25 後に対応済み):** 上記の新規 must-fix
(source entry 抽出の decoy 経路) は、開き波括弧 `{` の mask 済み code 上での
実在確認を追加する fix-c で解消済み。回帰テスト
`test_r33_source_contract_ignores_entry_in_docstring_within_observation_roles`
を追加。
