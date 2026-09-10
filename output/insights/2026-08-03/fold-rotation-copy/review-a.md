### 1. [real / must-fix 候補] `D(fragment) + A(rotation)` が全制限を通るため、I1 は文字どおりには成立しない

**根拠 (file:line)**

`_FRAGMENT_PATH_RE` と `_ROTATION_PATH_RE` はそれぞれ [git_state.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:23)、[git_state.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:27)。fold 検査は `D` を fragment、`A` を rotation として個別に数えるだけである ([git_state.py:756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:756)、[git_state.py:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:773)、[git_state.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:777))。blob/`FoldPlan` 照合は明示的に行わない ([git_state.py:710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:710))。

**具体的な失敗シナリオ**

次の commit を作る。

```text
R100  docs/spool/worklog/2026-08-03-wave-1.md
      docs/archive/worklog-phase3-0803-123.md
M     docs/archive/README.md
M     docs/spool/FOLDED.md
```

現行 `-M -C` では `R100` が [git_state.py:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:763) の `path-status` で拒否される。`--no-renames` 後は次になる。

```text
D  docs/spool/worklog/2026-08-03-wave-1.md
A  docs/archive/worklog-phase3-0803-123.md
M  docs/archive/README.md
M  docs/spool/FOLDED.md
```

これはすべて通る。

- `D` は fragment regex に一致し、削除数 1。
- `A` は rotation regex に一致し、archive 数 1。
- README と archive 数の相関も成立。
- `M FOLDED.md` があり minimum-shape も成立。

つまり、fragment 自体を archive へ移しただけで「fold 済み」と認定できる。`Cnnn worklog→archive` についても、内容が高類似だが誤った archive であっても、正しい rotation と同じ `M+A+D+M` へ正規化される。status/path だけでは区別不能である。

なお README 条件は [git_state.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:783) の一方向だけだが、上の反例は README も変更するため、双方向化だけでは閉じない。

**成果物影響**

certified 選択値や既存レポート数値は直ちには変わらないが、fragment が canonical worklog へ反映されないまま `FOLDED.md` だけ進み、試行台帳・archive・「次の一手」の参照が欠落または別内容になる。

**推奨**

`fragment→rotation` の負例を事前登録する。拒否を要求するなら、archive blob を親 worklog から移した正しい範囲へ束縛するか、commit を `FoldPlan.targets` の独立検証結果へ束縛する必要がある。scope 外を維持するなら、I1 を「正規化後の path/status alphabet は広がらない」へ狭め、この commit 集合の拡大を残存穴として明記すべきである。

### 2. [real / must-fix 候補] landed 側の `R` 分岐削除は I2 を入力契約依存へ弱める

**根拠 (file:line)**

現行は rename 元が fragment なら拒否する ([git_state.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:557))。プランはこれを `D` 専用へ変える ([plan.md:37](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan.md:37))。landed 区間には未知 status を拒否する閉集合検査がなく、helper が false ならそのまま進む ([git_state.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:730))。

**具体的な失敗シナリオ**

将来の Git 挙動変更、フラグ回帰、または異常な Git 出力により landed commit が次を返すとする。

```text
R100  docs/spool/worklog/2026-08-03-wave-1.md
      docs/archive/orphan.md
```

プランどおり R 分岐を消すと、保持された parser は正しく 2 path を読むが helper は false を返す。その commit 後に pending fragment がゼロなら、`fold_commit_sha=None` の経路は [git_state.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:737) から `"no-fold"` を返せる。変更前は rename 元 fragment により拒否される。

現在の `--no-renames` 契約が守られる通常経路では、同じ rename は `D+A` となり `D` で拒否される。この通常経路の漏れ懸念は refuted。ただし R 分岐削除により予備防壁は実際に失われるため、I2 は無条件では保証されない。

**成果物影響**

fragment が receipt 更新なしで spool から消えた landed 区間を正当と扱い、台帳追記が欠落する。checker/recovery は完了扱いへ進み得るが、certified 選択値は直ちには変わらない。

**推奨**

`_landed_fold_output_path` の `R*` 元 fragment 判定は残す。fold slot 側の明示 `R/C` 条件は、後続の `status not in {"M","D","A"}` と重複するため削除してよい。両者を同じ「到達不能分岐」として一括削除してはいけない。

### 3. [real / 計画は partial] `_diff_entries` の R/C 二 path parse は残す必要があるが、プランにはその防壁を固定するテストがない

**根拠 (file:line)**

現 parser は `R`/`C` だけ 2 path を消費する ([git_state.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:565)、[git_state.py:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:579))。プランは parser を残すが scope 外として無検査にする ([plan.md:43](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan.md:43))。

**具体的な失敗シナリオ**

parser を「全 status は 1 path」と単純化すると、次の正規 R レコード 2 件は record 不足にならず誤整列する。

```text
R100\0frag1\0dst1\0R100\0frag2\0dst2\0
```

誤 parse 結果は概ね次になる。

```text
("R100", ("frag1",))
("dst1", ("R100",))
("frag2", ("dst2",))
```

landed の R 分岐まで削除されていれば、どれも `M FOLDED` / `D fragment` に一致せず、2 fragment の移動が漏れる。1 件だけの R なら末尾不足で fail-closed に見えるため、単一レコードテストだけではこの穴を捕捉できない。

**成果物影響**

複数 fragment の隠れた移動を landed 区間で見逃し、FOLDED receipt と canonical 台帳の対応が崩れる。

