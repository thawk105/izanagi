# 段 4 裁定 (plan v2)

## 1. 置き場所と入口予算

- **採用:** 新規 L2 節 `DW-O28` を `docs/dev-wave/operations.md` の `DW-O27` の後に作る。
  読む契機は**新規の条件 dispatch 27「land 成功後の自己撤去直前」**とする。
- **不採用:** 条件 23 への併載 (luna 所見 2 = real)。「発火点は land 成功後」と主張しながら
  land 前の条件で読むのは、入口の読み込み契約「条件成立操作の直前に再評価して読む」と矛盾する。
- **親の誤りを 2 件訂正する。**
  - `DW-O25` 不変更と 158 byte 追記撤回は **D433 ではなく D432 の末尾**にある (luna 所見 4)。
  - 「予算引き上げを提案しない」は D432 のその場の選択であり、現行方針ではない。
    **D671 (2026-08-23 ユーザー裁定)** が「`COMMAND_LIMITS` は必要な分だけ引き上げてよい。
    幅は最小限とし、何を収容するために何 byte 上げたかを決定記録に残す」と定めている。
- **入口:** 条件 27 の行は実測 87 byte。`.claude/commands/dev-wave.md` は 9,497 → 9,584 byte。
  `tools/check_docs.py` の `COMMAND_LIMITS` を **9,500 → 9,584 へ引き上げる**。
  最長行は 66 文字で上限 140 に影響しない。
- **全角括弧の半角化 (28 byte) は行わない。** 意味不変だが、pin 済み統治ファイルへ無関係な
  churn を入れる。条件 20 の trigger は全文が `CONDITION_TRIGGER_CONTRACT` に逐語登録されて
  おり (luna 所見 3)、圧縮のために pin を触る取引に見合わない。
- `DW-O28` は `DEV_WAVE_EXACT_VISIBLE_SECTIONS` の節全文 exact pin へ追加する (luna 所見 6)。
  破壊操作と権限境界を書く節だからである。
- `DW-O28` 本文に `tools/dev_wave_land.py` を再掲しない。checker が同 path を
  operations 全体で exact 1 件かつ `DW-O23` 内だけに制限する (luna 所見 7)。

## 2. D271 admission の裁定

- **条件 1 (発火実績) = 成立。** F26 の 2026-08-01 と 2026-08-05 の実害。
  D271 本文が要求するのは「実際の wave での失敗または near miss」であり、独立 2 例ではない。
  **「独立 2 例」「DW-G03 を満たす」とは書かない** (luna 所見 1 の該当部分 = real)。
  F26 自身が「同一経路」と明記しているためである。
- **DW-G03 は本件に不適用と裁定する。** DW-G03 は族全体への制度一般化を縛る規範であり、
  本件は単一発火点への義務追加である。
- **条件 2 (機械代替なし) = 成立。** `check_wave_startup.py` は観測専用、`dev_wave_land.py` は
  land 後 cleanup を呼ばず、daemon も持たない (luna が実測)。
- **条件 3 (意味検索で反証なし) = 成立。** `DW-O20` = wave 開始時、`DW-O23`/`DW-O25` = land 前、
  `/cleanup-branches` §3 = 明示 cleanup 実行時。同一発火点「land 成功後」の運用正本は無い。
- **記録義務:** 探索範囲・検索語・hit・real/refuted を decisions fragment に残す (D271 の要求)。

## 3. D204 の扱い

luna 所見 8 = real、採用。本発話を D204 の通常適用としない。decisions fragment に
**「D204 を狭く部分 supersede する恒久例外」**として、次の束縛付きで記録する。

- 対象は同一 invocation の exact wave path / ref だけ。
- `tested_tip` が `refs/heads/main` の祖先であること。
- `git branch -d` のみ。`-D`、force、remote、一括は禁止。local のみ。
- その他の branch には D204 をそのまま維持する。

## 4. sol 所見 (破壊安全性) の裁定

