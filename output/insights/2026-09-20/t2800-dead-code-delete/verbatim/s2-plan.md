## 削除手順 (file:line)

基準は `947fd160ab44e6ae82b6eab56ee8d70813fda31d`。worktree は clean。必読射影はすべて読取可能だった。以下の行番号は変更前のもの。

**段 3 には渡せるが、17 file 全削除を author に確定指示する前に P1 の解消が必要。** 技術的な削除手順と、裁定上の留保を分けて示す。

削除候補の全体アンカーは次のとおり。

| file | 全削除範囲 |
|---|---:|
| `orchestrator/campaign/p2_5.py` | 1–167 |
| `orchestrator/campaign/s6_amendment_20260713_fence.py` | 1–117 |
| `orchestrator/manual_probes/t1994_capdrop_probe.py` | 1–99 |
| `orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py` | 1–100 |
| `orchestrator/manual_probes/t1994_rootview_probe.py` | 1–100 |
| `orchestrator/manual_probes/t1994_seccomp_probe.py` | 1–96 |
| `orchestrator/campaign/backoff_requested_us.py` | 1–1262 |
| `orchestrator/tests/test_backoff_requested_us.py` | 1–1221 |
| `orchestrator/campaign/s6_canary_rename.py` | 1–312 |
| `tools/insights_date_layout.py` | 1–411 |
| `orchestrator/tests/test_insights_date_layout.py` | 1–447 |
| `tools/migrate_output_gzip.py` | 1–885 |
| `orchestrator/tests/test_migrate_output_gzip.py` | 1–473 |
| `tools/plotting/plot_t2266_tail_mechanism.py` | 1–625 |
| `orchestrator/tests/test_plot_t2266_tail_mechanism.py` | 1–505 |
| `tools/t1434_t1222_science_slice.py` | 1–1282、P1 留保 |
| `orchestrator/tests/test_t1434_t1222_science_slice.py` | 1–521、P1 留保 |

author の手順は次の順序とする。commit・docs 編集は行わない。

```bash
git rm -- \
  orchestrator/campaign/p2_5.py \
  orchestrator/campaign/s6_amendment_20260713_fence.py \
  orchestrator/manual_probes/t1994_capdrop_probe.py \
  orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py \
  orchestrator/manual_probes/t1994_rootview_probe.py \
  orchestrator/manual_probes/t1994_seccomp_probe.py \
  orchestrator/campaign/backoff_requested_us.py \
  orchestrator/tests/test_backoff_requested_us.py \
  orchestrator/campaign/s6_canary_rename.py \
  tools/insights_date_layout.py \
  orchestrator/tests/test_insights_date_layout.py \
  tools/migrate_output_gzip.py \
  orchestrator/tests/test_migrate_output_gzip.py \
  tools/plotting/plot_t2266_tail_mechanism.py \
  orchestrator/tests/test_plot_t2266_tail_mechanism.py
```

次の 2 file は **P1 が削除可に解決した場合だけ**追加する。未解決なら両方とも byte 不変で残す。

```bash
git rm -- \
  tools/t1434_t1222_science_slice.py \
  orchestrator/tests/test_t1434_t1222_science_slice.py
```

共有 test の必須削除は **6 エントリ行**。brief の「7 行」は現物と一致しない。

`orchestrator/tests/test_ccbench_spawn_sites.py:75`：

```text
74      # and a mandatory timeout; stdout is diagnostic-only requested-us data.
75      ("campaign/backoff_requested_us.py", "<module>._run_rep"): 1,
76      # Correctness trace witness owned by pipeline's verifier path.
```

同 file `:215–218`：

```text
214     ("campaign/s5_permutation_coverage.py", "<module>._verify"): 1,
215     ("campaign/s6_canary_rename.py", "<module>.export_stock"): 3,
216     ("campaign/s6_canary_rename.py", "<module>.git_apply"): 1,
217     ("campaign/s6_canary_rename.py", "<module>.normalize_cxx"): 1,
218     ("campaign/s6_canary_rename.py", "<module>.verify"): 1,
219     ("campaign/s6_proposal_rounds.py", "<module>.call_headless"): 1,
```

`orchestrator/tests/test_p3_build_authority_cli.py:152`：

