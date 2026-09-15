## 真値の導出表

**再集計は計測前 3250 秒。別紙 D の 3230 秒は perf 候補を 1 件分しか数えていない。**

以下、`S` = `tools/pegasus/certify_calibration.sh`、`C` = `orchestrator/calibrator/cli.py`。行番号は確認時点。

| 式の項 | 実在する根拠 | 秒 |
|---|---|---:|
| `qstat(30)` | S:252 | 30 |
| `static_probe(120)` | S:383 | 120 |
| `gflags_configure(60)` | S:475 | 60 |
| `gflags_build(60)` | S:481 | 60 |
| `gflags_install(60)` | S:487 | 60 |
| `glog_configure(120)` | S:540 | 120 |
| `glog_build(120)` | S:546 | 120 |
| `glog_install(120)` | S:552 | 120 |
| `third_party_copy(3*120)` | S:585 の masstree / mimalloc / googletest の **3 回**、timeout は S:587 | 360 |
| `pristine_verify(120)` | S:598 | 120 |
| `ccbench_configure(900)` | S:681 | 900 |
| `ccbench_build(900)` | S:682 | 900 |
| `binary_hash(60)` | S:685 | 60 |
| `trace_nm(60)` | S:687 | 60 |
| `pre_probe(120)` | S:729 | 120 |
| `perf_version(2*10)` | S:850 の候補ループ、S:858。`policy.json:19` の候補は 2 件 | 20 |
| `perf_smoke(2*10)` | 同ループ、S:863 | 20 |
| **計測前小計** | 上記の和 | **3250** |
| `TSC(10)` | C:65、C:229 | 10 |
| `cooldown_max(1200)` | C:63、C:229 | 1200 |
| `points(5)*sweep_reps(3)*120` | C:224 の倍増点数計算、C:64、C:230 | 1800 |
| `noise_reps(10)*120` | C:64、C:231 | 1200 |
| `2*sweep_reps(3)*120` | C:64、C:232 | 720 |
| `cli_finalize(60)` | C:66、C:233 | 60 |
| **CLI 予約小計** | C:220 `reservation_budget()` | **4990** |
| `post_probe(120)` | S:928 の成功条件内、S:929 | **外側 reserve に内包** |
| `finalize_reserve(600)` | `calibration_v1.json:7` → S:125、S:141、S:819 | 600 |

条件分岐は次のように数える。

- perf は非実行ファイルなら省略、version 失敗なら smoke を省略、成功候補で打ち切る。ただし「第 1 候補の smoke が失敗し、第 2 候補が成功」は到達可能なので、最大配分は **40 秒**。
- build 等の失敗は途中停止するが、成功経路には全段が存在するため全項を積む。
- protocol の 3 分岐は argv 選択であり、CCBench build を 3 回とは数えない。
- post probe は calibrator 成功時だけ走る。その 120 秒は常に確保する。

したがって別紙 D の修正は、計測前 **3250**、前後 timeout 合計 **3370**、旧 `build_cap(1080)` との差 **2170**。親の 8760／8820 は、それぞれ **8780／8840** となる。

なお、この「真値」は**指定された timeout と CLI 予約項の和**である。S:197 の最大 60 回の sleep、timeout のない source 検査・後処理、CLI の hash／nm 定数（C:67–68）などまで含む job 全体の実時間上限を証明した数ではない。この区別は冒頭コメントにも明記する。

## 計測予算の積み方

**4990 秒をそのまま積み、post probe は外側の 600 秒に含める案を採る。**

CLI 内蔵 60 秒と wrapper の 600 秒を区別でき、CLI 予約式の意味も変更しない。

```text
R = pre_timeout_caps(3250) + cli_budget(4990) + finalize_reserve(600)
  = 8840
```

C:726–731 の時間に関する受理条件は、reserve が正で、次の両方が成立すること。

```text
4990 + 600 ≤ R
R ≤ Q
```

| 積み方 | R | `reservation-mismatch` を回避 | Q=10800 で qsub 判定 |
|---|---:|---|---|
| 4990 をそのまま積む〔採用〕 | 8840 | 5590 ≤ 8840 | 8840 ≤ 10800 |
| 内蔵 reserve を除いた 4930 | 8780 | 5590 ≤ 8780 | 8780 ≤ 10800 |

