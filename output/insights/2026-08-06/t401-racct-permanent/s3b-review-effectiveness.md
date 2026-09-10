# 防御側レビュー — レンズ B

参照略号: `BRIEF` = 親 `brief.md`、`PLAN` = `s2-plan.md`、`RP` = `run_probes.py`、`SO` = `signal_observer.py`、`TEST` = `test_run_probes_evaluator.py`。静的読み取りのみで、pytest・scheduler command・probe は実行していない。

### 1. 推奨案 A の permission 即時打切りは受理集合を広げうる

- 対象: `PLAN:103-112`、`RP:1765-1789,1797-1854,396-400`
- 根拠:
  - 実装事実: 現行は各 command を `rc=0 ∧ valid=true` まで最大5回試し、最後の snapshot を採用する。record が存在して invalid なら `accounting_integrity_valid=false` となり、観測 gate を落とす。
  - PLAN は初回が「record 不在 + permission marker」なら残り4回を省く一方、受理集合不変と断定する。
  - 反例: 1回目が permission、2〜5回目が foreign ID・件数過剰等の継続した present-invalid なら、現行は `integrity=false`、案 A は `integrity=null` になる。後者は `observation_valid` を通せる。
  - 「次の attempt で再確認」は代替にならない。`accounting_available=false` 単独は再試行理由ではなく、authority が成立すれば次 attempt 自体がない (`verdict-preregistration.md:57-66`, `RP:4041-4045`)。
- 重大度: 受理集合
- 反証可能性: permission 判定後は同一 request・credential session 中に record が出現しないという scheduler/wrapper の一次契約を示すか、`permission → present-invalid` を含む全5応答列について現行と新案の最終判定が同値になることを機械比較すれば潰せる。

### 2. 案 C/D は現行 snapshot selector のままでは既存 racct 異常を救済してしまう

- 対象: `PLAN:198-205,234-240`、`RP:2688-2761,3040-3054`、`TEST:835-854`
- 根拠:
  - PLAN は composite/receipt を「既存 false の救済に使わず、受理集合は同じか狭い」とする。
  - 実装事実: `_select_accounting_snapshot` は `controller-later` の available/valid snapshot を先に選び、その後でしか earlier snapshot の integrity failure を探さない。
  - TEST は「later valid が earlier integrity-false を置換する」挙動を明示的に固定している。
  - したがって controller-later を composite/export receipt に置換すると、observer-earlier の foreign-ID racct を新しい別源の valid で隠せる。これは PLAN の「救済しない」と反対である。
- 重大度: 受理集合
- 反証可能性: source 別 integrity を独立 field/conjunct にし、`racct=false ∧ composite=true` と `racct=false ∧ export=true` が必ず observation false になる設計表と fixture を提示すれば潰せる。

### 3. 新しい会計意味の consumer・version・移行規約が列挙されていない

- 対象: `PLAN:204,210,218-244`、`RP:262-342,3741-3875,4087-4321,4548-4950`
- 根拠:
  - PLAN は案 C で「新 evaluation model と schema/migration」、案 D で「新 decision」が必要とだけ書き、互換表を定義していない。案 D は同じ field 名の意味を変えるのに新 evaluation model すら明記しない。
  - 更新対象となる実装 consumer は少なくとも次の全経路である。
    - model/legacy 判別・envelope・authority: `RP:262-342`
    - observer 側 racct validator と controller adapter: `SO:1150-1360,1564-1641`、`RP:2431-2555`
    - source 選択・因果判定・attempt 合成: `RP:2688-3083`
    - 保存 raw の再評価: `RP:3476-3508,4087-4321`
    - wave-state 検証・first-authoritative 再構築: `RP:3741-3875,4199-4228`
    - resolve の評価・台帳書換え: `RP:4548-4950`
    - attempt-result/session summary: `RP:5406-5458,5749-5769`
    - README の旧判定説明: `README.md:99-103,111-131`
  - 未タグ record だけを legacy とする規約は `RP:262-272`、未知 model の拒否は `TEST:1370-1377` に固定されている。
  - 保存済み台帳は実際に混在する。`wave-state-snapshot.json:44-101` は `evaluation_model` 欠落の legacy、同 `:109-195` は split-v2。保存 attempt は再評価で旧評価を `superseded_evaluation` に移し得る (`TEST:1620-1657`)。
  - fixture 自体も取り残されている。`TEST:16-38` は `accounting_available=false` の既定に `accounting_integrity_valid=true` を組み合わせるが、production の unavailable snapshot は `null` である (`RP:2688-2712`)。