| # | 主題 | 判定 | 措置 |
|---|---|---|---|
| 1 | 自己所有の証明なし | real / 部分採用 | lease・capability は D205 により scope 外。common git-dir 一致・branch↔tip 束縛・占有 rc=0・clean・ancestry の 5 条件で代替し、残余を記録 |
| 2 | inode 検査後の path 差替え | real / 不採用 | quarantine rename は `.claude/worktrees/` 配下に `.git` 欠落残骸を作る経路そのもので、その残骸は全 wave の land を rc=21 で止める既知事故。攻撃者モデルは単一ユーザーの協調 session に不成立。残余を記録 |
| 3 | path 正規化の定義不足 | real / 採用 | raw argv の `..`・末尾 slash・symlink component を拒否。lexical == strict realpath == porcelain path の byte 一致を要求。検証済み path object 以外を削除経路へ渡せない構造にする |
| 4 | `branch -d` の CAS 欠如 | real / 部分採用 | 直前に ref == tested tip を再確認し、`Deleted branch X (was <sha>)` の sha を事後照合する。`update-ref -d <old>` には替えない (git 自身の merged 判定という最後の防壁を失う)。残余を記録 |
| 5 | `unreachable.cwd_permission` の見落とし | real / 採用 | `status == "unoccupied"` に加え `occupants`・`issues`・`same_uid_cwd_unreachable` が空、`unreachable.cwd_permission == 0` を全部要求 |
| 6 | ignored bytes と remote job | real / 部分採用 | ignored 一括拒否は `__pycache__` 等で常時不成立になるため採らない。`DW-O28` へ「投入した job の終端後に呼ぶ」を書き、tool は tracked + untracked の空を要求。残余を記録 |
| 7 | global prune が他 record を巻き込む | real / 採用 | `worktree prune --dry-run --verbose --expire=now` を先に走らせ、候補のうち **directory が現存するもの**が 1 件でもあれば停止する |
| 8 | land の部分成功を弾けない | real / 採用 | `git rev-parse --git-path izanagi-spool-fold-state.json` の実在を fail-closed 条件に加える。`DW-O28` にも親の `landed`/`already-landed` 確認を書く |
| 9 | reflog-only commit の消失 | real / 採用 | `git rev-list --walk-reflogs refs/heads/<branch> --not refs/heads/main` が空であることを要求 |
| 10 | 中断からの再入不能 | real / 採用 | preflight を 5 状態の分類にし、残りの手順だけ実行する。transaction journal は D205 で scope 外 |
| 11 | F26 の構造保証不足 | real / 部分採用 | git 実行を単一 wrapper に集約し、許可 subcommand の runtime allowlist で `worktree remove` / `submodule deinit` / `branch -D` を構築方法によらず拒否。実 submodule fixture は作らない (D205) |
| 12 | 実測の一般化 | real / 採用 | 測定記録を checkout `59ef288c` の現 worktree に限定して書き、harness が常に lock するという一般化を削る |

## 5. plan からの採用

- **rc 契約を正直にする。** `rm -rf` 以後の失敗は `partial` として rc=30 で出す。
  brief の I5「非 0 なら何も撤去せず」は preflight (rc=2/20/21/22) にだけ成立すると訂正する。
- **撤去順は `branch -d` を最後**に置く。`rm` が失敗しても branch が残り、`branch -d` 自身が
  最後の ancestry 防壁になる。`/cleanup-branches` §3 は branch 削除を 2 番目に置いており
  食い違うが、§3 の是正は段 8 の cleanup-branches 改善候補へ回す。
- CLI は 4 引数必須・推論ゼロ。`--force` / `--all` / `--resume` を設けない。

## 6. 変異事前登録 (DW-M01、B-057)

実装後に次の 4 変異を登録する。単一理由性は実装後にコードで確認し、確認できない変異は
登録せず実効 gate へ再照準する。

- MUT-1: ancestry 検査の rc 判定を常に成立へ倒す → 期待 kill = ancestry 負例。
- MUT-2: 占有 payload 検査から `unreachable.cwd_permission == 0` を落とす → 期待 kill = 同負例。
- MUT-3: fold state file の不在検査を落とす → 期待 kill = active transaction 負例。
- MUT-4: git subcommand allowlist から `worktree remove` の拒否を落とす → 期待 kill = 禁止 verb 検査。

## 7. 成果物影響 (DW-G05)