```text
151     "backoff_profile.py": "BACKOFF_PROFILE",
152     "backoff_requested_us.py": "BACKOFF_PROFILE",
153     "backoff_repro.py": "BACKOFF_REPRO",
```

spawn 表は `test_ccbench_spawn_sites.py:31–34` の **calibrator と campaign 両ディレクトリ**を `:420–432` で再帰走査し、`:2840–2847` で Counter の exact 一致を要求する。削除する 5 エントリは launch 数では **7**（1＋3＋1＋1＋1）。別の固定合計値の更新は不要。`:4100–4107` の measurement 側比較も同じ表を使うため追随する。

`MACHINE_CALLERS` は `test_p3_build_authority_cli.py:1210–1221` で表を巡回して実ファイルを読む型。行削除で足り、別の件数 pin はない。`:1224–1264` の manual materializer／registry 比較は別集合なので変更しない。

なお spawn file `:73–74` は削除する requested-us 行の専用コメントである。

```text
73      # Fixed balanced argv under the compute-site bench lock, shell disabled,
74      # and a mandatory timeout; stdout is diagnostic-only requested-us data.
```

残すと pipeline の説明に誤接続する。段 3 で scope を **「pin 6 行＋付属コメント 2 行」**へ訂正することを推奨する。現在の「pin 行だけ」を厳密適用する author は、確定前にコメントまで削らない。

親の docs 追随は `orchestrator/tests/README.md:138` のみ。

```text
137 - test_env_contract.py
138 - test_insights_date_layout.py
139 - test_layer3_report.py
```

## 赤になる gate と追随

| gate／アンカー | 削除時の影響と必要な追随 |
|---|---|
| `test_ccbench_spawn_sites.py:2840` `test_reviewed_process_launch_inventory_is_recursive_and_exact` | 表が残れば、消えた launch が expected に残って赤。上記 5 エントリ削除。 |
| `test_p3_build_authority_cli.py:1210` `test_machine_callers_use_closed_generator_receipts` | `:1212` で削除 file の `read_text()` が失敗。`:152` 削除。 |
| `test_plain_runner_coverage.py:77` `test_allowlist_has_no_stale_or_self_runnable_entries` | `:81–83` が README の不在 file を検出。親が README `:138` を削除してから統合焦点走する。 |
| `test_p3_build_authority_cli.py:649` `test_tracked_python_coder_authority_ast_closure_is_exact` | 未 stage 削除だと `:213–223` の `git ls-files` に残り、`:667` で読取失敗。最初から `git rm` を使う。 |
| `tools/run_tests.py:784–819` | **受入実行で**未 stage 削除を検出し rc=13。`:787–788` により targeted run はこの gate の対象外。焦点走が通っても DW-O11 の証明にはならない。 |
| `tools/check_ai_provenance.py:75–85,1717–1722,1794–1799` | 削除も実装変更・staged diff の対象。削除だから provenance 不要とはならない。親の commit 後に通常の監査を行う。対象 module の常時実在を要求する特別登録は見つからない。 |
| `tools/check_docs.py:129–170,6767–6775` | living docs のパス実在を検査する。削除候補への該当 living-doc 参照は検索で見つからない。歴史記録の参照を一括修正する必要はない。 |

赤を予想しないが、明示確認すべき箇所は次のとおり。

- **台帳 coverage**：`test_acceptance_schedule_order.py:704–715` は `covered / len(rows)` を計算する。台帳 entry 数を分母にせず、stale entry の存在も禁止しない。削除 5 test に対応する台帳 entry は実数で **36＋62＋12＋22＋30＝162**。台帳総数は 24,379。
- **coverage の限界**：実 collection をしない本段では、現在の HEAD の正確な分母・covered 数は未確定。削除前を `C/N` とすれば、162 node がすべて収集・covered だった場合の削除後は `(C−162)/(N−162)`。90% 維持の条件は `C−0.9N ≥ 16.2`。旧測定の収集数 25,381（`output/insights/2026-09-19/test-inventory-prune/README.md:21,35`）と台帳全件対応を仮定すれば約 96.03% だが、これは現 HEAD の実測値ではない。**追随として台帳を編集せず、親が G5 を実走して確定する。**
- **cohort2 import**：`test_t2187_adaptive_const_probe.py:24–26` の import と `:1974–1980` の seed 集合比較は保持 module を参照しており無傷。
- **閉包 47**：`test_p3_b4_wiring_probe.py:324–327` は全 campaign module 数ではない。`p3_b4_wiring_probe.py:1083–1099` の指定 root からの静的 import 閉包である。削除対象への incoming import は見つからず、47 を変更する根拠はない。
- **materializer admission 等**：`orchestrator/campaign/materializer_admission.py`、`tools/pegasus/admission_registry.json`、hooks、設定、残存 tests を path・stem・部分名で検索し、上記以外の対象 file 登録を検出しなかった。
- **import 例外台帳**：`test_campaign_import_invariant.py:1222–1286` は exact な例外台帳を検査するが、削除集合の該当 entry は見つからない。追加の削除追随は不要と判断する。

