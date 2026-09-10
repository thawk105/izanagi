# 段 4 裁定とプラン v2 — [T-1825] / [T-1826]

親が段 3 の全所見を real/refuted に裁定し、プラン v2 と変異事前登録を確定する。
両レンズとも NO-GO を返した。プラン v1 は採らない。

## 0. 親が独立に再現・追加した実測 (裁定の根拠。子の申告をそのまま採らない)

| ID | 実測 | 値 |
|---|---|---|
| N1 | `printf 'main\n--not\nmain\n' \| git rev-list --stdin` | `fatal: options not supported in --stdin mode` |
| N2 | `<oid>` + `^<oid>` を stdin へ | 正常。`b2a38a46 ^main` が 1 commit を返す |
| N3 | non-main local branch と checkout 中の数 | 31 本中 27 本が checkout 中 |
| N4 | `ahead=0` の branch と checkout 中 | 20 本中 18 本 |
| N5 | git 2.34.1 の loose auto-gc 標本 (`objects/17`) | **22** 個。閾値 `(6700+255)/256` = **27**。残り 5 |
| N6 | `git count-objects -v` の総数 | 6422 (wave 開始時 6268。live に増える) |
| N7 | 真の root 集合での喪失閉包が**非空**の branch | **31 本中 10 本**。1〜12 commit |
| N8 | detached worktree 25 本を**一括**撤去したときの喪失 | **0 commit** (1 本ずつの和も 0) |

N5 は親 brief と段 2 プランの両方の誤りを正す。**「6268 / 6700 で残り 432」は git 2.34.1 の
発火余裕ではない。** 実際の判定は fanout 1 ディレクトリの標本であり、現在は 22/27 で残り 5 である。

N7 は `DW-O13` が要求する値域の実測である。喪失閉包は空・非空の両方が実データで到達可能。

N8 は「worktree 撤去側は現時点で喪失ゼロ」を示す。この repo の detached worktree は
すべて何らかの ref から到達可能だった。

## 1. レンズ A の裁定

| # | 主張 | 裁定 | 扱い |
|---|---|---|---|
| A1 | `rev-list --stdin` は `--not` を受理しない | **real** (N1/N2 で親が再現) | 採用。`^<oid>` へ |
| A2 | root 棚卸しが private ref と壊れた administrative entry を尽くさない | **real** | 採用 (縮約。下記 2.3) |
| A3 | 期限付き root (reflog・prunable worktree) を恒久的な負 root にすると閉包そのものを過小報告する | **real / 最重要** | 採用。設計の中心を変える |
| A4 | P1 を撤回し `dev_wave_cleanup.py` を編集面へ戻せ | **real な観測 / scope 外の是正** | 下記 1.1 |
| A5 | `6268/6700` と headroom 432 は発火余裕を表さない | **real** (N5) | 採用 |
| A6 | M6 は完全な root inventory を実証していない | **real** | 採用。記録を降格 |
| A7 | M9 の一回走査から「重複ゼロ」とは言えない | **real** | 採用。段 5 直前に再検査 |
| A8 | 禁止 command 検査が孫 process を覆わない | **real** | 部分採用 (境界を明示) |

### 1.1 A4 (`dev_wave_cleanup.py` を編集面へ戻すか) — **観測は real、本 wave では実装しない**

観測は正しい。親も現物で確認した。

- `tools/dev_wave_cleanup.py:919-931` の sha 照合は `git branch -d` の**診断行を削除後に**
  parse するもので、CAS ではない。line 991 の tip 比較と削除の間に branch が動けば、
  別 tip を消してから事後に気づく。
- line 986 の `git worktree prune --expire=now` は branch 削除**前**に worktree の
  administrative entry を落とす。preview 時の worktree root が削除時まで残る保証は無い。

それでも本 wave では実装しない。理由は 3 つで、いずれも実測または台帳に基づく。

1. **是正には `docs/dev-wave/operations.md` の DW-O28 本文を変える必要がある。** 同節は
   「branch は `git branch -d` だけで消し `-D` を使わない」と命じている。真の CAS
   (`git update-ref -d refs/heads/<b> <expected>`) はこの命令と両立しない。D978 の CAS 裁定は
   `/cleanup-branches` を対象とし、DW-O28 を対象としていない。DW-O28 へ広げるのは新しい裁定である。
