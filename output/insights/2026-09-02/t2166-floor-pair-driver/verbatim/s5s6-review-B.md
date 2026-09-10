## 総括

静的 review の結論は要修正です。最重要は、任意の `probe_argv` で `/bin/false` 相当を指定すると競合検査を常に clear にできる点です。
calibration API の署名は一致しますが、`quality.status="rejected"` を受理し、逆に `attestation_mode="none"` の正規戻り値を必ず拒否します。テスト stub が両方を隠しています。
変異 12 件には対応テストがありますが、#2・#6 は単一理由ではなく、#4・#11 は変異の切り方によって SURVIVED します。
また、`source_commit`、spec の `site`、`protocol` は実効検査に使われず、finalizer も HMAC 実行順や terminal status を再検証しません。
pytest は実走しておらず、親が報告した 110 件緑を本 review で再確認したとは主張しません。

## 変異 12 件の表

|#|変異|赤にするテストの file:line|単一理由か|SURVIVED 予測|
|---:|---|---|---|---|
|1|未知 key 拒否を外す|`orchestrator/tests/test_floor_pair_driver.py:395`|はい。後段に未知 top-level key の拒否はない|なし|
|2|expected SHA-256 比較を外す|`orchestrator/tests/test_floor_pair_driver.py:412`|いいえ。入力が invalid JSON なので、hash gate 除去後も `orchestrator/campaign/floor_pair_driver.py:1032` の JSON parse で拒否される|なし。ただし KILLED の理由が「受理へ広がった」ことではなく例外種別の変化|
|3|spec と HEAD blob の byte 一致を外す|`orchestrator/tests/test_floor_pair_driver.py:421`|はい。追記 LF は JSON として有効で、後段に作業木 byte の同値検査はない|なし|
|4|calibration projection equality を外す|`orchestrator/tests/test_floor_pair_driver.py:499`|条件付き。テストが隔離するのは `threads` gate (`floor_pair_driver.py:986`) だけ。実 API は env_tag と clocks を既に `calibration_verify.py:121-129` で拒否し、workload gate はこのテストで未到達|`threads` または全 block 除去は KILLED。env_tag・clocks・workload の単独変異は SURVIVED|
|5|trace symbol 検査呼出しを外す|`orchestrator/tests/test_floor_pair_driver.py:819`|はい。`trace=false` は自己申告だけで、fixture binary の symbol 出力を拒否する別 gate はない|なし|
|6|live env_tag 一致検査を外す|`orchestrator/tests/test_floor_pair_driver.py:864`|いいえ。除去後は text fixture binary に対する実 `nm` が失敗し、`floor_pair_driver.py:1607-1627` の `binary_binding_failed` で止まる|なし。ただし live env gate 単独の測定防止を証明しない|
|7|非 complete session を無視する|`orchestrator/tests/test_floor_pair_driver.py:1019`|はい。書き換え後も raw 値と identity は完全なので、`floor_pair_driver.py:1921` だけが全体を未生成にする|なし|
|8|`upper >= 1` を 0.999 へ clamp|`orchestrator/tests/test_floor_pair_driver.py:1070`|はい。値域分岐は `floor_pair_driver.py:2085` の一箇所|なし|
|9|production identity 判定を外す|`orchestrator/tests/test_floor_pair_driver.py:1091`|はい。fake の raw 値は他の完備検査を通る|なし|
|10|`O_EXCL` を外す|`orchestrator/tests/test_floor_pair_driver.py:893`|はい。`_validate_output_path` は既存 regular file を拒否せず、衝突拒否は `floor_pair_driver.py:1383` だけ|なし|
|11|HMAC rank を固定順へ変える|`orchestrator/tests/test_floor_pair_driver.py:564`|条件付き。role 順は検査されるが、fixture は 1 pair・1 sample なので `floor_pair_driver.py:1132` の sample 順変異を観測できない。artifact の実記録順も検査されない|role 順または HMAC 全除去は KILLED。sample 順だけ固定、または実行側で plan を並べ替える変異は SURVIVED|
|12|`require_all_reps=False`|`orchestrator/tests/test_floor_pair_driver.py:611`|はい。adapter の実 keyword を直接検査している|なし|

#2 は有効な spec bytes と誤った expected hash を使う形へ再照準すべきです。#6 は trace 検査を実 `nm` 境界で成功させてから foreign env_tag を入れるべきです。#4 は実効的に単独な `threads` と `workload` を別変異にし、env_tag/clocks の冗長比較は証拠対象から外すべきです。#11 は複数 pair・複数 sample の golden 順と、recorded session ID の順序一致を追加する必要があります。

## 所見

1. **主張:** `probe_argv` が任意 command なので、競合検査を valid spec だけで無効化できます。
   **根拠:** loader は非空文字列列しか要求しません (`orchestrator/campaign/floor_pair_driver.py:620-622`)。その argv をそのまま実行し (`:1325-1333`)、pgrep 専用分類器へ渡します (`:1429-1437`)。分類器は rc=1 かつ空出力を「無競合」と解釈します (`orchestrator/calibrator/runner.py:327-341`, `:355-358`)。したがって `probe_argv=["/bin/false"]` は常に clear です。
   **影響:** 競合 process が存在しても session が complete となり、汚染 throughput から candidate floor が生成されます。受理集合が「正しい pgrep 観測」から「rc=1 を返す任意 command」へ広がります。
   **提案:** probe argv を spec の自由 field にせず、exact な pgrep argvまたは閉じた probe IDへ固定してください。少なくとも `/bin/false` の負例を追加してください。

