# 8c formal consumer の `_wal_trigger()` を production の WAL 形状へ直した — 受理形は production 形状 1 つに閉じ、旧形状・非 exact 形状は FC05C で拒否する

**種別:** 読み手 (consumer) の修理。dev-wave `dev-wave-t2257-formal-consumer-wal-shape` (2026-09-05〜09-07)、[T-2257]。
設計判断は {{D:formal-consumer-production-wal-trigger-shape}} (fold 後は実番号)。起点は D1555 の「あわせて記録する実装上の事実」。

**この wave が直したのは trigger binding record の読み方だけである。** consumer の terminal record 検査
(`_validate_wal_outcomes()` の `terminal.get("kind")`) は据え置きで、production の terminal は `stage` が `commit` / `abort`
(`orchestrator/campaign/model.py`) なので、修理後も本番 projection は FC05C を通った後 FC07 で止まる (別 carry)。
end-to-end で本番 projection が通るようになったとは書かない。

## 1. 食い違いと修理

| | 変更前 | 変更後 |
| --- | --- | --- |
| trigger record の識別 | root `kind == "TriggerGateBinding"` | `stage == "trigger_binding"` の record がちょうど 1 件 |
| 比較対象 | root `trigger_binding` (ledger と同形の dict) をそのまま比較 | outer key 集合・outer 値の型・payload key 集合を exact で閉じ、raw binding を `validate_record(require_source=False)` で検証し、`{mask, candidate_wire, trigger_gate_binding_commitment}` へ射影して ledger と exact 比較 |
| 旧形状 | 受理 | FC05C |
| production 形状 | FC05C (読めない) | 受理 (P-1〜P-3) |

producer 側 (`orchestrator/campaign/wal.py` の `log_trigger_binding()`) は 1 byte も変えていない。稼働中の
`dev-wave-t1851-unit-a` worktree の `wal.py` は local main と差分ゼロで、producer 変更は不要と確認した。

## 2. 正例の出所

`output/campaigns/p3-s8a-trigger-*/runs/wal.jsonl` 7 本に `"stage":"trigger_binding"` は 0 件で、保存済みの production record は
無かった。正例は producer 関数を実走して得た:

- `verbatim/producer-verbatim-record.txt`: `wal.log_trigger_binding()` → `wal.log(build_start)` を tmp layout で実走した 2 行の逐語
  (script の逐語は `verbatim/probe-script.md`)。テスト `test_verbatim_producer_records_with_only_attempt_transplanted_reach_p6` は
  この 2 行を byte 単位で literal に持ち、attempt id だけ fixture へ移植する。`_wal_trigger()` の射影 commitment が producer の
  `build_start` に書かれた commitment (`3971d4e1…b7029`) と一致することを独立 pin する。
- P-1 / P-2: テスト内で `CampaignLayout(...).ensure()` と `wal.log_trigger_binding()` を実際に呼び、書かれた WAL 行を projection
  に入れる (mask 7 / source なし、mask 18 / source 付き)。

ledger 側 `trigger_binding` (`{mask, candidate_wire, trigger_gate_binding_commitment}`) の production producer は未実装で、値は契約
(`reflux_result_evidence` の exact keys、`trigger_gate_binding.commitment()`) から導いたものであり実測ではない (DW-O13 の限界)。

## 3. 段 3 / 段 6 の所見と裁定

- 段 3 レンズ A (受理集合): payload の key 集合閉包、root/payload の attempt 併存 (root shadow) 拒否、source 付き正例と
  source-only 負例、独立 commitment pin。レンズ B (テスト設計): FC06 test の追随、`_rewrite_wal` の root 注入禁止、
  `test_reflux_*` は pytest-only allowlist なので焦点走は `run_tests.py` 経由、fixture builder test の exact key 検査。全採用。
- 段 6 レビュー A (NO-GO → fix3): canonical-list 経路の projection は `wal.parse_line()` を通らないため outer 値の型
  (`variant` / `env_tag` / `ts`) が未検査だった。`wal.py` と同じ型契約を consumer 内に敷いた。レビュー B は GO。
  焦点再レビューは GO。
- 親の erratum: producer 実走 record を refs へ保存し直した (2 回目の走) のに、brief には 1 回目の `ts` を写したまま残し、
  段 5 の子が refs を正しく写した literal を fix1 で誤値へ書き換えさせた。親の byte 比較 script で発覚し fix2 で戻した。
  F1 の near-miss として追記。

## 4. 変異 matrix

事前登録 (段 4、実装前): M1〜M11。段 6 fix3 後に M13〜M15 を追加登録し、等価変異 M12 を SURVIVED 期待の正例として混ぜた。
probe (全件 SURVIVED 期待) で観測 node を集め、本走で KILLED 期待 node を完全集合で登録した。冗長 gate (drift mask) は出なかった。

spec は `verbatim/mutation-main-spec.json` (sha256 `f41620143b0a51f934908529914bf76666a7c714bab3198b26a7f64441bfe4d2`)、
台帳は `verbatim/mutation-main-ledger.json` と `verbatim/mutation-probe-ledger.json`。走行対象は
`test_reflux_formal_consumer.py` / `test_reflux_origin_fixture_builder.py` / `test_reflux_result_evidence.py` /
`test_p3_autonomous_workload_trial.py` の 4 file、`--runner-mode dispatch --detached`、runner argv に `--force-dispatch`。