- 重大度: 正しさ境界
- 反証可能性: legacy / split-v2 / 新 model の読み込み・resolve・再評価・authority 順序を閉表化し、上記全 consumer と保存済み台帳を replay して既存 authority が変わらないことを示せば潰せる。

### 4. 案 C は job roster 数を job 単位の会計 record 数へ読み替えている

- 対象: `PLAN:183-204`、`RP:215-258,1649-1730`、`docs/pegasus-runbook.md:115-122`
- 根拠:
  - 実装事実: `leg.nodes` は `#PBS -b` の要求 node 数である。T-361 は `Leg(..., nodes=2)` (`RP:239-258`) と `#PBS -b 2` (`flock_cross_node.pbs:4`) が対応する。
  - 現行 exact-count は `racctjob` stdout 内の `Request ID` record 数を数える (`RP:1668-1683`)。
  - 実 `.e` は `Number of Jobs: 2` を持つ request block 1個だけである (`t361...000.stderr.raw:3-14`)。
  - 案 C の qstat roster は job identity の存在数であり、各 job に Started/Ended/Elapse を持つ最終会計 record ではない。request 単位 `.e` と結合しても現行 per-job accounting invariantを含意しない。
  - 既存 qstat parser は host 列だけを読む (`RP:667-692`)。保存一次資料も1-job例しかなく、`-b 2` で Batch Job Number 0/1 が完全列挙される実測は PLAN にない。
- 重大度: 正しさ境界
- 反証可能性: `-b 2` 以上の request で全 job ID を一つの束縛済み qstat snapshotから取得し、各 ID に final accounting fields が対応する一次資料と、現行 racct invariantへの含意を示せば潰せる。

### 5. 推奨案 A が改善するのは待時間だけで、会計欠測も証拠強度も改善しない

- 対象: `BRIEF:9-10,71-78`、`PLAN:96-123,248-260`、`docs/decisions.md:7970-7999`
- 根拠:
  - 案 A は `accounting_available=false`, `reason=permission`、`.e` の用途、authority 式をすべて据え置く。
  - D161 により availability は authority gate ではない。したがって hazard verdict、authoritative 選出、独立 accounting evidence は一件も変わらない。
  - immediate permission の具体的改善は、1回の `_collect_accounting` を10 subprocess + 16秒 sleepから2 subprocess + 0秒 sleepへ縮めること、すなわち8 subprocess/16秒の削減だけである。
  - 案 B も gate に入力しない (`PLAN:155-161`)。しかも既存 nested `saved_nqsv_stderr_accounting` は request ID、block count、Ended、hash/sizeをすでに保存する (`RP:1957-2068,5344-5352`; 保存例 `attempt-result.json:120-143`)。追加 object の大半は重複する。
  - 設計までという外枠は守っており実装越境はないが、「racct 欠測の恒久対応」の成功条件を「証拠回復」から「死荷重削減」へ変更する裁定が明記されていない。
- 重大度: 記述整合
- 反証可能性: 案 A によって値または下流判断が変わる consumer を示すか、「独立会計は回復せず、成功条件は8 call/16秒削減だけ」とユーザー裁定に明記すれば潰せる。

### 6. 親 brief の「すべての `.e` が manifest-bound」は resolve 経路では偽である

- 対象: `BRIEF:44-46`、`RP:1882-2069,4591-4645`
- 根拠:
  - 実装済みなのは、通常回収時の manifest 保存 (`RP:2072-2116`)、manifest entry の filename/request ID・sha256・size 照合 (`RP:1912-1945`)、block 内 Request ID 照合 (`RP:1957-1988`) である。
  - 一方 `_saved_nqsv_stderr_accounting` は未改名 `*.e` を直接 glob する (`RP:1908-1912`)。
  - 最終 `valid` は manifest-bound を要求せず、matching block が一つでもあれば真になり得る (`RP:2050-2068`)。resolve はその `valid` と qstat 不在だけで path 3 を採用する (`RP:4616-4618`)。
  - PLAN は `:90,262` でこの誤りを発見しているため、この修正を親 brief の確定前提へ昇格させる必要がある。
