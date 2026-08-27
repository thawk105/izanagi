# 段 1 brief — [T-1825] branch 削除前の rescue gate (+ [T-1826])

base = local main `b253e0b7`。branch `worktree-dev-wave-t1825-rescue-gate`。受入・実測は login node
(この wave は計測を持たない。全走は `tools/dev_wave_wait.py acceptance` 経由)。

## 純増 (親が実測した既存被覆。機構名でなく性質で archive まで検索した)

- `tools/check_branch_landed.py` (D922、schema `izanagi-branch-landed-v1`) は **既に**
  branch の closure を列挙し、`landed` / `not-landed` / `indeterminate` の 3 値と
  `branch_delete_authorized` / `land_authorized` / `manual_review_required` を JSON で出す。
  実測: `worktree-dev-wave-t1219-carry-same-id` で rc=2・3 秒・closure 1 commit。
- したがって本 wave の純増は「判定器を作ること」では**ない**。純増は次の 3 点である。
  1. **判定器と削除を繋ぐものが何も無い。** 実測: `branch_delete_authorized` (line 335) と
     `land_authorized` (line 326) は **無条件定数 `False`** で一度も再計算されない。これは
     道具の意図どおりで (docstring が "This tool never authorizes landing or branch deletion")、
     壊れた gate ではなく **gate が存在しない**ことを意味する。呼び手も無い —
     `git grep` を tools/ orchestrator/ docs/ .claude/ .agents/ hooks/ へ全件かけて 7 hit、
     すべて自身のテストと decisions/archive の記述。`/cleanup-branches` §1 は
     `audit_dangling_commits.py` と `check_worktree_occupancy.py` は回すが
     `check_branch_landed.py` は回さない。
  2. **closure の定義が「削除で失われる集合」と一致しない。** `_enumerate_closure` は
     `rev-list <branch> --not <main>` で、main 以外の ref を root に入れない。
  3. **gc 期限が出力に無い。** 実測: `gc.auto` / `gc.pruneExpire` / `gc.reflogExpire` /
     `gc.reflogExpireUnreachable` は全て未設定 = 既定 (6700 / 2.weeks.ago / 90 days / 30 days)。
     loose object は現在 **6268 個**で、auto gc の閾値 6700 に近い。窓は時間だけでなく
     「次に git command が gc --auto を引くとき」でも閉じうる。
- `/cleanup-branches` §1 が削除前に回す `audit_dangling_commits.py` は
  **既に到達不能なもの**を検出する道具で、**これから到達不能になるもの**は検出しない。
  [T-1756] の事故はこの差そのもの。「削除後に人が気づく構造しかない」は gate の意味で真。

## scope

- **in**: (a) 削除候補 branch 集合を受け、削除後の ref 集合に対する真の到達不能閉包を出し、
  各 commit を `check_branch_landed.py` で判定し、gc 期限を添えて JSON + fail-closed rc を返す道具。
  (b) `/cleanup-branches` への配線。(c) [T-1826] の期限付き台帳と通知。
- **out**: `tools/dev_wave_cleanup.py` (下記 (P1))、[T-1828]・[T-1823] (ユーザー裁定待ち)、
  D978 の CAS 削除への移行 (別裁定。ただし本 gate は D978 と矛盾しないこと)、手動 gc。

## 不変条件 (破ったら成果物が変わる — DW-G05)

1. 道具は **何も削除せず、ref も object も変えない**。削除を authorize もしない。
   ユーザーの枠組みどおり「消す判断の前に閉包を可視化する道具」であり、AI の削除防壁ではない。
   破ると T-1756 の逆側 (勝手に消す) の事故面を新設する。
2. **閉包の過小報告を禁じる。** `--not` 側の root 集合は「削除後も残り、かつ gc が root として
   honor するもの」だけに限る。honor されない root を入れると失われる commit を見落とす。
   複数 branch を同時に消す場合は削除後の集合で 1 回で計算する (1 本ずつでは互いに隠し合う)。
