---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2293-origin-producer-2
seq: 1
---

## 新規

### {{F:wave-base-commit-amended-away}}. 起動 gate を通った基底 commit が main 上で書き換えられ、wave 全体を作り直した [ドリフト] [手順漏れ]

- 事象: wave 開始時に local main の tip から fresh worktree を作り、`tools/check_wave_startup.py`
  が rc=0 (HEAD == local main、乖離 0) を返した。実装 commit の直後に `DW-O17` の full 監査として
  `python3 tools/check_ai_provenance.py` を走らせると **rc=1 で新規違反 1 件**が出た。違反は自分の
  commit ではなく、**基底にした main の tip 自身が AI-Agent trailer を欠いていた**ものだった。
  その commit は別 session が直後に amend し、trailer を足した別 SHA へ差し替えられていたため、
  基底はもはや main の祖先ではなかった (`git merge-base --is-ancestor` が偽、
  `git diff <旧>..<新>` は空)。この基底のままでは land の全史 provenance 監査 (`DW-O25`) が
  必ず赤になる。
- 根本原因: 起動 gate は「HEAD が local main と同一か」しか見ず、**その main 自身が監査を通るか**は
  見ない。main は書き換えられうるので、「開始時点で main と同一」は「その commit が将来も main の
  祖先である」ことを含意しない。着手時に見た main の tip が未監査の commit を載せている窓が実在する。
- 恒久対応: `DW-O17` の統合 commit 直後 full 監査が唯一の検出点として実際に働いた
  (本件はこの監査が出した)。復旧は **rebase も reset も使わず、現行 main から worktree と branch を
  作り直し、所有 path 限定 patch を当て直して commit する**。`git reset` / amend の痕跡は land が
  拒否するので、既存 branch を巻き戻して直そうとしてはならない。旧 worktree と branch は未着地の
  まま残し、撤去はユーザー裁定に委ねる。
- 再発検知: 統合 commit 直後の `python3 tools/check_ai_provenance.py` (機械、rc≠0)。
  新規違反が自分の commit でないときは、`git merge-base --is-ancestor <基底> main` で
  基底の生存を確かめる。偽なら基底が書き換えられている。

## 再発

### F953

- **再発: 2026-09-14** — 段 5 の投入で author 段へ `--reasoning` を渡して rc=2。子は 1 度も
  起動せず `.done` に 2 が入った。`DW-C01` に「`--reasoning` は plan/consult で必須、他段指定は
  rc=2」と明記があり、親は wave 開始時にその節を読んでいたにもかかわらず適用を落とした。
  前 wave の script を写した F953 本体と違い、本件は**読了した制約の適用漏れ**である。
  再投入は `--job-id` と出力 path を変えて行った (既存 `.done` を消して再利用しない)。
