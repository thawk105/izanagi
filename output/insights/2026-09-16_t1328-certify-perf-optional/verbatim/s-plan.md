# 段 2 プラン — [T-1328]

## 前提の検算

必読 5 件はすべて読めた。以下は静的なソース確認であり、編集・テスト実行・計算ノード実測は行っていない。行番号は提示された repo root 起点。

**確認できた事項**

- `tools/pegasus/certify_calibration.sh:907-909` は候補全滅を理由に `write_failure 2 perf`、`exit 2` する。
- acquisition receipt は同ファイル `846-848` で先に生成される。ただし、CLI の acquisition 判定まで完了した意味ではない。CLI は `orchestrator/calibrator/cli.py:853-905` で binary・TSC・attestation・receipt を別途検査する。
- `sweep.py:102-113` と `235-246` は `use_perf` を渡さず、`runner.py:1086` の既定 `True` が使われる。
- 伝播だけでも不足する。`runner.py:1252-1267` は counter 欠損を fatal にし、`sweep.py:273-286` は飽和判定不能でも noise へ進む。
- `analyze.py:48-57` の全欠損結果は `records=0 / saturated=False`。これをそのまま v2 にすると `schema_v2.py:652` の `minimum=1` に違反する。
- D494 の先例は `t126_qualification.sh:649-670` に存在する。

**確認できなかった／訂正が必要な事項**

- 19 attempt・直近 3 attempt の perf 成功は親からの情報であり、本段では再検証していない。
- 親が挙げたテスト `1643` は qsub argv の期待値、`1792-1818` 付近は submitter の検査である。候補全滅まで到達する既存 fixture harness ではない。
- script 全体を実走する既存テストはあるが、`test_pegasus_calibration_workload.py:461-462` が明記するとおり、入力検査直後で意図的に停止する。
- 「perf 有りの受理集合が完全不変」は既存行だけでは無条件に証明できない。追加する canonical probe と従来 smoke は異なる command である。

## 変更プラン

推奨は、**no-perf でも既存の有限 sweep を実行し、throughput を保存する。飽和点に依存する noise は実行せず、認証は rejected のまま終了する案**。

### `tools/pegasus/certify_calibration.sh`

- **`907-931` → 候補選択と可用性判定を分離する。**
  - 候補全滅による即時終了を削除する。
  - `911-928` の selection JSON・symlink は候補通過時だけ実行する。
  - 通過時の最終 PATH は従来の `931` と同じにする。全滅時は perf symlink を作らず、選択済み Python の directory と元 PATH を使う。
  - この最終 PATH の下で、選択済み `CALIBRATE_PYTHON` を使って `probe_perf_availability` を一度呼ぶ。
  - receipt を attempt 内の `perf-preflight.json` に保存し、`use_perf_from_receipt` の結果だけから分岐する。probe_error は unavailable に変換せず失敗として残す。
  - 候補全滅でも PATH 上の literal perf が available なら perf 有り経路へ進む。

- **`945-946` 間 → unavailable の場合だけ receipt 引数を追加する。**

  ```bash
  if [[ "$USE_PERF" == 0 ]]; then
    calibrate_argv+=(--perf-preflight-json "$PERF_PREFLIGHT_RECEIPT")
  fi
  ```

  perf 有り時の calibrate argv は維持する。環境変数を独立した可用性判定にしない。

- **`955-988` → rc の意味は維持する。**
  - no-perf 認証の rc=1 を成功へ変換しない。
  - `job-result.json` と `failure.stage=calibrate` を既存経路で残す。
  - CLI 内の post attestation は実行するが、wrapper `960-963` の成功時専用 post probe を実行したとは報告しない。

### `orchestrator/calibrator/cli.py`

- **`157-163` → optional `--perf-preflight-json` を追加する。**
  - bool の `--no-perf` は追加しない。
  - `797-814` の CLI 検査で certify 用引数として扱う。

- **`851-855` 付近 → receipt 読込みと canonical 判定。**
  - 指定された receipt を `_strict_json_file` で読み、`use_perf_from_receipt` に渡す。
  - 未指定は既存の `None → True` 契約を使う。
  - 指定 receipt は CLI attempt にも保存し、成果物とともに回収できるようにする。再 probe はしない。

