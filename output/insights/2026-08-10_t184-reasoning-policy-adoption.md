# [T-184] 工程別 reasoning policy の採用 — 選択理由 receipt (2026-08-10)

`docs/phase3.md` の [T-184] が要求する「選択理由 receipt」「旧 policy への明示 rollback」に対応する。
本 wave は **実装差分ゼロ**である。docs と本 receipt しか変えていない。

## 1. 何が確定し、何が確定していないか

| 面 | 状態 |
|---|---|
| reasoning policy (工程別の値と採用根拠の区分) | **確定した** (本 wave) |
| model policy | 既に確定済み (D241 / D242、`DW-O01` が権威) |
| resource envelope (launcher 結線・stage 別上限値) | **未確定**。裁定パッケージへ (§5) |
| retry policy | **未確定**。[T-183] が未完了で依存が充足していない |
| model×reasoning 非対応組の事前検査 | [T-184] の scope 外 ([T-371] / [T-189] 系が所有) |

**[T-184] は完了していない。** 本 receipt を下流タスクの待ち解除根拠に使ってはならない (§4)。

## 2. 採用した policy と根拠区分

| 工程 | 節 | 値 | 根拠区分 | 機械 pin |
|---|---|---|---|---|
| 段 2 | `DW-S02` | `max` | 直接比較証拠なし → D207 に従う据え置き | あり (D223) |
| 段 3 | `DW-S03` | `max` | 同上 | あり (D223) |
| 段 5 | `DW-S05-A` | `high` | 同上 | **なし (§3 の裁定により意図的)** |
| 段 6 敵対レビュー | `DW-S06-A` | `high` | ユーザー裁定による段 6 限定の外挿 (D243) | あり |
| 段 6 焦点再レビュー | `DW-S06-C` | `high` | 同上 | あり |
| 段 6 fix | `DW-S06-B` | 継承 | 実装子契約を継承。独自値なし | 不在を検査 |

**値は 1 つも変更していない。**

### 2.1 待機条件は充足した

2026-08-01 のユーザー裁定 (択 (a)) は「工程別 policy の採用は reasoning A/B の認証再走の後」だった。
2026-08-09 の認証再走が `aggregate` / `verify` とも rc=0 / `experiment_complete=true` で完了し、
採点器欠陥については erratum を添えて引き渡す裁定 (2026-08-09、§51) が下りた。gate は開いた。

### 2.2 台帳から言ってよいことの上限

台帳 `output/insights/2026-08-09_t181-certified-rerun/` と
その `erratum-f176.md` が許す主張は **「限定された段 6 focused review の 6 run で
劣化を観測しなかった」**までである。非劣性・同等性・採用の証明ではない。

**段 2 / 段 3 / 段 5 に使える証拠は存在しない。** 確認した経路は次の 3 つで、すべて同じ結論だった。

1. `schedule.json` の slot と `manifest.json` の attempt / judgment に**工程軸の field が無い**。
2. 台帳が束縛する 2 本の prompt (POS / NEG) は、いずれも冒頭で段 6 focused reviewer を明記している。
3. erratum が「この証拠は段 6 の focused review という工程に限定され、他工程へ外挿できない」と
   明文で禁じている。

非汚染とされた資源数値も、同じ段 6 workload に束縛された観測であり、
他工程の品質・費用へ変換できない。erratum が汚染と列挙した機械集計行・一次品質台帳・
両適格性 field は、本 receipt でも本決定でも根拠に使っていない。

したがって段 2 / 段 3 / 段 5 は **「証拠が支持した採用」ではなく「直接比較証拠の不在を明記した
保守的据え置き」**である。値を下げないのは D207 の帰結であって、本 A/B の帰結ではない。

## 3. 機械 pin を増やさなかった裁定と、その実測

本 wave は当初、機械 pin の外にある `DW-S05-A` の `reasoning=high` を
`tools/check_docs.py` の pin 閉包へ加える予定だった。段 3 の敵対相談 2 本が
**そろって NO-GO** を返し、次の 2 つが判明したため撤回した。

1. **2026-08-08 のユーザー裁定が、この pin 拡大を「見送りで終端」と裁定済みだった** —
   「`DW-S05-A` の `high` と `DW-S06-B` への pin 拡大はしない (防御的堅牢化、D205 既定)」。
   再訪条件は **「当該節の drift の実測」**。
2. D223 も同じ拡大を「当時の scope 外の受理集合縮小」として却下していた。

### 3.1 再訪条件を実測した — 成立しない

