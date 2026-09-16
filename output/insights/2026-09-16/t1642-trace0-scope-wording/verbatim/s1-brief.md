# 段 1 brief — [T-1642] TRACE=0 検査の射程文言を「必要条件の一つ」へ統一する

- wave: dev-wave-t1642-trace0-scope-wording / branch `worktree-dev-wave-t1642-trace0-scope-wording`
- worktree (子が読み書きする repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1642-trace0-scope-wording`
- 基準: local main 9d52ef1459fdae5bc97050155b28fce0601d259f (着手直前)

## 研究前進 (土台)

止めている研究は mocc の TRACE=0 材料値の昇格経路である。T-1677 が束縛付きの観測値
(341,200.03 txns/s、pilot receipt + job-result に checker report を束縛) を既に取得済みで、
D780 は「防壁を先に作ると TRACE=0 の材料が長く止まる」として文言統一を先に置いた。
最小差分は、この検査の射程 (規律 1 に対して必要条件の一つでしかない) を producer 側の live な
文言へ入れ、以後の材料レポートが同じ文言を写せる状態にすることである。
完了判定: 対象アンカーの射程記述が D780 決定 1 の趣旨と一致し、checker の受理集合が 1 bit も
変わらず、受入全走が緑。

## 確定済みユーザー裁定 (D780、2026-08-25 /rulings 全件 択 (c)。正本は worklog entry 911 の [T-1642])

1. 成果物側の文言を「この検査は D297 の保証を証明するものであり、計測ビルドからの trace 完全除去に
   対しては必要条件の一つである」で統一する。完全除去を証明したと読める記述を残さない。
2. 実 compile command・全 TU・link object・trace symbol/data・build receipt を結合する別防壁は
   [T-1644] と同じ閉包でだけ設計する。**本 wave は 1 だけを閉じ、2 に着手しない** (裁定が順序を定めている)。
3. 静的に解決できない間接値の限界は D774 の docstring 明記のまま据え置く。

## scope と成果物影響 (DW-G05)

- in: `docs/` 以外の live な射程文言 (checker の docstring/コメント、pilot のコメント) を D780 決定 1 の
  趣旨で統一する。放置すると TRACE=0 材料レポートの読み手が「規律 1 の完全除去が証明済み」と読み、
  材料レポートの主張の強さが実際の保証を超える (= 成果物の主張が受理集合より強くなる)。
- out: 別防壁、新 gate・検査・台帳・一般化、report schema 変更、`GUARANTEE` 定数の値変更、
  歴史記録 (decisions / failures / archive / spool / 過去 insight) の遡及改変。

## 不変条件

- 規律 2 を緩めない。checker の受理集合・拒否条件・出力 JSON の bytes を 1 bit も変えない
  (変えてよいのは docstring・コメントだけ)。
- 凍結 pin: `GUARANTEE` 定数は `orchestrator/tests/test_check_trace0_preprocess_identity.py:24` に
  literal 複製があり `:230` で report の値と一致検査される。schema は
  `izanagi-trace0-preprocess-identity/v2` で pilot が family prefix を受理する。どちらも非変更。
- 実装面 (`tools/**`) は Codex author が書く (D95)。親は直接編集しない。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- (P1-a) 「成果物側」= checker report を生む producer の live な文言と、以後の材料レポートが写す元。
  過去 insight は歴史記録として非改変 (規律 7: 過去の判定は追記でのみ訂正)。
- (P1-b) checker report JSON へ射程 field を足さない。schema 変更は consumer と凍結に触れ、
  D780 が求めているのは文言であって新しい束縛ではない。
- (P1-c) 純増を水増ししない。実際に射程注記が欠けているアンカーだけを直す。

## 成果物の形

- 実装面 diff: アンカー表 A 群のみ (コメント/docstring)。
- 記録: `docs/spool/` fragment (worklog + 必要なら decisions)、`output/insights/` に insight 1 本。

## 並列分割

段 2 plan 1 本 → 段 3 敵対相談 2 本 (レンズ A = 対象閉包の網羅性と歴史記録の扱い、
レンズ B = 統一で主張の強さが変わる箇所と規律 2 非緩和の実証) → 段 4 裁定 → 段 5 実装 1 本
(2 file、衝突なし) → 段 6 レビュー + 受入全走。

## 受入・実測環境

login node で完結する (Pegasus 計算ノード不要。TRACE=0 の再計測はしない)。
受入は `tools/dev_wave_wait.py acceptance -- python3 tools/run_tests.py`。

## アンカー表

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1642-trace0-scope-wording/s1/anchors.md`
