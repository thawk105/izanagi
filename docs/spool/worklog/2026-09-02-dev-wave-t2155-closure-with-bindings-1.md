---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2155-closure-with-bindings
seq: 1
title: [T-2155] 閉包検査が誤って除外していた 2 経路を被覆する — 受理集合を広げる変更 (branch worktree-dev-wave-t2155-closure-with-bindings)
---

## 本文

- 静的閉包検査 (`orchestrator/tests/test_ccbench_spawn_sites.py`) の 2 つの射程の穴を直した。
  **これは検査の受理集合を変える変更である。** 設計判断は
  {{D:campaign-sink-dominating-returned-evidence}} と
  {{D:closure-check-reports-reachable-domain-not-total}}。
  一次資料は `output/insights/2026-09-02_t2155-closure-with-bindings/`。

- **現行 base で測り直したところ、裁定文の実測欄が再現しなかった。** archive の原文は
  「(a) を直すと s1 既定枝の 22 セルが `proven-unreachable` から `unresolved` へ移り、
  (b) が無ければ赤になる」だが、base `c1531d43b` では s1 1215 が
  `covered 4 / proven-unreachable 18` へ移り **failure は 0 のまま**だった。
  段 2 の plan も独立に同じ結論へ到達した。当時の測定は当時の記録として残し、
  現行 base の事実としては引用しない。2 欠陥を 1 commit にまとめたのは、
  **確定済みユーザー裁定が同一変更単位を指定したため**であり「片方が赤になるから」ではない。

- 分類の推移 (sink 53 x macro 22 = 1166 セル)。base は
  proven-unreachable 947 / covered 130 / deferred 89 / failures 0、
  実装後は proven-unreachable 943 / covered 156 / deferred 67 / failures 0。
  - `s1_direct_comparison.py <module>.run_role` 1215 campaign:
    `proven-unreachable 22` → **`covered 4 / proven-unreachable 18`**。
    到達可能 domain 4/4 を被覆した。**22/22 が被覆されたのではない。**
  - `s8b_oracle_driver.py <module>.run_block` 1788 campaign:
    `deferred 22` → **`covered 22`**。繰延べ台帳 entry を削除した (7 → 6 件)。

- **段 3 の 2 レンズが BLOCKER を返し、うち 1 件を親が実体で refute した。**
  「helper は一部 macro しか検査していないので全 patch macro の付与は誤り」という指摘に対し、
  helper が観測 record と期待 request digest の**完全一致**を早期 return より前で検査している
  ことを現物で確認した。指摘が根拠にした「期待集合が空なら素通り」は一致検査の後の話で
  含意が逆である。この指摘どおりに絞ると、実 driver の期待集合は実行時にしか決まらないため
  本題の 2 経路が 1 つも被覆されなくなる。

- **段 6 の 2 レンズが独立に同じ 3 件の BLOCKER を挙げ、焦点再レビューがさらに 3 件を挙げた。**
  いずれも新設した経路の false-green で、fix を 2 巡当てた (上限 3 巡)。
  2 巡目では、構文ごとに模型化を追うのをやめ**名前を鍵にした fail-closed** で族ごと閉じた。
  構文を鍵にすると 53 sink 中 27 sink (対象 2 file を含む) を巻き込むが、
  名前を鍵にすると触れる production file は 3 本だけで対象 2 file はどちらも該当しない、
  という実測を先に取ってから指示した。

- **焦点再レビューが「過剰拒否 = regressed」とした 3 件は親が refute した。**
  本 wave 以前の baseline は「campaign sink に被覆が一切付かない」であり、
  それらの形が拒否されるのは main に対する回帰ではない。受理集合を狭める向きの保守性として
  維持し、追わないことを記録した。

- **変異は 2 巡 23 件。1 巡目で 1 件が SURVIVED し、冗長な防壁だと判明した。**
  helper 乗っ取りの検出は 2 層が独立に同じ入力を拒否している。実効 gate へ再照準し、
  片層ずつの無効化は SURVIVED (1 件は事前に SURVIVED と登録して的中)、
  両層同時の無効化で狙った負例 2 本がちょうど KILLED になることを確かめた。
  初回の SURVIVED は消さず一次資料に残した。事前登録から 1 件外した理由も同資料に書いた。

- 正例・負例は実装前に判別力を実測してから登録した。合成 source すべてから campaign sink が
  実際に採取されること (0 件だと `failures == []` が恒真になる) と、支配性を行番号順で
  近似した実装では 2 つの負例が誤って通ることを確認している。

- 検査対象の driver (`s1_direct_comparison.py` / `s8b_oracle_driver.py`) は 1 行も
  変更していない。関門を通すために解析される式を選ばないという既裁定に従った。

## 次の一手差分

### 完了

- [T-2155] 誤った到達不能証明で除外されていた 2 経路を被覆する形へ直した。
  s1 は到達可能 domain 4/4 被覆 (残り 18 は非 domain)、s8b は 22/22 被覆で
  繰延べ台帳 entry を削除した。
  remaining: none
  base: 1822fb352e7a866157b40e64ad1cbd25ee667f8a8f3424ddf0bb463d14b0645d

### 新規

- {{T:closure-inventory-dynamic-input}} **P2・新規・ユーザー裁定要**: 設定式が動的入力に
  依存するとき、部分 inventory の不在を到達不能の証明に使ってよいかを裁定する。
  現状は非空 inventory があれば不在 macro を直ちに `proven-unreachable` にしており、
  s1 の 18 セルがこれで落ちている。閉包状態を持たせて `unresolved` に倒すなら受理集合が動く。
- {{T:closure-opaque-with-target}} **P3・新規**: 不透明な束縛 target
  (`with ... as holder.value` / `as holder[0]`) を依存判定で扱う。
  実測では採用すると `between_run_floor.py <module>.main` の campaign sink が 22 セル赤になるため、
  その sink の所有者判断か繰延べ台帳への追加が同時に要る。
- {{T:expression-macro-inventory-with-blindness}} **P3・新規**:
  `_expression_macro_inventory` も with 束縛を追えない。現行 sink の分類には影響しないが、
  依存解析と macro 棚卸しで束縛解決が食い違ったままになる。
- {{T:injected-branch-helper-authenticity}} **P3・新規**: 注入枝が使う既存の返却物検査認定は
  helper 名の後方一致だけで真正性を見ていない。本 wave では campaign 側だけ厳密化したので、
  注入枝も揃えるか、揃えない理由を記録する。
