# 判定: NO-GO

必読資料はすべて読めた。read-only の静的検証のみで、テストは実行しておらず、緑は主張しない。

## B-1 — REAL / BLOCKER: 三 tree 証明で fold transaction を分離密輸できる

plan の証明対象は transaction ではなく個々の signature path である。

> 「各 key について…direct parent P があれば『trusted main からの取り込み』と証明して免除する」  
> [plan.md:187](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:187>)

次の履歴は条件 1〜4 をすべて満たす。

| commit | fragment `f` | `FOLDED.md` | canonical 台帳 |
|---|---|---|---|
| `B` = merge-base | 存在 | `R0` | `L0` |
| `P` = `base_main_sha`、正規 main fold | 削除 | `R1` | `L1`（`f` を反映） |
| `Q` = wave 親 | `B` と同じ | `R0` | 妥当だが `f` を含まない `Lq` |
| `C` = merge(`Q`,`P`) | `P` を採用 | `P` を採用 | `Q` を採用 |

`C` について、

1. `P == base_main_sha`
2. `C[f] == P[f]`、`C[FOLDED] == P[FOLDED]`
3. `merge-base(Q,P) == B` で一意
4. `Q[f] == B[f]`、`Q[FOLDED] == B[FOLDED]`

となり、fragment D と FOLDED M の両 key が免除される。しかし結果は「fragment は消え、receipt はあるが、canonical に内容がない」。これは plan 自身の脅威モデル、

> 「fragment を消して canonical へ反映されない作業を失わせる。」  
> [plan.md:65](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:65>)

そのものである。

この攻撃が通る根拠は明示的である。

- 現 helper は「`FoldPlan` との blob 単位照合は行わない」。  
  [git_state.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:708)
- canonical 文書変更は既存正例で許可されている。`allowed` に `"docs/worklog.md"`, `"docs/decisions.md"`, `"docs/failures.md"` が入り、最後は `assert result.ok`。  
  [test_dev_waves_git_state.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:457)
- 本来の `FoldPlan` は canonical 4 面と FOLDED を同じ `changes` に入れ、同一 transaction ID を作る。  
  [spool_fold.py:1858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/spool_fold.py:1858)
- `C` に pending fragment がなければ `plan_fold` は canonical を再照合せず `"noop"` を返す。  
  [spool_fold.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/spool_fold.py:1720)
- land は noop 時に helper を通した後、そのまま ff-only し、`return merged` する。  
  [dev_wave_land.py:1819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1819), [dev_wave_land.py:1916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1916)

予定された負例は「wave が fragment を M」「C の FOLDED が P と異なる」の二つだけで、上の「protected 2 path は P と同じ、canonical だけ Q」を扱わない。  
[plan.md:416](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:416>)

M1〜M7 にも canonical 選択を変異させる項目がない。したがって予定テストを全通過して密輸できる。

### 攻撃 (d) が現在守っているもの

`B` から、hidden fold `H` で `f` を D、FOLDED を M、canonical を偽造し、その後 `R` で `f/FOLDED` だけ `B` へ戻して canonical 偽造だけ残す。endpoint の protected 差分は空でも、現行 per-commit loop は `H` の D/M を発見する。

> `for commit in commits:`  
> `if _landed_fold_output_path(status, paths):`  
> `return _fold_fail("landed-fold-owned-path")`  
> [git_state.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:730)

つまり守っているのは endpoint tree ではなく、canonical・receipt・GC が同じ許可された fold transaction に由来するという履歴上の原子性である。

## B-2 — REAL / HIGH: consumer の受理変更がテストされていない

production は「3 module・4 static call site」であり、land に二本ある。  
[plan.md:9](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:9>)

### base の伝播自体は REFUTED

4 箇所すべて正しい base を渡せる。

- land 二経路: `tested_main` は exact `tested_main..tested_tip` closure の起点。  
  [dev_wave_land.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:932), [dev_wave_land.py:1707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1707)
- checker: receipt base は `spec.before_main_sha` に binding 済み。  
  [checker.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:406)
- daemon: receipt base は wave manifest base に binding 済み。  
  [daemon.py:1500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1500)
- receipt parser も `base_sha != binding.base_sha` を拒否する。  
  [receipt.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/receipt.py:196)

`landed_commits` も land/checker では引き続き exact closure であり、wave-tip 用と別の意味には二重化されない。  
[git_state.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:527)

### consumer テスト閉包は REAL

