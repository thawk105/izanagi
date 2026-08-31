---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1830-d1070-ratification
seq: 1
title: [T-1830] 批准検査の受入・dispatch 拡張は D1318 が既に終端済みで、残っていたのは持ち越し本文だけだった (docs のみ、branch worktree-dev-wave-t1830-d1070-ratification、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- 依頼は D1070 の実装だった。段 1 の裁定前提実測 (`DW-S01`) で前提が覆り、**実装対象の批准機構は
  main に存在しない**と確定した。さらに調査の途中で、**D1318 (2026-08-31) が D1039 と D1070 の
  実装を「着手せずに終端する」と既に裁定済み**であることが判明した。したがって本 wave は
  新しい裁定を書かず、終端済みなのに開いたままだった持ち越し本文を畳むだけにした。
- **同型の起動が 2 度繰り返された。** D1318 を生んだ [T-1985] の wave (entry 1113) 自身が、
  D1139 の着地後に更新されなかった持ち越し本文から起動されている。同 wave の裁定 D1318 は
  却下した選択肢に「持ち越し本文を無変更のまま残す — 同じ調査を次の担当が繰り返す」と書いた。
  **その翌日、同じ D1070 を指す別 ID [T-1830] の持ち越し本文から本 wave が起動された。**
  [T-1985] の wave は自分の ID だけを畳み、同じ裁定が終端した [T-1830] と [T-1820] を開いたまま
  残していた。ID が 3 つに分かれていたため、1 つ畳んでも残り 2 つが起動源として生き続けた。
- **[T-1820] も同じ理由で畳んだ。** D1318 は D1039 が命じた「既存 lock からの resume で批准を
  再検査する」実装も名指しで終端している。[T-1820] の本文はその実装を「実装待ち」と記したままで、
  放置すれば同型の起動が 3 度目に起きる。本 wave の依頼 scope 外だが、根拠が同一裁定であり
  他 wave が所有していないことを worktree と branch の実測で確認したうえで畳んだ。
- **D1318 の存在に気づく前に、独立の 4 経路で同じ結論へ到達していた。** (a) D1139 本文が D1070 を
  名指しして「批准 verifier が無くなるため実装不能になり、実効を失う」と書いていること。
  (b) 判定器が main から撤去済みで production caller が 0 件であること。(c) D1308 が救出候補を
  全件破棄と裁定していること。(d) 失敗台帳が同じ反転を記録していること。結論は一致した。
- **pin 閉包は依頼指定の全軸で 0 件を確定した。** 識別子 `require_ratified_closure`、module
  `enforcement_source_ratification`、操作 key `enforcement-source-closure-unratified`、台帳 path、
  fixture 名 `ratified_enforcement_source` の 5 軸に加え、子が `getattr` / `__import__` /
  `import_module` などの動的解決軸も 0 件と実測した。tracked tree の hit は docs と
  `output/insights/` の記録だけである。
- **素朴な全 repo grep は他 session の worktree 残骸を拾う。** `require_ratified_closure` は撤去前に
  切られた `.claude/worktrees/` 配下 2 本の checkout に実在する。閉包の確定には `git grep` を使った。
- **棄却した所見: `.py` に残る `ratif` は該当機構ではない。** `s8b_ratified_freeze` は floor protocol v2 の
  承認済み世代を扱う別機構である。同名識別子の二義化 (D75) をここで踏みかけた。
- **棄却した所見: `批准比較` 文字列の残存は欠陥ではない。**
  `test_s1_9pair_figure_provenance.py` の当該文字列は `FROZEN_E0_EPOCH` という凍結済み歴史記録の
  中にあり、現行の期待値からは既に外れている。絶対規律 7 どおりである。
- **敵対相談の 1 本目は親の prompt 書式ミスで全損した。** `DW-O01` が要求する必須見出しは
  `## 総括` (level 2) だが、親が出力形式へ `### 総括` (level 3) と書いたため、子は完走
  (codex rc=0、出力 7755 bytes、model call 58、wall 1072 秒) したのに採用検査が `f43_fragment` で
  弾いた。子の欠陥ではない。書式を直して再投入し、2 本目は採用検査 rc=0 で通った。
- **2 本目が親の誤りを 3 点訂正した。** (a) 親は「D1317 が最新裁定」と誤認していた。現行 main は
  D1321 まで進んでおり、D1318 が本件を既に終端していた — これが本 wave の結論を書き換えた。
  (b) D1163 が artifact 受入の `recorded-current-closure-mismatch` 拒否を撤去済みであり、
  親の「記録 closure と現行 closure の一致を検査している」は誤り。(c) 撤去 commit は v1 判定器が
  `b4ff38f6b`、署名 receipt 版が `c986c1459` であり、親は両者を取り違えていた。
- **撤去の残骸を実測した。** 台帳 `hooks/enforcement-source-closure-ratifications.v1.jsonl` は
  [T-2084] (D1329) が既に相乗り撤去と裁定済みである。残る 3 件は本 wave では掃除せず新規項へ送った。
- 工数: 敵対相談の Codex 子 2 本 (1 本は上記の書式ミスで非採用)。実装子と fix 子は起動していない。
  実装面の差分がゼロのため変異 matrix は `DW-S04` の免除に当たる。受入全走は免除せず実走した。
- wave 中に local main が 2 度進んだ (`11b44e2d1` → `cb4a11b6e` → `ac9a9ed7f`)。docs は取り込んでから書いた。

## 次の一手差分

### 完了

- [T-1830] D1318 が D1070 の実装を終端済みであることを独立に裏取りし、終端後も更新されずに
  起動源として残っていた持ち越し本文を畳んだ。実装は行わない。
  remaining: none
  base: f003e108f5bddd688821651a3cbdac0e1b8a58182871022c525f81d1566403c1

- [T-1820] D1318 が D1039 の実装も名指しで終端している。同じ理由で持ち越し本文を畳んだ。
  実装は行わない。
  remaining: none
  base: a4f91d6c0511cba51d1179da90bc1e76520dcd0f80d21001a8b8b556db53ebae

### 新規

- {{T:ratification-residue-remaining}} **P3・ユーザー裁定待ち**: D1139 の批准撤去が残した 3 件を
  掃除するかを裁定する。(a) `hooks/README.md` の批准 broker 節が、D1308 で破棄済みの
  `tools/ratification_broker.py` と `enforcement_source_ratification_receipt.py` を現存する道具として
  運用注意つきで記述している。hooks の配線の正本が撤去済み機構を指したままである。
  (b) `orchestrator/tests/conftest.py` の fixture `ratified_enforcement_source` は本体が空の互換 stub で、
  112 箇所が参照し続けている。(c) `docs/failures.md` の F594 が、恒久対応と再発検知の根拠を
  撤去済みの `require_ratified_closure` と `enforcement-source-closure-unratified` に置いたままである。
  いずれも受理集合を変えないため緊急性は無い。(a) は `hooks/` 配下で [T-2084] (D1329) の相乗り撤去と
  同じ編集面にあるため同梱できる。(b) と (c) は別の編集面につき同梱しない。
