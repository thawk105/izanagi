# 依頼の逐語 (ユーザー、2026-09-21、`/dev-wave` 引数)

[T-2814] (P2・新規、F1034) + [T-2601] (P1・裁定済み D2044 項 17) の docs のみ wave、着手直前の local main から fresh worktree。(1)
  .claude/commands/cleanup-branches.md §2・§3 に、(a) submit-tree / wave worktree の未追跡 output/ (exploration/・env/)
  を撤去候補にする前に該当 wave の insight「証拠の所在」節で repo 外原本かを確かめる、(b) 退避 tar の -C 順と entry
  数の検算を撤去の前提にする、の 2 点を足す (同 command §0/§6 が自己改善を別 dev-wave に限るため本 wave が担う。一次資料
  output/insights/2026-09-20/cleanup-backup-loss-record/README.md、entry 1759)。同 file は tools/check_docs.py の byte 予算 6,204 (現物
  6,181、余白 23 bytes) の下にあるので D782 手順 1 段目 (既存記述の削減) で収容し上限は動かさない (動かすなら Codex author +
  裁定パッケージ)。.agents/skills/cleanup-branches/SKILL.md (codex 側の写し) も同じ 2 点を揃える。(2) [T-2601] の対象
  dev-wave-t1875-delta-min-gate と dev-wave-t2267-exec-site-class は git worktree list に無い (実測) ので carry を閉鎖記録に更新する。稼働中の
  cleanup git branches session (00:15 起動) の final が返す罠があれば文言に反映するが、そのために待たない。command 本文以外の
  gate・検査・台帳・一般化の追加は scope 外。

# T-2814 の carry 原文 (worklog archive `docs/archive/worklog-phase3-0920-1759-1760.md`、entry 1759 の次の一手、逐語)

- [T-2814] **P2・新規**: `/cleanup-branches` §2・§3 に (a) submit-tree / wave worktree の未追跡 `output/`
  (`exploration/`・`env/`) を候補にする前に該当 wave の insight「証拠の所在」節で repo 外原本かを確かめる、(b) 退避 tar の
  `-C` 順と entry 数の検算を撤去の前提にする、を書く (command 改訂は同 command §0/§6 により別 wave。F1034)。

# T-2601 の裁定済み carry 原文 (`docs/archive/worklog-phase3-0916-1528.md`、entry 1528 の次の一手、逐語)

- [T-2601] **P1・裁定済み (D2044 項 17) → 実行手番**:
  `dev-wave-t1875-delta-min-gate` を撤去する。`dev-wave-t2267-exec-site-class` は施錠を尊重して
  残す。実行段で占有と差分を再確認し、掃除の授権境界を維持する。

# D2044 項 17 (`docs/decisions.md`、逐語)

### 項 17 — 撤去候補 1 本だけを名指しで撤去する

対象: T-2601。

**決定:** `dev-wave-t1875-delta-min-gate` を撤去する。`dev-wave-t2267-exec-site-class` は
施錠を尊重して残す。実行段で占有と差分を再確認し、掃除の授権境界を維持する。

**理由・採らない案:** 前者は取り込み済み・clean・非占有・非施錠で撤去の条件を満たす。
施錠されたものまで一括で撤去する案は、施錠の意味を無効にするため採らない。
