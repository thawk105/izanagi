---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-cleanup-cost-root-cause
seq: 1
title: /cleanup-branches の 98 分を実測分解し、根治 4 件・高速化 1 件・恒久対策 1 件を次の一手へ起票した (docs のみ、branch worktree-dev-wave-cleanup-cost-root-cause)
---

## 本文

- `/cleanup-branches` を 1 回完走した。取り込み済みの local branch 4 本
  (`worktree-dev-wave-t1643-has-include-pair` / `worktree-dev-wave-t1875-delta-min-gate` /
  `worktree-dev-wave-t2470-create-only-partial-write` / `impl-dev-wave-t2496-u1`) と、対応する
  `.claude/worktrees/` の 3 worktree を F26 の手順で撤去した。事後検査は submodule 初期化・
  main checkout の status 同一・detached 残骸 0 件をすべて通過し、repo file の変更と commit は
  行っていない。remote branch の削除と main の push はユーザー手番として引き渡した。
- **削除で最後の根を失う 4 commit について、ツールの判定が解けなかったので手で照合した。**
  `tools/check_branch_rescue.py` は `not_landed=0` を返す一方で 3 件を `indeterminate` のまま残した。
  commit が導入した path を main と 1 本ずつ突き合わせた結果、不在だったのは fold 済みの
  spool fragment 3 本だけ、insight は同一 blob で main に在り、相違した 2 file は main 側が
  後から改版した版 (erratum 17 行の追記と、可視文字不変の行末空白正規化) だった。
  **内容の喪失はない。** loose object の救出猶予は 2026-09-28。
- **所要 98 分の実測内訳** — dangling 監査 42.4 分 (うち repo 外走査 2429.3 秒 = 95.5%、
  抑止 0 件)、worktree 68 件の差分検査 14.4 分 (直列、1 件 12.7 秒)、救出検査 2 回 12.6 分
  (114 秒 + 644 秒)、branch 92 本への `git cherry` 直列が約 10 分、撤去 3 件が約 9 分。
  この数値が下記の次の一手の根拠である。
- **実行中に repo が動き続けた。** 棚卸し開始から終了までの約 100 分で worktree が 69 → 90、
  local branch が 72 → 92 に増え、棚卸し時点で存在した worktree 1 件と branch 1 件は別セッションが
  先に撤去した。削除は名指し + 期待 tip の照合付きで行い、tip が動いていたら中止する形にした。
- **near-miss を 1 件踏みかけた。** 追跡外ファイルを見るために撤去対象 worktree へ `cd` した時点で、
  背景セッションの作業ディレクトリが撤去対象の中へ移った。撤去前に main checkout へ戻して回避した。
  F51 と同型のため新規 F は採らず再発として記録した。
- ユーザー裁定 — 本実行の §6 で報告した自己改善候補を dev-wave のタスクへ起票すること、
  その際「恒久対策と根治」を重視し、並列化・高速化も落とさないこと。本 fragment はその起票である。

## 次の一手差分

### 新規

- {{T:cleanup-offrepo-scan-yield}} **P2・新規**: `/cleanup-branches` §1 必須の
  `tools/audit_dangling_commits.py` の repo 外走査が 1 回 2429.3 秒 (監査全体 2542.8 秒の 95.5%)
  を占める。走査対象は `/work/1/SFC/tanab/dev-wave-jobs` の job dir 1186 本・約 176 万 file で、
  得た一致は 17 file・23 対、**抑止は 0 件**だった (いずれも landed 参照なし)。所要上限 300 秒の
  8 倍超過は tool 自身が開示している。根治は走査を O(全 file) から O(候補) へ移すことで、
  候補は (a) 走査結果の索引化と増分更新、(b) 監査の定期実行と鮮度上限つき cache の消費、
  (c) job dir 自体の退役。着手はまず過去実行での抑止の実収量を測り、収量が構造的に 0 に近いなら
  走査を既定 off にする案も設計に含める。cleanup の所要はこの 1 項目で 4 割が決まる。
