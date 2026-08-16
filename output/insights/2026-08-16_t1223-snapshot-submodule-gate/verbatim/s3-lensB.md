## 所見

### 所見 1 — P1 の「深さ 1 が最大安全要求」は未立証

- 所見: 親は起動時の非再帰初期化だけを production 契約として扱っているが、受入前には再帰状態が必須である。P1 は時間順序を固定していない。
- 根拠 (file:line): `tools/codex_reasoning_ab.py:715-762` は source で初期化済みの階層だけを snapshot へ伝播する。`tools/dev_wave_wait.py:1835-1850` は `git submodule status --recursive` の `-` / `U` を受入前に拒否する。`docs/pegasus-runbook.md:858-861` も再帰初期化を要求する。実 repo の `.gitmodules:1-4`、`external/ccbench/.gitmodules:1-3`、`external/ccbench/third_party/shirakami/.gitmodules:1-3` は深さ 3 の構造を示す。
- 成立条件: snapshot を起動時の非再帰 worktree から作成し、後から source だけを再帰初期化する運用。
- 成果物への影響: 深さ 1 の gate は、`external/ccbench` だけ初期化済みで、`shirakami` や `googletest` が未初期化の snapshot を受理する。`supervise_pair` は `tools/codex_reasoning_ab.py:2475-2483` で snapshot 自体を検証するだけなので、source の後続初期化は既存 snapshot を直さない。
- 提案: production snapshot の条件を「manifest の全行が initialized」と明記する。固定値なら、現在の実 repo では深さ 3。深さ 1 を残すなら、nested 内容は意図的に不要であるという別の裁定と build 証拠が必要。
- 確信度: high

### 所見 2 — 提案の正例が under-rejection を固定する

- 所見: plan は top-level initialized、nested uninitialized を正例として受理するが、実 repo の実際の階層と同型である。
- 根拠 (file:line): `plan.md:118-120`。manifest の再帰条件は `tools/codex_reasoning_ab.py:1010-1034`。実 repo では現在、3 行すべてが initialized である。
- 成立条件: `external/ccbench` は存在するが、その配下の gitlink worktree だけが欠落した snapshot。
- 成果物への影響: snapshot は「CCBench の tracked tree が完全に存在する」とは言えないのに verifier を通る。nested dependency を使う build/test では、実験実行時に別内容へ変わるか、後段で失敗する。
- 提案: nested を任意とするなら対象 path を明示して build 依存性を検証する。任意でないなら、正例を「深さ 2 未初期化は reject」に変更する。
- 確信度: medium

### 所見 3 — production の `enforce_closure=True` 経路を新規負例が検査していない

- 所見: 新規負例は `git_object_closure=False` だけで、既定 caller の実経路を直接固定していない。
- 根拠 (file:line): `plan.md:80-116` は負例を `enforce_closure=False` で検証する。既定経路は `tools/codex_reasoning_ab.py:1682-1692` の `enforce_closure=True` 側。
- 成立条件: gate を `if not enforce_closure:` 側へ移す、または false 側だけで実行する変異。
- 成果物への影響: 提案テストは通るのに、既定 spec の `verify_snapshot` は未初期化 top-level を受理する。これは親が防ごうとしている穴そのもの。
- 提案: 同じ合成 snapshot について `enforce_closure=True` と `False` を両方負例にする。少なくとも true 側で新 reason を確認する。
- 確信度: high

### 所見 4 — delimiter 判定と全 top-level 列挙の変異帰属が成立していない

- 所見: plan 自身が delimiter 付き prefix を要求しているが、その退行を新規テストが検出しない。
- 根拠 (file:line): `plan.md:26-40`、`plan.md:134-136`。現行の既存正例は `deps/child` と `deps/child/third_party/grandchild` という真の親子だけである。
- 成立条件: `parent + "/"` を `parent` に変える変異、または manifest の先頭行だけ検査する変異。
- 成果物への影響: `deps/a` と `deps/ab` のような兄弟を誤って親子扱いし、未初期化 top-level を depth 2 として受理できる。二つの top-level のうち後者だけ未初期化という変異も、現行の正負テストでは落ちない。
- 提案: `deps/a` / `deps/ab` の兄弟 fixture と、initialized / uninitialized の二つの top-level fixture を追加する。
- 確信度: high

### 所見 5 — 成長負債と実装面の scope は現状では問題なし

