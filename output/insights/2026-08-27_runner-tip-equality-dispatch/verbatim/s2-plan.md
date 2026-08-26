## 1. 削除する述語

行番号は変更前の現行 file に対するもの。

1. `tools/acceptance_launcher.py:438-439`

   削除対象は次の byte 等値述語だけ。

   ```python
   if source != tip_source:
       raise LauncherFailure("tested-main and tested-tip runner blobs differ")
   ```

   `tools/acceptance_launcher.py:437` の tip 読み取りは残し、未使用変数を避けるなら次の bare call にする。

   ```python
   blob_reader(config.repo_root, config.tested_tip)
   ```

   削除後の `_launch` は「tested main の runner を読む → tested tip の runner が blob として読めることだけ確認する → main bytes を実行する → main blob を独立再読して M3 照合する」と読める。

2. `tools/dev_wave_land.py:1084`

   `tools/dev_wave_land.py:1074-1087` の or 連鎖から、次の一項だけを削除する。

   ```python
   or main_runner_entry[1] != tip_runner_entry[1]
   ```

   削除後の `_verify_acceptance_receipt` は「main と tip の runner entry が双方存在し、双方 blob で、object ID が妥当であることを確認したうえで、receipt の実行 digest を main runner blob の内容だけと照合する」と読める。

3 か所目の確認方法は次のとおり。

- 対象: repo の active production source 全体、特に `tools/dev_wave_wait.py`、`tools/dev_waves/**/*.py`、`hooks/**/*`、および二つの対象 tool。
- 検索語: `source != tip_source`、`tested-main and tested-tip runner blobs differ`、`main_runner_entry`、`tip_runner_entry`、`runner_executed_sha256`、`tools/run_tests.py` と `tested_main` / `tested_tip` / `==` / `!=` / `differ` / `match` の組合せ。
- active production source で runner の main/tip byte または blob ID を比較する結果は上記二つだけだった。
- `tools/dev_wave_wait.py:3028-3052` は launcher outcome の型と SHA-256 形式を検査するだけで、main/tip runner の比較はない。`tools/dev_waves/` と hooks にも該当比較はない。
- repo 全体検索では `output/insights/` の過去 mutation spec や docs、tests に同じ文字列が出るが、現行の実行述語ではない。
- `tools/dev_wave_land.py:1124` の `main_checker_blob != checker_blob` は `tools/check_acceptance_reds.py` の別の等値境界であり、runner の 3 か所目ではない。

## 2. 残す述語

### Launcher 側

- `tools/acceptance_launcher.py:436`: 実行用 `source` を `config.tested_main` から取得する。
- `tools/acceptance_launcher.py:437`: tested tip の runner blob を読み、`_read_runner_blob` の失敗を伝播させる。byte 値は実行に使わない。
- `tools/acceptance_launcher.py:194-196`: `git cat-file blob` が失敗した main または tip を fail-closed にする。
- `tools/acceptance_launcher.py:440-441`: main 由来の `source` の SHA-256 を記録し、同じ `source` を `blob_runner` へ渡す。
- `tools/acceptance_launcher.py:443-449`: 実行後に `tested_main` を独立再読し、`runner_executed_sha256 != sha256(refreshed tested-main bytes)` なら拒否する M3 述語を維持する。

したがって、tip bytes を実行する置換と、実行後に観測した main bytes からずれた bytes を実行する置換は引き続き失敗する。

### Land 側

- `tools/dev_wave_land.py:950-953`: `runner_executed_sha256` が SHA-256 形式であること。
- `tools/dev_wave_land.py:1065-1068`: tested tip と tested main の runner entry を双方取得し、どちらかが欠落すれば拒否すること。
- `tools/dev_wave_land.py:1080-1083`: main と tip の双方が `blob` で、双方の object ID が妥当な SHA 形式であること。
- `tools/dev_wave_land.py:1085-1086`: `receipt["runner_executed_sha256"]` が `content_sha256(tested_main の runner blob)` と一致すること。

最後の述語が land 側の main 束縛を直接殺している。tip digest を記録した receipt、main runner 欠落、非 blob、main 内容と異なる digest は変更後も拒否される。

## 3. テストの改訂計画

### 現行テストの 3 分類

(a) 等値述語だけを削除すると落ちるもの:

- `test_main_tip_runner_blob_mismatch_is_rejected_before_execution`
- `test_land_rejects_child_green_runner_blob_divergence`

