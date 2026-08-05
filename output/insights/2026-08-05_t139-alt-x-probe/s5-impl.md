実装を完了しました。repo の変更は指定された 3 ファイルだけで、docs・policy・submodule・output は変更せず、commit/qsub/qstat も実行していません。

### 変更ファイル

- [t139_positive_control.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:1)
  - mode2 を modeX へ改名。
  - identity global を全削除。
  - `alignas(64)` の mutex wrapper × 4 と static assert。
  - 先頭・中央・末尾・長さ・storage の固定回数 mixer。
  - mode1/modeX とも stock と同式の CAS を mutex 内で iteration 当たり 1 回実行。
  - `ADD_ANALYSIS` build のみ、共有 `steady_clock` と固定 1500 ms 境界による 2-window liveness を出力。

- [t139_positive_control_probe.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.sh:1)
  - `stock/mode1/modeX` × performance/live の 6 build。
  - CMake cacheと `transaction.cc` の実 compile argvを保存・exact 検査。
  - mutex global と trace symbol の nm 補助検査。
  - liveness を exact 576 cell 化。
  - fixed balanced schedule、exact 30-row verdict。
  - `limited_screen` 36/36、job 外 process・affinity・pre/post snapshot。
  - attempt rate、abort rate の副次診断。
  - runtime hash/pin witness。
  - verdict・row・liveness・compile argv の正例/拒否 self-check。

- [t139_positive_control_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:1)
  - dependency rootを必須化し、非 symlink・git root・pin・cleanを検査。
  - policy top-level pinとの一致を検査。
  - gflags/glogを `git archive <pin>` から不変 snapshot 化。
  - tree SHA、archive SHA、root realpath等を witness 化。
  - 3290秒の内部予算、3300秒の絶対 deadline、3600秒 walltime。
  - probe 3 bytesがHEADと異なる状態での実走を拒否。

検査用に [s5-stripe-mixer-check.cc](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s5-stripe-mixer-check.cc:1) と実行ファイルをrepo外へ作成しました。patch dry-run用CCBenchコピーは検査後に削除済みで、元submoduleは無変更です。コピー自体は残っていませんが、元から再作成できます。

### 受理・拒否挙動の差

現行は、W1/W2ごとのarm総数が各5で `mode1 < mode2 < stock` なら受理します。repの欠落と重複が相殺された形、未知row、余分rowを拒否できず、livenessは1窓288 cell、identity symbol中心のbuild識別、runtime `shuf`、限定的な事前solo検査でした。

変更後も、正常な性能標本に対する厳密分離式は `mode1 < modeX < stock` のままです。一方、未知workload/arm、rep範囲外、重複・欠落cell、余分rowを拒否します。さらに576-cell liveness、compile argv exact、nm補助検査、limited screen 36/36が揃わなければ拒否します。これはprobe内部のmalformed-input拒否強化であり、Izanagiのcertified受理集合や既存gateは変更していません。

### 波及可能性

- 所有外caller:
  - PBS投入者は従来のthird-party rootに加え、`IZANAGI_T139_DEPENDENCY_SOURCE_ROOT` が必要。
  - PBS→driver間にdeadlineとdependency witness envが追加。
  - driver→patch→CCBench `transaction.cc` の関係は維持。
- 共有fixture:
  - `hooks/guard_bash.py` の両scriptに対する`unknown`分類は不変。
  - `orchestrator/tests/test_hooks.py` のpath分類期待値にも変更なし。
  - `policy.json` は読み取りのみ。
- consumer:
  - raw schemaは `mode2`→`modeX`、liveness 288→576、`solo-checks`→`limited-screen`、nm列変更、diagnostics追加となるため、手動collectorは新schemaへの対応が必要。
  - repo検索ではこのraw schemaを直接parseするコードconsumerは見つかりませんでした。
  - generic `transaction.cc` はTPCC/BoMB/SBoMBにも使われるため、親による計算ノードcompile smokeが必要です。

### 実行した検査

