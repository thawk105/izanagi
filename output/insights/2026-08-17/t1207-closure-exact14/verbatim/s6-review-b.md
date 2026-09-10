## 所見

### COST-01 / should-fix

- **主張:** 「新規検査は O(1)」という完了報告は誤りで、closure size N に対し対照2 nodeとclean nodeは O(N) である。
- **根拠:** `s5.md:81` は「新規検査はO(1)」とするが、`test_t671_source_binding.py:112-135` は各一時 repoで N fileを作成して N blobを読む。対照2 nodeは同 helperを呼び (`:207-209`)、clean nodeはさらに N 回の独立 `git cat-file` を行う (`:264-290`)。
- **反例または検算:** 静的node数は T671が51から63へ増加した。内訳は既存4系列の12から14への展開で+8、対照+2、clean+1、census+1。単純比では `3.19 × 63 / 51 = 3.94s`、二乗比では `3.19 × (14/12)^2 = 4.34s` となり、どちらも3.51s超過を予測する。ただし親の既存ログ `/home/SFC/tanab/.claude/jobs/f3762925/tmp/wave/focus2.log:14` は63 passed / 2.70sを記録しており、現実測では閾値未満である。
- **成果物影響:** certified値は変わらないが、費用台帳を O(1) と記録すると将来の閾値判断を誤る。

補足費用分類:

- T671の既存4系列: O(N²)。
- 新規対照2 nodeとclean node: O(N)。census: O(1)。
- codec: missing-key系列は O(N²)、旧exact-12拒否nodeは O(N)。増分は+3 node。
- artifact admissionのverifier drift系列: O(VN)、verifier member数 VもNと増える最悪形では O(N²)。増分は+2 node。
- repo履歴に比例する処理は見つからず、O(履歴)はゼロ。

### F357-01 / should-fix

- **主張:** s5のF357候補集合は過大で、登録済み焦点走では偽赤nodeはゼロ、名指しされた関連consumer群では静的に確定できるのはLayer3の1 nodeである。
- **根拠:** s5はartifact/bench/env/layer3/S6/S8aを広く候補にする (`s5.md:90-94`)。しかしartifactのE1 nodeは一時repoへ `_REPO_ROOT` を差し替える (`test_artifact_admission.py:1122-1129,1180-1199`)、S6/S8aも同様である (`test_s6_sort_sweep.py:616-638`, `test_s8a_trigger_sweep.py:826-848`)。一方 `test_layer3_report.py:54-64` はHEAD blobだけでlockを作り、`test_accepted_report_requires_e1_and_records_epoch` は差替えなしでcertified gateへ進む (`:817-835`)。gateはそこでlive closureをcaptureする (`artifact_admission.py:778-800`)。
- **反例または検算:** 現在のfocus1/focus2はT671とcodecだけで、T671は全live検査を一時repoへ隔離し、codecはlive captureを行わない。関連範囲をLayer3へ広げた場合の偽赤は `orchestrator/tests/test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch`。全suiteへ範囲を広げるなら別途再列挙が必要である。
- **成果物影響:** product bytesは変わらないが、偽赤集合の過大申告は真の回帰の帰属と受入窓を誤らせる。

### DOC-01 / should-fix

- **主張:** B-01、B-03とexact-14文書追随は未実装であり、段7で新D、F357 supersede、T-819消化を必ずlandする必要がある。
- **根拠:** D442はexact-12、旧excluded集合、旧受理言語を保持している (`docs/decisions.md:18501-18516,18528-18539,18549-18555`)。F357も12 pathのままである (`docs/failures.md:8792-8801`)。T-819は未消化台帳に残る (`docs/phase3.md:1215`)。
- **反例または検算:** D442は歴史記録なのでin-place変更ではなく、裁定どおり新Dで決定1・3とdispatch/report制限だけをsupersedeする。F357には14 path化に加え、隔離fixtureの焦点走では偽赤ゼロになり得るという限定も必要である。
- **成果物影響:** 未追随のままlandすると、decision・failure・phase台帳が実際のclosureと保証範囲を誤記する。

## B-01〜B-05判定

- B-01: **未実装**。現checkoutのphysical `output/**/campaign.lock`に限定する文言は段7待ち。
- B-02: **部分実装**。node数と実測は親側にあるが、費用クラスの O(1) 宣言が誤り。
- B-03: **部分実装**。裁定にはrunner作法があるが、T-819台帳の消化と変異実測は未完。
- B-04: **実装済み**。excluded scopeは裁定逐語と一致する (`artifact_admission.py:69-72`)。
- B-05: **実装済み**。独立 `git cat-file` digest照合がある (`test_t671_source_binding.py:284-290`)。

受理集合と取り残しの検算では追加所見なし。既存12 pathは順序・綴りとも不変で新2 pathだけ末尾追加 (`campaign_lock.py:29-43`)。v1 decode (`:234-241`) とdomain (`artifact_admission.py:63`) は不変で、禁止2ファイルもHEADと同一SHA-256だった。旧exact-12逐語は意図的なpre-wave反例とD442/F357以外には残っていない。新旧node名、test file集合、node数を固定する追随対象meta-testも見つからなかった。

## 総括

must-fixはゼロ、should-fixは費用分類、F357集合、段7文書carryの3件です。  
productionの受理集合変更は裁定どおりv2 exact-12からexact-14への置換だけです。  
v1、domain、既存12 path、verifier禁止2ファイルのbytesは不変です。  
私はpytestを実行しておらず、実測値は親が既に作成したログとしてのみ引用しました。