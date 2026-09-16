# 段 6 敵対レビュー A (正しさ防壁) — [T-1328]

指定4資料と実装を静的検査した。比較用ツリーの対象ファイルが基底 `9d52ef145` と一致することも確認した。ファイル変更・テスト実行・変異実走は行っていない。

## must-fix (real 所見)

### 1. calibrate 失敗時の成果物保存を検証する既存テストが、対象処理へ到達しなくなっている

- **file:line:** `orchestrator/tests/test_pegasus_tools.py:1431`、`tools/pegasus/certify_calibration.sh:965`
- **成立させる具体的入力:** 既存 `test_calibrate_failure_survives_err_trap_and_writes_job_result` の入力そのもの。timeout stub は rc=7 を返すが、抽出 fixture は `USE_PERF` を定義していないため、その手前の変数展開で停止する。
- **成果物への影響:** `failure.stage=calibrate` と `job-result.json.calibrate_rc=7` の保存を保証する既存検証が失われる。
- **推奨是正:** perf 有り対照として fixture に `USE_PERF=1` を設定し、既存の rc・failure・job-result・argv assertion を維持する。これは D494 による supersede 対象ではない。

production の accepted 防壁を破る入力は確認できなかった。上記は変更に伴うテスト保守の欠落であり、production の終端処理が壊れたという所見ではない。

## refuted (攻めたが成立しなかったもの)

### no-perf 成果物の accepted 化

**入力:** canonical unavailable receipt、rratio=20/50/80、records=1000→2000→4000、各2 rep、stdout に throughput=100・maxrss=4096、rc=0。

`sweep.py:272` は sweep 後に必ず `saturation=None` として返し、noise の生成箇所 `sweep.py:288` に到達しない。`cli.py:759` の補完も noise を空の throughputs にするだけである。`report.py:106`、`:115`、`:121` が拒否理由を生成し、`cli.py:1055` で登録前に rc=1 となる。

さらに、この成果物の `quality.status` だけを accepted に書き換える入力は `schema_v2.py:529` が拒否する。saturation だけを非nullにしても、空 noise は `:531` が拒否する。両方を測定外で捏造することは、今回追加された実行経路による昇格とは区別すべきである。

**成果物への影響:** throughput を保存した rejected 成果物となり、registered には進まない。

### 候補全滅を第二の no-perf 判定にする経路

**入力:** policy 候補は全て失敗するが、最終 PATH の literal perf は canonical probe に必要な全イベント行を返して rc=0。

`certify_calibration.sh:908` の候補判定は selection・symlink の生成にしか使われない。perf mode は `:945` の `use_perf_from_receipt` から取得され、`:965` だけが追加引数を制御する。この入力では perf 有り経路になる。

**成果物への影響:** no-perf 引数は付かず、既存品質条件を満たせば accepted になり得る。これは裁定が明示した受理集合の増分である。

### canonical probe_error の unavailable 化

**入力:** literal perf の SIGTERM 終了、10秒 timeout、予期しない OSError。

`perf_preflight.py:130`、`:150`、`:153` は probe_error を維持する。wrapper は `certify_calibration.sh:945` の例外を受けて `:948` で停止する。CLI に probe_error receipt を直接渡しても `cli.py:867` の導出で失敗する。未捕捉例外も成功値には変換されない。

候補 smoke の失敗や candidate evidence の例外処理は canonical 判定とは別であり、それだけで unavailable を決めてはいない。

**成果物への影響:** wrapper は calibrate argv の生成前に失敗し、直接CLIでは拒否記録となる。

### perf 有り argv・call shape の変更

**入力:** 第一候補が失敗、第二候補が smoke・canonical probe とも成功。

基底との比較では、選択成功時の最終 PATH と `calibrate_argv` の既存要素は同一。`cli.py:1005` の `perf_kwargs` は空であり、`sweep.py:226` も追加 keyword を渡さない。capability の値も従来の True と一致する。