plan は明示的に checker と daemon の受理を広げる。

> 「checker.py…valid receipt の受理変更は同じ正規 merge の赤→緑のみ」  
> 「daemon.py…accepted-wave recovery が同じ正規 merge receipt を再受理」  
> [plan.md:439](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:439>)

しかし既存テストはこの変更を識別しない。

- checker 単体 fixture は `"schema_version": 1`。  
  [test_dev_waves_checker.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_checker.py:125)  
  checker は v1 を `"legacy-v1"` として helper を迂回する。  
  [checker.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:539)
- supervised `fold_success` は名前どおり「direct child fold」で、merge を含まない。  
  [test_dev_waves_integration.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_integration.py:492)
- land の stale-resync E2E は merge を含むが、winner は `"winner.txt"` を commit するだけで fold がない。  
  [test_dev_wave_land.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:2471)
- daemon resume test は最終的に常に `RunState.FAILED` を期待する。  
  [test_dev_waves_integration.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_integration.py:925)  
  `accepted_matches=True` でも `_resume_accepted` が `AMBIGUOUS_RECOVERY` へ止めるため、helper が誤って拒否しても同じ表面結果になり得る。  
  [daemon.py:1566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1566)

最低でも以下が必要である。

- land no-fold の main-fold merge 正例
- land declared-fold の main-fold merge 正例
- schema v2 checker の同じ正例
- WAVE_ACCEPTED recovery で、helper 受理/拒否が terminal state を分ける daemon test
- B-1 の canonical 分離 merge を helper・land・checker の各層で拒否する負例

また、必須 keyword 追加に対し、git_state 単体だけで既存直接呼び出しが 17 本ある。plan が明記した test 側追随は land の一本だけである。  
[plan.md:421](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:421>), [test_dev_waves_git_state.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:260)

TypeError は全走で捕まるが、各 fixture に「実際の interval 起点」を渡すことまで段 4 で列挙しないと、都合のよい SHA を差し込む fixture laundering を防げない。

## B-3 — REAL / MEDIUM: `merge-base --all` の rc=1 契約が欠落

plan は、

> `"merge-bases": ("merge-base", "--all")`  
> 「複数なら免除を与えず fail-closed」  
> [plan.md:224](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:224>)

とするが、merge-base が存在しない場合を定義していない。`git merge-base --all` は no-base で rc=1 になり得る一方、既存 `_run` は既定で `(0,)` のみを許し、それ以外を `DevWavesError` にする。

> `allowed_returncodes: Sequence[int] = (0,)`  
> [git_state.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:173)

unrelated-history の Q と、current base P を親に持つ merge object は land の `base ancestor tip` を満たせる。Q に同名 fragment/FOLDED があれば signature key も発生する。これは「証明不能なので `landed-fold-owned-path`」へ閉じるべきであり、例外化してはならない。

特に no-fold land 呼び出しは helper の `DevWavesError` を局所捕捉せず、`land()` 最外周も `_Reject` しか捕捉しない。  
[dev_wave_land.py:1819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1819), [dev_wave_land.py:1949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1949)

段 4 では次を逐語化すべきである。

- `_merge_bases` は rc `(0,1)` を許し、1/空/複数を「免除なし」に正規化する
- 新しい全 Git 呼び出しへ同一 `deadline_ns` の `_left(deadline_ns)` を渡す
- no-base、multiple-base、timeout をそれぞれ負例化する

### argv・encoding 等は REFUTED

- `shell=False`、bytes 出力、per-call timeout は既存 `_run` 契約に沿う。  
  [git_state.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:185)
- 非 UTF-8 status/path は strict decode で fail-closed。  
  [git_state.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:565)
- `--root` は parent を持たない commit-diff に必要だが、二 tree 比較には不要。plan の分離は正しい。
- worktree 越しでも shared object DB を使うため二 SHA 比較は成立する。
- production は shallow/replace を既存入口で拒否する。  
  [dev_wave_land.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:517), [git_state.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:335)
- `_validate_base` は構文しか見ないが、不在 object は Git error へ閉じ、誤受理にはならない。  
  [git_state.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:381)

## 既存テストの誠実性

### `test_n31` 書き直し — REFUTED

期待値は拒否のままで、skip・削除・緩和はない。現行 fixture の、

> `landed_commits=(tip, first_fold)`  
> `assert (not result.ok)`  
> [test_dev_waves_git_state.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:374)

