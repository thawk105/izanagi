# [T-2169] 正しさ検証を経ない測定面の repo 全体の閉包

- 実施日: 2026-09-02
- 基準 commit: `8a2ccac7feb559805efbb2d9a1b76a68cf41abc1`
- 種別: read-only の静的閉包調査。build・benchmark・測定・dispatch は 1 件も行っていない
- 起票元: `docs/archive/worklog-phase3-0902-1170.md:424-430` (entry 1170、段 6 の 2 レンズ)
- 子: codex plan 1 本 + 敵対相談 2 本 (いずれも `gpt-5.6-sol` / `xhigh` / 受理)。逐語は `verbatim/`

## 結論

**「測定面が verifier を通らない」こと自体は欠陥ではない。** 絶対規律 1 が、性能計測を
trace-disabled build の別 run で行うことを要求している。同じ run で verifier を回せば
観測者効果が入る。したがって層 A (性能値を作る producer) に verifier が無いのは正常な状態である。

争点は層 B、すなわち**その値が certified な成果物 (公式 report・selector・順位・headline) へ
届くか**である。実測の結論は次のとおり。

- **pipeline の COMMIT 経路は閉じている。** verifier 発行 capability と commit receipt、
  WAL の live 再検証、persisted consumer の再検証が合成として働いている。
- **repo 全体は閉じていない。** pipeline を通らない sink が別に存在し、そのうち
  `s8c_result_judge` の観測受理面は正しさ判定を caller の自己申告に委ねている。
- **未検証の性能値を certified 成果物へ実際に運んでいる既存経路は見つからなかった。**
  上記 sink には production caller が無い。したがって本 wave の実装差分は 0 である。

## 起票元の 3 主張の裁定

| 主張 | 裁定 | 根拠 |
|---|---|---|
| `measure_point_floor()` の直接呼出しは admission を通らない | **事実。ただし単独では欠陥でない** | admission は `between_run_floor.py:361` の `main()` 内だけ。関数は `:202` の module-level。python の公開関数は import すれば呼べるのが常であり、「呼べる」ことと「値が公式成果物へ入る」ことは別 |
| floor CLI は verifier を実行しない | **事実。規律 1 の要求どおりで欠陥でない** | ただし理由は「calibration だから安全」ではない。floor は `screening_driver.py:305-349` で読まれ `:407-447` を経て `pipeline.py:1573-1591` の棄却閾値になる。**記述値ではなく受理集合を変える値**である |
| screening は verifier より先に bench を実行できる | **事実。D58 の既裁定であり欠陥でない** | `pipeline.py:1553-1565` が bench 先行、`:1576-1591` が screen-reject を verify 前 abort。生存候補は `:1593-1633` で全 verify を通り `:1634` で初めて certified になる |

起票元の「official commit writer は certified 判定後に閉じている」という表現は、
`execution_guard.require_certified_writer_authorization` を指すなら**誤りである**。同関数は
env_tag / clocks_per_us / numactl と登録 contract の一致、および Pegasus compute での required
contract 一意性を見る**実行環境の authorization** であって、correctness・verifier verdict・
genome・source・binary・throughput・WAL を一切検査しない (`execution_guard.py:107-169`)。
pipeline では build より前の `:1030` で呼ばれ、verifier は `:1472-1516` である。
正しさの閉包は、全 verify 完了 (`pipeline.py:1593-1634`)、COMMIT 前条件 (`:1714-1726`)、
receipt 付き WAL append (`:1756-1772`) の**合成**が担っている。

## 層 A — 性能値を作る producer の一覧

閉包の定義: (a) CCBench 実行ファイルを直接または委譲先経由で起動し、stdout・perf 出力・
経過時間から throughput / latency / counter / 比較用統計を導出する。(b) その実行前に、同じ
protocol・compile-time configuration・source/build identity に束縛された verifier の
certified 証拠を要求しない。

`Genome` を持たない shell / native 経路があるため、「同じ genome + source」は
「同じ protocol、compile-time configuration、source/build identity」へ一般化してある。

### orchestrator/campaign

