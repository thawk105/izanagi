---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t950-acceptance-floor
seq: 1
title: 受入の単一 payer を 53.81 秒から 30.34 秒へ下げた — 三軸検索に必要条件 literal の前置フィルタを入れ、受理集合は canonical bytes で不変を固定した (コード + docs、変異 10/10 期待どおり、branch worktree-dev-wave-t950-acceptance-floor)
---

## 本文

ユーザー依頼「受入全走のボトルネックを高速化してください。**リワードハック禁止**」の wave。

### 律速は 1 関数に集約されていた

計算ノード全走 (9,848 node、node 秒合計 3,973.2) を親が測ったところ、`@real-repo` 直列鎖は
44 node / 115.80 秒で、**うち単一 node が 64.80 秒 (鎖の 56%)** だった。残り 43 node は
`real_repo_receipt_memo` により 0.00〜12.09 秒。その 1 node が払っているのは実 repo に対する
`verify_receipt` 1 回で、repo 外 probe で **53.81 秒**。内訳はほぼ 2 等分だった。

- `_batched_history_touches_path` 26.21 秒 — `git diff-tree` 1 本、**commit 数に比例**
- `search_repository` 26.36 秒 — 12,189 file を読み 9 本の正規表現、**file 数に比例**

### 実装したのは検索側だけ (履歴側は裁定へ返した)

三軸 template は literal のみの選択肢で、各選択肢は自軸の key を literal として含む。
「全 key の共通部分文字列を含まない text はどの軸にも一致しない」を前置検査にした。
**受理集合は変えていない** — 導出器を無効化した独立 slow 経路と全 report の canonical JSON bytes が
完全一致することを実 repo で 3 回とも確認した (同一 sha256)。

実測 (単独条件、実 repo 12,189 file): `search_repository` **24.85 → 11.83 秒**、
`verify_receipt` **53.81 → 30.34 秒** (判定は `active-valid` のまま)。
陽性対照 82 hit、holdout conjunction 0 件、`per_axis_counts` いずれも不変。

**効果を wall では主張しない。** junit に worker ID が無く critical path を再構成できないため、
言えるのは「直列鎖の候補 115.80 秒」と「並列側の平均下限 82.77 秒」を分けて出すことまでである。
また `verify_receipt` の差 (23.47 秒) は search の 13.03 秒より大きいが、
**超過分を実装効果へ帰属しない** (cache と run 間変動を含む)。

### 親が撤回した主張が 4 件ある

1. **「受入 wall の床は `verify_receipt` 1 回分」** — 段 3 レンズ B が覆した。worker ID が無く
   critical path は再構成不能で、直列鎖と並列側の下限は分けて述べるしかない。
2. **「戻り値が変われば受入が自動で赤になる」** — 実体を読んで自分で訂正した。live 照合は
   `per_axis_counts` と `result_sha256` を見ない。
3. **「前置フィルタが過剰に落とせば陽性対照が必ず赤になる」** — 段 3 レンズ A が反例を構成した。
   必要 literal を固定陽性対照だけが含む形にすると、陽性対照を残したまま holdout hit を落とせる。
   **oracle gate は騙せる。**安全性の根拠を等価テストへ移した
   ({{D:prefilter-safety-rests-on-slow-path-equivalence}})。
4. **「履歴走査のコストは commit 数に対して一定係数で線形」** — 段 3 レンズ B が覆した。
   ms/commit は 9.90 → 6.86 と下降しており、測った入力も本番と違った (reachable 3,276 対
   descendants 2,622)。本番入力での直接実測 23.55 秒だけを権威とする。

### 起草案を 1 点、敵対レビューが受理集合の穴として差し戻した

段 2 の起草は「導出器の入力は module の template だけ」としていたが、段 3 レンズ A が
`_expressions` の monkeypatch seam を突いて反例を構成した。段 4 で撤回し、
**各 scan が実際に compile する式から導出する**形へ変えた ({{D:prefilter-binds-to-actual-expressions}})。
段 6 のレビューはさらに「compile と導出が同一 snapshot でない」を突き、fix で閉じた。

### 変異が静的レビュー 6 本の見落としを 1 件見つけた

値側を literal 導出に混ぜる 1 行変異が、既存テスト 105 件を 1 本も発火させずに生存した。
多軸で書かれたテストが恒真になっていたためで、実害は単軸経路に出る
({{F:multi-axis-masks-value-side-literal-check}})。単軸検査 2 件を足して閉じ、本走で
**10/10 期待どおり (負例 9 件 KILLED、正例 1 件 SURVIVED、MISMATCH ゼロ)** になった。

### 段 3 の敵対レンズ 1 本が 2 回失われた

子は完全な成果物を出していたが、Codex CLI の web_search event に重複 JSON キーがあり
harness が attempt ごと破棄した ({{F:codex-web-search-duplicate-id-discards-output}})。
2,668 秒を空費した。Web 検索を禁じた 3 度目で通った。

## 次の一手差分

### 新規

- {{T:history-scan-two-phase-ruling}} **P1・ユーザー裁定待ち**:
  受入の残り半分 (履歴走査 23.55 秒、commit 数に比例) を安価な二段構えで 0.37 秒にできる。
  安価走行 (`-M -C` なし) で対象 path と対象 OID の不在を確かめ、現れたときだけ従来経路へ倒す。
  正常な git 出力上の受理集合が保たれることは段 3 の敵対レンズが網羅表で支持し、
  親も本番入力で結論一致 (False) を実測した。**ただし故障時意味論が変わる** —
  高価コマンドを実行しなくなるので、その呼び出しに固有の破損を検出しなくなる。
  択一は (i)「構文検証を通した安価出力を不在の十分な証明とする」= 採用可、
  (ii)「高価コマンド固有の故障まで毎回観測する」= 採用不能。**親の推奨は (i)。**
  採用時の実装条件 (安価側 trigger は status 非依存、`--find-copies-harder` を機械的に排除、
  包含関係の property test、cheap-only / high-only 破損の両変異) は裁定パッケージに揃えてある。
- {{T:acceptance-worker-timeline-instrumentation}} **P2・新規**:
  受入成果物へ worker ID・worker 別開始終了時刻・receipt memo の cache hit/miss・
  lock 取得待ちを記録する。**現状これが無いため critical path も memo の flock 待ち仮説も
  実測できず**、段 3 の敵対レンズ 2 本が独立に要求した。効果報告が
  「直列サービス需要を減らす」までしか言えない原因でもある。
- {{T:codex-evidence-status-invalid-diagnosis}} **P2・新規**:
  `evidence_status=invalid` の理由を receipt へ記録する。現状は
  `codex_exit_code=0` / `validator_rc=0` のまま成果物が捨てられ、
  どの行のどの検査で落ちたかが一切残らないため、prompt や成果物の品質を疑う方向へ誤誘導される。
  併せて consult / review 段で web_search を既定無効にするか、
  stdout event の重複キー扱いを証跡検査から分離するかを決める
  ({{F:codex-web-search-duplicate-id-discards-output}})。
- {{T:prefilter-scan-sharing-backlog}} **P3・新規**:
  3 scan がそれぞれ独立に containment を 1 巡している。安全性を落とさずに共有する形はある
  (`search_repository` 1 呼出しに閉じた cache を、各 scan が実際に導出した literal で key 化する)。
  段 6 レビューが file:line 付きで提示した。実測して効果が見合うなら実施する。
