# 親が commit 前に差分を読んで掴んだ疑義 (段 6 レビューの照準)

親は実装面を直接編集しない。以下は所見であって修正ではない。
レビュー子は**これを鵜呑みにせず独立に判定**し、real なら根拠つきで、refuted ならなぜ違うかを書け。
親の見落としを探すことも仕事である。

## 疑義 A1: 共有 test fixture の既定値を変えた

`orchestrator/tests/test_s8b_floor_campaign.py` の共有 fixture
`_FIXTURE_DEPENDENCY_RECEIPT["config_sha256"]` が、この wave で
`"b" * 64` から `hashlib.sha256(b"fixture-dependency-config").hexdigest()` へ変わった。

段 6 の fix 子は、赤になった 3 箇所 (`test_floor_postflight_staged_source_set_and_expected_hash_are_enforced`、
`test_build_cells_production_postflight_rejects_dependency_drift` の正例部分、
`test_phase_marker_is_create_only_fsynced_private_and_carries_dependency_hash`) で
`dataclasses.replace(..., config_sha256="b" * 64)` を明示して元の値へ戻した。

**しかし明示的に戻していない他のテストは、新しい値で走っている。**

問うべきこと:
- 共有 fixture の既定値を変える必要が本当にあったか。`"b" * 64` のままで新設テストは書けなかったか。
- 値が変わったことで、明示していないテストの**検査の意味**が変わっていないか。
  とくに「この値と別の値が一致しないこと」を見るテストが、偶然一致するようになっていないか、
  逆に「一致すること」を見るテストが別経路で通るようになっていないか。
- 3 箇所だけ戻して他を戻さない状態は一貫しているか。一貫していないなら、
  どちらへ揃えるのが既存契約に忠実か。

## 疑義 A2: build 境界から実 source の receipt 再観測が消えた

`buildcache.py` の `_assert_post_oracle_dependency_material` から、次の照合が削除された。

```
expected_receipt = {"masstree_head": ..., "config_sha256": ...}
if _observe_fetchcontent_dependency_receipt(source_root) != expected_receipt:
    raise BuildCacheError("FetchContent dependency HEAD/config.h が oracle binding と不一致")
```

代わりに `sort_swo_dependency_material.assert_source_matches_canonical(...)` へ
`expected_head=` を渡す形になった。

問うべきこと:
- `_observe_fetchcontent_dependency_receipt` は HEAD の照合だけでなく、
  **実 source root が VCS の top-level であること**、**HEAD が一意に取れること**、
  **root が canonical な non-symlink directory であること**も検査していた。
  新しい `assert_source_matches_canonical` はそれらを**完全に**包含するか。
  1 つでも落ちていれば、それは受理集合の拡大である (規律 2)。
- `_observe_fetchcontent_dependency_receipt` は他の呼び出し元がまだ使っているか。
  使っているなら、2 経路で別の検査規則になっていないか (F625 の型)。

## 疑義 A3: `build_v2` の archive 検査が `elif` で分岐した

```
if post_oracle_binding is not None:
    _assert_post_oracle_dependency_material(post_oracle_binding)
elif dependency_archive_sha256 is not None:
    observed_archive_sha256 = ...
```

問うべきこと:
- `post_oracle_binding` があるとき、`dependency_archive_sha256` による検査が走らなくなる。
  `binding["archive_sha256"]` がそれを完全に代替するか。
  2 つの値が別の出所を持つなら、片方の検査が黙って消えている。
- 呼び手が `post_oracle_binding` と `dependency_archive_sha256` の**両方**を渡し、
  かつ両者が食い違う入力を作れるか。作れるなら、その入力で何が起きるか。

## 親が既に確定させた事実 (再調査は不要)

- 帰属赤 8 件は fix 後にすべて緑。親が実走した結果:
  `test_buildcache_v2.py` 176 passed / `test_s8b_floor_campaign.py` 461 passed 2 skipped 1 failed /
  `test_sort_swo_dependency_material.py` 13 passed 1 skipped /
  consumer 群 147 passed / 143 passed。
- 残る 1 failed は `test_real_output_snapshot_excludes_git_ignored_real_output_changes` で、
  **非帰属**である。`git_ignored_output_prefixes` は実在する untracked ignored path しか返さず、
  fresh worktree には `output/runs` が実在しないため必ず落ちる。`.gitignore:18` に規則自体はある。
  この wave の差分と無関係。**触るな。**
- `test_s8b_approved.py` の `ModuleNotFoundError: No module named 'tests'` は
  file 選択走の偽赤であり回帰ではない (`DW-O18`)。
