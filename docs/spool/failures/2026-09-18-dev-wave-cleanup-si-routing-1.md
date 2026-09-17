---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-cleanup-si-routing
seq: 1
---

## 新規

### {{F:cleanup-tool-rejects-hardlinked-admin}}. 段 9 の自己撤去 tool が admin dir 配下の submodule object の hardlink を「単一 regular file でない」として拒否する [恒真ゲート] [手順漏れ]

- 事象: 2026-09-18 の `dev-wave-cleanup-si-routing` wave の段 1 で、land 済み worktree
  `.git/worktrees/dev-wave-t2756-pin-evidence/modules/external/ccbench/objects/**` に `st_nlink > 1` の
  regular file が 31 件あることを実測した (`find -type f -links +1`)。段 6 で `.git/worktrees/` 配下
  172 本を走査すると、`modules/` を持つ 171 本すべてに `st_nlink > 1` の regular file が少なくとも
  1 件あった (各 admin dir で最初の 1 件を見つけて打ち切り。再走 184 本では 183/183。原出力は
  `output/insights/2026-09-18/cleanup-si-routing/count-hardlinks.txt`)。`tools/dev_wave_cleanup.py` の
  `_read_admin_file` は `st_nlink != 1` を `admin entry is not a single regular file` で拒否し、
  `_admin_snapshot` は admin dir を `modules/` まで再帰する。したがって `DW-O28` の自己撤去は、
  通常 preflight の snapshot (`_bind_admin`) に到達した時点で、この hardlink が残る限り
  `RC_REJECTED` (20) で止まる (state d / e の早期 return など、snapshot に到達しない経路は別)。
  本 wave 自身の段 9 での rc は最終報告に載せ、次 wave の worklog へ記録する。同日の
  `git worktree list` は 146 本 (locked 46 本) だが、この蓄積のうちどれだけが本拒否の帰結かは
  段 9 の rc が記録されていないため未確認である。
- 根本原因: `git submodule update --init` が local URL から clone する際に git が object を hardlink で
  共有する (local clone の標準挙動) のに対し、admin dir の同一性検査が registry file (`gitdir` /
  `commondir` / `HEAD` / `locked` 等) と submodule の object store を区別せず一律に `st_nlink == 1` を
  要求した。検査は「admin file が差し替えられていない」を見るためのもので、object の hardlink 共有は
  その脅威ではない。過去 wave の段 9 で同じ拒否が出ていたかは worklog に rc の記録が無く未確認であり、
  「拒否が報告で吸収されて顕在化しなかった」は仮説である (本 wave の段 9 の rc が最初の一次記録になる)。
- 恒久対応: 未実施。修正は実装面 (Codex author の別 wave、worklog の次の一手 {{T:cleanup-tool-hardlink-fix}})。
  案は `output/insights/2026-09-18/cleanup-si-routing/README.md` §3.2 (`modules/` 配下の object file に限り
  nlink>1 を許容し、registry file は現行どおり)。正例 (hardlink 入り admin dir の fixture で撤去成功) と
  負例 (registry file の hardlink は拒否) を同時に登録する。
- 再発検知: 段 9 の自己撤去の rc を worklog に必ず書く (`DW-O28`)。rc=20 の `admin entry is not a single
  regular file` を見たら本エントリを引き、tool の修正状況を確かめる。

## 再発

### F26

- **再発: 2026-09-18** — 作成側の再発 (2026-09-02 / 09-07 と同型)。`dev-wave-cleanup-si-routing` wave の段 6 で
  Codex fix 子用の `git worktree add -b <branch> <path> <sha>` が checkout 57% で「システムコール割り込み」(EINTR、
  背景 job の待ち手完了通知と同時) により fatal 終了した。残った中途状態は「branch は作成済み、directory も
  admin dir も無く `git worktree list` に現れない」で、`git worktree prune` の後に既存 branch を再利用して
  `git worktree add <path> <branch>` で作り直した (実害なし)。kill・背景化に続く第 3 の中断形。判別は
  `git branch --list` と admin dir の有無を 1 command ずつ見て、残っている物だけ畳む。

## supersede 追記

- F26 **supersede: 2026-09-18** — 削除側の運用則「1 worktree ずつ削除し、必要なら timeout を延ばす」は D2104 項 32 / D2113 の固定 launcher `tools/cleanup_remove_dirs.py` (`/cleanup-branches` §3 手順 3、全対象を前景 1 回で渡す) で置換済み。2026-09-17 の実走では 17 本並列 101 秒・10 本 161 秒で全件 removed (数値は同実走の final 報告を依頼文が引用したもの、job dir は消失)。作成側の運用則 (`git worktree add` は 1 件ずつ、必要なら timeout を延ばし、背景化されたら pid 終了を待つ) は残る。現行実体は §3 の同 launcher と `DW-O28` の `tools/dev_wave_cleanup.py`。
