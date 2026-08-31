## 総括

裁定 1: **修正版 A を当面採用し、再現可能な新 corpus を作るなら C を別 wave で行う**ことを推奨する。
裁定 2: **(i) verified IR と trusted interpreter の生死確認を別 wave で起票する**ことを推奨する。
A は可用性判定の精密化であり、正しさ判定そのものを緩めない限り絶対規律 2 には抵触しない。
ただし既存 fixture の guard だけを変えても、rollout を直接読む 5 node は残るため、親案のままでは不十分である。
B は歴史的比較を別実験へ置換し、host corpus のままなら次回剪定でも再び壊れる。
T-2076 の 3 案不成立には同意する。現行設計では観測 bytes の出所を候補 comparator に束縛できない。
pytest は実走しておらず、以下は射影資料とコードの静的評価である。

## 裁定 1

### Q1-1

**案 A の考え方自体は「正しさゲートを緩める変異」ではない。**

線引きは、次の二つを分離できるかである。

- skip してよいのは、テストが前提とする repo 外の exact な証拠 corpus が存在せず、検査を開始できない場合だけ。
- rollout が存在するのに SHA 不一致、identity 重複、内容破損、manifest 不整合がある場合は skip せず失敗させる。

既存の `historical rollout root is unavailable` が許されるのは、外部 prerequisite の欠落を「正しい」と判定せず、「検査不能」として明示する契約だからである。根 directory は在るが要求された 7 月 pin が一件もない状態は、意味論上は根ごと無い状態と同じであり、そこを精密化するだけなら判定基準は変わらない。

ただし acceptance が skip を pass と同じ保証として報告するなら別問題であり、「当該歴史検査は未実施」を receipt 上で保持する必要がある。

### Q1-2

availability 判定は node ごとの required pin 集合を受け取り、次を満たすべきである。

- session root が無い、または required session ID の identity match が **0 件**なら unavailable。
- match が **1 件かつ pinned SHA-256 と一致**する場合だけ available。
- 複数 match、SHA 不一致、session metadata の破損、manifest の欠落、予期しない I/O error は失敗。skip に変換しない。
- 一つの pin が欠落し、別の pin が破損している場合も、破損を先に失敗として扱い、欠落による skip で隠さない。
- required でない pin の欠落によって、その pin を使わない node を skip しない。

必要集合は少なくとも次の三つに分ける。

- `benchmark_snapshots`: `POS`, `NEG`, `author`, `fix1`, `fix2`
- `test_m2_production_golden_requires_both_routes`: `author`, `fix1`, `fix2`
- rollout 直接参照 4 node: `POS`

正例は、一時 session root に各 required ID の valid な session metadata と、その内容に対応する digest を持つ rollout を用意し、availability が available を返すだけでなく、後続の snapshot または prompt 検査が実際に呼ばれたことまで確認する形にする。対になる負例は、1 pin 欠落なら skip、SHA 不一致と重複なら failure、未要求 pin の欠落なら検査継続を要求する。

### Q1-3

**B:** exact な再実験を行って 5 role を張り直すなら、新しい実験について ID、digest、prompt、patch route の整合性を保証できる。しかし 2026-07-29 の POS/NEG 比較を保証するものではなく、単なる手近な session への変更ならテストの意味を失う。repo 外の Codex session に置く限り、pin は保持を保証しないため次回剪定で再び壊れる。

**C:** 失われた 7 月 JSONL を repo 内へ持ち込むことは不可能である。新しい再実験または最小 fixture を commit すれば、その新基準の再現性と host 非依存性は得られるが、7 月の markdown が元 rollout から正しく導かれたことや、旧実験の歴史的同一性は回復しない。したがって C は「復元」ではなく、明示的な再基準化として扱う必要がある。

### Q1-4

ソース上の `benchmark_snapshots` 依存閉包は、parameterized variant を数えて **23 node** ある。

