# 段 1 brief — [T-328] docs/dev-wave/** の逼迫を入口 + 条件付き reference の外出しで解く

- wave: 2026-08-03 / branch `worktree-dev-wave-t328-docs-externalize` / base `e0b9073`
- 軽量版ではない: `DW-C00` の「受理集合が変わる」に該当する (`check_docs` の閉包・予算受理集合を
  変える) ため、段 2・3 と段 6 の敵対レビュー 2 本を省かない。

## scope

1. `docs/dev-wave/**` (hard ceiling 25,200 / 実測 25,198 / 余裕 2 bytes) の逼迫を、**縮約でなく
   外出し**で解く。低頻度条件節を、独立予算と独立閉包検査を持つ新 reference 族へ移設し、
   入口 `.claude/commands/dev-wave.md` の条件 dispatch から引く。
2. 空いた枠へ、滞留 7 ID の実測済み手順候補 (A1〜A11) を統合する。
3. [T-282] 残留の検出を、本 wave の受入全走で実測して閉じる。

## 確定済みユーザー裁定

- **択 (b)**: 入口 + 条件付き reference への外出し (先例 D110)。縮約で終えない。
- **予算上限は上げない**: `DEV_WAVE_AGGREGATE_BYTES = 25_200` と
  `.claude/commands/dev-wave.md` の 9,500 を据え置く。

## 不変条件

- **I1** 外出しは移設であって削除ではない (D110 決定 1)。移設前後の義務対応表を insight へ凍結する。
- **I2** 新族を予算外に置かない (D110 却下案 (b))。個別 cap + 族合計 ceiling + 閉包検査
  (未登録実体・登録済み member の不在/読取不能/symlink・必須 H2 の欠落と重複・孤児 H2・
  予算 path 集合 / 節 registry / dispatch 契約の三面一致) を新族にも張る。
- **I3** `docs/dev-wave/**` の aggregate 25,200 と「cap 総和 ≤ ceiling × 1.10 = 27,720」を維持する。
  cap 再配分はこの範囲内でだけ行う。
- **I4** 節 ID (`DW-Oxx` / `DW-Mxx`) を改番しない。入口 dispatch 表で変わるのは参照先 path だけとする。
- **I5** 受理集合を変えるので境界テストを同じ変更単位へ置く (D96)。
- **I6** 変異は **byte 中立**にする ([T-264](c))。予算 gate 対象で非中立変異を打つと、
  予算超過の赤が変異の kill と誤帰属する。
- **I7** 実装面 (`tools/check_docs.py`、テスト、probe) は Codex `role=author` が書く。
  親は docs 本文・統合・commit・全走・記録のみ。

## 前提実測 (2026-08-03, e0b9073, 本 worktree)

