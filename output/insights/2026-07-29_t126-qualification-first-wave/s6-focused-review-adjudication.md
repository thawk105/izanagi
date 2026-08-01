authority: none
default_effect: no-state-change

# T-126 qualification-first — focused re-review 裁定

## 判定

focused re-review 1 は NO-GO。B (formal COMMIT AST gate) と I (active process-group cleanup) は
closed。C は regressed、A と D〜H / J〜M は partial と裁定する。第2 fix を行い、次の
focused re-review で `closed / partial / regressed` を再判定する。`DW-O16` の上限3巡のうち
1巡を消費した。

review 正本:

- `.codex/dev-wave-t126-qualification-jobs/s6-focused-review/output.md`

fix 1 後 / fix 2 前 snapshot:

- `.codex/dev-wave-t126-qualification-jobs/s6-pre-fix2-integrated.patch`
- SHA-256:
  `b362bccc6982d5aa498281e64ed8e7c79069fcb0604a825c72dbe36fe3a6c0df`

## 親裁定

| 対象 | 裁定 | 第2 fix の境界 |
|---|---|---|
| A | real | sink の derived field を immutable にし、relative path、round、role、event index を layout と append 済み event から再導出する。root の全 ancestor を write ごとに再検査する。 |
| B | closed | direct formal `wal.log(..., STAGE_COMMIT, ...)` 2件と既存 AST test を不変維持する。 |
| C / NR-1 | real / BLOCKER | receipt 公開前に ledger submitted binding を検査する。post-job verifier は matching attempt/index/job/nonce/outcome/receipt SHA を ledger から必須検証する。receipt→outcome 間 crash は explicit pending/finalize protocol で idempotent recovery する。 |
| C / NR-2 | real / HIGH | dry-run は authoritative ledger を一切消費しない。qsub 非0 / bind 前 failure は同 nonce 再開または explicit cancelled/submit-failed で initial attempt を消費しない。 |
| C / NR-3 | real / BLOCKER | attempt 内 job-result が存在すれば CLI 省略を authority にせず自動採用または拒否する。pre-attempt class は exact pre-attempt recovery phase に限定し、accounting RC 30 を member-rejected のまま保つ。 |
| D | real / BLOCKER | series-result 有・job-result 無の late TERM/SIGKILL を failure receipt へ閉じる。final/failure 分岐は series file の存在だけでなく accounting、job-result、terminal phase から導出する。 |
| E | real / BLOCKER | post verifier が pointed job-result の exact schema/field と accounting-derived class/RC/job ID/nonce/script/envelope を意味検証し、attempt phase と global ledger outcome を検証する。 |
| F | real | preimage shadow field を approved protocol へ exact 比較し、dependency commit を policy expected head へ、build argv を exact registered argv へ束縛する。submission snapshot safe-relative を共通 helper で検査する。 |
| G | real / BLOCKER | `git ls-files -v` の lowercase と `S` を拒否する。persistent tree から local qualification module を import する前に、stdlib-only/bootstrap で全 transitive execution input を HEAD blob と照合するか committed staging から submission logic を実行する。source-stage/perf evidence を consumer が再検証する。 |
| H | real | live `run` は外部 job-start/deadline envelope を必須にし、alternate direct run の Wmax 再発行を禁止する。prologue/final publication を残 budget timeout と elapsed consumer check に含める。 |
| I | closed | handler/handshake/finally cleanup を維持する。actual TERM/HUP positive/negative test は M で補強する。 |
| J | real | dry-run/qsub failure poisoning を閉じ、job は durable binding を確認するまで measurement を開始しない。既存・各 critical use 直前の component symlink/containment を再検査する。非協力的同一 UID が syscall 間に差替える一般 race は今回の absolute authority claim に含めず、normal path の dirfd/O_NOFOLLOW 境界を固定する。 |
| K | real / BLOCKER | submission snapshot/receipt、attempt preimage、series ledger、accounting、`.o/.e` の job ID / nonce / attempt / index / intent hash を相互再導出する。coherent 別 job swap を拒否する。 |
| L | real | `.create-*` の partial crash を deterministic safe cleanup / recovery 可能にし、成功後と write/fsync/link 各境界後の rerunを閉じる。 |
| M | real | A/D/E/G/J/K/L の具体的反例 test を追加し、M5a-b、M6a-d、M7a-c を一理由 fixture へ差替える。 |

## 第2 fix 受入

1. 上表の real finding を code/schema/test/script だけで閉じる。
2. B / I と既存全受理集合を回帰させない。
3. receipt が存在しても ledger outcome 未閉鎖なら verifier は invalid。idempotent finalize 後だけ valid。
4. dry-run / qsub failure は canonical series を消費せず、RC30 job-result 省略で retry を取得できない。
5. late TERM/SIGKILL、coherent job swap、skip-worktree import、partial staging crash を test で拒否する。
6. M5〜M7 は単一 anchor を消したときだけ期待 node が赤になる fixture にする。
7. parent related test と focused re-review 2 を通るまで commit / mutation / live qsub へ進まない。
