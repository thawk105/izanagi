## 観点 1 の所見

[real / must-fix 1] `test_bound_evidence_token_is_the_cache_authority` は現状では目的箇所まで到達しない。`_sort_cache_request()` が借りる `_fake_build_environment` は `buildcache.source_digest.resolve_evidence` を `ccbench_dir, cxx` しか受けない関数へ置換するが、legacy fresh の `_recheck_source_evidence` は `sort_oracle_contract_id` も渡す。そのため最初の `build()` が `TypeError` で終了し、key assertion、v2、cache-open 前拒否は未観測になる。T13 と同様、request 作成後に resolver を `lambda *_args, **_kwargs: request.evidence` へ置換する必要がある。  
放置時: 新規受入集合が常時赤になり、evidence token の cache authority と open 前拒否を受理根拠として参照できない。

実装上の拒否位置自体は正しい。legacy は `buildcache.py:3135` が cache root open `:3164` より前、v2 は `:2343` が contract directory open `:2556` より前である。`_require_secure_fs_contract()` はこの呼出し時には directory を開かない。

追加17 node内での「1行変異でその nodeだけ赤」の対応は次のとおり。

| node | 単独で赤にできる実装行 |
|---|---|
| T1 | `p3_s4_loop_sort.py:340` の `declared != expected` を除去 |
| T2 | `p3_s4_loop_sort.py:417` の forwarding を除去 |
| T3 | 8署名のどれか1件の既定値を `None` 以外へ変更 |
| T4 | `source_digest.py:2226` の相互排他条件を無効化 |
| T5 | `loop.py:483` または `:567` の一方を無効化 |
| T6[legacy] | `pipeline.py:1274-1276` を無効化 |
| T6[v2] | `pipeline.py:1259-1260` を無効化 |
| T7 | 答えられない。wrapper forwarding の欠落は T8 の v2 2 nodeも赤にする |
| T8[legacy-fresh] | `buildcache.py:3253` を除去 |
| T8[legacy-hit] | `buildcache.py:3187` を除去 |
| T8[v2-fresh] | `buildcache.py:2842` を除去 |
| T8[v2-hit] | `buildcache.py:2599` を除去 |
| T9 | `buildcache.py:3335-3338` を無効化 |
| T10 | `source_digest.py:2214` の domain `v1` を変更 |
| T11 | `source_digest.py:110` の `\|src=` preimage を変更 |
| T12 | 現状は答えられない。fixture 修正後なら legacy の `buildcache.py:3135` を緩和すると T12だけ赤 |
| T13 | 答えられない。raw token を選ぶ自然な変異は T12も赤にする |

[real / must-fix 2] T7とT13には独立した実装行 owner がなく、登録済み M11とM8がそれぞれ他テストを同時に赤化する。  
放置時: mutation report の owner 参照が非一意になり、wrapper、binder、raw-entry 非参照を個別に検証したという報告値が過大になる。

そのほかの重点照合結果は以下のとおり。

- [refuted] T8 の hit が fresh 2回になる懸念。legacy/v2とも warm call が同じ key/digestへ完成 entryを publishし、2回目はそれぞれ `buildcache.py:3168` / `:2565` の hit 分岐へ入る。fake runner は legacy の `cmake -B` と `cmake --build` にも適合する。2回目が freshなら `expected_fresh=False` が失敗する。
- [refuted] T13 の poison path 不一致。legacy は実物の `root/<cache_key>/cc/silo/ycsb_silo.exe`、v2 は `root/contracts/<contract_sha256>/<digest>/cc/silo/ycsb_silo.exe` と完全一致する。v2 identity の site、dependency prefix、toolchain、admissionも実呼出しと一致する。
- [refuted] T11 の固定式不一致。legacy preimage、v2 base preimage、`verification_variant_id` は基点 `e9e4c27c6` の実装式と一致する。
- [refuted] `_sort_contract_evidence` の schema 不一致。全 wire field名と `source-evidence/v1` は実物と一致し、各 SHA-256、absolute root、false/nonempty tracked state、sorted unique tuple は `__post_init__` を通る。production が設定する非wireの `proof_source_snapshot` と `verification_variant` は省略されているが、両方とも許可された既定 `None` である。

