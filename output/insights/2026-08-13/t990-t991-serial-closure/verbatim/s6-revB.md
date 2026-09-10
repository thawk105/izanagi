## 所見

1. **real / must-fix** — `source_digest` の Git 環境衛生が status だけに適用され、proof chain 内で参照 repository が分裂する。  
   根拠: `source_digest.py:765-775` は危険な Git env を除去する一方、`_git_show()` (`:597-601`) と `_tracked_diff_sha256()` (`:808-816`) は親 env を継承する。`resolve_evidence()` (`:858-868`) は三者を同一 snapshot として結合する。新テスト `test_campaign.py:10238-10262` は `_tracked_status_paths()` 単体しか撃たない。  
   直さない場合: 汚染 env 下で `source_root`・tracked paths と baseline/diff hash が別 repo 由来になり、proof chain の source evidence と certified 選択・受理集合が不正に変わり得る。

2. **real / must-fix** — 段 4 の `(i)+(ii) = 80〜120 行` 目安を超過している。  
   根拠: 全差分は 348 行追加。R4 の中核だけでも `patchharness.py` 28行、`conftest.py` の stamp/hook 12行、collection report 57行、閉包 helper 51行で **148行**。controls と guard test まで含めると約219行である。  
   直さない場合: certified 値自体は変わらないが、検査面積と受入時間・故障点が増え、赤または timeout 時に proof chain と certified 選択結果が発行されない。

3. **refuted / nit** — `pytest_runtest_protocol` の hook 契約・返値は現行 pytest に適合する。  
   根拠: `conftest.py:434-442` の `wrapper=True` と `return (yield)` は pytest 9.1.1／pluggy 1.6.0 の新式 wrapper に適合し、first-result の返値も保存する。現環境では xdist、pytest-cov、Hypothesis は同 hook を実装せず、pytest-randomly は未導入。cacheprovider も同 hook を持たない。  
   直さない場合: certified 選択結果、proof chain、受理集合は変わらない。

4. **refuted / nit** — growth-test hold の configure/unconfigure 順序契約は壊していない。  
   根拠: hold の session 印は `conftest.py:562-566` と `:946-965`、新 wrapper は item protocol の `:434-442` に独立している。例外時も context manager の `finally` で印を戻す。  
   直さない場合: hold の受理集合と certified/proof chain は変わらない。

5. **real / nit** — `ContextVar` による guard は新しい OS thread へ自動伝播しない。  
   根拠: `patchharness.py:45-55,272-286`。現行の実共有 submodule checkout 経路には thread 実行を確認できなかったため、現在の22 nodeに対する即時回帰ではない。  
   直さない場合: 将来、未登録 test が別 thread で checkout すると guard を迂回し、共有 source 競合により proof chain や受理集合が変わり得る。

6. **real / nit** — fixture 閉包処理のコストは厳密には `O(Σ item の fixture closure 長)` で、collection item 数に比例する。  
   根拠: `test_real_repo_serialization.py:402-443,445-477,548-596`。helper は `:703,823,881,962,977` から計6回呼ばれ、最後は2回ループする。履歴・台帳・Python file 全走査は新設していないため、D311/D335 の禁止対象ではない。  
   直さない場合: 値は不変だが、collection 成長に伴う受入時間増で certified 結果と proof chain が未発行になり得る。

7. **real / nit** — 優先順メタテストは22 nodeの追加自体ではほぼ増えないが、report 拡張を全 suite collection 3回で負担する。  
   根拠: `test_real_repo_priority_order_is_literal_and_writers_follow_barrier` は `test_real_repo_serialization.py:962` と `:977-981` で通常・`--ff`・`--nf` の3回収集する。22名追加は set membership と小さい sort の増加だけで、主要増分は全 item の fixture closure／JSON化である。  
   直さない場合: 順序・certified 値は不変だが、受入 wall time 超過時に proof chain が閉じない。

8. **real / nit** — 16.21秒の新設検査は、既存の全 suite collection subprocess が構造上の支配項と見積もる。ただし純増時間は未分離。  
   根拠: `test_real_repo_serialization.py:700-713` は従来からの収集1回に、collection 内の線形走査と親側集合検査を追加した形で、新しい subprocess はない。baseline 計測がないため「純増何秒」とは認証できない。  
   直さない場合: certified 値は不変だが、未把握の純増が wall budget を超える場合は受理結果が得られない。

9. **real / nit — 検出可能・統合時要調整** — t983 による17 nodeの rename は literal coupling を赤にする。  
   根拠: `conftest.py:228-252` と独立 golden `test_real_repo_serialization.py:80-96`、未収集検査 `:788-796`。現在の t983 worktree では17名はすべて存続し、未コミット変更は `tools/codex_reasoning_ab.py` のみだった。  
   直さない場合: stale 名は false green にならず受入を停止するため、誤った certified 値は出ないが、proof chain と受理集合が未確定になる。

10. **refuted / nit** — skipif 付き3 canaryは、skip 環境でも新設 collection 検査を赤にしない。  
    根拠: `test_s8b_floor_campaign.py:3450-3455,3493-3498`、`test_s8b_oracle_driver.py:4613-4618`。`skipif` は item 収集後の runtime skip であり、marker/stamp と collected count は存在する。`benchmark_snapshots` の runtime `pytest.skip()` (`test_codex_reasoning_ab.py:275-279`) も同様。  
    直さない場合: certified 選択結果、proof chain、受理集合は変わらない。