## consumer 再確認

検索範囲は repo の `orchestrator/`、`tools/`、`hooks/`、`.claude/`、`.codex/`、設定・文書と、output の実行 script。完全 path、dotted module 名、短い stem、`requested_us`／`canary_rename` 等の部分名、`import_module`／`__import__`／`spec_from_file_location`／`run_module`／`run_path`、module 探索関数を確認した。短名検索は `python -m` と subprocess argv の両方を含む。

| 削除候補 module | 検出した consumer と判定 |
|---|---|
| `backoff_requested_us.py` | 専用 test `:24`、共有 2 表に加え、**`output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh:383` に実呼出しあり**。これは凍結された歴史再現 script。現行 operational consumer は見つからない。「consumer ゼロ」ではなく「現行 consumer なし」と記す。 |
| `s6_canary_rename.py` | spawn 表 `:215–218` と歴史資料。別の import／argv／動的 loader の入力は見つからない。自身の `:311–312` は `main()` を起動するだけ。 |
| `insights_date_layout.py` | 専用 test `:12` の import、`:180,209,228,246` の短名 `sys.argv` 設定。残存 code の consumer は見つからない。自身の `:410–411` が CLI 入口。 |
| `migrate_output_gzip.py` | 専用 test `:15–16` が path を組み立て、**`spec_from_file_location()` で動的 load**する。対削除に含まれる。残存 consumer は見つからない。自身の `:884–885` が CLI 入口。 |
| `plot_t2266_tail_mechanism.py` | 専用 test `:25–27` の **file-location 動的 load**。図 provenance `:46–47` に path／SHA-256。残存実装からの load は見つからない。自身の `:624–625` が CLI 入口。 |
| `t1434_t1222_science_slice.py` | 専用 test `:12` の import と過去の変異 spec／記録。現行 operational consumer は見つからないが、P1 の維持指定は別問題。自身の `:1274–1275` が CLI 入口。 |

一般的な動的 loader も確認した。

- `axis_mocc_temperature.py:179–185` の文字列組立て import は `axis_*.py` 限定で、候補は入らない。
- `p3_b4_wiring_probe.py:1261–1267` は静的閉包の module 名だけを import する。
- `s8c_preregistration.py:1843–1845,1876–1878` は固定した evidence／projection module。
- `tools/pegasus/run_probe.py:32–35` は固定した `env_attestation`。
- 実在する package `__main__` と CLI 入口に、候補を自動起動する辺は見つからない。

任意の実行時文字列生成まで不存在を証明したわけではない。定数結合を AST で一括走査する追加コマンドは `guard_bash` に拒否されたため、その走査済みとは数えず、読取専用の `rg` と loader 現物確認で補った。

親の output pin 走査は `pin-closure-output.done` が `0`。図スクリプトの SHA-256 hit があるため、「output 側も hash hit ゼロ」とは報告しない。

## 残す 9 対の反証

