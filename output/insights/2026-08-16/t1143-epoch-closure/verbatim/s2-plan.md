## 1. 編集面 file:line 表

以下は現行行番号である。確定済みの 4 file なら exact 12 path、後述の推奨どおり `__init__.py` も採るなら exact 13 path となる。表の変更後は後者を採用した案である。

| file:line | 現在の内容 | 変更後の内容 | 変更の理由 |
|---|---|---|---|
| `orchestrator/campaign/campaign_lock.py:27-38` | exact 8 path という comment と 8 要素 tuple | 既存順を保ち、`core.py`、`dsg.py`、`model.py`、`parse.py`、最後に推奨追加の `__init__.py` を追記。comment は exact 13 path | ここが v2 authority の exact key 集合と epoch の順序付き hash preimage の正本 |
| `orchestrator/campaign/campaign_lock.py:167-180` | tuple と同じ exact key 集合を要求し、tuple 順で map を再構成 | ロジック変更なし | 定数変更を自動消費する。順序は epoch hash に効くため、将来 sort へ変えない |
| `orchestrator/campaign/artifact_admission.py:63` | domain は `campaign-verifier-epoch/v1` | 据え置き | P2 の評価どおり。wire key、schema、`E1:` prefix も変更しない |
| `orchestrator/campaign/artifact_admission.py:65-70` | exact 8 path、verifier 全体を除外 | identity scope を exact 13 path とし、`pipeline.py` と verifier 5 file を含むと明記。excluded scope は P3 の exact 3 file | 現在の診断は 4 file 追加後に偽になる |
| `orchestrator/campaign/artifact_admission.py:98-103` | exact 8 path、verifier 全体を束縛しないという class docstring | exact 13 pathと、束縛する verifier 5 file、束縛しない 3 file を記載 | `CampaignVerifierEpoch` の意味を定数と一致させる |
| `orchestrator/campaign/artifact_admission.py:172` | blob map の exact 集合を定数と比較 | 変更なし | 新定数を自動消費する |
| `orchestrator/campaign/artifact_admission.py:714-750` | docstring は exact 8、738-740 は定数順で hash | docstring のみ exact 13 と exact excluded set へ更新。hash 式は変更なし | 既存の path、NUL、32-byte digest の順序付き preimage を維持する |
| `orchestrator/campaign/artifact_admission.py:787-793` | 記録 map と current map の exact 比較 | 変更なし | verifier drift が certified gate で `E1-stale` になる実体 |
| `orchestrator/campaign/artifact_admission.py:796-805` | exact 8、verifier 全体を除外する API docstring | exact 13 と exact excluded set へ更新 | 公開 API の名乗りを真にする |
| `orchestrator/campaign/contract_loader_binding.py:2` | 件数を持たない歴史名の説明 | exact 13 path の binding であると明記 | brief が指定した module docstring を具体化する |
| `orchestrator/campaign/contract_loader_binding.py:49-53` | enforcement closure 8 path | 13 path | class が検査する map と説明を一致させる |
| `orchestrator/campaign/contract_loader_binding.py:73-85,324-377` | 定数による exact 集合検査、capture、live/committed 検証 | ロジック変更なし | 定数変更だけで追加 file の disk/blob drift を検査する |
| `orchestrator/tests/test_t671_source_binding.py:22-31` | 独立した exact 8-path tuple | production と独立に、同じ順序の exact 13-path tuple | production 定数から要素を外す変異を test parameter ごと消失させない |
| `orchestrator/tests/test_t671_source_binding.py:119-128` | test 名が `exact_eight_paths` | `test_enforcement_source_closure_is_the_independent_exact_thirteen_paths` | exact cardinality を保持する。外部 nodeid 参照は検索範囲内で 0 件 |
| `orchestrator/tests/test_t671_source_binding.py:131-134,179-182,207-210,308-311` | 8 要素による 4 組の parametrize | decorator 自体は変更せず、独立 tuple の増加を自動消費 | 4 file は各 parametrize に 4 node ずつ増える。P1 採用時は shim の node も増える |
| `orchestrator/tests/test_artifact_admission.py:312-346` | exact 8-path fixture。golden domain は `/v1` | docstring を exact 13-path へ更新。fixture loop と `/v1` golden は変更なし | tuple と domain を動的に消費済み |
| `orchestrator/tests/test_artifact_admission.py:925-941` | `"exact 8 path"`、`pipeline.py`、verifier wildcard の部分一致 | identity scope と excluded scope を提案 literal へ exact equality で比較 | 期待値を緩めず、診断の集合を独立 golden として固定する |
| `orchestrator/tests/test_artifact_admission.py:1051-1059` | blob map の長さ `== 8` | `== 13` | brief 外で見つかった固定件数依存。`>=` にはしない |
| `orchestrator/tests/test_artifact_admission.py:1107` 付近 | verifier 各 file の certified drift test はない | verifier 4 file、P1 採用時は shim も対象にした新規 parametrize test を追加 | 下位 binding だけでなく実際の certified consumer を通して fail-closed を固定する |
| `orchestrator/tests/test_s6_sort_sweep.py:616-630` | fixture docstring が exact 8-path | exact 13-path | loop は動的だが説明が固定件数に依存 |
| `orchestrator/tests/test_s8a_trigger_sweep.py:826-840` | fixture docstring が exact 8-path | exact 13-path | 同上 |
| `orchestrator/verifier/{core,dsg,model,parse}.py:全体` | closure 外 | bytes は一切編集せず、path だけ closure に追加 | 確定裁定と no-touch 不変条件を両立 |
| `orchestrator/verifier/__init__.py:16-20` | closure 外の再 export | bytes は編集せず、推奨案では path を closure に追加 | `pipeline.py:30` が実際に解決する shim を束縛する |

