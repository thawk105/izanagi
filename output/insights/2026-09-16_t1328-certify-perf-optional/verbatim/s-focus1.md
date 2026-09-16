# 段 6 焦点再レビュー — [T-1328]

`b8e2e06dd` の8ファイル差分と指定5文書を静的検査した。編集・テスト・変異・性能測定は実行していない。以下の repo 内パスは指定 checkout を起点とする。

## 所見ごとの対応表

| 出所 | 所見 | 判定 (closed/partial/regressed) | 根拠 file:line |
|---|---|---|---|
| レビュー A must-fix 1 | calibrate 失敗時の終端保存テストが未定義変数で停止する | **closed** | `orchestrator/tests/test_pegasus_tools.py:1504` で `USE_PERF=1` を設定。`:1510`～`:1522` に既存の rc=7・failure stage・job-result・identity・argv assertion が残る。`:1532`～`:1547` は no-perf の rc=1・receipt 引数・終端保存も検査する。静的な閉鎖判定である。 |
| レビュー B must-fix 1 | 既存4テストの契約移行と fixture 修復 | **closed** | 同ファイル `:381` の policy・順序検査、`:424` の実 repo／隔離 PATH helper、`:475` の改名テスト、`:497` の unsupported 検査、`:1485` の終端検査を確認。候補全滅では unavailable／available／probe_error を分離し、unsupported 候補の非選択も維持。実環境への適合確認は下記の別残件。 |
| レビュー B must-fix 2 | 「既存テスト期待値の変更なし」という記録の訂正 | **partial** | `author.md:15` の誤記が残る。commit message は4テストの移行を説明するが、`orchestrator/tests/test_official_perf_closure.py:44` の inventory 追加と `:451` の guard 期待値更新を明記していない。commit 本文と一致する `commit-msg-impl.txt:28`～`:32` も同様。段7の訂正記録は確認できなかった。fix が触れていないことを regression とは扱わない。 |

## 派生値の検算

テスト module を import せず、AST の test 関数と parameter 定義を数えた。

| ファイル（`orchestrator/tests/` 起点） | test 関数数 | parameter 展開後 |
|---|---:|---:|
| `test_pegasus_tools.py` | 54 | 72 |
| `test_pegasus_calibration_workload.py` | 48 | 79 |
| `test_calibrator_certify.py` | 48 | 86 |
| `test_official_perf_closure.py` | 7 | 7 |
| `test_calibrator.py` | 69 | 69 |
| `test_holdout_observation.py` | 45 | 108 |
| `test_plain_runner_coverage.py` | 3 | 3 |

`test_pegasus_calibration_workload.py:38` の `THIRD_PARTY_NAMES` は3要素として展開した。終端テスト内の rc=7／rc=1 は、収集上は1件である。

**fix 報告の「4ファイル全244件」**

- 主張：`fix1.md:22`～`:26` の 72＋79＋86＋7。
- 再計算：**244件。一致。**
- ただし、静的件数の一致は「全件を実走して緑」の追認ではない。実走結果は子の報告として扱う。

**段5報告の「289件緑」**

- 主張：`author.md:19` の289件。
- 列挙された5ファイル：86＋69＋108＋7＋3＝**273件**。5ファイルだけなら16件不足する。
- 別掲分は、新規 shell 対照4件、workload の追加6件、tools 2件、env_contract 3件、schedule 1件＝**16件**。
- 合計 **273＋16＝289件。一致。** `author.md:35`～`:37` の新規 CLI 7件は86件に含まれるため再加算しない。ここでも緑自体は未検証。

**commit message の「増分・減分はちょうど」**

**無条件の受理集合の等式としては不一致。**

- 「候補全滅＋canonical available」は perf 有り経路への到達条件であり、accepted の十分条件ではない。品質理由が残れば `cli.py:1036`～`:1057` で rejected になる。増分には「その後の既存品質・登録条件も満たす」という限定が必要。
- 減分も旧版で実際に accepted になる入力との交差で記述すべきであり、smoke 成功だけでは旧版 accepted を保証しない。
- **第三の縮小経路もコード上にある。** 候補配列に同一文字列を重複して与えると、shell の読込み・選択は通り得る（`certify_calibration.sh:145`、`:882`）。canonical literal probe が成功しても、全候補の evidence を作った後、`perf_preflight.py:237` の重複検査が失敗する。wrapper は `certify_calibration.sh:948` で rc=2、argv 未生成となる。これは「canonical probe だけ失敗」ではない。**現行 policy の2候補は重複していない**（`tools/pegasus/policy.json:19`）ため、現行設定での発火を主張するものではない。
- 現行 policy に限定しても、追加 probe／candidate evidence の所要時間は増える（`perf_preflight.py:122`、`:157`）。予約期限近傍の完走可能性まで不変とはいえない。