- **`959`、`980` → observation plan／receipt の `True` を同じ導出値へ置換する。**
  - rr20/rr80 では必須。`holdout_observation.py:945-947` が実走の perf mode と capability の一致を要求する。
  - 同ファイル `757-758` は既に bool の False を許すため、capability 実装の変更は不要。

- **`991-1003` → no-perf のときだけ `use_perf=False` を calibrate に渡す。**
  - perf 有りでは既存 call shape を維持する。

- **`1003-1014` 間 → no-perf の測定条件を既存 host／notes に記録する。**
  - 例：`host["perf"]="unavailable"`、notes に「counter 未取得、同じ perf 条件内でのみ比較、認証レコード数は選択不能」を記録する。
  - `env_tag=pegasus` 自体は変更しない。canonical receipt と測定条件を併記する。
  - `report.py:106-123` の認証条件は変更しない。

### `orchestrator/calibrator/sweep.py`

- **`150-169` → `calibrate` に既定 `use_perf=True` を追加する。**
- **`224-240` → 内部 `_measure` で False の場合だけ `measurement_kwargs["use_perf"]=False` を設定する。**
  - `run_sweep` の signature、`102-113` の kwargs、`258-265` の呼出しは変更不要。closure で全測定へ届けられる。
  - `require_all_reps=True` と `require_complete_metrics=True` は維持する。

- **`267-273` 間 → no-perf の結果を保存して return する。**
  - `find_saturation` の判定不能 notes を result に残す。
  - `result.saturation=None`、`noise_floor=None` のまま返す。
  - `273-277` の capability noise 遷移も実行しない。`records=0` は `holdout_observation.py:874-875` でも拒否される。
  - sweep の測定点は `result.sweep` に保持する。

### `orchestrator/calibrator/runner.py`

- **`1256-1260` → counter の必須検査だけを `if use_perf:` 内へ置く。**
  - throughput 検査 `1254-1255`、maxrss 検査 `1261-1262`、rep 失敗処理 `1184-1192` は維持する。
  - `require_complete_metrics=False` への一括切替はしない。
  - no-perf raw 値は既存 `716-724` の空 perf 入力／null raw 経路を使う。

これは**測定の完了条件を取得可能量に対応させる変更**であり、認証の counter 必須条件を削除する変更ではない。

### テスト

- `test_pegasus_calibration_workload.py:606-630` 周辺に、production shell の perf 選択から argv 記録までを抽出して実行する fixture helper と正負例を追加する。
- `test_calibrator_certify.py:133-192`、`379-428`、`775-782` を利用して、実際の sweep／runner を通す no-perf 測定・却下成果物の検査を追加する。
- `test_official_perf_closure.py:44-46` に CLI・sweep の追加面を登録し、`448-449` の runner guard inventory を実際の新条件へ更新する。

`analyze.py`、`report.py`、`schema_v2.py`、`perf_preflight.py`、`submit_certify.sh`、T126 本体は変更しない。

## 必ず答えるべき問い への回答

### 1. 配線の最小集合

wrapper だけでは perf を呼びに行く。証拠は `sweep.py:102-113 / 235-246` と `runner.py:1086`。

必要なのは次の集合である。

1. wrapper の候補解決後 probe と receipt 引渡し。
2. CLI の receipt 判定、calibrate への伝播、rr20/rr80 capability の一致。
3. `calibrate` closure から `measure_point` への伝播。
4. runner の counter 必須検査を perf 有り測定に限定。
5. no-perf sweep 後の noise 回避と `saturation=None`。
6. 測定条件の記録と対応テスト。

P1 の `run_sweep` まで引数を通す案より、**`calibrate` と `_measure` の closure だけを変更する案が小さい**。ただし P1 は runner の厳格検査・schema・capability への対応を欠いている。

### 2. perf 必須の判定の所在