| producer | 入口 | 層 B の到達先と止めている機構 |
|---|---|---|
| `between_run_floor.py:202` `measure_point_floor` / `:351` `main` | 公開関数 + CLI | `_write_out():255-315` が canonical calibration 名で書く → `screening_driver.py:305-349` が glob → screening 棄却閾値。**consumer は生成時の protocol admission・source pin・artifact SHA を要求しない** |
| `pegasus_floor_scoping.py:135` / `:238` `main` | 公開関数 + CLI | 出力名が `scoping_between_run_*.json` (`:195-200`) で上記 glob に一致せず、`_prepare_out_dir():107-127` が出力先を repo 外へ強制する。**止めているのは filename と出力先であって `ELIGIBLE_FOR_COMPARE` ではない** |
| `pipeline.py:739,747,2027` | screening 有効時のみ bench 先行 | screen-reject は `SCREEN_REJECTION_REASON` の abort。certified にならない。critic loader は識別子と reason しか読まない (`critic/digest.py:834-854`)。s6 / s8a の report は COMMIT 無し候補の bench payload を空にする |
| `s8b_floor_campaign.py:7684,7690` | campaign driver | floor campaign の oracle / admission 系で閉じる |
| `s8b_floor_attempt_launcher.py:435` (`capture_measure_point`) | launcher | 同上 |
| `backoff_profile.py:857` | CLI | 診断 profile。D20 により headline へ流用不可 |
| `s8b_oracle_n_pilot.py:951` | CLI | pilot |
| `s2_verify_calibration.py:232,354` | CLI | verify 構成の較正 |
| `backoff_requested_us.py:1116` | CLI | 診断 |
| `backoff_overthrottle.py:438` | CLI | 診断 |
| `b10_backoff_shape_sweep.py:2538,2896` | CLI | B10 事前登録 campaign。report は `official certification: false` (`:2647-2656`) |
| `silo_ladder_rung1.py:4359-4372` | campaign driver | CCBench argv を組み `_run` で実行、`:4393` で `throughput_tps` を parse する |

### orchestrator/calibrator

| producer | 入口 |
|---|---|
| `runner.py:1057` `measure_point` / `:803` `capture_measure_point` / `:584,661-664` 実 spawn | 中核 gateway |
| `sweep.py:236,244`、既定 `measure_fn=measure_point` の注入 (`:77-113`) | 公開関数 |
| `orchestrator/calibrate.py` / `python -m calibrator` (`calibrator/__main__.py:2-7`) | CLI 2 形態。`--binary` で事前 build 済み binary を直接受ける |

品質判定と registered publish (`calibrator/cli.py:908-928`) が calibration 側の barrier である。

### tools/

| producer | 入口 |
|---|---|
| `tools/pegasus/t141_region_profile.sh:1346-1477` | PBS job。perf record を含む |
| `tools/pegasus/run_ss2pl_lock_study.py:2684`、値導出 `:2507-2565` | PBS job。plotter が「certified fitness・floor・oracle・selection evidence ではない」と明記 (`tools/plotting/plot_ss2pl_lock_study.py:429`) |
| `tools/pegasus/t810_pbs_wrapper.py:777-789,978-995` | `measurement_run` を注入。production では `run_allowed_measurement` に束縛 (`:1102-1108`) |
| `tools/pegasus/exec_calibrate.py:24-43` | JSON の argv を `os.execv`。運用上は calibrator certified CLI へ接続 (`certify_calibration.sh:778-799`) |
| `tools/pegasus/dispatch_compute.py:153-160,286-293,1311-1321` | 汎用 `os.execvpe`。**target 依存の unresolved dynamic entry であり blocked と丸められない** |

T-810 は preregistered executable / argv、AuthorizationToken、completion validator
(`t810_runner_policy.py:122-180`、`t810_validator.py:940-1010`) という独自 barrier を持つ。

### output/ 配下の再実行可能入口 (4 件)

`output/env/pegasus/t139-probe/t139_probe_gap.sh:76-87`、
`output/insights/2026-07-29_t139-ladder-verbatim/t139_probe_gap.sh:76-87` (同一 bytes)、
`output/insights/2026-08-26_b10-balanced-profile/job-body.sh:191-200`、
`output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh:381-390`。
いずれも probe / profile / diagnostic 用で、certified report への consumer は確認できなかった。

### submodule 側

CCBench の native `main()` は 45 hit ある (`external/ccbench/cc/silo/ycsb_silo.cc:24` など)。
性能値の共通出力は `external/ccbench/common/result.cc:55`。ただし `replayTest`・`testzip`・
microbench まで一律 producer に数えると過大計上になる。
`external/ccbench/cc/*/script/` には `.exe` を直接参照する shell が 116 本あり、
そのうち `test_t1k.sh:10-41` のように `ycsb_*.exe`・`grep throughput`・`perf` のいずれの語も
持たない producer が存在する。**語による走査だけでは submodule 側は閉じない。**

### 生値から公式値を導出する importer

CCBench を起動しないため上記の定義 (a) を満たさないが、**未認証の生値を受け取って公式値を
新たに作る**点で同じ危険を持つ。

