# 段 1 brief — dev-wave 段 9 の自己 worktree/branch 撤去経路

## scope

- S1: 新規 `tools/dev_wave_cleanup.py`。land 成功後に wave 自身の worktree と branch を
  fail-closed で撤去する単一経路。
- S2: 新規 `orchestrator/tests/test_dev_wave_cleanup.py`。fail-closed 回帰。
- S3: `docs/dev-wave/operations.md` の `DW-O25` へ land 後の自己撤去義務を統合。
  `tools/check_docs.py` の `DEV_WAVE_DW_O25_SECTION_LITERAL` と
  `orchestrator/tests/test_check_docs.py` の合成 fixture を同じ commit で更新する。
- S4: 台帳。F26 へ「経路を新設し 2 回の再発で指摘された欠落を閉じた」を追記する fragment、
  D204 の適用範囲 (自 branch は main の祖先のときだけ削除) を確定する decision fragment。

scope 外: 既存の worktree 31 本 / branch 114 本の一括掃除 (`/cleanup-branches` の担当)。
`/cleanup-branches` §3 に残る F51 由来記述の是正 (別 command の自己改善 gate に属する)。

## 確定済みユーザー裁定

2026-08-23 の本 wave 引数「dev-wave を終えた後、main land まで成功したら自分のワークツリー・
ブランチを掃除するよう dev-wave を改善して」。これが D204 の要求する「対象を特定した
ユーザー指示」に当たる。対象は dev-wave 自身が作った worktree と branch に限る。

## 不変条件

- I1: branch 削除は `git merge-base --is-ancestor <branch> refs/heads/main` 成立時のみ。
  `git branch -d` を使い `-D` は使わない。
- I2: `git worktree remove` と `git submodule deinit` を使わない (F26)。
  撤去は unlock → detach → `rm -rf` → `git worktree prune`。
- I3: 撤去前に (a) `tools/check_worktree_occupancy.py` rc=0、(b) 対象 worktree の
  `git status --porcelain` 空、(c) cwd が対象 worktree の外、(d) 対象が primary worktree でない、
  を全部満たす。1 つでも欠ければ何も消さずに非 0 で止まる。
- I4: 1 worktree ずつ処理し、一括ループにしない (F26 の 2026-07-30 事象)。
- I5: 冪等。既に撤去済みなら `already-clean` で rc=0。
- I6: 新規 L2 節を作らない。`.claude/commands/dev-wave.md` は無変更 (残 3 byte)。
  `tools/check_docs.py` の byte 予算値を引き上げない。

## 成果物の形と成果物影響 (DW-G05)

rc 契約は 0=`removed` / `already-clean`、非 0 = 何も撤去せず理由を stderr へ。
実装しない場合、land 済み wave の worktree が `.claude/worktrees/` に積み上がる。`.git` を欠く
残骸が 1 本あるだけで `tools/dev_wave_land.py` は rc=21 を返し、**持ち主に関係なく全 wave の
land が止まる**。その状態では worklog / decisions / failures への追記自体ができなくなる。

## provisional 裁定 (親の暫定判断であり攻撃対象)

- (P1) 置き場所は `DW-O25` への統合。新規節 `DW-O28` + 条件 27 は D271 の第 3 条件
  「同一発火点の既存正本もなし」を満たさない (条件 25 = land 起動直前) ため却下する。
- (P2) 手順は tool に集約し、docs は呼び出しと fail-closed 条件だけを書く。
  `/cleanup-branches` §3 を dev-wave の手順として引用しない。
- (P3) 本 wave 自身の段 9 で新 tool を実走して dogfood する。
- (P4) 計算ノード job の残存検査は tool に入れない (マシン密結合)。
  代わりに worktree の `git status --porcelain` 空を要求する。
- (P5) 全 9 段で回す。破壊操作と権限境界 (D204) に触るため DW-C00 の軽量版条件を満たさない。

## 実測済みの前提 (main checkout 59ef288c)

- dev-wave の docs / command に撤去義務・手順ポインタは 0 件。
- F26 は 2026-08-01 と 2026-08-05 の 2 回、「段 9 の撤去手順の正本が `/cleanup-branches` §3 に
  あることを指していない」と記録している。独立 2 例 (DW-G03) を満たす。
- 予算: 入口 9,497/9,500、L1 10,624/10,625、L1.5 9,565/9,566、`DW-O25` 649/1,000。
- `check_docs.py` baseline rc=0。
- EnterWorktree が作る worktree は harness が `git worktree lock` 済み
  (reason: `claude session <name> (pid ...)`)。撤去には unlock が要る。

## 並列分割

実装子 1 本 (tool と test は同一所有)。段 3 は 2 レンズ (破壊安全性 / docs 予算と pin 閉包)。
段 6 は review 2 本 + fix 1 本。変異事前登録は段 4 で行う。

## 訂正 (2026-08-23 13:05 JST、段 2 起動後に判明した新事実)

(P1) は既裁定に反するため撤回する。

- **D433** は「`docs/dev-wave/operations.md` は変更しない。`DW-O25` は checker が節全文を
  exact pin しているため 1 byte も触らない」と明記している。
- **D280** は `DW-O25` を可視 H2 節全体 exact pin の規範節 4 つの 1 つに指定している。
- **D279** は `DW-O25` の L2 admission 自体が D271 条件 2・3 を満たさない一回限りの適用除外で
  あり、先例にしてはならないと定めている。
- D433 は `DW-O23` へ 158 byte を追記して L1 予算超過 (10783 > 10625) となり、
  **予算引き上げを提案しない方針**で追記を取り下げた先例も残している。

**訂正後の (P1):** 新規 L2 節 `DW-O28` を `docs/dev-wave/operations.md` に作る。D271 の 3 条件は
次の理由で全部満たすと判断する — 条件1 発火実績 = F26 の 2 回の再発、条件2 機械代替なし =
現在この義務を強制する機構が存在しない、条件3 同一発火点の既存正本なし = 発火点は
「land 成功後」であり `DW-O23`/`DW-O25` は land の前を規定し、`/cleanup-branches` §3 は
別の発火点にある (F26 が「指していない」と 2 度記録)。

**訂正後の (P2):** 入口 `.claude/commands/dev-wave.md` の条件 dispatch 行 23 の読む節へ
`` , `DW-O28` `` を足す (約 11 byte)。残余 3 byte を補うため、同ファイルの全角括弧 7 対
(`（F23/F24）`、`（最遅: 段 1 前）` 等) を半角化して約 28 byte を意味不変で捻出する。
`tools/check_docs.py` の byte 予算値は引き上げない。全角括弧の装飾セルが tests/tools に
pin されていないことは grep 0 件で実測済み。

**却下:** `tools/dev_wave_land.py` 本体へ撤去を組み込む案。land は
`cwd must be the exact wave worktree` を要求する (`tools/dev_wave_land.py:1078`) ため、
land 自身が自分の cwd を消す立場になり成立しない。撤去は land 後に main checkout 側から行う。
