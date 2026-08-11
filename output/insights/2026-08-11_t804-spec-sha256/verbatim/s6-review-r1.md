## 総括

**NO-GO。**

manifest 層の 6 投影比較、driver の注入再束縛、required keyword、D288 の generic builder 受理は静的には成立しています。一方、judge の「再検証」は hash 2 本だけで、observations 本体を verified manifest の schedule へ束縛していません。正しい公開 hash をコピーした自己整合 observations から determinate verdict を作れるため、正しさ防壁が恒真化しています。

親の「赤 3 件は production を変えず、承認 spec fixture を用意する」暫定裁定自体は妥当です。ただし、それだけでは下記 BLOCKER は閉じません。

## 所見 1: judge は manifest を再検証しても observations 本体を再束縛していない

- 分類: **BLOCKER**
- 根拠:
  - [s8b_oracle_judge.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:147) は `"manifest_sha = observations.get(\"manifest_sha256\")"`、[同:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:157) は `"spec_sha = observations.get(\"spec_sha256\")"` とし、CLI が渡す実値との一致しか見ません。
  - manifest 由来であるべき試行数とセル集合は、[同:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:166) の `"n = observations.get(\"n_per_cell\")"`、[同:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:180) の `"raw_expected = observations.get(\"expected_cells\")"` という自己申告値です。
  - [同:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:238) の比較は `"actual_cells != expected_counter"`、すなわち observations 内の rows と observations 内の expected_cells の自己整合検査に留まります。
  - CLI は [同:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:324) で manifest を実検証していますが、core へ渡すのは [同:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:334) の `"verified_manifest_sha256=verified.sha256"` と [同:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:335) の `"approved_spec_sha256=approved.sha256"` だけです。
  - observations loader も [s8b_oracle_artifacts.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_artifacts.py:149)–153 の schema 名確認だけで、report 発行物の封印ではありません。
- 成果物影響:
  - 迂回者は valid manifest/spec の公開 hash をコピーし、別 spec 相当の `n_per_cell`・`expected_cells` と、それに自己整合する任意の rows/bench 値を与えられます。judge は [s8b_oracle_judge.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:281)–288 で `status="determinate"` の `OfficialVerdict` を生成可能です。
  - combined 層はその medians を [s8b_verdict.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_verdict.py:347)–362 で利用し、[同:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_verdict.py:671)–725 で certified 結論を組み立てます。したがって winner、floor 超過判定、最終 certified 選択を改変できます。
- 対処案:
  - `judge_oracle` に hash 文字列だけでなく `VerifiedManifest`、またはそこから一度だけ導出した immutable な `n`・expected-cells projection を required keyword で渡す。
  - `n_per_cell` と `expected_cells` を verified manifest の schedule から再導出して完全一致させる。
  - 同じ正しい hash を保持したまま `n_per_cell` と `expected_cells`・rows を一緒に別 schedule へ変える metamorphic 負例を追加する。現在の spec hash 1 field だけの負例ではこの迂回を検出できません。
  - report→judge 間の rows 自体の改竄まで防御すると主張するなら、別途 `VerifiedObservations` 等の封印・検証境界が必要です。

## 所見 2: observations schema の CLI 負例が manifest 側で先に落ちる恒真テストになった

- 分類: **MAJOR**
- 根拠:
  - [test_s8b_oracle_judge.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:379) のテスト名は `test_judge_cli_rejects_non_observations_schema_without_output` ですが、[同:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_judge.py:384)–386 で同じ invalid `source` を `--input` と `--manifest` の両方へ渡しています。
  - production は [s8b_oracle_judge.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:315) の `"load_official_manifest(args.manifest)"` を、observations load の [同:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:331) より先に実行します。したがって全 parameter が manifest 側だけで rc=2 になり、observations loader を削除してもテストは緑です。
- 成果物影響:
  - このテストの機械受理集合には「judge CLI が observations schema を検査しない実装」が含まれます。その退行では、本来 rc=2・出力なしの入力から oracle verdict artifact が生成され得ます。
- 対処案:
  - 実 verifier を通る valid manifest・freeze・approved spec fixture を `--manifest` に与え、`--input` だけを別 schema にする。
  - positive control として同一 manifest/spec で valid observations が rc=0・出力生成になることも固定する。

## 確認できた非所見

- `verify_manifest` の投影比較は恒真ではありません。schedule は approved spec から再生成され、campaign/run-contract/binding/reasons/generators は被検証 document と独立な approved snapshot と比較されています。
- 正規化による正当 manifest の過剰拒否は確認できません。binding validator は入力順を保存し、generator の key 整列と dict key 順は Python の deep equality に影響しません。JSON 生値の list/dict 型にも戻されています。
- `_validate_run_contract` は [s8b_oracle_manifest.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_manifest.py:396)–427 の部分集合検査・全 key 保存のままです。余剰 key は builder で保存されるため D288 は維持されています。
- `gate_check` の注入経路は exact type、manifest canonical hash、approved spec hash の 3 点を再束縛しています。
- `judge_oracle` の 2 keyword は [s8b_oracle_judge.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_judge.py:127)–130 のとおり default なしです。`verify_manifest.approved_spec` にも default はありません。
- 新規 skip・xfail・期待値反転は差分上確認していません。

## 親の暫定裁定

赤 3 件について production を緩めず、テストへ approved spec fixture を追加する方針は正しいです。`APPROVED_SPEC_SHA256 = None` は [s8b_oracle_spec.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/campaign/s8b_oracle_spec.py:21)–23 で意図的な fail-closed 状態であり、承認前に downstream の構造診断や rc=3 より `no-approved-spec` が先行するのは本番の認可順として妥当です。

ただし fixture は各テストの検査対象と整合させる必要があります。特に contract SHA mismatch テストは、変更後 contract を含む spec を承認代役にしなければ、spec 比較で先に拒否されます。

pytest は実走していません。実測値は依頼に記載された親の結果のみを前提にしました。