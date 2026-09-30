## 対応表 (所見 ID・closed/partial/regressed・根拠 file:line)

| 所見 | 状態 | 根拠 |
|---|---|---|
| 親の既知 D5 emitter 名 | closed | [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:35) が `set_gate_txid(` を検査し、[test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:174) に正例がある。 |
| A-R1 | closed | [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:120) は自分の書き前の外部読みを毎回照合する。2 回目だけ誤る試験は [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:106)。 |
| A-R2 / B-B3 | closed | 最終起動器のキーは [launch_gate_liveness_v3.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/launch_gate_liveness_v3.py:22) で [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/report.py:138) の投影と一致する。fix-u1 の合成投影確認は [fix-u1.md](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/fix-u1.md:18)。実走結果の確認は別途残る。 |
| A-R3 | partial | 最終 [ycsb.hh](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/include/ycsb.hh:19) は `#line 16`。他の復元指定も同ファイルの 115、121、145、157、176 行などにある。論理行の静的照合は [fix-u1.md](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/fix-u1.md:11) に記録されたが、指定された GCC 11・12 の D297 結果は未着。 |
| A-R4 / B-B5 | closed | [launch_gate_liveness_v3.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/launch_gate_liveness_v3.py:50) は N を記述値として扱い、S・X・B の条件を 61〜80 行で個別評価する。 |
| A-R5 | partial | V/W と thread 集合の明示検査は [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:84) および同 89 行に入った。M9・M10 の単一理由性は下表の注入で成立する見込みだが、変異本走は未了。 |
| B-B1 | closed（refuted を維持） | [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:104) は `first_read ⊆ reads`、同 105 行は `reads ⊆ q_read`。後者の負例は [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:82)。B-B1 の包含方向の指摘は当たらない。 |
| B-B4 | partial | B5 型、要求時の一部欠落・読取不能の CLI 試験は [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:98)、同 154、164 行に追加された。N2 は [s6-ruling-1.md](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/s6-ruling-1.md:12) により実走へ送られ、変異本走も未了。 |
| B-B6 | closed | 書式を読めた Q の thid 不一致は [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:208) で D1(c) に計数される。対応試験は [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:181)。 |
| B-B7 | partial | 計算ノードの CI build・D297・生死確認は依頼時点で走行中で、結果は未着。起動用の D297 コマンドは [run_judge_v3.sh](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/run_judge_v3.sh:24)、生死確認は [launch_gate_liveness_v3.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/launch_gate_liveness_v3.py:164)。 |
| B-B8 | closed | [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:71) の到達可能性、同 95 行の D1、同 115 行の D2 に分割された。分割に伴う問題は次節に記す。 |

親から提示された **195 passed** は焦点試験の結果として扱った。計算ノードの結果や変異の kill を、この静的レビューで合格済みとは扱わない。

## 新規所見 (ID・重大度・file:line・放置時の成果物への影響 1 行・推奨 1 つ。受理・拒否の含意を 2 文に分け、通る正例を添える)

| ID・重大度 | 位置 | 放置時の成果物への影響 | 推奨 |
|---|---|---|---|
| F1・should | [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:163)、同 206、140 行 | 明示検査を外す変異が素通りできるため、将来の変更で欠落した thread や V を静かに見逃す経路が残る。 | 到達可能性と V/W の不変条件を保ったまま、後段の `continue` と membership guard を到達不能を示す assertion に替える。 |
| F2・should | [launch_gate_liveness_v3.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/launch_gate_liveness_v3.py:35)、同 75 行 | B の期待一致は D1(b1) 件数と `indeterminate` だけを見るため、同時に別の D1/D2 違反があっても B の成果物は `match` と表示される。 | B について到達可能 0、D1(b1) 以外と D2a/D2b の違反 0 も照合し、B1 単独の発火を記録する。 |
| F3・nit | [gate_check.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/scripts/gate_check.py:45) | Q の操作数 0 は production parser では有効なのに診断器は到達不能とするため、両者の診断が食い違う。 | 診断器の `n == 0` 拒否を外し、production と同じ入力集合に揃える。 |

F1 の現行実装では、先行する [thread 集合比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:84) と [V/W 比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:91) が働く限り、欠落を受理する正例はない。比較を外した変異まで受理集合として扱う含意はなく、正常な `trace_0.log` と `gate_0.log`、対応する V・W・Q が揃う履歴はそのまま通る。

F2 を受理すると、B1 のみが発火したという成果物の読み方を守れる。拒否すると、例えば D1(b1)=B1 committed=1 に D1(a)=1 が併発した B 走行も `match` と表示される。通る正例は D1(b1)=B1 committed=1、他の gate 違反 0、verdict=`indeterminate` の走行。

F3 を受理すると、診断器と production の到達可能性が一致する。拒否すると、`C 0 0 1 1 0 0`・`E 0` に対応する `Q 0 0 0` を production が通し、診断器が拒否する。

