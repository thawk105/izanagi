# 段 4 親裁定 — dev-wave [T-419] (iii)

## 裁定: **実装しない。** 段 5・6 を飛ばして `4→7→8→9`。

### 決定的根拠 (一次資料)

`docs/worklog.md` の [T-560] 項 (エントリ 270、2026-08-06 /rulings 第 7 回、委任一括裁定):

> **[T-560] P2・裁定済み (2026-08-06 /rulings) → 見送り**: publish 済み bytes の別 process
> verifier + 最終 receipt 束縛の完全形は作らない。同一 process 内再読で足りる (プロトタイプ基準)

同エントリ本文は「再考で反転したもの」に `[T-560]/[T-563] → **見送り**` を明示している。
大前提はユーザー逐語「プロダクション実装ではないから完璧な堅牢性はいらない。アカデミアの
プロトタイプ実装ではそこまでやらない」(D205 化)。

**本 wave の scope は T-560 の逐語と完全に一致する。** `DW-S04` の「承認済み裁定を親が
不採用にしない」は逆向きにも効く — 見送り裁定を親の判断で実装し直さない。

### 裁定を覆す未見の新事実: 無い

段 3 の敵対レンズ 2 本はいずれも独立に **NO-GO** を返し、しかも
「実現するのは process-local state からの分離であって完全独立ではない」(B2)、
「land しても (iii) は閉じない」(B5)、「効くのは future certify wrapper だけで、
published 集合・registry/loader の受理集合・現行 certified 選択結果は一切変わらない」(B4)
と結論した。これは T-560 の見送り判断を**覆すのではなく補強する**。

`DW-G05` の観点でも、この機構を実装したときに変わる成果物の値は
**「将来の certify job の成功集合」だけ**であり、certified 選択結果・レポート・台帳の
どの値も参照も変わらない。段 1 brief が書いた成果物影響
(「(iii) が閉じないと登録・活性化へ進めない」) は **B5 により誤り** — (iii) は
T-560 により既に着手条件から落ちており、実装しても閉じない。

## 所見の real / refuted と採否 (段 3、A 10 件 + B 10 件)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B1 | T-560 と正面衝突 | **real** | **採用 = 本裁定の根拠** |
| B2 | 「完全独立」ではなく process-local 分離 | real | 採用 (名乗りの上限として記録) |
| B4 | 効く層は future certify wrapper だけ | real | 採用 (成果物影響ゼロの根拠) |
| B5 | land しても (iii) は閉じない | real | 採用 |
| B8 | 94a4 活性化で frozen floor protocol が壊れる | **real (親が独立に実測)** | **裁定へ返す (最上位)** |
| A7 | 「registered を列挙する test は無い」は誤り | real | 採用 = 親 brief の訂正 |
| B7 | 「job 再走なしに再現不能」は過大 | real | 採用 = 親 brief の訂正 |
| B10 | T-272 の phase3 記述への親の訂正も過大 | real | 採用 = 親 brief の限定 |
| B3 | P4 (被検証者が検証者を選ばない) は不成立、9 系統の迂回 | real | 採用 = (P4) 撤回 |
| A1〜A6, A8〜A10, B6, B9 | 設計欠陥 (fail-open binding、Base64 自己成就、locator swap、policy 負例欠落、3.9 テスト恒真、変異帰属不成立、重複バイト、命名過剰、consumer 不在、provenance 欠落) | real | **moot (実装しないため発火しない)。再裁定時の材料として insights へ凍結** |

refuted は 0 件。**scope 外の real 所見は実装せず裁定パッケージで返す** (`DW-S04`)。

## 親 brief の誤り 3 件 (訂正して記録する)

1. **「`registered/` を列挙する test は 1 件も無い」は誤り。**
   `orchestrator/tests/test_pegasus_tools.py:632` の `_acquisition_probe_document` が
   `next((REPO / ".../registered").glob("calibration-*.json"))` で列挙している。
   正しい主張は「**94a4 の verdict を固定する意味的 assertion が無い**」。
   なお registered/ が 2 件になった今、この `next(glob(...))` は
   filesystem 順序依存で fixture 対象が変わる — **新規所見として裁定へ返す**。