静的依存の全数確認は次のとおり。

- `CONTRACT_LOADER_RELATIVE_PATHS` を `orchestrator/campaign`、`orchestrator/verifier`、`orchestrator/tests` で検索し、43 hit、11 file だった。上表以外では `campaign_lock_test_support.py:10-20`、`test_campaign_lock_codec.py:34-47,166-179,226-232`、`test_layer3_report.py:54-64`、`test_bench_first_real_wal.py:158-173` が動的 fixture、missing-key parametrize、先頭要素の型異常 test として自動追随する。
- `test_artifact_admission.py:1200-1243,1294-1298,1452,1474,1496,1509,1534-1538` も定数から fixture、先頭要素、membership、alias identity を導くためロジック変更不要。
- scope の report consumer は `autonomous_trial_completeness.py:1920-1921`、`backoff_sweep_report.py:90-92,152-155`、`layer3_report.py:246-252`、`p2_2_report.py:106-107`、`s1_report.py:118-134`、`s6_sort_sweep.py:521-524`、`s8a_trigger_sweep.py:626-629`、`s8b_oracle_report.py:375-410`。すべて epoch object または scope 定数を転送するため変更不要。対応 test も `test_s1_report.py:464-465`、`test_layer3_report.py:536-537`、`test_s8b_oracle_report.py:795-796` で動的に受ける。
- `silo_ladder_rung1.py:262-286` は別閉包で、`verifier.rglob("*.py")` により verifier 8 file 全部を既に束縛する。campaign closure の変更は不要。
- `exact 8`、`8-path`、`closure 8`、blob map の `len(...)` を指定パスで検索した固定依存は、上表の production docstring、fixture 3 件、`== 8` 1 件だけだった。`docs/decisions.md:12351-12395` は歴史的 D268 なので実装子は編集せず、親が段 7 で supersede を記録する。
- `orchestrator/verifier/(core|dsg|model|parse).py` の literal を campaign、verifier、tests で検索した結果は 0 件だった。したがって新しい独立 tuple と新規 certified test の parameter は純増である。
- 改名前の T671 test 名と `test_t671_source_binding.py::` を同じ限定パスで検索し、外部 meta-test/nodeid consumer は 0 件だった。