前者は execution callback が呼ばれる新挙動に反し、後者は既に main digest を持つため変更後は正当に land される。

(b) 緑のままだが、main/tip の byte 選択を十分に区別できないもの:

- `test_matching_main_and_tip_runner_blobs_execute_tested_main_source`
- `test_land_accepts_child_green_matching_main_and_tip_runner_blobs`

launcher test の object identity 検査自体は非自明だが、実行内容としては main と tip が同じである。land test は main と tip の runner blob が同一なので、main digest と tip digest のどちらを照合しても同じ結果になり、main 束縛の部分が恒真になる。

(c) 等値削除後も現在の期待どおり通るもの:

- Launcher: `test_missing_tested_main_runner_is_rejected_before_execution`、`test_missing_tested_tip_runner_is_rejected_before_execution`、`test_m3_runner_digest_mismatch_is_rejected`、`test_nonexact_runner_argv_is_rejected`、`test_shard_activation_does_not_expand_exact_outer_runner_argv`、`test_blob_bootstrap_uses_canonical_file_without_pathname_reload`、`test_receipt_is_exact_canonical_json_bytes`、`test_trusted_mode_authority_kind`、`test_unknown_effective_scheduler_is_rejected`、`test_bootstrap_mode_authority_kind`、`test_negative_child_rc_is_normalized`。
- Land の runner 周辺: `test_m4_runner_executed_digest_mismatch_is_rejected`、`test_land_rejects_non_attributable_runner_blob_divergence`、`test_land_runner_divergence_precedes_checker_lookup_process_failure`、二つの runner path absence test、二つの runner lookup failure test、`test_land_runner_gate_uses_tested_main_after_main_reaches_tip`、`test_land_rejects_non_blob_runner_objects_even_when_trees_match`。
- `orchestrator/tests/test_dev_wave_wait.py::test_child_green_receipt_does_not_require_main_tip_runner_equality` も schema-level の確認なのでそのまま通り、編集しない。
- その他のテストは削除対象比較を判定理由として参照しておらず、静的には変更不要。

### `test_acceptance_launcher.py`

- `orchestrator/tests/test_acceptance_launcher.py:87-130` を `test_different_main_and_tip_runner_blobs_execute_tested_main_source` 相当に改名する。
- `main_source`、`tip_source`、`refreshed_main_source` をそれぞれ別 object にするだけでなく、tip の bytes を main と明確に異ならせる。
- `executed_sources[0] == main_source`、`executed_sources[0] != tip_source`、読取順が `[tested_main, tested_tip, tested_main]`、receipt の runner digest が main bytes の SHA-256 であることを確認する。
- `orchestrator/tests/test_acceptance_launcher.py:133-159` の旧 mismatch 拒否 test は削除する。その反転後の正例は上の divergent positive test が担う。
- `test_m3_runner_digest_mismatch_is_rejected` の second run も main、異なる tip、drift した再読 main の三つを使い、tip が異なっていても M3 が main 再読差分を拒否することを固定する。

### `test_dev_wave_land.py`

- `_Repo._acceptance_receipt` の `orchestrator/tests/test_dev_wave_land.py:354-357` は、`runner_digest_revision` 未指定時の既定を `tested_tip` から `tested_main` に変える。これは実 launcher の producer semantics に fixture を合わせる変更である。
- `runner_digest_revision` 引数自体は残す。tip digest を偽造する negative test だけが `runner_digest_revision=tip` を明示する。
- `_assert_v5_binding_baseline` の `orchestrator/tests/test_dev_wave_land.py:677-692` も runner entry と内容 SHA-256 の基準を `request.tested_main_sha` に変える。waiter の tip 基準は変えない。
- `test_land_rejects_child_green_runner_blob_divergence` は `runner_digest_revision=tip` に変え、`test_land_rejects_child_green_tip_runner_digest_when_blobs_diverge` 相当に改名する。receipt digest が tip と一致し main と異なることを明示し、main 束縛による拒否を確認する。
- `test_land_accepts_child_green_matching_main_and_tip_runner_blobs` は divergent positive test にする。tested tip で runner を変更し、receipt は既定の tested main digestを使い、main/tip の blob と内容 SHA-256 が異なることを先に assert してから land 成功を確認する。
- 同 test の forward-main 要素を残す場合は、locked main にも tip と同じ新 runner bytes を別 commit として置く。これにより tested main だけが旧 bytes、tested tip・locked main・landing tip が新 bytes となり、成功が tested main 照合でしか説明できなくなる。
- `test_land_rejects_non_attributable_runner_blob_divergence` は tip digest の明示を維持し、main digest と異なることを追加 assert して「divergence 自体」ではなく「tip digest を名乗ったこと」による拒否だと明確化する。
- fixture 既定変更後も ordering test を維持するため、`test_land_runner_divergence_precedes_checker_lookup_process_failure` は `runner_digest_revision=tip` を明示し、`test_land_main_runner_digest_mismatch_precedes_checker_lookup_process_failure` 相当に改名する。