`DW-O28` と tool を実装しないと、land 済み wave の worktree が積み上がる。`.git` を欠く残骸が
1 本あるだけで `tools/dev_wave_land.py` は rc=21 を返し、持ち主に関係なく全 wave の land が
止まる。その状態では worklog / decisions / failures への追記自体ができなくなる。

---

# 段 4 裁定の訂正 (2026-08-23 14:35 JST、親の実走で判明した新事実)

DW-O12 に従い、裁定手順と実行手順の食い違いを裁定側で訂正する。実装子の自己申告ではなく
親の実測が根拠である。

## A1 — `worktree list --porcelain -z` は使えない

この機体の git は 2.34.1 で、`git worktree list --porcelain -z` は
`error: unknown switch 'z'` / rc=129 (実測)。`--porcelain` 単独は rc=0。

**訂正:** `git worktree list --porcelain` を使う。`-z` が無いことによる path 曖昧性は、
対象 path に改行・制御文字が含まれる record を**判定不能として拒否する**ことで塞ぐ。

## A2 — `rev-list --walk-reflogs <ref> --not refs/heads/main` は誤った命令形

`--walk-reflogs` は `--not` 側の ref にも適用されるため
`fatal: cannot walk reflogs for refs/heads/main` / rc=128 (実測)。版依存ではなく用法の誤りで、
段 4 裁定 4-9 の記述が間違っていた。`git rev-list --walk-reflogs <branch>` 単独は rc=0。

**訂正:** `git rev-list --walk-reflogs refs/heads/<branch>` で reflog 上の commit を列挙し、
各 SHA へ `git merge-base --is-ancestor <sha> refs/heads/main` を掛ける。
1 件でも非祖先があれば停止する。

## A3 — 占有 payload の要求を実測で緩める

段 4 裁定 4-5 は sol 所見 5 を採って `unreachable.cwd_permission == 0` と
`same_uid_cwd_unreachable == []` を要求した。**この共有 login node では両方とも恒久的に
成立しない。**

- `unreachable.cwd_permission` の実測は 2,020〜2,035。これは cwd を読めない**他ユーザーの
  process 数**であり、対象 worktree とは無関係で、構造的に観測できない。
- `same_uid_cwd_unreachable` の実測は 3 件で、中身は自 session の `(sd-pam)`・`sshd`・
  `ssh-agent`。ssh session である限り常在し、worktree へ chdir することはない。

**訂正:** 要求は `status == "unoccupied"` かつ `occupants == []` かつ `issues == []` とする。
`unreachable.cwd_permission` と `same_uid_cwd_unreachable` は**要求せず、値を報告へ出す**。
根拠は、cmdline 走査は列挙した全 PID を覆うため、worktree 内で走る worker は
cwd が読めなくても cmdline 側で捕まることである。

## A4 — `check_worktree_occupancy.py` の zombie 誤分類を直す (scope 追加)

**実測:** ホスト上の pid 1035937 は `State: Z (zombie)` の python3 である。zombie は
`/proc/<pid>/cwd` を持たないが `/proc/<pid>/` 自体は残るため、`_pid_disappeared()` が
False を返し、`issues` へ `{"error": "missing", "source": "cwd"}` が積まれる。
結果、**どの path を対象にしても `status = "indeterminate"` / rc=2 を返し続ける**。
2 回連続で同じ pid で再現した。

これは占有検査の恒久的な不成立であり、`/cleanup-branches` §3 の「rc0 のみ進み、
rc2=判定不能は停止」も同じ理由で満たせない。worktree が 31 本溜まっている説明がつく。
zombie は定義上 cwd も fd もアドレス空間も持たず、何も占有できない。

**訂正:** scope に次の 2 file を追加する。

- `tools/check_worktree_occupancy.py`
- `orchestrator/tests/test_check_worktree_occupancy.py`

`/proc/<pid>/cwd` が `FileNotFoundError` で、かつ `/proc/<pid>/status` の `State:` が
`Z` で始まる場合は、issue にせず**非占有として扱う**。件数は payload の新 field
(`unreachable.zombie` 等) へ出して沈黙させない。他の `FileNotFoundError` の扱いは変えない。

