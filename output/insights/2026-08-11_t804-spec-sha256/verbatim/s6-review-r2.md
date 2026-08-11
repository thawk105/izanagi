## 総括

**NO-GO。**

静的検査のみ。pytest・build は実走しておらず、コード変更は 0 byte。

主な停止理由は 2 件。

1. judge は approved manifest を再検証するが、observations の内容をその manifest に束縛していない。正しい公開 hash を転記した手書き observations から determinate verdict を生成できる。
2. `PIN_GATE_SPEC_RAW` は現在の judge/report bytes に対して stale であり、親が確認した赤 2 件と一致する。

`verify → driver → official report` の束縛、通常の legacy 経路の非 certified 化、freeze 解決の同型性は確認できた。

## 所見

- **所見 1**: judge は manifest を再検証しても observations 本文を検証済み manifest へ束縛していない
  - 分類: **BLOCKER**
  - 根拠:
    - [s8b_oracle_judge.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:324) は確かに `verify_manifest` を呼ぶが、[同:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:332) で core へ渡すのは逐語で `verified_manifest_sha256=verified.sha256` と `approved_spec_sha256=approved.sha256` の 2 値だけ。
    - [同:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:147)〜165 は observations の公開 hash との等値しか見ない。
    - `n_per_cell` と `expected_cells` は検証済み manifest からではなく、[同:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:166) と [同:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:180) で observations 自身から読む。
    - loader も [s8b_oracle_artifacts.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_artifacts.py:149)〜153 の schema 確認だけ。
    - 実際、[test_s8b_oracle_judge.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:56)〜68 は observations を手書きし、[同:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:85)〜89 で determinate `unique-best` を受理している。
  - 成果物影響: 正しい manifest/spec hash を転記し、承認済み schedule と異なる自己整合的 `expected_cells` / `rows` を書けば、`OfficialVerdict.status`、holdout 集合、`winner_configuration_id`、median を変更できる。report と budget ledger は変更されないが、judge の受理集合と verdict 値が直接変わる。
  - 対処案: judge CLI で observations を WAL/output-root から再構築して入力 bytes と照合するか、共有 `verify_observations` から得た sealed token のみを core に渡す。少なくとも `n_per_cell` / `expected_cells` は `VerifiedManifest.document["schedule"]` から再導出する。正しい公開 hash を持つ手書き observations の負例を追加する。

- **所見 2**: A の reviewed-spec golden は B の最終 bytes に未収束
  - 分類: **BLOCKER**
  - 根拠:
    - [test_s8b_oracle_manifest.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:84)〜91 の埋込み値は judge=`b56fa6...`、report=`4e6ce6...`。
    - 現在の実 bytes は judge=`36f75524dc5c87f33da4f82b605ab675f93fc14c150bf5b9768b64cb78ff15f7`、report=`cc28c86074aead3747eadcaaf1a09a2eaf4bdaae0ca72cca4a9d4f32bfd5acbf`。
    - verifier は [s8b_oracle_manifest.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:467) の「`実 byte hash と不一致`」で拒否する。
  - 成果物影響: 独立 reviewed-spec golden が現 production source を承認できず、approved manifest の正例受理集合が空になる。親の赤 2 件を解消できないため統合不可。
  - 対処案: 所見 1 の judge fixを先に完了し、その最終 bytes で judge/report hash と `PIN_GATE_SPEC_SHA256` を再計算する。現コードだけを更新した暫定 spec hash は `51b86c4abebda922b9423db81f109bab2819ebd893a65cf2be3439d752bd2bf1` だが、judge fix で再度変わるため今は固定しない。
  - 収束性: [s8b_oracle_manifest.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:53)〜60 の source 集合に test file は含まれない。したがって最終 B → A golden 更新の 1 往復で収束し、循環はない。

- **所見 3**: `gate_check` の 3 点再束縛は実装済みだが、テストは spec 軸しか直接固定していない
  - 分類: **MINOR**
  - 根拠:
    - production は [s8b_oracle_driver.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:464) の exact type、[同:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:468)〜474 の実 file/document hash、[同:478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:478) の approved spec hash を全て検査する。
    - しかし追加負例 [test_s8b_oracle_driver.py:1860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_driver.py:1860)〜1895 は spec 不一致だけ。matching な injected token の正例、exact-type 単独負例、実 file/document hash 単独負例はない。
  - 成果物影響: 現コードに実迂回は確認できない。将来 exact-type/hash の一部だけが退行しても、standalone gate の injected-token 受理集合が拡大したままテストが通り得る。`run_block` は token 注入を公開していないため、現 ledger への直接影響はない。
  - 対処案: 同一 fixture で injected token の正例を先に通し、type・file hash・document hash・spec hashを各 1 点だけ変える負例を追加する。