2. **M9 で実在が確認された唯一の編集面重複がこの file である** (`dev-wave-b4-prereg-enactment` が
   staged 保持)。
3. 本 wave の scope は「消す判断の前に閉包を可視化する道具」であり、DW-O28 はユーザーが
   判断しない自動経路である。

**扱い:** failures 台帳へ 1 件、次の一手へ 1 件 (新規 T)。裁定パッケージでユーザーへ返す。
実装したふりにしない。

## 2. レンズ B の裁定

| # | 主張 | 裁定 | 扱い |
|---|---|---|---|
| B1 | = A1 | **real** | 採用 |
| B2 | 候補がほぼ checkout 中で gate が恒常停止する | **real** (N3/N4) | 採用。ただし解法を変える (2.2) |
| B3 | 「全 commit landed」を rc=0 条件にすると実データで到達不能 | **real** | 採用。rc の意味を変える (2.1) |
| B4 | D978 未施行では gate が非空 closure の削除経路に繋がらない | **real** | 採用。配線先を変える (2.1) |
| B5 | 台帳が永久に空でも検出できない | **real** | 採用。ただし解法を変える (2.5) |
| B6 | `/cleanup-branches` は通知の発火点として頻度を保証しない | **real** | 部分採用 (2.6) |
| B7 | scope 外の境界が成果物に固定されていない | **real** | 採用 |
| B8 | 台帳が object を延命しない事実が prose にしかない | **real** | 採用 |

### 2.1 中心の裁定 — gate は「削除の可否」ではなく「判断の材料」を作る

ユーザーの指示は明示的である。「branch 削除自体はユーザー指示があるときだけ行う運用なので、
この gate は『AI が勝手に消さないための防壁』ではなく『**消す判断の前に閉包を可視化する道具**』
として設計すること。」

B3/B4 はこの指示とプラン v1 の食い違いを突いている。したがって次を確定する。

- **rc の意味は「完全な絵を描けたか」だけ。** 削除の可否を表さない。
  - `0` = 可視化が完全 (root snapshot 安定、閉包完全、全 commit の判定と期限を出せた)
  - `2` = 技術的に不完全 (timeout、上限超過、ref/worktree/index/reflog の移動、
    壊れた administrative entry、期限算出不能、台帳 parse 不能)
  - `3` = 可視化は完全で、台帳に期限が近い未裁定 entry がある
  - `64` = usage error
  - **`1` は使わない。** `not-landed` があることは技術的失敗ではない。JSON の field で表す。
- **`deletion_authorized` という field を作らない。** `check_branch_landed.py` の
  `branch_delete_authorized` が無条件定数 `False` のまま呼び手ゼロで残っている (M3/M4)。
  同じ形をもう 1 つ作らない。代わりに `decision_inputs` に事実だけを置く。
- **配線先は `/cleanup-branches` の §1 (棚卸し) と §5 (ユーザー引き渡し)。**
  §2 (削除条件) には置かない。理由は測定済みである — 現行 §2 は `ahead=0` のみを削除対象とし、
  `ahead=0` は定義上 `rev-list b ^main` が空なので、**§2 に置いた閉包検査は構造的に一度も
  発火しない**。これは述語が候補集合に含意されて恒真になる形であり、保護と数えてはならない。
- **代わりに §5 の報告義務にする。** 削除しなかった branch の閉包・判定・期限を、
  ユーザーへ渡す報告に必ず含める。N7 のとおり現時点で 31 本中 10 本が非空であり、
  この経路は今日から実データで発火する。
- **D978 の施行 ([T-1754]) がこの gate の阻止側を初めて意味あるものにする。**
  依存関係として記録し、[T-1754] を先行条件として明示する。本 wave では施行しない
  (削除権限の拡大であり、ユーザー裁定の射程を親が広げない)。

### 2.2 B2 の解法 — 「branch 削除」ではなく「掃除操作そのもの」をモデルにする

プラン v1 は「候補が checkout 中なら `indeterminate`」とした。N3/N4 のとおり候補の 9 割が
checkout 中なので、この形は恒常停止になる。レンズ B は「先に detach しろ」と提案したが、
それは道具に repo を変えさせる方向であり不変条件 1 に反する。

