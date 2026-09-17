## 段 1 brief (2026-09-17)

**研究前進 (土台):** D2114 項 1〜4 (Silo 固定の解除、mocc 第 2 例の準備) のうち TicToc 側の準備。between-run floor driver が TicToc を名指しできる状態にし、pin 前進 (D1603 材料) と hook 移植 (T-2759) が済んだ時点で `--protocol tictoc` の実測が「driver の baseline 不在」で止まらないようにする。完了判定 = (a) `BASELINES["tictoc"]` が根拠つきで登録され、(b) 引数解析が tictoc を受理し、(c) 出力 stem が `between_run_noise_tictoc_…` に分かれ、(d) 現行 pin 511c9538 では D1373 の関門が build 前に拒否する (calls 空) ことが test と変異で立つ。**実測 (計算ノードでの floor 生成) は完了条件に含めない** (D2114 項 4 「TicToc の準備は mocc 達成の必須鎖に含めない」、D2083 項 5 の再開必要条件 = hook 移植 + pin 再承認が別途要る)。

**根拠 (brief 前に実測):**
- TicToc の stock genome = `tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1`。
  1. 現行 pin 511c9538 の `external/ccbench/cmake/Options.cmake` の cache 既定 (L20 BACK_OFF=1、L27 NWLIV=1、L28 NWOT=0、L44 PREEMPTIVE_ABORTS=1、L45 TIMESTAMP_HISTORY=1) と一致。`cc/tictoc/CMakeLists.txt` の OPTIONS はこの 5 つ + PARTITION_TABLE (死にフラグ) + SLEEP_READ_PHASE (計測撹乱、D1418 で軸外)。mocc 登録の根拠も「CMake defaults」(T-2115 の段 2 plan、`output/insights/2026-09-01/t2115-cross-protocol-impl/verbatim/s2-plan.md` L40) で同形。silo だけは p2_2 の歴史的 stock (BACK_OFF=0) で既定と異なる。
  2. `TICTOC_SPACE` (genome.py) の点であり制約 `_tictoc_no_wait_not_both` を満たす ((1,0)、D1418)。silo / mocc の既存 baseline も各 SPACE の点 (実測 True)。
  3. accepted な認定較正 record 2 件 (`output/env/pegasus/calibration/registered/calibration-9b49335d02ad4d2e.json` rr50、`calibration-cb98513996e5ae35.json` rr95、D2083 項 1、ccbench head_sha 511c9538) の `genome` と文字列一致。mocc の record 2 件も `BASELINES["mocc"]` と一致 (同形)。`tools/pegasus/certify_calibration.sh` の tictoc 軸表 (D1863) とも一致。
- 現行 pin での述語: `_protocol_source_has_trace_hook_evidence_only` = silo True / mocc False / **tictoc False** (`cc/tictoc/` に `izanagi_trace` 0 件)。引数解析は現状 `unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])` で拒否。
- 既裁定との関係: D2083 項 6 「`BASELINES` へ tictoc を足すことも行わない」は同 wave (T-2634) の scope 判断であり禁止ではない。D2114 項 4 が T-2760 として明示的に起票した。D1373 (許可リストでなく source 事実へ束縛) は不変 — tictoc を足しても関門は同じ述語のまま。

**scope (実アンカー表):**
| file | anchor | 変更 |
|---|---|---|
| `orchestrator/campaign/between_run_floor.py` | `BASELINES` L60-73 (mocc entry の直後) | `"tictoc": Genome("tictoc", {5 flags})` を追加。silo / mocc entry の bytes は不変。entry 直上に根拠 comment (Options.cmake 既定 @ pin、TICTOC_SPACE 所属、認定較正 record と同 genome、D2083/D2114 項 4、hook 移植前は関門で拒否) |
| 同 | L59 header comment | 必要なら「protocol ごとの stock baseline」の 1 文に tictoc の位置づけ (準備登録、実測は関門待ち) を追記。他は不変 |
| `orchestrator/tests/test_between_run_floor.py` | L251 `test_trace_hook_admission_is_bound_to_source_facts` | `assert not …("tictoc")` を追加 (現行 pin の source 事実へ束縛) |
| 同 | 新規 test (末尾) | (1) 全 `BASELINES` entry が `space_for(p).enumerate()` の点 (制約充足) / (2) tictoc baseline の 5 flag が `external/ccbench/cmake/Options.cmake` の `set(CCBENCH_<AXIS> <v> CACHE …)` 既定と一致 (根拠の source 束縛) / (3) `_parse_cli_args` が `--protocol tictoc` と `--protocol=tictoc` を受理し、`cicada` (SPACE はあるが baseline なし) を `unknown protocol` で拒否 / (4) `_write_out(protocol="tictoc")` の stem が `between_run_noise_tictoc_t48_…` で silo・mocc と衝突しない / (5) 現行 pin の実 source で `main(["prog","read-heavy","--protocol","tictoc"])` が ValueError "trace hook" で build 前に止まり calls 空 (mocc の L440 と同形) / (6) hook 入り fixture source で main が 0 を返し build/measure が `BASELINES["tictoc"]` を受ける (L486 と同形) |
| `orchestrator/campaign/genome.py`、`model.py`、`screening_driver.py`、`layer3_*` | — | **変更なし** |

