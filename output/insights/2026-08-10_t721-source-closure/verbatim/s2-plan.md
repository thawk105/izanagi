結論として、P1 の歴史的命名は据え置きを推します。実装は「定数 1 箇所＋説明 1 ファイル＋テスト 3 ファイル」で完結し、停止点・検証ロジック・6 対象 module 自体は変更しません。

なお、HEAD `b0b84837` で静的確認しただけで、ファイル変更・pytest 実行は行っていません。

## 1. 編集対象の完全一覧

### 実装コード

| file:line | 変更 |
|---|---|
| [campaign_lock.py:27-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:27) | `CONTRACT_LOADER_RELATIVE_PATHS` の既存 2 path の後ろへ、brief 順に `execution_guard.py`、`loop.py`、`pipeline.py`、`wal.py`、`ident.py`、`artifact_admission.py` を追加する。直前に「識別子は歴史的名称で、値は enforcement source closure 8 path」とコメントする。 |
| [contract_loader_binding.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:2) | module docstring の「loader 2 module」を「歴史的 API 名を保持した enforcement source closure 8 module」へ直す。 |
| [contract_loader_binding.py:48-50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:48) | `ContractLoaderBinding` の説明を exact 2 loader から exact 8 enforcement source blob へ更新する。 |
| [contract_loader_binding.py:320-337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:320) | capture/live 検証の docstring だけを新しい閉包名へ合わせる。ループ、Git 解決、disk/blob 比較は変更しない。 |

ロジック変更が定数だけで足りる根拠は、codec が同定数を exact key 集合として使う [campaign_lock.py:153-172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:153)、capture/live/committed の全ループが同定数を走査する [contract_loader_binding.py:320-373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:320) ためです。

次は編集しません。

- [ident.py:246-273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:246)、[ident.py:365-369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:365)：既に binding 全体を capture/live 検証している。
- [ident.py:432-498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:432)：停止点はこの `ensure_campaign_identity` 1 点のまま。
- [artifact_admission.py:549-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:549)：既に authority 全体から binding を作り committed 検証している。
- `execution_guard.py`、`loop.py`、`pipeline.py`、`wal.py`、`ident.py`、`artifact_admission.py`：束縛対象にはするが、P1 据え置きなら本 wave では内容を変えない。
- `campaign_lock.py` と `contract_loader_binding.py` 自身は閉包に入れない。

### テスト

| file:line | 変更 |
|---|---|
| [test_t671_source_binding.py:14-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:14) | test-side golden を `_EXPECTED_ENFORCEMENT_SOURCE_PATHS` 等へ改名し、裁定順の exact 8 tuple にする。`campaign_lock` と `contract_loader_binding` の同一定数 object 参照も検査する。 |
| [test_t671_source_binding.py:50-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:50) | 一時 Git repo に 8 path 全てを作成・commit する helper に拡張する。HEAD hash の直書きはしない。 |
| [test_t671_source_binding.py:109-147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:109) | live drift test を 8 path parameterize する。各 path の disk bytes を 1 本ずつ変え、`IdentityMismatch(reason="contract-loader-drift")` と lock/WAL 無書込みを検査する。 |
| [test_t671_source_binding.py:150-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:150) | recorded-commit blob mismatch testも 8 path parameterize する。各 path の digest 改変が admission で `contract-loader-blob-mismatch` になることを検査する。 |
| [test_campaign_lock_codec.py:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:5) | `hashlib` を追加する。 |
| [test_campaign_lock_codec.py:33-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:33) | `str(index) * 64` を `sha256(path bytes).hexdigest()` 等へ変える。閉包サイズに依存せず常に 64 lowercase hex を作る。 |
| [test_campaign_lock_codec.py:153-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:153) | 各 blob key を 1 本ずつ削った v2 authority が codec で拒否される parameterized test を追加する。 |
| [test_artifact_admission.py:1132-1154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:1132) | `[-1]` を明示的な対象 path に置換する。新しい末尾である `artifact_admission.py` を選ぶなら、その文字列が closure に含まれることも assert し、順序変更でテスト対象が沈黙して変わらないようにする。 |