**採る形:** 入力を `--branch <名>` と `--retire-worktree <絶対 path>` の 2 種にし、
**それら全部が同時に消える前提**で 1 回だけ閉包を計算する。これは `/cleanup-branches` が
実際に行う操作 (branch 削除 + worktree 撤去) そのものである。候補が checkout 中でも
`indeterminate` にせず、その worktree を撤去対象に含めるか否かで結果が変わることを出す。

- 撤去対象に含めない worktree の HEAD と index は**残る root** として負側へ入れる。
- 撤去対象に含める worktree の HEAD と index は負側へ入れない。
- N8 のとおり、現時点で detached worktree 25 本を一括撤去しても喪失は 0 である。
  この値は「撤去側は今のところ安全」を意味するだけで、機構が不要であることは意味しない。

### 2.3 A2/A3 の解法 — root を 3 種に分け、期限付き root を負 root にしない

これが設計の中心である。A3 の指摘どおり、**保持期限のある root を恒久的な負 root にすると、
対象 commit は閉包からも台帳からも完全に消える。** 期限を少し長く見積もる誤りではなく、
報告そのものが消える誤りである。

root を次の 3 種に分ける。

1. **恒久 root (負側へ入れる):** 撤去対象でない `refs/*` 全部
   (`heads` / `tags` / `remotes` / `stash` / `notes` を namespace で狭めない)、
   撤去対象でない worktree の HEAD、および同 worktree の index にある commit 型 object。
2. **期限付き root (負側へ入れない。閉包に残し `retention.additional_sources[]` に記録する):**
   残存 reflog の old/new oid、prunable worktree の HEAD/index/reflog。
   各々に種別・失効の下界・根拠設定 (`gc.reflogExpire` / `gc.reflogExpireUnreachable` /
   `gc.<pattern>.reflogExpireUnreachable` / `gc.worktreePruneExpire`) を添える。
3. **root にしないもの:** 撤去対象 branch 自身の ref と reflog
   (git 2.34.1 の `git branch -d` は `logs/refs/heads/<b>` も消す)、alternates の ref、
   `ORIG_HEAD` / `FETCH_HEAD` / `MERGE_HEAD` / `CHERRY_PICK_HEAD` / `REVERT_HEAD` などの
   非 ref pseudoref。`refs/bisect/*` `refs/worktree/*` `refs/rewritten/*` は **ref である**が
   worktree-private であり、gc が root として honor する範囲を invocation worktree の
   ref store と同一視できない。**検証できない private ref を負 root へ入れない**
   (入れる向きが過小報告)。存在を検出したら `issues` へ出し `rc=2` にする。

さらに `$common/worktrees/*` の administrative entry を `git worktree list --porcelain` と
相互照合し、片方にしか無い entry・読めない entry・`refs/replace/*` / grafts / shallow の
存在は `rc=2` にする。

### 2.4 A5 の解法 — gc.auto は標本 heuristic として出す

`headroom = gc.auto - count` を出さない。git 2.34.1 の判定を版付きで再現する。

- 標本 fanout (`<objects>/17`) の entry 数と、閾値 `(gc.auto + 255) / 256` を出す。
  実測 N5 は 22 / 27 である。
- `gc.autoPackLimit` (既定 50) と現在の pack 数も別 field で出す。
- **encode 済みの git 版と実行中の版が一致しないときは `proximity: "indeterminate"`** にする。
  総数 (`count_objects.count`) は観測値としてだけ出し、余裕の根拠にしない。

### 2.5 B5 の解法 — 台帳の非空虚性を既存の道具で機械検査する

レンズ B の `prepared` → `pending` 遷移案は、削除直前に durable な書込みを要求するため
不変条件 1 (道具は repo を変えない) と衝突する。代わりに **既に repo にある観測器**を使う。

`tools/audit_dangling_commits.py` は repo 全体の**既に到達不能な** commit を報告する。
これを台帳の照合相手にする。

- `--ledger-check`: 同 audit が報告した要確認 commit のうち、台帳に entry を持たないものを
  列挙する。1 件でもあれば `rc=3` (通知あり)。