- **所見 4**: consumer pin は「新しい consumer が必ず赤」を保証しない
  - 分類: **nit**
  - 根拠:
    - [test_s8b_oracle_manifest_contract.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest_contract.py:43) と [同:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest_contract.py:78) は consumer を file path の `set` に潰す。同じ既存 file に loader call を追加しても集合は変わらない。
    - direct import alias は [同:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest_contract.py:49)〜76 で捕捉する。一方、re-export、callable への代入、higher-order wrapper、動的 access は捕捉しない。
    - docstring は [同:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest_contract.py:83)〜86 で「`限定 AST inventory`」「`全実行経路の全称保証ではない`」と明記しており、動的経路についての過大主張はない。
  - 成果物影響: 現在の production consumer 取り残しは確認できない。将来、既存 file 内または re-export 経由で loader-only sink が追加された場合だけ、report/verdict の受理集合拡大を検知できない。
  - 対処案: backlog。必要なら file 集合に加えて `(file, function, callsite)` を pin し、re-export を明示拒否または allowlist 化する。

- **所見 5**: manifest 層の正例は負例と同じ fixture instance ではない
  - 分類: **nit**
  - 根拠: 正例は [test_s8b_oracle_manifest.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:1434)〜1471、負例は別 test/別 root の [同:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:1490)〜1569。同じ helper・値は使うが、負例ごとに baseline を先に通してはいない。
  - 成果物影響: exact error regex を [同:1562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_manifest.py:1562) で固定しているため恒真リスクは限定的。現受理集合の誤りは確認していない。
  - 対処案: 各 parameter 内で mutation 前 document を一度 verify し、その object の 1 projection だけを変更する。

- **所見 6**: `config_for_block` 自体は未検証 Mapping を受理できる
  - 分類: **nit**
  - 根拠: [s8b_oracle_manifest.py:1144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:1144)〜1152 は `Mapping` と schedule/campaign shape だけを要求する。ただし唯一の production caller は [s8b_oracle_driver.py:1224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:1224)〜1226 で、`verified_manifest.document` を渡している。
  - 成果物影響: 現 driver・ledger の迂回はない。将来この public helper を直接利用する production caller が追加された場合にだけ、未検証 campaign/run contract の射影が可能になる。
  - 対処案: backlog として `VerifiedManifest` exact type を受ける APIへ狭めるか、raw projection helper を private 名へ分離する。

## 層・legacy・経路確認

- production consumer の再計数:
  - `verify_manifest`: driver / report / judge
  - `load_official_manifest`: report / judge
  - `load_official_observations`: judge
  - `load_official_verdict`: `s8b_verdict` のみ。裁定どおり scope 外
- driver の診断再検査 `_manifest_structural_refusal` は [s8b_oracle_driver.py:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_driver.py:1122)〜1137 の active freeze 解決失敗時に refusal を追加するだけで、manifest 値を実行・台帳へ使わない。
- report と judge の freeze 解決はともに `load_ratified_freeze → reverify_published_freeze → load_approved_spec → verify_manifest` で同型。
- 通常の legacy chain は閉じている:
  - report は legacy に `manifest_kind="legacy"`、`spec_sha256` 不在を出す。
  - judge core は `manifest-kind` と `spec-sha256` で indeterminate。
  - judge CLI は `LegacyManifest` を [s8b_oracle_judge.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:315)〜319 で verdict 作成前に拒否する。
- 層別正例:
  - driver: 同一 test 内で gate allowed＋実行到達と拒否＋無出力を確認。
  - report: 同一 manifest pathで approved A の rc=0 と approved B の rc=2を確認。
  - judge core: 同じ observations object の `spec_sha256` だけを変更。
  - manifest: 所見 5 のとおり同じ値群だが別 fixture instance。
  - injected gate: 所見 3 のとおり同一 fixture の正例なし。

## 裁定パッケージ候補

1. **combined verdict の sealed upstream**
   - **A（推奨）:** 別 wave で `VerifiedOracleVerdict` を導入し、`judge_combined` を sealed token 専用にする。
   - **B:** 現 marker-only API を維持し、「judge までの束縛」に主張を限定し続ける。

2. **legacy artifact の将来**
   - **A（推奨）:** 現在の report 互換を維持し、legacy は永続的に non-certified と明記する。
   - **B:** schema migration として legacy observations を別 schema/typeへ分離し、段階廃止する。

3. **official sink の全称監査**
   - **A:** callsite・re-export・動的 access allowlistを含む横断監査を別 wave で導入する。
   - **B（現裁定維持）:** 限定 AST inventory と敵対レビューを併用し、全称保証は主張しない。