[campaign_lock_test_support.py:8-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:8) と [test_layer3_report.py:53-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53) は binding を動的 capture するため、P1 据え置きでは編集不要です。

### 親が段 7 で作る文書

- `docs/spool/decisions/2026-08-10-dev-wave-t721-source-closure-1.md:1`：新 D。D259 決定 2 の exact 2 path、同「名乗ってよい範囲」、[decisions.md:11969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/docs/decisions.md:11969) の caller closure 延期だけを supersede する。他の D259 決定は維持する。
- `docs/spool/worklog/2026-08-10-dev-wave-t721-source-closure-1.md:1`：[T-721] 完了と新 D を記録する。canonical `docs/decisions.md` / `docs/worklog.md` は wave から直接編集しない。

新 D の名乗りは次のように時点を限定すべきです。

> certified lock の確立または再開で `ensure_campaign_identity` が成功した時点で、enforcement closure 8 module の disk bytes は、lock に記録した commit の blob と一致する。

「任意の artifact admission 時点でも現在 disk と一致する」とは書けません。admission は [artifact_admission.py:549-564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:549) のとおり committed blob/digest だけを検査し、live disk を読みません。

## 2. 閉包拡張で壊れる既存テスト

単純に定数へ 6 path だけ追加した場合、赤になる test function は次の 3 本です。

1. [test_loader_drift_rejected_before_campaign_lock_or_wal_bytes:109-147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:109)

   [line 116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:116) の「production 定数 == 2-path `_LOADER_PATHS`」で失敗します。

2. [test_admission_rejects_contract_loader_blob_mismatch_at_recorded_commit:150-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:150)

   [line 156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:156) で同様に失敗します。assert を消すだけでは、line 191 の 2-key map が codec の exact 8-key 検査で落ち、意図した blob-mismatch 検査になりません。

3. [test_v2_exact_shape_and_canonical_encoding:95-106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:95)

   `_authority()` の [lines 40-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:40) は index 4 から開始します。8 path では最後の 2 path が index 10/11 になり、`"10" * 64` / `"11" * 64` は 128 文字です。そのため有効 v2 fixture 自体が codec で拒否されます。

赤にはならないものの、同じ不正 fixture により誤った理由で緑になる箇所もあります。

- [test_v2_rejects_invalid_hash_and_commit_shapes:173-187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:173)：指定した authority hash/commit ではなく、先に検証される不正 blob digest で落ちる。
- [test_v2_requires_canonical_inner_and_outer_text:231-238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:231)：`pretty_outer` と trailing-newline の 2 case が、outer canonical 検査前の不正 blob digest で落ちる。

index census は次のとおりです。

- 意味が変わるのは [test_artifact_admission.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:1137) の `[-1]` だけです。旧 `env_contract_activation.py` から新 `artifact_admission.py` へ対象が移ります。テストは緑のままなので明示 path 化が必要です。
- `[0]` は [test_t671_source_binding.py:122,176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:122)、[test_campaign_lock_codec.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:193)、[test_artifact_admission.py:981,1159,1181,1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:981) にありますが、P2 の append 順なら引き続き `env_contract.py` で意味は変わりません。
- closure 定数に対する `len(...)` 仮定はありません。
- exact 2 path の closure golden は [test_t671_source_binding.py:20-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:20) だけです。

## 3. 足すべき検査と検出する改変

1. exact closure sentinel

   期待する 8 tuple を test 側で独立に列挙し、production 定数との exact equality、binding module が同一 object を参照することを検査します。6 path のうち 1 本の脱落、余分な path、順序違い、検証器自身の混入、第二定数への分岐を落とします。

   [test_artifact_admission.py:1217-1224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:1217) は二つの module が同じ定数を参照することしか検査せず、両方から同じ 1 path が抜ける改変には緑です。したがって重複ではありません。

