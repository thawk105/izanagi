静的結論は **NO-GO** です。pytest は実行しておらず、緑とは判定していません。

## 1. 新規10 nodeid

1. `...test_evidence_contract_hash_rejects_nul_path[required-evidence]`
   **real / High**。旧実装なら `evidence_contract_sha256()` は hash を返すため `pytest.raises` で止まり、恒真ではない。一方、fixture は最後の condition・最後の required path だけを変更する（[s2:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:144)、[s2:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:148)）。「最後だけ検査する」壊れた実装は通る。pointer 期待値自体はテスト fixture の独立計算で、実装からの導出ではない。
   影響: 先頭・中間の required path に NUL が残ると、hash・`protected_sha256`・凍結 record が生成され続ける（[core:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1416)、[core:1669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1669)）。

2. `...test_evidence_contract_hash_rejects_nul_path[consumer-requirement]`
   **real / High**。旧実装では赤になるが、最後の consumer path しか検査しない実装を検出できない。consumer は12箇所あるのに、最後の1箇所だけを変更している（[s2:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:155)）。
   影響: 未検査の consumer path に NUL があれば、検証時の evidence hash と凍結 record が受理される（[core:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1407)）。

3. `...test_evidence_contract_hash_accepts_non_nul_path_controls[cr]`
   **real / Medium**。新実装なしでも現行実装が64桁 hashを返すため通る。回帰テストとしては意図的だが、`len(...) == 64` だけなので、誤った64桁 hashやCR正規化でも通る。さらに required path しか試していない（[s2:199](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:199)、[s2:202](/work/1/SFC/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:202)）。
   影響: CRを誤って拒否・正規化すると、非NUL入力の hash 受理集合または record の evidence hash が変わる。

4. `...test_evidence_contract_hash_accepts_non_nul_path_controls[lf]`
   **real / Medium**。3と同じ。旧実装でも通り、consumer path のLFは未検査、hash値も固定していない。
   影響: consumer path のLFを誤拒否すると、裁定(c)が禁じる「NUL以外の拒否」へ受理集合が狭まる。

5. `...test_evidence_contract_hash_accepts_non_path_nul`
   **real / Medium**。旧実装でも通る意図的回帰テストだが、64桁であることしか見ていない。`static_only_note` のNULを拒否する過剰な全文字列検査を防ぐ役割はある。
   影響: このテストが弱いままだと、非path NULを誤拒否して evidence hash・protected hash・凍結受理集合を変える実装が残る（[s2:206](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:206)）。

6. `...test_evidence_contract_hash_accepts_unconsumed_schema_path_nul`
   **現行v1限定では refuted、将来スキーマについて real / Major**。loaderが読むpathは required path と consumer pathだけ（[evidence:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:226)、[evidence:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:253)）なので、`metadata.path`を受理する現行設計は説明可能。しかし親briefのP2は「exactな`path` keyを再帰検査」であり、このテストはNUL pathを意図的に保護対象外へ固定している（[s2:213](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:213)）。
   影響: この方針を明文化せず残すと、将来追加されたpath位置のNULが hash・protected hash・凍結台帳へ入る。

7. `...test_evidence_contract_hash_preserves_canonicalization_reason_before_nul`
   **refuted / nit**。旧実装でも `evidence-contract-json` になり、意図的なreason優先順位テストである。検査をcanonicalization後へ置く設計（[s2:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:60)）は、NUL+unpaired surrogateでもfail-closedであり、NUL-free入力のreason順序は変えない。
   影響: 省略しても成功する成果物の値は変わらず、混合不正入力のreasonだけが変わり得る。

8. `...test_current_evidence_contract_hash_is_frozen`
   **refuted / Low**。旧実装でも通るが、これは実装検出ではなく、現行hashの独立literal固定である。g1 recordの値とも一致する（[condition-freeze.v1.g1.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1)）。
   影響: 省略すると、現行契約のhash driftを見逃し、既発行g1の `evidence_contract_sha256` / `protected_sha256` との不一致を検出できない。