## 2. (P1) shim の評価

`__init__.py` は入れることを推す。ただし、これは確定裁定の「verifier 4 ファイル」という literal を超える追加であり、段 4 で明示裁定が必要である。

入れない場合、`core.py:19-24`、`dsg.py:26-27`、`model.py:202-220`、`parse.py:41` の実装 bytes は閉じる。一方、campaign はそれらを直接呼ばず、`pipeline.py:30` が package export を import し、`pipeline.py:1056` でその object を呼ぶ。closure 外の `__init__.py:16` を別実装へ向ければ、束縛済み 4 file と `pipeline.py:1083` を変えずに `vr.certified` の供給元を差し替えられる。この dispatch edge は開いたままである。

入れる場合、`pipeline.py:30` から `__init__.py:16`、`core.py:19`、`model.py:218`、`pipeline.py:1083` までの直接の gate decision 経路が閉じる。ただし次は開いたままである。

- `__init__.py:20` が import する `report.py:42-76`。通常の制御フローでは `result_to_dict` は reject 分岐へ入った後の `pipeline.py:1090` で呼ばれるため、受理可否ではなく構造化 rejection payload が未束縛となる。
- `cli.py:23-25,58-100` と `__main__.py:5-8`。これは campaign pipeline とは別の CLI gate である。

敵対的な import-time side effect まで閉じるなら `report.py` も同時に入れて exact 14 にすべきである。CLI 全体まで名乗るなら `cli.py` だけでは足りず、`__main__.py` も必要で exact 16 になる。本 plan の最小推奨は campaign の直接 dispatch を閉じる `__init__.py` までである。

## 3. (P2) domain

`_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` は `/v1` のまま据え置くことを推す。

据え置きの具体的な危険は、旧 8-path generator と新 13-path generator がどちらも `E1:<digest>` を発行し、表示値だけでは preimage schema を判別できないことである。古い binary、repo 外へ複製された epoch、rollback 後の値を横断比較すると、同じ `E1` namespace の意味が曖昧になる。

ただし、これは同じ digest が生成されるという危険ではない。`artifact_admission.py:738-740` は path、NUL、固定長 digest を順に入れるため、要素追加後の preimage は旧 preimage と異なる。さらに brief 前提では v2 lock も保存済み epoch artifact も 0 件なので、現 corpus に旧定義と新定義が同居する実害はない。

domain だけ `/v2` に上げる場合、直接編集は `artifact_admission.py:63` と独立 golden の `test_artifact_admission.py:336` で足りる。lock の key、schema、identity preimage は増えないが、将来出力される全 `campaign_verifier_epoch` 値が変わる。version を wire 上でも判別可能な `E2` として表すなら、さらに次が変更面になる。

- `artifact_admission.py:121-135,742-748,761-793`
- `layer3_schema.json:62-64`
- `s8b_oracle_artifacts.py:174-200`
- E1 state/prefix を固定する layer3、S1、S8b、backoff 系 test

これは本 wave の「wire key・schema を変えない」を越える。現状では scope 文字列を必須診断として更新し、domain は据え置く方が変更面に比例している。

## 4. (P3) excluded_scope 文言

P1 の `__init__.py` 追加を採用する前提で、文言は次の 1 つを提案する。

`verifier package 内で束縛しない implementation bytes は orchestrator/verifier/__main__.py, orchestrator/verifier/cli.py, orchestrator/verifier/report.py`

`rg --files orchestrator/verifier` が返す Python source は exact 8 file である。計画上束縛する `__init__.py`、`core.py`、`dsg.py`、`model.py`、`parse.py` を差し引くと、この 3 file だけが残るため真である。

親が P1 を不採用にする場合は `__init__.py` も実際の excluded set に戻るため、この文言をそのまま実装してはならない。

## 5. 新設テスト

既存 parametrize が自動で増やす検出力は次のとおり。