| 対象 | 実測 | 予算 | 余裕 |
|---|---|---|---|
| core.md | 8537 | 9600 | 1063 |
| workers.md | 4623 | 5000 | 377 |
| mutation.md | 3682 | 3750 | 68 |
| operations.md | 8356 | 8400 | 44 |
| **docs/dev-wave/** 合計** | **25198** | **25200** | **2** |
| 個別 cap 総和 | 26750 | 27720 | 970 |
| .claude/commands/dev-wave.md | 8907 | 9500 (行 140) | 593 |

- `python3 tools/check_docs.py` = 違反なし (baseline 緑)。
- **条件 09 (凍結 bytes の pin 閉包) の実測結果**: `docs/dev-wave/**` を bytes で pin する凍結台帳・
  trust root は存在しない。`FROZEN_MANIFEST` (23 件、`orchestrator/tests/test_frozen_artifacts.py`)
  は対象外。pin は 3 箇所のみ — (1) `tools/check_docs.py` の予算・節 registry・stage/condition
  dispatch 契約・literal 検査、(2) `orchestrator/tests/test_check_docs.py` の pin テスト
  (`test_dev_wave_reference_limits_pin_adjudicated_caps` ほか)、(3) `.agents/skills/dev-wave/SKILL.md`
  の literal 参照 (`docs/dev-wave/workers.md` と `docs/dev-wave/operations.md`)。
  role 名 key 側 (`DW-O08`/`DW-O09`/`DW-O11`/`DW-O14`/`DW-M06`) も検索したが、tracked な出現は
  4 reference 本体と `_OPERATION_NUMBERS` 由来の生成形だけで、他は `output/insights/` の歴史記録。
  → **条件 10 (producer write-path) は不成立** (これらを書く producer が無い)。
- **stale 判定 (F35)**: [T-328](a) (merge 競合解消を Codex author へ) は commit `5b246e2` で
  `DW-O17` へ統合済み。[T-264](a) / [T-279](100) (codex 子は計算ノード dispatch 不可) は
  `DW-O05`「テスト実測は親が行い、子の非実走を緑と記録しない」で概ね充足。**両者を候補から外す**。

## 成果物の形

1. 新 reference root (P1) + 移設節。移設量は候補統合に足りる量 (目安 ≥ 2,300 bytes)。
2. 4 reference への候補統合 (A1〜A11)。
3. `.claude/commands/dev-wave.md` 条件 dispatch 表の参照先更新 (path のみ、ID 不変)。
4. `tools/check_docs.py` の新族登録・閉包/予算検査 + `orchestrator/tests/test_check_docs.py` の境界テスト。
5. 残留検出の実測結果 ([T-282])。
6. worklog / decisions fragment (`docs/spool/`)、insight 一式。

## 統合候補

| # | 出所 | 内容 | 統合先 |
|---|---|---|---|
| A1 | [T-328](b) | 背景 job の codex 起動で harness 完了通知が子完了と食い違い、2 子が同じ `-o` へ書く | `DW-O01` / `DW-O02` |
| A2 | [T-279](96)-1 | 背景 job から codex を起動するとき、呼び出しが返ると子が死ぬ | `DW-O01` |
| A3 | [T-279](96)-2 | worktree から `qsub` すると `.o<ID>` / `.e<ID>` が worktree root へ落ち、clean-tree gate と `git add -A` を汚す | `DW-O20` |
| A4 | [T-328](c) | 変異 harness の `flock` は repo 単位で並行 wave を跨ぐ。他 wave 保持時の abort が正常であること、解けなければ本走未実施と正直に記録すること | `DW-M05` |
| A5 | [T-341](a) | 実装子が build できない環境では、投入前に親が「子が参照した識別子の実在」を実測する | `DW-S05-C` |
| A6 | [T-341](b) | scope が新機構を含む場合の `DW-G01` 生死確認を brief 段へ位置づける | `DW-S01` |
| A7 | [T-345] | 敵対レンズ prompt を exploit 構築でなく「どの構文クラスがどの拒否分岐にも該当しないか」の列挙に落とす | `DW-S03` |
| A8 | [T-346] | 引数タスクが worklog 末尾で完了扱いなら brief を書かず裁定へ返す | `DW-S01` |
| A9 | [T-317] | ファイルを書かない実行 (stdin heredoc) が段 1 前提実測として足りる場合がある | `DW-S01` / `DW-O19` |
| A10 | [T-264](b) | 実装子へ渡す契約逐語は親 docs 確定後に渡し、変えたら即同期する | `DW-S05-C` |
| A11 | [T-264](c) | 予算 gate のある対象では変異を byte 中立にする | `DW-M01` / `DW-M08` |

**A1 と A2 は語が衝突しうる** (切り離せ vs 重ねるな)。統合時に一つの規則へ整合させ、
どちらの実測も否定しない書き方にする。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 新 root は `docs/dev-wave/` の**外**に置く (案: `docs/dev-wave-rare/`)。中に置くと
  `DEV_WAVE_AGGREGATE_BYTES` の名前と実体が乖離し、「aggregate が実効 gate」という現行の性質が
  骨抜きに見える。**攻撃点**: 新族の新設は実質的な総量引き上げではないか / 命名と分割軸の妥当性。
- **(P2)** 移設対象は低頻度条件節。候補は `DW-O06` / `DW-O08` / `DW-O09` / `DW-O10` / `DW-O11` /
  `DW-O14` / `DW-M06` (実測合計 ≈ 1,830 bytes)。不足分の追加移設先は段 2 プランが決める。
  **攻撃点**: `DW-O09` は本 repo では頻繁に発火する (docs-only wave でも成立、F78) ので
  「低頻度」判定が誤りではないか。
- **(P3)** 残留検出は恒久 tool (`tools/measure_test_residue.py`) として置く。
  **攻撃点**: ユーザー裁定は「測って済ませる」であり、恒久 tool は盛りすぎ (規律 5) ではないか。
  実測だけで閉じ、恒久化は裁定へ返す案と比較する。

## 分割方針

- 実装単位 1: `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py` (新族の登録・閉包・予算・
  dispatch 三面一致と境界テスト)。
- 実装単位 2: 残留検出 probe とそのテスト (P3 が採用された場合のみ)。
- docs 本文 (4 reference + 新族 + 入口) は親が編集する (docs-only は親の担当)。
- 実装単位 1 と 2 は所有パスが素集合。

## DW-G05 成果物影響

実装しない場合、**変わるのは台帳と受理集合**である。(a) `check_docs` の受理集合は現状のまま
「docs/dev-wave/** に置ける実体 = 4 ファイル」に固定され、実測済みの手順欠落 9 件
(A1〜A11 のうち stale を除く) は **どの正本にも入らない** ため worklog の裁定待ち行に残り続ける。
(b) certified 選択・材料レポート・試行台帳の**数値は変わらない** — dev-wave 契約はそれらの
producer ではない。したがって成果物影響は「wave の再発失敗率と、滞留 ID が台帳へ滞留し続けること」
に限る。この 1 行を書けたので `DW-G02` の 1 cycle 送りには当たらない。
