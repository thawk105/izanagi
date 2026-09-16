# 段 3 敵対相談 A (正しさ境界) — [T-1328]

必読 5 件は読了。以下は静的検査であり、編集・テスト・測定は実施していない。`plan.md`、`brief.md` は指定された段 2・段 1 文書、repo 内のパスは指定 root 起点。

## real 所見

### 1. 候補全滅＋literal perf 成功は、認証の受理集合を実際に広げる

- **file:line:** `plan.md:35,201-203`、`brief.md:39-40`、`tools/pegasus/certify_calibration.sh:886-909`、`orchestrator/calibrator/cli.py:1014-1040`
- **成立させる具体的入力:** policy 候補の全パスが存在しない。一方、最終 PATH 上の `perf` は canonical probe と本測定を成功させる。acquisition は正常、各 rep の counter は完全、飽和点の miss rate は 0.10、noise CV は 0.01、その他の品質条件も満たす。
- **成果物への影響:** 現行は `failure.stage=perf / rc=2`。提案後は `quality.status=accepted` となり、registered 成果物を作り得る。
- **推奨是正:** これは壊れた counter の救済ではないが、「現在 fail する入力を一つも pass にしない」という親の不変条件とは両立しない。D494 に沿う提案を採るなら、この具体的増分を親の受入条件へ明記する。「認証 predicate が不変」を「script 全体の受理集合が不変」と言い換えない。旧 smoke 成功を新 gate として再要求する是正は、今回の目的に逆行する。

### 2. 候補選択成功でも、追加 canonical probe によって既存の accepted 走を失える

- **file:line:** `plan.md:33-34,159`、`tools/pegasus/certify_calibration.sh:890-904`、`orchestrator/calibrator/perf_preflight.py:23-25,132-145`
- **成立させる具体的入力:** 選択候補が `--version` と `stat … -- sleep 0.1` に成功し、実際の benchmark に対する counter 取得にも成功するが、`stat -x, -o … -- /bin/true` だけ rc=2 を返す。その他は所見 1 と同じ正常入力。
- **成果物への影響:** 現行では accepted にできる走が、提案後は unavailable と判定され、counter 未取得・`saturation:null` の rejected 成果物になる。
- **推奨是正:** プラン自身も認識している未解決の契約衝突である。D494 の指定手順を守ることと、全環境・全 argv 応答について旧受理集合を保存することは別。親の「完全不変」を修正し、この反例を差分の限界として残す。第二の可用性判定や fallback probe を足して隠さない。

### 3. no-perf 負例の「拒否される」だけでは、維持すると謳う gate の検出力を証明できない

- **file:line:** `plan.md:90-95,214`、`orchestrator/calibrator/runner.py:1252-1267`、`orchestrator/calibrator/report.py:111-123`、`orchestrator/calibrator/cli.py:1101-1139`
- **成立させる具体的入力:** canonical unavailable receipt、全 rep rc=0、throughput は正常、maxrss だけ欠損。ここで runner の maxrss 必須検査を削除する変異を考える。
- **成果物への影響:** 本来の rep fatal が、欠損を含む sweep 保存へ変わっても、`saturation=None` と noise 欠如だけで最終結果は rejected のままになる。
- **推奨是正:** 負例では rc・rejected・未登録だけでなく、該当 rep の fatal 理由と後続測定の停止を確認する。正常 no-perf 正例では全 rep と throughput 保存を確認する。対応テストの assertion を具体化すれば足り、新 gate は不要。

これは実装済みテストの欠陥を実測した所見ではなく、**計画された検査条件では変異を区別できない**という静的所見である。

## refuted (攻めたが成立しなかったもの)

- **unavailable の自己申告で、壊れた perf 走を certified に昇格できるか。**  
  整合した receipt として `status=unavailable, available=false, rc=2, parsed_events=[], reason=nonzero-rc` を渡す経路は構成できる。しかしプランは degraded accepted 分岐を作らない。`plan.md:82-85` の `saturation=None / noise_floor=None` により、`report.py:111-123` が拒否し、`cli.py:1033-1040` が登録を止める。D493 型の認証昇格は成立しなかった。

- **no-perf が L3/RSS 経由で選択 records を主張できるか。**  
  全点 `miss_rate=None`、RSS が L3 の 100 倍でも、`analyze.py:48-57` で判定不能となり、下限基準へ進まない。`report.py:79` は選択なしを null にでき、`schema_v2.py:529-532` は null saturation の accepted を拒否する。`schema_v2.py:652` は非 null の `records=0` も拒否する。sweep 各点の正の records は測定入力であり、認証された選択値ではない。