| ID | 種別 | 期待 | 本走 | 殺した node 数 | 代表 node |
| --- | --- | --- | --- | --- | --- |
| M1-legacy-root-shape-fallback | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_legacy_root_trigger_binding_shape` |
| M2-select-by-payload-key-not-stage | negative | KILLED | KILLED | 2 | `test_fc05c_rejects_duplicate_trigger_stages_with_invalid_second_payload 他 1` |
| M3-drop-mask-compare | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_ledger_mask_only_mismatch` |
| M4-drop-commitment-compare | negative | KILLED | KILLED | 3 | `test_fc05c_rejects_ledger_commitment_only_mismatch 他 2` |
| M5-first-of-many-stage-records | negative | KILLED | KILLED | 2 | `test_fc05c_rejects_duplicate_trigger_stages_with_invalid_second_payload 他 1` |
| M6-reverse-wire-bit-order | negative | KILLED | KILLED | 20 | `test_origin_public_path_preserves_capability_identity_and_projects_terminal 他 19` |
| M7-skip-validate-record | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_raw_trigger_binding_extra_key` |
| M8-count-only-payload-bearing-stage-records | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_duplicate_trigger_stages_with_invalid_second_payload` |
| M9-drop-outer-key-closure | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_root_attempt_shadow` |
| M10-drop-payload-key-closure | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_trigger_payload_extra_key` |
| M11-reject-non-null-source | negative | KILLED | KILLED | 1 | `test_live_producer_trigger_with_source_reaches_only_p6_unavailable` |
| M12-equivalent-count-predicate | positive | SURVIVED | SURVIVED | 0 | — |
| M13-drop-outer-type-checks | negative | KILLED | KILLED | 3 | `test_fc05c_rejects_boolean_trigger_timestamp 他 2` |
| M14-allow-bool-ts | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_boolean_trigger_timestamp` |
| M15-allow-str-ts | negative | KILLED | KILLED | 1 | `test_fc05c_rejects_string_trigger_timestamp` |

本走 summary: `registered=15 completed=15 matching=15 KILLED=14 SURVIVED=1 MISMATCH=0 PARSE_ERROR=0 TIMEOUT=0`、
baseline は rc=0 (58 秒)。16 走の実行時間合計は 1168 秒。

**読み取り:** M1 (旧形状の fallback を足す) は N-1 だけが殺し、M11 (source 付きを拒否する) は P-2 だけが殺す。
受理集合を広げる変異と狭める変異が、それぞれ 1 本のテストに固有に対応している。M6 (wire のビット順反転) は 20 node を
巻き込み、fixture の `candidate_wire` を consumer と独立な実装で作った設計が効いている。M12 (`len(x) != 1` を
`not len(x) == 1` へ) は意味が同じで SURVIVED し、テスト群が字面でなく挙動を見ていることの正例になっている。

## 5. 焦点走・受入

| 走 | 対象 | 結果 |
| --- | --- | --- |
| 焦点走 1 (fix 前) | 11 file、Pegasus 978585 | 679 緑 / 4 赤 (`test_reflux_result_evidence.py` の golden 4 定数 = 旧 fixture bytes の値 pin、F39 再発) |
| 焦点走 2 (fix1/2 後) | 11 file | 683 緑 |
| 焦点走 3 / 3b (fix3 後) | 11 file | rc=16 (3: 同 worktree の provenance 監査 job と並行投入で orphan-hold、3b: queue-wait-timeout、いずれも非帰属) |
| 焦点走 3c (fix3 後、D612 上書き) | 11 file | 686 緑 |
| 変異 probe 1 回目 | 4 file | baseline 段が rc=16 (既定 900 秒の queue 待ち、runner script に D612 上書きを書き忘れた。変異は 1 件も走らず) |
| 変異 probe 2 回目 | 4 file | baseline 緑、14 件が殺され M12 のみ SURVIVED (観測 node を本走 spec へ写した) |
| 変異本走 | 4 file | 15/15 一致 |

受入全走は本記録 commit の後に投入し、結果は受入 receipt と land 報告に残す (記録 commit を tested tip の内側へ置くため)。

## 6. 変更面と commit

- 19b897a43: consumer + fixture builder + baseline 3 entry + builder test + consumer test + golden 4 定数 (段 5 + fix1 + fix2)。
- a7ffb661f: 型契約 + N-11〜N-13 + P-3 改名 (fix3)。
- b279c564d: 記録の前に local main 5ce5157cd を取り込む merge (変更面には触れていない)。
- 本 README、spool fragment 3 本、変異台帳を含む記録 commit。

新規テスト 18 本 (P-1〜P-3、N-1〜N-13、および builder test の追加検査) は
`orchestrator/tests/acceptance_duration_ledger.json` へ未登録である。台帳の読み込みは fail-soft なので受入は止まらないが、
所要の見積りには入らない。焦点走の dispatch は JUnit XML を残さないため、この wave では登録できない。

## 7. 次 wave の出発点

- {{T:formal-consumer-terminal-stage-shape}}: terminal record の `stage` 読み (consumer 側) と fixture の terminal の production 形状化。
- producer が record 形状を変えるときは、裁定済みなら consumer と literal を更新し、未裁定なら producer 側の回帰として扱う。
  旧 literal の互換受理は足さない。