4930 案も**数値上は受理される**。ただし CLI の判定は項の重複・包含を検証しておらず、それ自体を予算分解の正しさの証明には使えない。

post probe を外に出す場合は各 R が 120 増え、8960／8900。両方とも `5590 ≤ R ≤ 10800` を満たす。今回は S:819 が後処理用 600 秒を差し引く設計に合わせて内包し、post probe 後の配分は 480 秒と説明する。

S:819 の `remaining` は perf より前に計算される。したがって、その outer timeout から「後処理に必ず 600 秒残る」とまでは主張しない。実行順・timeout は変更しない。

## 要求枠の 2 案

### 案 A：10800 秒へ増加し、8840 秒を凍結

| 編集箇所 | 変更内容 |
|---|---|
| S:4 | `elapstim_req=03:00:00` |
| S:7–11 | 上表の項による式と `8840 < 10800`、保証範囲を記載 |
| S:770 | 計測前各項＋CLI 各項（内蔵 60 を含む）＋`int(reserve_s)` |
| S:771–775 | 同じ項・合計 8840 の逐語 |
| `tools/pegasus/policies/calibration_v1.json:5–6` | `"03:00:00"`／`10800` |
| `tools/pegasus/policy.json:7–8` | 同じ 2 値へ同期 |
| `orchestrator/tests/test_pegasus_tools.py:212–214` | 下節の pin へ置換 |

数値整合は成立する。ただし **03:00:00 が必要最小とは導けない**。02:30:00＝9000 秒でも 8840 を 160 秒上回る。10800 の余裕は 1960 秒であり、その採用理由は別途必要になる。

裁定上は D1936 項38 の「必要分だけ要求時間を増やす」と方向が一致する。一方、後続の D1971 は次を明記している。

> 要求時間・timeout・標本数は本waveで変更しない。

> 要求時間増加へ戻さず、時間式再凍結を完了扱いにしない。

したがって、親の「禁止ではない」という解釈は逐語に反する。**案 A はレビュー可能な実装案だが、現裁定のまま実装へ渡せない。**

### 案 B：7200 秒を据え置き、予約配分として定義

具体案は、CLI 予約と後処理予約だけを `required_s` にする。

```text
allocation_only:
cli_budget(4990)+finalize_reserve(600)=5590
```

| 編集箇所 | 変更内容 |
|---|---|
| S:4、両 policy の上記箇所 | 02:00:00／7200 を維持 |
| S:7–11 | 配分 5590、残余 1610、計測前 timeout 和 3250、最大経路の包含を保証しない旨 |
| S:770 | CLI 各項＋`int(reserve_s)`＝5590 |
| S:771–775 | `allocation_only:` を明示した上記逐語 |
| test:212–214 | 配分式・5590 の pin へ置換 |

受理条件は `4990+600=5590 ≤ 7200` で成立する。ただし計測前への残余は `7200−5590=1610 < 3250`。式の再命名で不足を解消したことにはならない。

案 B は D1971 の要求枠据え置きには沿うが、D1936 の「既存逐次処理の上限を使う同じ式」、親 brief の完了条件を満たさない。また D1971 は予約配分への意味変更を承認していない。**案 B も本欠陥の解決としては採用しない。**

## pin 側の書き換え

**B1〜B3 は逐語 pin を維持し、新式へ差し替える。** 新しい一般化・式パーサーは追加しない。

確認時の B1〜B3 は `test_pegasus_tools.py:212–214`、B7 は :211。別紙とは 2 行差がある。

| pin | 案 A の扱い |
|---|---|
| B1 | `frozen_required_s` の実際の代入式全体を pin。計測前各項、CLI 内蔵 `+60`、`+int(reserve_s)` を含める |
| B2 | `walltime_formula` に上表の各名称・秒・回数が並ぶ新しい文字列を pin。架空の `build_cap` を除去 |
| B3 | `finalize_reserve(600)=8840` に置換 |
| B4、:149–152 | 維持。PBS と calibration policy の 03:00:00 を照合 |
| B5、:157–160 | 維持。03:00:00 と 10800 の換算一致 |
| B6、:164–172 | 維持。全 `finalize_reserve(N)` が `{600}`、かつ `600 < 10800` |
| B7、:211 | 維持。receipt が `frozen_required_s` を使うことを確認 |

