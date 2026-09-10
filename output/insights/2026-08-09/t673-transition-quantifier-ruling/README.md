# [T-673] 遷移述語の量化縮退 — 生成的 / property-based テストの採否を裁定へ返す wave

wave branch: `worktree-dev-wave-t673-transition-pbt-package`
基準 commit: `4be7a362` / 実測 tip: `86842ee0` / probe commit: `3912c7fc` (side branch、land 対象外)

## 何をして、何をしなかったか

**していない。** 本番コード (`orchestrator/campaign/**`) と既存テストを 1 byte も変えていない
(ユーザー指示)。候補テスト 5 本も land していない。この wave が land するのは
**docs fragment と本 insights だけ**である。

**した。** `_validate_activation_transition` の 2 つの量化点に対する `[:N]` truncation 族について、
現状維持と 5 つの候補案の**検出力とコストを実測**し、裁定パッケージ (`RULING-PACKAGE.md`) を作った。

## この wave が確定させた事実

- **現状 (A) の検出天井は N ≤ 3。** focal 4 node の matrix でも、既存テストファイル全体
  (77 node) の matrix でも同じ結果で、scope による過小評価ではない。
- **B1 (stdlib 生成、依存ゼロ) と B2 (hypothesis) の frontier は完全に一致した (ともに N ≤ 63)。**
  本 wave の測定範囲では hypothesis 固有の追加検出力は 1 マスも観測されなかった。
  ただし B2 の frontier は `@example(env_count=64)` が単独で決めており、
  これは **PBT 一般の効用を測ったものではない** (shrinking・多軸探索は未評価)。
- **C1 (AST 構造検査) は登録した直接 slice 14 種を全 N で検出するが、検出力と偽陽性が
  同じ 1 本の規則から出る。** 意味保存リファクタ 3/3 (tuple 化・変数 rename・診断 loop 追加) で
  赤になり、一方で別名 slice + `continue` と冒頭 `return` は見逃す。
- **C3 (runtime sentinel) は量化点 G のみを閉じ、P には届かない。** sentinel は引数にしか
  注入できず、関数内ローカルの `changed` には届かないため。
- **現行および直近 land 予定の入力ではこの族で誤受理を作れない。** 現行 chain は record 1 件で
  定常 loader からは遷移検査が呼ばれず、land 待ちの実 serial 2 (`677d0952`) でも変化 env は
  1 個なので `changed[:N]` は恒等、`successor_rows[:1]` は fail-closed の誤拒否になる。
  ただし**発行 tool の publish 経路は今日でも遷移検査を発火させる。**
- **変異は distinct 14 種を 7 つの scope / 候補へ適用し、ledger entry 92 件。事前登録との不一致 0。**
  親が probe 本文から導出した期待 node 集合が、全 92 件で実測と一致した。

## 既存台帳への erratum

worklog 2026-08-08 (318) は `changed[:1]` の 10 node を「semantic 3 / diagnostic 7」と記録したが、
**正しくは semantic 5 / diagnostic 5** である。受理集合が変わる意味的検出には、2〜4 番目の env の
述語 false 3 件に加え、後段の非 bool と例外の 2 件 (`test_transition_rejects_non_bool_result_from_second_changed_env`、
`test_transition_wraps_exception_from_second_changed_env`) が含まれる。
根拠は同 wave の台帳 `mutation-ledger-v3.json` の M4 の `failed_nodes` である。

## 親自身が犯し、是正した誤り

1. **「dispatch は tracked 限定コピー」は誤り** (段 3 レンズ A が反証)。dispatch は計算ノードで
   共有 path へ chdir するため、非変異のコスト測定なら repo 外の probe も走らせられる。
   変異台帳を作るときだけ harness が固定 HEAD の tracked target を要求する。
2. **「現行本番では遷移検査が一度も呼ばれない」は言い過ぎ** (段 6 レンズ C / D が反証)。
   発行 tool 経路は今日でも発火し、実 serial 2 は land 待ちで存在する。
   正しい根拠は「呼ばれないから」ではなく「未検出域 N ≥ 4 が env 2 個では恒等だから」。
3. **C1 負制御の事前予測 3 件が誤り。** 事前 slice・`del`・decoy loop は、実際には C1 が検出する。
4. **C1 の「変数 rename」負制御が壊れた変更だった** (段 6 焦点再レビューが指摘)。
   loop 側だけを rename して定義側を残していたため `NameError` になる。定義側も含めて
   正しく rename して測り直したが、**C1 は依然赤**で結論は変わらなかった。
5. **前版の裁定パッケージは現状維持へ誘導していた** (段 6 焦点再レビューが NO-GO)。
   依存ゼロで frontier を広げる A′ / B1 と、本番編集禁止で未測定の D を比較せずに
   A を既定推奨にしていた。推奨を「B2 は land しない」までに限定し直した。

## 一次資料

- `RULING-PACKAGE.md` — ユーザーへ返す裁定パッケージ (これが本 wave の成果物)
- `s1-brief.md` / `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-adjudication.md` /
  `s5-impl.md` / `s6-lensC.md` / `s6-lensD.md` / `s6-corrections.md` / `s6-refocus.md`
- `mutation-spec-*.json` (7 本) / `mutation-ledger-*.json` (7 本 + wrapper receipt)
- `parent-probe-c1-controls.out` / `dep-install.out` — 親測定器の逐語出力
- `verbatim-probes-and-instruments.md` — 候補テスト 5 本と親測定器 7 本の逐語 + SHA-256

実行可能な原本は wave の job directory
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/`) と、
候補テストは probe commit `3912c7fc` にある。
