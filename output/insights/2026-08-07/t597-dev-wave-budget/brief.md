# 段 1 brief — [T-597] dev-wave 4 文書の予算捻出

## scope

- **供給 (T-597 本体):** `docs/dev-wave/{core,workers,mutation,operations}.md` から byte を捻出する。
  手段は 3 つだけ — (i) 機械検査で完全代替済みの記述の意味等価な縮約、(ii) 文書間の重複義務の一本化、
  (iii) 未 pin の機械強制へテストを足してから prose を tool ポインタへ縮約 (テスト化)。
- **需要 (T-592。同一ユーザー裁定が供給と束縛):** 空いた分だけ規約候補を採録し、
  入らない分は見送りとして worklog に残す。
- **非 scope:** 予算値 (aggregate 25,200 / 個別 cap / 110% gate) の変更。節 (H2) の削除。
  hooks の変更。`.claude/commands/dev-wave.md` 入口の編集。

## 確定済みユーザー裁定

- 2026-08-06 /rulings: 規約 4 候補は「**陳腐化規則の削除・テスト化で予算を空けて採録、
  入らない分だけ見送り**」。予算上限は上げない。[T-592] (需要) / [T-597] (供給) 起票。
  一次控え = `rulings-inbox/2026-08-05-background-waiter-duplication.md` 末尾。
- [T-454] 裁定: 「**docs でなく機械検査へ寄せられるものは寄せる**」。
- [T-127] 裁定: 上限を上げず使い方を管理する。
- D94 決定 2: 節削除を裁定パッケージへ送れるのは L2 × 発火実績なし × 機械代替済みの
  両条件を満たす節だけ。**削除の実施はユーザー裁定に限る**。
- T-160 insight §5: O03/O04/O10/O11 は**完全機械化できた場合だけ再裁定**。
  O13/O14/M02 は発火実績ありで候補外。

## 段 1 前提実測 (2026-08-07、本 worktree、rc のみ — F41)

1. 実 byte = core 8534 / workers 4668 / mutation 3674 / operations 8311 = **25,187 / 25,200**
   (余地 13)。個別 cap 総和 26,750 ≤ 27,720 (110% gate) で緑。
2. `tools/mutation_harness.py` は DW-M08 の機械部分を**全て**強制している:
   `-rf` 欠落は `main()` が拒否 (message が "DW-M08 の -rf" を名指し)、
   ANSI と行前置の除去 = `_strip_relay_prefix`、`" - "` 無しは行末まで = `_failed_nodes`、
   rc≠0 かつ node 0 件 → `PARSE_ERROR` = `_observed_status`。
3. 期待 node と記録 node の照合は `failed_keys == expected_keys` の**完全一致**
   (`_observed_status`)。→ T-592 候補 (c)「期待 node 完全一致」は**既に機械化済み**。
4. ただし 2・3 のうち **`-rf` 欠落拒否には test が 0 件**、`rc≠0 かつ node 0 件` も
   `failed=[]` の case が無い。完全一致も専用 pin が無い。→ テスト化の純増検出力あり
   (性質検索: 「argv 検証」「PARSE_ERROR」「expected 集合比較」で `test_mutation_harness.py` を走査)。
5. `operations.md:112`「段 1 前提実測は本走でないが、この復元規律に従う。」は
   `core.md:34` と同一義務の重複。段 1 は DW-S01 を無条件に読むので core 側が load-bearing。
6. T-592 候補 (b)「`DW-M05` pgrep 自己一致」は**採録済み** (commit `a62be201`、現行本文に実在)。
   → 需要は 4 件でなく 3 件。
7. 需要は他 wave からも来ている: (285) の DW-S01「機構名でも台帳検索」、
   [T-529] wave の DW-S01「保留裁定の解除条件棚卸し」、[T-595] wave の DW-O01「run_sN.sh 起動形」。

## 不変条件 (破ってはいけない)

- **予算のために安全義務を削除・弱化しない** (`docs/skill-self-improvement.md`)。
  縮約は意味等価に限る — 縮約後の本文で同じ読者が同じ判断に至ること。
- 機械検査へ寄せた記述を prose から削るのは、**その強制が test で pin された後**に限る。
  コードにその分岐があることを自己申告の根拠にしない。
- H2 見出しを削除・改名しない (`REQUIRED_REFERENCE_SECTIONS` / `STAGE_DISPATCH_CONTRACT` /
  入口 dispatch 表の 3 面が同時に整合を要求する)。
- 個別 cap・aggregate ceiling・cap 総和 110% gate の 3 つとも緑のまま終える。
- 実装面 (`orchestrator/tests/**`、`tools/**`) は Codex `role=author` が書く。親は docs のみ。

## provisional 裁定 (親の暫定判断であり攻撃対象)

- **(P1) 供給と需要を同一 wave で行う。** 裁定文が「空けて採録、入らない分だけ見送り」と
  1 つの動作に束ねており、空けた分を計らないと「入らない分」を決められないため。
  起動引数は T-597 のみだが、T-592 は同じ裁定の対側である。
- **(P2) 捻出の主経路は DW-M08 のテスト化。** 実測 2・3 で全項目が強制済みと確認でき、
  4 で pin 不在も確認できた。テストを足して prose を tool ポインタへ縮約する。
- **(P3) 節削除は本 wave で実施しない。** D94 決定 2 によりユーザー裁定必須で、
  O03/O04/O10/O11 は「完全機械化」が前提条件。本 wave の scope で完全機械化は達成できない。
  実測した機械化状況は裁定パッケージとして返す。
- **(P4) inline code 前後の空白削り (107 bytes) は採らない。** 可読性を予算のために削るのは
  手段目的の逆転であり、skill-self-improvement の禁止に触れる。
- **(P5) 全段を回す (軽量版を採らない)。** 本 wave は全 wave を拘束する契約本文の
  受理集合を変える (`DW-C00` の carve-out「正しさ防壁に触る」「設計択一が割れる」に該当)。

## 成果物影響 (DW-G05)

- 供給を実装しない場合: 余地 13 bytes が続き、裁定済みの規約候補 3 件と他 wave の
  改善候補 3 件が採録できないまま滞留する。**certified 選択・材料レポート・試行台帳の値と
  受理集合は 1 つも変わらない**。変わるのは開発 wave 契約の本文と、その契約が将来の wave に
  課す義務だけである。
- テスト化 (実装面) を入れない場合: DW-M08 の `-rf` 必須と完全一致判定が prose だけの義務に戻り、
  harness の該当分岐を消しても既存テストが緑のままになる (実測 4)。変異検査の検出力が
  静かに落ちる経路であり、これは変異台帳の値に効く。

## 分割方針

- 実装面は `orchestrator/tests/test_mutation_harness.py` の 1 ファイルに閉じる見込み。
  → 段 5 は Codex 実装子 1 本で足りる。所有分離は不要。
- docs 編集 (供給の縮約 + 需要の採録) は親が行う。実装子が pin テストを land した後に縮約する
  順序を守る (不変条件 2)。