| module | 判定と現物の根拠 |
|---|---|
| `backoff_counterfactual_analysis.py` | **一致**。`:20–25,332,582` の測定／解析事前登録 pin と seed 検査は、`docs/backoff-counterfactual-preregistration.md:345–351` の義務に対応。T-2586 README `:14–20,212–216` も consumer として扱う。 |
| `backoff_counterfactual_cohort2_analysis.py` | **補強**。`:20–25,77,404,674` の cohort 専用束縛に加え、残存 `test_t2187_adaptive_const_probe.py:24–26,1974–1980` が直接依存する。 |
| `backoff_nonmonotonicity_analysis.py` | **一致**。T-2583 の `verbatim/probe.py.txt:43–44` が動的 load、T-2635 の `verbatim/probe_t2635.py.txt:183` が analyzer の既定 path に指定。両 README `:380`／`:202` が同一 hash の無改変利用を記録する。 |
| `backoff_sweep_report.py` | **一致**。`docs/phase2.md:184` の射影器の位置付け、T-2702 README `:52,93` の consumer／現存挙動の記述と一致。`docs/orchestrator-design.md:117` の材料レポート規約にも対応。 |
| `floor_liveness.py` | **補強**。`:20,539,575,607` が checkpoint/index/journal を読む診断 consumer。`s8b_floor_campaign.py:123,7295,7644` と shell 2 本は **floor_liveness を呼ぶのでなく producer の floor_job_checkpoint を使用**する。保持理由はこの producer–consumer 関係として記述する。 |
| `mocc_trace_pair_anchor.py` | **一致**。`:27–31,342–379` の schema／署名済み外部 pin 検証は `docs/decisions.md:37465–37479` の D1110 を実装する。checker が anchor を import するという逆向きの主張は不要。 |
| `t1994_readonly_snapshot_qualification.py` | **一致**。`:716–718` の errno 連言を `test_buildcache_v2.py:5787,5796` が直接検査。現行機構でないとはいえない。 |
| `tools/mutation_fanout.py` | **一致**。D433 `docs/decisions.md:18009–18023` が実行不能・gate 緩和禁止を確定し、`docs/phase3.md:1997` に T-1177 が残る。`:35` の import は driver → contract であり、逆向き参照を保持理由に使っていない点も正しい。 |
| `tools/verify_paper_story_a1_balanced_sizing.py` | **一致**。事前登録 README `:278–291` が道具の bytes を束縛。`test_paper_story_a1_balanced_sizing.py:21–22` は generator と verifier 両方の共有 test。専用 test ごと削る前提も成立しない。 |

追加削除を支持する反証は **0 対**。根拠の一部を補正しても「3 条件を確認できなければ残す」という裁定は変わらない。

## (P1)〜(P3) と副作用

**P1：優先断定を反証。削除可否は条件付き。**

`test_t1434_t1222_science_slice.py:409–442` は外部 jobs path 集合の exact pin であり、`output/insights/2026-09-19/test-inventory-prune/inventory/list-D.txt:283` に掲載される。

一方、D2172 項 6 は `docs/decisions.md:68612` で「確認済み 15 関数も未確認候補 246 関数も削らず」と明記する。項 5 `:68594–68597` は残り 15 対の**条件付き削除**であって、この test の削除や項 6 の supersede を明記していない。一次棚卸しの「対象集合への掲載」は「無条件の削除指定」と同義ではない。

したがって、brief の「項 5 が優先」は本段の現物確認だけでは支持できない。段 3 でこの重なりを解決する。未解決時の author 指示は **science-slice の module/test 両方を残す**。test 一部移植や新 gate は不要。

**P2：支持。ただし失われる検査範囲を正確に記録する。**

専用 test `:1104–1143` は凍結 job-body の予算・site・失敗ログの pin。`:1074–1089` も driver 呼出し回数を検査する。被検体は現行 module だけではないが、対削除によりこれら歴史 script の継続検査も消える、という明示的な scope として整合する。成果物そのものは変更しない。

**P3：支持。patch は完全な孤児ではない。**

`condition_meaning_gate.py:143–146` が patch を引き続き登録し、`test_ccbench_spawn_sites.py:2885–2898` が patch define 集合と registry の一致を検査する。driver が消えても patch／DEFINE_SPECS は残す。patch まで消す追随は誤り。

その他の副作用：