pytest は実走せず、以上は静的な改訂計画である。

## 4. 受理集合の差分

- 受理側: 変更前に受理された receipt は変更後も受理され、さらに main と tip の runner blob が異なっていても tip 側が実在する blob で `runner_executed_sha256 == sha256(tested_main runner bytes)` を満たす receipt が新たに受理される。
- 拒否側: tip または main の runner が欠落・非 blob・不正 object ID の receipt、あるいは `runner_executed_sha256` が tested main runner 内容と異なる receipt は引き続き拒否されるため、拒否集合は空にならない。

## 5. `docs/pegasus-runbook.md` の改訂箇所

親が編集するため、以下は文案のみ。

### `docs/pegasus-runbook.md:928-932`

現行文:

> 実行前に `tested_tip:tools/run_tests.py` の bytes も別に読み、**一致しなければ suite を一度も起動せずに** rc=70 で止まる。

置換案:

> 実行前に `tested_tip:tools/run_tests.py` も blob として別に読み、欠落または読取不能なら suite を一度も起動せず rc=70 で止まるが、tested main との byte 等値は要求しない。実行する bytes は常に `tested_main:tools/run_tests.py` から取得し、実行後の独立再読でも tested main の内容 SHA-256 と `runner_executed_sha256` を照合する。

### `docs/pegasus-runbook.md:945-953`

現行文:

> **`tools/run_tests.py` を変更した wave は、どの verdict でも受入を通せない (D838)。** launcher は suite 起動前に、land は verdict によらず共通に、`tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` の object type が `blob` であることと blob SHA の等値を要求する。受領証の `runner_executed_sha256` の照合先も `tested_main` 側の blob である。実行器を触る wave は受入そのものが通らないので、**実行器の変更と他の変更を同じ wave に載せない**こと。  
> この等値は、claim 後・待ち手の内部 merge 前に**別の wave が実行器の変更を main へ land した**場合にも破れる。実行器を触っていない wave が一度拒否され、受入をやり直すことになる。そのときは新しい main を取り込んでから再投入する。

置換案:

> **`tools/run_tests.py` を変更した wave も受入を通せる。** launcher と land は `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` が双方 blob として実在することを要求するが、両 blob の SHA または bytes の等値は要求しない。実行する runner と受領証の `runner_executed_sha256` の照合先は常に `tested_main` 側の blob である。したがって claim 後の内部 merge で tested tip 側の runner が変わっても、その差だけを理由に受入をやり直す必要はない。

## 6. 編集しない境界

- `tools/check_acceptance_reds.py` と、land の checker main/tip 等値 `tools/dev_wave_land.py:1124` は編集しない。
- 待ち手の tip source 束縛、特に `tools/dev_wave_wait.py:3761-3766` の `_verify_waiter_source_bytes` と `waiter_executed_sha256` は編集しない。
- `tools/dev_wave_wait.py`、`tools/dev_waves/`、hooks に runner 等値撤去のための変更を入れない。
- `dev-wave-acceptance-receipt/v5`、`runner_executed_sha256` を含む field 集合、canonical JSON は変更しない。
- `_runner_tree_entry` 自体も変更せず、削るのは caller の SHA 等値一項だけとする。
- scope 外の real 所見として追加実装が必要なものはない。D987 の forward-main receipt 再利用拒否は別機構のまま扱う。

## 総括

launcher の byte 比較二行と land の blob-ID 比較一項だけを削除する。  
tip runner の実在・blob 条件と、main runner の実行・M3・receipt digest 照合は残す。  
test fixture の既定 digest を main に直し、main/tip が異なる正例と tip digest の負例を対にする。  
runbook の二つの旧等値説明を main 束縛のみの契約へ置換する。  
waiter、checker 等値、hooks、receipt schema は編集しない。