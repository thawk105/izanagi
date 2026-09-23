## 1. 配線

- [cli.py:23–25, 84–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:23) で `result_to_dict_v3` を `core` から import し、`--json` の結果リストを同関数へ切り替える。テキスト出力は既存の `render_text` を使う。
- [pipeline.py:39–45, 654–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:39) では `core.result_to_dict_v3` を import し、reject 時の `diagnostic` だけを切り替える。従来どおり `trace_dir` を除く。
- [core.py:284–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284) の capability 射影を切り替える。`trace_dir`、framing 詳細、permutation 詳細の既存 `pop` は維持し、存在件数・詳細は残す。[core.py:194–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194) は最初に旧 `result_to_dict` を作り、v2 の `existence_violation_details is None` なら追加せず、`AnomalyV3` 以外の anomaly も変更しない。したがって v2 の辞書、挿入順、CLI の `json.dumps(..., indent=2, ensure_ascii=False)` の bytes は同一になる。[cli.py:84–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:84) [test_verifier.py:3855–3863](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3855)
- framing 詳細の除外は、詳細追加時も既存受領証 hash を安定させる裁定に由来し、permutation 詳細も同じ除外を既存試験が固定している。[docs/decisions.md:23919–23921](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/docs/decisions.md:23919) [test_t1286_commit_receipt.py:345–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_t1286_commit_receipt.py:345) **存在詳細を残すのは新しい v3 射影の意図的な digest 変更**であり、v2 の hash 安定性とは矛盾しない。ただし v3 capability は既に公開 API から作れるため、「旧 v3 digest が存在しえない」は誤り。既存試験も v3 capability を発行している。[test_verifier.py:3742–3749](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3742)
- domain `izanagi-verifier-result-v1` は据え置く案。受領証 consumer は verifier result digest を **64 桁 hex として束縛・検証**し、元の verifier 結果を再計算しない。[commit_receipt.py:384–404](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/commit_receipt.py:384) [commit_receipt.py:465–475, 549–576](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/commit_receipt.py:465) domain を変えると v2 digest も変わる。既発行の v3 digest を後から再現する用途には、この変更後の射影を適用しないことを記録する。
- 不正な `AnomalyV3` には cycle と型数の不一致、表なし reason で `ValueError` が出る。[core.py:204–216](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:204) 現状、CLI は `ParseError` だけを捕捉するので JSON 射影時の `ValueError` は外へ伝わる。pipeline も verifier 呼出しでは `ParseError` だけを捕捉し、capability 生成中の `ValueError` は外へ伝わる。[cli.py:67–78, 84–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:67) [pipeline.py:613–631](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:613) 正規の parser が作る結果についての新しい回復処理は足さず、この契約を試験で明示する。

## 2. allowlist

[ pipeline.py:409–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:409) の条件を、概念上次へ置き換える。

```python
name = os.path.basename(binary)
tpcc_stage1 = (
    name.startswith("tpcc_") and name.endswith(".exe")
    and all(flags.get(key) == value for key, value in {
        "tpcc_perc_payment": "43",
        "tpcc_perc_order_status": "0",
        "tpcc_perc_delivery": "0",
        "tpcc_perc_stock_level": "0",
    }.items())
)
if not (name.startswith("ycsb_") or tpcc_stage1):
    raise _TraceWitnessUnsupportedWorkload(binary)
```

`flags` は文字列キー・文字列値の辞書で、呼び手が `dict(flags)` を渡し、`-key=value` に展開する。[pipeline.py:146–151, 520–523, 438–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:146) 実 run の argv は上の正確な 4 値を持つ。[B0-tpcc-run.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/compute-2/B0-tpcc-run.json) 文字列比較により欠落、`"043"`、`"00"`、整数値を拒否する。特に 3 つのゼロ指定が欠けると CCBench の既定 4% に落ちる。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md) `ycsb_` 条件をそのまま残すので既存の受理集合は維持され、その他は従来の `trace-witness-unsupported-workload` になる。[pipeline.py:434–437, 558–570](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:434)