を、first fold 後に protected tree を restore する stronger fixture へする。新 plan でも `first_fold` は non-merge なので、

> 「parent 数 < 2: 現行どおり…各署名を拒否」  
> [plan.md:183](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:183>)

により拒否され続ける。DW-S05-C / DW-S06-B の禁止形は認められない。

### 既存拒否テスト — REFUTED

fragment D、D+A rename、FOLDED M はいずれも non-merge fixture であり、merge 限定免除の対象外である。  
[test_dev_waves_git_state.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:503), [test_dev_waves_git_state.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:517), [test_dev_waves_git_state.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:570)

declared fold の parent-count、typechange、closed path shape は helper 後半を変更しないため維持される。  
[plan.md:263](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:263>)

### 新設正例の現行赤 — CONFIRMED

現行 argv は逐語で、

> `"diff-tree", "--root", "-r", "-m"`  
> [git_state.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:90)

である。新正例の merge tip は landed closure に含まれ、wave 親との差に FOLDED M と main fragment D が出るため、declared fold 検査より前の [git_state.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:730) で拒否される。したがって正例は現行欠陥を実際に捕まえる。

### argv test — REAL / 不十分

現テストは `safe_short_options = {"-r", "-m", "-z"}` として `-m` を明示的に許す。  
[test_dev_waves_git_state.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:75)

plan は renamed test を挙げるが、M1 は rename detection の変異だけで、`-m` 再導入を殺す変異がない。  
[plan.md:453](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/plan.md:453>)

更新後テストには少なくとも以下の exact assertion が必要である。

- `"-m" not in GIT_COMMANDS["commit-diff"]`
- `"--root" not in GIT_COMMANDS["tree-diff"]`
- 両 diff に `"--no-renames"`
- move/copy detection option が両方にない

## 親 brief 自身への攻撃

### 不変条件不足 — REAL

brief の 5 条件は path signature と既存 gate しか固定していない。  
[brief.md:37](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:37>)

不足している不変条件は少なくとも次のとおり。

- 免除される D/FOLDED M は、同一 trusted parent の canonical targets・receipt・GC と同じ fold transaction に由来する
- checker、daemon recovery、land の4 call site が同じ base binding と受理集合を持つ
- exact `base..tip` closure の意味を helper API 変更後も維持する
- Git error、no merge-base、multiple merge-base、timeout、encoding は例外漏れでなく fail-closed result に閉じる
- 正例は direct helper だけでなく production consumer ごとに現行赤を示す

F82 は、

> 「防ぎたい攻撃を path の所有で表現しようとした」  
> 「fold の署名は…2 条件」  
> [failures.md:1749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/failures.md:1749)

と戒めている。今回の案は signature を保持した一方、免除の正当性を path 単位へ分解し、transaction coupling を失った。複雑さが単なる美観問題ではなく B-1 の実反例になっている。

### 単一 Codex 実装単位 — PARTIAL

単一単位そのものは、必須 keyword を helper と全 caller へ原子的に入れるため妥当である。しかし理由、

> 「編集面は 1 モジュール + そのテスト」  
> [brief.md:73](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:73>)

は事実ではない。実際は helper、land、checker、daemon の4 production module と複数 test module である。所有面を広げた単一単位として書き直す必要がある。

### 親の既存テスト一覧漏れ — REAL

親一覧以外の relevant pin を独立に列挙すると以下になる。

- `test_dev_waves_git_state.py`: exact shape、rotation/copy、archive count/index、typechange、N31/N32/P07/N33、encoding、全 non-signature docs、FOLDED A、D、D+A、R parser、fragment M、FOLDED M、N34。  
  [test_dev_waves_git_state.py:255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:255)
- `test_dev_wave_land.py`: exact audit 4 本、zero-fragment、実 fold lock、rotation、supervised slug、encoding、rollback/generated-docs、stale-resync merge。  
  [test_dev_wave_land.py:1146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:1146), [test_dev_wave_land.py:1492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:1492), [test_dev_wave_land.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:1563), [test_dev_wave_land.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:2471)
- `test_spool_fold.py`: parallel fold、canonical bytes 保存、second-fold/replay、transaction third-state/resume、deterministic plan、P01/P02、real canonical target closure。  
  [test_spool_fold.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_spool_fold.py:485), [test_spool_fold.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_spool_fold.py:613), [test_spool_fold.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_spool_fold.py:746), [test_spool_fold.py:1592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_spool_fold.py:1592)