- `s8c_result_judge.py:33` が `verify_floor_bytes` / `judge` / `publish_result_table` を公開。

## 層 B — 「止まっている」と言える条件

次のいずれかを file:line で示せた場合だけ停止と判定した。

- official sink が verifier 発行の capability / receipt を必須とし、receipt が raw verifier
  evidence・source/build identity・対象 variant・terminal payload に束縛され、別の raw writer が無い。
- persisted artifact consumer が receipt を再検証し、未認証 `bench_done` を順位や性能表から除外する。
- artifact が記述専用であるだけでなく、official consumer 側にもその artifact を拒否する機構がある。

次は停止の根拠にしなかった。**caller 0、leading underscore、`__all__` 非掲載、caller 供給の
`certified: true`、caller 自身が作れる hash、非空の issuer 名、docstring の「official ではない」
という説明、出力先が repo 外であること、`calibration` / `report` という file 名。**

この基準で、pipeline COMMIT 経路だけが十分条件を満たした
(`verifier/core.py:162-259`、`verifier/commit_receipt.py:296-340`、`wal.py:692-717`、
`artifact_admission.py:686-770`)。

## 見かけの gate — 書かれるが読まれない不適格 marker

production の拒否判断に使う読み手を静的に確認できなかったもの。

| marker | 定義 | 実際に止めているもの |
|---|---|---|
| `ELIGIBLE_FOR_COMPARE = False` | `pegasus_floor_scoping.py:41-43`、payload へ `:187-194` | 出力先の repo 外強制と filename 不一致。読み手は test のみ (`tests/test_pegasus_floor_scoping.py:165-180`) |
| `paper_gain_eligible=False` | `backoff_extended_sweep_report.py:37-49` | 未確認 |
| `headline_eligible=False` | `backoff_profile.py:1127-1154` | 未確認 |
| `fitness_eligible=False` | `t152_write_intent_coverage.py:773-795` | 未確認 |

**これらを barrier に数えてはならない。** marker を反転しても certified 値・順位・受理集合は
変わらないので marker 自体は nit だが、「この成果物は安全だ」という結論を marker から導くと
恒真な保証になる。安全性は個別 consumer の admission から立証する必要がある。

## 実在するが本 wave の scope 外の所見 (裁定パッケージ)

### 1. `s8c_result_judge` の観測受理面が権威へ束縛されていない

段 8c 正式系列の事前登録済み受理 consumer である。事前登録 contract の condition 7
(`s8c_preregistration_evidence_contract.v1.json:265-300`) が
`verify_floor_bytes -> judge -> publish_result_table` の到達性を静的に検査している。

- 正しさ判定は caller 供給の boolean / string を受理する (`:452-459`)。
- attestation は caller が同じ値から計算できる SHA-256 と、任意の非空 issuer 名だけを見る
  (`:495-529`)。外部 trust root を照会するコードは無い。
- `source_binding` も caller が両側へ同じ文字列を置けば一致する (`:129-144`、`:293-315`、`:1626-1628`)。
- raw throughput を直接受理し (`:472-492`)、順位を導出し (`:1607-1623`)、
  `official_conclusion` / `official_status` / `selection_evaluation` を書く (`:2316-2358`、`:2413-2438`)。
- 既存 test fixture が `correctness_gate_passed=True` と自己計算 hash と
  `issuer="test-gate-issuer"` だけで受理される観測を作り、official / selection table を
  生成している (`tests/test_s8c_result_judge.py:156-193`、`:1749-1773`)。
  これは保証の正例ではなく、**自己申告入力が通る witness** である。

**ただし production caller は存在しない。** repo 内の参照は上記の凍結 contract と
`s8c_preregistration_evidence.py:3108,3201` の静的到達性検査だけである。module docstring
(`:1-9`) 自身が「外部 producer / issuer が trust root であり、この wave の外に残る」と明記する。
つまり**未接続の interface** であり、既存経路が未検証値を運んでいるわけではない。

**これは起票元が問うた「D1360 をどの admission で強制するか」の答えそのものである。**
tictoc / cicada を floor / campaign consumer へ接続する時点で、この観測受理面が
D1360 を強制すべき場所になる。束縛を実装することは新しい防壁の新設に当たるため、
本 wave では行わず設計択一としてユーザーへ返す。

なお **D1360 は方針の裁定であって共通の code gate ではない。** 実行コード上の D1360 参照は
`genome.py:208` のコメントだけである。「D1360 で塞がる」を file:line の実装根拠に使えない。

### 2. D58 の適用範囲がコードで閉じていない

