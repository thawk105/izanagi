# 裁定パッケージ — dev-wave-floor-campaign-speed (C2)

本 wave は依頼「`test_s8b_floor_campaign` の高速化」に対し、**snapshot 側 (C1) を実装して
guard 11 テストを 35% 速くした**。しかし**この file の wall を支配しているのは別機序 (C2)** で、
そちらは隔離の意味論に触るため親が独断で採らず、ユーザー裁定へ返す。

## 事実 (すべて計算ノード実測、一次資料は job dir)

`test_real_seal_protocol_to_floor_official_core_e2e` は `_clone_committed_head_with_ccbench`
(`orchestrator/tests/test_s8b_floor_campaign.py:471`) で
**`git clone --no-hardlinks` により repo 全体 (313MB) + ccbench submodule を複製する。**

| 観測 | 値 |
|---|---|
| 受入全走 base arm でのこのテスト | **82.09s** (file 直列和 900.83s の 9.1%) |
| 変更後の file 走行での同テスト | 39.19〜39.34s (この file の **wall そのもの**) |
| clone 単体 solo: 現行 `--no-hardlinks` | **26.81s** |
| clone 単体 solo: 既定 (hardlink 許可) | **16.33s (-39%)** |
| clone 単体 solo: `--no-checkout` + hardlink | 5.24s |
| clone 後の size | 313MB |

**C1 をどれだけ削っても、この file の wall は C2 で頭打ちになる** (base 42.19s / 最終形 41.78s の
うち 39s 台が C2)。[T-827] handoff が「次標的」に挙げた `tools/codex_reasoning_ab.py:1289` の
repo 全体 clone × 2 と**同型の機序**である。

## 親が独断で採らなかった理由

`--no-hardlinks` の除去は **clone 隔離の意味論に触る**。git の object は不変なので hardlink 共有は
一般に安全だが、「テストが実 repo の object store と inode を共有する」状態を作ることになり、
本 file が守っている「テストは実 repo を 1 bit も変えない」という不変条件と同じ面に触れる。
**速度のために正しさ防壁の周辺を緩める形**であり、規律 2 の趣旨から親の独断で採らない。

## 選択肢 (親の推奨は Q1 = (b))

**Q1. C2 をどう扱うか。**

- **(a)** 触らない。この file の wall は 39s 台のまま受け入れる。
- **(b) [親の推奨]** 専用 wave で **`--no-hardlinks` の除去の可否を先に検証**する
  (-39%、26.81 → 16.33s)。検証は「clone 先で object を書き換えても source の object が
  変わらないこと」を機械検査で示す形にする。示せなければ (a) へ戻す。
- **(c)** `--no-checkout` + 必要 path だけの sparse checkout (5.24s、-80%)。
  ただしテストが必要とする working tree の範囲を確定する作業が要り、
  「必要な path を落とすと検査が静かに弱まる」危険がある。
- **(d)** このテスト自体を受入全走から外す (**推奨しない** — 受理集合が変わる)。

**Q2. 同型機序の横展開をどうするか。**

`tools/codex_reasoning_ab.py:1289` の repo 全体 clone × 2 が [T-827] の次標的として既出である。
C2 と同型なので、**同じ裁定を両方へ一度に当てる**か、個別に扱うか。
親の推奨は「Q1 の結論が出たら両方へ同じ判断を当てる」。

**[T-827] セッションの実測 (2026-08-12 に本 wave へ共有された値、出典は同セッション):**

| 対象 | 実測 |
|---|---|
| 本 wave の C2 (`test_real_seal_..._e2e`) | repo 全体 313MB + submodule を複製。solo 26.81s / hardlink 許可 16.33s / `--no-checkout` 5.24s |
| [T-827] の `codex_reasoning_ab.py:1289` | `git clone --no-hardlinks --no-checkout` を POS/NEG の **2 回**。`.git` は **258MB**。`benchmark_snapshots` の setup が **87.00s** = `test_codex_reasoning_ab.py` 単独 259.36s の 1/3 |

**両方とも「repo 履歴に比例して重くなる」型**であり、2026-08-11 のユーザー恒久ルール
**「repo 履歴に比例するコストをテスト経路に入れない」**の対象である。
両セッションが独立に同型と判断し、互いの実測を併記することで合意した。

**Q3. 本 wave の成果表現。**

親は段 6 裁定で、成果を **「実 `output/` snapshot を行う 11 テストの仕事量を 35% 削減した」**
に限定し、**「file を高速化した」「受入全走の wall を改善した」とは書かない**ことにした
(敵対レビュー S6-LUNA-08 の受諾)。依頼文が「file の高速化」だったため、
**この限定で依頼を満たしたと見なすかどうか**はユーザーの判断に返す。
