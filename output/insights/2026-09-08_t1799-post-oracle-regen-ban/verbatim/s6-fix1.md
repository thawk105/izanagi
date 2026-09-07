## 変更した file と要旨

- [sort_swo_dependency_material.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/campaign/sort_swo_dependency_material.py:507)
  - tree の mode 採取と chmod より前に、保護根自身の write bit を検査。
  - write bit がなければ、新 detail code `post-oracle-protected-root-not-writable` で拒否。
  - 既存検査、chmod、再走査、identity 照合、残存検査、復元の順序と内容は未変更。
- [test_sort_swo_dependency_material.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_sort_swo_dependency_material.py:216)
  - 重複 context の拒否、内側拒否前後の全 node mode 不変、外側退出後の exact 復元を実 filesystem で検査。

## 変更前の受理・拒否挙動と、変更後に変わる集合

変更前は、根の write bit が既にない場合も tree 全体を「元 mode」として採取し、2 個目の context が進入できました。

変更後に新しく拒否されるのは、exact 一致した保護根自身の mode が `0o222` を一切含まない入力だけです。配下 node の既存 mode は新しい拒否条件にしていません。

通常の単独保護、根に write bit がある入力、binding base の sibling 作成、generic build、既存の exact mismatch などの受理・拒否挙動は変更していません。

## 新規検査の nodeid

`orchestrator/tests/test_sort_swo_dependency_material.py::test_post_oracle_protection_rejects_overlapping_context_without_mode_change`

## 実走した検査 (nodeid と結果) または未実走の申告

`tools/run_tests.py` は予告どおり `qstat -Q` preflight で rc=16となり、child は起動されませんでした。

`PYTHONPATH=.` の自走 harness では、次の 6 node の test 関数本体を実走し、全件 PASS でした。

- 新規重複 context 検査
- `test_post_oracle_protection_restores_exact_modes_on_success_and_error`
- `test_post_oracle_protection_leaves_binding_base_writable_for_new_entry`
- `test_v2_post_oracle_effective_root_mismatch_never_starts_build`
- `test_v2_post_oracle_build_cannot_rewrite_identical_material_bytes`
- `test_v2_generic_build_does_not_enter_post_oracle_protection_or_change_argv`

`git diff --check` も成功しています。正規 runner による pytest 実走は未実走です。

## 波及可能性の静的列挙

- 直接の production caller は [buildcache.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/campaign/buildcache.py:2713) の post-oracle build 分岐だけです。
- 間接 consumer は `s8b_floor_campaign.py` の post-oracle binding 経路です。同一根で後発した build は build 開始前に拒否されます。
- 関連 consumer test は `test_buildcache_v2.py`、`test_s8b_floor_campaign.py`、`test_sort_swo_dependency_material.py` です。
- 共有 fixture は変更していません。新規検査は `tmp_path` 内だけで完結します。
- generic build と binding なし caller への波及はありません。

## 総括

指定された重複 context の欠陥だけを修正しました。変更は実装 1 file、検査 1 fileの計 2 fileで、docs、既存期待値、commitには触れていません。正規 runner の実走は親側で必要です。