これは安全検査の受理集合を変えるので、変異 MUT-5 を追加登録する。

- MUT-5: zombie 判定を落として従来どおり issue へ積む → 期待 kill = zombie 非占有テスト。

## A5 — 段 5 実装子の扱い

launcher の receipt は `outcome=not_accepted` / `evidence_status=invalid` だった。
親が rollout を検算した結果、`session_meta` 1 件・`turn_context` 2 件・events 216 行すべて
妥当な JSON・`termination_verified: true`・codex exit 0・上限抵触なしで、**内容の欠陥ではなく
launcher 側の evidence 収集の取りこぼし**である。子の編集は 6 file すべてツリーに存在する。

子の自己申告は**未検証**として扱う。親の実走では
`orchestrator/tests/test_dev_wave_cleanup.py` が **selected=10 / failed=10** で全滅した
(rc=22、占有判定不能)。よって段 6 は「レビュー → fix」ではなく、**先に fix で実測赤を閉じ、
その後に敵対レビュー 2 本**を掛ける順にする。死んだコードを 2 本のレビューに掛けない。

## A6 — 段 5 の子が書いたテストのうち、撤回済み述語を固定した 2 ケースの更新を許可する

fix 子が正しく停止した。`orchestrator/tests/test_dev_wave_cleanup.py` の
`test_rejects_occupancy_payload_failures_without_mutation` の `cwd-permission` と
`same-uid-cwd` の 2 ケースは、訂正 A3 で撤回した旧述語を期待値として固定している。
両立しないので、fix 子は「期待値を変えるな」の指示に従って止まった。

**裁定:** この 2 ケースは**本 wave の段 5 の子が数十分前に書いた成果物**であり、
保護対象の「既存テスト」ではない。撤回済みの裁定を固定しているので更新を許可する。

許可の範囲は厳密に次に限る。

- 対象は `orchestrator/tests/test_dev_wave_cleanup.py` の当該 2 ケースだけ。
- `cwd_permission != 0` と `same_uid_cwd_unreachable != []` を**受理側の正例へ移す**。
  すなわち `rc=0` / `status="unoccupied"` / `occupants=[]` / `issues=[]` / `worktree` 一致
  であれば、`cwd_permission=2030` と same-uid 到達不能 process があっても `removed` になる。
- `occupants != []` (rc=21) と `issues != []` (rc=22) の拒否ケースは**そのまま残す**。
- 本 wave より前から存在するテストの期待値は 1 件も変更しない。特に
  `orchestrator/tests/test_check_worktree_occupancy.py` の既存期待値は保護対象のままで、
  A4 の zombie 変更で既存期待値が落ちるなら**報告して止まる**規律を維持する。

---

# 段 6 レビュー所見の裁定 (2026-08-23)

sol は NO-GO、luna は must-fix 2 件。sol の判定に同意し、下記を閉じるまで land しない。

## sol (破壊安全性・実装忠実性) 11 所見

