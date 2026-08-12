# 判定: NO-GO

指定資料を静的に監査した。書込み・pytest・scheduler 実走は行っていない。

## 所見

1. **相互 digest が構成不能**
   - 位置: `s2-plan.md:32-35,94-95,190-195`
   - 種別: **blocker**
   - 破壊: manifest は `pre_submission_guard_sha256` を要求する一方、pre-submission `GuardReceipt` は `group_manifest_sha256` を要求する。双方の canonical hash が相互依存し、片方の後書き・未束縛・placeholder のいずれかになる。
   - 修正: manifest より先に確定する `launch-intent/v1` を設け、guard/budget receipt はその digest、最終 manifest は両 receipt を束縛する。

2. **release token の edge 強制が未実装**
   - 位置: `s2-plan.md:45-49,57,70-72,98,156`
   - 種別: **blocker**
   - 破壊: manifest に nonce の事前 commitment がなく、marker は既知の manifest hash と任意 nonce で作れる。偽 `release`／`start-permit` と timely な ack を置けば、schema は通る。coordinator が ack の `release_marker_sha256` を自分が発行した marker と一致検査する規定もない。
   - 修正: manifest に release-token commitment を凍結し、ack→実 release hash、permit→release hash＋exact N ack-set digest を双方向照合する。共有 root が同一 UID から書けるなら署名等も必要。

3. **dormant seal を import 経路から迂回できる**
   - 位置: `s2-plan.md:13,108,129-130,178-179,305`; `t810_preregistration.py:798-803`
   - 種別: **blocker**
   - 破壊: CLI だけが `request_t810_launch()` を通る。caller は `_coordinate_authorized(..., scheduler_run=実 runner)`、`withdraw_b_group(..., scheduler_run)`、`run_wrapper(..., measurement_run)` を直接呼び、qsub/qdel/測定を実行できる。underscore は capability 境界ではない。
   - 修正: 本 slice は callable を実行せず transcript 値を消費する純粋 FSM に限定し、実 scheduler／benchmark effect adapter 自体を後続承認 wave まで置かない。

4. **(d2) は repo 不在を証明せず、唯一の構造的防壁にならない**
   - 位置: `brief.md:43-45`; `s2-plan.md:149-150,163,314`; protocol `:370-378`
   - 種別: **blocker**
   - 破壊: package を `/scratch/t810` に置けば、その ancestor に `.git` がなくても `/work/.../izanagi` が同じ node namespace に mount されたままアクセスできる。wrapper は合格し、素の `open()` で repo に書ける。
   - 修正: repo mount が存在しない filesystem namespace/container/node-local staging を実行条件にし、用意できなければ fail-closed。ancestor `.git` 検査は補助検査／limitation と明記する。

5. **開始ばらつきが実際の measurement start を拘束しない**
   - 位置: `s2-plan.md:98,156`; protocol `:186-190`
   - 種別: **blocker**
   - 破壊: 全 wrapper が即座に `start_ack` した後、permit 受領後に一台だけ 30 秒停止しても、計算値は 5 秒以内のまま実測区間だけがずれる。
   - 修正: permit→exec→第1反復開始の観測 edge を定義して coordinator 時計へ返し、その edge を gate/state に束縛する。状態境界との矛盾は実装前に裁定する。

6. **budget ledger を caller がリセットできる**
   - 位置: `s2-plan.md:179,233-264`
   - 種別: **blocker**
   - 破壊: `ledger_path` は caller 引数で、policy は単に `repository-external` としか束縛しない。毎回新しい空 ledger を指定すれば残枠が全量へ戻る。また `0 <= required` はゼロ attempt の admission を許す。
   - 修正: 承認済み canonical ledger identity/path を policy に束縛し、run kind から正の attempt 数を内部導出する。予約は lock 下で `fsync` 完了後にのみ submission へ進める。

7. **runner allowlist が単一 mediation 点になっていない**
   - 位置: `s2-plan.md:129-130,155,167-168`
   - 種別: **must-fix**
   - 破壊: caller 指定 `measurement_run`／`runner` が allowlist を無視して certify executable を実行、または偽 `CompletedProcess` を返せる。wrapper だけの AST tripwire は注入先・import 先を検査しない。
   - 修正: production API から effectful injection を除去し、verified preregistration 由来 policyを使う固定 `run_allowed_measurement()` だけへ結線する統合 tripwireを置く。

8. **並走ガードに qstat snapshot 後の race が残る**
   - 位置: `s2-plan.md:190-208`
   - 種別: **must-fix**
   - 破壊: 2 回目 qstat が空を返した直後、release 作成前に T-139 が投入されると、B 系はそのまま開始する。exact parser は snapshot と release の原子性を与えない。
   - 修正: A/B 共通の優先 lease を単一 mediation 点にするか、成立しない間は unresolved と同様に常時 deny する。

9. **§5.4 の検査時点を前倒しして retry を誤許可する**
   - 位置: `s2-plan.md:54-62,96,154`; protocol `:350-352`
   - 種別: **must-fix**
   - 破壊: dependency/module/trace/NUMA を ready 前の一括 preflight で検出すると `pre_release_invalid` となり retry 可能になる。正本では release 後・measurement 前の状態 2 で retry 不可。
   - 修正: state-1 検査と release 後の state-2 検査を別 event/schema に分け、reason code ごとの許容 phase を exact に検証する。

