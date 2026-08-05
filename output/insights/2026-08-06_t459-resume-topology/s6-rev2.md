結論は **NO-GO**。blocker 候補が1件、テスト検出力・運用記録の must-fix が5件あります。以下は pytest 未実行の静的レビューです。

## 所見

### 1. p3 の inner 経路が recovery seam を迂回できる

- severity: **blocker 候補**
- 根拠: 裁定は identity-only の5経路を新 seam へ移すとしています。[s4-ruling.md:85](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:85)  
  outer `drive_iteration` の配置自体は正しい一方、inner は依然 `ensure_campaign_identity` のみです。[p3_s4_loop.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:708)、[p3_s4_loop_sort.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:238)、[p3_s4_loop_trigger_gating.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:542)。さらに backoff/sort の fixture CLI は inner を直接呼びます。[p3_s4_loop.py:952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:952)、[p3_s4_loop_sort.py:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:474)
- 取り残しシナリオ: `record_diff_reject` は start と abort を別々に追記します。[p3_s4_loop.py:265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:265)。start の fsync 後に crash し、同じ reject 提案を inner から直接再実行すると、決定論的に同じ `diffq_variant_id` へ二つ目の start が追加されます。後の topology 検査は「未終端 attempt がある」と拒否します。[wal.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:940)
- 成果物影響: campaign admission、critic digest、Layer3/report が campaign 単位で失効し、T-459 が同じ形で再発します。trigger inner では proof chain も不整合になります。
- 提案: outer seam は維持したまま、3つの inner の identity call も `ensure_resumable_attempts` に置換するか、inner を外部・CLIから呼べない構造にする。各 inner の reject-start crash を real `wal.log` で再現するテストも追加する。

### 2. MU-7 は単一理由の変異になっていない

- severity: **must-fix**
- 根拠: 裁定は、単一理由性を確認できない変異を取り下げるよう要求しています。[s4-ruling.md:108](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:108)。ところが事前 topology 検査の戻り値そのものが `attempts` の射影値であり、[wal.py:1182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1182)、直後の回復処理がそれを必須使用します。[wal.py:1202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1202)
- 取り残しシナリオ: 検査ブロックを削除する素直な MU-7 は `attempts` 未定義で落ち、WAL bytes は変わりません。例外 wrapper だけを外した場合も raw `AttemptTopologyError` で落ちるだけです。テストは赤になりますが、期待された「違反 WAL に追記したため赤」ではありません。[test_campaign.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:932)
- 成果物影響: MU-7 の赤を、既存違反 WAL への追記防止を証明する mutation evidence として採用できません。将来の gate 弱化を見逃す可能性があります。
- 提案: validation と active-attempt 射影を分離し、validation だけを外す一箇所変異で実際に append へ到達する構造にするか、MU-7 を取り下げて実効 gate へ再登録する。実装報告の「bytes が変わって赤」という説明も修正する。[s5-impl.md:51](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s5-impl.md:51)

### 3. B7 テストが4つの schema key を独立に殺していない

- severity: **must-fix**
- 根拠: 実コードの key 集合は裁定どおり4種です。[wal.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:70)。しかしテストは「全 key 無し」と、`build_attempt_id` と receipt SHA を同時に持つ一例だけです。[test_campaign.py:950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:950)、[test_campaign.py:964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:964)
- 取り残しシナリオ: `_ATTEMPT_SCHEMA_KEYS` から `build_admission` または trigger commitment だけを落とす変異は、現テストが緑のまま生存します。該当 key だけを持つ不正 start が strict topology に送られず no-op になります。
- 成果物影響: malformed post-policy WAL に後続 suffix を重ね、最終 admission で campaign 全体を失効させ得ます。
- 提案: 4 key を一つずつ単独で配置した parameterized test にし、各 omission mutant を殺す。

### 4. recovery lock のテストは no-lock 変異が確率的に生存する

- severity: **must-fix**
- 根拠: 二 thread の barrier は recovery 呼び出し前にしかありません。[test_campaign.py:973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:973)。`flock` を削除しても、一方が scan→append を完了してから他方が走れば、期待どおり `[0, 1]`・abort 1本になります。[test_campaign.py:996](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:996)
- 取り残しシナリオ: [wal.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1159) の lock を外した mutant がスケジューリング次第で緑になる。
- 成果物影響: 実際に両者が同じ prefix を読めば recovery abort が二重追記され、次 topology/admission が拒否します。
- 提案: 外部 fd で `LOCK_EX` を保持し、recovery worker が解放まで進めないことを Event 付きで確認する決定的テストを加える。

### 5. MU-8 が exact な過剰拒否を十分に検出しない

- severity: **must-fix**
- 根拠: 実装は正しく「対象 start より後」だけを走査し、[wal.py:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1207)、回数を variant ごとに数えています。[wal.py:1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1225)。しかし正例は履歴のない campaign のみです。[test_campaign.py:4214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:4214)
- 取り残しシナリオ:
  - `records[start_index + 1:]` を全 `records` に広げる mutant は、過去 attempt の verify signal を理由に現在の signal 前 crash を過剰拒否しますが、全新設テストを通ります。
  - recovery count から `record.variant == variant` を落とす mutant も、別 variant の3回を理由に過剰拒否しますが、現上限テストは同一 variant しか使わないため生存します。
- 成果物影響: 裁定より受理集合が縮み、正当に回復できる campaign が人手介入扱いになります。
- 提案: 「過去 attempt に signal→abort、その後の active attempt は signal 前」と「variant A は上限、variant B は初回 active」の2正例を admission 到達まで固定する。

### 6. 裁定必須の worklog 記録が未実装

