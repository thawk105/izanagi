## A. 対応表

| 所見 | 判定 | 実コードの根拠 | 残る record 列 |
|---|---|---|---|
| rev1-1 | **closed** | truncated でない WAL は直ちに noop。truncated の場合は active attempt 検査が [wal.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:552) で走り、receipt 生成は [wal.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:584)、`ftruncate` は同 585 行目。拒否テストも WAL bytes と receipt directory の双方を固定する。[test_campaign.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:835) | なし |
| rev1-2 | **closed** | topology 検証後、active start の `start_index + 1` 以後かつ `later.variant == variant` の `build_done/verify_done/bench_done` を拒否する。[wal.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1274)、[wal.py:1291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1291)。実 emitter は `build_done` を先に書き、後から同じ variant で verify/bench を書く。[pipeline.py:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:787)、[pipeline.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/pipeline.py:877) | なし |
| rev1-3 | **closed** | recovery reason の場合だけ、receiptless は `{reason, build_attempt_id}`、receiptful はそれに SHA を加えた exact set を要求する。[wal.py:1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1045)。artifact admission も同 validator を使用する。[artifact_admission.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:646) | なし |
| rev1-4 | **closed** | direct API 自身が `campaign.lock.search_config.build_admission == admission_policy.as_preimage()` を要求し、schema 判定や append より前に拒否する。[wal.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1243) | なし |
| rev1-5 | **closed** | 事前 `_validate_attempt_topology` の戻り値を使わず、active 射影は `_project_active_attempts` で独立している。[wal.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1118)、[wal.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1274)。MU-7 で事前検査だけを外せば invalid history の後ろへ実 append まで到達する。 | なし |
| rev2-1 | **closed（実装）** | backoff、sort、trigger の inner 全てが `ensure_resumable_attempts` を呼ぶ。[p3_s4_loop.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:708)、[p3_s4_loop_sort.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:238)、[p3_s4_loop_trigger_gating.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:542) | 実装上なし。ただし trigger 用 MU-12 テストに B-1 の穴あり |
| rev2-2 | **closed** | 検査・射影・suffix 検証が分離され、prospective 全履歴再検査による二重防御もない。[wal.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1118)、[wal.py:1141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1141) | なし |
| rev2-3 | **closed** | 4 key を一つずつ単独配置し、各 omission で recovery が no-op になるのを検出する parameterized test がある。[test_artifact_admission.py:360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:360) | なし |
| rev2-4 | **closed（静的）** | 外部 FD が `LOCK_EX` を保持中、worker の `finished` が立たないことを確認し、解放後の recovery 完了も確認する。[test_campaign.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:1088) | なし |
| rev2-5 | **closed** | 過去 signal は current start より前なので回復し、別 variant の3回上限も current variant を拒否しない。双方 admission 到達まで固定する。[test_artifact_admission.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:404)、[test_artifact_admission.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:441) | なし |
| rev2-6 | **partial（親の職掌）** | fix 子は worklog を変更していない。[s6-fix.md:17](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s6-fix.md:17) | record 列ではなく、親による運用前提・回復射程の worklog 記録が残る |

fix 自己申告が全件を「pytest 未実走なので partial」とした点とは判定が異なる。[s6-fix.md:1](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s6-fix.md:1) 本レビューはテストの緑を主張せず、実コード上閉じたものを `closed` と判定した。patch と worktree の差分 SHA-256 はともに `7c6af7ea…b9738` で一致した。

## B. 新しい穴

### B-1. trigger-inner の MU-12 が、WAL 挙動ではなく無効な fixture の別例外で赤くなる

- **severity:** must-fix
- **根拠:** trigger inner の実装自体は seam を通るが、対応テストは `sub="/must-not-run"` を渡している。[test_p3_s4_loop_trigger_gating.py:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1904)。MU-12 として seam を identity-only に戻すと、次に `patchharness.applied` へ進み、存在しない Git tree の検査で WAL writer より前に別の `RuntimeError` となる。[p3_s4_loop_trigger_gating.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:546)、[patchharness.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/patchharness.py:243)
- **具体的な record 列:** 現 fixture の mutant 実行は `trigger_binding(v_old,A) → build_start(v_old,A)` のまま止まり、二つ目の WAL record 群を書かない。それでも期待例外型が違うためテストは赤になる。さらに seed variant は文字列 `"crashed-trigger-reject-v"` で、実 retry が使う `diffq_variant_id(genome,predicate)` と一致させていない。[test_p3_s4_loop_trigger_gating.py:1910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1910)、[p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:241)
- **成果物影響:** 現コードの成果物は直ちには壊れない。しかしこの赤を MU-12 の kill evidence とすると、trigger inner seam の回帰を「殺した」と誤認する。実用 fixture なら `binding(v,A) → start(v,A) → binding(v,B) → start(v,B) → abort(v,B)` が追記され、同じ variant の二重 start は topology を拒否する。[wal.py:959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:959)。その結果 campaign admission、certified 選択、trigger proof-chain report、WAL SHA を持つ台帳参照が失効する。
- **提案:** backoff/sort テストと同様に、有効な一時 source treeと `applied` の制御済み context を使う。seed variant を実 predicate から計算した `diffq_variant_id` に一致させ、auditor/quarantine を決定的な reject にする。current 実装では bytes 不変、trigger-site MU-12 では二つ目の binding/start が実追記され topology/admission が変わることを直接 assert する。

