# 段 6 変異 matrix 実測台帳 — [T-205]

対象 = 統合 commit `fee55899faf0f9c6685340c41e1460d1af8df1c7`。事前登録は
`s4-adjudication-plan-v2.md` §5 (段 6 fix 後の期待 node 更新を含む)。
harness は親の監査計器なので job tmp に置き repo へは入れていない (T-179 / T-181 と同じ読み)。

## 結果: **13/13 KILLED**、正例 green、tree 復元 OK

| # | 変異位置 | 意図 | rc | 実際に落ちた node | 判定 |
|---|---|---|---|---|---|
| POS | (変異なし) | 受理集合の過剰縮小がないことの正例 3 本 | 0 | — (3 passed) | **OK** |
| M1 | `check_ai_provenance.py:578` `if waived:` → `if False:` | 免除発火そのものを殺す | 1 | `test_waiver_exact_line_exempts_implementation_author_gate` | **KILLED** |
| M2 | `:375` `if len(raw_values) != 1:` → `if False:` | waiver の物理 1 行性検査を殺す | 1 | `test_waiver_boundary_rejects_malformed_and_out_of_block[body-plus-valid]` / `[two-lines]` (他 8 id は緑) | **KILLED** |
| M3 | `:405` `elif not any(` → `elif False and not any(` | 同一 block の `role=author` 要求を殺す | 1 | `test_waiver_requires_own_role_author_ai_agent_line` | **KILLED** |
| M4 | `:916` `and not correction.waiver.exact` → `and True` | **waiver 付き commit を前方訂正の担い手に戻す = 受理集合の拡大** | 1 | `test_waiver_does_not_widen_forward_correction_acceptance` / `test_waiver_disqualified_correction_carrier_explains_the_reason` | **KILLED** |
| M5 | `:833` `if not commits:` → `if False:` | 空 selected set の guard を殺し rc=0 を rc=2 へ退行させる | 1 | `test_audit_history_empty_range_returns_zero_findings` | **KILLED** |
| M6 | `:747` `--topo-order` を除去 | 位相順の保証を外し祖先 bitset を不完全にする | 1 | `test_ancestry_bitset_matches_merge_base_oracle_for_every_pair` | **KILLED** |
| M7 | `:755` `acc = 1 << i` → `acc = 0` | `is_descendant` の反射性を殺す | 1 | 同上 | **KILLED** |
| M8 | `:851` `pool.map` の結果を逆順化 | findings の入力順保証を殺す | 1 | `test_audit_history_findings_follow_input_order_under_skewed_latency` | **KILLED** |
| M9 | `:1056` `PEGASUS_SUSPECT` 判定 → `if False:` | SUSPECT の fail-closed 拒否を殺す | 1 | `test_suspect_history_audit_refuses_with_infra_rc_without_dispatch` | **KILLED** |
| M10 | `:1054` `if args.message_file is None:` → `if True:` | commit 前 preflight の dispatch 免除を殺す | 1 | `test_login_message_file_is_dispatch_exempt[--message-file]` / **`[--message-f]`** | **KILLED** |
| M12 | `dispatch_compute.py:427` v1 受理 → `if False:` | in-flight job を殺す一方向 bump へ戻す | 1 | `test_job_run_accepts_v1_request_as_tests_task` | **KILLED** |
| M13 | `guard_bash.py:590` 借用抑止を除去 | sanctioned 借用の抑止を殺し `-mpytest` の穴を開ける | 1 | `test_bash_login_blocks_nonsanctioned_provenance_entrypoints[dash-m-pytest]` / `test_provenance_script_borrow_does_not_lend_sanctioned_status` (他 6 は緑) | **KILLED** |
| M14 | `:939` `waived_applied` → `waiver.exact` | 免除件数を実発火数から waiver 行の付与数へ戻す | 1 | `test_waived_count_excludes_docs_only_commits` | **KILLED** |

**帰属の精密さ**: 期待外の node は 1 つも落ちていない。M2 は同 parametrize の 8 id が緑のまま 2 id だけ、
M13 は 6 node が緑のまま 2 node だけが落ちた。M10 は接頭辞省略形 `[--message-f]` も落ちており、
段 3 レンズ A の R9 (raw token allowlist を移植すると `--message-f` が免除から外れる) に対する検出力が実証された。

## M11 は kill ではなく diagnostic sensitivity pin (DW-M03)

事前登録 M11 (`_dispatch_impl` の `if task not in TASKS: raise ValueError` を削除) は、
段 6 レビュー B の N2 が指摘したとおり、削除しても直後の `TASKS[task]` が `KeyError` を投げ
**同じく INFRA_RC を返し scheduler にも触れない**。すなわち**受理集合も fail-closed 挙動も変わらず、
例外クラス名だけが変わる**。`DW-M03` の「診断文字列だけの赤を kill にしない」に従い、
本変異は実施せず **diagnostic sensitivity pin として別枠に記録**する。

## harness の設計と、実行時に踏んだ既知欠陥

harness (`$JOB_TMP/mutation_harness.py`) は `DW-M04/M05/M08` に従う:

- anchor は「行番号 + その行の逐語」で指定し、一致しなければ**その変異を注入せず停止**する。
  実際に **M10 の行番号が 1 つずれていた** (1053 はコメント行) のを事前検証で検出し、注入前に是正した。
- 復元は `read_text() == 元ソース` の内容比較で検査する (git diff に頼らない)。全 13 変異で復元 assert を通過し、
  実行後の `git status --short` は**空**だった。
- `flock` で単一走行を guard する。
- pytest は `tools/run_tests.py` 経由で**計算ノードへ dispatch** される (ログインノードでは 1 度も走らせていない)。

**踏んだ欠陥**: harness は「rc≠0 かつ FAILED node 非空」を KILL と判定したが、
**dispatcher が子の pytest 出力を親 stdout へ中継しない**ため FAILED を抽出できず、
全 13 件を SURVIVED と誤報告した。これは worklog に既起票の **[T-194]** そのものである。
親が receipt (`output/pegasus-dispatch/<nonce>/receipt.json` の `scheduler_logs.stdout.tail`) から
事後抽出して上表を確定した。**初回の SURVIVED 表示は erratum として本節に保存する** (DW-M02)。
T-194 を閉じれば harness は receipt を読まずに判定できる。