2. **「in-process の判定は certify job を再走しない限り再現不能」は過大。**
   publish 済み artifact は content-addressed で残っているので、job を再走せず再評価できる
   (本 wave の段 1 前提実測がまさにそれを実行した)。正しい主張は
   「**判定そのものが artifact として残らない**」。
3. **T-272 (`docs/phase3.md`) への親の訂正も過大。**
   job 892707 の `calibrate_rc=0` は `calibrator.cli → execution_guard → env_contract` の
   import が当時の計算ノードで通ったことを示すが、artifact は `python3 --version` を
   記録していない。1 job・1 node の成功は shell 3 本の版数 gate 不在を解消しない。

## 実装差分ゼロの射程

実装差分が無いため、**変異 matrix と受入全走は対象外**である (`DW-S04`)。
`DW-M01` の変異事前登録も行わない (登録すべき変異面が存在しない)。
段 1 で行った前提実測は repo 外の使い捨て probe であり、repo へ 1 byte も書いていない。

## [T-419] の状態更新 (記録すべき新事実)

- **(iii) は着手条件から落ちる。** T-560 が「同一 process 内再読で足りる」と裁定済み。
  D191 が実装した二重 gate + publish 後の同一 process 再読が (iii) の充足形である。
- **残る blocker は (iv) のみ**: `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の空化。
  これは 94a4 の登録が前提で、登録は [T-529] の活性化権限が前提。
- **ただし (iv) の手前に未知の壁がある (B8、親が実測で確認)。**
  `output/s8b-freeze/floor_protocol.json` は `FROZEN_MANIFEST` で凍結され、その bytes は
  `contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` を pin する。
  `s8b_floor_campaign.validate_protocol` はこれを**現在の** `env_contract.lookup(env_tag)` と
  比較する。94a4 を新世代として活性化すると active contract hash が変わり、
  **凍結済み floor protocol が拒否されうる**。凍結 bytes の書換えは禁止なので、
  歴史的世代の解決 (`resolve_by_contract_sha256`) か新 protocol 世代の発行かを先に決める必要がある。

## 同型欠陥の再発 (`DW-G03` の独立 2 例)

**見送り裁定が「次の一手」の該当項へ反映されず、後続の作業者が再着手する**事故。

- 1 例目 = [T-558] (worklog エントリ 273、2026-08-06。T-577 傘下の見送りが項に反映されず再浮上、
  rulings セッションが検出して訂正)。
- 2 例目 = 本件。[T-560] の見送りが [T-419] の着手条件 (iii) へ反映されず、
  dev-wave が (iii) を対象として起動され、**codex 子 3 本 (段 2 + 段 3 × 2) を消費してから**
  段 3 レンズ B が台帳の一次資料で検出した。

検出者が異なる (前者 = rulings、後者 = dev-wave の敵対レンズ) ため、`DW-G03` の
「異なる consumer で独立に 2 件」は成立する。**制度化の可否は裁定へ返す** —
プロトタイプ基準 (D205) の下では機械化が既定で見送りになりうるため、親は決めない。

## 裁定パッケージ (ユーザーへ返す、優先度順)

1. **94a4 活性化と凍結 floor protocol の衝突** (上記 B8)。(iv)/[T-529] の手前に効く。
2. **[T-560] の見送りを維持するか、覆して (iii) を実装するか。** 覆す場合の材料は
   段 2 プランと段 3 の 20 所見が揃っている (insights に凍結)。
3. **見送り裁定の「次の一手」への反映漏れ** (`DW-G03` 2 例目)。制度化するか、都度訂正か。
4. **`test_pegasus_tools.py:632` の `next(glob(...))`** が registered/ 2 件で非決定になった。
5. **`docs/phase3.md` T-272 の記述訂正** (「env_contract を含む 3.10+ module は certify 経路から
   すべて失敗」は job 892707 の実測と矛盾する。裸 python の版数 gate 不在の指摘は残す)。