fix 自己申告の「MU-12 は三テストで対応済み」は、backoff/sort については正しいが、trigger arm については過大申告である。[s6-fix.md:64](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s6-fix.md:64)

### MU-1〜MU-12 の静的追跡

| 変異 | 判定 | 赤になる本質 |
|---|---|---|
| MU-1 | 有効 kill | ID 欠落で exact suffix が成立せず、期待された recovery 成功・payload 集合が消える。[test_campaign.py:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:885) |
| MU-2 | 有効 kill | receiptful SHA 欠落で recovery 成功と replay state が成立しない。同上 |
| MU-3 | 有効 kill | guard を外すと build_done/signal 後にも abort が実追記され、拒否・byte 不変が崩れる。[test_campaign.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:916) |
| MU-4 | 有効 kill | trigger guard を外すと machine/proposal attempt が回復され WAL が変わる。[test_campaign.py:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:961) |
| MU-5 | 有効 kill | recovery abort が `retryable_abort` でなくなり、retry/commit の代わりに permanent skip となる。[test_campaign.py:911](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:911)、[test_campaign.py:4404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:4404) |
| MU-6 | 有効 kill | 上限解除で4本目の recovery abort が追記される。[test_campaign.py:991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:991) |
| MU-7 | 有効 kill | 事前 topology 検査だけを外すと、SHA 不一致の歴史を越えて active attempt の abort が実追記される。[test_campaign.py:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:1006) |
| MU-8 | 有効 kill | 全履歴走査への拡大は過去 signal 正例を、variant 条件脱落は別 variant 上限正例を過剰拒否し、admission 到達が消える。[test_artifact_admission.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:404) |
| MU-9 | 有効 kill | repair 先行なら WAL bytes または receipt directory が変わる。診断条件だけでなく両方を検査している。[test_campaign.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:857) |
| MU-10 | 有効 kill | exact check を外すと余剰-key abort が replay/admission の受理集合へ戻る。[test_artifact_admission.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:331) |
| MU-11 | 有効 kill | lock check を外すと missing/legacy lock の WAL に abort が追記される。[test_campaign.py:943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:943) |
| MU-12 | **partial** | backoff/sort は二つ目の start/abort を実観測するため有効。[test_p3_s4_loop.py:1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:1117)、[test_p3_s4_loop_sort.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_sort.py:383)。trigger-site は B-1 の別理由赤で、受理集合・fail-closed 挙動を pin しない。 |

MU-1〜MU-11 に静的な surviving mutant は見つからなかった。MU-12 を三箇所まとめた一個の multi-site mutant と数えれば backoff/sort が殺すが、trigger-site 単独変異の証拠は不成立である。

## 攻撃したが破れなかった箇所

- **FIX-2 の帰属:** `verify_done/bench_done` は attempt ID を持たないため、「同じ variant かつ current start より後」で保守的に帰属している。`start(v,A) → records(w,…) → verify_done(v)` は中間の別 variant を飛び越えて検出する。`start(v,A) → start(v,B)` は guard より前に multiple-active/topology 違反となる。同一 variant の過去 signal が current start より前なら回復する正例もある。
- **遅延 peer:** recovery が先なら、その後の `build_done(A)` は inactive attempt への record として validator が拒否する。[wal.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1002)。実 pipeline はそれを通らず verify/bench を emit しないため、旧 rev1-2 列は再構成できなかった。
- **FIX-1:** active+truncated の拒否までに走るのは open/flock/fstat/pread/parse のみ。receipt、truncate、recovery append は到達しない。
- **FIX-3 過剰拒否:** 正規 receiptless/receiptful recovery は helper が exact payload を生成する。[wal.py:1169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1169)。非 recovery abort は reason 条件に入らない。pre-policy artifact は shared validator より前に historical pathへ返る。[artifact_admission.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/artifact_admission.py:604)
- **FIX-5 の二重 seam:** public backoff/sort/trigger は outer と inner の二度、do-build では `run_campaign` でも三度目を通る。ただし一回目の abort で active が消え、後続は `recoveries == []` の byte-stable no-op になる。[wal.py:1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1336)。identity も同じ canonical lock の再照合だけで、対応範囲内の成果物差は構成できなかった。
- pytest・mutation harness は実行しておらず、緑は主張しない。

## 総括

- 判定: **NO-GO**
- 残 blocker 候補: **なし**
- 残 must-fix: **1件** — MU-12 trigger-inner の非本質的 kill
- 旧コード所見は rev2-6（親の worklog 職掌）を除き、静的には閉じている
- FIX-1/2/3/5 の現実装から certified 偽受理へ至る新 blocker は構成できなかった
- pytest・変異実走は未実施であり、テストの緑は主張しない