2. **主張:** `load_verified_calibration` の戻り値契約を半分しか扱っておらず、required と none の受理集合が逆方向に壊れています。
   **根拠:** API は keyword-only の 6 引数を取り、`VerifiedCalibration.calibration` は Optional です (`orchestrator/campaign/calibration_verify.py:41-48`, `:81-89`)。mode=none は正常系として `calibration=None` を返します (`:144-157`)が、driver は常に拒否します (`orchestrator/campaign/floor_pair_driver.py:969-982`)。一方、v2 schema は `quality.status="rejected"` を有効値として許し (`orchestrator/calibrator/schema_v2.py:478-482`)、driver は quality を確認しません。既存 registry consumer は明示的に accepted を要求しています (`orchestrator/campaign/env_contract.py:629-631`)。テスト stub (`test_floor_pair_driver.py:218-230`, `:246-250`) は Optional と quality の双方を表現していません。
   **影響:** 正規の grandfathered linux-baremetal calibration は必ず拒否され、quality rejected の v2 calibration は値生成へ進めます。前者は受理集合を不必要に空にし、後者は不適格 calibration 由来の candidate floor を許します。
   **提案:** Pegasus required 専用なら parser から mode=none と OTHER を削り、`calibration.quality.status == "accepted"` を要求してください。OTHER も支援するなら legacy artifact の意味を読む既存経路を使い、実 `VerifiedCalibration` による結合テストを置いてください。

3. **主張:** `source_commit` と execution contract は provenance fieldとして存在しますが、実行を束縛しません。
   **根拠:** `source_commit` は 40 hex として parse・格納されるだけです (`floor_pair_driver.py:556-567`)。loader の HEAD (`:1073`)、実行時 HEAD (`:1736`)との比較がありません。execution contract と build receipt も tracked bytes/hash の確認だけです (`:953-967`)。summary は loaded HEAD を残しますが source commit と runtime HEAD を直接載せません (`:2091-2114`)。
   **影響:** 任意の 40 hex source commit、無関係な tracked execution-contract/build-receipt bytes、異なる runtime HEAD の組合せでも candidate floor を生成できます。spec hash を辿れば矛盾は発見できますが、生成自体は拒否されません。
   **提案:** `source_commit == loaded_head == runtime_head` が意図なら三者を gate にしてください。別 commit を許す設計なら、source commit が何の source を指すかを限定し、build receiptの該当 fieldと意味的に照合してください。

4. **主張:** performance 実行前の site 判定が fail-closed な evidence modeを使っていません。
   **根拠:** driver は `current_site()` を既定引数で呼びます (`floor_pair_driver.py:1369-1374`)。site policy は Pegasus 名の hostでも NQSV 証拠が取れなければ OTHER を返し得ます (`orchestrator/campaign/site_policy.py:42-45`, `:66-79`)。`require_evidence=True` の場合だけ同じ状態を PEGASUS_SUSPECT へ倒します (`:81-84`)。
   **影響:** NQSV 検出が壊れた Pegasus login nodeを OTHER と誤認し、対応する env_tag の specなら性能測定へ進めます。測定場所が変わり、floor 値の参照可能性が失われます。
   **提案:** `site_policy.current_site(require_evidence=True)` を使用し、PEGASUS_LOGIN/SUSPECT を出力確保前に拒否する負例を追加してください。

5. **主張:** finalizer は計画の集合を検査しますが、計画どおりの実行順と terminal/header の完全性を検査しません。
   **根拠:** session ID は Counter 一致だけです (`floor_pair_driver.py:1856-1877`)。`recorded_ids == planned_ids` は要求されません。terminal は event、window ID、件数だけで、`status=="complete"` を確認しません (`:1851-1854`, `:1893-1900`)。header も一部 fieldだけです (`:1840-1850`)。
   **影響:** HMAC 順を後から並べ替えた artifactや、terminal が incomplete と主張する artifactからも candidate floorを生成できます。純粋な並べ替えでは数値は同じでも、「ランダム化された順で実行した」という参照が失われます。
   **提案:** session recordを plan順で exact 一致させ、terminal status、headerの format・loaded/runtime HEAD・randomization fieldも再検証してください。