- `test_parent_numstat_controls_remain_pinned`
- `test_forbidden_commits_are_unreachable_in_both_cases`
- `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure`
- `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested`
- `test_m1_snapshot_head_pin_is_independent`
- `test_m3_snapshot_mode_change`
- `test_m3_symbolic_head_is_required`
- `test_m3_ignored_extra_and_missing`
- `test_m3_focus_artifact_directions` の 3 variant
- `test_snapshot_submodule_object_store_is_recursive`
- `test_pos_neg_submodule_initialization_state_mismatch_is_rejected`
- `test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`
- `test_git_answer_object_reinjection_is_rejected`
- `test_supervisor_launches_pair_and_scrubs_git_environment`
- `test_agent_sandbox_binds_exclude_attempt_receipt_directory`
- `test_verify_replays_complete_fake_codex_experiment`
- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`
- `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`
- `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`
- `test_attempt_four_is_rejected_before_launch`
- `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation`

fixture を通らず corpus に依存する node はさらに **5 node** ある。

- `test_m2_production_golden_requires_both_routes`
- `test_prompt_replacement_count_zero_expected_and_excess[0]`
- 同 `[9]`
- 同 `[10]`
- `test_real_rollout_collector_golden_is_source_bound`

したがってソース上の外部 corpus 依存集合は **28 node**、非依存集合は同 file の残りすべてである。特に一時 directory と合成 rollout を使う `_find_rollout_*` 群や、resolver を monkeypatch する pin wiring tests は非依存であり、file 全体を skip してはならない。

主資料の `21 errors + 5 failures` は実行時選択集合では説明できるが、射影されたソースの fixture 依存 variant は23ある。2 node が事前 skip または非選択だった理由は射影資料からは確定できない。

[既存 guard](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_codex_reasoning_ab.py:788)だけを変更する A は、後者の直接参照 5 nodeには掛からない。一方、非依存 node までは巻き込まない。

### Q1-5

**修正版 A を即時採用:** required pin 集合別の狭い availability gate を、fixture と直接参照 5 node の双方へ適用する。
**B は不採用:** 歴史的意味を変更し、host 外部 pin の剪定問題も解消しない。
**C は別 wave:** 新 corpus の明示的な再基準化としてのみ検討し、旧 corpus の復元とは主張しない。

## 裁定 2

### Q2-1

**「3 案いずれも不成立」に同意する。**

現行コードでは、候補文が trusted wrapper と同じ translation unit にそのまま連結される（`_translation_unit`, 1246〜1247行）。さらに `active_write_set`, `active_order`, `relation`, `sort_called`, `observation_fd`, `observation_count` は書込み可能な同一 address space にある（[sort_swo_oracle.py:918](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_swo_oracle.py:918)）。

- fd witness: candidate process は `observation_fd` への `write` を許される（1078〜1084行）。broker は bytes の長さ、値、反復一致を検査するだけで、その producer を認証しない（1417〜1445行）。
- trap: comparator call と `emit_bool` は同一 TU の935〜956行にあり、候補も同じ callsite や helper へ到達できる。trap の発火点だけでは「trusted loop が comparator を呼んだ結果」という出所を証明しない。
- fork: seccomp allowlist に `clone`, `clone3`, `wait4` はなく、filter は候補文より先に導入される（1058〜1135行、1227〜1234行）。また comparator 引数式の評価は `sort` へ入る前なので、`sort` 内 fork では親側副作用を隔離できない。

なお `active_order` 由来の `lhs/rhs` は946行の `relation[]` 書込みにしか使われず、comparator 入力は position 添字である。段4がこの点を訂正したことにも同意する。ただし、それで observation producer の穴は閉じない。

### Q2-2

**(i) を推奨する。**

候補側で任意の C++ を同じ address space で実行したまま、その C++ が生成する観測値の出所を同じ process 内の helper、fd、global、callsite によって証明する現実的な第3案は見当たらない。

(ii) は現状を正確に記述する選択ではあるが、oracle を adversarial な合成候補に対する正しさ gate として使えない状態を恒久化する。(i) は受理集合を変えるため、現 wave へ押し込まず別 wave とするのが妥当である。

### Q2-3

最初の生死確認は、次の一問でよい。

> 現在の authoritative comparator 15件を、小さい型付き whitelist IR へ全件表現でき、その trusted evaluator が現行2 corpusの関係行列を再現し、未知 opcode、型不一致、任意 C++ 文字列を評価前に fail-closed で拒否できるか。

手書きの IR table、最小 evaluator、2 corpusへの適用だけなら、100行以内の使い捨て driver で確認できる。この問いが偽なら、parser、receipt、合成エージェント変更へ進む前に設計を止められる。

### Q2-4

(ii) で失われるのは、SWO oracle の pass を「実 comparator が当該 corpus 上で SWO だった」という証明として扱う資格である。残るのは、協力的な候補に対する有限 counterexample finder と、corpus mutation・final protocol write の隔離だけである。

D1271 が「限界として明記するだけ」を退けた具体的理由は、candidate-visible な基準 snapshot という当時の実在する穴を文書だけでは閉じられないことだった。その前提は T-1574 により消えている。したがって、その具体的な却下理由は relation provenance へ自動継承されない。

一方、「文書化は防壁ではない」という一般原則は今も生きている。ゆえに (ii) を選ぶなら非保証を保証へ読み替えてはならず、fresh なユーザー裁定として「この oracle を正しさ証明に数えない」と維持する必要がある。

## 親の案への反対

- 案 A を788〜790行の fixture guard変更だけで完了とする点には反対する。直接 rollout を読む5 nodeが残り、受入の赤を解消しない。
- source-level の corpus 依存閉包は28 nodeであり、実測26件との差2件の選択理由を確認せず「完全な対象集合」と断定すべきではない。
- 段4の「3案不成立」と T-2076 をユーザー再裁定へ返す判断には反対なし。