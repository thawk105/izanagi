## 所見

1. **主張:** plan の「shape 検査直後に読み直し、既存 identity/schema/request 検査も canonical evidence へ切り替える」は、materialize の受理集合を縮小だけでなく拡大する。

   - **file:line:** `plan.md:28-33,58-68`、`brief.md:27,34,37`、`paper_story_a2_certification.py:4450-4482,4526,4531-4556`
   - **具体例:** disk 上に正しい acquisition と、それから作った report がある状態で、渡す evidence を `{"acquisition_path": 正しいpath}` だけにする。現行は `evidence.get("acquisition") is None` により 4452–4464 で拒否する。plan 後は path から完全な evidence を読み直し、それだけで identity・再導出が通るため、certified artifact を新たに作れる。
   - **成果物への影響:** 現行で拒否される evidence 引数が受理され、tracked artifact が増えるため、brief の「受理集合は縮小のみ」と両立しない。
   - **関連する P4 の誤り:** `evidence["acquisition_bytes"]` だけを偽造しても、現行検査も予定された読み直しも、その値を disk bytes と比較しない。予定実装は偽造値を**拒否する**のではなく、canonical bytes で**置換する**。`brief.md:37` の末文は誤り。
   - **提案する対処:** 現在の identity/schema/request 検査は渡された evidence に対してそのまま維持し、その後 v4 に限って読み直し・再導出比較を行い、戻り値だけ canonical evidence にする。P4 は「食い違う dict bytes は捨てられ canonical bytes が出力される」と訂正する。
   - **自己判定:** **real**

2. **主張:** 変異 4 件中 3 件は、提示された `old` が実装後に一箇所へ定まらない。

   - **file:line:** `plan.md:125-170`、`paper_story_a2_certification.py:4388-4389,4431-4432`
   - acquisition 読み直しの `canonical_evidence = validate_acquisition_bundle(...)`、比較代入の `report_matches_rederived_evidence = report == expected`、条件の `if not report_matches_rederived_evidence:` は partial 側に既に存在する。plan どおり逐語射影すると各 2 箇所になる。
   - **成果物への影響:** text replacement が cardinality error になるか、partial と full を同時に変異させる。後者では KILLED/SURVIVED が full 射影単独の証拠にならない。
   - **提案する対処:** full 側だけ `canonical_full_evidence`、`full_report_matches_rederived_evidence` のような局所名にするか、`report_schema == CERTIFICATION_SCHEMA` と full 固有エラーを含む block 全体を old にする。「再導出を外す」`_canonical_full_report` 呼出しの old は一意のままでよい。
   - **自己判定:** **real**

3. **主張:** 新規 3 node に伴う既存 acceptance-duration ledger の更新が plan の実行項目から抜けている。

   - **file:line:** `brief.md:6,42`、`plan.md:74-102,174-180`、`test_paper_story_a2_certification.py:5312-5318`
   - brief は ledger 登録が必要と明記する一方、plan は二つの実装 file しか変更対象に挙げず、テスト手順にも ledger producer の実行を含めていない。
   - **成果物への影響:** ledger 完全集合を検査する meta-test があるなら、実装と対象テストが緑でも受入全走は赤になる。少なくとも新 node の所要時間被覆が成果物から欠落する。
   - **提案する対処:** 新しい台帳を作らず、既存 ledger への 3 node の add-only 更新を実行項目と変更所有者に明記する。正確な meta-test 名、producer invocation、命名上の追加制約を確定するには、射影外の `orchestrator/tests/acceptance_duration_ledger.json` とその producer/meta-test の参照が必要。
   - **自己判定:** plan の欠落は **real**。外部 meta-test の具体名は今回の射影だけでは未確認。

## 破れなかった箇所

- 3 負例はいずれも現行 materializer を通る。

  - `status` の `"observed-positive"` → `"reject"` は許可語彙内（`paper_story_a2_certification.py:4323-4325`）。analysis 形では status と cells の意味整合を検査しない（4491–4520）ため拒否されない。
  - `effects["rr5"]` の finite float 変更は、`effects` が exact `dict` であることしか見ない（4491–4502）ため拒否されない。
  - 偽 `driver_rcs` と indeterminate report は、validator が `driver_rcs` を参照せず、`_require_materializable_authority` も manifest/source authority だけを見る（1176–1187）。直接 `materialize` を呼ぶので `_collect_command` の attempt/driver 分岐（4720–4741）も介在しない。

- 予定変更後も、3 件は final の `differs from evidence re-derivation` だけで拒否できる。fixture の disk acquisition は正しいため読み直しは成功し、status/effects 変異は既存形検査を通る。偽 driver も canonical evidence へ戻した後に positive report と比較されて初めて不一致になる。

- 「読み直しを外す」変異の挙動設計自体は成立する。偽 `driver_rcs={"rr5": 7, "rr50": 0}` を使うと `_canonical_full_report` は raw 分類前に同じ indeterminate report を作る。後段の authority 検査も driver RC を拒否しないため、この負例だけが当該変異を殺す。ただし所見 2 のとおり old の一意化は必要。

- 「常に拒否」の完全な KILL 集合は、指定された現行 file 内では 2418、5274、3331、3395、3431、3455、3477、3499 の 8 node。3431/3455/3477 も後段の別エラーへ到達できなくなるため KILL になる。2947 は再導出より前の schema-chain 検査で落ちるため影響しない。新規負例 3 件は同じ専用エラーを期待するので、この変異下でも通る。

- 等価変異について、非 `dict` の report が比較へ到達する経路はない。4443 で `type(report) is dict` を要求し、expected も full canonicalizer の `dict` 戻り値である。canonical JSON として成果物になれる通常値について比較方向変更は等価である。

- 2418、3331 と `_materialization_case` 系はすべて `evidence["raw_results"]`、`raw_files`、`attempt_root` から report を作っており、再導出と同じ入力である（test file 2426–2431、3338–3342、3385–3389）。

- 5274 も静的には一致する。`load_raw_results` は manifest 作成・validation 後に未変更の raw files を再読込する（5277–5283）。再導出の frozen/raw 差は、condition receipt では 2451–2465、lock/WAL/claim では 3123–3152 の「同じ bytes の取得元」が違うだけである。fixture 中にその間の書換えはなく、attempt root も `_policy` の durable base と一致する。

- self-run harness は `pytest.main([__file__, "-q"])` なので新しい top-level node を自動的に含む（test file 5312–5318）。提案名はいずれも `test_` で始まり、helper は `_full_...` なので pytest の基本 discovery 規約にも適合する。

## 総括

3 負例の現行通過性、変更後の単一理由性、5274 を含む既存正例の継続性は静的に成立する。  
修正必須なのは、canonical evidence への早期切替による受理集合拡大と、変異 old 3 件の非一意性である。  
P4 は「不一致を拒否」ではなく「渡された bytes を無視して canonical bytes を出力」が正しい。  
新規 node の既存 ledger 登録も、外部正本を確認したうえで plan の明示的な実行項目に含める必要がある。