特に `test_n37...` は real plan の target に `{"docs/worklog.md", "docs/spool/FOLDED.md"}` が同時に含まれることを pin しており、B-1 の transaction coupling を裏づける。  
[test_spool_fold.py:1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_spool_fold.py:1615)

### 受入計画 — REAL / 不十分

> 「`tools/run_tests.py` 全走緑…`check_docs.py` rc=0」  
> [brief.md:66](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:66>)

全走は存在する assertion しか検査しない。B-1 の履歴も consumer merge 正例もないため、全走と check_docs の双方が通っても三 tree proof の回帰は残る。`check_docs.py` は Git parent provenance を検査しない。段 4 の mutation matrix に canonical 分離 M8 と consumer-level mutation を追加しなければ受入根拠にならない。

## 代替案比較

| 案 | 受理集合 |
|---|---|
| merge commit を全除外 | 正例に加え、任意の merge resolution fold も受理。過広で不採用。 |
| `--cc` | 全 parent と異なる path だけ検出。結果を一親に合わせる laundering を受理。 |
| first-parent diff | wave first なら正例を拒否、main first なら wave fragment の捨てを見逃す。parent 順依存。 |
| merge-base→C | 正規 main fold 自体を再検出し、目的の正例を拒否。 |
| endpoint 累積差分 | hidden fold + restore を見逃す。plan の棄却は正しい。 |
| plan の key 単位三 tree | B-1 の canonical/FOLDED/GC 分離を受理。 |

より単純で安全側なのは、signature key ごとではなく、単一 trusted parent `P` の「fold transaction delta」を単位にする案である。`merge-base→P` で変更された canonical/FOLDED/GC path 全体について、非 trusted 親は merge-base と同じ、merge result は P と同じことを要求する。wave 独自の新規 fragment A は delta 外なので正例を保てる。

ただしこれは同じ canonical path を直接編集した legacy wave を拒否し得る。F82 が記録する、

> 「worklog を直接書くのが現行契約」  
> [failures.md:1746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/failures.md:1746)

との政策衝突がある。legacy canonical merge まで無条件に保つなら、path 同一性では足りず、FoldPlan delta の保存または決定的 merge/replay を証明する必要がある。

## この wave 自身の land

### bootstrap cycle — REFUTED

修正後 checkout の `dev_wave_land.py` は自身の `__file__` から repo root を入れ、その checkout の `git_state` を import する。

> `_REPO_ROOT = Path(__file__).resolve().parents[1]`  
> `from tools.dev_waves.git_state import ...`  
> [dev_wave_land.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:27)

したがって「旧 helper で先に land しないと新 helper が使えない」という循環はない。

### 手順穴 — REAL

brief は、

> 「main を定期的に確認し、動いたら都度取り込む」  
> [brief.md:80](</work/1/SFC/tanab/izanagi-jobs/9aba3998/land-fix/brief.md:80>)

としか書かない。しかし O23 は main merge 後に「新main監査…条件再評価・受入後に再試行」を要求する。  
[operations.md:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/docs/dev-wave/operations.md:134)

main を取り込むたびに tip と audited closure が変わるため、全受入・provenance・レビュー結論の再確認が必要である。また「前 wave branch を実際に land できること」を current main 上で実行すると main が動き、本 wave 自身を再 merge・再受入する順序になる。実 main を動かすのか disposable clone で証明するのかを先に固定すべきである。

## 裁定パッケージ候補

- canonical direct-edit と main fold が競合したとき、保守的に transaction closure 一致を要求するか、legacy acceptance を守るため FoldPlan/merge の意味証明まで scope を広げるか。
- long-running supervised daemon が旧 module を import 済みの場合、再起動を本 wave の deployment 条件に含めるか。
- 前 wave の land 可能性を実 main mutation で確認するか、固定 SHA の disposable repository で確認するか。

## 総括

- **BLOCKER:** key 単位三 tree 証明は、fragment/FOLDED を main 親、canonical を wave 親から採る transaction 分離密輸を受理する。
- **HIGH:** land・checker・daemon の4 call site は base を渡せるが、checker/daemon の新しい赤→緑を識別する consumer test がない。
- **HIGH:** brief の不変条件・scope・受入 matrix は transaction closure、consumer 閉包、no-base/error 契約を欠く。
- よって現 plan は **NO-GO**。B-1 の政策裁定と負例追加前に段 4 へ進めてはならない。