---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-cleanup-dangling-audit
seq: 1
---

## 新規

### {{F:branch-deleted-with-unlanded-work}}. ahead>0 のブランチが検査なしに消され、未 land 作業が到達不能になった [手順漏れ]

- 事象: `[T-213]` を名乗る commit 4 本 (tip `77db32c`、`tools/pegasus_policy.py` ほか実装 7 ファイル)
  が main 未取り込みのまま、ブランチ `codex/dev-wave-improve` ごと消えた。2026-08-03 22:58 に
  「ahead=4・main に不在」を実測して報告した後、08-04 08:07 には branch が消えていた。worklog 上
  `[T-213]` は現在も未了項目である。既定 `gc.pruneExpire` 未設定 = 約 2 週間で回収されるため、
  放置すれば失われていた (2026-08-05 に `rescue-t213` で reachable 化して確保)。
- 根本原因: 削除は cleanup-branches 以外の経路で行われた (同 §2 は ahead>0 の削除を禁じており、
  `git branch -d` は拒否するため同スキルでは起こり得ない)。**経路は未特定。** 加えて同 §1 は
  現存ブランチしか棚卸ししないため、消えた後は単発実行で検出できず、複数回実行をまたいだ
  記憶で偶然気づいたにすぎない。
- 恒久対応: `tools/audit_dangling_commits.py` — 到達不能 commit のうち、変更した path が
  main の tree にも他のどの local branch tip の tree にも存在しないものだけを報告する。
  `.claude/commands/cleanup-branches.md` §1 から呼び、**rc=0 のときだけ削除工程へ進む**。
- 再発検知: `orchestrator/tests/test_audit_dangling_commits.py::test_positive_control_deleted_branch_work_is_reported`
  (ブランチごと消した合成 repo で必ず鳴ることを固定) と、cleanup-branches 実行時の rc≠0 停止。
- 未了: **予防は未実装。** ahead>0 のブランチを検査なしに消した経路の特定が残る。本対応は
  「消えたあとに気づく」だけで、「消す前に止める」防壁ではない。また判定は path 名の有無だけを
  見るため、既存ファイルへの変更・削除・同名別内容・gitlink 更新は検出しない (出力に明示済み)。
  拡張の可否は裁定へ返した。

### {{F:merge-parentwise-diff-inflates-changed-paths}}. merge commit を親ごとの差分で見て、取り込んだ側を丸ごと「その commit の変更」と数えた [測り方の誤り]

- 事象: 上記監査を実 repo で走らせたところ、`orchestrator/campaign/reflux_origin_authority_v1.json`
  を巡って **3 件の誤検出**が出た。3 件はすべて merge commit だった。
- 根本原因: `git diff-tree -m` は「いずれか 1 つの親と異なる path」をすべて列挙する。merge が
  取り込んだ側の内容が丸ごと「この commit の変更」になり、実測で 1 件の merge が **123 path**
  (combined diff なら 3 path) を返していた。当該ファイルは main の履歴に実在し
  (`e6349be8` 作成 → `61fc5202` 削除、どちらも main 上)、`..._v2.json` へ改名されたものだった。
- 恒久対応: 親が 2 つ以上の commit は combined diff で評価する
  (`tools/audit_dangling_commits.py` の diff mode 分岐)。実 repo の報告は 3 件 → **0 件**。
- 再発検知: `orchestrator/tests/test_audit_dangling_commits.py::test_negative_main_side_of_unreachable_merge_is_not_reported`
  と、変異 M06 (combined 分岐を親ごと差分へ戻すと同 control が赤)。
- 併記: 親は当初「path が main の履歴に一度も現れていないこと」を追加条件にする案を出したが、
  敵対レビュー 2 本が「path 再利用時の見逃しを広げる」と反証し、真因の特定によって不要になった。
  **誤った修正案を実装前に捨てられたのは、レビューと実測の両方があったためである。**

### {{F:implementation-blocked-by-provenance-after-the-fact}}. 実装面を Claude が書いた commit が provenance 契約に阻まれ、検査緑のまま land 不能になった [手順漏れ]

- 事象: 上記恒久対応を先に実装した commit `e8d0c44c` は `check_docs` 緑・テスト緑だったが、
  実装面 path を持ちながら Codex `role=author` を欠いており (D95)、`check_ai_provenance.py` が
  rc=1 を返した。同 checker の full-history 監査は D95 導入 commit 以降を恒久的に検査するため、
  **この commit を main へ入れると main が永久に赤くなる**。
- 根本原因: 作業の入口が dev-wave ではなく cleanup-branches の自己改善だったため、
  「実装面がある = Codex author が要る」を確認する段が無いまま実装まで進んだ。
- 恒久対応: 旧 commit を land せず、参照案として渡したうえで現行 main の上に Codex `role=author` の
  実装子が書き直した (本 wave)。前セッションが trailer の書き換え (帰属の捏造) も無断 waiver も
  選ばず停止して裁定へ返したのは正しい。
- 再発検知: `check_ai_provenance.py` の `--message-file` preflight と full-history 監査。
  どちらも既存であり、本件は検知が働いた側の記録である。
- 派生して実測した事実: **両側が同じ実装面ファイルを変更していると、local main を取り込む
  merge commit 自体が D95 で赤くなる。** git が競合なく自動 merge しても、merge commit の
  combined diff (全 parent と異なる path) に実装面が残るためである。`DW-O17` は「競合解消が
  実装面なら Codex へ回す」と書くが、競合が出なかった場合の扱いを持っていない。

## 再発

### F26

- **再発: 2026-08-05** — main checkout の `.git/config` から `submodule.external/ccbench.*` の登録が
  消え、`git submodule status` が `-` prefix (未初期化) を返す状態を **2026-08-03 と 2026-08-05 の
  2 回**観測した。両回とも working tree の実体は健全で、HEAD は pin (`d706650`) 一致・clean であり、
  **失われていたのは登録だけ**である。復旧は `git submodule init external/ccbench` (config 書き込みのみ、
  通信もファイル書き換えも無し) で両回とも即座に完了した。F26 本文が記録する
  「worktree 側の `git submodule deinit` が共有 `submodule.*` 登録を消す」経路と**最終状態は同一**だが、
  **機序は同定できていない** — repo 内のコード・スクリプトに `git submodule deinit` の呼び出し箇所は
  無く、今回の消失を起こした主体は不明のままである。恒久対応は**検出のみ機械化済み**で、予防の実体は
  無い — `.claude/commands/cleanup-branches.md` §4 の事後検査が `-` prefix を検査しており、
  上記 2 回はいずれもこの検査で発見した (発火実績 2 回)。**機序未特定のため予防策は未実装**であり、
  この点を恒真な対応として扱わない。次に再発したら、消失の直前に走った worktree 操作の特定を
  先に行う。