9. `...test_validate_condition_freeze_at_rejects_legacy_frozen_nul_path_contract`
   **到達性は refuted、hash oracle は real / High**。fixtureではg1だけを追加するため、namespace unknown・ruling reference・spurious revisionには倒れず、hash計算へ到達する（[core:1346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1346)、[core:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1416)）。ただし「legacy hash」を `M._sha256(M._DOMAIN_EVIDENCE + M._canonical_bytes(...))` で再構成している（[s2:266](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:266)）。canonicalization・domain・hash実装が変更されると、fixtureも同時に現行実装へ追随する。
   影響: 独立した旧hashでないため、旧recordの実際の証拠hash／protected chainの互換性破壊を見逃し、履歴検証結果を誤って受理側へ寄せ得る。

10. `...test_prepare_revision_rejects_nul_path_contract_before_create`
    **到達性は refuted、網羅性は real / Medium**。g1なしなので、`prepare_revision()`はnamespace確認後にsource/evidenceを読み、hashへ到達する（[core:1688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1688)、[core:1725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1725)）。ただし既存freezeがある分岐と、production reportの `freeze_reason_code` / `condition_freeze_valid` / `protected_sha256` / `effective` は検査していない。
    影響: 直接APIは拒否しても、report側がfreeze valid・protected hashありとして扱う退行を見逃す可能性がある。

## 2. fixture と helper

**実在性についての real 所見はない。全件、signatureも整合する。**

- `_init_repo(tmp_path, *, filled=False) -> Path`: [core test:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:84)
- `_write(root, relative, raw) -> None`: [core test:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:99)
- `_commit(root, subject) -> str`: [core test:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:105)
- `_record_raw(...) -> bytes`: [core test:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:111)
- `_install_g1(root) -> tuple[str, bytes]`: [core test:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:135)
- `M._record_document(...)`: 6引数の実装がある（[core:1648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1648)）。
- `M._strict_json(raw, *, what)`: [core:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:329)
- `M._sha256(raw)`: [core:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:296)
- `M._DOMAIN_EVIDENCE`: [core:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:113)
- `M._canonical_bytes(value)`: [core:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:300)
- `M.parse_preregistration_markdown(raw)`: [core:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:835)
- `M.generation_path(number)`: [core:999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:999)

`_record_raw()` は内部で既存の `evidence_contract_sha256()` を呼ぶ（[core test:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:120)）ため、修正後のNUL fixtureには使えない。プランがlegacy record生成に直接 `_record_document()`を使うのは正しい。

`_init_repo()`が書く `{"predicates":[]}`（[core test:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:92) も矛盾しない。両E2Eはその後、現行contractを上書きしてから呼ぶ（[s2:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:261)、[s2:317](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:317)）。base commitにはfreeze generationがないため、履歴検証もbaseのdummy contractをschema-loadしない。

## 3. exception message

**refuted / nit**。`PreregistrationError`はdetailが空ならreasonのみ、非空なら `[reason] detail` になる（[core:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:121)、[core:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:123)）。

したがって実装が `repr(pointer)` をdetailとして渡すなら、

```text
[evidence-contract-path-nul] '/conditions/11/consumer_requirement/path'
```

の形で、プランの `f"[evidence-contract-path-nul] {pointer!r}"` と一致する。`read_blob_at()`がdetailなしでreasonのみを返す契約（[core:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:969)、[core test:1029](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:1029)）は別APIの契約であり、今回と矛盾しない。成果物値への影響はなく、違えばテストが赤くなるだけなのでnit。

## 4. E2E到達性

- `prepare_revision()`は、fixtureにfreeze namespaceがないため `freeze-namespace-unknown`、`record-ruling-reference`、`spurious-revision`を通らない。source parse後に evidence hashへ到達する（[core:1721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1721)）。
- 履歴検証fixtureは正規のg1 pathだけを追加し、g1なので ruling checkも不要。record schemaを通過した後、source parseとevidence hashが実行される（[core:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1397)、[core:1419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1419)）。