- severity: **must-fix**
- 根拠: 裁定は、外部 root 走査の限定、旧 evaluator 終了後だけ resume する運用前提、trigger 非回復、縮小した射程を worklog に記録するよう明記しています。[s4-ruling.md:17](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:17)、[s4-ruling.md:27](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:27)、[s4-ruling.md:35](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:35)、[s4-ruling.md:102](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s4-ruling.md:102)。実装報告は docs を変更していないと明記しつつ「実装できなかった項目なし」としています。[s5-impl.md:1](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s5-impl.md:1)、[s5-impl.md:93](/work/1/SFC/tanab/dev-wave-jobs/t459-resume-topology/s5-impl.md:93)
- 取り残しシナリオ: 運用者が生存 evaluator と並行 resume し、回復後に旧 evaluator が `build_done` を追記する。
- 成果物影響: topology 拒否または旧 evaluator の成果破棄。trigger campaign が自動回復すると誤認する危険も残ります。
- 提案: landing 前に spool fragment 経由で4点を記録し、「実装できなかった項目なし」の自己申告を改める。

## 新設テストごとの変異追跡

| 新設テスト | 静的判定 |
|---|---|
| [payload receipt matrix](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:848) | MU-1/MU-2 は prospective topology が拒否して回復成功期待を破る。MU-5 は `retryable_abort` が false。いずれも受理・skip 挙動で赤。 |
| [signal guard](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:879) | MU-3 で abort が実追記され、byte 不変と拒否が崩れる。強い。 |
| [trigger guard](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:887) | machine lock／attempt commitment の両方で MU-4 を殺す。強い。 |
| [exhaustion](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:917) | MU-6 で第4 abort が追記される。ただし cross-variant 過剰拒否は未検出。 |
| [invalid/multiple active](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:932) | multiple-active の byte 不変は強い。MU-7 は所見2の理由で有効な mutation evidence にならない。 |
| [schema detection](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:950) | no-key no-op は固定。4 key の独立検出は不足。 |
| [concurrent recovery](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:973) | 最終形は検査するが no-lock mutant を決定的には殺さない。 |
| [loop crash E2E](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:4214) | MU-1/MU-2/MU-5 と基本 MU-8 を強く殺す。recovery→retry→commit→admission まで到達。 |
| [artifact admission positive](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_artifact_admission.py:285) | MU-8 の admission 受理と read 中 byte 不変を固定。初期 prefix は手書きであり real writer テストではない。 |
| [p3 backoff public entry](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:1082) | stopped-before による outer bypassを殺す。inner 直接経路は未検査。 |
| [p3 sort public entry](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_sort.py:352) | 同上。 |
| [p3 trigger public entry](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1863) | MU-4 に加え、WAL・checkpoint・provenance の不変を検査。強い。 |
| [s6 public sweep](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s6_sort_sweep.py:321) | recovery abort が quarantine record より先であることを実 `wal.log` で固定。 |
| [s8 public sweep](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_s8a_trigger_sweep.py:372) | MU-4／入口未配線なら例外が出ず赤。WAL byte 不変も固定。 |

MU-1〜MU-6 の対象テストは、診断文字列だけでなく append・受理・retryable/skip の変化で赤になります。例外は MU-7 です。

## 攻撃したが破れなかった点

- public `drive_iteration` の行順は裁定どおりです。backoff は recovery→state load→`check_stop`→checkpoint、sort も同順、trigger は recovery→provenance header→`check_stop`→checkpoint です。[p3_s4_loop.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:826)、[p3_s4_loop_sort.py:322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_sort.py:322)、[p3_s4_loop_trigger_gating.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop_trigger_gating.py:714)
- recovery 本体の exact payload、signal/trigger/limit guard、事前・prospective topology、同一 lock 区間は実装されています。[wal.py:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1090)、[wal.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1159)、[wal.py:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1244)
- plan §5／§8 の混入はありません。`wal.replay` は従来どおり trigger orphan tombstone を書きます。[wal.py:1280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/wal.py:1280)。trigger provenance schema に `recovered_attempts` は追加されていません。
- patch と worktree diff は一致し、既存テストの削除・期待値緩和・反転・skip/xfail 追加、既存 hash pin の更新はありません。
- “real pipeline/WAL writer” テストでは `pipeline.evaluate` と `wal.log` は実物です。一方、build/source digest/trace/verifier/bench/tenant probe は `_mock_pipeline` が偽装しています。[test_campaign.py:2178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:2178)、[test_campaign.py:2205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:2205)、[test_campaign.py:2214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:2214)、[test_campaign.py:2251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:2251)。したがって実装報告の限定的な表現は正しいですが、実 build E2E ではありません。
- 既存テストの静的赤は予測しません。未終端 attempt を seed する D25 テストは新 recovery reason が retryable 集合に入るため再評価を維持します。[test_campaign.py:4168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_campaign.py:4168)。`RETRYABLE_ABORT_REASONS` の exact 集合を pin する既存テストはありません。guided は attempt key 無しの pseudo-WAL なので no-op です。[guided.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/guided.py:127)。screening・S1 の既存 resume テストは completed attempt または tail repair が中心で、今回の suffix は増えません。

## 総括

- blocker 候補: **あり（p3 inner の identity-only bypass）**
- must-fix: MU-7、B7 key matrix、lock test、MU-8 過剰拒否、worklog 記録
- core recovery 実装と outer `drive_iteration` の順序は裁定どおり
- plan §5／§8 の不採用項目は混入していない
- 既存テストの静的赤は予測しないが、pytest は未実行で緑は主張しない
- 判定: **NO-GO**