`docs/dev-wave/workers.md` を含む**全 19 commit** (2026-07-24 `2cd329d5` 〜 2026-08-08 `f9e2756e`)
について、各 commit の当該節本文から effort 表記
(`reasoning=` / `reasoning_effort=` / `model_reasoning_effort=`) を全数抽出した。

| 節 | 抽出値の履歴 | drift |
|---|---|---|
| `DW-S05-A` | 19 commit すべて `reasoning=high` のみ | **0 件** |
| `DW-S02` | 19 commit すべて `reasoning=max` のみ | 0 件 |
| `DW-S03` | 19 commit すべて `reasoning=max` のみ | 0 件 |

再訪条件が成立しないため、pin の追加は本 wave の権限外である。
**ユーザー再裁定 (見送り裁定の再訪) が要る。** 親は不採用にせず裁定パッケージへ返す (§5-1)。

なお、この実測は「pin が不要である」ことの証明ではない。
「見送り裁定を覆す条件がまだ揃っていない」ことの実測である。

## 4. 下流タスクの待ちは解除されない

段 3 のレンズ A が指摘し、親が採用した。

- [T-316] は sandbox profile を [T-184] 所有の stage policy へ追加してから進む契約である。
- [T-665] / [T-662] は canonical stage matrix と**起動前 policy の発行**を待っている。

本 wave が発行したのは reasoning の値と根拠区分だけで、
**canonical stage matrix (model × reasoning × resource × retry) も起動前 policy も発行していない。**
これらは §5-3 の残余の完了が条件である。
「reasoning policy 採用済み」を待ち解除語として引用してはならない。

## 5. 裁定パッケージ (ユーザー判断が要るもの)

1. **段 5 節への機械 pin の可否。** 見送り裁定の再訪。再訪条件 (drift の実測) は §3.1 のとおり
   **不成立**。それでも入れるなら、根拠は drift の実測ではなく別の理由になる。
   親の推奨 = **現状維持 (入れない)**。研究最優先・防御的堅牢化は既定で見送り、という既存方針と整合する。
2. **既存 pin (`DW-S02` / `DW-S03`) の実効性の残余。** F170 は「契約文の pin は存在検査ではなく
   位置・文脈の検査である」と結論し、独立行 exact 検査を導入したが、
   **その恒久対応は段 6 の 2 節にしか適用されていない**。段 2 / 段 3 の pin は
   literal 出現数方式のままで、規範文を引用・否定文・例示リンクへ置換する経路が残っている
   (段 3 レンズ B が静的に指摘、親は実走していない)。
   raw HTML block 本体へ別値を隠す経路も同族。
   親の推奨 = **見送り** (防御的堅牢化、実害の実測なし)。実測が出たら起票する。
3. **resource envelope と retry policy。** `DW-O01` への launcher 結線と stage 別上限値は
   [T-180] が [T-184] へ送った残余だが、台帳に資源上限の証拠は無く、
   全 wave の起動経路を変える設計択一である。retry policy は [T-183] 未完了で依存が未充足。
   親の推奨 = **[T-183] 完了後に、resource と retry をまとめて 1 本の設計 wave で扱う**。

## 6. rollback (旧 policy への明示経路)

本 wave は値も受理集合も変えていないため、**戻すべき機械状態は無い**。
採用の記述だけを取り消す場合の経路は次のとおり。

1. 後継の決定記録を起こす (既存の決定記録は削除・改変しない)。
2. `docs/phase3.md` の [T-184] 項を、reasoning 採用済みの表記から未確定へ戻す。
3. 本 receipt は削除せず、rollback receipt から参照する。
4. `docs/dev-wave/workers.md` の値、D223 / D243 の pin、
   `output/insights/2026-08-09_t181-certified-rerun/` の台帳は本 wave で一切変更していないため、
   rollback の対象にならない。

## 7. 本 wave の限界 (記録から落としてはならない)

- 段 3 の 2 レンズは read-only sandbox で静的検査のみを行った。pytest を実走していない。
  親は受入全走だけを実走した (結果は worklog)。
- §5-2 の迂回経路は**静的な指摘であり、親は production 経路の probe で再現していない**。
  実測なしに「破れている」と断定しない。
- 凍結台帳の pin 閉包について、当初 brief は「bytes を pin する code は 1 箇所」と書いたが、
  正確には sha256 で bytes を pin するのは 1 定数 (`_S03_SHA`) で、
  同 directory の `run-outputs/` は filename key の parametrized consumer が別に 9 本ある。
  閉包は 10 ファイル。本 wave は bytes を 1 byte も変えていないため成果物影響はゼロ。
