authority: none
default_effect: no-state-change

# T-126 qualification-first — 段6 review 裁定

## 判定

NO-GO。段7、commit、live qsub へはまだ進まない。親の独立 test が検出した formal
COMMIT の AST gate 回帰に加え、2本の独立 review が同じ load-bearing boundary に
具体的な反例を示した。下記 must-fix を一度の implementation fix にまとめ、親の再検査と
focused re-review を通す。

査読正本:

- `.codex/dev-wave-t126-qualification-jobs/s6-review-proof/output.md`
- `.codex/dev-wave-t126-qualification-jobs/s6-review-runtime/output.md`

fix 前の統合 snapshot:

- `.codex/dev-wave-t126-qualification-jobs/s6-pre-fix-integrated.patch`
- SHA-256:
  `40083475c73162b71ebb72af2b51e86c6025efddae1d8d4d9ecbeb6d9b917f30`

## 親の独立検査

関連 11 file の plain runner は `1 failed, 496 passed, 9 skipped`。唯一の赤は
`test_evaluate_commit_writes_are_syntactically_verify_gated` で、`evaluate()` 内の direct
`wal.log(..., STAGE_COMMIT, ...)` が期待2件に対して0件だった。generic `emit` alias が
formal COMMIT の構文的 gate を不可視化したためであり、既存 test を弱めない。

両 reviewer は exit 0、`tools/check_codex_output.py` 成功。proof reviewer は read-only
sandbox のため pytest 非実走、runtime reviewer は pure/opt-in の focused test と
`bash -n` / JSON parse を実走した。親の上記 full related test が test 正本である。

## findings 裁定

| ID | 裁定 | 成果物影響 / 修正境界 |
|---|---|---|
| A | real / BLOCKER | `QualificationPipelinePolicy` が `emit()` duck type だけを受理し、formal layout + WAL wrapper で qualification lineage を落とせる。exact qualification sink、capability、layout、attempt root の同一性と root containment を最初の write 前に検証する。fake sink / formal layout / mutable-root 反例を拒否する。 |
| B | real / BLOCKER | formal COMMIT 2箇所が generic alias へ隠れ、既存 AST safety gate が赤。formal branch は direct `wal.log(..., STAGE_COMMIT, ...)`、qualification branch は認証済み sink への明示分岐に戻し、既存 test を無変更で緑にする。 |
| C | real / BLOCKER | retry 履歴を singleton に切り、attempt ID ごとの claim なので A→B→C と fresh index 0 を繰返せる。canonical series-level create-only ledger/claim、全 chain 検証、retry index 1 の再 retry 拒否、duplicate initial 拒否を実装する。missing ledger や自己申告 failure class は許可理由にしない。 |
| D | real / BLOCKER | prologue failure、controller signal、SIGKILL では attempt/job-result がなく collector が failure receipt を作れない。job 開始時の submission/job namespace、catchable exit trap、accounting を authority にした job-result 不在 closure を追加し、全 scheduler terminal を final/failure のいずれかへ閉じる。 |
| E | real / BLOCKER | final/failure receipt の nested schema が `{}` を許し、post-job receipt を再検証する consumer がない。再帰 exact-key schema と専用 read-only verifier を追加し、pointer、closure、accounting、stdout/stderr、submission/job-result の hash と意味を再導出する。`hold_enforced=false` は維持する。 |
| F | real / BLOCKER | empty identity でも series ID と failure/retry が成立し、recorded commit/tree/gitlink、protocol、script、toolchain への外部錨定がない。clean/failure 共通の exact required identity、safe relative snapshot、Git object 再導出、approved protocol/pair、dependency/toolchain executable hash を必須にする。 |
| G | real / BLOCKER | persistent worktree の Python/policy/script を実行し、CCBench だけを `/scr` に staging している。hidden dirty/scan failure は比較前に code を実行できる。live source 全体を committed bytes から immutable scratch へ staging し、scan rc、policy、dependency state/build argv、functional perf output を永続化・検証する。 |
| H | real / BLOCKER | prologue 後にほぼ全 Wmax を driver へ再付与し、29100秒を超えられる。job start の単一 monotonic deadline で prologue、driver、gap、attestation、finalize を囲み、receipt consumer も elapsed/envelope を検証する。 |
| I | real / BLOCKER | controller TERM/HUP/exception 時に detached member PGID が残り得る。active PGID を追跡し、signal/finally を含む全経路で TERM→bounded grace→KILL→消滅確認する。実 descendant test を追加する。 |
| J | real / BLOCKER | submit namespace の中間 symlink、qsub 後 receipt race、post-submit qstat 不在がある。全 component の lstat/realpath containment、qsub 前 intent、strict job ID、durable receipt、exact qstat visibility を実装する。qsub 後に未束縛 job を残さない fail-closed protocol にする。 |
| K | real / BLOCKER | collector の accounting job ID が substring、`.o/.e` が任意同一 file、submission receipt が attempt snapshot と未束縛、external copy が check/read TOCTOU。exact field/job ID、scheduler filename/distinctness、snapshot hash、O_NOFOLLOW open+fstat+copy に閉じる。 |
| L | real / HIGH | collector の逐次 O_EXCL copy は crash/quota 後も成功後も再実行不能。staging + atomic publish、または既存 exact hash の idempotent reuse と fault-injection test を追加する。 |
| M | real / HIGH | test/schema は文字列・mock・schema syntax 中心で、実 submit、descendant、tamper、partial collector を殺さない。fake qsub/qstat、実 process tree、symlink/hidden drift、consumer verifier、copy fault injection を追加する。 |

