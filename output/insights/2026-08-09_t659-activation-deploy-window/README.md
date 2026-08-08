# [T-659] activation 発行→配備の分裂窓 — 設計択一を裁定へ返した (2026-08-09)

wave = `dev-wave-t659-activation-deploy-window` /
branch = `worktree-dev-wave-t659-activation-deploy-window` / 起点 main = `ee2da0bf`。
親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave は **実装差分ゼロの設計 wave** である。land したのは裁定パッケージと逐語だけで、
**quiesce/drain も atomic deployment も 1 行も実装していない。**

- 「[T-659] が解決した」と書いてはならない。したのは**択一の整理と前提事実の実測**だけである。
- 段 2 プランの推奨 (同一 commit の機械検査) は**親が採らなかった** — 成果物の値も受理集合も
  変えないため (`DW-G05` / D205)。パッケージの推奨は「機構を作らず手順で担う」である。
- 親の当初案 (発行 tool に head 定数まで書かせる) は**取り下げた** — 発行が commit 前の
  有効化になり、承認された head という信頼の根が発行者の選択に置き換わるため。
- **[T-660]** (head=2 での末尾巻き戻し検出力) は並行 wave `dev-wave-t657-t660-g2-activation`
  の担当であり、本 wave は触れていない。**[T-658]** は見送り済みで復活させていない。
- 全 process の名簿・fencing token は**入力が存在しない**ため設計していない。

## 成果物

- `package.md` — 裁定パッケージ (R0〜R4 + 不変条件 7 件)。**ユーザーが読む正本。**
- `verbatim/s1-brief.md` — 段 1 brief (provisional 裁定 P1〜P3、erratum、追補 2 を含む)
- `verbatim/s2-plan.md` — 段 2 codex プラン (sol / max / read-only、rc=0)
- `verbatim/s3-lensA.md` — 段 3 レンズ A / 正しさ境界 (sol / max、**NO-GO** / must-fix 8 + nit 1)
- `verbatim/s3-lensB.md` — 段 3 レンズ B / 整合・最小性 (luna / max、**NO-GO** / must-fix 9 + nit 1)
- `verbatim/s4-adjudication.md` — 段 4 親裁定 (real/refuted と処置の一覧)
- `verbatim/probe_split_window.py` — 親の実測 probe (temp copy 上、live は不変)

## 証拠の状態 (これを隠して引用してはならない)

- **probe が実測したのは leaf の検証関数の範囲まで**である。`load_activation_state` へ期待値を
  直接渡しており、production の読み込み経路 (process cache、fork、root 解決、較正検証) を
  通していない。「live 経路に fail-open が無い」と一般化してはならない (段 3 レンズ A の指摘、
  親が受理)。
- **実機の並行実行は測っていない。** main 更新中の読み取り競合、SIGKILL 後の残骸、PBS wrapper の
  全分類はいずれも制御フローからの静的推論である。
- 実装規模の概算 (機械検査案で 300-500 行) は**静的見積り**で、実測ではない。
- 段 2・段 3 の子は read-only sandbox で静的読解のみ (`DW-O05`)。pytest は 1 度も実走していない。
- **`git ls-files` で確認した事実** (新 record が untracked であること) と、
  `_validate_activation_transition` が据置 env を許すことは、親が一次資料で裏取りした。

## 親が段 3 の指摘を受けて訂正した自分の記述 (4 件)

1. 「窓は 2 つ」→ **3 段の壁** (発行ツリー内 / 配備 / 旧世代の掃け残り)。
2. 「record と head はどちらも git tracked」→ **新 record は untracked**
   (`git ls-files` で確認。`git commit -a` が record を落とす、素の `stash` が分裂を作る、
   逆に中断からの復帰は untracked 削除で足りる)。
3. 「receipt の serial で混在を追える」→ **追えない**。durable には `contract_sha256` しか
   載らず、据え置かれた env は新旧の activation を区別できない (D245 が据置を許すため)。
   段 1 で書いた `evidence_contract_sha256` は段 8c の evidence 文書 hash で、環境世代の
   識別子ですらなかった。
4. 「probe で live 経路に fail-open が無いと実測した」→ 実測範囲は leaf 検証まで。

## 親が範囲を訂正した段 3 所見 (1 件)

段 3 レンズ B は「runbook への追記が `docs/dev-wave` の byte 予算 (残 16 bytes) を超える」と
した。**`docs/pegasus-runbook.md` に `tools/check_docs.py` の byte 上限は存在せず**
(`PROVENANCE_REFERENCE_LIMITS` は provenance 2 文書のみ、現状 `check_docs: 違反なし`)、
予算超過の懸念は当たらない。**節境界を切らずに §7.3 へ混ぜると受入 lease と activation 窓が
同じ契約に見える、という指摘だけが real** である。