## 観点 2 の所見 (変異 M1〜M15 の帰属予測表を含む)

全15件で `old` は対象 fileにちょうど1箇所存在する。`new` も意図した変異で、M14を除き非等価である。M12/M13の `new` は変異前から別位置にも1件存在するが、置換対象となる `old` の一意性には影響しない。

以下は追加17 nodeに限定した静的な赤化予測である。T12は前節の基準線故障を直した場合を `*` で示す。

| ID | 赤化予測 node | 帰属 |
|---|---|---|
| M1 | T1 | 単一 |
| M2 | T2 | 単一 |
| M3 | T5 | 単一 |
| M4 | T5 | 単一 |
| M5 | T6[legacy], T6[v2] | 過剰決定 |
| M6 | T6[legacy] | 単一 |
| M7 | T6[v2] | 単一 |
| M8 | T10, T12*, T13 | 過剰決定 |
| M9 | T10 | 単一 |
| M10 | T4 | 単一 |
| M11 | T7, T8[v2-fresh], T8[v2-hit] | 過剰決定 |
| M12 | T8[v2-hit] | 単一 |
| M13 | T8[legacy-fresh] | 単一 |
| M14 | なし | 等価、SURVIVED |
| M15 | T9 | 単一 |

M14は真に等価である。`type(sort_oracle_contract_id) is not str` が先に短絡評価されるため後段へ来る値は exact `str` に限られ、その集合では `not value` と `value == ""` は同値である。

[real / must-fix 3] mutation spec は M1〜M13/M15をすべて `expected_status: SURVIVED`、`expected_nodes: []` としており、段4の KILLED 裁定および上表と逆である。M14だけが正しい。  
放置時: mutation report が binding を欠落させる実装を期待どおりの survivor として受理し、未束縛 cache binaryを使う certified 選択まで受入集合へ混入させうる。

単一帰属へ直す実装変異案は次のとおり。

- M5: `pipeline.py:1096` を `sort_oracle_contract_id is not None and env_contract is not None` にして legacy resolverだけを欠落させれば、owner は T6[legacy] だけになる。
- M8: 「rawを返す」という意図を維持したまま単一 ownerにはできない。T12/T13も raw aliasを意図的に検査するためである。単一帰属を優先するなら、`source_digest.py:2207` の NUL拒否節を除く変異へ置き換え、T10だけを ownerにする。
- M11: wrapper omissionは必ず T7とv2出口を同時に壊す。単一帰属を優先するなら `buildcache.py:2842` の v2 fresh forwarding除去へ置き換え、T8[v2-fresh]を ownerにする。

## 観点 3 の所見

- [refuted] sort driver の `run_campaign` caller数が増えた懸念。対象差分後も `p3_s4_loop_sort.py:412` の1呼出しだけである。
- [refuted] `from test_buildcache_v2 import ...` の sibling import固有の懸念。同じ test moduleは既に module-levelで `campaign_lock_test_support` を同形式でimportし、D1411元テストも `test_buildcache_v2` を同形式でimportしている。既存moduleを収集できる受入環境なら今回のimportも同じ tests directoryから解決される。
- [不確定] `test_campaign.py` の caller inventory、`test_pytest_collection_config.py` の oracle import pin、duration ledger、`conftest.py` の real-repo inventoryは、単独段の必読射影に本文が含まれていないため、exact assertionとの照合はできない。対象差分からは17 node追加と module-level oracle import追加、およびこれらmeta fileが未変更であることまでしか確定できない。
- [不確定] 同じ理由で duration ledgerが全node必須か、遅いnodeだけかは判定不能である。29 nodeのままでよいとは認定できない。

pytestは実行しておらず、いずれも緑とは報告しない。

## 総括

must-fix は3件。最重要は mutation spec が14件のnegative mutationを `SURVIVED` としている期待値逆転である。  
加えてT12はfixture不整合で目的箇所へ到達せず、M5/M8/M11は単一帰属を満たさない。  
meta-testとledgerは射影不足により未確定で、実走結果もない。  
判定は NO-GO。