**推奨**

二 path parser を残し、R/C を各 2 件含む raw NUL record の arity テストを追加する。parser を消す案を採るなら 1 path として解釈せず、R/C を検出した時点で明示的に fail-closed にする。

### 4. [real residual／任意 fold commit 注入説は refuted] lock は生成を限定するが、壊れた fold の意味検証にはならない

**根拠 (file:line)**

`LandRequest` に fold SHA はなく ([dev_wave_land.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:77))、land は lock を取得して ([dev_wave_land.py:1668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1668))、plan/apply、docs 検査、path closure、commit、shape 検査を順に行う ([dev_wave_land.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1438)、[dev_wave_land.py:1460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1460)、[dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1513))。したがって、通常の外部入力から任意の prebuilt fold commit を渡す攻撃はできない。

一方、durable plan の復元は self-declared hash と schema の整合を検査するだけで ([spool_fold.py:1615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1615)、[spool_fold.py:1655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1655))、shape verifier も親 blob との意味照合をしない。

**具体的な失敗シナリオ**

壊れた plan/apply が次を生成する。

- worklog の過去部分を削除する。
- archive にはその過去部分と高類似だが、試行値を 1 件だけ改変した構文上有効な内容を書く。
- README と FOLDED を正規形式で更新する。
- fragment を GC する。

hash、対象 path、docs 構文は自己整合できる。現行では archive が `Cnnn worklog→archive` と判定され偶然拒否されるが、変更後は `M worklog + A archive + M README + M FOLDED + D fragment` となり受理される。lock は競合を止めるだけで、この意味差を検出しない。

また、プランの新規正例は `test_dev_waves_git_state.py` 内の人工 commit に留まり、実際の lock/apply/docs/staging 経路を通さない。既存 lock テストも rotation を生成しない ([test_dev_wave_land.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_wave_land.py:1563))。

**成果物影響**

worklog/archive 内の試行値・参照本文が直接変わり、台帳とそれを引用する後続レポートが誤る。既発行の certified 選択値は直ちには変わらない。

**推奨**

real `plan_fold` を用いた lock 内 rotation 正例を `test_dev_wave_land.py` に追加する。壊れた apply に対しては land 側で `plan.targets.after_sha256` と commit blob を独立照合する。壊れた plan 自体も脅威に含めるなら、親 worklog から archive への意味相関が必要であり、現 scope のまま I1 を保証することはできない。

### 5. [real / brief・plan 不整合] I3 はプラン自身が反証している

**根拠 (file:line)**

brief の I3 は checker/daemon を含む他 caller の挙動を変えないとしている ([brief.md:48](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/brief.md:48))。しかしプランは checker の fold slot が fail→pass、daemon recovery が停止→受理へ変わると明記している ([plan.md:142](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan.md:142)、[plan.md:143](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan.md:143))。実コードも `declared.ok` を直接 slot/recovery 判定へ使う ([checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/checker.py:543)、[daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/daemon.py:1526))。

**具体的な失敗シナリオ**

所見 1 の commit と整合する schema v2 receipt が存在すると、変更前は checker の `fold-commit=fail(path-status)`、daemon は `AMBIGUOUS_RECOVERY`。変更後は `fold-commit=pass`、daemon は次 wave 継続へ進む。

**成果物影響**

checker レポートの `fold-commit` 値と daemon 台帳の terminal/recovery 状態が変わる。後続 wave が実行されれば、将来のレポート・選択対象にも波及する。

**推奨**

I3 を「公開 API、他 Git operation、reason/detail 変換は不変。ただし valid rotation の fold 判定とその consumer 状態遷移は意図した変更」と書き直す。checker と daemon について valid rotation 正例と所見 1 の adversarial 負例を追加する。

### 6. [unproven / 段 4 の process gate] I4 はプランに所有者がなく、まだ保証されていない

**根拠 (file:line)**

brief はコードとテストを Codex `role=author` が書くことを要求する ([brief.md:50](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/brief.md:50))。段 2 プランには実装単位の owner、author 子、patch 帰属が一切ない。一方 dispatcher は実装面を author 子へ限定する ([dev-wave.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/.claude/commands/dev-wave.md:34))。

**具体的な失敗シナリオ**

段 4 で owner を明記せず親が `git_state.py` またはテストを直接編集すると、挙動が正しくても I4 は破れる。

**成果物影響**

数値・受理集合は変わらないが、実装 commit の provenance と wave の監査済み集合が無効になる。

**推奨**

plan v2 にコード・テストの単一 author owner と、親は統合だけを行う境界を明記する。

静的検査のみであり、pytest は実行していない。

## 総括

must-fix 候補:

- I1: `R fragment→rotation` が `D+A` 化して全既存制限を通る。意味相関を追加するか、I1 と scope を正直に狭める。
- I2: landed の R 元 fragment 分岐を残し、R/C 二 path parse をテストで固定する。
- lock 内の実 rotation 正例と、壊れた plan/apply の負例を追加する。
- I3 を実際の checker/daemon 状態遷移に合わせて修正する。
- 段 4 で I4 の author ownership を明示する。

nit / 既存残存穴:

- fold slot の明示 `R/C` 拒否は閉集合判定と重複しており、ここだけの削除は安全。
- `A rotation ⇒ M archive/README.md` は shape verifier では要求されない既存の非対称性。ただし通常 land は `check_docs.py` の archive 到達性検査で未掲載 archive を拒否するため、今回新設される通常 land 穴とは判定しない。