| # | 主題 | 判定 | 措置 |
|---|---|---|---|
| 1 | cwd 不読 + 相対 argv の live worker を取り逃す | real / 部分採用 | lease と job 終端証明は D205 で scope 外のまま。ただし `same_uid_cwd_unreachable` の**無条件受理をやめる**。comm が session 基盤の固定 allowlist (`sshd` / `ssh-agent` / `(sd-pam)` / `systemd`) に無い pid が 1 つでもあれば rc=22 で停止する。実測でこの 3 種以外は現れず、worker の cwd は同 uid なら読めるため、fail-closed 側へ倒しても運用は成立する。残余を記録 |
| 2 | worktree HEAD reflog を見ていない | real / 採用 (must-fix) | 対象 administrative gitdir の `logs/HEAD` が参照する commit も main ancestry 検査へ入れる。detached commit の fixture を足す |
| 3 | 状態 c が record と branch の束縛を要求しない | real / 採用 (must-fix) | 5 状態を**完全な積 predicate** として列挙する。c は record が detached・branch なし・HEAD == tip を必須にする |
| 4 | allowlist が先頭 2 要素しか見ず `branch -d -f` を通す | real / 採用 (must-fix) | verb 単位をやめ、**完全 argv schema** で照合する。branch は `("branch","-d","--",<branch>)` だけを許可する |
| 5 | identity 検査と lookup の非原子性 | real / 不採用 | 既裁定 (訂正前 §4-2) のとおり。quarantine rename は `.claude/worktrees/` 配下に land を止める残骸を作る経路そのもの。残余を記録 |
| 6 | `branch -d` に CAS がない | real / 不採用 | 既裁定 (§4-4) のとおり。repository-wide lock は D205 で scope 外。残余を記録 |
| 7 | 状態 e が直前再検査なしで `already-clean` を返す | real / 採用 | e でも path・record・ref の全不在を返却直前に再取得し、競合を検出したら拒否する |
| 8 | `KeyboardInterrupt` で partial が出ない | real / 採用 | mutation 開始後の捕捉を `BaseException` へ広げ、rc=30 の 1 行を出してから再送出する |
| 9 | A3 の診断値が捨てられている | real / 採用 | 診断を成功経路まで伝播し、**stderr へ出す**。stdout は `removed` / `already-clean` の 1 行のままとする |
| 10 | テストが過剰決定で単一防壁を検証しない | real / 採用 | 各信号を 1 つだけ不正にした payload、HEAD-only commit、`-d` と force option の順列、record/branch 混成状態を足す |
| 11 | 同一 invocation の所有権が未証明 | real / 不採用 | 既裁定 (§4-1) のとおり。capability/lease は D205 で scope 外。残余を記録 |

## luna (正本整合) 4 所見

| # | 主題 | 判定 | 措置 |
|---|---|---|---|
| 1 | `DW-O28` の逐語どおりでは動かない | real / 採用 (must-fix) | 完全な呼出し形 (main worktree から、4 引数すべて) と、fail-closed 述語を極性込みで書く。`DW-O28` は現在 695 / 1,000 byte で 305 byte の余裕がある |
| 2 | 破壊開始後の `partial` を worklog へ書く経路が無い | real / 部分採用 | 段 9 の後に記録段は無いという指摘は正しい。`DW-O28` の文言を「撤去できない理由は報告し、次 wave の worklog へ記録する」へ改める。post-land 記録 commit の新設は scope 外として残余に記録する |
| 3 | 入口上限 9,584 を固定する独立 test が無い | real / 採用 | 上限が exact 9,584、実体も exact 9,584、9,585 が拒否されることを独立 literal test で固定する |
| 4 | `DW-O28` の位置が pin されていない | nit | reviewer 自身が成果物影響なしと判定。DW-G05 に従い nit とし、追加 review wave を起こさない |

## 分割

fix は 2 単位に分け、**逐次**に投入する (同一 worktree で workspace-write の子を並行させない)。

- 単位 A: `tools/dev_wave_cleanup.py` + `orchestrator/tests/test_dev_wave_cleanup.py`
  (sol 1 部分・2・3・4・7・8・9・10)
- 単位 B: `docs/dev-wave/operations.md` + `tools/check_docs.py` +
  `orchestrator/tests/test_check_docs.py` (luna 1・2・3)

## A6 の適用範囲の拡張

sol 所見 1・10 と 所見 3・4 の是正は、本 wave の段 5/fix 子が書いたテストの期待値を変える。
A6 と同じ理由 (本 wave 自身の成果物であり、撤回・是正された述語を固定している) で、
`orchestrator/tests/test_dev_wave_cleanup.py` の当該ケースの更新を許可する。
**本 wave より前から存在するテストの期待値は 1 件も変更しない**という制約は維持する。

## 変異事前登録の追加

- MUT-6: 状態 c の record 束縛検査を落とす → 期待 kill = record/branch 混成の負例。
- MUT-7: allowlist の完全 argv schema 照合を verb 単位へ戻す → 期待 kill = `-d -f` 負例。
- MUT-8: worktree HEAD reflog の ancestry 検査を落とす → 期待 kill = HEAD-only commit 負例。

---

# 変異 probe の結果と DW-M02 の再照準 (2026-08-23)