11. **refuted / nit** — T-991 の新規単体テストは既存 patchharness test の完全重複ではなく、要求された二条件を両方撃つ。  
    根拠: 既存 `test_campaign.py:10198-10213` は patchharness の optional-lock 上書きだけ。新規 `:10238-10262` と `test_s8b_protocol_builder.py:426-449` は親の `GIT_OPTIONAL_LOCKS=1` を `0` にし、危険な6変数をすべて除去する。hash・時刻・実 working-tree path は期待値に焼き込んでいない。  
    直さない場合: 単体 helper の受理値は変わらない。ただし `resolve_evidence` 全体の穴は所見1のとおり残る。

## 既存回帰のリスク

- `test_real_repo_group_collection_exactly_matches_canonical_nodes`  
  親確定済みの空閉包退行により、現在の14 passedは fixture 閉包の実効性を証明していない。

- `test_real_repo_priority_order_is_literal_and_writers_follow_barrier`  
  順序意味論の回帰は見つからないが、全 suite report 拡張を3回負担する。

- `test_growth_test_holds_contract.py` と `test_pytest_failure_digest.py::test_nested_pytest_main_currently_clears_outer_failure_stash`  
  lifecycle 衝突は静的には refuted。ただし新 wrapper を含む実走は未確認。

- `test_source_digest_allowlist`、`test_source_digest_include_change_rejected_by_resolve`  
  通常 env では従来挙動のまま。危険な Git env を置いた `resolve_evidence` E2E がなく、所見1を検出できない。

- `test_codex_reasoning_ab.py` の17 consumer  
  現在は全名が存在する。t983 land 後に rename があれば collection exact test が fails-closed で検出するため、統合後再走が必要。

- 実共有 submodule canary 3件  
  collection だけは確認済みだが、新 runtime hook と実 checkout の結合は未実走。

## must-fix の一覧

1. 親確定済み: `test_real_repo_serialization.py:402-443`  
   `shared_fixture_closure()` が実際の共有 fixture を非空で返すよう修正し、少なくとも既知の系統1・3 fixture名と複数 consumer を独立 positive control で固定する。空 closure では control 自体を通さないこと。

2. 新規: `source_digest.py:597-601,765-775,808-816,844-868`  
   source_digest 内の Git read を共通 sanitizer に統一し、status・diff・show が同じ明示 root を見るようにする。scope拡張になるなら fix 子へ直投せず、親の再裁定へ戻す。`resolve_evidence` に危険 env を置く consumer testを追加する。

3. 新規: R4実装の規模超過  
   detector を弱めず、中核148行を120行以下へ縮約するか、超過理由を親が明示的に再裁定する。per-item closure と consumer集約の二重表現・重複型検査が主な縮約候補。

4. 統合条件: t983 land 後  
   17 node名を再照合し、renameがあれば `conftest.py` と独立 goldenを同時更新して collection exact testを再走する。

## 親が次に走らせるべき nodeid

優先度1:

- `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `orchestrator/tests/test_campaign.py::test_patchharness_real_shared_checkout_guard_is_pytest_only_and_fails_closed`
- `orchestrator/tests/test_campaign.py::test_source_digest_status_scrubs_git_environment_and_disables_optional_locks`
- `orchestrator/tests/test_s8b_protocol_builder.py::test_repo_status_scrubs_git_environment_and_disables_optional_locks`

優先度2:

- `orchestrator/tests/test_campaign.py::test_source_digest_allowlist`
- `orchestrator/tests/test_campaign.py::test_source_digest_include_change_rejected_by_resolve`
- `orchestrator/tests/test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged`
- 所見1の修正後に追加する、危険 Git env 付き `resolve_evidence` consumer node

優先度3 — 実 checkout 結線:

- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2`

優先度4 — lifecycle／統合:

- `orchestrator/tests/test_growth_test_holds_contract.py`
- `orchestrator/tests/test_pytest_failure_digest.py::test_nested_pytest_main_currently_clears_outer_failure_stash`
- t983 land 後の `orchestrator/tests/test_codex_reasoning_ab.py`
- 変更 test file 単独走として `orchestrator/tests/test_campaign.py` と `orchestrator/tests/test_s8b_protocol_builder.py`

## 未確認のまま残した点

- 私自身はpytestを走らせていない。緑と認定した追加範囲はない。
- fixture report 拡張の純増秒数はbaselineがなく、16.21秒から分離できない。
- `ContextVar` の thread 越境は実走していない。現行 sensitive callerにthread経路は見つからなかった。
- t983の今後のrename有無は未確定。確認時点では17 node名は不変だった。
- レビュー中に外部から実装差分が commit `47ce274b` へ入り、さらに main が merge `732081f1` で取り込まれた。私は書込みをしていない。7対象ファイルにmerge由来の追加差分がないことは再確認した。
- Web検索は使用していない。

## 総括

判定は **NO-GO**。親確定済みの空閉包退行に加え、`source_digest` が status だけをsanitizeしてdiff/showと異なるrepositoryを参照し得る新しいproof-chain不整合、および段4規模目安の超過がmust-fixである。hook順序、pytest 9.1.1契約、growth hold、skip collectionには現時点で回帰を認めない。