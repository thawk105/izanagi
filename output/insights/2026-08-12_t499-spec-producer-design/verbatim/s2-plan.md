静的検査のみを行いました。指定ファイルはすべて読めています。両 durable directory は不在で、作業ツリーは無変更です。pytest・producer・計測は実行しておらず、緑とは主張しません。

## (1) reviewed spec producer の設計

### 結論

将来の別タスクで、`s8b_oracle_spec.py` とは分離した専用 module、仮称 `orchestrator/campaign/s8b_oracle_spec_producer.py` を設けるのが妥当です。

- AI が active ratified freeze と凍結済み契約から値を導出し、canonical bytes と SHA-256 を生成する。
- rulings セッションが decoded values、exact bytes、SHA-256、導出根拠を一体で提示し、ユーザーが承認する。
- 承認後の別タスクだけが、承認された bytes を再導出し、固定 path へ create-only で配置する。
- 本 wave では `output/s8b-oracle-spec/` に 1 byte も書かず、`APPROVED_SPEC_SHA256` も `None` のままとする。

親の P1 は正しいです。現行 gate は raw bytes の SHA-256 pin だけで、git provenance は検査しません（`orchestrator/campaign/s8b_oracle_spec.py:182-200`）。`_assert_user_commit` は freeze v2 の approval、pointer、revocation、cancellation にだけ適用されています（`orchestrator/campaign/s8b_ratified_freeze.py:537-549,1113,1128,1143,1156`）。

### producer が作る exact document

top-level は次の 8 key だけです（`orchestrator/campaign/s8b_oracle_spec.py:25-34,105-110`）。

- `allowed_excluded_reasons`
- `binding_identity`
- `campaign_ids`
- `generator_versions`
- `run_contract`
- `schedule_parameters`
- `schedule_sha256`
- `schema_version`

生成手順は次のとおりです。

1. `schedule_parameters` を exact 5 key、すなわち `n`、`master_seed`、`block_sizes`、`holdout_ids`、`configuration_ids` で構成する（`orchestrator/campaign/s8b_oracle_spec.py:35-41,112-121`）。
2. `build_schedule` だけを使って schedule を再生成する。`n` と block 合計、非空・重複なしの軸、決定論的 shuffle はここで拘束される（`orchestrator/campaign/s8b_oracle_manifest.py:211-270`）。
3. `schedule_sha256(schedule)` を再計算して記録する。loader も同じ再計算との完全一致を要求する（`orchestrator/campaign/s8b_oracle_spec.py:123-137`）。
4. downstream manifest の単一 block 契約を満たすため、producer は block を正確に 1 件に限定する。`build_schedule` 自体は複数 block を許すが、manifest validator は拒否する（`orchestrator/campaign/s8b_oracle_manifest.py:278-305`）。
5. `campaign_ids` は block ID 集合と一対一にし、値も重複させない（`orchestrator/campaign/s8b_oracle_spec.py:147-158`）。
6. `run_contract` は exact 9 key にする。`verify="legacy+s2"`、`screening="off"`、`bench_max_rounds=1`、`reps=5`、`extime=5` が必要である（`orchestrator/campaign/s8b_oracle_spec.py:139-145`、`orchestrator/campaign/s8b_oracle_manifest.py:396-427`、`orchestrator/campaign/s8b_experiment_numbers.py:14-15`）。
7. `binding_identity` は全 schedule cell に 1 件ずつ置き、7 key の exact schema、cell の非重複、`binding_sha256` の再生成一致を満たす（`orchestrator/campaign/s8b_oracle_manifest.py:487-537`）。
8. `generator_versions` は現在の exact 5 source を、canonical path と実ファイル SHA-256 で記録する。余剰 key も欠落も拒否される（`orchestrator/campaign/s8b_oracle_manifest.py:53-62,430-470`）。
9. `allowed_excluded_reasons` は非空文字列の重複なし list にする（`orchestrator/campaign/s8b_oracle_spec.py:171-177`）。
10. 完成 document に `validate_reviewed_spec` を適用した後、`_manifest._canonical_bytes` で `sort_keys=True`、compact separator、UTF-8、非有限値拒否の bytes にする（`orchestrator/campaign/s8b_oracle_spec.py:98-102`、`orchestrator/campaign/s8b_oracle_manifest.py:139-146`）。
11. その bytes を strict loader に戻し、duplicate key・不正 UTF-8・非有限値を拒否したうえで、再 canonical 化した bytes と byte-for-byte 一致させる（`orchestrator/campaign/s8b_oracle_artifacts.py:80-109`、`orchestrator/campaign/s8b_oracle_spec.py:258-269`）。

