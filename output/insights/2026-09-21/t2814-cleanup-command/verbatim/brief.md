# 段 1 brief (親、2026-09-21 00:5x JST、起点 local main 285477c0052819e272e390d798f6442658075866)

**研究前進:** K2 loop 3 巡の campaign 原本 (論文ストーリー §8 B-6 / fig12 の provenance の強さ) が cleanup で消えた F1034 の再発防止。
止めている研究は無い (下流影響の評価は T-2815、別 wave)。土台の最小差分 = `/cleanup-branches` §2・§3 に命令 2 つ + Codex overlay 2 項 + exact pin の追随。

**scope (依頼の逐語 `T-2814-origin.md`):**
1. `.claude/commands/cleanup-branches.md` §2 に (a) 未追跡 `output/` (exploration/・env/) を候補にする前に該当 wave の insight「証拠の所在」節で repo 外原本かを確かめる、
   §3 に (b) 退避 tar の `-C` 順と entry 数の検算を撤去の前提にする。予算 6,204 bytes (現物 6,181) の下で D782 手順 1 段目 (既存記述の削減) で収容、上限は動かさない。
2. `.agents/skills/cleanup-branches/SKILL.md` の overlay に同じ 2 点 (予算 3,100、現物 2,646)。
3. [T-2601] carry の閉鎖記録 (worklog fragment)。
4. F1034 恒久対応末尾の「[T-2814] で別 wave」を supersede 追記で現況へ (failures fragment、routing 5: 入口は命令、failures は事象)。
scope 外: command 本文以外の gate・検査・台帳・一般化の追加。稼働中の cleanup session の final は待たない。

**段 1 で実測した前提 (依頼の想定を更新するもの):**
- **「docs のみ」は成立しない。** `tools/check_docs.py` が両 file を whole-file SHA-256 で pin (`CLEANUP_COMMAND_SHA256` / `CODEX_CLEANUP_BRANCHES_SKILL_SHA256`)、
  `orchestrator/tests/test_check_docs.py` が本文の byte literal 全文 (`_SYNTHETIC_CLEANUP_COMMAND` / `_SYNTHETIC_CLEANUP_SKILL`)・sha 2 個・`len == 6_181` を pin。
  先例 T-2813 (DW-O26 exact pin 追随) と同型なので、実装面 (定数・fixture の追随) は Codex author 1 本。これは「gate・検査の追加」ではなく既存 pin の追随 (scope 内)。
- T-2601 対象 2 本 (`dev-wave-t1875-delta-min-gate` / `dev-wave-t2267-exec-site-class`) は `git worktree list` (38 本)・`git branch --list`・`.git/worktrees/` admin・
  `.claude/worktrees/` と `dev-wave-jobs/` の directory・`docs/unreachable-object-ledger.md` のいずれにも無い。撤去の実行記録 (実行者・日時) は worklog 現行 + archive・
  `cleanup-20260920/inventory/`・git 履歴 (`--all --grep`) に無い → 閉鎖記録は「不在の実測」だけを書き、実行者・日時は不明と明記する。
- command 本文に「退避」の概念は現在無い。command 自身は §2 で status 空のものだけ撤去し、dirty は §5 で引き渡す。F1034 は引き渡し script (repo 外) で起きた。
  → (b) は §3 に「dirty を撤去する引き渡し script も本節の退避検算を撤去の前提にする」の形で書く。`tools/cleanup_remove_dirs.py` は退避を作らない (docstring 実測)。
- 既存被覆: decisions / failures / dev-wave docs / commands に「退避 tar の検算」「証拠の所在で原本判定」の命令は無い (F1034 の恒久対応が本 wave を名指すのみ)。純増。
- command file は living docs でないので D/PATH 腐敗検査の対象外。check_docs の構造検査 (F26 共起行、§3 exact 2 行契約、`$ARGUMENTS` 1 件、skill-self-improvement 到達性、
  最長行 110 bytes) は保つ。
- base digest (local main 現物、HEAD == main の時点): [T-2814] `dab673869c…`、[T-2601] `2aeff5a373…`。

**割れうる前提 (親の provisional 裁定・攻撃対象):**
- (P1) (b) の置き場は §3 でよい (command 自身は dirty を撤去しないが、§3 が「worktree の削除手順」であり引き渡し script も同手順に従うべき)。§5 (引き渡し) でなく §3。
- (P2) F1034 のポインタを本文に書く (routing 4「長い事故説明は F ポインタ」)。command は腐敗検査対象外なので fixture placeholder 不要 — 実測は check_docs 直叩きで確認。
- (P3) 予算収容の削減対象は「意味を変えない縮約」だけ (安全義務を削らない、skill-self-improvement.md「予算のために安全義務を削除・弱化しない」)。
  候補: §0 末尾「削除は不可逆に近いので…」(§2 見出し・高い条件と同義)、§0「未確定事項…別 dev-wave だけが行う」(§6 と同義、§6 へ寄せる)、
  §1「rebase/cherry-pick 後も ahead>0」(根拠説明)、§3「(取り込み済み確認の上)」(§2 ahead=0 と重複)、§5 の command 例、frontmatter argument-hint の冗長語。
- (P4) SKILL.md は command を「全文読み不可分に適用」する overlay なので、command 側の 2 命令は Codex にも効く。overlay に足すのは Codex 固有の縮退
  (原本確認を経るまで候補にしない、退避検算なしに引き渡し script を書かない) の 2 項。

**不変条件:** 規律 2・3・6 不変 (正しさゲート非接触)。上限 (6,204 / 3,100) 不変。check_docs の構造検査・skill interface 契約不変。push なし。

**成果物の形:** command §2・§3 改訂 + SKILL.md overlay 2 項 (親 docs commit) → Codex author の pin 追随 (統合 commit) → 本 insight + worklog fragment
(T-2814 完了・T-2601 完了 = 閉鎖) + failures fragment (F1034 supersede) → land。

**段構成 (DW-C00):** 軽量版。一次資料から事実を抽出する docs + 実装面 (pin 追随) → 段 2・3 省略、段 5 Codex author 1、段 6 read-only review 1 + 変異 matrix
(literal / fixture / bytes assert 側) + 焦点走 (`test_check_docs.py` + consumer)。全 9 段はユーザー明示なし。

**受入・実測環境:** 焦点走・変異・受入は Pegasus 計算ノード (`tools/dev_wave_wait.py acceptance`)。check_docs 直叩きは login (背景化、2 分超)。