よって、指定された二つのE2Eが想定reasonより前に別reasonで倒れるという懸念は **refuted**。ただし、legacy hashの自己参照は別問題として **real**。

## 5. 親briefと静的解析・meta-test

親の主張は分解が必要。

- **「C述語の静的解析には影響しない」**は **refuted（影響するという懸念が誤り）**。contractのpathは証拠artifact群であり、core module pathはない（例: [contract:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:9)、[contract:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:480)）。`_reachable_calls()`は渡されたartifact ASTだけを解析する（[evidence:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:354)）。
- **「protected_sha256には影響しない」**も狭義には正しい。preimageはevidence hash、normative body、section5 names、section6 conditionsだけで、core module hashは含まない（[core:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:183)）。
- しかし **「従って成果物全体へ影響しない」なら real / High**。`activation_report_at()`はcore blobを明示的にhashし（[core:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1559)、reportに格納する（[core:1611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1611）。そのreport digestも変わり（[core:1771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1771）、trial launch admission／台帳へ伝播する（[trial_registry.py:1238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/trial_registry.py:1238)）。既存commitを新coreで再検証すれば、core blob mismatchによりcertified選択が未発効化する経路もある（[core:1592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1592)）。
- CLI command一覧はchoicesだけを検査する（[core test:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py:939)）。repo scanもcore pathの存在を確認するだけ（[invariant:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_invariant.py:30)）。docs対応はliving docとtest moduleの列挙で、関数一覧・`__all__`・core行数上限の検査は見つからない（[check_docs.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/tools/check_docs.py:50)、[tests/README.md:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/README.md:162)）。この部分のmeta-test懸念は **refuted**。

## 6. 抜けているテスト案

受理集合の十分性はまだありません。特にCR/LFはrequired pathだけで、consumer pathを試していません。また、`len(hash) == 64`は受理だけを見ており、hash値の保存を見ていません。

追加すべきnodeid案:

- `test_evidence_contract_hash_rejects_nul_at_every_consumed_path`
- `test_evidence_contract_hash_accepts_non_nul_path_controls[required-cr]`
- `test_evidence_contract_hash_accepts_non_nul_path_controls[required-lf]`
- `test_evidence_contract_hash_accepts_non_nul_path_controls[consumer-cr]`
- `test_evidence_contract_hash_accepts_non_nul_path_controls[consumer-lf]`
- `test_evidence_contract_hash_preserves_exact_hash_for_non_nul_corpus`
- `test_validate_condition_freeze_at_legacy_fixture_uses_independent_pre_t739_hash`
- `test_activation_report_marks_legacy_nul_bound_freeze_invalid`
- `test_prepare_revision_rejects_nul_path_contract_with_existing_freeze`
- `test_existing_g1_record_bytes_and_protected_hash_are_unchanged`
- `test_core_module_rebinds_report_digest_without_changing_protected_hash`

最初のnodeidは、現行contractの38個のpath位置を1つずつ変えて、各pointerで拒否する必要があります。未知pathを受理する方針を採るなら、将来schemaでpath位置を追加したときにhelperとの同期を検査する静的testも必要です。

## 総括

1. real所見は、(i) 最後のpathしか検査しない実装を通す、(ii) consumer側のCR/LF未検査、(iii) `len==64`だけの弱い受理確認、(iv) legacy hash oracleの自己参照、(v) report／certified／台帳へのcore blob hash波及の未記載、(vi) report-level E2E不足です。
2. 上記の追加nodeidを入れ、legacy hashを固定raw bytes＋独立literalへ置き換えるべきです。
3. **NO-GO**。少なくとも独立oracle、全path位置検査、consumer CR/LF、report-level fail-closed確認、core module hashの下流影響の明記を満たしてから実装してください。
