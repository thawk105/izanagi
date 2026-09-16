# 段 3 敵対相談 B (整合と実効性) — [T-1328]

指定の必読 5 件を確認した。以下は静的検査のみ。編集・テスト・計算ノード実走は行っていない。`plan.md`、`brief.md` は指定された段資料、それ以外は repo root 起点。

## real 所見

### 1. 測定停止は解消するが、認定較正取得の停止は解消しない

**file:line:** `plan.md:25,82-86,145`、`orchestrator/calibrator/report.py:106-123`、`orchestrator/calibrator/cli.py:1017-1040`、`tools/pegasus/certify_calibration.sh:955-988`

他の検査と全 sweep が成功した場合でも、提案経路の終端は以下になる。

1. wrapper が acquisition receipt を生成する（`certify_calibration.sh:846-848`）。
2. canonical unavailable receipt から no-perf を選び、sweep の throughput を取得する。
3. 飽和選択と noise は成立させない。品質判定は少なくとも `required-metrics-missing`、`selection-invalid`、`within-run-cv-invalid` を返す（`report.py:106-123`）。
4. CLI は `calibration.json`、`calibration.md`、`window-probes.json` を保存し、rc=1。登録処理には到達しない（`cli.py:1021-1040`）。
5. wrapper は成功時専用 post probe を省き、`job-result.json` に `calibrate_rc=1`、failure に `stage=calibrate` を残して rc=1（`certify_calibration.sh:960-988`）。

したがって、分割には測定値保存という実体がある。しかし「認定較正取得が perf 不在で止まる」という実害は残る。登録済み較正への橋渡しはない。

予約は引き続き 7200 秒（`tools/pegasus/policies/calibration_v1.json:5-6`）。実経過時間・課金が必ず 2 時間になるとは断定できないが、予約と build に加えて sweep を消費し、認証は必ず却下される。

**成果物への影響:** throughput を含む却下成果物は増えるが、`registered/` に認定較正は増えない。

**推奨是正:** 本 wave の達成範囲を「D352 に従う測定継続と証拠保存」と明記する。「認定較正取得の回復」「予約浪費の解消」を完了扱いにしない。認証条件の変更は本 scope に混ぜない。

### 2. shell テストの抽出範囲は、主張する calibrator 呼出しまで届かない

**file:line:** `plan.md:192-207`、`tools/pegasus/certify_calibration.sh:946-958`、`tools/pegasus/exec_calibrate.py:17-41`

プランが抽出する `857-953` は argv JSON の保存までである。実際の起動は `956` の `exec_calibrate.py`、その先の `os.execv` で行われる。したがって、この範囲だけでは「calibrate 呼出し到達」「probe_error で calibrate が呼ばれない」の実行証拠にならない。終端の job-result／failure も抽出範囲外である。

Python 側も、既存 `_invoke` の subprocess fixture は `nm` と `sha256sum` しか受け付けない（`test_calibrator_certify.py:401-406`）。実 `sweep.calibrate` を渡すだけでは bench 実行まで通らない。既存例の `sweep.measure_point` 差し替え（同 `149`）や `runner.run_once` 差し替え（同 `187`）を流用すると、それぞれ runner の変更や実 argv 生成を検証できなくなる。

**成果物への影響:** argv 保存と合成した却下 JSON だけで緑になり、実起動・no-perf command・wrapper の rc／job-result の不整合を見逃し得る。

**推奨是正:** 既存テストファイル内で、shell 抽出を実呼出しと終端まで含めるか、検証主張を「argv 生成」に限定する。Python は実 `cli.main → sweep.calibrate → runner.measure_point → runner.run_once` を通すと名指しし、fixture は subprocess 境界に置く。これは対応テストの具体化であり、新しい gate の追加ではない。

### 3. 「計算ノードでは no-perf を実走できない」は一般化しすぎている

**file:line:** `brief.md:94-96`、`tools/pegasus/certify_calibration.sh:127-161,882-905`、`orchestrator/calibrator/perf_preflight.py:100-103,121-148`

候補成功の観測は、故障注入した経路まで不可能にしない。

- **PATH 操作だけでは不足する。** wrapper は policy 候補を直接実行し、成功候補を PATH より前に置く。
- **候補と literal perf の両方を制御すれば発火できる。** 隔離した実験用 checkout で、policy の候補を存在しない絶対パスにし、PATH の literal perf を rc=2 の fixture にすれば、実 canonical probe が unavailable を返す。空候補配列は `certify_calibration.sh:149` の要素数検査に抵触するため、非空の失敗候補が必要。
- **probe 単体にも注入境界がある。** `probe_perf_availability(subprocess_runner=...)` が実装済み。ただし、これは wrapper 全体の実走とは別の証拠である。

通常 submit は dirty checkout を拒否する（`submit_certify.sh:110-112`、job 側 `certify_calibration.sh:221-225`）。したがって、稼働 checkout をその場で改変する方法ではなく、実験条件を記録した隔離環境が必要になる。

**成果物への影響:** 現状の brief は、選択した検証方法を技術的に唯一の方法として誤記している。

**推奨是正:** 「本 wave では計算ノードへの投入を行わず、fixture 検証を採用する」に訂正する。追加 job 投入を本相談から要求する必要はない。

## refuted (攻めたが成立しなかったもの)

### consumer が新しい成果物を一律に壊す、という疑い