- `analyze.py:48-57`：miss rate が全欠損なら飽和判定不能。
- `analyze.py:135-145`：L3 下限基準も `usable` にしか適用しない。RSS だけで救済できない。
- `report.py:32-44 / 79`：`records=0` を自動的に null にしない。
- `schema_v2.py:648-652`：null は許すが、非 null の records は正数必須。
- `report.py:106-123`：counter 欠損、selection 不成立、noise CV 不成立はそれぞれ rejection reason。
- `cli.py:1017 / 1033-1035`：理由があれば rejected、rc=1。
- `schema_v2.py:529-532`：null saturation／空 noise は accepted にできない。

したがって no-perf 成果物は、**正の records を持つ各 sweep 測定点と、選択結果 `saturation:null` を区別して保存する**。`quality.status` は `rejected`。取得した点の records を「認証されたレコード数」として主張しない。

### 3. no-perf 走の終わり方

差分規模は未編集の設計概算。テスト行数を除く。

| 案 | 主な変更箇所 | 概算規模 | 評価 |
|---|---|---:|---|
| sweep を実行し noise を省く | wrapper `907-946`、CLI、sweep `150-169 / 224-240 / 267-273`、runner `1256-1260` | production 4 file、約80–130行の追加・置換 | throughput を取得し、D352 の測定継続を満たす |
| acquisition 判定後に測定せず終える | wrapper 同箇所、CLI `905` 以後で post 検査・rejection 出力 | production 2 file、約60–100行の追加・置換 | 小さいが、perf 不在が測定停止理由として残る |

**前者を推奨する。** 後者は診断改善にはなるが、「動かない環境では perf なしで測定を進める」という D352 の是正としては不十分。

ただし、rejected JSON ができるだけなら目的達成とは言えない。推奨案は throughput 系列を実際に取得・保存することが条件である。認証された飽和レコード数を得る問題までは解決しない。

また、2時間は予約であって必ず全時間を消費する意味ではない。既定 sweep は `cli.py:145-150` と `sweep.py:135` より5点×3 rep。no-perf は既存 early stop が成立せず全5点を測る。時間上限と完走保証の不足は wrapper `783-800` に既に記録されており、本変更で完走を保証しない。

### 4. 受理集合の不変

**認証 predicate を不変に保つ箇所**は以下。

- rep 成功・throughput・maxrss：`runner.py:1184-1192 / 1252-1267`。perf=True のとき同じ counter 検査を実行する。
- 認証品質：`report.py:87-129` 全体を無変更。
- v2 accepted 制約：`schema_v2.py:522-545` を無変更。
- accepted のみ登録：`cli.py:1033-1040` を無変更。
- acquisition：`cli.py:853-905` を無変更。

ただし、**実行経路全体の受理集合が無条件に完全不変とは断言できない**。従来 smoke は wrapper `895` の `stat -e … -- sleep`、canonical は `perf_preflight.py:23-25` の `stat -x, -o … -- /bin/true`。前者だけ成功する入力や probe timeout は存在し得る。D494 の順序は PATH 解決による付け替えを防ぐが、この差まで論理的に消さない。

逐語上の射程は次のとおり。

- **D348** の pilot 限定は、S8b floor／freeze の exact run_cmd 受理言語に対する決定。calibration/v2 全体を pilot 限定する根拠にはならない。
- **D493** の厳格性原則は calibration にも適用すべき。ただし列挙された `counter_status`／`claim_scope` 等を calibration schema にそのまま追加する指示ではない。
- 本案は degraded calibration を accepted にする分岐を作らない。認証条件を維持したまま測定証拠を残す。

### 5. 閉包

wrapper だけへの追加なら、親の見込みは正しい。

- script は `test_official_perf_closure.py:88` に登録済み。
- shell 発見器 `524-532` は perf predicate のある file を検出する。
- exact shell marker 数の検査 `845-860` は `20` の `_T126_SCRIPT` 専用。本 script の probe 数を固定していない。

一方、推奨する全配線には更新が必要。

- CLI・sweep は `44` 以降の登録集合にない。新しい canonical call／perf 分岐が `499-520` で検出され、`908-915` が赤になる。
- runner の `if use_perf:` 追加は `448-449` の guard 期待値と食い違う。`740-745` が追加条件を検出する。
- 既存 inventory を新しい実装面に合わせる。別の一般化検査は追加しない。