6. **主張:** 実行 command の PATH 解決が成果物へ束縛されず、障害の一部は構造化例外にもなりません。
   **根拠:** `git` は PATH から timeoutなしで起動され、起動時 `OSError` は `_git_show_head` / `_git_head` で捕捉されません (`floor_pair_driver.py:482-506`)。`nm` も PATH・timeoutなしです (`orchestrator/campaign/buildcache.py:3446-3459`)。runner は `extra_env` を親環境へ上書きするため (`orchestrator/calibrator/runner.py:650-654`)、spec の PATH が `numactl_argv` の解決先を変えられます (`:536-545`)。
   **影響:** 同じ spec hashでも PATHごとに別 commandを実行できます。欠落時、nm/probe/numactl は出力予約後の incomplete artifactとなり、git 欠落は裸の `FileNotFoundError` になります。
   **提案:** 出力予約前に commandを解決し、許可された absolute pathまたは実行体 digestを記録してください。git/nm に timeoutを設け、起動失敗を driver固有例外へ正規化してください。

7. **主張:** 3,395 行の大半は裁定に必要ですが、未使用 fieldと自由 command surfaceは D1453 の専用 driver境界を越えています。
   **根拠:** strict loader、3 role plan、HMAC、raw sink、前後 probe、exclusive writer、raw再計算、二つの統計 ID、証明限界は裁定に直接必要です。一方 `environment.site` は parse後に読まれず (`floor_pair_driver.py:597-604`)、`CellConfig.protocol` も格納後に使われません (`:702`)。`source_commit` も前述のとおり非実効です。`extra_env` と `probe_argv` は汎用 command launcher相当の自由度を持ちます。
   **影響:** 実行値が同じまま site/protocol/source claimだけ異なる specとplanを無数に作れます。成果物 identityに科学的意味を持たない自由度が混入します。
   **提案:** B-4で実際に固定・消費する fieldだけへ縮小してください。site/protocol/sourceを残す場合は実効 equalityと成果物再検証を実装し、probe argvは固定してください。

8. **主張:** 変異事前登録の単一理由性は #2、#6、#4、#11 について現状の証拠では成立しません。
   **根拠:** #2 は invalid JSON (`test_floor_pair_driver.py:412-419`)、#6 は trace検査を成立させない text binary (`:864-891`)です。#4 は threads不一致だけ (`:499-527`)、#11 は単一 sample/pair (`:564-580`)です。
   **影響:** mutation runが KILLED と表示されても、hash・env・calibration・HMAC のどの実効 gateが効いたか一意に帰属できません。workload equalityや sample orderingの変異は生存し得ます。
   **提案:** 表の再照準どおり入力を隔離し、#4と#11は変異対象を分割してください。

## 検査したが問題なしと判断した点

- `load_verified_calibration` の引数名、keyword-only性、`VerifiedCalibration.calibration` から `env_tag`、`threads`、`clocks_per_us`、`workload` を読む形自体は実 API と一致します。問題は Optional と quality の扱いです。
- `buildcache.assert_binary_sha256(path, expected)` は成功時 None、不正 expectedや読取失敗で `BinaryDigestError`、不一致でその subclass `BinaryDigestMismatch` です (`buildcache.py:598-611`)。driver の呼出し引数は一致します。
- `_assert_no_trace_symbols(binary, *, binary_fd=None)` の呼出しも一致し、nm 起動・rc・trace symbolはいずれも `RuntimeError` で fail-closedです (`buildcache.py:3437-3464`)。
- `runner.measure_point` の全指定引数名と位置引数は一致します (`runner.py:1057-1077`)。戻り値 `ScalePoint` には `records`、`threads`、`throughputs` が実在します (`orchestrator/calibrator/model.py:55-76`)。
- 実 raw sinkは、成功 repごとに `rep_returncodes`へ rc、`rep_timestamps`へ3 key、`rep_observations`へ `rep_index`、`returncode`、`counter_status`、`missing_perf_events`、`perf_raw`、`throughput` が入ります (`runner.py:1189-1218`)。driver が必要な部分を読む型は一致します。
- tokenless runner admissionは current registered calibration workloadの `ycsb_rratio="50"` では拒否されません。保護対象 rr20/rr80なら admissionが必要です (`orchestrator/holdout_observation.py:1194-1201`)。
- 競合分類の rc 解釈は共有 classifier と一致します。rc=1・空出力だけ clear、rc=0・非空は competitors、その他は `CompetingBenchProbeError` となり、driverは indeterminateへ倒します。
- pytest の通常収集には `pytest.ini:13` により新規 test fileが入ります。`test_plain_runner_coverage.py:44-46` の全 `test_*.py` 列挙にも追加され、同 test fileの `__main__` (`test_floor_pair_driver.py:1219-1221`) は静的 self-run predicateを満たします。README allowlist追加は不要です。
- xdist group markerはなく、real-repo resource registryにも登録されていません。全 testが `tmp_path` と process-local monkeypatchだけを使うため、ungrouped配置は妥当です。acceptance shardの node集合は110件分増え、duration ledgerでは未知 cost扱いになりますが、欠落自体は拒否されません。
- repository全 Pythonを走査する subprocess bytecode guardの対象には増えますが、新規 subprocess callは Python fileを子として起動しないため、同 checkerの追加登録は不要です。
- 新規 production moduleを列挙する既存の閉じた file inventory、lint設定、または既存 callerは静的検索で見つかりませんでした。`check_docs`への file登録も不要です。AI provenance監査では通常の実装面 `.py` として自動的に対象になります。