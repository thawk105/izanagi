---
authority: none
default_effect: no-state-change
---

# [T-2638] 段 1 brief — Codex 実装子 worktree の終端所有者と終端契約

**研究前進 (土台):** 止めているのは全 dev-wave の段 9 と掃除である。`/cleanup-branches` は 1 回 14.4 分
かかり所要は worktree 件数に比例する (差分検査 1 件 12.7 秒、本 login node の再測で 4.57〜6.32 秒)。
`.codex/worktrees/` は 2026-09-15 に 58 件、2026-09-16 04:35 JST に 67 件で、掃除の高速化 ([T-2641])
は流入に追い越される。最小差分は「実装子 worktree の終端所有者と終端契約を 1 つ決めること」である。
本 wave はユーザー明示により**実装せず、案と根拠まで**。

**確定済みユーザー裁定・既裁定 (不変):**

- 本依頼: 実装しない。終端契約の案と根拠、既存 58 (実測 67) 件の扱いを分けて出す。
- D702 / `DW-O28`: dev-wave は land 成功後に**自分の** worktree と branch を撤去する。
- D854: 生の `git worktree remove` と強制削除は防壁の破壊系集合。F26: 一括ループでなく 1 件ずつ。
- D391: 削除直前に `tools/check_worktree_occupancy.py`。rc0 は削除の必要条件であって十分条件でない。
- `DW-O23`: land は Claude/Codex worktree へ非接触。`/cleanup-branches` §2: status 空・ahead=0 のみ削除。

**不変条件:**

- 絶対規律 2 を緩めない。提案する撤去 gate は fail-closed とし、判定不能を撤去可へ倒さない。
- 本 wave は `.codex/worktrees/` の中身を一切変更しない (`--no-optional-locks` の読み取りのみ)。
- 稼働中 wave の子を撤去可能と判定しない。

**scope:** (1) 終端契約の案 — 所有者・発火点・撤去条件・記録先・却下した案。(2) 既存 67 件の分類と
救出要否。(3) 成果物影響を 1 行で。**scope 外:** docs 正本・tool・command の編集、実際の撤去。

**(P1) 親の provisional 裁定 — 段 3 の攻撃対象:**

- (P1-1) 穴は wave の死亡率ではなく**契約の射程**にある。根拠は名指しの実例である。`t1643-impl` は
  現存するが、その wave 作業木 `dev-wave-t1643-has-include-pair` は `.claude/worktrees/` に無く、
  T-1643 は着地済み (worklog 1498)。同型が `t1706-impl`・`prov-batch` (1518)・`t1994-*` 21 件 (1519)
  にもある。wave は段 9 へ到達し `DW-O28` で**自分だけ**畳み、子を残している。
  → 正しい発火点は段 9 の `DW-O28` 拡張である。
  (件数比は時点依存で根拠に使わない。`.claude/worktrees/` は 04:20 JST に 9 件、04:55 JST に 17 件。)
- (P1-2) 案 A (子の木を branch へ commit) は**一時 probe を歴史へ焼き付ける**。実例: `t1643-impl` の
  `tools/t1643_has_include_pair_probe.py` (475 行) はどの commit にも存在せず、T-1643 は
  「docs のみ・実装面差分ゼロ」で着地している。意図的に落とした probe である。
- (P1-3) 撤去 gate は「変更 file の内容 blob が着地 main から到達可能」で足りる。ただし**照合の
  一次判定は `git rev-parse main:<path>` との直接比較 (O(1)) にする**。`git log --find-object` は
  既定で merge commit の差分を作らず偽陰性を出す (本 wave で実証、`9f2f8d3a3`)。
  親の初版照合器はこの欠陥を持っていたため取り下げ、`reach2.sh` で取り直した。
  **副産物として gate の費用は履歴探索から O(1) 比較へ下がり、[T-2641] の高速化を損なわない。**
- (P1-4) 案 A 単独では掃除は塞がらない。commit すると branch が ahead>0 になり、§2 が要求する
  `git branch -d` が拒否する。汚れた作業木という障壁が、未 merge branch という障壁へ移るだけである。
- (P1-5) 所有の記録は**新設不要だが現状は寿命が足りない**。`codex_worker_launch.py` が wave ごとに
  `manifest.json` を書き、各 session の `recorded_cwd` が子 worktree の絶対 path を持つ。ただし
  背景 job の wave は artifact root を job dir (`~/.claude/jobs/<id>/dev-wave-jobs/`) に置くため、
  job を消すと記録ごと消える。実測: 全 183 manifest が名指す codex worktree 66 件のうち、現存 67 件と
  一致したのは 2 件だけ。残る durable な符号化は **branch 名**で、61/67 (91 %) が
  `<種別>-dev-wave-<wave slug>` 形式。外れる 6 件は `codex-*` 5 件と `acceptance-*` 1 件である。

- (P1-6) 原因は汚れだけではない。**`DW-O20` は「子を走らせる worktree は `git worktree lock`」を
  命じるが、その lock を解く節がどこにも無い。** `/cleanup-branches` §3 は locked を
  「detach・unlock・削除・prune を行わず、そのまま引き渡す (F51)」と定めるため、段 5 で掛けた錠が
  永久の除外になる。実測で 8 件が locked で、うち少なくとも 4 件 (`prov-batch`、`t1706-impl`、
  `t2288-impl`、`t2591-impl`) は wave 本体が既に存在しない。**汚れを解決しても、この 8 件は残る。**

**成果物の形:** `output/insights/2026-09-16/t2638-codex-worktree-retirement/`
(`authority: none` / `default_effect: no-state-change`) に裁定パッケージ本体・実測表・逐語。
worklog / decisions は `docs/spool/` fragment とし、段 9 の land が fold する。

**並列分割:** 段 2 = plan 子 1 本 (read-only、`reasoning=medium`)。段 3 = 敵対 2 本並列 (レンズ (i)
終端契約の穴と恒真性、(ii) 救出判定の偽陰性と所有境界)。段 4 で「実装しない」を裁定し段 5・6 を飛ばす。