**確定済みユーザー裁定:** D2114 項 4 (T-2760 起票、実測を完了条件に含めない)、D1373 (関門は source 事実束縛、緩めない)、D2083 項 5 (再開の必要条件)、D95 (実装面は Codex author)。scope 外 = 仮想リスク向け gate・検査・台帳・一般化、hook 移植 (T-2759)、pin 前進 (D1603)、cicada baseline、実測。

**割れうる前提:**
- (P1) 「根拠つき」の形 = code comment (短い出典列挙) + insight README の詳細。silo / mocc も code 内は 1 行 header comment のみで、詳細根拠は T-2115 insight にある。→ 親の provisional 裁定: 同形 (comment + insight)。test (2) が根拠の一部 (CMake 既定) を source へ束縛する。
- (P2) test (2) が Options.cmake を読む = pin 前進で既定が変われば赤になる。これは「根拠が現行 checkout と一致するか」の束縛であり、規律 7 の「同一性だけを理由に無効化」ではない (値の意味を検査)。→ 採用。ただし silo は歴史的 stock なので対象外、mocc も本題外で対象外 (tictoc のみ)。

**不変条件:** (a) 受理集合不変 — 現行 pin で tictoc の floor 生成は D1373 関門で build 前に拒否され、`_assert_single_tenant`・build・measure・write のいずれも呼ばれない。(b) silo / mocc の baseline bytes・出力 stem・既存 floor JSON 4 件の bytes 不変。(c) 新しい gate・validator・schema・env・argv を足さない。(d) `_protocol_source_has_trace_hook_evidence_only` の bytes 不変。(e) 規律 2 を緩めない。

**凍結 pin 閉包 (DW-O08/O09/O10):** 両 file の変更前 sha256 (`36c8325c…`、`d9c32ecb…`) は repo 内 (output 含む) に出現なし。path 参照は `output/s8b-freeze/holdout_freeze.json` の hit_paths (holdout 漏洩走査の rratio=80 / skew=0.9 / rmw=0 文字列計数) — 本変更は workload 文字列を足さないので計数不変。`test_s8b_floor_campaign.py:1738` の `use_perf` call-site 列挙は変更面外。→ O08/O09/O10 は不成立。O13 (gate 新設) 不成立。O11 (削除) 不成立。

**軽量版判定 (DW-C00 の 3 条件):** 設計択一なし (genome は証拠から一意)、正しさ防壁のコードに触れない (関門述語・reject 経路は不変、新 test が発火させるだけ)、floor 生成の受理集合不変。→ 軽量版: 段 2・3 と段 6 review 子を省き、段 5 Codex author + 段 6 fix (必要時) + 変異 matrix + 焦点走 + 受入全走。

**受入・実測環境:** 焦点走は `python3 tools/run_tests.py orchestrator/tests/test_between_run_floor.py` (§7.0.0 自動判定、login)。変異 matrix は `tools/mutation_harness.py` (container worktree、spec/out は job dir)。受入全走は `tools/dev_wave_wait.py acceptance --lease-optional`。

**分割方針:** 実装面 1 file + 1 test file → author 子 1 本。

## 段 4 裁定 (2026-09-17)

- P1 採用 (comment + insight)、P2 採用 (tictoc のみ Options.cmake 既定へ束縛)。
- **変異事前登録 (DW-M01、実装後に anchor と期待 node を probe で固定):**
  - M0 (equivalent、SURVIVED 期待): tictoc entry 直上の comment 1 行を書き換え。
  - M1 (negative): `BASELINES` から tictoc entry を削除 → killer: 引数解析受理 test (3)、hook 入り経路 test (6)。
  - M2 (negative): tictoc の `BACK_OFF` を 0 に → killer: Options.cmake 束縛 test (2)。
  - M3 (negative): tictoc の `NO_WAIT_OF_TICTOC` を 1 に (制約違反 (1,1)) → killer: SPACE 所属 test (1)、Options 束縛 test (2)。
  - M4 (negative、規律 2): `main()` の `if not _protocol_source_has_trace_hook_evidence_only(protocol):` を恒偽に → killer: tictoc 拒否 test (5) + 既存 mocc 拒否 test L440。
  - M5 (negative、protocol 別出力): `_write_out` の `protocol_part` を tictoc でも "" に → killer: stem test (4)。
  - M6 (negative): `_parse_cli_args` の `if protocol not in BASELINES:` を恒偽に → killer: cicada 拒否 (3 の負例)。
  - M7 (negative): `main()` の `baseline = BASELINES[protocol]` を `BASELINES["silo"]` に → killer: hook 入り経路 test (6) + 既存 mocc 経路 test L486。