- **shell の `USE_PERF` が第二の判定入口か。**  
  `plan.md:33-45,58-60` では canonical 結果の伝達値として使う。候補全滅だけでは False にしない。`perf_preflight.py:261-270` の `None→True` も既存契約であり、同関数を二箇所で呼ぶこと自体は独立した判定根拠の追加ではない。

- **`<not counted>` を unavailable にして壊れた counter を隠すか。**  
  全 event 行が揃えば値が `<not counted>` でも `perf_preflight.py:70-78,142-145` は available とする。実測 counter 欠損は perf 有りの `runner.py:1256-1267` に残る。

- **追加配線そのものが scope 逸脱か。**  
  wrapper だけでは `sweep.py:235-240` の strict measurement が counter 欠損で止まる。さらに `sweep.py:273-286` は無効な選択値で noise へ進み、rr20/rr80 では `orchestrator/holdout_observation.py:874-875,945-947` の制約もある。提案の伝播・counter 必須部分の限定・noise 回避は本題に必要。既存 inventory の更新も、新しい一般化 gate の追加とは認めない。

## 親 brief への不同意

1. **「19 attempt 中 0 件」から計算ノード全体の現在の可用性は結論できない。**  
   `brief.md:12-16,61-63` の一般化は強すぎる。実際、`output/env/pegasus/calibration/job-staging/0:867863.nqsv/failure.json:7` は allocation、`0:892177.nqsv/failure.json:7` は gflags、`0:989232.nqsv/failure.json:7` は source_identity で停止している。これらは perf 可用性の試行ではない。

   直近 3 件の `0:998860.nqsv`、`0:998863.nqsv`、`0:998864.nqsv` は、それぞれ `perf-selection.json:8` に指定 perf、`job-result.json:3` に rc=0 があり、観測された成功は確認できた。ただし母集合は保存済み attempt、観測 regime は各実行時のノード・kernel・PATH・権限である。別ノード、kernel 更新、linux-tools の撤去、counter 権限変更が反例条件になる。**未観測の実害は推測**であり、「観測範囲では perf 段失敗を確認できない」までに限定すべき。

2. **D352 違反の是正は、上記の頻度推定と独立に成立する。**  
   入力を「全 policy 候補不在、literal perf 不在、他の準備条件正常」とすれば、現行 `certify_calibration.sh:907-909` は測定前に停止する。これは逐語 `rulings-d348-d353.md:135-139` の測定継続要求に反する。発火頻度が未確定でも是正根拠は消えない。

3. **既存 fixture が perf 段を実走するという根拠は誤り。**  
   `brief.md:94-96` に対し、`orchestrator/tests/test_pegasus_calibration_workload.py:461-462` は入力 gate 直後で停止させている。追加する抽出 harness の成功を、全 job の実走成功として報告してはならない。

## nit / backlog

- **変異の事前登録が未提示。** `brief.md:90` は matrix を要求するが、`plan.md` に変異行と期待検出テストの対応表はない。そのため「想定変異が実際に別 gate で先に赤になる」と実証済みのようには書けない。静的な帰属上の注意は次の二つ。
  - capability を True のままにして no-perf 伝播を壊すと、`orchestrator/holdout_observation.py:945-947` が測定前に拒否する。runner の metric gate の検出力には帰属できない。
  - 新しい `if use_perf:` 自体の削除は、`test_official_perf_closure.py:740-745` の構造検査でも検出され得る。suite 全体の赤だけでは行動テストへの帰属にならない。
- 必読の `rulings-d348-d353.md` は読めたが、内容は 151 行で D352 まで。D353 本文は含まれていない。今回の結論には使っていない。
- 調査時に `orchestrator/perf_preflight.py`、`orchestrator/calibrator/holdout_observation.py` は存在しなかった。実体の `orchestrator/calibrator/perf_preflight.py`、`orchestrator/holdout_observation.py` で検査を続行した。

## 総括

最大の問題は、候補全滅＋literal perf 成功が accepted を新たに作れるのに、親が受理集合の完全不変を要求している点。  
最小の是正は、この増分を受入条件に明記し、認証 predicate の不変と実行到達性の変化を分けること。  
no-perf 自己申告による certified 昇格経路は見つからなかった。  
追加 gate は不要。対応テストでは最終 rejected だけでなく、失敗理由・測定停止位置・保存された系列を確認する。