- `test_t671_source_binding.py:131-177` は verifier 4 file の未 commit drift による新規 lock/WAL 作成前拒否を各 1 node 追加する。
- 同 `207-276` は記録 commit blob mismatch を各 1 node 追加する。
- 同 `179-204,308-346` も live binding と共有 fixture を各 file について追加被覆する。
- `test_campaign_lock_codec.py:166-179` は各新 path が欠けた v2 map の拒否 node を追加する。
- 独立 tuple test は要素数、内容、順序を exact に固定する。

これらだけでは、既存 campaign を `CERTIFIED_ACCEPTANCE` として読む中央 gate、すなわち `artifact_admission.py:771-793` を verifier 4 file ごとには通さない。

最小の純増として、`test_artifact_admission.py:1107` 付近へ 1 本の parametrize test を追加する。parameter は production tuple から導かず、verifier 4 path を literal に持たせる。P1 採用時は `__init__.py` も加える。

各 node は次を行う。

1. clean な `_committed_closure_repo` と v2 campaign を作る。
2. 対象 file を未 commit のまま変更する。
3. `require_admitted_campaign(..., purpose=CERTIFIED)` が `CampaignVerifierEpochRejected`、`E1-stale`、`current-closure-unavailable` で拒否することを exact に確認する。
4. 同じ変更を commit し、今度は `recorded-current-closure-mismatch` で拒否することを確認する。
5. 両方で exception の epoch が元の `_expected_fixture_epoch()` と一致し、記録 campaign bytes が変更されていないことを確認する。

既存の `pipeline.py` committed-drift test `test_artifact_admission.py:1081-1105` は残す。exact equality、exact count、reason code は一切緩めない。

## 6. 実装順序

1. 段 4 で exact 12 か推奨 exact 13 か、domain 据え置きを確定する。ここが未確定のまま count、順序、scope 文言を書かない。
2. 独立 tuple、test 名、exact count、scope golden、新規 certified parametrize test を先に変更する。この時点では production が exact 8 のため意図的に赤になる。
3. `campaign_lock.py:27-38` の正本 tuple と comment を変更する。これで codec、binding、fixture、parametrize は自動追随するが、scope literal test はまだ赤である。
4. `artifact_admission.py` の scope 定数と 3 docstring、`contract_loader_binding.py` の 2 docstring、test fixture 3 件の固定件数説明を更新する。
5. 親が focused test、関連 consumer test、4 file の path-removal 変異 matrix、全受入を実走する。本 plan worker は実走していない。

なお `artifact_admission.py` 自身は既に closure の一員である。これを編集してから commit するまで、実 repo を直接使う certified 実行は live drift として fail-closed する。これは期待された赤であり、xfail、dirty bytes の差し込み、gate 回避で緑にしてはいけない。最終確認は clean な commit snapshot でも行う必要がある。

## 7. 未解決の疑問 (親が段 4 で裁定すべきもの)

- 確定裁定の literal を超えて `__init__.py` を加え、exact 13 とするか。本 plan は追加を推す。
- threat model に import-time side effect と構造化 rejection payload まで含め、`report.py` も同じ wave へ加えるか。加えるなら exact 14 となる。
- CLI の correctness gate まで `campaign_verifier_epoch` の名乗りに含めるか。含めるなら `cli.py` と `__main__.py` を対で扱う必要があり、全 verifier source を束縛する exact 16 になる。
- domain `/v1` を据え置くか。本 plan は、現 corpus の v2 lock 0 件と wire 拡張面を踏まえて据え置きを推す。

## 総括

- 確定 4 file は必ず追加し、技術的には dispatch shim の `__init__.py` も加える exact 13 を推す。
- domain は `/v1` のままにし、scope 診断で新しい閉包を明示する。
- 固定件数 test 1 件と fixture docstring 3 件が brief 外の必要変更として見つかった。
- 新規 parametrize test で verifier drift を実際の certified gateまで通し、未 commit、commit 後の両方を fail-closed に固定する。