- {{T:codex-worktree-retirement-owner}} **P2・新規**: `.codex/worktrees/` の実装子 worktree
  58 件を誰も撤去しない。dev-wave 段 9 は実装子 worktree を撤去対象外とし、`/cleanup-branches`
  §2 は未コミット差分があるため削除できない。差分の中身は再生成可能物ではなく**実際の未コミットの
  ソース編集**で、数日前のものを含む (3 件抽出して確認)。掃除の費用は worktree 件数に比例する
  (差分検査 1 件 12.7 秒) ため、ここを塞がない限り高速化は件数の増加に追い越される
  (実測で 100 分に 21 件増えた)。根治は実装子 worktree の終端所有者と終端契約を決めること —
  wave 終了時に子の作業木を branch へ commit するか、破棄を記録して撤去可能にするか。
  どちらを採るかは所有と正本の変更を含むため裁定を要する。
- {{T:branch-rescue-path-first-assessment}} **P2・新規**: `tools/check_branch_rescue.py` の
  landed 判定が本 repo の規模で解けない。`--assessment-timeout-seconds` を既定 8 秒から上限の
  60 秒へ上げても、対象 3 commit のうち 1 件が `assessment-timeout`、2 件が
  `one-or-more-states-unproven` のまま残り、rc は 2 回とも 2 (可視化不完全) だった
  (所要 114 秒 → 644 秒)。**常に不完全を返す gate は警告として情報を運ばない。**
  今回 rc=2 を実際に解いたのは、commit が導入した path を main と 1 本ずつ突き合わせる照合で、
  数秒で終わり「不在は fold 済み spool fragment、相違は main 側の改版」と確定した。根治はこの
  path 照合を一次判定に据え、総当たりの状態証明を残余への fallback にすること。あわせて
  「fold 済み spool fragment の不在」を未証明ではなく既知正常として一級に扱う。
  上限 60 秒という定数自体が repo 規模に対して据え置きであることも併せて見直す。
- {{T:unreachable-ledger-notification-contract}} **P1・ユーザー裁定待ち**:
  `docs/unreachable-object-ledger.md` は entry 0 件のまま、監査が未記帳の到達不能 commit を
  30 件報告し続け、`ledger_notification_due` が毎回立つ。常時 due の通知は判断材料として
  機能せず、無視する習慣を作る。記帳して閉じるのか、既知良性の類型を entry 無しで認める契約へ
  変えるのかは台帳契約の変更であり、AI が単独で決めない。30 件の内訳は 8〜9 月の旧 wave の
  変異台帳・spec 類で、今回の掃除が作ったものではない。
- {{T:cleanup-gate-order-and-parallelism}} **P3・新規**: `/cleanup-branches` の棚卸しが直列で、
  安い判定と高い判定が混在している。実測で worktree 68 件の `git status` 直列取得が 14.4 分
  (1 件 12.7 秒)、branch 92 本への `git cherry` 直列が約 10 分。恒久対策は §1 / §2 の手順を
  (i) 安い gate (locked / ahead / HEAD の古さ) 先行、(ii) 高い gate (差分・占有) は残った対象だけ、
  (iii) 独立な読み取り probe の並列化、(iv) `git cherry` は ahead>0 の対象だけ
  (実測 92 本中 13 本) へ直すこと。撤去の `rm -rf` は F26 の「1 件ずつ」の趣旨
  (一括ループが timeout で殺され半端に消える) を保ったまま、各々へ長い timeout を与えれば
  並列化できる。安全条件は 1 つも緩めない。
- {{T:cleanup-forbid-cd-into-retirement-target}} **P3・新規**: `/cleanup-branches` §3 が、
  背景セッションが**自分で**撤去対象 worktree へ入る経路を塞いでいない。§3 は「cwd 固定の
  背景セッション」を想定するが、cwd が固定でないセッションが `cd` した場合も harness が追従して
  作業ディレクトリが撤去対象の中へ移る (F51 の再発として記録)。恒久対応は、対象へ `cd` せず
  `git -C` と絶対 path で扱うことを §3 に明示し、撤去 step の cwd 検査を手順に据えること。
  今回の実行では script 内の cwd 検査が実際に機能した。command 本文は Codex skill との
  whole-file SHA-256 parity 契約下にあり checker 定数の同時更新を要するため、
  実装面として Codex author が要る。