producer 自身の builder だけを信頼せず、production loader と同じ最終検査を通すことが必要です。

### producer の所在

| 選択肢 | 得失 | 判断 |
|---|---|---|
| `s8b_oracle_spec.py` に CLI を追加 | fixed path と validator に近い。一方、approval loader と生成・書込 capability が同居する | 非推奨 |
| 別 module に producer CLI | loader を read-only authority のまま保てる。active freeze、environment contract、binding 導出を producer 側へ隔離できる | 推奨 |
| 人間が bytes を直接配置 | compact canonical JSON、schedule hash、12 cell の binding、実 source hashを手作業で一致させる必要がある | 却下 |

将来の producer は `preview` と `install-approved` を分けるべきです。

- `preview`: canonical bytes、SHA-256、human-readable projection を標準出力または rulings パッケージへ返す。公式 2 directory には書かない。
- `install-approved`: explicit user approval 後にのみ、再導出した hash が receipt と一致する場合に固定 path へ create-only で配置する。任意 `--output` は持たせない。

### 書込作法

`_write_approved_manifest` の安全性は踏襲すべきです。

- dirfd 単位の traversal
- `O_NOFOLLOW | O_DIRECTORY`
- leaf の `O_EXCL`
- regular-file 検査
- partial write を考慮した write loop
- leaf と親 directory の `fsync`
- 失敗時に同一 inode の partial leaf だけを回収

根拠は `orchestrator/campaign/s8b_oracle_manifest.py:895-987` です。

ただし、この関数自体は pretty JSON と末尾 LF を生成します（同 `:903-905`）。reviewed spec は compact canonical bytes と末尾 LF なしを要求するため、直接再利用できません。将来タスクでは dirfd primitive を byte-oriented helper として抽出するか、同じ安全契約を専用 writer に実装します。

### provenance の択一

| 選択肢 | 長所 | 欠点・不足 | 規模 |
|---|---|---|---|
| (i) 現行の code pin のみ | raw bytes の改変は exact SHA-256 で閉じる。最小 | 誰が何を承認したかを機械表現しない | 小 |
| (ii) code pin + T-810 型 receipt | approval ID、scope、対象 SHA を内容と結び付けられる | receipt 単独には信頼根がない。pin または別の authority が必須 | 中 |
| (iii) git provenance も強制 | user commit、非 merge、ancestry を機械拘束できる | full git history への実行時依存、export/tarball での利用困難、private freeze helper の一般化が必要 | 大 |

推奨は **(ii) receipt を code pin に加える** です。receipt 単独を権威にはしません。

T-810 は receipt の exact key、schema、artifact raw hash を検査します（`orchestrator/campaign/t810_preregistration.py:142-185,758-795`）。一方、その prereg 自身が `approval_receipt_trust_root_absent=true` を明記しています（同 `:406-457`）。したがって、T-810 の形を表面的にコピーするだけでは足りず、oracle では以下を一体にします。

- receipt の `spec_sha256`
- rulings の approval ID
- 承認対象 scope
- code の `APPROVED_SPEC_SHA256`
- fixed-path raw bytes
- active freeze と環境契約の識別情報

T-810 policy の導入 commit `c80513a862a0fa1d66166fe9c832060a6abb0344` には非 none の AI-Agent trailer があり、親 M7 の履歴上の読みも支持されます。

(iii) を採るなら `_assert_user_commit` を直接 import せず、git provenance を一般 authority として設計し直す別タスクが必要です。

### `APPROVED_SPEC_SHA256` と TOCTOU

以下はすべて、承認後の**別タスク**で行う手順です。

