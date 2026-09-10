## 変更した file と要旨

- [sort_swo_dependency_material.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/campaign/sort_swo_dependency_material.py:494)
  - post-oracle 専用 context manager を追加。
  - 実効 build 根と binding source 根を canonicalize して exact 照合。
  - 一致した根と全配下 node の write bit のみ除去し、親 directory は変更しない。
  - chmod、保護後検査、mode 復元の失敗を fail-closed 化。
  - 正常、consumer 例外、保護検査例外の各経路を `finally` で exact mode 復元。

- [buildcache.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/campaign/buildcache.py:2708)
  - post-oracle 束縛時だけ、既存の configure 後 2 assert の後で `protected_root` を取得して context 内で build。
  - build 後の `effective_root` は既存位置で改めて取得するまま維持。
  - 束縛なし build の既存 build arm と configure argv は変更なし。

- [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_buildcache_v2.py:1373)
  - M1、M2、generic 非到達・argv 不変検査を追加。

- [test_sort_swo_dependency_material.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_sort_swo_dependency_material.py:175)
  - M3、M4 の実 helper 検査を追加。

docs、`external/ccbench`、公開 API、receipt schema、cache identity、submodule pin は変更していません。

## 変更前の受理・拒否挙動と、変更後に変わる集合

変更前は、post-oracle の最後の材料 assert 後も source tree が書込み可能で、同一 bytes の再生成は後段 hash 検査を通過できました。実効根不一致は build 実行後に拒否されていました。

変更後は次のとおりです。

- 実効根不一致は最終的な拒否集合を変えず、拒否時点だけ build 前へ移動します。
- 同一 bytes を含め、保護中に判定済み根へ書き込む build を新たに拒否します。
- chmod 不能 node、または保護後も write bit が残る node を含む根も新たに拒否します。
- 正常な up-to-date post-oracle build は、全 node を保護・復元できる限り引き続き受理します。
- `<base>` 自身は保護しないため、sibling entry の新規作成は引き続き受理します。
- 束縛なし build の受理・拒否、configure argv、既存検査順序は不変です。

## M1〜M4 の各検査の置き場所と nodeid

- M1: [test_buildcache_v2.py:1373](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_buildcache_v2.py:1373)  
  `orchestrator/tests/test_buildcache_v2.py::test_v2_post_oracle_effective_root_mismatch_never_starts_build`  
  例外型ではなく `events == ["configure"]` を固定します。

- M2: [test_buildcache_v2.py:1410](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_buildcache_v2.py:1410)  
  `orchestrator/tests/test_buildcache_v2.py::test_v2_post_oracle_build_cannot_rewrite_identical_material_bytes`  
  実 helper の保護中に `config.h` と archive の同一 bytes 再書込みが失敗することを検査します。

- M3: [test_sort_swo_dependency_material.py:175](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_sort_swo_dependency_material.py:175)  
  `orchestrator/tests/test_sort_swo_dependency_material.py::test_post_oracle_protection_restores_exact_modes_on_success_and_error`  
  正常終了と例外終了を単一 node で検査します。

- M4: [test_sort_swo_dependency_material.py:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1799-regen-ban-author/orchestrator/tests/test_sort_swo_dependency_material.py:216)  
  `orchestrator/tests/test_sort_swo_dependency_material.py::test_post_oracle_protection_leaves_binding_base_writable_for_new_entry`

追加の generic 検査:

- `orchestrator/tests/test_buildcache_v2.py::test_v2_generic_build_does_not_enter_post_oracle_protection_or_change_argv`

## 実走した検査 (nodeid と結果) または未実走の申告

- 上記新設 5 node: `5 passed`
- `orchestrator/tests/test_buildcache_v2.py`: `219 passed`
- `orchestrator/tests/test_sort_swo_dependency_material.py`: `16 passed, 1 skipped`
  - skip: `test_real_prebuilt_masstree_material_is_pinned_when_explicitly_configured`
  - `IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` 未設定のため、protected real CMake build は未実走です。
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: `違反なし`
- `git diff --check`: OK

test file の新設・改名はなく、静的検索でも file 集合列挙 meta-test の更新対象はありませんでした。

## 波及可能性の静的列挙

- 束縛付き production caller は `s8b_floor_campaign.py` の `sort_best` build のみです。
- 束縛なし caller の `pipeline.py`、各 backoff sweep、B-10、oracle pilot は generic branchに留まり、今回の保護へ入りません。
- 共有 fixture の consumer は `test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_real_repo_serialization.py`、`test_sort_swo_dependency_material.py` です。fixture 自体の signature は変更していません。
- `test_s8b_floor_campaign.py` は capability の生成・転送を検査するため、唯一の上位 consumer test 面です。
- 同一根を並行利用する context 間の排他はありません。SIGKILL、OOM、walltime kill では `finally` が走らず、根が読取専用のまま残り得ます。
- owner 自身による chmod 巻戻しと privileged actor は discretionary-mode 保護の対象外です。

## 総括

plan v2 の 1〜6を実装し、指定した焦点 test と変更 test file 全体は緑です。実 CMake を用いた protected build のみ環境未設定で未実走です。変更は4 fileだけに残し、`git add`、commit、push は行っていません。