## 3. v3 の要求

TPC-C に限り、`run_verifier` が返した直後、`verify_payload` と certified 判定の前で `verify_result.integrity.existence_violation_details is not None` を要求する。[pipeline.py:613–655](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:613) この値は v3 で空リストを含む list、v2 で `None` とする既存契約なので field 追加も再 parse も不要。[model.py:498–499](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/model.py:498) [test_verifier.py:3763–3767](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3763)

v2 TPC-C は、parse 自体が成功して `certified` になりえても、この位置で abort する。理由は既存の `trace-parse-error` や `trace-witness-unsupported-workload` と意味が異なるため、`trace-schema-mismatch` を提案する。`ycsb_` が v3 を出した場合は現行どおり verifier の判定に従わせる。新条件は TPC-C 名の場合だけに適用する。[pipeline.py:626–630, 654–671](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:626) [test_verifier.py:3720–3767](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3720)

## 4. witness

`_run_trace` は stdout の `commit_counts_` と `batch_commit_counts_` を重複・非整数を拒否して読み、trace 内の C 行を数える。[pipeline.py:330–350, 448–460](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:330) executor は計数の欠落と非ゼロ batch を先に拒否し、`commit_counts_` を `expected_commits` として verifier へ渡す。verifier は観測取引数と完全一致を要求し、不一致なら `clean=False`、pipeline は `indeterminate` で abort する。[pipeline.py:598–625, 654–666](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:598) [core.py:61–74](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:61) TPC-C でも同じ経路を通る。実 run は C=36,156、両 stdout 計数は 36,156 と 0。[B0-tpcc-run.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/compute-2/B0-tpcc-run.json)

既存の fake binary 試験と同じく実 `_run_trace` に `tpcc_fake.exe` を渡し、完全な v3 frame を書く脚本を用意する。[test_campaign.py:7481–7502](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7481) (b) 末尾 C frame、(c) 最大 txid の全 frame、(d) 片方の `trace_*.log` 全体を落とし、stdout の元の commit 数を維持する。各件で `expected_commits > observed_commits`、`indeterminate`、COMMIT 不発を確認する。[test_campaign.py:7382–7414](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7382) (a) は CCBench 側の計数修正の対象で、repo の合成試験には帰属させない。[設計 §3.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md)

## 5. §6.1 の対応表

| 段 1 の行 | 現状と追加案 |
|---|---|
| 表識別 | 既存 `test_v3_table_identity_separates_edges` は、表を含む key の分離と辺集合 `{(0,1)}` を直接検査する。**参照グラフとの辺集合の一致**として使える。表を落とした変異の具体的な余分な辺も assertion に足す。[test_verifier.py:3475–3492](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3475) |
| lost update | v3 の District（表 1）で 2 取引が genesis の同じ版を読み、同じ行を順に `U` する合成 fixture を追加。期待辺は `A→B` の ww と `B→A` の rw、cycle、non-serializable。既存 v2 の lost update 例だけでは v3 の証拠にならない。[設計 §6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md) [test_verifier.py:3378–3386](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3378) |
| 手書き G2 | `test_v3_cycle_reports_tables_and_tx_types` に表 0・9 の双方向 rw、取引種別、構造化出力が既にある。v3 parser と cycle 検出の control と記し、表識別の control に重複計上しない。[test_verifier.py:3390–3396, 3517–3542](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3390) |
| genesis の誤用 | `test_v3_existence_negative_pairs` が `read-unborn-genesis` と一行修正の正例を既に持つ。存在履歴の indeterminate に帰属する。[test_verifier.py:3903–3927](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3903) |
| si | 段 1 の対象外。設計は si の読みが native set から消えると記す。[設計 §3.4・§6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md) |
| witness | v2 の基礎試験はあるが、TPC-C 名で (b)(c)(d) を実 `_run_trace` から通す試験がない。§4 の案を追加。[test_campaign.py:7382–7414, 7481–7502](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7382) |
| 正常対照 | v3 の正常履歴と capability 認定は既存。lost update と同じ表・key・操作を直列にした対照、および pipeline の 57:43・X/P・witness を備えた認定例を追加する。[test_verifier.py:3720–3749, 3930–3949](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3720) |