1. schema reissue、producer、receipt loader を先に実装・commit し、公式 2 directory は空、pin は `None` の状態を維持する。
2. clean HEAD と active ratified freeze を固定し、AI producer が exact bytes と SHA-256 を生成する。
3. rulings が全値、decoded JSON、raw-byte SHA、active freeze、source hashes を提示する。ユーザーは hash だけでなく内容を承認する。
4. 承認後、実装担当が同じ clean HEAD から bytes を再導出し、承認 hash との一致を検査する。
5. 単一の staged change に、固定 path の bytes、receipt、同じ SHA の `APPROVED_SPEC_SHA256` を置く。bytes だけの commit、pin だけの commitには分けない。
6. 独立 checker が working tree ではなく staged blob の hash、staged pin、receipt、strict loader、full validator の一致を検査する。
7. ユーザーがその staged diff を review し、単一 commit にする。push は人間が行う。

worktree 上で bytes 配置から pin 編集までに短い窓は残りますが、その間は pin が `None` なので loader は fail-closed です（`orchestrator/campaign/s8b_oracle_spec.py:182-200`）。履歴上の分離は単一 commit で閉じ、staged blob 検査で commit 直前の差替えも閉じます。

## (2) D302 の schema 択一

### 先に区別すべき 2 schema

親 P2 は「2 directory の両方を見る」という点で正しいですが、schema 自体も 2 つあります。

| artifact | 現行 schema authority |
|---|---|
| reviewed spec | `s8b-oracle-reviewed-spec/v1` — `orchestrator/campaign/s8b_oracle_spec.py:18,109` |
| official manifest | `8b-oracle-manifest/v1` — `orchestrator/campaign/s8b_oracle_artifacts.py:20,131-146` |

D302 が直接論じているのは manifest schema です（`docs/decisions.md:13993-14019`）。一方、zero-file 番人は spec directory も同時に対象としています（`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`）。

したがって、選択肢 B は **spec だけの v2 化では不十分**です。reviewed spec と official manifest を協調して v2 に再発行する必要があります。

### 選択肢 A: schema 据え置き

最初の `reviewed_spec.json` を将来配置した時点で、test は `rglob("*")` でそのファイルを収集し、`durable_files == []` に失敗します。schema 内容は一切読みません（`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`）。

さらに `build_approved_manifest` は spec を読み、active freeze の全軸一致を検査した後、candidate directory に manifest を書きます（`orchestrator/campaign/s8b_oracle_manifest.py:1170-1232`）。この candidate も同じ test に捕捉されます。

A を通すためには、例えば次のどれかが必要になります。

- v1 spec/candidate を scan 対象から除外する
- 非空 directory を許す
- test を削除・skip する
- schema version によって v1 durable artifact を許す

いずれも「durable 発行 0 件だから v1 据え置き」という D302 の根拠を失ったまま受理集合を広げる変更です。規律 2 に抵触するため、**A は採用不可**です。

### 選択肢 B: 協調 v2 再発行

親への推奨は **B** です。ただし対象は以下の両方です。

- `s8b-oracle-reviewed-spec/v1` → `/v2`
- `8b-oracle-manifest/v1` → `/v2`

#### reviewed spec 側の consumer

- schema authority と exact check: `orchestrator/campaign/s8b_oracle_spec.py:18,105-110`
- production loader consumer:
  - `orchestrator/campaign/s8b_oracle_driver.py:487,497,1220`
  - `orchestrator/campaign/s8b_oracle_judge.py:372`
  - `orchestrator/campaign/s8b_oracle_report.py:1763`
  - `orchestrator/campaign/s8b_oracle_manifest.py:1186`
- fixture は定数を参照するため追随する: `orchestrator/tests/s8b_oracle_spec_fixture.py:38-89`
- 独立 raw golden は v1 literal と raw SHA を持つため、v2 の exact bytes/hash に再発行が必要: `orchestrator/tests/test_s8b_oracle_manifest.py:61-100,1078-1099`
- normative doc は D302 を新決定で supersede する。歴史記録である既存 worklog は遡及改変しない。

production consumer は loader 経由なので、定数と新 bytes が揃えばコード構造上は追随します。旧 v1 bytes は exact check で fail-closed になります。

#### official manifest 側の consumer

- authority/classifier: `orchestrator/campaign/s8b_oracle_artifacts.py:20,131-146`
- alias、生成、verify: `orchestrator/campaign/s8b_oracle_manifest.py:34,766-787,991-1018`
- driver の構造拒否: `orchestrator/campaign/s8b_oracle_driver.py:320-339`
- official manifest loader の production consumer:
  - judge
  - report  
  consumer pin は `orchestrator/tests/test_s8b_oracle_manifest_contract.py:18-34,85-102`