- これで「削除したのに台帳へ書き忘れた」が**機械で検出される**。台帳が空でも、
  audit が 0 件なら正常、audit が非 0 件なら赤になる。空台帳を一律に異常とする検査は
  削除履歴ゼロの正常状態を拒否するため作らない (レンズ B の指摘どおり)。
- 台帳の全 entry と出力に `object_retention_provided: false` を機械可読な固定 field として置く
  (B8)。台帳は所在の索引であって保持機構ではない。

### 2.6 B6 の扱い — 通知の発火点は実在するものだけ実装し、頻度保証は裁定へ返す

`DW-G04` は「発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ実装する。
書けなければ設計メモに留める」と定める。

- **実装する:** `/cleanup-branches` §1 での `--ledger-check` 実行。これは実在の path である。
- **実装しない:** 「gc の窓が閉じる前に必ず届く」保証。`/cleanup-branches` の実行間隔は
  worklog から推定できない (親も探したが実行日の系列を機械で引ける記録が無い)。
  gc の窓は 2 週間、N5 のとおり標本は閾値まで残り 5 である。
  **高頻度な発火点の選定を裁定パッケージへ返す。** 候補は `tools/check_wave_startup.py`
  (全 wave 起動時に走る) だが、古い未裁定 entry 1 件で全 wave の起動が止まる形は採れないため、
  非阻止の通知にするか別経路にするかはユーザー裁定が要る。

## 3. プラン v2 (確定)

- 新規 `tools/check_branch_rescue.py`、schema `izanagi-branch-rescue-v1`。
- 入力: `--branch <名>` (複数可)、`--retire-worktree <絶対 path>` (複数可)、`--ledger-check`。
  全候補を **1 回**で受け、まとめて閉包を出す (1 本ずつの和は互いに隠し合う)。
- 閉包: `git rev-list --stdin` へ `<oid>` と `^<oid>`。`--not` を stdin へ置かない。
- root は 2.3 の 3 分類。期限付き root は負 root にしない。
- 期限は loose object の mtime + `gc.pruneExpire` を**下界**とし、packed / alternate /
  算出不能は assessment time を下界として `deadline_status: "indeterminate"`。
  gc.auto は 2.4 の標本 heuristic。
- `check_branch_landed.py` は変更せず CLI として呼ぶ。用語は `deletion_loss_closure` と分ける。
  1 件 8 秒・全体 300 秒・64 件を上限とし、超過分は黙って落とさず `indeterminate` として全件出す。
- rc は 2.1 のとおり。`deletion_authorized` field を作らない。
- 台帳 `docs/unreachable-object-ledger.md`、schema `izanagi-unreachable-object-ledger-v1`、
  `object_retention_provided: false` を固定 field に持つ。
- `/cleanup-branches` は §1 に `--ledger-check`、§5 に閉包・判定・期限の報告義務を足す。
  §2 の削除条件は変えない。
- `tools/dev_wave_cleanup.py`、`tools/check_branch_landed.py`、
  `tools/audit_dangling_commits.py` と既存テストは変更しない。
- **保証の名前を成果物へ固定する (B7):** 「`/cleanup-branches` dispatcher を通る掃除の可視化」。
  手で打つ `git branch -d`、DW-O28 の自動撤去、D978 の未施行部分は覆わない。
  この 3 つを README と JSON の `coverage_boundary` へ明記する。

### 段 5 の所有分割 (素集合)

- **単位 A:** `tools/check_branch_rescue.py`、`orchestrator/tests/test_check_branch_rescue.py`
- **単位 B:** `docs/unreachable-object-ledger.md`、
  `orchestrator/tests/test_branch_rescue_ledger.py`、`.claude/commands/cleanup-branches.md`

単位 B は単位 A の CLI 契約だけを使い、`tools/check_branch_rescue.py` を編集しない。
docs (insights・spool fragment) は親だけが書く。

## 4. 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」ことを実装確定後に
コードで確認し、確認できなければ登録を取り下げて実効 gate へ再照準する。