| consumer／参照経路 | 静的確認 |
|---|---|
| `schema_v2.py:632-652` | counter null と saturation null を読める。`cli.py:756-760` が noise 未測定を空配列の既存形に変換する。rejected v2 の生成自体は可能。 |
| `collect_receipt.py:118-141,171-178` | acquisition／job-result を読み、rc は整数を要求するだけ。rc=1 を拒否しない。両 staging の manifest に追加 receipt を回収できる。 |
| `certified_writer_admission.py:167-175` → `env_attestation.py:1028-1041` → `calibration_verify.py:116-141` | helper を 2 段追っても新しい perf receipt の直接解釈はない。既存較正の読込み経路である。 |
| `env_contract.py:606-631` | **no-perf rejected 成果物を有効較正として使えない consumer。** content-addressed registered path と accepted を要求する。これは所見 1 の未解決点であり、読込み事故ではない。 |
| `qualification/identity.py:37-53` | calibration job の consumer ではない。参照する script は明示的に `t126_qualification.sh`。 |
| `submit_certify.sh:159-193,205-229` | submit 時の identity・予約・qsub 配線を所有する。compute の perf receipt を読む consumer ではなく、変更不要。 |

**成果物への影響:** 却下証拠の保存・回収は既存形で成立する。一方、登録・activation に利用できない点は残る。

### T126 と完全同形でないこと自体が誤り、という疑い

- 候補解決後の PATH で canonical probe を呼ぶ順序は、`t126_qualification.sh:649-670` と一致する。
- calibration が receipt を unavailable 時だけ CLI に渡す点は、既存 `None → True` 契約と perf 有り call shape 維持のためであり、独立した判定入口を増やさない。
- T126 は toolchain identity と perf observation を別途束縛する（`t126_qualification.sh:745-769,802-816`）。今回それを calibration schema へ移植しない判断は、degraded **accepted** を新設しない範囲では正当。ただし、T126 と同じ研究上の前進を得るとは言えない。

**成果物への影響:** D494 の候補解決方式は再利用できるが、T126 の degraded 受理まで実現した成果物にはならない。

### T141 も直すべき、という疑い

`tools/pegasus/t141_region_profile.sh:1451-1454` は `perf record` でサンプルを取得し、`1478-1479` は非空 `perf.data` を必須にする。後続は IP／source-line／region 集計（`1482-1487`）。throughput だけでは目的の地域別 profile が成立しないため、`900` の `fail 2 perf_select` を残す判断は正しい。

**成果物への影響:** perf のない「profile 完了」を作らず、目的の測定不能として終了する。

### 閉包更新がプランから全て漏れている、という疑い

- CLI・sweep の登録追加と runner guard 更新は `plan.md:101,175-179` に既にある。更新しなければ `test_official_perf_closure.py:908-915` が赤になる。対応する登録は `44-97`、runner の期待値は `448-449`。
- `test_hooks.py:3038,3139-3143` と `admission_registry.json:34-38` は既存 script を dispatch-required と登録済み。今回の分岐変更は分類を変えない。
- プランは既存テストファイルへの追加であり、新規ファイルによる自走 harness 漏れはない。
- 新規ファイルを作る場合、自走要件は `test_plain_runner_coverage.py:60-74`。所要台帳の実装上の検査は **全体の 90% 被覆**（`test_acceptance_schedule_order.py:704-713`）であり、「新規ファイルを一つ足せば台帳も必ず赤」は断定できない。

**成果物への影響:** 明示済み inventory 更新を実装すれば、今回必然となる未対応の dispatch 登録漏れは見つからなかった。

## 親 brief への不同意

- **P2／達成範囲:** acquisition receipt の生成は認証成功ではなく、提案経路は最終的に未登録・rc=1。認定較正取得の回復とは区別すべき。
- **実測方法:** `brief.md:95-96` の「唯一」は所見 3 のとおり撤回すべき。
- **identity の根拠:** `brief.md:82-83` の引用は対象違い。`qualification/identity.py:42-48` は T126 の committed blob と submission の一致も要求しており、「submission と job-result の相互一致だけ」でもない。calibration 自身の根拠は `certify_calibration.sh:221-259`。
- **既存 harness:** `test_pegasus_calibration_workload.py:606-630` は argv 代入の抽出であり、perf 選択から認証終端までの実走証拠ではない。

**成果物への影響:** brief の完了主張・検証範囲・identity 説明を訂正しないと、実際より強い保証を記録してしまう。

## 裁定パッケージ候補 (scope 外だが real)

**perf なしの取得を、正式系列で利用可能な較正として成立させるか。**

`analyze.py:48-57` は飽和点を選べず、`report.py:106-123` と `env_contract.py:606-631` は登録・利用への道を閉じる。これを変えるには、perf に依存しない較正が何を保証するかという新しい認証契約が必要。

**成果物への影響:** 裁定なしには throughput 証拠を正式な較正へ昇格できない。本 wave の分岐修正に紛れ込ませるべきではない。

## 総括

本案は perf 不在による測定前停止を解消し、throughput 証拠を残す。  
認定較正取得の停止と予約費用の問題は解消しない。  
最も重い未解決点は、全 sweep 後も必ず rejected・未登録となること。  
実装前に shell テストの到達範囲と、親の「実走不可能」という説明を訂正すべき。