- schema alias test: `orchestrator/tests/test_s8b_oracle_artifacts.py:218-240`

旧 manifest v1 は classifier と verifier の両方で拒否されます。現時点で durable artifact は 0 件なので、データ移行対象はありません。

#### zero-file assertion は B でも落ちるか

落ちます。親 M4 の読みは正しいです。この test は schema を parseせず、両 directory の任意の file を拒否するからです（`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`）。

従って、B の schema 実装タスクでは、旧 test を単に「非空でもよい」に変えるのではなく、D302 の意図を次の lifecycle gate に再表現する必要があります。

1. 両 directory に旧 v1、未知 schema、非 canonical file が 1 件でもあれば失敗。
2. spec があるなら固定 path 1 件だけを許し、v2、pin、receipt、raw hash、full validation の全一致を要求。
3. candidate があるなら approved v2 spec と active freeze に対する `verify_manifest` 成功を要求。
4. candidate だけが存在する状態、余剰 file、unapproved bytes、hash 不一致を拒否。
5. mutation/negative test で v1、wrong pin、wrong receipt、malformed JSON、spec 内容不一致、未検証 candidate が必ず落ちることを固定。

これは「任意の durable file を許す」緩和ではなく、0-file という暫定前提を、v2 の有効状態だけを受理する強い不変条件へ置き換えるものです。この表現が採れないなら、correctness gate を保ったまま本走へ進む方法はありません。

### test の意図と実効

- 意図: D302 の「v1 durable artifact はまだ 0 件」という判断根拠を監視する番人。
- 実効: spec を初回発行しただけで赤になり、manifest candidate 発行でも赤になる。

test は runtime guard ではないため、pytest を無視すればプロセス自体を技術的に起動できます。しかし acceptance を必須とする repository workflow では、初回発行や本走を landing できなくするため、**実質的な本走阻止器**です。

## (3) 事前登録値の草案と承認パッケージ草案

### 値の草案

active ratified freeze の live pointer は現時点で存在しません。loader も live pointer なしを `no-active`、すなわち v2 未発効として拒否します（`orchestrator/campaign/s8b_ratified_freeze.py:1253-1256`）。従って、freeze 由来欄は条件付きまたは未確定です。

| field | 草案 | 状態・導出 |
|---|---|---|
| `n` | `8` | AI 推奨、ユーザー承認対象。既存文書では `N_oracle=8` は非拘束 planning prior（`docs/phase3-8b-descriptor-design.md:357-360`） |
| `master_seed` | `"s8b-oracle-v2-t499-20260812"` | 自由値の具体案。結果閲覧前にユーザーが exact string を承認する |
| `block_sizes` | `{"b0": 8}` | `sum=8` かつ単一 block 契約から導出 |
| `campaign_ids` | `{"b0": "s8b-oracle-v2-b0-20260812"}` | 自由値の具体案。block と一対一。repository 全体での過去 ID 衝突検査は別タスク |
| `holdout_ids` | `["rr20", "rr80"]` | 条件付き確定。将来の active freeze 全 holdout から sorted 導出 |
| `configuration_ids` | `["backoff_fixed_best","ident_all","p2_2_flag_opt","sort_best","stock_common","system_gate"]` | 条件付き確定。各 holdout の exact entry set から sorted 導出 |
| `schedule_sha256` | 未確定 | 上記の全値を承認後、producer が `build_schedule` から再計算 |
| `binding_identity` | 未確定、予定 12 件 | active freeze の 2×6 cell と `LaunchValidatedFreeze.binaries_by_cell` が必要 |
| `generator_versions` | 未確定 | schema/producer 実装完了後の clean HEAD の実 bytes を再 hash |
| `run_contract` | 下記の条件付き草案 | active freeze と active environment contract の一致を最終確認して確定 |
| `allowed_excluded_reasons` | `["competing_process","launch_failure","nonfinite_or_partial_output","performance_anomaly"]` | floor protocol からの流用案。oracle の除外契約として改めて承認対象 |