| ID | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| m01 | root 分類表 | 期限付き root (残存 reflog) を恒久 root 側へ移す | KILLED | 閉包から commit が消える。他層に reflog を復元する経路は無い |
| m02 | root 分類表 | 撤去対象でない worktree の HEAD を負側から落とす | KILLED | 喪失閉包が過大になる。root inventory の完全性検査は別 assert |
| m03 | root 分類表 | 撤去対象 branch 自身の reflog を負側へ入れる | KILLED | 失われる commit を隠す。過小報告の直撃 |
| m04 | root 分類表 | `refs/*` を `heads`+`tags` に狭める | KILLED | `remotes`/`stash` が保持する commit を過大報告 |
| m05 | 閉包計算 | 候補を 1 本ずつ計算して和を取る | KILLED | 互いに隠し合う fixture でのみ差が出る |
| m06 | 閉包計算 | stdin の `^<oid>` を `--not` 行へ戻す | KILLED | git が `fatal` を返し閉包が作れない (N1) |
| m07 | rc 集約 | `indeterminate` が残っていても rc=0 を返す | KILLED | 技術的不完全を完全と偽る |
| m08 | rc 集約 | `not-landed` を rc≠0 にする | KILLED | 内容判断を技術的失敗に混ぜる (B3 の逆行) |
| m09 | 期限 | loose の下界を `now + pruneExpire` (上界) にする | KILLED | mtime が古い object で下界が未来へずれる |
| m10 | 期限 | packed object の下界に pack の mtime を使う | KILLED | object 個別の到達不能時刻でない |
| m11 | 期限 | `deadline_status` を常に `determinate` にする | KILLED | 算出不能を確定と偽る |
| m12 | gc.auto | 標本 heuristic を総数比較 (`count` vs `gc.auto`) へ戻す | KILLED | N5 の 22/27 と 6422/6700 で判定が逆転する fixture |
| m13 | 上限 | 上限超過 commit を出力から落とす | KILLED | 黙った切り捨て。件数の一致検査で殺す |
| m14 | 台帳 | `--ledger-check` を常に rc=0 にする | KILLED | audit 非 0 件 fixture で書き忘れを見逃す |
| m15 | 台帳 | `object_retention_provided` を `true` にする | KILLED | 台帳が保持機構だと偽る |
| m16 | read-only | 禁止 command allowlist から `gc` の拒否を外す | KILLED | argv 記録の assert |
| m17 | snapshot | 開始・終了の root digest 照合を外す | KILLED | 走行中の ref 移動を見逃す |

**正例 (受理集合を縮小しないことの確認、DW-M01):**

| ID | 内容 | 期待 |
|---|---|---|
| p01 | 閉包が空で全 root が安定な入力 | rc=0、`deletion_loss_closure.commit_count == 0` |
| p02 | 閉包が非空で全 commit `landed`、期限が確定 | rc=0 (「削除可」ではなく「絵が完全」) |
| p03 | 閉包が非空で `not-landed` を含む | rc=0。内容は JSON field |
| p04 | 台帳が空で audit も 0 件 | `--ledger-check` rc=0 |

## 5. `DW-G05` — 実装しない場合の成果物影響

- 2.3 (期限付き root) を実装しない → 到達不能になる commit が閉包に現れず、
  台帳 entry も作られない。[T-1756] と同じ喪失が、道具がある状態で再発する。
- 2.1 (rc の意味) を実装しない → 非空閉包の rc=0 が実データで到達不能になり
  (N7 の 10 本のうち D922 の判定率から見て大半が `indeterminate`)、関門は迂回される。
- 2.4 (gc.auto) を実装しない → 「残り 432」という表示が、実際には残り 5 の状態を安全と見せる。
- 2.5 (台帳の非空虚性) を実装しない → 台帳が永久に空のままでも誰も気づかない。

## 6. ユーザーへ返す裁定パッケージ (本 wave では実装しない)

1. **DW-O28 の branch 削除に真の CAS を入れるか** (A4)。観測は real。
   `docs/dev-wave/operations.md` の DW-O28 本文と、D978 の射程を DW-O28 へ広げるかの裁定が要る。
2. **期限通知の高頻度な発火点** (B6)。`/cleanup-branches` は手動起動で、
   間隔が gc の 2 週間窓に間に合う保証が無い。
3. **[T-1754] (D978 施行) を先行させるか。** この gate の阻止側は D978 施行後に初めて意味を持つ。