必要なのは、到達可能性と最終受理を分け、入力・環境を限定した記録への訂正である。新しい gate は要求しない。

**「schema_v2.py の accepted 制約が保証する」**

保証が存在するという主張は一致するが、**唯一の保証という解釈は不一致**。

- `sweep.py:272` が no-perf の saturation を `None` にして noise 前に戻る。
- `report.py:106`、`:115`、`:121` が counter・selection・noise の欠損から拒否理由を作る。
- `cli.py:1039` が rejected を決め、`:1055` が登録前に rc=1 を返す。
- `schema_v2.py:529`、`:531` はさらに accepted の構造制約を課す。

したがって schema は追加の防壁であり、通常経路の rejected 判定は report／CLI にも存在する。

## 実機で確かめるべき残件 (親への指示)

1. **最終 PATH と interpreter を実環境で確認する。**  
   静的には、候補成功時は `$TMPDIR/bin:$(dirname "$CALIBRATE_PYTHON"):$PATH`、全滅時は `$(dirname "$CALIBRATE_PYTHON"):$PATH` で意図どおり（`certify_calibration.sh:907`、`:927`）。probe と calibrate argv は同じ値を使う（`:931`、`:955`）。実際の選択 interpreter・symlink 解決先・PATH 全体を記録すること。

2. **選択済み Python で実 repo の module が import されることを確認する。**  
   `:936` は REPO_ROOT を `sys.path[0]` に追加し、入口の `orchestrator/calibrate.py:10` と整合する。ただし interpreter 選択時の smoke は版数だけ（`:429`）。静的な経路整合だけで実機 import 成功を認定せず、同じ interpreter／環境で module の実際の参照先を確認すること。

3. **ホスト perf 有無の対照を記録する。**  
   新規 shell fixture は Python 自身も隔離 `base` 内の symlink にし、元 PATH を継承しない（`test_pegasus_tools.py:434`、`:461`、`test_pegasus_calibration_workload.py:647`、`:686`）。perf は fixture または選択 symlink に限定される。新規 Python 対照も subprocess 境界を置く（`test_calibrator_certify.py:1657`、`:1701`）。**通常の PATH 解決でホスト perf の有無が結果を変える残存経路は見つからなかった。** 実環境ではホスト perf が見える／見えない双方で、この隔離が効くことを確認すること。

4. **証明範囲を維持する。**  
   shell 対照は argv 生成まで、終端対照は timeout stub による保存検査であり、実 `os.execv`・認証 job 完走の証拠ではない。裁定の「追加 job を投入しない」を越えて新規投入を要求しない。実環境確認が未実施なら、その面を未確認として段7に残すこと。

## 新たな回帰

fix による新たなコード回帰は、静的検査では確認しなかった。

- 改名した候補全滅テストは削除されず、3 parameter に拡張されている（`test_pegasus_tools.py:474`）。
- policy の候補値・順序、event smoke、unsupported 検出、symlink 文字列の assertion は `:383`～`:399` に残る。
- 最終 PATH → probe → receipt 判定の順序は `:401`～`:415` で検査する。
- unsupported 出力保存・候補非選択・symlink 不在は `:515`～`:520` に残る。
- 候補成功側のリンク先・selection・argv 完全一致は `test_pegasus_calibration_workload.py:713`、`:715`、`:732` に残る。
- 改名旧名を参照する Python consumer は `tools`／`orchestrator` の検索では見つからなかった。

## 残る must-fix

1. **レビュー B must-fix 2 の記録訂正を完了する。**  
   段5の閉包・guard 期待値更新と、fix の既存4テスト移行を明記し、段7から訂正記録を参照すること。成果物への影響：レビュー記録が、更新した既存検査と検証範囲を正しく伝える。

2. **受理集合の「ちょうど」を限定・訂正する。**  
   到達可能性と accepted を分け、上記の第三の縮小経路も扱うこと。成果物への影響：変更前後の certified 選択可能集合を過大・過小に説明しなくなる。

## 総括

A1・B1 はコードと assertion 上で closed、B2 は記録訂正が partial。  
244件は一致し、289件も5ファイル273件＋別掲16件で整合する。  
fix による新たなコード回帰は確認しなかった。  
「受理集合はちょうど」の訂正と、DW-O16 の実環境確認が残る。  
静的レビューから全件緑・実 job 成功・wave 全体の closed は認定しない。