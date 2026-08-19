---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t201-output-bytes
seq: 2
---

## {{D:t201-output-bytes-history-preserving}}. output/ tracked bytes 削減は履歴保全した gzip 圧縮で行い、破壊的な履歴書き換えは使わない

**決定:** `output/` 配下の tracked bytes 削減は、対象ファイルを決定的 gzip (`.gz`) へ置換する
通常の commit (`git rm <元>` + `git add <元>.gz`) で行う。git-filter-repo や BFG 等による
過去 commit の blob 書き換えは使わない。除外判定は path の exact 一致で行い、basename 一致は
使わない (同名 basename が無関係な別 file にも存在しうるため)。

**理由:**
- 通常 commit なら過去 commit の tree/blob は一切書き換わらず、元 bytes は
  `git show <旧commit>:<path>` で永久に取得可能。破壊的書き換えは全 commit hash を変え、
  worklog / decisions / failures 台帳が張っている無数の commit hash 引用
  (一次資料の正本性、規律6) を道連れにする。
- 削減対象は HEAD の tracked bytes (checkout・worktree 作成・repo 内 grep 等の I/O コストに
  直結する) であり、`.git` オブジェクトストア総量やクローン/フェッチ転送量ではない
  (旧 blob は履歴に残り続けるため後者は変わらない)。この区別を報告・記録で混同しない。
- basename 一致の除外は、無関係な同名 file (`manifest.json` が複数 wave の insight
  ディレクトリに独立して存在する等) まで巻き込み、削減効果を不必要に落とす
  (output/ tracked bytes 削減 wave の段3・段6レビューで実測)。

**却下した選択肢:**
- `git filter-repo`/BFG による全履歴書き換え — commit hash 安定性を壊し規律6 と worklog
  citation を破壊するため不採用。
- `git rm --cached` によるファイルの unstage (追跡解除) — 新規 checkout・worktree では
  ファイルが存在しなくなり実質的に削除と等価になる (dev-wave は wave ごとに新規 worktree を
  作るため特に有害)。「削除ではなく」という要求と矛盾するため不採用。
- basename 単位の除外リスト — 上記理由により path exact 除外へ変更。
