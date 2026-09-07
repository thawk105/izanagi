## 所見

### 所見 1 — 受信値が送信値に束縛されず、値の入替えでも緑になりうる

- 主張: 現計画は 3 変数の存在と値の形を検査するだけで、投入側が生成した値との exact 一致を検査しない。承認あり側は先頭 2 値が同一なので入替えを識別できず、承認なし側も 2 本の hex を入れ替えて配送されても両方 regex を通る。`explicit_env_order` は job 側の定数であり、配送順の観測ではない。
- 根拠: `s2-plan.md:47-53,77,89-133`
- これが放置されると成果物の何が変わるか: `ok=true` でも「3 本が送った値のまま届いた」「名前と値の対応が保たれた」とは言えず、本 wave の中心成果が存在確認へ弱まる。
- 提案: 各 evidence directory に create-only の `expected-env.json` を置き、投入側の ordered `(name,value)` から `-v` と期待資料を同時生成する。job は 3 値すべてを exact 比較する。順序は job env から観測できないため「投入 argv に記録された順序」と明記し、到着側の観測とは分ける。

### 所見 2 — 固有 sentinel では承認 env 自身の ambient 継承を証明できない

- 主張: plan は両 request で `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` を unset し、別名の `T1259_NQSV_AMBIENT_SENTINEL` だけを ambient に置く。一般変数が継承されても `IZANAGI_` 名が個別に除外される可能性は残り、brief が問題にする承認 env の漏洩を直接測っていない。
- 根拠: `s1-brief.md:14-16,65-66`; `s2-plan.md:107-124,135-159`
- これが放置されると成果物の何が変わるか: probe が緑でも「承認 env が投入 shell から届きうるか」は未確定のままになる。これは本題の欠測である。
- 提案: probe job だけを対象に、`-v` へ承認変数を載せず、投入 subshell で exact 名を ambient に置く条件を追加する。真に unset の負対照も残すため、明示承認、ambient-only、完全 unset の 3 request が妥当である。ambient-only は mismatch 値でも配送可否を測れ、official shell と承認あり driver は起動しない。

また、現 subshell は `IZANAGI_SUBMISSION_NONCE` と `IZANAGI_FLOOR_JOB_EVIDENCE_ROOT` を unset していない。同名の親環境と `-v` の優先順位が混ざるため、意図的な ambient 対象以外の全 target 名を先に unset すべきである。新規 2 名の repo 検索は双方 0 hit であり、固有名衝突自体は認めなかった。

### 所見 3 — ambient 継承があっても `submit_floor.sh` の引数 guard は迂回されない

- 主張: `submit_floor.sh` の実投入 guard は shell 内部の `CONFIRM_OFFICIAL_FLOOR_RUN` を見る。これは既定 0 で、CLI 引数だけが 1 にする。ambient の `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` は guard 判定に使われず、引数なしなら `qsub` より前に停止する。
- 根拠: `submit_floor.sh:33,44-46,84-87,632-650`; `verbatim-t2324-insight.md:74-84,140-145`; `docs/pegasus-runbook.md:1647-1650`
- これが放置されると成果物の何が変わるか: brief の「ambient 継承が承認束縛の前提そのものを崩す」という一般化から、D926 の標準経路保証を不当に弱める結論へ進みうる。
- 提案: 結果が ambient present でも「標準 submitter の引数必須性は不変」と記す。影響するのは raw `qsub` の非標準経路で、これは現 runbook でも D926 の保証外である。ambient absent の場合にも guard、§8、driver gate を緩めないこと。現 plan に緩和変更は混入していない。

### 所見 4 — T-2228 の「2 本目到達済み」は投影資料だけでは成立しない

- 主張: T-2228 PBS にある 2 変数の `qsub -v` はコメント上の例である。evidence path の必須検査と、その先に成果物があることは値の存在を示すが、ambient 継承が未確定な状況では「2 番目の `-v` field が運んだ」とは識別できない。
- 根拠: `s1-brief.md:41-46,55-56`; `s2-plan.md:9`; `t2228_driver_gate_liveness_probe.pbs:7-12,100-115`
- これが放置されると成果物の何が変わるか: 過去 request の送信 argv と受信値を結ぶ一次証拠がないまま、既存実測として固定される。
- 提案: P1-a の根拠は「未検証の間接証拠」へ降格する。専用の 2-field request は不要だが、それは新 probe の 3-field 条件が 2 本目も exact 再観測するためであり、T-2228 が既に証明したためではない。