`build_approved_manifest` は `holdout_ids` が active freeze の全 holdout と sorted 完全一致し、全 holdout が同じ configuration set を持つことを要求します（`orchestrator/campaign/s8b_oracle_manifest.py:1193-1213`）。従って subset を自由に選ぶことはできません。

`n=8`、2 holdout、6 configuration なら、`build_schedule` が作る行数は `8 × 2 × 6 = 96` です（`orchestrator/campaign/s8b_oracle_manifest.py:243-263`）。既存文書の `verify ×96` planning prior とも一致しますが、これは既承認の oracle n ではありません（`docs/phase3-8b-descriptor-design.md:357-360`）。

### `binding_identity`

producer は freeze JSON の entry を手作業で写してはいけません。

- materializer は freeze entry と prepared binary から `genome_canonical`、`src_token`、`variant_id`、`entry_sha256`、`binding_sha256` を導出する（`orchestrator/campaign/s8b_materialization.py:98-146`）。
- `launch_validate` 後の型は全 scan 済み `binaries_by_cell` を保持する（`orchestrator/campaign/s8b_ratified_freeze.py:764-778`）。
- ratified validator は全 cell 集合、binding hash、freeze entry hash を検査する（同 `:1640-1720`）。

従って producer は `binaries_by_cell` から、holdout/configuration の辞書順で 12 record を射影します。active freeze と launch validation がない現時点では、実際の 12 record を推測して埋めることはできません。

### `generator_versions`

現 HEAD の既存 golden に記録された 5 digest は次のとおりです（`orchestrator/tests/test_s8b_oracle_manifest.py:81-91`）。

| key | path | 現 HEAD の静的候補 SHA-256 |
|---|---|---|
| `materializer` | `orchestrator/campaign/s1_direct_comparison.py` | `dc67d934c5554d17ef4886533088adb6333edbcfe68baab1e13d39348c370e55` |
| `report` | `orchestrator/campaign/s8b_oracle_report.py` | `cc28c86074aead3747eadcaaf1a09a2eaf4bdaae0ca72cca4a9d4f32bfd5acbf` |
| `judge` | `orchestrator/campaign/s8b_oracle_judge.py` | `6e90a77532e7ea68c14c2076268e38783180c6c142d23ed9ae7d09466201a0b2` |
| `outcome_stage_contract` | `orchestrator/campaign/s8b_outcome_stage_contract.py` | `f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af` |
| `artifacts` | `orchestrator/campaign/s8b_oracle_artifacts.py` | `b29f3dd6d989044a39f568f9e3621d93a66101b038e9a1913c3500c5e522f614` |

これは承認値ではありません。選択肢 B で少なくとも `s8b_oracle_artifacts.py` が変わるため、その hash は必ず変わります。全 5 件を schema 実装完了後の clean HEAD から再計算する必要があります。

現 validator の exact key 集合に producer 自身を 6 件目として足すことはできません（`orchestrator/campaign/s8b_oracle_manifest.py:53-62,430-470`）。producer の provenance は receipt と code review で表現し、generator set を広げるなら別の schema 設計タスクに分離します。

### `run_contract` の条件付き草案

```json
{
  "bench_max_rounds": 1,
  "ccbench_pin": "d706650cdb31e442bef45b9b4216951d4fb40969",
  "clocks": 2100,
  "contract_sha256": "e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01",
  "env_tag": "pegasus",
  "extime": 5,
  "reps": 5,
  "screening": "off",
  "verify": "legacy+s2"
}
```

この object はソース上の key・型・固定値制約を満たす形です。ただし実走検証はしていません。

- `reps=5`、`extime=5` は共有 authority の承認値（`orchestrator/campaign/s8b_experiment_numbers.py:2-15`）。
- `verify`、`screening`、`bench_max_rounds` は validator の exact 値（`orchestrator/campaign/s8b_oracle_manifest.py:396-427`）。
- `pegasus` generation 1 は `clocks_per_us=2100` を持つ（`orchestrator/campaign/env_contract.py:245-261`）。
- activation record は `pegasus` g1 と上記 contract SHA を active としている（`orchestrator/campaign/env_contract_activations/00000001.json:1`）。
- `ccbench_pin`、environment contract SHA、allowed reasons は現 floor protocol の値（`output/s8b-freeze/floor_protocol.json:1`）。

