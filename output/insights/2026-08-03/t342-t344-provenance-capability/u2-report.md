U2「identity 束縛」を実装し、working tree に残しました。docs・所有外ファイル・git add/commit/branch は操作していません。U1 の既存差分も変更していません。

### 変更前の受理・拒否挙動

- legacy key: admission を含まず、同一 genome/source/toolchain なら class を跨いで同じ key。sidecar がなく、binary があれば source/trace 検査後に hit になり得ました。
- v2 preimage: admission field がなく、class/receipt の違いが digest を変えませんでした。
- completion manifest: exact schema に admission がなく、receiptless manifest が構造上の正規形でした。
- campaign replay: campaign ID/lock に admission policy がなく、variant 単位の最終状態集約だけでした。receiptless COMMIT、attempt 間 splice、別 attempt の receipt 流用を区別できませんでした。
- なお U1 適用直後は materializer が旧 `require_build_admission()` signature を呼ぶため、実際の build 呼出しは TypeError になる過渡状態でした。上記はその背後に残っていた validator/identity の受理面です。

### 変更後の4面

- legacy cache:
  - 全 class で receipt SHA を key に含めます。stock も例外ではありません。
  - exact-key の `admission.json` sidecar を必須化しました。
  - sidecar 欠落、schema/key/class/policy/source/current admission 不一致を明示拒否します。
  - fresh build は staging 内で binary＋sidecarを完成させてから publish します。旧 namespace fallback はありません。
- v2 preimage:
  - full canonical admission receipt が必須です。
  - admission、source root、current `SourceEvidence`、build request の genome/commit/root を exact 照合します。
- completion manifest:
  - top-level admission が必須です。
  - preimage admission、manifest admission、current derived admission の三者が一致した新 entry だけ通します。
  - admission 欠落旧 manifest を新 digest 配下へ置いた場合も validator で拒否します。
- campaign/replay:
  - `search_config.build_admission` に policy preimage を入れ、IDとlockを同時に変更しました。
  - lock の exact top-level keys と current policy を照合します。
  - BUILD_START/DONE/COMMIT を attempt ID で束ね、receipt SHAを伝播します。
  - cross-attempt splice、重複START、receipt SHA流用、receiptless DONE/COMMITを拒否します。
  - receiptless pre-build attempt は、DONE/COMMITがない場合だけ通ります。abort後の正規retryは通ります。
  - 過去attemptのsourceを現在worktreeと比較していません。過去receiptはcanonicality/policy/topologyだけを検証し、現在source一致は現在候補とcache境界で要求します。

主な変更先は [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u2/orchestrator/campaign/buildcache.py)、[pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u2/orchestrator/campaign/pipeline.py)、[wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u2/orchestrator/campaign/wal.py)、[ident.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u2/orchestrator/campaign/ident.py) です。

### 検査結果

実行成功:

- U2 production 7ファイル＋test 2ファイルの `python3 -m py_compile`
- `test_buildcache_v2` / `test_campaign` のmodule import
- `git diff --check`

pytest nodeidの実行結果はありません。計算ノードdispatchを次の範囲で3回試みましたが、すべて実行開始前に `qstat -Q preflight rc=1` で失敗しました。

- `test_buildcache_v2.py -x -q`：2回、実行0件
- `test_campaign.py -x -q -k 'campaign_id... or attempt_topology... or tail...'`：1回、実行0件

したがって、追加した以下を含めpytest greenとは主張しません。

- `test_legacy_key_binds_admission_for_all_classes`
- `test_legacy_hit_requires_exact_admission_sidecar`
- `test_v2_preimage_binds_exact_admission`
- `test_completion_manifest_rejects_missing_receipt`
- `test_campaign_id_binds_admission_policy`
- 4つのattempt topology nodeid
- `test_resume_rejects_committed_attempt_without_receipt`
- 正規receipt化した既存tail-repair nodeid

未実行範囲は、上記nodeidを含むpytest全件、関連する所有外test、フルスイート、build、campaign実走、mutationです。

### 他単位未landによる期待赤

- U3 caller/CLI:
  - `backoff_*`、`between_run_floor.py`、`demo.py`、`p2_2.py`
  - `p3_kickoff.py`、`p3_s4_red.py`、`p3_s4_loop*.py`
  - `s1_direct_comparison.py`、`s1_verify_extime_calibration.py`
  - `s2_verify_calibration.py`、`s3_lock_coverage.py`、`s5_permutation_coverage.py`
  - `sanity_silo.py`
  - 直接constructor、旧evaluate/run_campaign signature、未束縛campaign configが残っています。
- U4 consumer/overlay:
  - `s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`replay.py`
  - Layer3、critic、autonomous trial/completeness
  - overlayとpositive receipt consumer gateはまだ未landです。
- U5/qualification:
  - `s8b_floor_campaign.py`、`s8b_oracle_driver.py`
  - `qualification/t126_driver.py`
- 共有testへの波及:
  - `test_build_site_gate.py`
  - `test_p3_exploration_namespace.py`
  - `test_p3_s4_loop_trigger_gating.py`
  - `test_screening_driver.py`
  - `test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`
  - `test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`
  - `test_t126_qualification_driver.py`

それ以外の回帰赤は観測していません。ただしpytest未実行のため、不存在とは主張しません。

### 変更した既存期待値

- legacy stock key:
  - 歴史値 `silo_24dd2f7509_t0` を `_PRE_T343_GOLDEN_CK0` として保存。
  - 新値は `silo_d7eee324f7_t0`。
  - 旧値が誤りな理由: stockを含めreceipt digestが必須になったため。
- 代表campaign ID:
  - 歴史値 `readheavy-locont-fullsearch-45ca7ab9` を保存。
  - 新値は `readheavy-locont-fullsearch-4347a1fd`。
  - 旧値が誤りな理由: admission policyを含まないpreimageだったため。
- v2 exact fixture:
  - preimageとmanifest双方へfull admission mapを追加し、exact receipt key集合も固定しました。
  - 旧fixtureが誤りな理由: receiptless completionを正規形としていたため。
- T-316直接constructor前提:
  - 必須引数をcaller-declared admissionから`BuildRunContext`へ変更しました。
  - 旧期待が誤りな理由: classをcallerが選ぶ経路はU1契約で廃止されたため。

## 総括

最重要の設計判断は次の3点です。

1. cache identityをclass名だけでなく、source evidenceを含むfull canonical receiptへ束縛した。
2. campaign policyと各build attemptを別層で束縛し、variant単位の最後勝ち集約によるspliceを排除した。
3. replayでは過去sourceと現在worktreeを比較せず、現在source照合を現在候補/cache境界へ限定した。

既知限界は、ABA/混在snapshot、同一process内issuerの真正性、歴史artifact全体の遡及分類が未閉包なことです。またU3–U5未landのため、現時点ではend-to-end campaign実行は期待赤です。