### 所見 5 — P1-b は成立するが、P1-e の副作用ゼロは条件付きである

- 主張: P1-b は正しい。`floor_campaign.sh` は実 driver argv より前に repo 内 attempt directory を作り、build と protocol 解決を行うため、承認あり argv の実観測に利用できない。P1-e については、`main()` の control flow は parser 後すぐ rc=2 を返し、protocol loader、`run_campaign()`、`take_checkpoint_environment()` へ到達しない。
- 根拠: `floor_campaign.sh:267-365,547-566,1002-1139,1172-1228`; `s8b_floor_campaign.py:7259-7261,8396-8413,8606-8622`; `s2-plan.md:171-184`
- これが放置されると成果物の何が変わるか: P1-e を「CLI main の state-mutating path は未到達」より広い「process は何も書かない」と報告すると、根拠を超える。
- 提案: P1-e は control-flow 上支持する。ただし成果物では、確認した範囲を main の早期拒否と前後 snapshot に限定する。

未検証の疑い: `main()` より前に多数の production module import が走るため、投影された 1 file だけでは import closure 全体の外部副作用を証明できない。`-B` は `__pycache__` を防ぐが、それ以外の import-time write は一般には防がない。根拠は `s8b_floor_campaign.py:54-76,81-164`。

### 所見 6 — repo 外 write の列挙は core dump と Git の副作用を閉じていない

- 主張: plan の列挙は通常終了時の file を概ね含むが、作成される親 directory、core dump、Git の optional index refresh が閉じていない。PBS 側は T-2228 の Git selector unset を踏襲するだけで、`GIT_OPTIONAL_LOCKS=0` は計算ノード driver の Git helper にしか記載されていない。
- 根拠: `s2-plan.md:32-37,46,186-210`; `t2228_driver_gate_liveness_probe.pbs:17-21,38-43,73-87,117-143`; `t2228_driver_gate_liveness_probe.py:108-145`
- これが放置されると成果物の何が変わるか: `git status` が `.git/index` または lock を更新したり、異常終了時の core が cwd に作られたりして、「repo へ 1 byte も書かない」が破れる可能性がある。core の実際の配置は機体の `core_pattern` 次第なので、これは未検証の疑いである。
- 提案: PBS shell 自身でも Git optional locks を無効化し、Python 起動前に cwd を job 専用 scratch へ移し、core を無効化する。作成可能 path の一覧には attempt root とその親 directory、`expected-env.json`、scheduler logs、qsub captures、一時 result、final result、scratch、異常終了時の残留一時 file を含める。`-B` と外部 `-o/-e` は維持する。

### 所見 7 — 登録簿閉包に追加漏れは見つからなかった

- 主張: P1-c は支持する。新 probe 2 本は registry、`test_hooks.py` の 2 golden、runbook 投影を同期する必要があり、新 test は self-run harness を持たせれば README 更新を避けられる。追加の literal closed set は見つからなかった。
- 根拠: `test_hooks.py:3032-3104,3926-3937,4360-4386`; `docs/pegasus-runbook.md:484-487`; `test_plain_runner_coverage.py:44-86`
- これが放置されると成果物の何が変わるか: registry なしでは execution inventory が赤になり、golden または runbook を欠けば同期検査が赤になる。self-run を欠けば新 test 自身が meta-test で赤になる。
- 提案: plan の 6 file を維持する。追加の台帳や一般化した gate は不要。

実行した検索と件数は次のとおり。

```bash
rg -n --hidden -g '!.git/**' -F \
  't2228_driver_gate_liveness_probe' . | wc -l
# 251 line

rg -n --hidden -g '!.git/**' -F \
  't2228_driver_gate_liveness_probe' . |
  cut -d: -f1 | sort -u | wc -l
# 17 file
```