2. 8-path live drift parameterization

   各 path を 1 本ずつ改変して `ensure_campaign_identity` が拒否し、lock/WAL bytes が増えないことを検査します。定数からの脱落だけでなく、capture/live loop の条件分岐、特定 path の skip、停止点を `wal.acquire_lock_atomic` より後ろへ動かす改変を検出します。既存 test は旧先頭 path 1 本だけなので、追加 7 case は重複ではありません。

3. 8-path committed mismatch parameterization

   記録 commit の各 blob digest を 1 本ずつ壊し、artifact admission が拒否することを検査します。`verify_committed_contract_loader_binding` の path skip、admission から同 verifier を外す改変を検出します。旧 1 path case 以外は重複しません。

4. 各 blob key 欠落の codec test

   authority map から各 key を 1 本ずつ除去します。exact equality を subset/superset 判定へ弱める改変を検出します。既存 [extra-key test:153-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:153) は余分な key だけなので重複しません。

5. recorded commit ≠ current HEAD の正例

   一時 repo で C1 binding を作り、HEAD を C2 へ進めた後、disk bytes だけを C1 blob に戻します。C1 binding の live 検証が通ることを固定します。`binding.contract_loader_commit` を無視して `_head_commit()` と比較する改変を検出します。

次は既存検出力と重複するため追加不要です。

- valid v2 roundtrip：`test_v2_exact_shape_and_canonical_encoding` が担当。
- v1 anti-downgrade / guided exemption：[test_artifact_admission.py:1002-1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:1002) が担当。
- 既存 v1 corpus の classification 不変：[test_artifact_admission.py:720-730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:720) が exact mapping を固定。
- qualification 集合との一致検査：選択肢 (c) は不採用。独立集合 [qualification/contract.py:38-76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/qualification/contract.py:38) は触らない。

## 4. 受理集合の変化

HEAD `b0b84837` で `output/**/campaign.lock` を JSON として独立走査した結果は、32 本、v1 32 本、v2 0 本、malformed 0 本でした。したがって「現在 repo にある成果物の admission status は変わらない」という親 brief の主張は正しいです。

ただし、全ての仮想 artifact bytes に対する受理集合が「縮むだけ」という表現は正しくありません。

| 入力 | 拡張前 | 拡張後 |
|---|---|---|
| exact 2-key v2 authority map | codec 受理 | 6 key 欠落で拒否 |
| exact 8-key v2 authority map | extra key として拒否 | 他条件も正しければ受理 |
| v1 lock | 従来規則 | 不変 |
| 旧 2 path は clean、追加 6 path のどれかが disk drift |新規作成/resume を受理し得る | `ident` で拒否 |
| 記録 commit C1 と current HEAD C2 は異なるが、disk bytes は C1 blob と一致 | 受理 | 引き続き受理 |
| admission 時に current disk だけが drift | committed 検証は disk を読まない | 同じく disk を読まない |

したがって、

- runtime working-tree 条件は意図どおり縮みます。
- wire codec の集合は exact-2 から exact-8 への置換であり、数学的には部分集合ではありません。
- exact-8 の新規受理は本裁定を実装するために必須の形式変更で、別の受理拡大提案ではありません。
- 既存 repo artifact 32 本については v2 が 0 本なので、実際の受理結果は不変です。
- land 前に v2 lock 数を再 census し、1 本でも発生していたら互換性評価をやり直すべきです。

## 5. P1 命名据え置きの評価

### 据え置き時の面

上記のとおり、production は `campaign_lock.py:27-30` と `contract_loader_binding.py` の説明だけです。`ident.py` と `artifact_admission.py` を変更しないため、追加直後も enforcement 6 path は HEAD blob と一致し、動的 v2 fixture を通常どおり検査できます。

### 改名時の面