実 CC 案は `patches/broken-silo-norw-validation.patch` が `cc/silo/transaction.cc` の読み検証を無効にするので、**対象箇所は TPC-C も使う silo** と静的に分かる。[broken-silo-norw-validation.patch:1–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/patches/broken-silo-norw-validation.patch:1) ただし現 pin に v3 emitter はなく、v3 source への patch 適用と異常 schedule の発生はこの静的読解では未確認。計算ノード build・run が必要で、出ても schedule と cycle の独立帰属を調べる費用がある。まず合成 fixture を段 1 の必須 control とし、実 CC は追加証拠として別扱いにする。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md) [設計 §6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md)

## 6. pipeline 側の段 1 正例・負例

`_execute_verification_repetition` の `trace_runner` seam に、合成 v3 を `trace_dir` に書き、stdout 相当の `_TraceRunResult` を返す runner を渡す。`verifier_runner` は実 `verify_trace_dir_with_capability` を使い、既存試験の build binding helper で genome・source evidence・build admission を作る。[pipeline.py:484–508, 520–524, 613–625](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:484) [test_campaign.py:6044–6071](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:6044)

正例は `tpcc_silo.exe`、4 flag、v3 の直列 trace、C 数と同数の witness、batch=0、X/P を満たす source binding で `certified` と capability を確認する。負例は v2 trace の `trace-schema-mismatch`、flag 違いの事前 `trace-witness-unsupported-workload`、C/witness 不一致の `indeterminate`、存在違反の `indeterminate` と `verify.integrity.existence_violation_details` を確認する。[pipeline.py:558–570, 598–671](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:558) [test_verifier.py:3903–3927](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3903)

`_eval` は WAL と evaluate の経路を通せるが `_run_trace` と build/source 解決を fake 化している。[test_campaign.py:5840–5849, 6000–6071](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:5840) 一方、現 production buildcache は YCSB binary を作るため、**現 pin のまま full production evaluate が TPC-C を build・選択して certified になる試験は本単位では作れない**。executor 結合試験と、親の repo 外実 trace probe の主張を区別する。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md)

## 7. consumer の静的列挙

変更箇所の直接 consumer は、CLI `main`、pipeline executor とその `evaluate` 側呼出し、capability 発行、受領証発行・検証である。[cli.py:62–92](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/cli.py:62) [pipeline.py:2162–2175](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:2162) [core.py:381–414](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:381) [commit_receipt.py:534–580](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/commit_receipt.py:534) `_parse_commit_witness` は campaign の silo policy、S2 calibration と `tools/pegasus/probes/t1683_rr5_cost_probe.py` も呼ぶが、この関数自体は変更しない。[pipeline.py:347–350](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:347)

bytes の既存固定点は verifier の凍結 JSON、v3/v2 射影同値、pipeline の WAL 診断・witness payload、capability hash の詳細除外である。[test_verifier.py:1404–1411, 3855–3863](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:1404) [test_campaign.py:7382–7427](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7382) [test_t1286_commit_receipt.py:345–416](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_t1286_commit_receipt.py:345) 新試験では **CLI 実 JSON bytes** と v2 capability の `_result_sha256` を切替前後で比較する。旧 `result_to_dict` を使う YCSB 専用の `silo_ladder_rung1` 再計算等は今回の配線対象にしない。[silo_ladder_rung1.py:3056](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/silo_ladder_rung1.py:3056)

## 8. 変異の候補