10. **`terminal_reduced` が first-match で潰れる**
    - 位置: `s2-plan.md:100-105`; protocol `:346-357`
    - 種別: **must-fix**
    - 破壊: 12 slot が R=10 を完了し一台が脱落した入力でも、先行する「measurement 後の欠損」に該当して `incomplete_after_start` になり得る。
    - 修正: 状態3を「完了 ≤N−2、または完了 job 自身の欠損／integrity 違反」に限定し、状態4では脱落 job を整合性評価から除外する。

11. **retry ordinal が 3 attempt を許し得る**
    - 位置: `s2-plan.md:32,106`
    - 種別: **must-fix**
    - 破壊: 0-based ordinal なら attempt 0 と1の両方で `<2` が真となり、ordinal 2への再投入が許可される。
    - 修正: ordinal を exact `{1,2}` とし、`retry_allowed = state==pre_release_invalid and ordinal==1` に固定する。

12. **自己申告 boolean と caller の approved host を真実として扱う**
    - 位置: `s2-plan.md:32-34,55-56,94-96,164`
    - 種別: **must-fix**
    - 破壊: config に未承認 host を追加し、well-shaped hardware と `passed=true`, `repo_absence=true`, `submission_argv_match=true` を書けば barrier が合格し得る。hash chain は内容の真正性を与えない。
    - 修正: approved host/hardware は承認束縛済み inventory から導出し、coordinator が raw evidenceから判定を再計算する。wrapper/package hash も ready edge で照合する。

13. **競合 process scan が他 UID を見落とす**
    - 位置: `s2-plan.md:151`
    - 種別: **must-fix**
    - 破壊: 割当て affinity 上で別 UID の process が動いても無視され、短時間負荷なら load1 も閾値以下のまま通り得る。
    - 修正: visible な全 process を対象とし、affinity/UID情報を読めない対象は安全側で拒否して、measurement 直前にも再走査する。

14. **凍結 presence matrix と新 schema の保存形が未結線**
    - 位置: `s2-plan.md:52-62,77-81,107`; `t810_validator.py:1111-1164`; `t810_prereg_v1.json:41-64`
    - 種別: **must-fix**
    - 破壊: plan は measurement rounds を node-event payload に入れるが、凍結 layout は別の `measurements.jsonl` を要求する。guard/budget receipt の配置と、`validate_t810(attempt_receipt=...)` に渡す `slots` projection も未定義で、valid run が missing/extra file または incomplete と判定され得る。
    - 修正: 既存の exact filename 全てへの serialization 表、control artifact の repo外・attempt外配置、validator 入力 projection をプランに固定する。

15. **能力限界の宣言と完了主張が食い違う**
    - 位置: `s2-plan.md:9-14,129-168`; `t810_validator.py:35-39`
    - 種別: **must-fix**
    - 破壊: validator は引き続き `execution_mediation_incomplete` と `d2...out_of_scope` を返すのに、plan は同 validator の pass で (c)/(d2) まで閉じた形を取り得る。
    - 修正: runner/harness 独自の `/limitations` と evidence を設け、能力遮断でない限界を残したまま第1段承認条件を満たしたと主張しない。

16. **親 brief の「実測済み」が一次資料を一般化し過ぎる**
    - 位置: `brief.md:29-35`; `mutation_fanout.py:1099-1119`; `t810_prereg_v1.json:569-577`
    - 種別: **must-fix**
    - 破壊: `_qstat_identity()` は重複 field を last-wins、未知 state をそのまま返すため「汎用 exact parser」ではない。さらに `build_argv` と `qsub_argv` は明示的に `unfrozen_procedures` であり、「凍結 field 実在」から凍結済み手順へは一般化できない。
    - 修正: 「字句／設計 pattern の素材」に格下げし、qsub/build は未凍結 limitation と明記する。`brief.md:33` も「統合済み機構が無い」へ限定する。

## 裁定パッケージ候補

- T-139 の anchored job identityだけでなく、A/B 共通 priority lease の所有者と mediation 点。
- budget 総枠・見積り・canonical ledger identity、および T-868 trust root による policy digest 承認。
- §3.3 の「request ID」を pre-qsub logical ID とするか PBS ID とするか。
- start response／permit／実際の `measurement_start` の定義と、5秒超過時の状態2/3境界。
- 現 prereg bytesを維持したまま未凍結 qsub/build procedure を補助 artifact で承認するか、再承認するか。

## 総括

- **NO-GO**。現プランのまま実装段へ進めない。
- 最大の blocker は、構成不能な digest graph、forge可能な release edge、dormant seal迂回、偽の(d2)である。
- 状態機械は検査 phase、`terminal_reduced`、retry ordinal の3点で正本とずれる。
- allowlist・guard・budget は存在するだけで、現状は単一 mediation／一意な残枠正本になっていない。
- 明示 `-o/-e` と unresolved identity の常時 deny は安全側だが、上記 blocker を相殺しない。