B6 が検査するのは **reserve と要求枠の大小**であり、`required_s < certify_walltime_s` ではない。後者を検査していると説明してはいけない。

案 B なら B1 は CLI＋reserve の代入式、B2 は `allocation_only:` 付き逐語、B3 は `finalize_reserve(600)=5590` にする。B4〜B7 は維持する。

逐語をそのまま残すため、production の式だけを人手で変更すれば対応 pin が失敗する。新式から期待値を作って新式自身と比較する循環にはしない。

## pin 閉包の穴埋め

**調べた repository 内には、過去 receipt を現在の job 式で再計算する consumer は見つからなかった。**

実測した範囲と根拠：

- `output/env/pegasus/calibration/attempts/**` の JSON **59 件を読み取り**。読み取り失敗なし。
- `walltime.formula` を持つ記録は **6 件**。いずれも旧式、`required_s=6610`、`reserve_s=600`、qsub 要求 7200。
- repository の Python／shell を対象に、旧式・`reservation_budget`・`_acquisition_reasons`・walltime formula の参照を検索。
- `cli.py:823,893` の再計算は新規認定の入力 receipt に対する処理。既存 attempts は :835–840 の create-only で再利用されない。
- `schema_v2.py:423–427,537–539` は文字列・数値と**同じ receipt 内**の大小を検証する。現行 policy／job 式を読まない。
- `campaign/calibration_verify.py:106–118` は成果物の SHA と schema を検証する。現行時間式への置換はない。
- `collect_receipt.py:107–179` は job ID・会計記録・ファイル hash を束ねる。時間式は再導出しない。

したがって移行は、新しい submit／job が新しい script SHA・要求枠・式を新規 receipt に残す既存経路だけでよい。過去の 6 記録は据え置き、旧式の過小計上の説明は予定済み insight／decisions への追記で扱う。

探索中に推測した `orchestrator/calibrator/loader.py` は存在しなかった。探索を継続して実 consumer の `campaign/calibration_verify.py` を確認した。

## 焦点走の対象

案 A の production 変更は script と 2 policy。参照関係に基づく中心集合は次のとおり。

| test file | 参照根拠 |
|---|---|
| `orchestrator/tests/test_pegasus_tools.py` | :23–24、:140、:200。両 policy と script を直接読み、pin・PBS・実行断片を検証 |
| `orchestrator/tests/test_pegasus_calibration_workload.py` | :33 の `JOB`、:430 の資材コピー、:471/:498 の script 実行、:659 の shared policy コピー |
| `orchestrator/tests/test_pegasus_policy_registry.py` | :20–24、:329、:371。registry と production consumer の読み取り経路 |
| `orchestrator/tests/test_official_perf_closure.py` | :88 の script 登録、:541–588 の source 読み取り |
| `orchestrator/tests/test_ccbench_spawn_sites.py` | :871–880 の production source 読み取り、:2686 の certify script の build sink 確認 |

shared `policy.json` の直接 consumer として、以下も参照がある。変更するのはトップレベルの 2 key のみで、各 test の他 job 用期待値は変更しない。

- `test_pegasus_floor_tools.py:963`
- `test_silo_ladder_rung1_driver.py:757`
- `test_silo_ladder_rung1_evidence.py:769`
- `test_s8b_floor_campaign.py:6278`
- `test_backoff_extended_sweep.py:1797`
- `test_ss2pl_lock_study.py:1253`
- `test_paper_story_a1_job_contract.py:1684`
- `test_t126_pegasus_tools.py:3048`

`test_claude_transport.py:163–186` は registry のパス一覧と transport policy の bytes を pin するだけなので、本件の値変更に伴う書き換え対象ではない。

実装後の焦点走は `tools/run_tests.py` 経由。この plan 段ではテスト・計測を実行していない。

## 総括

- 採用する計算方法は **3250＋4990＋600＝8840 秒**。親の D 表は perf 候補数により 20 秒不足。
- 10800 秒案は数値整合するが、**D1971 の逐語に反する**。9000 秒との選択根拠も未確定。
- 7200 秒の予約配分案は具体化できるが、最大経路を収容するという本来の完了条件を満たさない。
- よって、両案をそのまま author に渡して完了扱いにすることは勧めない。要求枠変更を認める裁定への更新が必要。
- ファイル編集・commit・push は行っていない。