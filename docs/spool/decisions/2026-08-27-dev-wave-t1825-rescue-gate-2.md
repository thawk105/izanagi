---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1825-rescue-gate
seq: 2
---

## {{D:rescue-gate-visualizes-not-authorizes}}. 掃除の可視化は削除の可否ではなく絵の完全さを返す

**決定:** 掃除で到達不能になる commit を出す道具は、`branch` の削除と `worktree` の撤去を
**ひとつの操作**として受け、rc は「削除してよいか」ではなく「**完全な絵を描けたか**」だけを表す。
配線先は `/cleanup-branches` の §1 (棚卸し) と §5 (ユーザーへの報告) とし、
§2 (削除条件) には置かない。`deletion_authorized` に類する field を出力へ作らない。

rc は `0` = 可視化が完全、`2` = 技術的に不完全 (timeout・上限超過・root の移動・
壊れた administrative entry・下界を立てられない・台帳 parse 不能)、`3` = 未記帳の通知あり、
`64` = usage error とする。`not-landed` は可視化の内容であって技術的失敗ではないので `0` に含む。

**理由:**
- **§2 へ置くと構造的に一度も発火しない。** 現行 §2 は `ahead=0` (main へ取り込み済み) の
  branch だけを削除対象にする。`ahead=0` は定義上 `rev-list <b> ^main` が空なので、
  喪失閉包も必ず空になる。述語がその候補集合に含意されており、保護と数えられない。
- **判断するのはユーザーである。** branch 削除はユーザー指示があるときだけ行う運用なので、
  道具の仕事は「消すな」と言うことではなく、消す判断の前に材料を出すことである。
- **削除の可否を表す field は、呼び手を持たないまま残る。**
  `tools/check_branch_landed.py` の `branch_delete_authorized` は無条件定数 `False` のまま
  production の呼び手ゼロで存在している (本 wave の実測: `git grep` 全件 7 hit がすべて
  自身の test と台帳の記述)。同じ形をもう 1 つ作らない。
- **掃除操作の単位でモデルにしないと、安全だと誤って報告する。** 実測で
  `worktree-dev-wave-t1629-ratification-broker` は branch だけ消す前提で喪失 0 件、
  その worktree も畳む前提で 12 commit 失われた。`/cleanup-branches` §3 は worktree を
  撤去するので、branch 削除だけをモデルにすると「失われるものは無い」と報告した直後に失う。

**却下した選択肢:**
- **§2 の削除条件へ閉包検査を置く** — 上記のとおり恒真になる。この gate の阻止側が
  意味を持つのは D978 (内容着地済みの非祖先 branch を CAS つきで削除対象へ入れる) の
  施行後であり、それは別裁定である。
- **`indeterminate` があっても rc=0 を返す** — ユーザーの要求は
  「判定できないものが残る間は通さない」であり、これに反する。
- **候補を 1 本ずつ判定して和を取る** — 同じ commit を指す候補どうしが互いを隠して
  0 件になる。実測で、同じ commit を指す 2 つの detached worktree が互いを隠していた。

## {{D:conservative-floor-is-a-complete-answer}}. 「今すぐ失われうる」は不完全ではなく最も切迫した完全な答え

**決定:** 到達不能になりうる object の喪失期限は、常に**下界**として出す。
`deadline_status` を 3 値にする。

- `determinate` — その object 自身の mtime と実効 prune 期限から下界を導けた。rc へ影響しない。
- `conservative-floor` — 下界は立つが object 固有の保持期間を観測できない。
  下界は評価時刻とし「いつ失われてもおかしくない」と読む。**rc=0 のまま**とする。
- `indeterminate` — **下界そのものを立てられない**。ここだけが rc=2 へ倒れる唯一の経路。

`conservative-floor` へ倒す事由は次の 4 つに限る。object が packed または loose-and-packed、
alternate ODB にしか存在しない、prunable worktree が保持する root の期限、
`gc.pruneExpire` を安全に解釈できない。

**理由:**
- **実データの過半数が packed である。** 本 wave の実測で、喪失閉包に入る commit 39 件のうち
  23 件 (59%) が packed だった。packed を判定不能として rc=2 にすると、実 repo の
  過半数の branch で道具が「絵を描けない」と返る。常に止まる関門は迂回される。
- **fail-closed の向きは「何も言えない」ではなく「今すぐ失われうる」である。**
  評価時刻を下界とする答えは、判断に使える最も切迫した答えであって、情報の欠落ではない。
- pack の mtime は object 個別の到達不能時刻ではないので、`determinate` にしてはならない。
  この禁止は 3 値化のあとも変わらない。

**却下した選択肢:**
- **保守的下界を `indeterminate` として rc=2 にする** (実装の初版) — 上記のとおり過半数で止まる。
- **prunable worktree の期限を git の `should_prune_worktree` と同じ判定で再現する** —
  保守負債が大きい。`conservative-floor` へ倒すほうが安全側で単純である。
- **総 loose 数と `gc.auto` の比較で余裕を出す** — git 2.34.1 の判定は fanout 1 個の標本であり、
  総数との差は発火までに作れる object 数ではない。実測で総数由来の余裕は 432、
  標本由来の余裕は 5 だった。台帳 schema からも総数由来の field を削り、
  標本の fanout・件数・閾値・heuristic の版に置き換えた。

## {{D:removed-reflog-is-a-loss-source}}. 削除される ref の reflog は引き算側でなく足し算側である

**決定:** 掃除で消える ref (候補 branch、撤去対象 worktree の HEAD) の reflog が持つ
old/new OID のうち commit 型のものは、喪失閉包の**正側**へ入れる。
負側から外すだけでは足りない。reflog を読めない・parse できない・
object が missing のときは `rc=2` とし、空として扱わない。

**理由:**
- git 2.34.1 の `git branch -d` は ref と `logs/refs/heads/<name>` の両方を消す。
  したがって候補 reflog にしか残っていない commit は、削除によって**失われる側**である。
- 負側から外すだけの実装では、その commit は閉包に現れず、道具は「絵は完全だ」と言いながら
  対象を丸ごと落とす。これは本 wave が防ごうとした事故そのものである。
- 期限のある root (残存 reflog、prunable worktree) は逆に負側へ入れてはならない。
  入れると、そこにしか支えられていない commit が閉包からも台帳からも消える。
  期限を長く見積もる誤りではなく、報告そのものが消える誤りになる。
  これらは閉包に残し、種別と失効の下界を retention に記録する。

**却下した選択肢:**
- **候補 reflog を単に負 root から外す** — 上記のとおり喪失を見落とす。
- **検証できない worktree-private ref を負 root へ入れる** — gc が root として honor する範囲を
  起動側の ref store と同一視できない。入れる向きが過小報告になるので、
  存在を検出したら `issues` へ出して rc=2 にする。