- 図 provenance `output/insights/2026-09-07_backoff-tail-mechanism/fig_tail_mechanism.provenance.json:46–47` の source path/hash、歴史 job-body `:383`、過去の変異 spec は保持する。現在の checkout での再実行可能性は失われるが、記録を書き換えない。
- `mutation_fanout_contract.py` は残存 driver `tools/mutation_fanout.py:35` が使用するため、本案では新たな孤児にならない。
- 台帳 stale 162 entry は保持する。`conftest.py:1595–1603` は JSON 内部の件数整合、`:1739–1758` は収集 item からの lookup。`tools/acceptance_shards.py:392–404` も records 起点なので余剰 key は使わない。
- P1 の対を保持する場合、削除は **15 file／6,820 行／台帳 132 node**。17 file 案は **8,623 行／162 node**。台帳秒の差引はそれぞれ 10.341 秒／11.580 秒であり、wall 短縮とはしない。
- 「残る test の受理集合は不変」は厳密には表現を修正すべき。共有 exact gate の期待集合は削除 site 分だけ変わる。**残存 site に課す述語を維持する**、と記録する。

## 焦点走と受入の予想

親が README 追随と staging を済ませ、`tools/run_tests.py` 経由で次を実走する。

```text
orchestrator/tests/test_ccbench_spawn_sites.py
orchestrator/tests/test_p3_build_authority_cli.py
orchestrator/tests/test_plain_runner_coverage.py
orchestrator/tests/test_acceptance_schedule_order.py
orchestrator/tests/test_t2187_adaptive_const_probe.py
orchestrator/tests/test_p3_b4_wiring_probe.py
orchestrator/tests/test_campaign_import_invariant.py
```

前半 5 file は brief の集合。後半 2 file は閉包 47 と import 例外台帳を直接確認するための追加。P1 を保持側で解決した場合は `test_t1434_t1222_science_slice.py` も残存対象として受入に含める。

実走場所は親の runner 判定に委ねる。続けて必要な docs／Codex agents 検査、親の commit 後に provenance 監査、受入全走を行う。author は commit しない。

予想される赤は、優先順に次のとおり。

1. 親 README 追随前の allowlist stale。
2. spawn 表または `MACHINE_CALLERS` の削除漏れ。
3. 未 stage 削除による受入 preflight、または tracked-source AST scan の読取失敗。
4. G5 内部の collection 失敗、または既存の台帳不足による coverage 赤。本削除を理由に台帳や 90% 閾値を変更しない。
5. 歴史資料・外部入力に由来する既存の赤。削除由来と混同せず、具体的な nodeid／例外で切り分ける。

本段は静的確認のみ。pytest 緑、47 の実走確認、現 HEAD の coverage 合格は報告していない。

## 変異 (負例) 案

各変異は追随済み baseline に対し、**一つの追随だけを欠落**させる。削除した専用 test の旧性質は登録しない。

| 案 | 変異アンカー | 期待する赤の nodeid／単一理由 |
|---|---|---|
| M1 | requested-us module は削除済みのまま、`test_ccbench_spawn_sites.py:75` を残す | `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`：expected に消滅 site が 1 個残る。 |
| M2 | canary module は削除済みのまま、同 file `:215` の export_stock 行だけを残す | 同上 nodeid：消滅 site の Counter 値 3 が残る。`:216–218` は正しく削除する。 |
| M3 | requested-us module は削除済みのまま、`test_p3_build_authority_cli.py:152` を残す | `orchestrator/tests/test_p3_build_authority_cli.py::test_machine_callers_use_closed_generator_receipts`：`:1212` が当該 file の `FileNotFoundError`。 |
| M4 | insights 専用 test は削除済みのまま、README `:138` を残す | `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`：`:83` がその 1 file の stale entry を検出。 |
| M5 | 隔離した変異 worktree で `p2_5.py` の削除だけを index に反映しない。他の追随は完了 | `orchestrator/tests/test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact`：`:667` が index に残る `p2_5.py` を読めない。別途、受入入口では `run_tests.py:792–819` が pytest 開始前に rc=13。 |

M5 の受入 preflight には pytest nodeid がないため、node の赤と runner の拒否を別観測として扱う。baseline と変異後の復元確認を親が行い、本段では KILLED と報告しない。

## 総括

段 3 へ渡せる。17 file 全削除の author 確定指示としては P1 が未解決。  
親の主要修正点は 2 件：①P1 の「項 5 優先」を撤回して重複指定を解決、②共有 pin は 7 行でなく 6 行、付属コメント 2 行の処置を明示。  
残す 9 対の追加削除を支持する反証は 0 対。P2・P3 と台帳保持は支持する。  
未解決 P1 を保持すれば 15 file／132 node。coverage の現在値と焦点走・受入の合格は親の実走で確定する。