D58 は適用先を「事前登録外の偵察 sweep と 8b campaign の opt-in」に限定する。しかし
`prepare_screening_campaign()` は任意の `base_cfg` に screening を追加でき
(`screening_driver.py:365-418`)、`verify_screening_preimage()` が検査するのは lock 内の
同一方針だけで (`ident.py:160-193`)、pipeline も preimage 一致しか要求しない
(`pipeline.py:1005-1010`)。範囲の限定は運用規律に載っている。

閉じるには新しい gate が要るため本 wave の scope 外。なお screen-reject は候補を捨てるだけで
uncertified な値を certified にはしないので、規律 2 は破れていない。

### 3. historical Layer 3 report に screen-reject の値が現れる

`layer3_report.build_report()` は `HISTORICAL_RAW` view の全 `bench_done` を `runs` へ射影し
(`:541-552`、`:627-657`)、screen-reject を除外しない。`certifying_input=False` (`:672-674`) なので
現行の certified sink ではない。D58 の「探索射影にも混ぜない」を逐語どおり読むと境界逸脱だが、
certified 値・順位・受理集合は変わらないため nit。

### 4. spawn-site inventory が実在の CCBench 起動を非 CCBench と分類している

`tests/test_ccbench_spawn_sites.py:199` が `("campaign/silo_ladder_rung1.py", "<module>._run"): 2` を
`_EXPLICIT_NON_CCBENCH_PROCESS_SITES` (`:79-222`) に置いている。周囲の項目はいずれも
「argv は CCBench を名指しも実行もしない」と注記された git / toolchain probe だが、この項目には
注記が無い。実際には `silo_ladder_rung1.py:4359-4372` が CCBench binary の argv を組んで
`_run` で実行し `:4393` で throughput を parse する。

`test_reviewed_ccbench_measurement_launches_use_bounded_sites` (`:2190-2197`) は
非 CCBench 分類を差し引いた残りが bounded gateway + safe allowlist に一致することを要求するので、
この分類により実在の CCBench 測定起動が bounded-site 要求の対象外になっている。

**ただし nit と分類する。** `_run` は git・cmake・nm・readelf にも使う汎用 helper であり、
inventory の単位が「subprocess 呼出しを含む関数」である以上、caller で区別できない構造的限界である。
当該起動は現に timeout=240・deadline・直前の競合検査 (`:4348-4354`) を持ち、測定値が
無防備になっているわけでもない。正しく直すには inventory の単位を argv dataflow へ変える必要があり、
それは新しい機構の設計に当たる。

## この調査が証明しないこと

- build できること、実際の `CCBENCH_TRACE` 値、実 argv、verifier verdict、性能値の正しさ。
- dynamic import・`eval`・shell 展開・scheduler 生成 argv・checkout 外の configuration や issuer。
- filesystem 権限、symlink race、TOCTOU、実行中の artifact 差替え、process isolation。
- test の monkeypatch が本番と同じ挙動であること。test が実環境で通ること。
- 現在 caller が無いことは、将来または直接 import による呼出し不能を意味しない。
- console 出力の数値を人間が手で report へ転記する経路は、repo 内の静的 call graph では閉じない。
- `output/` の過去 artifact が生成時点で正しかったこと。規律 7 に従い、現行コードとの差だけで
  無効化もしない。
- vendored `external/ccbench/third_party/**` の独立 benchmark 全体。
- **層 A の全経路件数**。両レンズが独立に「N はまだ主張できない」と結論した。語による走査が
  submodule shell で閉じないこと、`output/` の再実行入口、`os.exec*`、callable default edge、
  class method が残余である。本書は**分類済みの一覧**であって全数の主張ではない。

## 親の provisional 裁定の帰結

| # | 裁定 | 結果 |
|---|---|---|
| P1 | 閉包の定義 | **修正。** 入口集合が Python CLI と公開関数だけで狭すぎた。native main・submodule shell・tools の sh/pbs・generic process helper・injected callable・生値 importer を追加した |
| P2 | screening は D58 の既裁定で欠陥でない | **維持。** ただし D58 の適用範囲がコードで閉じていない点を新たに検出 |
| P3 | 直接呼出しは単独では欠陥でない | **維持。** ただし P5 の閉包根拠には使えない |
| P4 | floor CLI は規律 1 どおりで欠陥でない | **結論維持、理由を修正。** floor は記述値ではなく screening 受理集合を変える |
| P5 | D1360 / D58 / certified writer admission の 3 層で塞がる | **棄却。** `require_certified_writer_authorization` の production caller は 5 site だけで、calibrator・T-810・standalone profile・submodule shell・S8c はこの層を通らない。D1360 は code gate ではない |