probe (全件 SURVIVED 期待、`--runner-mode local`) の結果は baseline PASSED、
8 変異中 KILLED 相当 6・SURVIVED 2。

- MUT-2 / 3 / 5 / 6 / 7 / 8 は期待どおり殺された。観測 node は本走の期待集合に使う。
- **MUT-1 (preflight の branch ancestry 検査を無効化) が SURVIVED。**
- **MUT-4 (allowlist へ `worktree remove --force` を追加) が SURVIVED。**

## MUT-1 の mask 源

`tools/dev_wave_cleanup.py` の `branch-recheck` 段に 2 つ目の ancestry 検査があり、
preflight 側を殺しても最終的には停止する。しかし**この 2 層目は `rm -rf` と prune の後**に
あるため、preflight が壊れた場合の実害 (worktree が消えてから拒否される) を防げない。
既存の ancestry 負例テストは、この差 (rc=20 で無傷 / rc=30 で撤去済み) を区別していない。

**再照準:** preflight の ancestry 拒否を単独で pin するテストを足す。非祖先 branch では
rc=20 で止まり、**worktree・record・branch・HEAD がすべて無傷**であることを要求する。
これで MUT-1 は単一理由で殺される。

## MUT-4 の mask 源

禁止 verb のテストは (a) source 走査と (b) 実行 argv spy の 2 面だけで、
`_validate_git_argv` が禁止 argv を**拒否すること自体**を検証していない。
allowlist に項目を足しても、誰も呼ばなければ両テストとも緑のままになる。

**再照準:** `_validate_git_argv` が `("worktree","remove",...)`、`("submodule","deinit",...)`、
`("branch","-D",...)` を拒否することを直接 pin するテストを足す。

## 手順

1. fix 子で上記 2 テストを足す (production の変更は不要と見込む)。
2. 焦点走で緑を確認する。
3. MUT-1 と MUT-4 を再 probe し、KILLED になることを確認する。
4. 全 8 変異の期待 node を完全集合で固定した本走を回す。

---

# comm allowlist の撤回 (2026-08-23、実測による 2 度目の gate 撤回)

sol 所見 1 の部分採用として入れた「same-uid で cwd を読めない process の comm が
`sshd` / `ssh-agent` / `(sd-pam)` / `systemd` の固定 allowlist に無ければ rc=22」を**撤回する**。

## 実測

焦点走が 11 件赤になり、全件の理由が
`same-uid process cwd is unreachable and comm is not allowlisted: 'nqs_shpd'` だった。
`nqs_shpd` はバッチスケジューラの常駐 process で、**テストを計算ノードへ dispatch した瞬間に
同 uid で現れる**。走行が終わった直後に再測すると消えており、そのときの payload は
`status=unoccupied` / `occupants=0` / `issues=0` / same-uid 3 件
(`(sd-pam)` / `sshd` / `ssh-agent`) / `cwd_permission=2213` で rc=0 だった。

つまりこの allowlist は、**本プロジェクト自身の作業フロー (dispatch を伴う走行) の最中にだけ
破れる**。撤去が必要になるのはまさにその直後であり、gate として成立しない。

## 裁定

- comm allowlist の要求を外す。payload の形式検査 (`unreachable` が dict で `cwd_permission`
  を持つ、`same_uid_cwd_unreachable` が list) と診断値の報告は**残す**。
- 要求は `status == "unoccupied"` かつ `occupants == []` かつ `issues == []` に戻す (A3 のとおり)。
- sol 所見 1 は **accepted residual** として記録する。「同 uid・non-dumpable・cwd が対象・
  cmdline に対象 path を含まない live worker」は検出できない。cmdline 走査は全 PID を覆うため、
  worktree 内で走る worker は通常 cmdline 側で捕まる。
- MUT-2 を再照準する。allowlist が消えるので、`issues == []` の要求を落とす変異へ替える。

## 一般化 (段 8 候補)

**追加した gate の述語が実環境で満たせるかを、採用前に実測する。** 本 wave では同じ型を 2 度
踏んだ (`unreachable.cwd_permission == 0` で 1 度目、comm allowlist で 2 度目)。
どちらも「field は実在するが、到達可能な値が要求を満たさない」型である。
