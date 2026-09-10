## 総括

T-2515の実装差分は回収可能です。ただし候補commitのcherry-pickや4 fileの置換ではなく、`e618883c2`を土台に`bcfd2b931`、`3dbf7ea1d`、`18704ae18`の意味差分だけを手作業で合成する必要があります。

P1の「旧file全置換不可」は正しい一方、T-2535は4実装fileすべてへ波及しており、さらに現main固有のfixture衝突が2件あります。既存8変異は定義と期待nodeを再使用できますが、旧reportの合格は再使用できません。

## 所見

- 実装元は次の3 commitです。

  - `bcfd2b931`: 両shellのexact 5値化とrratio正負例
  - `3dbf7ea1d`: `CALIBRATE_PYTHON`の前倒し、関門argv、job body実起動検査
  - `18704ae18`: interpreter fragment抽出修正

- `ad002de1b`と`ec17af5dc`はdocs・証拠側、`559bcbc29`はD1877のfixture共有化なので、4実装fileへ混ぜません。
- T-2535の`e782b7721`と`ca1e4995d`は、合計すると4実装fileすべてを変更しています。「T-1851/T-2417との重複0」はその2 waveに限ればよく、T-2535との非重複を意味しません。
- P1は次の合成固有問題を見落としています。

  1. T-2535の`_protocol_shell_observation()`はproductionの`run_condition_gate()`を実行します。関門先頭を`"$CALIBRATE_PYTHON"`へ変えると、fixtureにもfake interpreterの絶対pathを注入しなければ未束縛で赤になります。
  2. `_certify_toolchain_fragment()`の終端が`run_condition_gate()`なので、選定ブロック前倒し後は無関係なinterpreter選定まで抽出します。境界を選定ブロック直前へ狭める必要があります。

## 根拠

- [submit_certify.sh:40](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:40)のrratio関門直後には、T-2535のoffline staging precheckがあります。同precheckは保持対象です。
- [certify_calibration.sh:154](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:154)のjob側関門直後にもT-2535 precheckがあります。
- [certify_calibration.sh:405](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:405)の条件関門は現在裸の`python3`です。
- [certify_calibration.sh:552](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:552)からのoffline source複製、独立した`THIRD_PARTY_VERIFY_PYTHON`、pristine検査、[同:652](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:652)の5個のFetchContent引数はすべて保持対象です。
- [certify_calibration.sh:900](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:900)の既存選定ブロックを前へ移し、後段には最終`CALIBRATE_PATH`設定だけを残します。
- [test_pegasus_calibration_workload.py:443](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:443)はT-2535がproduction関数を実行するよう強化した箇所です。
- [test_pegasus_tools.py:255](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:255)と[同:1134](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:1134)の2つの抽出helperが移動の影響を受けます。

## 最小plan

| file:line | 合成内容 |
|---|---|
| [submit_certify.sh:8](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/submit_certify.sh:8) | usageと40行目のexact関門を`5,20,50,80,95`へ拡張。44行目以降のprotocol関門とT-2535 staging precheckは変更しない。 |
| [certify_calibration.sh:154](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:154) | job側exact集合と失敗文言だけを5値化。protocol・offline precheckは保持。 |
| [certify_calibration.sh:398](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:398) | 現900〜920行の選定ブロックをNM記録直後、関門定義前へ内容を変えず移動。関門argv先頭だけを`"$CALIBRATE_PYTHON"`へ変更。macro、meaning、timeout 300、silo限定呼出しは不変。 |
| [certify_calibration.sh:556](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:556) | `THIRD_PARTY_VERIFY_PYTHON`の独立選定と呼出しを保持。前倒し後に虚偽となる「calibrator resolver below」コメントだけを現配置に合わせる。 |
| [certify_calibration.sh:898](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/tools/pegasus/certify_calibration.sh:898) | 後段の選定本体を削除し、perf shim用初期値と`$(dirname "$CALIBRATE_PYTHON")`を含む最終PATH設定を保持。 |
| [test_pegasus_calibration_workload.py:355](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:355) | 両関門の値抽出、5値exact一致、job bodyの5正例と6非canonical負例を移植。 |
| [同:443](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:443) | production関門fixtureへ`CALIBRATE_PYTHON=<fake_python絶対path>`を追加。既存offline configure引数観測を維持。 |
| [同:1402](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_calibration_workload.py:1402) | submitter負例を8値へparameterize。dry-run helperへ`rratio`を足すが、T-2535の三者staging作成は残す。5値すべてのpre-submit、receipt、qsub exportを検査。 |
| [test_pegasus_tools.py:255](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:255) | `18704ae18`どおり、選定ブロックと後段PATH shimを別抽出して連結し、無関係行の混入を拒否。 |
| [同:1134](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2515-recovery/orchestrator/tests/test_pegasus_tools.py:1134) | toolchain fragmentの終端を`CALIBRATE_PYTHON`選定前へ変更し、toolchain検査がinterpreter選定を実行しないようにする。T-2535のdry-run staging fixtureは保持。 |

consumer閉包は次の7 fileです。旧焦点走ではなく、合成後に全て再実走する対象です。

- `orchestrator/tests/test_pegasus_calibration_workload.py`
- `orchestrator/tests/test_pegasus_tools.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_pegasus_floor_tools.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_check_docs.py`

### 既存8変異

| 変異 | 再使用 |
|---|---|
| M1 submitから95削除 | 可 |
| M2 submitから5削除 | 可 |
| M3 submitへ51追加 | 可 |
| M4 jobから95削除 | 可 |
| M5 `+`除去正規化 | 可 |
| M6先頭0除去正規化 | 可 |
| M7 README whitelist巻戻し | 条件付きで可。現在は親の未commit README差分にanchorがある。 |
| M8関門を裸の`python3`へ戻す | 可 |

M1〜M6、M8は候補と同じ改行・比較順を維持すればreplacement anchorと期待nodeを変更せず使えます。M7を含め、旧`mutation-report-final.json`の8/8結果は採用せず、合成HEADでbaseline、anchor count 1、期待failed node完全一致を再取得してください。

## 未確認

- 指示どおり編集、pytest、変異、実機jobは実行していません。
- T-1851/T-2417の動的な所有状態は射影資料外なので独立確認していません。
- 監査開始時はcleanでしたが、途中で外部から`tools/pegasus/README.md`変更とinsight一式の未追跡追加が現れました。4実装fileはcleanのままです。これらをresetせず、親のdocs作業として統合してください。
- `BACKOFF_FIXED`の既知関門は変更対象外です。accepted calibration生成は今回も主張できません。