| 検査 | 結果 |
|---|---|
| `bash -n ...probe.sh` | rc=0 |
| `bash -n ...probe.pbs` | rc=0 |
| CCBenchコピーへの `patch -p1 --dry-run --forward` | rc=0、`transaction.cc` 適用可能 |
| `probe.sh --self-check` | rc=0、4系統の正例accepted・拒否例rejected |
| `g++ -std=c++17 -O2 -Wall -Wextra ...` | rc=0、warningなし |
| `python3 tools/check_codex_agents.py` | rc=0 |
| `python3 tools/check_docs.py` | rc=0、違反なし |
| `git diff --check` | rc=0 |
| 最終`git status` | 指定3ファイルのみmodified |

Mixer実測:

| key族 | bucket 0/1/2/3 | 最大占有率 |
|---|---:|---:|
| YCSB 8 byte | 25063 / 24974 / 24956 / 25007 | 25.06% |
| 共通prefix+suffix・同一長 | 21330 / 24390 / 23040 / 21240 | 27.10% |
| TPCC相当16 byte | 23914 / 25604 / 25712 / 24770 | 25.71% |

空keyはstripe 0、1 byte keyはstripe 1で正常終了しました。`align=64`、wrapper size=64、gates=4です。

未実施:

- CCBench本体build、TPCC/BoMB/SBoMB compile smoke
- performance benchmark
- 実binaryのcompile argv/nm witness
- 実576-cell liveness、limited screen、dependency archive end-to-end
- PBS/qsub実走、全submission集約
- pytest
- commit後provenance監査

いずれも計算ノードまたは親の段6以降で行う項目で、現段では「実装済み・未実走」です。

### V-1〜V-3対応

| 項目 | 状態 |
|---|---|
| V-1.1 modeX改名・相互排他 | 実装 |
| V-1.2 identity global削除 | 実装 |
| V-1.3 4 stripe・alignas/static assert | 実装 |
| V-1.4 固定回数3窓mixer | 実装、小片実走済み |
| V-1.5 2-window liveness | 実装・本体未実走 |
| V-1.6 stock同式CAS・追加CASなし | 実装、静的確認済み |
| V-2.1 3 arm×live | 実装 |
| V-2.2 compile argv exact・nm補助 | 実装・実binary未実走 |
| V-2.3 fixed schedule | 実装 |
| V-2.4 exact 30-row | 実装・self-check済み |
| V-2.5 576-cell liveness | 実装・self-check済み |
| V-2.6 limited screen | 実装・未実走 |
| V-2.7 dependency witness | 実装・未実走 |
| V-2.8 attempt/abort診断 | 実装・未実走 |
| V-2.9 self-check fixture | 実装・8/8実走済み |
| V-3.1 dependency root検査 | 実装・未実走 |
| V-3.2 archive snapshot/tree/archive SHA | 実装・未実走 |
| V-3.3 top-level pin一致 | 実装・未実走 |
| V-3.4 deadline/timeout予算 | 実装・未実走 |

### P-A〜P-G対応

| 項目 | 状態 |
|---|---|
| P-A 候補・arm・workload・rep・hash/pin | 実装。runtime witness化 |
| P-B 固定schedule | 実装 |
| P-C primary受理条件 | 実装。性能式不変、付帯条件をexact化 |
| P-D 副次診断 | 実装。verdictから独立 |
| P-E 失敗閉表 | 部分実装。exact true/falseを終端化しjob内retryなし。submission間retry・全ID集約は親責務 |
| P-F 走行後分岐 | 親責務。driverはexact verdictのみ生成しqualificationを宣言しない |
| P-G 走行前commit | 部分実装。PBSがprobe bytes≠HEADを拒否。commit自体は明示禁止のため未実施し、統合commitは親責務 |

## 総括

段4のV-1〜V-3はすべてコード化しました。P-A〜P-Dはprobe内に実装し、P-E〜P-Gのjob内で強制可能な部分も閉じています。submission横断判断、統合commit、計算ノードbuild・実測は権限どおり親へ残しています。