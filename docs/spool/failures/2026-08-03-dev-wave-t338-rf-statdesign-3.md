---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t338-rf-statdesign
seq: 3
---

## 新規

### {{F:land-rejects-wave-side-merge-of-folded-main}}. land の fold-owned-path 防壁が、stale の正規救済である wave-side merge を構造的に拒否する [手順漏れ] [防壁の射程誤認]

- 事象: 段 9 で `tools/dev_wave_land.py` が `status="fold-failed"`,
  `reason="declared fold shape rejected: landed-fold-owned-path"` を返し、local main は
  1 byte も動かなかった (fail-closed は正しく働いた)。原因は wave 側の 3 commit のうち
  **local main を取り込んだ merge commit だけ**が判定に触れたことである。
  親が各 commit を `git diff-tree --root -r -m --no-commit-id --name-status --no-renames` で
  個別に検査したところ、自分の docs commit 2 本は無反応で、merge commit だけが
  `M docs/spool/FOLDED.md` を出した。
- 根本原因: `tools/dev_waves/git_state.py` の `_landed_fold_output_path` は
  「landed 区間に `docs/spool/FOLDED.md` の変更または fragment 削除があれば拒否」と定義され、
  `_commit_diff` は `diff-tree -m` で merge を**全 parent へ展開する**。したがって
  「wave 自身が fold した」と「wave が fold 済み main を取り込んだ」を区別できない。
  防壁の意図 (wave 側で fold してはならない) は正しいが、**射程が merge commit へ溢れている**。
- なぜ回避不能か: `DW-O23` は stale の救済を「固定 SHA の wave-side merge」と定めるが、
  main は通常 `docs(spool): <wave>` → `Fold landed documentation fragments` の 2 commit で前進する。
  つまり **main が動けばほぼ必ず fold commit を含む**ため、正規の救済を実行した瞬間に本防壁へ当たる。
  さらに merge commit は branch 履歴に残るので、**fresh context で同じ branch を再利用しても
  同じ拒否が再現する** (判定は `main..tip` の全 commit を走査する)。
  rebase / force は `DW-O23` が禁じているため、wave 側だけでは解けない。
- 恒久対応: **未実施 — ユーザー裁定へ返す** (段 9 の条件不足を rebase で迂回しない規律に従い、
  親は branch を書き換えていない)。候補は (a) `_landed_fold_output_path` の判定を
  merge commit の第 1 parent 展開に限る、(b) landed 区間から merge commit を除いて判定する、
  (c) merge の代わりに wave 自身の commit を最新 main の上へ作り直すことを `DW-O23` で明示的に許可する。
  **現に効いている fail-closed は本 F の防壁そのもの**であり、main は汚れていない。
- 再発検知: 「main が fold commit で前進した後に wave が wave-side merge して land する」経路を
  並行回帰テストへ固定する (現行テストはこの組合せを覆っていない)。

## 再発

### F77

- **再発: 2026-08-03** — 本 F の恒久対応どおり `nohup bash -c '...' &` で段 2 の codex 子を投入したが、
  **`nohup` でも子は tool 呼び出しの終了とともに死んだ** (ログは 3 分ぶん残り `.done` は不在)。
  すなわち本 F が記録した「背景 job では `nohup` で投入し」は**十分条件ではない**。
  一方で「`.done` 不在を根拠に再投入しない — 先に生存確認する」は効いた — 親は再投入前に
  `ps` で同一 artifact を書く process が 0 本であることを実測し、二重起動を起こしていない
  (1 回目のログは別名で保全した)。実際に生き残ったのは、`&` も `nohup` も使わず
  **harness 管理の background 実行へ `bash -c '<cmd>; echo $? > <log>.done'` をそのまま渡す**経路で、
  投入 20 秒後に `ps` と log 増加で生存を実測した。成果物影響ゼロ (near-miss)。
  `DW-O01` への明文化は本 F の記録どおり byte 予算に阻まれたままであり、
  必要 63 bytes に対し `operations.md` の余裕は 44 bytes、意味等価な縮約 1 件で 15 bytes 回収しても
  **4 bytes 足りない**ことを実測した (この数値を [T-341] へ足した)
