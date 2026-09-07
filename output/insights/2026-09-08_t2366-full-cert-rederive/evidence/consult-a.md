## 所見

1. **主張** — plan の `evidence`→`canonical_evidence` 一括切替は、full materializer の入力受理集合を縮小だけでなく拡大する。具体的には、disk 上の正規 evidence を `E`、`R = canonical(E)` とし、呼出時の dict だけ `E["attempt_id"]` または `E["acquisition_schema"]` を改竄する。現行は identity/schema 検査で拒否するが、plan 後は改竄値を読み直した値で置換して `R` を受理する。  
   **file:line** — [plan.md:58](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/artifacts/t2366-full-cert-rederive/plan.md:58)、[paper_story_a2_certification.py:4450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4450)、[同:4469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4469)、[同:4476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4476)。  
   **成果物への影響** — accepted argument tuple は増える。一方、出力される report/receipt は canonical `E` 由来なので、新しい certified artifact 値が増えるわけではない。この区別なしに「受理集合は縮小のみ」とするのは誤り。  
   **提案する対処** — 現行の supplied evidence に対する identity/schema/request-id 検査を残したまま、その後に acquisition を読み直し、canonical evidence にも full chain 検査と report 再導出を行う。既存ゲートを置換しない。  
   **自己判定** — **real**。

2. **主張** — brief の「manifest 無効 → indeterminate」は production `_collect_command` の実際の到達経路ではない。また plan の helper は `_require_materializable_authority` を内包しないため、partial canonicalizer と同じ総関数にもなっていない。全 driver 成功で manifest が無効なら `raw_manifest_invalid_kind="authority"` となり、else 枝より前に `AuthorityError` が出る。driver 非0なら manifest 枝より先に failed-driver 枝へ入る。  
   **file:line** — [brief.md:12](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:12)、[paper_story_a2_certification.py:1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1666)、[同:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1176)、[同:4728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4728)、[同:4742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4742)、partial の [同:2865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:2865)。  
   **成果物への影響** — collector では plan 後も外側の authority gate が残るため、invalid-manifest artifact が新たに出ることはない。ただし validator から helper を呼ぶ際、report mismatch が `AuthorityError` より先になる入力が生じ、partial とエラー優先順位が異なる。  
   **提案する対処** — `_canonical_full_report` 冒頭にも `_require_materializable_authority` を置き、brief の manifest 分岐説明を「authority gate 後に到達可能な evidence に限る」と訂正する。  
   **自己判定** — **real**。

3. **主張** — 「exact shape 後に読む」は partial の配置を正確には射影していない。partial は top-level shape に加えて status と cell shape を検査してから読み直すが、plan は full の top-level key 集合だけを検査して読み直し、status/cells 検査より前に I/O を行う。例えば正しい v4 key 集合を持つ report から cell の `src_token` を削除し、supplied evidence の `acquisition_path` を `None` にすると、現行は cell-field エラー、plan 後は acquisition-authority エラーになる。  
   **file:line** — [plan.md:30](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/artifacts/t2366-full-cert-rederive/plan.md:30)、[paper_story_a2_certification.py:4375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4375)、[同:4381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4381)、full の [同:4443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4443)、[同:4491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4491)。  
   **成果物への影響** — この例は前後とも拒否されるため、certified 成果物・受理集合は変わらないが、観測される例外契約は変わる。確認した既存 materialize tests の `match=` が直接壊れる例はない。cross-chain の `"legacy result is crossed"` と unsupported v2 の `"identity differ"` は従来位置で残る。  
   **提案する対処** — 少なくとも既存 full の structural/identity/schema/request/cell 検査を完了してから読み直す。これで既存エラー優先順位を保ちつつ、materialize 前の exact 再導出は実現できる。  
   **自己判定** — **real**。