ただし active ratified freeze が未発効なので、`ccbench_pin`、`env_tag`、`clocks`、`contract_sha256` は最終値ではありません。driver は実走前に active environment contract と完全一致させるため、freeze 発効後に再導出が必要です。

### 承認パッケージ草案

ユーザーがそのまま判断できるパッケージは、次の目次にします。

1. **承認対象と非対象**
   - 協調 v2 再発行
   - exact reviewed spec bytes と SHA-256
   - receipt の approval ID と scope
   - 本承認は本走開始そのものではないこと
   - 本 wave では durable 発行も pin 設定もしないこと

2. **科学設計値**
   - `n=8`
   - master seed
   - 単一 block と campaign ID
   - 96 schedule rows になる導出
   - allowed exclusion reasons
   - 各自由値について採否欄

3. **active freeze からの導出値**
   - active generation、pointer、freeze SHA
   - holdout/configuration の全集合
   - 12 件の binding identity
   - subset が存在しないこと
   - 各 binding の entry hash と再計算結果

4. **実行環境契約**
   - `ccbench_pin`
   - `env_tag`
   - `contract_sha256`
   - clocks、reps、extime
   - verify/screening/bench rounds
   - active activation との一致

5. **再現性資料**
   - exact canonical JSON bytes
   - raw-byte SHA-256
   - schedule の human-readable table と schedule SHA
   - generator 5 source の path/hash
   - strict loader、canonicalization、full validator の静的検査結果
   - 実走していない検査の明示

6. **provenance**
   - rulings approval ID
   - approver
   - approval scope
   - receipt SHA と spec SHA の一致
   - code pin が authority で、receipt 単独を trust root にしないこと

7. **承認後に起きること**
   - 別タスクで schema/producer/gate 実装を完了
   - exact bytes、receipt、pin を単一 commit で発行
   - 親が関連テストと static check を実測
   - active freeze と approved spec から manifest candidate を生成
   - candidate を full verify した後にだけ本走判断へ進む

8. **誤承認時の故障モード**
   - `n` や seed の誤り: 検出力・順序事前登録が意図とずれる
   - axis の誤り: `build_approved_manifest` が cell product mismatch で停止
   - binding の誤り: spec loader または launch validation が停止
   - source hash の誤り: generator byte 検査が停止
   - run contract の誤り: driver が環境契約不一致で本走前に停止
   - exclusion reasons の誤り: legitimate failure を記録できない、または裁量的除外の余地を作る
   - provenance の誤り: bytes は一致しても「誰が何を承認したか」を証明できない
   - schema の誤り:旧 v1 の意味を再利用し、D302 と contract gate を破る

9. **変更・撤回規則**
   - 承認後に 1 field でも変えるなら新しい exact bytes と新しい承認が必要
   - create-only artifact は上書きしない
   - durable v2 発行後に schema の意味を変える場合は次 version へ再発行
   - revocation/provenance の機械契約は別タスクで確定

承認質問は少なくとも「協調 v2 を採るか」「自由値 4 件を承認するか」「active freeze 由来の exact projection を承認するか」「receipt + code pin を採るか」「最終 exact bytes と SHA を承認するか」に分けるべきです。

## 総括

親への推奨は、**選択肢 B、すなわち reviewed spec と official manifest の協調 v2 再発行**です。A は durable v1 を許すために現行 contract test の受理集合を広げる必要があり、規律 2 と両立しません。

producer は別 module とし、AI が exact bytes を導出、rulings が内容と hash を提示、ユーザーが承認する形にします。provenance は **receipt + code pin**を推奨し、receipt 単独は authority にしません。

本 wave で実装してはならず、すべて別タスクへ分離する項目は次のとおりです。

- producer CLI と hardened writer
- reviewed spec／official manifest の v2 schema 実装
- zero-file test から v2 lifecycle gate への置換
- receipt schema／loader
- git provenance 検査を採る場合の一般化
- active freeze 由来の binding と run contract の最終生成
- `reviewed_spec.json`、manifest candidate、receipt の durable 発行
- `APPROVED_SPEC_SHA256` への値設定
- pytest、acceptance、計測の実走

本調査では公式 2 directory への書込み、pin 変更、contract test の緩和、実装差分のいずれも行っていません。