| 変異 | 殺す試験案・既存の基礎 |
|---|---|
| CLI を旧射影へ戻す | 新 `test_cli_v3_json_projection`。表・取引種別・存在詳細を検査。[core.py:194–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194) |
| pipeline 診断を旧射影へ戻す | 新 `test_tpcc_existence_abort_has_v3_diagnostic`。[pipeline.py:654–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:654) |
| capability を旧射影へ戻す | 新 `test_v3_capability_digest_binds_existence_and_tables`。[core.py:284–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:284) |
| 存在詳細を digest から `pop` | 同試験で、詳細だけ変えた verifier 発行結果の digest 差を検査。[core.py:197–203, 284–292](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:197) |
| payment 比較を外す | 新 `test_tpcc_allowlist_rejects_each_flag` の payment=44。[pipeline.py:434–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:434) |
| 他の 3 flag の一つを省略許容 | 同試験の各欠落例。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md) |
| 文字列を数値化して比較 | 同試験の `"043"`、`"00"`。[pipeline.py:146–151](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:146) |
| TPC-C の v3 要求を外す | 新 `test_tpcc_v2_trace_rejected_after_verify`。[test_verifier.py:3763–3767](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3763) |
| `ycsb_` 受理条件を消す | 既存 `test_run_trace_parses_commit_witness_from_stdout`。[test_campaign.py:7481–7502](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7481) |
| witness 引渡しを消す | 新 TPC-C (b)(c)(d) と既存 `test_pipeline_tail_loss_witness_reaches_verifier`。[test_campaign.py:7382–7414](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7382) |

## 9. 規模と分割

見積りは `core.py` 1–3 行、`cli.py` 2–4 行、`pipeline.py` 20–35 行、`test_verifier.py` 80–130 行、`test_t1286_commit_receipt.py` 25–45 行、`test_campaign.py` 130–220 行。合計約 **260–440 行**。fixture・新 module は作らず、既存 v3 frame helper と fake binary の流儀を使う。[test_verifier.py:3376–3386](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3376) [test_campaign.py:7481–7502](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_campaign.py:7481)

A（`core.py`、`cli.py`、verifier・受領証試験）と B（`pipeline.py`、campaign 試験）の所有 path は素集合で成立する。B の新診断試験は A の `result_to_dict_v3` 配線を前提にするため、**A の射影契約を先に固定してから B を結合**する。一本化が必須となる共有ファイル編集は見当たらない。[core.py:194–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194) [pipeline.py:654–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:654)

## brief への異議

- 「v3 受領証はこれまで作られえない」を domain 維持の理由にしてはいけない。公開 API と既存試験で v3 capability は既に発行可能。[test_verifier.py:3742–3749](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/tests/test_verifier.py:3742)
- P2 の `tpcc_` **前方一致だけ**では `tpcc_fake.sh` 等も通る。実 binary の `.exe` まで条件に含め、試験用 fake executable も `.exe` 名にする。[pipeline.py:434–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:434) [B0-tpcc-run.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-ccbench-v3/evidence/compute-2/B0-tpcc-run.json)
- brief の完了判定にある「pipeline が実 TPC-C run を通す」は executor と実 verifier の結合なら本単位で検証できるが、現 pin の buildcache を含む production `evaluate` 全体については主張できない。pin 前進と workload/build 選択は scope 外と明記されている。[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit5-v3-wiring/s1-brief.md)

## 総括

v3 射影の差し込み先は CLI JSON、pipeline の reject 診断、capability digest の 3 箇所。v2 は `result_to_dict_v3` の分岐により辞書と bytes を維持する。[core.py:194–218](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/core.py:194)
TPC-C は `.exe` 名と 57:43 の正確な 4 flag で trace 前に絞り、verifier 後に既存の存在詳細 field で v3 を要求する。[pipeline.py:409–440](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:409) [model.py:498–499](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/verifier/model.py:498)
witness は既存の完全一致経路を使い、TPC-C 名の欠落 3 例を追加する。[pipeline.py:598–625](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/orchestrator/campaign/pipeline.py:598)
§6.1 の主な不足は v3 lost update の合成例、直列対照、pipeline 結合例。実 CC での再現は追加証拠として扱う。[設計 §6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2854-unit5-v3-wiring/output/insights/2026-09-21/tpcc-trace-certification-design/README.md)
未決事項は、v2 TPC-C 用の提案 abort reason `trace-schema-mismatch` の採用と、実 CC 追加走の要否。実装・テスト実行は行っていない。