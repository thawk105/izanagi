## 所見

以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`、`brief.md` と `plan.md` は指定 job root 配下を指す。編集・pytest・計測は実施していない。

### must-fix

1. **real — `commit_witness` の null 許容は、`verify_done` 到達時の値域と一致しない。**

   根拠: `plan.md:139`、`C/pipeline.py:575,598,606,633`。型宣言は `Optional[int]` だが、witness が null なら598で abort、batch witness が非ゼロなら606で abort する。633の `verify_payload` に到達する時点では両方 integer、batch は0である。abort payload の値域との混同がある。

   **放置時の成果物影響:** 現 producer が verification として発行しない「witness 欠測」の行まで新 schema が受理する。

   最小是正: verification 用の両 count は integer とし、property 自体は optional のままにする。null の正例を verification 用 fixture に混入させない。abort の既存値域は変更しない。

2. **real — brief の非 null delta と whiteboard 2件という前提が残っている。**

   根拠: `brief.md:10–11,68–70`、`C/p3_s4_loop.py:1213,1315,1964,2483,2495`、`T/test_p3_s4_loop.py:7076,7090`。`_DELTA_PCT_LIVE=False` で、成功時も `delta_pct=None`。2件になるテストは同じ layout に2回 drive している。`last_delta_pct` を現物から取ること自体は正しいが、前提となる whiteboard 2件が誤っている。

   **放置時の成果物影響:** planner-3 入力や insight に、存在しない履歴・非 null 差分を補ってしまう。

   最小是正: 親が brief の上記両箇所を plan §3・§8に合わせる。本巡の whiteboard は実 checkpoint の件数、delta は null と記録する。

3. **real — 本巡の取込み完了と renderer の双射を、件数式だけで結び付けてはいけない。**

   根拠: `plan.md:100–117,255–280`、`C/layer3_report.py:246–278,912`。読み取った AO の canonical ref Counter を期待側にすることは、**AO file と report の双射として正しい**。等件数置換にも内容 hash で対抗できる。「読めた件数だから等件数置換に弱い」という攻撃は、そのままでは成立しない。

   ただし、取り込まれなかった event はその Counter に存在しない。`W+1+5`、または coder-2 を除いた `W+1+4` だけでは、本来の原本との対応を証明できない。

   **放置時の成果物影響:** AO の取込み漏れや別出力への置換を残したまま、「本巡の役割出力を完全収録した」と報告できる。

   最小是正: renderer の期待側は、report と独立に読んだ全 AO envelope の Counter を維持する。親の本巡受入では、plan §8の各原本について stage・入力 hash・出力全文・provenance と AO を照合する。coder-2 未回収なら4件の双射成功と、取込み未完了を併記する。新台帳は不要。

4. **real — 変異候補は、まだ単一理由の登録に使える粒度ではない。**

   根拠: `plan.md:25,117,219–228`、`C/wal.py:452–463`、`C/layer3_report.py:269–278,913–914`、`docs/dev-wave/mutation.md:5`。

   **放置時の成果物影響:** 別層の拒否で緑を保ち、AO 完全性や原文保持の欠落を検出したと誤認する。

   最小是正: 段4で少なくとも次のように照準を分ける。実装後の単一理由確認は依然必要。

   | plan 候補 | 重複拒否・恒真化の問題 | 最小の照準 |
   |---|---|---|
   | 1 未知 stage | CLI choices、共通 reader、schema enum が重なる | reader の直接負例と schema の直接負例を分ける |
   | 2 未終端行 | `wal.iter_lines` が内側で既に拒否する | AO 側に冗長な終端検査を設けず、実際の framing 経路を対象にする |
   | 3 時刻変更再取込み | envelope 完全重複と混ぜると理由が二つになる | `ts` のみ変え、canonical envelope hash が異なる正例から semantic duplicate を試す |
   | 4 planner/coder 欠落 | 古い `source_refs` を残すと区画整合でも拒否される | report 本体と `source_refs` を同時に欠落形へ揃え、入力 Counter だけを不変にする |
   | 5 critic 二重計数 | 「view を走査する」という実装変異と、view 重複入力は別 | 正常な一次配置＋正常な critic view に対し、一次走査への view 混入を変異する |
   | 6 expected を report 由来へ変更 | critic を替えると view 照合にも捕まる | planner/coder の有効 envelope を等件数置換し、`source_refs` も置換後に揃える |
   | 7 別 critic 参照 | 存在しない ref では参照存在検査も拒否する | 有効な critic 2件を用意し、view の対応だけを入れ替える |
   | 8 provenance | literal `"present"` は契約 enum 外で schema が拒否する | 不在時に有効値 `"agent_outputs"` を発行する変異にする |
   | 10 全文・入力 hash | 二つの異なる保証が一候補に混在 | 外側 metadata 削除と、入力 hash の出力 hash 化を別変異にする |

   特に「3 stage のみから選んだ候補が3 stage 内にある」という検査は恒真なので、検出力には数えない。

### 確認して反証した懸念・nit

5. **refuted — 全 stage の一次配置と critic view が必然的に二重計数になるわけではない。**

   根拠: `plan.md:100–117,318–319`、`C/layer3_report.py:246–278`。plan は `agent_outputs` の全 envelope を一次走査し、`mechanism_hypotheses` は二次 view と明示している。既存実装も Counter の完全一致であり、件数比較ではない。

   **成果物影響:** plan どおりなら各 AO は一次配置に1回現れ、critic view は参照として追加されるだけである。

   最小是正: 追加設計は不要。AO 入力と report が同じ可変 list/object を共有し、変異が期待側にも伝播しないよう、負例では独立した入力を保持する。

6. **refuted — `proof_surfaces` の3値 enum は現在の producer 受理集合を狭めない。**

   根拠: `orchestrator/verifier/model.py:29–37,66–90`。`as_record()` は exact に `protocol/X/P/I`。X/P/I はコンストラクタでも3値に制限される。一方 `protocol` は任意の string または null であり、`silo/si/mocc` enum に閉じてはいけない。

   **成果物影響:** 現在の3値 enum なら producer 出力を失わない。protocol を3プロトコルに限定すると producer が許す値を排除する。

   最小是正: plan の X/P/I enum を推す。D830 は主に **key 閉包**の規則であり、enum だけでは満たせない。producer コードからの導出と実 emit 検査を残す。将来 producer の値域を変更する場合は、その変更で schema との不一致を検出させる。

7. **refuted — 較正ディレクトリ不在だけで submit-tree の render が停止する。**

   根拠: `C/layer3_report.py:456–461,530–547,659–667,671–679,714–734,865–872`。指定 `--output-root <submit-tree>/output` は campaign を包含する。外部 campaign の ancestry 境界は submit-tree。較正ディレクトリ・通常の pin file の不在は欠測へ進む。

   **成果物影響:** 較正が無ければ floor は `value:null`、`provenance:"no-matching-env-record"` となる。pin があれば検索詳細に `pin-file-missing` が残る。

   最小是正: path 対策や較正の複製は不要。dangling symlink・不正 file・SHA 不一致は引き続き拒否する。`brief.md:37` の「schema error 1件のみ、双射通過」からは、floor が非 null だったとは推論できない。

8. **refuted／未実測 — ファイルの行数から受入5分超過は断定できない。**

   根拠: `T/test_layer3_report.py:211`、`T/test_p3_s4_loop.py:6145,7056`、`T/acceptance_duration_ledger.json:1`。台帳を読み取った合計は layer3 が237 node・22.445秒、loop が414 node・115.081秒。これは node 所要の合計で、受入 wall time でも今回の実測でもない。

   **成果物影響:** 重い実 repo fixture を新規負例ごとに作ると受入費用が増えるが、現時点で5分違反の証拠はない。

   最小是正: AO parse/write は一時 layout と3行程度、双射・view はメモリ上の最小 report、schema は最小行で検査する。admission 付き `_campaign` や public drive は結線正例に限定し、全変異へ丸ごと展開しない。親が受入 wall を測定する。

### pin 閉包と所有

9. **refuted — 現 plan に、既存 pin を必ず破壊する変更は見つからない。ただし brief の一覧は不完全。**

   根拠と保持対象は次のとおり。

   | pin 元 | 内容 |
   |---|---|
   | `T/test_t126_pegasus_tools.py:463,471,476` | ancestry 呼出しの改行・字下げ、lock/records の lineage 条件 |
   | `T/test_official_perf_closure.py:57,246` | renderer 登録と `_validate_schema` 内の perf validator 呼出し |
   | `T/test_campaign.py:5397,5479` | loop の `run_campaign` 呼出し各1本 |
   | `T/test_ccbench_spawn_sites.py:135` | renderer `_git_head` の subprocess site 1本 |
   | `T/test_layer3_report.py:439,1820` | 旧空 MH fixture、v3 const、runs required |
   | `T/conftest.py:329,492`、`T/test_real_repo_serialization.py:3310` | 既存 public-drive node の分類・結線 |

   **成果物影響:** 内容や呼出し本数を変えると既存の防壁・受入検査が成立しなくなる。単なる物理行番号の移動はこれらの違反ではない。

   最小是正: 上記を親の受入範囲へ含める。A1 は専用 writer と既存 framing reader を使えるため `wal.py` 編集は不要。A2 の schema/view 変更も所有内に収まる。`hooks/guard_write.py:58–69` は runs の leaf 名を限定しておらず、追加編集不要。ただし別 submit-tree・全ツール経路まで防護済みとの主張はできない。brief・記録 docs の訂正は親が所有する。

### 裁定パッケージ候補

10. **real — 旧 artifact の全文可読性と fresh 比較は、別々の未解決問題である。**

   根拠: `C/layer3_report.py:307–314`、`C/autonomous_trial_completeness.py:4652,4687–4721,5033`、`T/test_layer3_report.py:1656`。

   `git grep` で列挙した保存済み report 8件を読み、現行 schema と現行の v2 導出操作をメモリ内で検査した。v2 の6件と v3 の1件は schema error 0件。v1 の1件は6件のエラーで、版・必須項目・noise_floor 構造などが既に不一致だった。新 schema は未実装なので、その検証結果ではない。

   v1 全文を現在読む専用 consumer は今回の `orchestrator/`・`tools/` 検索では確認できず、本巡は新規 v3 である。したがって v1 reader 新設を本 wave 外へ返す判断は妥当。ただし `brief.md:61` の「既存 v1/v2/v3 が妥当」は訂正が必要。

   generator SHA は新 report で必ず変わる。旧 SHA の固定 fixture による直接回帰は確認できず、主要 fixture は `T/test_autonomous_trial_completeness.py:3774` と `T/test_trial_registry.py:1272` で現 generator から作る。しかし保存済み report を fresh と比較する consumer は SHA と新 optional 区画を保持するため、不一致になり得る。

   **放置時の成果物影響:** 旧 report は保存されたままだが、現行 consumer による再受理が失敗する。通常テストが通っても、この後方互換問題は消えない。

   最小是正: 親が「v1 全文 reader」と「保存済み report の fresh 比較」を別の裁定パッケージ候補として返す。本 wave で consumer を解決済みとせず、旧成果物の再生成や SHA 差し替えで合わせない。

## 総括

段4で直すべき点は、verification witness の値域、brief の delta・履歴前提、本巡取込みと双射の区別、変異候補の単一理由化である。AO 一次配置、proof enum、submit-tree の欠測処理、A1/A2 のコード所有分割は基本的に成立する。

実施したのは読取りと既存 artifact のメモリ内 schema 検査のみ。pytest・受入全走・本巡 render の成功は報告していない。