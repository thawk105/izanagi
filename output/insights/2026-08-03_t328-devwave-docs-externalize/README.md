# [T-328] docs/dev-wave/** の外出し — dev-wave 逐語 (2026-08-03)

外出しを**実装しない**と裁定した根拠の一次資料と、[T-282] の実測。正本は `docs/worklog.md` の
該当エントリで、本ディレクトリは逐語を凍結するだけである。

| ファイル | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。前提実測 (byte 表・凍結 pin 閉包・stale 判定) と provisional 裁定 (P1)〜(P3) |
| `s2-plan.md` | 2 | codex プラン起草 (read-only)。risk 軸への対案、横断 ceiling 27,200、変異事前登録候補 |
| `s3-lens-a.md` | 3 | 敵対レンズ A — 予算 gate の意味と実効性 (**NO-GO**) |
| `s3-lens-b.md` | 3 | 敵対レンズ B — 移設の無損失性と consumer 閉包 (**NO-GO**) |
| `s4-adjudication.md` | 4 | 親の裁定。**実装しない**、ユーザー再裁定へ返す |
| `t282-residue-measurement.md` | — | [T-282] 残留の検出。全走前後の prefix 別実測 |
| `t282-tmp-new-entries.tsv` | — | 実測の生データ (新規 `/tmp` entry 226 件の bytes / path / inode) |
| `t282-run-meta.txt` | — | 全走 job のメタ (host / PBS_JOBID / interpreter / rc / 所要) |

子は 3 本とも `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`。
実装子は起動していない (実装差分なし)。job artifact 一式は
`/work/1/SFC/tanab/dev-wave-jobs/t328-docs-externalize/` にある。

## この wave が閉じたことと閉じていないこと

**閉じた:**

- **[T-282]** — repo 残留はゼロ、`/tmp` 残留は 1 全走あたり 226 entry / 5.74 GB だが **job 内に閉じる**。
  恒久 tool は置かない
- **[T-328](c) の前提の反証** — 変異 harness の `flock` は repo 単位ではなく **worktree 単位**
  (`tools/mutation_harness.py:1814`)。並行 wave は競合しない
- **[T-264](a) の stale 判定の撤回** — `DW-O05` は read-only 子にしか発火せず、
  workspace-write 実装子への「テスト実走は親」義務は現行のどの節にも無い

**閉じていない (主張しない):**

- 外出しそのもの。**D94 却下案 (a) が既に同じ scope を却下している** — dev-wave の読み込み契約は
  leaf 節単位なので、節をどのファイルへ移しても読了 payload は変わらない (削減 0)。
  D110 (provenance) が成功したのは入口が全文読まれる構造だったからで、その構造は dev-wave に無い
- 滞留 7 ID の統合。必要な 1,463 bytes を「上限を上げず・縮約せず」に作る手段が存在しない
- レンズが挙げた既存欠陥 (発火条件逐語の未検査、前置き位置の dispatch 到達不能、
  ID 全族一意性、land 境界の check receipt 不在、F 台帳の逆方向 pointer) — 新 ID として起票する