**成果物への影響:** canonical available の wrapper 経路に `--perf-preflight-json` は付かない。旧 smoke 成功・canonical unavailable の入力は別分類であり、裁定に記載された縮小側の限界である。

### counter 以外の検査の緩和

**入力:** no-perf の第2 rep だけ maxrss 欠損、throughput 欠損、または rc=7。

基底との差分は `runner.py:1256` の counter 検査の条件化だけ。throughput は `:1254`、maxrss は `:1262`、rep 失敗処理は `:1184` に残る。

**成果物への影響:** 該当 rep で fatal となり、後続測定を停止する。最終 rejected だけに依存した検証ではない。

### 新規テストが両層 stub だけで成立する疑い

`test_calibrator_certify.py:1693` は実 `sweep.calibrate` へ委譲し、`:1701` から実 CLI→sweep→measure_point→run_once を通す。benchmark の fixture は subprocess 境界にある。負例も `:1761` で実 calibrate を指定している。

shell テストは `test_pegasus_calibration_workload.py:680` 付近で production script を抽出し、実 canonical probe を走らせる構造である。ただし検証範囲は argv 生成までであり、実起動・job終端を証明しない。報告もその限界を明記している。

**成果物への影響:** 新規テストは実装の伝播と保存内容を検査する構造になっている。既存期待値の変更は、承認された closure guard 更新に限られ、既存テストの削除・skip 化は確認しなかった。

## 所有外の赤 4 件の判定

| node | 判定 | 本文根拠・具体的入力・成果物への影響 |
|---|---|---|
| `test_certify_perf_stage_is_policy_driven_fail_closed_and_precedes_calibrate` | **supersede 済み** | `test_pegasus_tools.py:397` が候補全滅時の即時失敗文字列を要求する。全候補失敗＋literal perf available は D494 が許す入力であり、この要求は撤回対象。他の policy・smoke・順序・symlink assertion は維持すべき。成果物への影響は意図された到達可能性の拡大。 |
| `test_perf_stage_all_candidates_failed_writes_perf_failure` | **supersede 済み** | `:437` の存在しない候補2本に対し、`:439` が canonical 結果によらず rc=2 を要求する。`:423` の fixture に `CALIBRATE_PYTHON` がない説明は正しいが、それだけでは直らない。仮の REPO_ROOT には runner.py しか用意されず、canonical module の導線と PATH の制御も必要。成果物への影響は、旧期待値を残すと正しい継続を誤って失敗扱いすること。 |
| `test_perf_stage_rejects_not_supported_smoke_output` | **supersede 済み** | `:452` の `<not supported>` 候補を選ばない条件は有効。しかし `:461` の「jobを必ず停止」は supersede 対象。候補拒否後に literal perf を probe し、その結果で進むべき。変数不足だけの問題ではない。成果物への影響は前項と同じ。 |
| `test_calibrate_failure_survives_err_trap_and_writes_job_result` | **real** | `:1443` までの fixture に `USE_PERF` がない。入力 rc=7 に対する `:1448`～`:1454` の終端保存契約は supersede されていない。must-fix 1 のとおり、対象処理へ届く fixture に修復する必要がある。 |

## 変異の帰属判定

以下は静的判定であり、変異が実際に kill されたという報告ではない。