D2a の照合拡大による正しい履歴の誤拒否は、調べた Silo 読み経路では確認できない。同じ key の再読は [transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/external/ccbench/cc/silo/transaction.cc:208) の read set に戻り、同じ版を使う。`#line 16` 以外の復元指定についても、今回の静的照合では新たなずれを特定していない。

## 変異の注入位置と単一理由性 (M1〜M15 の表: 位置・old 式・new 式・赤になる test・単一理由か)

以下は**静的な予測**であり、変異を実行した kill 結果ではない。`core.py` と `test_verifier_gate_witness.py` は上記 repo root の `orchestrator/verifier/`、`orchestrator/tests/` 配下を指す。

| 変異 | 位置・old 式 → new 式 | 赤になる test | 単一理由か |
|---|---|---|---|
| M1 | `core.py:103` `set(writes) != q_write` → `False` | `test_gate_b2_unregistered_write_m1` | はい。後続読みがなく D1(a) だけ。 |
| M2 | `core.py:104` `not first_read.issubset(reads)` → `False` | `test_gate_b1_missing_initial_read_m2_m15` | はい。D1(b1) だけ。 |
| M3 | `core.py:105` `not set(reads).issubset(q_read)` → `False` | `test_gate_trace_read_without_q_key_m3` | はい。D1(b2) だけ。 |
| M4 | `core.py:208` `txid is None or txid != frame_txid or q_thid != thid` → `False` | `test_gate_q_frame_m4` の `Q -`、`Q 1` の 2 ケース | **一部のみ。** 空 gate のケースは `core.py:220` の別の D1(c) 計数で依然赤い。M4 を一変異に保つなら Q 不一致の fixture 一つに絞る。枠だけは別変異にする。 |
| M5 | `core.py:228` `observed != expected` → `False` | `test_gate_b4_wrong_version_payload_m5`、`test_gate_b5_later_reader_disagrees_with_stored_stamp` | はい。V と版は整合し、非 genesis D2a だけ。 |
| M6 | `core.py:131` `obs != int(key, 16)` → `False` | `test_gate_genesis_wrong_payload_m6` | はい。genesis D2a だけ。 |
| M7 | `core.py:124` `obs != last[key]` → `False` | `test_gate_b6_stale_own_read_m7` | はい。D2b(i) だけ。 |
| M8 | `core.py:141` `stamp != pending_v[(frame_txid, key)]` → `False` | `test_gate_last_write_wins_m8` | はい。最後の書きと V の差だけ。 |
| M9 | `core.py:91` `set(pending_v) != wanted_v` → `False` | `test_gate_v_missing_m9` | はい。後段の membership guard により例外にはならず、欠落を素通りして期待する到達不能が消える。ただし F1 の保守上の問題は残る。 |
| M10 | `core.py:84` `trace_ids != set(paths)` → `False` | `test_gate_missing_thread_m10` | はい。欠落 thread は `core.py:163` で飛ばされ、期待する到達不能が消える。ただし F1 と同じ素通りに依存する。 |
| M11 | `core.py:251` `bool(gate_paths or bad_gate_names or require_gate_witness)` → `bool(gate_paths or bad_gate_names)` | `test_gate_required_absent_m11_cli_rc` | はい。要求時の全欠落だけが gate を起動できなくなる。M10 と同じ集合比較を変異させない。 |
| M12 | `model.py:540` `and (not self.gate_witness_required or self.gate_d5 == "pass")` → `and True` | `test_gate_b7_emitter_missing_m12` | はい。D5 だけが不成立。 |
| M13 | `core.py:72` `if bad:` → `if False:` | `test_gate_invalid_filename_m13` | はい。正しい gate に不正名を一つ足した fixture。 |
| M14 | `core.py:275` `if gate_enabled:` → `if gate_enabled and isinstance(parsed, _CompactTrace):` | `test_gate_legacy_parse_m14` | はい。legacy と gate の組だけを素通りさせる。`core.py:74` の型検査だけを外すと後段で属性例外になり、適切な変異ではない。 |
| M15 | `core.py:251` `bool(gate_paths or bad_gate_names or require_gate_witness)` → `bool(bad_gate_names or require_gate_witness)` | `test_gate_b1_missing_initial_read_m2_m15` | はい。要求なしの gate presence だけを無効にする。 |

M4 の元の事前登録は「枠だけ・Q だけ・txid `-` の各 fixture」を一つの条件としていたが、現実装の D1(c) は [余分な Q](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:180)、[不一致](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:208)、[Q 欠落](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:220) の三地点にある。一地点の比較除去で三ケース全部を殺す主張は成立しない。

## GO / NO-GO

**現時点は NO-GO。** 親の 195 passed は確認済みだが、段 4 裁定が受入条件とした変異本走、CI build、GCC 11・12 の D297、生死確認 4 条件の結果はまだ揃っていない。M4 の変異と fixture の対応も実行前に修正が必要。

## 総括

段 6 の主要な判定器修正は静的には成立し、B-B1 の refuted 判断も正しい。受入を止める残件は実測と変異の証拠、および M4 の単一理由性である。新たに見つかった素通り経路と B 条件の評価不足は、成果物の主張範囲を明確にするため修正を推奨する。