```bash
rg -n --hidden -g '!.git/**' \
  -e '_PEGASUS_EXPECTED_CLASSES' \
  -e '_PEGASUS_EXPECTED_ENTRIES' \
  -e 'test_bash_pegasus_execution_inventory_is_synchronized' \
  -e '_ADMISSION_PROJECTION_HEADER' \
  -e '_check_admission_projection' \
  -e 'PYTEST_ONLY_ALLOWLIST' \
  -e 'test_every_test_file_is_self_runnable_or_allowlisted' . | wc -l
# 126 line

# 同条件の rg -l
# 93 file
```

履歴、output、paper-story、`.claude` を除いた検索は 23 hit だった。そのうち duration ledger 2 hit と `docs/failures.md` 1 hit は enforcement ではなく、実効面は plan 記載どおり 20 hit である。さらに `admission_registry.json|execution_inventory|PYTEST_ONLY_ALLOWLIST|_ADMISSION_PROJECTION_HEADER` の広い検索は 44 hit。追加 entry を要求する closed set は上記以外になかった。

### 所見 8 — probe が緑でも official 投入との同一性は証明されない

- 主張: 承認あり request の名前、値の形、並びは `submit_floor.sh` の最大 3-field 構成を模しているが、実 submitter を通らず raw `qsub` を直接呼ぶ。job 側 §8 も実 shell の実行ではなく複製した純粋関数による射影である。
- 根拠: `s2-plan.md:79-133,161-169`; `submit_floor.sh:607-650`; `floor_campaign.sh:547-566,1216-1225`
- これが放置されると成果物の何が変わるか: 緑を次の事項の証拠に誤拡張しうる。

  - `submit_floor.sh` を通った production request でも同じ env になること
  - `floor_campaign.sh` §8 が実際にその分岐を取ったこと
  - shell が生成した実 driver argv
  - 異なる変数順、個数、長さ、空文字、comma・空白を含む値
  - 別時刻、別 node、別 queue、将来の NQSV 構成
  - transient write、repo 外の import-time write
  - official 走行の承認または D926 の保証拡張

- 提案: 最終報告を「当該 request、当該時刻、当該 3-field argv と値形での raw qsub 到達」に限定する。四分岐の複製を新しい correctness gate と扱わず、実測値への source projection と明記する。empty/mismatch など未実測枝の一般化した検査は、本題に必要な最小限を超えるなら削る。

### 所見 9 — production nonce 名の使用は必要だが、証拠の権威区分が必要

- 主張: probe は `IZANAGI_SUBMISSION_NONCE` と同名を使うが、`floor_campaign.sh` を起動せず、production submission receipt や `output/.../submissions/<nonce>` を作らないため、現計画上の実 path 衝突はない。128-bit nonce の偶然衝突も実務上無視できる。技術的な新 bypass も作っていない。
- 根拠: `s2-plan.md:64-75,112-125,186-210`; `floor_campaign.sh:41-77,568-620`; `submit_floor.sh:310-327,693-723`
- これが放置されると成果物の何が変わるか: 外部 evidence の nonce を production receipt と誤認したり、raw approval の例を sanctioned official 投入と誤読する余地が残る。
- 提案: 測定対象なので env 名は変更しない。一方、result に `authority="diagnostic-only"`、probe schema、probe job script path/hash、`official_campaign_executed=false` を明示し、production receipt namespace へ何も書かない。承認あり条件では実 driver を起動しないという plan の制約を維持する。

## 総括

**NO-GO。** 最も重い所見は所見 1 である。現 plan は受信した 2 本の hex を投入値へ exact 束縛しないため、値の入替えや別値への置換でも緑になりうる。加えて、所見 2 により承認 env 自身の ambient 継承という中心 estimand が未測定である。

P1 の判定は次のとおり。

| P1 | 判定 |
|---|---|
| P1-a | 根拠は不成立。ただし新 3-field probe が 2 本目も再測定するため、専用 request は不要 |
| P1-b | 支持 |
| P1-c | 支持。6 file で閉じる |
| P1-d | 固有名衝突回避は支持するが、承認 env 漏洩の測定としては不十分 |
| P1-e | CLI control flow は支持。process 全体の副作用ゼロは条件付き |

expected 値への exact 束縛、承認 env exact 名の ambient-only 条件、Git/core/cwd の write 閉包を計画へ戻せば GO にできる。コード変更、file 編集、test、commit、job 投入は行っていない。