| ID | 判定 | 入力・帰属・再照準先 |
|---|---|---|
| M1 | **期待 node 変更** | `[unavailable]` で即時 exit を復活させると receipt 未生成になる。現在は `test_pegasus_calibration_workload.py:699` の読込みが先に失敗し、分岐 assertion には届かない。receipt 読込み前に rc／生成到達を検査すれば候補全滅停止に帰属できる。 |
| M2 | **期待 node 変更** | `[selected]` の base PATH に literal perf はない。probe を前へ移すと FileNotFoundError 由来 unavailable となる。現在は `:731` の status assertion が argv 一致より先に赤になる。期待 node は「選択後 PATH の available 判定」とする。 |
| M3 | **要再照準** | probe_error を wrapper だけで False に変換して元 receipt を渡す変異は、CLI の `use_perf_from_receipt` でも拒否される。全経路の最終拒否では帰属できない。抽出 shell の `:701`／`:704`、すなわち「argv 生成に進ませない」に限定して照準する。receipt 自体の改変とは別変異にする。 |
| M4 | **要再照準** | 選択ブロックを単純に無条件化すると、全滅時の空 `PERF_SELECTED_REAL` に対する `ln -s` が先に失敗し得る。`:717` の不在 assertion まで届かない。selection JSON 生成と symlink 生成を分け、後者は具体的な非空リンク先を定めて登録する。 |
| M5 | **単一理由性 OK** | `[selected]`／`[literal_available]` で available receipt 引数を常時追加。CLI は available receipt を受け入れるので別の拒否には依存しない。`:732` の argv 完全一致が対象となる。 |
| M6 | **期待 node 変更** | unavailable receipt を無視して True にすると、subprocess fixture は perf CSV を書かず、`runner.py:1256` が counter 欠損で停止する。現在は `test_calibrator_certify.py:1709` の rep 数が prefix assertion `:1715` より先に赤になる。現状の実効 gate は counter 必須検査。prefix 伝播を証明するなら subprocess 境界で argv を先に検査する。 |
| M7 | **要再照準** | rr20/80 で closure の False 伝播を削ると、`holdout_observation.py:945` の capability 不一致が benchmark 前に拒否する。rr50 はこの衝突を避けるが、現 fixture では M6 同様 counter 欠損へ帰属する。rratio と期待 gate を分けて登録する。 |
| M8 | **要再照準** | no-perf early return を外すと sat.records=0。rr20/80 は `holdout_observation.py:874` が noise 実行前に拒否する。観測 wrapper により `test_calibrator_certify.py:1708` が先に赤になる構造は有効だが、証明するのは「遷移を試みた」こと。「noise が実行された」とは異なる。実行抑止の実効 gate は holdout。noise 測定への到達を狙う変異は rr50 を指定し、`:288` の測定呼出し／追加 command に再照準する。 |
| M9 | **単一理由性 OK** | unavailable＋正常 stdout で counter 常時必須化。最初の rep 後、`runner.py:1264` で停止する。全 rep assertion の赤をこの metric gate に帰属できる。 |
| M10 | **単一理由性 OK** | 第2 rep の maxrss だけ欠損。過剰緩和すると後続 rep に進む。`test_calibrator_certify.py:1766` の停止位置と `:1771` の理由検査が弁別する。後段の品質判定も rejected にするが、この早期停止の観測を代替しない。 |
| M-POS | **単一理由性 OK（範囲限定）** | 第一候補失敗・第二候補成功・canonical 成功の `[selected]`。選択先、available、argv 完全一致を検査する。証明範囲は shell の argv 生成までで、認証 job の完走ではない。 |

## nit / backlog

- author 報告の「残り3件は変数不足」は、うち2件について不十分。旧 rc=2 期待値、canonical module への導線、literal perf の環境依存も修正対象として記録する。
- M8 の「noise 未呼出し」は、rr20/80 では「noise 遷移未試行」と書く方が正確。観測 wrapper は内側の拒否を消してはいない。
- D493 の degraded **受理**条件は、この変更で較正成果物を accepted にする根拠にはなっていない。今回の終端が rejected であるという説明は維持されている。

## 総括

production の正しさ防壁を迂回して no-perf 成果物を accepted にする経路は確認できなかった。  
counter 以外の必須検査と perf 有りの既存 argv・call shape は維持されている。  
既存終端テスト1件の fixture 修復は必要であり、他2件も変数追加だけでは直らない。  
変異は M3・M4・M7・M8 の再照準、M1・M2・M6 の期待 node 訂正が必要。  
本レビューは静的検査のみであり、実走・変異成功の証明は含まない。