4. **主張** — production `_collect_command` に限れば、安定した filesystem 上の `report == expected` は構成上恒真である。最初の `validate_acquisition_bundle` から helper で `R` を作り、直後に同じ path を再検証して同じ helper で expected を作るためで、CLI は外部 report を受け取らない。brief の「偽 report が production の tracked 成果物として公開される」はこの前提では一般化しすぎている。  
   **file:line** — [brief.md:11](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:11)、[同:16](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:16)、[paper_story_a2_certification.py:4722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4722)、[同:4767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4767)。  
   **成果物への影響** — supported CLI の安定入力では受理集合は変わらない。実際に縮むのは、外部 Python code や tests が `materialize` を直接呼び forged report を渡す API 境界である。二回の読み取り間で disk が変われば拒否されるか、最終 evidence が同じ report を正当に再導出する場合だけ通る。  
   **提案する対処** — 実装自体は direct-call 境界の防壁として維持し、成果物影響の説明を「CLI report injection」ではなく「importable materializer の直接呼出しと二回読み間の整合性」に限定する。呼び手確認のため指定外 `.py` を repo-wide `rg` したが、A-2 production hit は `_collect_command` のみだった。  
   **自己判定** — **real**。

5. **主張** — P4 の「渡された evidence bytes の不一致は sha で拒否される」は誤り。正規 evidence `E` の `acquisition_bytes` だけを `b"forged"` に変え、path・logical fields・report をそのままにすると、現行 materializer はそれを検査せず tracked receipt として書く。plan 後は不一致を拒否するのではなく、dict 内の bytes を捨てて disk から読んだ canonical bytes を書く。  
   **file:line** — [brief.md:37](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:37)、[paper_story_a2_certification.py:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1725)、[同:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:1804)、[同:4551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4551)。  
   **成果物への影響** — bytes-only forged input は前後とも受理されるが、成果物は forged receipt から canonical receipt へ変わる。したがって certified artifact bytes の集合は縮むが、入力受理集合は縮まない。  
   **提案する対処** — P4 を「不一致を sha で拒否」ではなく「supplied bytes を authority とせず、再読した canonical bytes を materialize」に訂正する。拒否要件を新設する必要はない。  
   **自己判定** — **real**。

6. **主張** — brief の `_COLLECT_TEST_TOKEN` test inventory は1件不足している。`test_patched_adopted_source_binding_positive_control` も token を渡す7件目である。ただしこの test も `collect_results` 止まりなので、「再導出の影響を受けない」という一般結論は正しい。  
   **file:line** — [brief.md:15](/home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/brief.md:15)、[test_paper_story_a2_certification.py:4088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:4088)、[同:4094](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:4094)。  
   **成果物への影響** — なし。テスト影響の分類結果も変わらない。  
   **提案する対処** — inventory に 4088 を追加する。plan が指摘した full validator 終端、evidence return 開始、synthetic test 定義行のずれも brief 側へ反映する。  
   **自己判定** — **real（軽微）**。

## 破れなかった箇所

- `_collect_command` の既存 else 本体を逐語的に移し、外側の attempt/authority checks を維持する限り、到達可能な driver 非0、`collect_results` 成功、列挙例外、`AuthorityError`、`source_commit` 付加で report は変わらない。`attempt_root` も事前の文字列一致検査により `Path(evidence["attempt_root"])` と既存値が一致する。canonical JSON は `sort_keys=True` なので dict 挿入順も bytes 差を作らない。

- 同一の disk bytes を再読する限り canonical evidence に drift はない。`attempt_root` は lexical canonical path、request IDs は submission 側で正規化され acquisition と一致必須、raw results は policy cell 順、raw files は manifest hash 検証済みである。5274 の live/frozen 差も fixture が途中変更しないため一致する。

- plan の3負例は現行 validator を実際に通過できる。`status` の positive→reject、finite `effects` 改竄、passed dict の `driver_rcs` だけに合わせた indeterminate report は、いずれも現在の形・identity 検査では拒否されない。

- legacy v3 full を触らない判断自体は今回の受理集合を広げない。既存の identity-only 集合を据え置くだけである。

- brief の evidence field 実在性と A-2 production caller の唯一性は確認できた。行番号は `acquisition_path` が 1804、synthetic positive の定義が 5274 という plan の訂正が正しい。

## 総括

plan の report 再導出本体は成立し、安定した canonical evidence の過剰拒否も見当たらない。  
修正必須なのは、既存 supplied-evidence gates を canonical 値で置換して受理入力を増やす点と、helper 内の authority precondition 欠落である。  
brief は production 経路の恒真性、manifest-invalid 分岐、P4 の「拒否」と「canonical 化」を区別して書き直すべきである。  
pytest は指示どおり実行せず、静的検査のみ。