- 重大度: 正しさ境界
- 反証可能性: manifest のない request-bound raw `.e` を fixture に置き、`saved["valid"]` または resolve path 3 が必ず false になることを現行コードで示せば潰せる。

### 7. `rbudgetcheck rc=0` から「外部会計信号」や上下界は導けない

- 対象: `BRIEF:39-43,65-67`、`PLAN:83,269`、`RP:3098-3156,5512-5559`
- 根拠:
  - 保存 raw は `SFC 307.72 ...` から `306.37 ...` への group 残高変化を示すが、request IDもjob IDもない。
  - parser は group identity と残高の `Decimal` 差だけを取り、換算は明示的に `UNDETERMINED` とする。
  - rc=0 が証明するのは command の利用可能性だけである。並行する同 group の消費を分離できないことは BRIEF 自身も認めている。
  - よって request の会計証拠、上界、下界のどれにも現状では使えない。さらに「唯一」も、qstat に scheduler resource counter が存在するため字義上成立しない。
- 重大度: 記述整合
- 反証可能性: group 排他期間、残高更新の単調性・精度・換算規約、requestとの対応を一次契約または対照実験で確立し、並行投入を加えても算出した境界が破れないことを示せば潰せる。

### 8. 親 brief の8秒/16秒は矛盾し、16秒も呼出し列全体の所要ではない

- 対象: `BRIEF:49-50,68-69`、`PLAN:270,278`、`RP:1058-1124,1765-1789,4591-4599,5284-5290`
- 根拠:
  - 固定 sleep は1 command当たり4回×2秒=8秒、2 commandで16秒。BRIEF 実測8の「sleep 8秒」は誤りで、P3の16秒が正しい。
  - ただし16秒は sleep 部分だけである。10 subprocess は各最大15秒 timeoutを持つため、I/Oを除いても理論上は最大166秒である。
  - 通常経路では request IDを得た attemptだけが対象だが、未解決 attempt の `resolve` は同じ `_collect_accounting` をもう一度呼ぶ。
  - SO の現コードは permission を初回で停止する (`SO:689-700,861-875`)。したがって「全呼出し列が毎 attempt 16秒」でもない。
- 重大度: 記述整合
- 反証可能性: normal/resolve別に command receipt の `duration_ns` と関数全体の monotonic durationを複数回測り、「固定sleep」「subprocess」「observer」を分解した表を示せば潰せる。

### 9. PLAN は `.e` を非独立と認定しながら、独立裏取りゼロへの反証に使っている

- 対象: `PLAN:76,82,253,280`、`BRIEF:62-67,73-77`
- 根拠:
  - PLAN は `.e` を job-writableな scheduler/job混合 stream とし、manifest/hashはproducer authenticityを与えないと正しく認定している。
  - それにもかかわらず `PLAN:280` は、`.e` が cause/terminal evidenceを与えることを理由に、BRIEF の「独立裏取りが恒久的にゼロ」を過剰一般化とする。
  - `.e` が追加証拠であることと、racct DBから独立した会計裏取りであることは別である。PLAN 自身の信頼境界に従えば、「独立 scheduler DB accounting はゼロ」は現在も正しい。
- 重大度: 記述整合
- 反証可能性: job bodyが同形blockを生成・混入できないorigin認証、scheduler署名、またはuser非書換えchannelを示せば、`.e` を独立裏取りとして扱えるため所見を潰せる。

## 総括

real 所見は **9件**。  
最重は所見1で、推奨案 A の permission 即時打切りが後続の present-invalid racct を隠し、D161 が残した integrity gateを `false` から `null` へ変えて受理集合を広げうる。  
この反例を閉じない限り、案 A の「受理集合不変」は採用根拠にならない。