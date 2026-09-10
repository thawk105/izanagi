## (1) 着手前の受理・拒否挙動

現行 issuer は build receipt の top-level `protocol` を探すため、実 receipt では常に `missing=("protocol",)` となり、権威 floor の発行を拒否していました。現行テストは receipt validator を monkeypatch し、実 schema にない偽の top-level key を通して拒否を迂回していました。

## (2) 変更した file:line と要旨

- [p3_b4_floor_artifact_issuer.py:33,746-810,831-837](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2423-author/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:33)
  - `protocol_from_floor_genome` を循環 import なしで導入。
  - receipt の path、SHA-256、JSON 読込を維持し、`binding.genome_canonical` から protocol を導出。
  - malformed、欠落、混在、全失敗、artifact 空を `missing=("protocol",)` として fail-closed。
  - threads、workload、campaign の到達不能な missing 分岐を削除し、保証元を docstring に記載。
  - summary loader の docstring を receipt binding 由来の実態へ更新。
  - `_authority_value` の guard と文言は維持。

- [test_floor_pair_driver.py:52,155](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2423-author/orchestrator/tests/test_floor_pair_driver.py:52)
  - `_portable_build_record(..., genome_canonical=None)` と `_write_inputs(..., genome_canonicals=None)` を追加。
  - 既定 receipt bytes は変更前後で一致:
    - candidate: 3095 bytes、`ce43374176abdad407277a6ea57cebdd8764c3b329401de0454c57307999886a`
    - reference: 3095 bytes、`f1795d7826746e7fa796beb034b9b3a09853659b95b992907a1ed120dd9675be`

- [test_p3_b4_floor_artifact_issuer.py:42,206,477-564](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2423-author/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:42)
  - `receipt_has_protocol` と receipt validator monkeypatch を完全撤去。
  - `Genome(...).canonical()` を使う mocc 正例、既定 JSON／未整列 genome 負例、mocc／silo 混在負例を追加。
  - 実 `finalize_floor` summary からの発行、`__protocol-mocc`、authority protocol を検査。
  - 有効 identity と非空 missing を併存させた `_authority_value` guard test を追加。

## (3) 実走結果

Pegasus login node 規律に従い、指定 pytest 引数を runner 経由で実行しました。

```text
PYTHONPATH=. python3 tools/run_tests.py \
  orchestrator/tests/test_p3_b4_floor_artifact_issuer.py \
  orchestrator/tests/test_floor_pair_driver.py \
  -q -p no:cacheprovider
```

結果は `rc=16`、pytest child 未起動です。`qstat -Q` が `EACCTAUTH Unknown user-id (uid: 31609)` で失敗し、login node 側も headroom 予約台帳を安全に更新できませんでした。`--collect-only` も同じ理由で child 未起動でした。

- 実走 nodeid: 0
- pytest の赤: 0
- infrastructure failure: 2回
- issuer の静的想定 nodeid: 23
- driver 全 test: 実装済み・未実走
- 自走 harness: repo 規律上、runner を迂回できないため未実走
- AST parse、`git diff --check`: 成功
- `closed` とは申告しません。

## (4) 変異 M1〜M8

以下の nodeid は殺す予定の対象で、infrastructure failure のため未実走です。

- M1 anchor: `protocol = protocol_from_floor_genome(binding["genome_canonical"])`
  - `test_real_finalize_floor_summary_is_issued_with_receipt_protocol`
- M2 anchor: 同上
  - `test_real_finalize_floor_summary_is_issued_with_receipt_protocol`
- M3 anchor: `if protocol_failed or len(protocols) != 1:`
  - `test_mixed_receipt_protocols_are_rejected`
- M4 anchor: `protocol = protocol_from_floor_genome(binding["genome_canonical"])`
  - `test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected[unsorted-flags]`
- M5 anchor: `if hashlib.sha256(raw).hexdigest() != receipt_sha:`
  - 帰属不成立。既存 driver の receipt 改変 test は producer loader で先に拒否され、issuer の `continue` に到達しません。登録 nodeid なし。
- M6 anchor: `f"__protocol-{identity.protocol}"`
  - `test_authority_filename_contains_all_five_derived_components`
- M7 anchor: `if summary.identity is None or summary.missing_identity_elements:`
  - `test_authority_value_rejects_nonempty_missing_protocol_with_valid_identity`
- M8 anchor: `missing.append("protocol")`
  - `test_identity_is_not_a_caller_surface_and_noncanonical_genomes_are_rejected[json-fixture]`

## (5) 所有外 caller・共有 fixture・consumer test への波及

- 所有外の production caller は `p3_b4_material_report.py` の `resolve_preregistered_authoritative_floor` 呼出しです。公開 API、authority schema、filename schema は不変です。
- `_portable_build_record` の caller は driver test 内だけです。既存 caller は全て既定引数のままです。
- `_write_inputs` の既存 driver test caller も全て既定引数のままです。issuer test だけが新 keyword を使用します。
- consumer test は `test_p3_b4_material_report.py`。変更していません。
- `test_module_source_has_no_frozen_fallback_or_publish_bypass` の走査対象へ禁止文字列は追加していません。
- acceptance duration ledger には改名前の2 nodeidが残っています。所有外かつ裁定で編集禁止のため未変更です。
- `floor_pair_driver.py`、docs、schema、driver、receipt validator は未変更です。
- tracked 差分は指定された3ファイルだけです。

## (6) 裁定と食い違って止めた点

実装を止める裁定上の食い違いはありません。現物には `receipt_has_protocol=True` の呼出しが9件ではなく5件あり、5件すべてを書き換え、唯一の `False` 呼出しも撤去しました。

採用したのは裁定どおり案 (c) です。案 (a) を望む場合は再裁定が必要です。停止したのはテスト実走だけで、原因は PBS の UID 認証失敗です。

## 総括

- receipt binding 由来の protocol identity を実装済みです。
- fail-closed、schema、driver、既定 fixture bytes は維持しています。
- 差分は所有3ファイルのみで、commit・push・branch 操作はありません。
- pytest は infrastructure failure により未実走のため、完了扱いにはしていません。