## closed / refuted

- legacy/formal caller の empty numactl 拒否、fullscale lock と competing process admission は
  現実装でも維持される。穴は public qualification opt-in の caller/sink 束縛である。
- 明示 marker、ancestor、lock、WAL lineage の Layer3 拒否と通常 formal 正例は存在する。
  whiteboard への marker 追加は exact schema が拒否する。残る穴は lineage laundering である。
- settled、5 reps、全 rc=0、unstable=false、legacy+S2 exact evidence、
  commits/aborts>0、anomalies=0、trace/perf distinct の正常系 admission は成立する。
- alternating order、prefix balance、Rmax=8、strict SPRT boundary、3 terminal の pure core は
  成立する。
- historical source hash、中央値、`+0.506556%` は一致し、実装も
  observational smoke / `statistical_claim=none` を維持する。
- writer の通常 API の traversal、O_EXCL、O_NOFOLLOW、fsync は成立する。ただし capability
  sealing と multi-file transaction は上記のとおり未完である。
- direct shell interpolation injection は検出されなかった。

Layer3 の formal root/lock を新しい一般 authority へ再設計する提案は、この wave の must-fix
にはしない。qualification opt-in を exact capability/layout へ閉じ、既存 formal loader の
positive shape と qualification lineage の negative shape を維持することで今回の非交差を閉じる。

## mutation 再登録

元の M1〜M7 はそのまま実走しない。実コード anchor と一理由 fixture に合わせて次へ更新する。

| ID | 実効 mutation / fixture |
|---|---|
| M1 | `subject > reference * (1 + threshold)` を `>=`。exact boundary だけが赤。 |
| M2a-c | Layer3 marker / ancestor-or-lock / WAL lineage gate を個別に削除。各 fixture は他の lineage を除き、通常 formal 正例を同走。 |
| M3 | source snapshot expected SHA 比較を削除。tampered bytes だけが赤。別に safe-relative / Git-object consumer mutation を追加する。 |
| M4a-b | producer settled gate と receipt consumer settled gate を個別に削除し、他方を満たす一理由 fixture を使う。 |
| M5a-b | 6-stage topology を保ったまま S2 exact tag / exact argv gate を個別に削除する。legacy-only 等の前段 rejection で mask しない。 |
| M6a-d | accounting existence / exact job ID / Exit_status / final pointer closure を個別に削除する一理由 fixture。 |
| M7a-c | series ledger の duplicate initial / retry-of-retry / first-x-or-terminal gate を個別に削除。実 submit→collector chain の許可済み1回 retry 正例を同走。 |

mutation は integrated commit 後に `DW-O19` に従って tracked tree を1件ずつ変更し、期待赤の
唯一理由を記録して exact restore を確認する。

## fix 受入条件

1. A〜M の修正を code/test/script だけへ実装する。docs、commit、qsub は parent が担う。
2. 既知 AST test は変更せず緑にする。
3. 通常 formal、lower/upper/indeterminate、許可済み一回 retry の過剰拒否 control を維持する。
4. fix 後に親の関連 test、focused re-review、全 test を通す。
5. clean committed tree と post-commit provenance / mutation が緑になるまで live qsub を禁止する。