改名するなら、例として次を exact replacement とします。

- `CONTRACT_LOADER_RELATIVE_PATHS` → `ENFORCEMENT_SOURCE_RELATIVE_PATHS`
- `contract_loader_commit` → `enforcement_source_commit`
- `contract_loader_blob_sha256s` → `enforcement_source_blob_sha256s`

旧/new key の併存や alias 受理は、裁定外の受理集合拡大になるため行いません。波及する全 consumer は次の 9 ファイルです。

- [campaign_lock.py:19-24,40-59,153-188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:19)
- [contract_loader_binding.py:15,47-82,320-384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:15)
- [ident.py:246-273,365-369,465-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/ident.py:246)
- [artifact_admission.py:549-560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:549)
- [campaign_lock_test_support.py:8-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:8)
- [test_campaign_lock_codec.py:33-45,145-195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:33)
- [test_artifact_admission.py:239-263,973-985,1122-1224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:239)
- [test_layer3_report.py:53-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53)
- [test_t671_source_binding.py:14-23,109-213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:14)

`git grep` では歴史的証拠 `output/insights/2026-08-09_t671-impl/mutation-ledger.json` と `mutation-spec.json` にも旧名がありますが、過去の変異記録なので書き換えません。親 brief 自体の lines 71-73 も入力記録であり編集対象外です。

### 推奨

P1 据え置きを推します。

v2 lock が 0 本なので「成果物 migration cost」はゼロですが、改名の実装コストはゼロではありません。特に改名すると、新しく閉包に入る `ident.py` と `artifact_admission.py` 自身を同時に編集するため、commit 前は live source gate がその未コミット差分を正しく拒否します。また `artifact_admission.py` の bytes 変更は [line 598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:598) の `validator_sha256` も変え、T-720 との衝突面も広げます。

歴史的名称という負債は残りますが、定数直前の明記、module/class docstring、新 D、exact 8-path sentinel で封じる方が、この wave の「機構を変えず path だけ追加する」という境界に忠実です。

## 6. 順序と依存

1. land 直前に v2 lock 0 本と、8 対象 source の HEAD/disk 一致を再確認する。
2. T-720 が先に land した場合は main を取り込み、`campaign_lock.py` の競合を解消する。
3. test-side exact 8 tuple、live/committed parameterization、codec missing-key testを先に置く。
4. production 定数へ 6 path を裁定順で追加し、歴史的名称の説明を更新する。
5. codec fixture の digest generator と `[-1]` の意味ドリフトを修正する。
6. 実装時のテストは direct pytest ではなく `tools/run_tests.py` 経由で、変更 3 test file、動的 v2 fixture consumer 群、関連 campaign tests を実行する。
7. 親が decisions/worklog fragment を追加し、docs・Codex agent checker・commit 後 provenance を実施する。

P1 据え置きなら単一 Codex 実装子・単一実装単位で十分です。production 定数と test golden が強く結合しており、並列分割の利益はありません。改名を選ぶ場合も子を分けず、wire consumer 改名を先に commit 可能な状態へ揃えてから閉包を拡張する順次作業が必要です。

## 総括

- 本体は `CONTRACT_LOADER_RELATIVE_PATHS` への exact 6 path 追加で、停止点・比較意味論は不変。
- naive な追加で赤になる既存 test は 3 本、加えて codec の 2 test が誤理由で緑になる。
- exact 8-path sentinel と live/committed の各-path parameterization で、1 path 脱落を構造・挙動の両面から落とす。
- 既存 `output/**` は 32 本全て v1 なので、現存成果物の受理は変わらない。
- 一般の wire 受理集合は exact-2 から exact-8 への置換であり、「縮むだけ」ではない。
- P1 は据え置きを推奨し、歴史的名称であることをコード説明と新 D に固定する。
- 最大のリスクは、名乗りを admission 時の live-disk 保証や in-process／artifact 改竄耐性まで広げてしまうこと。
