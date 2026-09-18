# 段 1 brief — [T-2447] D1893 の P2 / P6 を docs/dev-wave へ収容する (wave: dev-wave-t2447-lens-p2-p6)

## 研究前進
土台。論文を直接進めない。止めている研究の実測: 所見→裁定→T 起票の出口が無く、worklog「次の一手」の持ち越しは D1798 時 345 → D1893 時 567 → 現在 638 項 (entry 1635、2026-09-18)。製品行は 09-11→09-18 で +12,070/−1,629 (merge 除く)。研究 wave が土台 wave の起票で押し出される。最小差分 = DW-S03 / DW-S06-A (P2) と DW-S04 (P6) の文言変更、bytes は同層内の D227 準拠削減で相殺。完了判定 = 3 節に効力語が入り `check_docs.py` rc=0、command 入口は不変。起点はユーザー裁定 D1893 + 明示引数 (D1798 の「ユーザー裁定へ返す」経路を既に通過)。

## scope
docs のみ。`docs/dev-wave/workers.md` (DW-S03、DW-S06-A、原資として DW-S06-B / DW-S06-C)、`docs/dev-wave/core.md` (DW-S04、原資として DW-S09)、`docs/dev-wave/operations.md` (原資として preamble 2 行目)。P4 (変異 matrix の義務) は触らない。`.claude/commands/dev-wave.md`・`tools/check_docs.py`・テストは触らない (実装面 0 byte)。仮想リスク向けの gate・検査・台帳・一般化は足さない (ユーザー引数)。

## 確定済みユーザー裁定
D1893 (2026-09-09、逐語は projection/D1893.md): P2 と P6 を採る。P4 はそのままでは採らない。D1798 (projection/D1798.md) が P1 を収容済みで、P2/P4/P6 は「裁定候補として残す」と書いた → D1893 で裁定済み。D782/D730: 予算は削減 → 独立 3 例の例外 → 増枠の順、増枠時だけ報告。D227: 削減の原資は「同一読点で読まれる上位互換節との重複」だけ。

## 不変条件
- 規律 2 不変。過剰・削除レンズは 2 本のうち 1 本で、もう 1 本は正しさ境界のまま。正しさゲート・変異義務 (DW-S04 の免除条件、DW-M01) は 1 byte も変えない。
- `tools/check_docs.py` の逐語 pin (実測): DW-S03 は `reasoning=medium` を可視本文にちょうど 1 回、DW-S06-A は行「実装 wave は異なるレンズの敵対レビューを `reasoning=medium` で必ず 2 本並列で行う。」がちょうど 1 行、DW-S06-C の同型行、core.md に「実装面があれば段 5 の Codex 実装子と fix 子は」「親は直接編集しない」、DW-S09 に「`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路」。これらの行は触らない。
- 層予算 (実測、main d2ebef7a4): L1 10,622 / 10,625 (残 3)、L1.5 9,696 / 9,696 (残 0)、L2 単節 ≤ 1,000。安全義務を予算のために削らない。
- 稼働 wave との編集面: `worktree-dev-wave-cleanup-si-routing` が operations.md の DW-O28 (末尾) を編集中。本 wave は DW-O28 に触らない。

## 成果物の形
workers.md / core.md / operations.md の差分 (projection/proposed-edits.md に候補文言と byte 差)、worklog fragment、insight (逐語)、`check_docs.py` rc=0、`orchestrator/tests/test_check_docs.py` と `test_dev_wave_launch_authority.py` の緑。decisions fragment は新裁定が無ければ書かない。

## 分割方針
docs-only、実装子なし、親が編集。段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A = 正しさ境界・整合: pin・予算・D227 の 3 条件・既存正本との二義化、レンズ B = 過剰・削除: 本 wave 自身に P2 を先行適用 — この追加は D1893 の実測欠陥に対応するか、削除・局所修正で済まないか、恒真化しないか)。段 6 は review 1 本 (受理集合 = 何を T にするかが変わるため省かない)。

## 親の provisional 裁定 (攻撃対象)
- (Q1) P2 の収容形は DW-S03 の既存 2 レンズ「正しさ境界 / 整合・実効性」を「正しさ境界・整合 / 過剰・削除 (追加が実測欠陥か研究前進に対応するか、削除・局所修正で済まないか)」に置き換える。3 本目にしない。実効性は過剰・削除に吸収される。
- (Q2) DW-S06-A には「1 本は `DW-S03` の過剰・削除レンズに固定する。」の 1 行を足し、同節の「所見ゼロの扱いは `DW-M02`。」を削る (DW-M02 は段 6 U で同一読点、見出し自体が「所見ゼロの裏取り」)。
- (Q3) P6 の収容先は DW-S04 の 2 文目だけ。段 7 (DW-S07) や skill-self-improvement.md の routing は触らない。文言: 「scope 外の real 所見は実装せず、研究前進か実測欠陥の根拠がある所見だけ設計択一・推奨案付きの裁定パッケージでユーザーへ返し、無い所見は起票せず insight に記録する。」
- (Q4) L1.5 原資: DW-S06-C 末尾「、成果物影響を書けない所見を must-fix にしない」(DW-G05 が段 6 U で上位互換) と DW-S06-B の列挙「権限、reasoning/sandbox、テスト弱体化禁止、受理集合、期待赤、波及報告、」(入口の「DW-S05-A/B/C を全文継承する」+ 段 6 U の S05-A/B/C が上位互換、「段 4 の規模上限」だけ固有なので残す)。
- (Q5) L1 原資: DW-S09「再試行・停止は `DW-O23` に従い、」(入口終端「段9は `DW-O23` に従い、競合時は再試行する」) と operations.md preamble 2 行目「該当節を操作直前に読み、停止条件を迂回しない。」(入口の読み込み契約と凍結境界)。
- (Q6) 否定命題: 「L1.5 に他の D227 準拠原資は無い」は読解による推測で実測ではない。反証を歓迎する。

## 模擬 / 実の差
節 bytes と pin は `tools/check_docs.py` の関数と定数で実測。持ち越し件数は worklog 末尾を機械で数えた。byte 差は候補文言の実測 (projection/proposed-edits.md)。
