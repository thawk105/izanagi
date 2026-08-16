```text
# プラン v1

## 1. 共通下位境界の位置

結論: brief (P1) の `measure_point` 単独案は採らない。共通実行 gate を `orchestrator/calibrator/runner.py:392-421` の `run_once` に置き、floor 固有の注入 seam は `s8b_floor_campaign.py:3425-3432` の callback 呼出し直前でも閉じる二重境界とする。

`orchestrator/calibrator` と `orchestrator/campaign` の production Python を対象に列挙した `measure_point` 呼出しは次のとおりで、これ以外の直接呼出しはない。

1. `orchestrator/calibrator/sweep.py:73-97`
   - `run_sweep` は `measure_fn=measure_point` を既定にし、引数の任意 `workload` を渡す。
   - `calibrate` も任意の workload を受ける (`sweep.py:134-157`)。CLI は `--workload` を無制限の key/value として受ける (`orchestrator/calibrator/cli.py:98-108,124-147`)。
   - よって holdout 相当を渡しうる。現在の非 holdout 入力は token なしでも従来どおり受理する。

2. `orchestrator/calibrator/sweep.py:202-211`
   - `calibrate` の sweep、noise、scale 全経路がここへ落ちる (`sweep.py:223-263`)。
   - 同じ任意 workload を使うため holdout 相当を渡しうる。

3. `orchestrator/campaign/pipeline.py:443-458`
   - `_run_bench` は `PerfConfig.workload` をそのまま渡す。`PerfConfig` は任意 dict を受ける (`pipeline.py:151-158`)。
   - `evaluate` の screening と通常 bench の両方から到達する (`pipeline.py:1112-1116,1213-1228`)。
   - 構造上 holdout 相当を渡しうる。現在の合法な非 holdout workload の受理は変えないが、潜在的な rr20/rr80 の無 admission 実行は変わる受理集合として D に明記する。

4. `orchestrator/campaign/s8b_floor_campaign.py:4531-4543`
   - 実 freeze のセルを渡すため、確実に rr20/rr80 を渡す。
   - 本 wave の実結線対象である。

5. `orchestrator/campaign/pegasus_floor_scoping.py:137-147`
   - 関数引数自体は任意だが、production の `POINTS` は rr5、rr50 のみ (`pegasus_floor_scoping.py:48-70,204-234`)。
   - 現在到達可能な入力に holdout はなく、受理集合は変わらない。

6. `orchestrator/campaign/between_run_floor.py:78-85`
   - 関数引数自体は任意だが、production の `POINTS` は rr5、rr50、rr95 のみ (`between_run_floor.py:63-67,156-178`)。
   - 現在到達可能な入力に holdout はなく、受理集合は変わらない。

`measure_point` は最下層ではない。自身が `run_once` を呼び (`runner.py:519-534`)、実 subprocess は `run_once` 内の `runner.py:409-421` で始まる。さらに `orchestrator/campaign/backoff_overthrottle.py:31-32,92` は `measure_point` を通らず `run_once` を直接呼ぶ。現在の workload は rr5/rr95 (`backoff_overthrottle.py:45-48`) なので現状値は変わらないが、P1 の共通性を反証する独立経路である。

層反転は次の形で避ける。

- 新規の stdlib-only leaf `orchestrator/holdout_observation.py` に、最小署名、effective gflag の last-wins 解釈、sealed `HoldoutObservationAdmission`、`assert_issued_holdout_observation` を置く。
- calibrator はこの leaf だけを import し、`orchestrator.campaign` や `trial_registry` を import しない。
- `trial_registry.HOLDOUT_BINDINGS` の H1/H2、workload 名、rratio の現在値は同 leaf の定義から射影する。これには `trial_registry.py:51-57` の意味不変編集が必要である。
- I6 の「8c の受理集合を変えない」は守れるが、「trial_registry のファイルを一切触らない」とは両立しない。詳細は §9 の裁定事項とする。

`run_once` は CCBench の last-wins と同じ方法で `-ycsb_rratio=` の最終値を読む。現在の最小署名で 20 または 80 なら、subprocess や一時 directory 作成より前に admission を要求する。token が渡された場合は ratio、records、threads、binary digest、cell binding も照合し、別セルへの流用を拒否する。20/80 以外で token 未指定なら既存 call shape と受理を変えない。

floor の `measure_fn` は `run_campaign` へ注入可能 (`s8b_floor_campaign.py:4052-4093`) で、`_Runner._run_session` が直接呼ぶ (`3425-3432`)。したがって `measure_point` または `run_once` だけでは、注入 callback が値を返す経路を塞げない。次の位置で閉じる。

- `_Runner` に cell ごとの admission mapping を保持させる (`s8b_floor_campaign.py:3230-3269`)。
- `run()` 冒頭の `_validate_live_admissions` (`3569-3589`) で全セルの存在と exact binding を検査する。
- `_run_session` の callback 呼出し直前 (`3425-3429`) でも対象 cell と token を再照合する。
- 外部の四引数 `measure_fn` seam は維持する。内部 wrapper が先に token を検査し、既定 closure の場合だけ `measure_point(..., holdout_observation_admission=token)` へ転送する。既存テスト callback の署名や期待値は変えない。

代案比較:

- (a) producer 側だけ: floor の注入 seam は確実に塞げるが、calibrator、pipeline、将来の第三 producer は自動では塞がらない。単独案として不採用。
- (b) freeze loader 側: `load_verified_freeze` は bytes/hash/parse の leaf にすぎない (`s8b_freeze_io.py:30-68`)。oracle driver や verdict も読む (`s8b_oracle_driver.py:308-317,354-406,542-562`; `s8b_verdict.py:968-1005`) ため、ここで台帳を消費すると非計測の読込みで一回性を失う。tag だけ付けても producer が捨てられる。単独案として不採用。
- `run_once` gate: 今後の producer が標準 CCBench 実行 API を使えば producer 側の追加実装なしで拒否される。これが第三 producer に対する共通境界である。
- 任意コードが直接 `subprocess.run` すれば Python 関数 gate は迂回可能である。新 D では「production throughput producer は `run_once` を唯一の実行 gateway とする」と定める。OS capability まで含む絶対的な実行禁止は T-523 の射程外であり、過大主張しない。

## 2. holdout 署名の識別

識別を二段に分ける。

1. floor 内での provenance 識別
   - authority は `VerifiedFreeze.document["holdouts"]` の map membership と bytes SHA-256 である。
   - 実 artifact では map key `rr80` に `candidate_id=H1` と rratio 80 がある (`output/s8b-freeze/holdout_freeze.json:39-48`)。
   - map key `rr20` には `candidate_id=H2` と rratio 20 がある (`holdout_freeze.json:307-315`)。
   - `enumerate_cells` は map key を列挙し (`s8b_floor_contract.py:317-348`)、`holdout_id` として cell へ写す (`352-362`)。
   - したがって「freeze 由来」の一次判定は、検証済み freeze の map key から再導出された cell であることとする。caller が渡した workload dict の自己申告は authority にしない。

2. 共通下位境界での最小署名
   - `run_once` では freeze provenance が既に失われ、gflag しか見えない。この境界では現行共通束縛の `candidate_id + ycsb_rratio` を使う。
   - 新 leaf の定義は概念上、H1 = `(freeze_holdout_key="rr80", trial_workload_name="rr80", ycsb_rratio="80")`、H2 = 同じく rr20/20 とする。
   - skew、rmw、records、threads を共通 `HoldoutSpec` の識別条件へ追加しない。それらは admission row に「実 freeze から得た観測座標」として exact 保存・照合するだけで、trial 側束縛の意味論には昇格させない。これにより [T-525] は実装しない。
   - rratio-only は現在の最小共有署名なので、別 skew 等でも effective rratio が 20/80 なら admission 必須となる。これは意図した fail-closed な受理集合変更であり、新 D と境界テストへ明記する。[T-525] は後にこの過不足を正式な全軸束縛で解消する。

名称は次のように分離する。

- `freeze_holdout_key`: freeze map key の rr20/rr80。
- `freeze_candidate_id`: H1/H2。
- `trial_workload_name`: 8c registry の workload 名 rr20/rr80。
- 既存 floor artifact の `holdout_id` は互換性のため変更しないが、新 module へ渡す adapter で `freeze_holdout_key` と明示的に改名する。
- 集合が同じことは対応関係の検査に使うだけで、`holdout_id` と workload 名を同義語として扱わない。

既存漏洩検査器の三軸 conjunction (`s8b_holdout_freeze.py:401-406,487-522,625-637`) は「repo に既知の三軸が現れていないか」の検査であり、実行時 admission の識別器としては使わない。実走後には hit が生じうる設計であることも docstring に明記済み (`s8b_holdout_freeze.py:919-928`)。

## 3. admission の発行根拠

実 `floor_protocol.json` は `output/s8b-freeze/floor_protocol.json:1` の 774 bytes、SHA-256 は `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac` である。存在する field は次だけである。

- `schema`、`formula`、`env_tag`、`ccbench_pin`
- `freeze.path`、`freeze.sha256`
- `stock_configuration`、`n_sessions`、`reps`、`master_seed`
- `schedule_algorithm`、`extime_s`、`wired_min_rel_floor`
- `retry_slots_per_cell`、`session_cv_max`、`cell_cv_max`
- `scale_adequacy_rel_tolerance`、`allowed_excluded_reasons`
- `contract_sha256`

`confirm_user_freeze`、`confirmed_by`、`approved_by`、承認時刻は protocol に存在しない。`--confirm-user-freeze` は生成時の手続 gate (`s8b_floor_campaign.py:718-766`) であり、返す receipt も status/path/byte_length/sha256 だけである (`791-796`)。一方、freeze bytes には `confirmed_by` と `confirmed_at` が存在する (`holdout_freeze.json:620-621`)。

よって P2 は次のように修正する。

- 発行 authority は「`--confirm-user-freeze` が記録されていること」ではなく、固定 path `output/s8b-freeze/floor_protocol.json` の HEAD 100644 blob と、そこから参照される固定 `holdout_freeze.json` の HEAD 100644 blobである。
- working-tree bytes が各 HEAD blob と exact 一致すること、raw protocol SHA が渡された `protocol_sha256` と一致すること、`protocol.freeze.path/sha256` が固定 freeze path/bytes と一致することを発行前に検査する。
- protocol は validator 上 `master_seed` 等を自由値として許す (`s8b_floor_campaign.py:556-570`)。したがって単に `validate_protocol` を通る別 protocol は authority にしない。CLI `--protocol` は固定 canonical path 以外を拒否し、同一 key を別 protocol hash でリセットできないようにする。
- 既存の fixed-file、hash、committed historical blob 検査 (`s8b_floor_campaign.py:2518-2565,2591-2598`) から狭い共通 primitive を抽出して使う。selector prediction 等を含む official preflight 全体は pilot admission の要件にしない。
- `measurement_head` を ledger row に保存する。自己コード hash による自己認証は循環するため、T-523 では新しい承認儀式として追加しない。

8c との構造対応は次である。

- `admit_registered_launch` は manifest、registry、effective preregistration を再導出してから sealed admission を返す (`trial_registry.py:1311-1361`)。
- caller 構築値は `assert_issued_trial_launch_admission` が拒否する (`1364-1405`)。
- durable な一回性との対応は `record_trial_start_once` の方が近く、admission 再導出後に lifecycle 行を append し (`1680-1739`)、durable update 後に token state を登録して返す (`1742-1772`)。
- 新しい `admit_floor_holdout_observations` は、前半を `admit_registered_launch`、書込みと token 発行順を `record_trial_start_once` に対応させる。
- `TrialLaunchAdmission` 自体は流用しない。trial の起動許可と freeze cell の観測許可は別 capability であり、同名 rr20/rr80 を理由に型を混ぜない。
- 8c の registered/unregistered API、理由コード、certifying 値は一切変更しない。

## 4. 一回性台帳

P3 の key は維持するが、曖昧な `holdout_id` を `freeze_holdout_key` に改名する。

`(freeze_sha256, protocol_sha256, freeze_holdout_key, configuration_id)`

この key は 1 freeze cell に 1 admitted campaign run を許す。session、rep、retry、prereg generation、arm、replicate slot は key に入れない。12 セルに 12 行であり、8 session による 96 行にはしない。これは [T-524] の実験単位を変更しない。

各 JSONL 行の exact schema は次とする。

- `schema_version`: `s8b-holdout-observation-ledger/v1`
- `event`: `admit`
- `measurement_head`
- `freeze_sha256`
- `protocol_sha256`
- `freeze_holdout_key`
- `freeze_candidate_id`
- `configuration_id`
- `cell_id`
- `records`
- `threads`
- `workload`
- `binary_sha256`
- `campaign_run_id`
- `run_relpath`
- `manifest_sha256`
- `mode`

`records`、`threads`、`workload` は key ではないが、同一 key の既存行と exact 一致を要求する。これは現在の freeze 座標の改変検出であり、T-525 の trial 共通束縛ではない。`mode` も key 外なので pilot が消費した cell を後から official として再観測できない。brief の「pilot だから緩めない」をそのまま反映する。

台帳 path は P4 の `output/s8b-holdout-observations/ledger.jsonl` を採る。ただし次を明確化する。

- `out_root`、`--resume` path、環境変数からは変更できない。`layout.repo_output_root()` (`layout.py:40-46`) を基準に固定解決し、既存 durable-root capability (`layout.py:55-79,121-165`) を使う。
- exclusive-create は「各行」ではなく、ledger file の初回作成に対する `O_CREAT|O_EXCL` である。
- 既存 file への更新は `O_APPEND|O_NOFOLLOW` と exclusive `flock` を使う。
- 初回作成競合で一方が `FileExistsError` になった場合は、既存 file を通常 append 経路で開き直して全行を検査する。truncate や上書きへフォールバックしない。

同型実装として次を再利用する。

- 初回 `O_EXCL`、directory-fd、path rebound、write loop、file/dir fsync は `trial_registry.py:933-1087`。
- canonical JSONL、重複検査は `trial_registry.py:1499-1566`。
- committed history の strict-prefix 検査は `trial_registry.py:1569-1611`。
- `O_APPEND`、`flock`、lock 内全量 read、schema 検査、file/dir fsync は `trial_registry.py:1614-1677`。

これらの低位機構を新規 `orchestrator/append_only_jsonl.py` に抽出し、schema/一意性検査を callback として渡す。trial lifecycle の wrapper と例外理由は維持し、既存テスト `test_trial_registry.py:1661-1696,1699-1715` を無変更の期待値で通す。私有関数を campaign 間で直接 import したり、安全コードを別実装として複製したりしない。

fresh/resume の扱い:

1. fresh
   - manifest を durable に作り SHA を得た後 (`s8b_floor_campaign.py:4386-4395`)、`runner.run()` より前に全 12 行を append する。
   - 途中の行で失敗した場合、発行済み token mapping を呼び手へ返さず、measure callback は 0 回とする。
   - 既に書けた行は保守的に残す。同じ run の事前計測 resume だけが残り行を補完できる。

2. exact resume
   - 同じ key の行があり、`campaign_run_id`、`run_relpath`、`manifest_sha256`、cell 座標、binary SHA がすべて一致すれば、追記せず既存 durable row から新 process 用 token を再発行する。
   - key が同じで別 campaign run なら拒否する。
   - 行が欠けていても journal に `session-start` または `session` が一件もなければ、fresh の書込み途中 crash として不足行だけ append できる。
   - 一件でも `session-start` があれば不足行の後付けを拒否する。`session-start` は measure より先に fsync される (`s8b_floor_campaign.py:3385-3394,3425-3432`) ため、観測後の台帳 backfill を許さない。
   - 既存 forward-only skip (`s8b_floor_campaign.py:3629-3635`; test `test_s8b_floor_campaign.py:4262-4303`) はそのまま維持する。

発行順は必ず次とする。

authority 再導出 → ledger lock → 既存全行検査 → canonical row append → `fsync(file)` → `fsync(parent)` → lock 解放 → sealed admission 生成・登録 → runner へ渡す。

`os.write`、`fsync`、schema、history のいずれかが失敗した場合は admission を生成しない。一部行だけ durable になった場合も campaign 全体の token mapping は返さない。

保証範囲は `trial_registry.py:1569-1580,1691-1695` と同様、同一 canonical ledger を共有する process と同一 Git repository の committed historyまでである。独立 clone 間の全世界一回性は主張しない。ledger を未 commit のまま削除した事故は Git history では検出できないため、実走後に ledger を proof chain として commit する運用を新 D と `output/README.md` に明記する。

既存 manifest/result schema は変えない。固定 ledger path と、既存成果物が持つ freeze/protocol/manifest hash、run dir、cell_id を使って row を決定論的に join できるようにし、既存 artifact 期待値を変更しない。

## 5. 編集計画 (file:line)

1. 新規 `orchestrator/holdout_observation.py:1-EOF`
   - `MinimalHoldoutSignature`、H1/H2 の単一源、effective gflag parser、`HoldoutObservationAdmission`、private issuer、`assert_issued_holdout_observation` を追加する。
   - 入れない場合: calibrator が campaign 層を import するか、20/80 を重複 hardcode することになり、第三 producer の rr20/rr80 が無 admission で受理される。

2. 新規 `orchestrator/append_only_jsonl.py:1-EOF`
   - directory-fd、`O_EXCL` first-create、`O_APPEND`、`O_NOFOLLOW`、`flock`、全量 read、committed prefix、write loop、file/dir fsync を共通化する。
   - 入れない場合: concurrent fresh run、symlink、partial write、履歴書換えのいずれかで ledger の一回性値が信用できない。

3. `orchestrator/campaign/trial_registry.py:51-57`
   - H1/H2 の現在値を neutral leaf から射影し、`HOLDOUT_BINDINGS` と `HOLDOUT_WORKLOADS` の公開形を維持する。
   - 入れない場合: neutral classifier と 8c registry が別の holdout 集合へ drift するか、calibrator→campaign の層反転になる。8c の受理集合・出力値は変えない。

4. `orchestrator/campaign/trial_registry.py:1569-1677`
   - lifecycle 固有 schema/history callback を残し、低位 append primitive を新共通 helper へ委譲する。
   - 入れない場合: 同型の lock/fsync 実装が二重化し、一方だけ修正される proof-chain 分岐が残る。lifecycle 行と理由コードは変えない。

5. `orchestrator/calibrator/runner.py:392-421`
   - `run_once` に keyword-only `holdout_observation_admission=None` を追加し、tempdir/subprocess より前に effective gflags と token を検査する。
   - 入れない場合: `backoff_overthrottle.py:92` 型の direct caller と将来の第三 producer が rr20/rr80 を無 admission で観測できる。

6. `orchestrator/calibrator/runner.py:455-534`
   - `measure_point` に同じ opt-in kwarg を追加し、指定時だけ `run_once` へ転送する。未指定時は既存 monkeypatch call shape を維持する。
   - 入れない場合: floor の既定 closure が正当な token を下位 gate へ渡せず、全 holdout rep が拒否される。

7. 新規 `orchestrator/campaign/s8b_holdout_admission.py:1-EOF`
   - 固定 protocol/freeze の HEAD blob 検証、cell 再導出、ledger key/row 検査、fresh/resume 規則、全セル token 発行を所有する。
   - 入れない場合: sealed token に人間凍結 artifact と durable 一回性の発行根拠がなく、ledger row と floor 値を結べない。

8. `orchestrator/campaign/s8b_floor_campaign.py:4184-4199`
   - `VerifiedFreeze`、cells、freeze/protocol hash を admission adapter へ渡す。caller workload を authority にしない。
   - 入れない場合: freeze 外から組み立てた同形 workload が freeze 由来 cell として誤受理される。

9. `orchestrator/campaign/s8b_floor_campaign.py:4386-4395,4404-4497`
   - fresh/resume の manifest SHA と検証済み journal が揃った直後に全セル admission を取得する。finalize-pending も既存 row が無ければ拒否する。
   - 入れない場合: manifest/run と ledger row の対応値が欠けるか、観測後 resume で台帳を後付けできる。

10. `orchestrator/campaign/s8b_floor_campaign.py:3230-3269,3569-3589`
    - `_Runner` に admission mapping を必須化し、全 cell の exact token を実走前に検査する。
    - 入れない場合: cell の token 欠落・交換が runner 起動時に受理される。

11. `orchestrator/campaign/s8b_floor_campaign.py:3425-3432,4524-4566`
    - 外部四引数 `measure_fn` を admission-aware 内部 wrapper で包み、各 callback 直前に再検査する。既定 closure は token を `measure_point` へ転送する。
    - 入れない場合: injected `measure_fn` が lower gate を通らず throughput を result に入れられる。

12. `orchestrator/campaign/s8b_floor_campaign.py:4960-4968,5109-5117`
    - production CLI の protocol path を固定 canonical artifact に限定する。ledger root は `out_root` ではなく `repo_output_root()` から取る。
    - 入れない場合: 別 protocol hash または別 output root で key/ledger をリセットできる。

13. `output/README.md:20-40`
    - `s8b-holdout-observations/`、固定 ledger、commit 前提、clone 間保証外を inventory に追加する。
    - 入れない場合: proof-chain の参照先と保証範囲が文書上存在しない。

14. `docs/decisions.md:17326` の後
    - 現 HEAD では次の空き番号 D414 として、共通実行 gateway、最小署名、pilot も消費する key、固定 authority、保証限界、却下案を記録する。
    - 入れない場合: 受理集合変更が D96 (`docs/decisions.md:4269-4297`) 違反となり、第三 producer が従う設計正本もない。

15. テスト
    - 新規ファイルは §7 の三本を追加し、既存 `test_s8b_floor_campaign.py:380-407` の helper には private canonical authority resolver の tmp 差替えだけを加える。
    - 入れない場合: gate、台帳、resume、注入 seam の各受理境界と事前登録変異の KILL 根拠がない。

## 6. 受理集合の変化

変わる受理集合:

1. `run_once`
   - before: 任意 gflags を admission なしで subprocess へ渡す。
   - after: effective `ycsb_rratio` が 20/80 の場合だけ、exact sealed admission が必須。欠落、caller 構築、別 cell、別 binary、座標不一致を subprocess 前に拒否する。

2. `measure_point`
   - before: rr20/rr80 を含む任意 workload を token なしで受理する。
   - after: rr20/rr80 は token を `run_once` まで伝播しなければ実測されない。非 holdout の既存呼出しは同じ引数と戻り値で受理される。

3. floor pilot
   - before: `validate_protocol` と freeze hash を通れば、一回性台帳なしで 12 セルを何度でも実走できる。
   - after: 固定 committed protocol/freeze と一致し、12 key を同一 fresh run に確保できる場合だけ実走する。二つ目の fresh run は拒否する。pilot も key を消費する。

4. floor injected `measure_fn`
   - before: callback が直接値を返せば `measure_point` を通らない。
   - after: callback 呼出し自体が exact cell admission を必要とする。

5. protocol
   - before: validator が許す別 master_seed 等の protocol を `--protocol` で渡せる (`s8b_floor_campaign.py:556-570,4964-4968`)。
   - after: holdout 観測 authority としては固定 committed artifact の exact bytes だけを受理する。

変わらない受理集合:

- rr5、rr50、rr95、rr100 等、effective ratio が 20/80 でない `run_once`/`measure_point`。gate は token 未指定時に追加 kwarg を下流へ送らないため、既存 monkeypatch seam も維持する。境界 anchor は `test_calibrator.py:352-390,445-472`。
- `pegasus_floor_scoping` の現在の rr5/rr50、`between_run_floor` の rr5/rr50/rr95、`backoff_overthrottle` の rr5/rr95。
- `s8b_freeze_io.load_verified_freeze` の bytes/hash/parse 受理集合。loader に admission 副作用を加えない。
- 8c の `admit_unregistered_exploratory`。rr20/rr80 の拒否 (`trial_registry.py:1245-1266`) と通常 workload の許可を維持する。
- 8c の `admit_registered_launch`、reason code、非 certifying 値、lifecycle row schema。
- official mode の無条件拒否 (`s8b_floor_campaign.py:314-324,5099-5106`)。新 admission は official 解禁 capability ではない。
- floor の manifest/result/session 数、throughput、CV、run_cmd 等の既存 artifact schema と期待値。

D96 の同時更新対象:

- 新しい主境界: `orchestrator/tests/test_holdout_observation.py` の rr20/rr80 token 必須と非 holdout passthrough。
- floor artifact 境界: `orchestrator/tests/test_s8b_floor_campaign.py:619-686` の既存成功形を維持しつつ、注入 callback の token 必須を追加する。
- resume 境界: `test_s8b_floor_campaign.py:4262-4303` に、exact row 再利用と観測後 backfill 拒否を追加する。
- 不変な 8c 境界: `test_trial_registry.py:1159-1191,1194-1215` を既存期待値のまま通し、neutral table への抽出で U4 が変わらないことを固定する。
- 新 D とこれらの境界テストを同一 commit に含める。既存期待値の書換えで新挙動へ合わせることはしない。

## 7. テスト計画

1. 新規 `orchestrator/tests/test_holdout_observation.py`
   - rr20、rr80 を token なしで direct `run_once` へ渡し、fake subprocess が 0 回であることを検査する。殺す誤実装: gate を `measure_point` だけに置く。
   - rr5、rr50、rr95、rr100 が従来どおり fake subprocess へ到達する。殺す誤実装: 全 YCSB workload を過剰拒否する。
   - duplicate gflag の最終値で分類する。殺す誤実装: first-wins、any-match、dict 化時の順序喪失。
   - caller 構築 token、別 ratio、別 records/threads、別 binary SHA を拒否する。殺す誤実装: `_seal` だけ見て payload を照合しない。
   - `measure_point` が token 指定時だけ `run_once` へ転送し、未指定の非 holdout call shape を変えない。殺す誤実装: 全既存 monkeypatch へ新 kwarg を強制する。

2. 新規 `orchestrator/tests/test_append_only_jsonl.py`
   - 初回だけ `O_EXCL`、以後 `O_APPEND`、exclusive `flock`、file/dir の二回 fsync を観測する。殺す誤実装: truncate、lock 外 check、directory fsync 欠落。
   - symlink、非 regular file、path rebound、途中改変、非 canonical JSON、末尾 newline 欠落、duplicate key、truncated row を拒否する。殺す誤実装: parse 成功だけで append する。
   - committed version の削除、縮小、非 prefix 書換えを拒否する。殺す誤実装: HEAD blob だけ比較して履歴を見ない。
   - 二 process 相当の first-create 競合で一方だけが新 run を確保する。殺す誤実装: check-then-create race。

3. 新規 `orchestrator/tests/test_s8b_holdout_admission.py`
   - 実 schema と同形の固定 protocol/freeze から 12 key、12 行だけを発行する。殺す誤実装: session ごとに 96 行発行する。
   - rr20/rr80 と H1/H2、freeze map key、trial workload 名を別 field として照合する。殺す誤実装: 同名文字列を一つの曖昧な `holdout_id` として扱う。
   - 別の valid master_seed を持つ protocol、未 committed bytes、別 freeze path/hash を拒否する。殺す誤実装: `validate_protocol` 通過だけを authority にする。
   - protocol に存在しない `confirm_user_freeze` を要求しない一方、固定 raw bytes を要求する。殺す誤実装: CLI flag の記憶を artifact field と誤認する。
   - 同一 key の別 fresh run を拒否し、同一 run/manifest の resume は行数を増やさない。殺す誤実装: resume のたびに二重消費する。
   - ledger 書込み途中 crash の事前計測 resume は不足行だけ補い、`session-start` 後の不足行は拒否する。殺す誤実装: 観測後 backfill。
   - write/fsync 失敗で token 発行数 0、measure callback 0 を検査する。殺す誤実装: token を先に構築する。

4. `orchestrator/tests/test_s8b_floor_campaign.py`
   - helper (`380-407`) に tmp の固定 authority/ledger resolver を patch するが、既存 result/manifest の期待値は変えない。
   - injected `measure_fn` が admission-aware wrapper を通ることを追加する。
   - default closure tests (`3365-3428`) に token が `measure_point` へ渡ることだけ追加し、clocks/NUMA/perf の既存期待値は維持する。
   - forward-only resume (`4262-4303`) に ledger 行数 12 の不変と再発行を追加する。
   - freeze hash mismatch (`3354-3362`) が ledger 作成前に落ちることを維持する。

5. `orchestrator/tests/test_trial_registry.py`
   - `HOLDOUT_WORKLOADS == {"rr80","rr20"}` (`1159-1163`) を維持する。
   - exploratory holdout 拒否 (`1180-1191`) と non-holdout admission (`1194-1215`) の期待値を変えない。
   - lifecycle lock/fsync (`1661-1696`) と canonical rejection (`1699-1715`) を共通 helper 抽出後も同じ期待値で通す。

read-only sandbox のため、ここでは pytest、checker、変異 harness は実行していない。上記は静的テスト計画であり、緑とは報告しない。

## 8. 事前登録変異の候補

以下の old は段4で実装する予定の逐語で登録する。

1. 最小署名の片側欠落
   - 位置: `orchestrator/holdout_observation.py::classify_minimal_holdout_signature`
   - old: `return rratio in HOLDOUT_RRATIOS`
   - mutation: `return rratio == "80"`
   - 期待 KILL: token なし rr20 が fake subprocess へ到達する。
   - 前層は direct `run_once` 入力なので拒否しない。後層は成功する fake subprocess であり拒否しない。rr20 を止めるのはこの classifier と gate の組だけである。

2. `run_once` gate の除去
   - 位置: `orchestrator/calibrator/runner.py:409` の直前
   - old: `assert_holdout_observation_admitted(binary=binary, gflags=gflags, admission=holdout_observation_admission)`
   - mutation: `pass`
   - 期待 KILL: direct `run_once` rr80、token なしで subprocess spy が呼ばれる。
   - 前に `measure_point` を置かない direct test とする。後の fake subprocess は同じ入力を拒否しない。

3. floor 注入 seam の直前検査除去
   - 位置: `orchestrator/campaign/s8b_floor_campaign.py::_invoke_admitted_measurement`
   - old: `assert_issued_holdout_observation(admission, expected_cell=cell)`
   - mutation: `pass`
   - 期待 KILL: forged token と injected callback の直接 unit testで callback が呼ばれる。
   - `_validate_live_admissions` を通さない局所 gateway test とし、前層の重複拒否を避ける。後層 callback は常に ScalePoint を返し、`run_once` も呼ばない。

4. key から configuration を脱落
   - 位置: `orchestrator/campaign/s8b_holdout_admission.py::_ledger_key`
   - old: `return (freeze_sha256, protocol_sha256, freeze_holdout_key, configuration_id)`
   - mutation: `return (freeze_sha256, protocol_sha256, freeze_holdout_key)`
   - 期待 KILL: 同じ holdout の異なる二 configuration が衝突し、12 行を発行できない。
   - 両 cell は authority 検査を通る。後層 token 検査も各 cell が発行されれば通るため、衝突の証拠は key 層だけに属する。

5. 観測後 resume の backfill 許可
   - 位置: `orchestrator/campaign/s8b_holdout_admission.py::admit_floor_holdout_observations`
   - old: `if measurement_started and existing is None:`
   - mutation: `if False and measurement_started and existing is None:`
   - 期待 KILL: `session-start` がある journal と欠損 ledger row の組が append/token 発行される。
   - manifest、protocol、freeze、既存行はすべて正当な fixture にする。後層 callback は許容するため、別 gate による KILL の取り違えがない。

6. durable-before-issue の fsync 除去
   - 位置: `orchestrator/append_only_jsonl.py::locked_append_canonical_jsonl`
   - old: `os.fsync(fd)`
   - mutation: `pass`
   - 期待 KILL: file と directory の二 fsync を観測するテストが一回しか記録せず失敗する。併せて durable receipt が返る条件を検査する。
   - 前層 schema/authority は正常入力で通す。後層は helper の durable receipt をそのまま受けるだけで、同じ欠陥を別理由で拒否しない。

## 9. 親 brief の誤り (あれば file:line 付きで)

1. `brief.md:18-19` の「実測の最下層は measure_point」は誤り。
   - `measure_point` は `run_once` を呼ぶ (`runner.py:519-534`)。
   - subprocess effect は `run_once` (`runner.py:409-421`)。
   - production に direct `run_once` caller がある (`backoff_overthrottle.py:92`)。
   - よって P1 (`brief.md:71-77`) の gate 位置は一段上すぎる。

2. P1 は floor の injectable `measure_fn` を閉じない。
   - seam は `brief.md:19` の既定 closure だけを前提にしているが、public API は `s8b_floor_campaign.py:4052-4093` で任意 callback を受け、実呼出しは `3425-3432`。
   - lower gate と floor callback gateway の両方が必要である。

3. P2 (`brief.md:78-81`) は CLI 手続と persisted artifact を混同している。
   - `--confirm-user-freeze` は `s8b_floor_campaign.py:718-736` の手続だけで、protocol field にはならない。
   - protocol 実 field は `floor_protocol.json:1` と builder `s8b_floor_campaign.py:607-629` の集合だけである。
   - authority は fixed committed bytes とその hash に修正すべきである。

4. I6 の二文 (`brief.md:51`) と P1 の層反転回避 (`brief.md:75`) は、そのままでは同時充足できない。
   - 現在の 20/80 単一源は `trial_registry.py:51-57`。
   - calibrator がこれを import すれば層反転、neutral module に複製すれば単一源破壊、neutral module へ移して trial_registry から射影すれば「trial_registry を触らない」に反する。
   - 推奨裁定は I6 を「8c の受理集合と artifact を変えない。意味不変の単一源抽出は許す」と狭めること。文字どおり file edit 禁止を維持するなら、第三 producer まで閉じる P1 系設計は実装不能であり、段4へ進めない。

5. P3 (`brief.md:82-85`) の `holdout_id` は二義的である。
   - floor では freeze map key (`s8b_floor_contract.py:352-358`)。
   - trial registry では workload 名 (`trial_registry.py:51-57`)。
   - key field を `freeze_holdout_key` に改名し、`trial_workload_name` と分離すべきである。tuple の単位自体は採用できる。

6. P4 (`brief.md:86-87`) の「append-only、exclusive-create」は解釈が不足している。
   - file 初回作成は `O_EXCL`、二行目以降は `O_APPEND` でなければ resume と追記を両立できない。
   - path は採用するが、I/O セマンティクスを §4 の形で確定する。

7. P5 (`brief.md:88-89`) は概ね妥当。
   - neutral signature、runner gate、floor token、ledger、D96 テストが相互依存するため、意味上は一つの実装単位とする。
   - ただし I6 の裁定が得られるまでは着手不可である。
```

## 総括

`measure_point` 単独では direct `run_once` と floor の注入 callback を塞げないため、共通 gate は `run_once`、floor artifact gate は callback 直前に置く。  
一回性は freeze/protocol/hash/セル/構成の12 keyで管理し、全行の durable append 後にだけ sealed token を発行する。  
`--confirm-user-freeze` は protocol field ではないため、authority は固定された HEAD の protocol/freeze bytes とする。  
最大の事前裁定事項は、8c の受理集合を維持したまま `trial_registry.py:51-57` を neutral 単一源へ射影する編集を I6 が許すかである。  
本回答は静的調査に基づくプランであり、実装・pytest・変異実行は行っていない。