`submit_certify.sh` は変更不要。`85-102` は予約 policy、`159-183` は source／script identity、`217-229` は qsub の配線であり、compute perf 判定を所有しない。perf 判定を submit host に移さない。

### 6. テストの実測経路

**既存 helper の役割を取り違えないことが前提。**

- `_make_submit_clean_fixture:1493-1521`：fixture repo 作成には使える。
- `_run_submit_with_fake_qsub:1711-1763`：submission を検査する helper。job script は実行しない。
- `_calibrate_argv:606-630`：production shell を抽出して実行する既存の方式。
- job 実走 `406-514`：冒頭 gate の検査であり、perf 段の実走根拠にはならない。

追加する shell harness は、production `857-953` の該当領域を境界文字列で抽出し、fixture 内で**その分岐を実行する**。shell ロジックをテストに再実装しない。これは全 job の end-to-end 実走とは区別して報告する。

正負例は以下。

- **正例：候補全滅＋literal perf unavailable**
  - 候補を version 失敗／event 失敗にし、fixture PATH の literal perf も rc=2 に固定する。
  - canonical unavailable receipt、calibrate 呼出し到達、receipt 引数追加、selection symlink 不在を確認する。
  - ホストの perf 有無に依存させない。

- **対照：候補全滅＋literal perf available**
  - canonical 用 CSV を fake perf が出力する。
  - 候補全滅を直接 no-perf 判定にしていないこと、no-perf 引数が付かないことを確認する。

- **負例：候補全滅＋canonical probe_error**
  - literal perf を signal 終了させる。
  - unavailable へ変換されず、calibrate が呼ばれないことを確認する。

- **perf 有り対照**
  - 最初の候補失敗、次候補成功。canonical probe が選択後 PATH を使い、従来 argv を維持することを確認する。

Python 側は `_invoke:379-428` の `calibrate_fn` seam に**実際の `sweep.calibrate`**を渡す。`_fake_calibrate:367-375` だけでは伝播を検証できないため、rep 実行の境界だけを fixture 化する。

確認事項は、全 sweep rep の `use_perf=False`、counter null、throughput 保存、noise 呼出しなし、v2検証可能、rejected、未登録。rep失敗・throughput欠損・maxrss欠損・acquisition不正は引き続き拒否する。rr20/rr80 の capability 一致も含める。

### 7. 編集面の競合

本 script の変更予定は **`907-931` と `945-946` 間**。

| 並行 worktree | 親提示 hunk | 本案との直接重複 |
|---|---|---|
| `.codex/worktrees/t2515-t2534-author` | `11 / 430 / 651 / 688` | なし |
| `.codex/worktrees/t2563-impl` | `10-11 / 774-787` | なし |

先頭コメントや予約式 `783-800` を変更しないので、提示行番号上は競合しない。ただし同一 file の並行編集であり、統合時の行ずれ・文脈競合まで保証するものではない。

## 親 brief への不同意

- **P1 は方向として正しいが不完全。** `run_sweep` への引数追加は不要。一方、runner の必須 metric 検査、noise 回避、v2 null 表現、capability の整合が必要。
- **P2 の「acquisition receipt がある」は acquisition 判定成功と同義ではない。** CLI の追加検査を通したうえで記録する必要がある。
- **既存 fixture が候補全滅を実走できるという前提は誤り。** perf 段を発火させる harness の追加が必要。
- **閉包無変更という見込みは wrapper 単独に限る。** 全配線では既存 inventory の更新が必要。
- **perf 有り経路全体の完全不変を既存行だけで保証する主張には同意しない。** 認証 predicate の不変と、追加 probe による到達可能性の変化を分けて扱う。
- P3 の現在の可用性は未再検証。D352 違反の是正という位置付けとは矛盾しない。

## 総括

推奨は、canonical receipt で no-perf を選び、既存 sweep の throughput を取得・保存して認証 rejected で終える案。  
飽和選択・noise・登録は通さず、schema と品質 predicate は変更しない。  
最小配線は wrapper＋CLI＋sweep closure＋runner の counter 必須部分と対応テスト。  
最大の弱点は、測定証拠は得られても認証済みレコード数は得られず、全 sweep の費用が残ること。  
追加 canonical probe を含む実行経路全体の完全不変は、無条件には保証できない。