- 所見: 提案テストは `_synthetic_nested_submodule_snapshot` と合成 repo を使い、実 repo fixture を要求していない。
- 根拠 (file:line): `plan.md:45-48`、`plan.md:89-100`。実 repo fixture は `orchestrator/tests/test_codex_reasoning_ab.py:350-380` で構築され、consumer は `orchestrator/tests/growth_test_holds.py:99-115`、serial 閉包は `orchestrator/tests/test_real_repo_serialization.py:38-111` に登録済み。
- 成立条件: 新規テストが `benchmark_snapshots` を引数に追加しないこと。
- 成果物への影響: 現案のままなら新規検出力は恒久保留へ消えない。plan の実装編集面も brief の 2 file と一致する。
- 提案: `benchmark_snapshots` を新規テストへ流用しない。P1 を再裁定して運用文書を直す場合は、2 file scope 外の変更として別 owner を立てる。
- 確信度: high

## 親の実測主張の検証

### 支持

- 深さの構造自体は支持する。root の直接 submodule は `external/ccbench`、子は `third_party/shirakami`、孫は `third_party/googletest` である。
- `_init_submodules_from_local_source` は source の初期化状態を実際に伝播する。source の未初期化行は `initialized` 配列へ入らず、snapshot 側で update されない。
- 現在の `git submodule status --recursive` は 3 行とも `-` なしで、現在の worktree は深さ 3 まで initialized である。

### 反証

- 「非再帰手順で作った worktree が production 上の正当状態」という一般化は反証される。受入前の `preflight-submodule-ready` は再帰 status を見て未初期化を拒否する。
- 2026-08-15 の記録も、非再帰初期化で nested submodule が残り、受入が rc=2 で停止したため `--init --recursive` へ是正すると記録している (`docs/archive/worklog-phase3-0815-558.md:460-464`)。
- 従って、全深度要求が「正当な production snapshot」を壊すという P1 の根拠は不足している。少なくとも現在の受入契約なら、全 manifest 行、現 repo では深さ 3 が自然である。

### 判定不能

- 現在の status から、親が実行した `--init --recursive` が本当に新規 clone だったか、既存 admin dir の再利用だったかは判定できない。
- snapshot 作成が source の再帰 preflight より前か後かは、`_build_snapshot_base` 自体には束縛されていない。この時間順序を確定しない限り、P1 の深さは一意に決まらない。

## 壊れる既存契約

- `test_parent_numstat_controls_remain_pinned`、`test_m1_snapshot_head_pin_is_independent`、`test_pos_neg_submodule_initialization_state_mismatch_is_rejected` は `benchmark_snapshots` を通じて実 repo を読む。top-level が未初期化の worktree で fixture を作ると、`verify_snapshot` が fixture 構築中に新 reason を出し、各テスト本来の assertion へ到達せず error になる (`test_codex_reasoning_ab.py:350-380`, `:862-870`, `:1225-1231`, `:2132-2143`)。
- `test_uninitialized_nested_submodule_is_manifested_and_accepted` は closure 層で nested 未初期化を正直に記録する契約である (`test_codex_reasoning_ab.py:2004-2028`)。gate を verifier の外へ出したり `_submodule_inventory` を変更したりすると、この node の `reasons == []` と manifest 行が壊れる。
- `test_uninitialized_nested_submodule_gitlink_pin_rejects_change` は未初期化 nested 行を manifest SHA の対象としている (`test_codex_reasoning_ab.py:2086-2109`)。manifest 行を削除して gate を通す実装は、この既存契約を壊す。
- `test_verify_replays_complete_fake_codex_experiment` など replay 系は oracle bytes を再計算する。新 policy key を oracle dict へ入れる変異は `tools/codex_reasoning_ab.py:1703-1723` と replay 照合 `:4885-4889` を壊す。
- `test_m1_snapshot_head_pin_is_independent` の `spec` は `_snapshot_spec("POS")` のコピーであり、key 欠落時の fallback 契約は検査しない (`test_codex_reasoning_ab.py:1225-1231`)。この穴は新規負例で補う必要がある。

## 総括

- P1 の深さ 1 は、非再帰起動と再帰受入を混同しており、production の普遍条件としては未立証。
- 現 repo の実構造は深さ 3で、深さ 1 の正例は未初期化 nested snapshot の受理を固定する。
- 新規負例が false closure だけなので、既定 production 経路を迂回する変異が生き残る。
- delimiter と複数 top-level のテストも不足している。
- pytest は実行せず、静的検査のみである。