3. **`indeterminate` は決して authorize へ倒れない。** 打ち切り・timeout・上限超過・parse 不能・
   ref 移動は全て `indeterminate`。D922 の 3 値規則をそのまま継承する。
4. **報告する期限は真の窓の下界**である。時間の窓と、gc.auto 閾値への近さの両方を出す。
   上界を書くと「まだ間に合う」と誤らせて不可逆に失う。
5. 手動 gc を打たない。`prune`・`gc`・`reflog expire` を道具から呼ばない。

## 親の provisional 裁定 (段 3 の攻撃対象)

- **(P1) `tools/dev_wave_cleanup.py` を編集面から外す。** 根拠は 2 つ。(a) 実測: `_delete_branch`
  の直前 (line 990-995) で expected-tip CAS と `merge-base --is-ancestor <ref> refs/heads/main` を
  再検査しており、通過時の closure は構造的に空。(b) 起動時の編集面重複検査 (下記) で
  唯一実在した重複がこの file。**攻撃点: (a) は本当に十分か。ancestry 検査と削除の間の窓、
  submodule gitlink、reflog 由来の別 root を見落としていないか。**
- **(P2) 新規 tool を 1 本足し、`check_branch_landed.py` は改造しない。** 後者は D922 の
  判定契約を持ち、そこへ root 集合の変更を入れると既存の判定意味が動く。
  **攻撃点: 2 本に割ると closure の定義が repo 内で二義化する (DW-O13 の同名識別子二義化)。**
- **(P3) [T-1826] の通知発火点は `/cleanup-branches` §1 とする** (DW-G04 が要求する実在 path)。
  wave 起動 gate へ挿すと、古い未裁定 1 件で全 wave の起動が止まる。
  **攻撃点: §1 は人が掃除を始めたときしか走らない。窓が閉じる前に届く保証になっていない。**
- **(P4) 台帳は repo 内 tracked とする。** repo 外だと [T-1824] と同じ「半年後に到達できない」に陥る。
  **攻撃点: 到達不能 sha を tracked file へ書くと、その file 自体が sha を延命させない
  (object は ref から到達可能にならない) — 台帳が救出の代わりに見えてしまう。**

## 成果物の形

- `tools/<新規>.py` + `orchestrator/tests/test_<同名>.py`
- `.claude/commands/cleanup-branches.md` の §1/§2 配線 (byte 予算あり。`check_docs.py` で検査)
- [T-1826] の台帳 file + 通知経路
- spool fragment (worklog / decisions / failures)、`output/insights/2026-08-26_t1825-rescue-gate/`

## 並列分割方針

正しさ防壁 (不可逆な喪失) に触り受理集合を変えるため **軽量版にしない**。段 2 プラン 1 本、
段 3 敵対相談 2 本 (レンズ: 閉包の過小報告 / 恒真な gate と発火点)、段 5 実装は
(A) 閉包・期限の中核、(B) 台帳と配線 に分ける。段 6 review 2 本 + 変異 matrix。

## 起動時の編集面重複検査 (ユーザー指示、実測)

- branch tip: 全 28 branch を対象 path 限定 diff → 重複 **0 件**。
- worktree 未 commit: **53 worktree 全件**走査 → 実在の重複は
  `dev-wave-b4-prereg-enactment` の 1 件だけ (`tools/dev_wave_cleanup.py` +62/-20 と
  `test_dev_wave_cleanup.py` +230 を staged 保持)。内容は占有判定
  (`_assert_unoccupied` / `_occupancy_issue_summary`) で `_delete_branch` ではない。
- ユーザーが名指しした 3 本のうち `dev-wave-b10-backoff-shape-orthogonal` と
  `dev-wave-flaky-holds-20260826` は対象 path に差分なし → 懸念は 3 本中 1 本だけ成立。
- (P1) により重複面はゼロになる。
