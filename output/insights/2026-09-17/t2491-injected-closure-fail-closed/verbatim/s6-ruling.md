# 段 6 裁定 (親) — レビュー A/B の所見と fix の scope (2026-09-17 22:35 JST、mtime で実測)

実装 must-fix: 両レビューとも 0 件。以下を **1 本の fix 子** (test file 単独所有、`DW-S05-A/B/C` 契約継承) へ寄せる。

| # | 出所 | 所見 | 裁定 | DW-G05 |
|---|---|---|---|---|
| F1 | A (a) | 変換先の判定が module 再代入 (`PilotErr = X`) を除外しない | **real、採用 (R3a)** | 放置すると E を再構築して外側で握り潰す形が covered に残る |
| F2 | A (b) | `local_names` が字句的親関数・関数引数の束縛を見ない | **real、採用 (R3b)** | 引数/親関数で E に束縛した名前の handler が NONE 扱いになり握り潰しが covered に残る |
| F3 | A (c) | `raise <as 名>` の前に as 名を再代入すると別例外の変換を bare と読む | **real、採用 (R3c)** | 別例外への変換 + 外側の握り潰しが covered に残る |
| F4 | A 1 | 保証限界 comment に型名・as 名の再束縛と finalbody 内 check が無い | **real、採用** (R3a〜c で締めた後に残る限界を書く) | 限界の名乗り過ぎを防ぐ (受理集合は不変) |
| F5 | A 2/3、B | TryStar・再束縛規則の専属負例が無い (n10/n12 は他規則でも落ちる) | **real、採用** → n13〜n17、p8 を追加 (下記) | 規則を外す変異を検出できない = 変異の帰属不成立 |
| F6 | A 4 | n3 は過剰決定、n7/p4 は一変更対でない | **real、採用 (記録 + p8 追加)**、n3 の期待値は変えない | 受理集合不変 (nit) |
| F7 | B must-fix 1 | M2/M4 の期待集合は author 補正 (M2 = n8 以外、M4 = n4 のみ) | **採用** → spec に反映 | 帰属証拠の成立 |
| F8 | B nit 3 | n10 の skip と検査重複 (3.11 でも TryStar 規則の専属 killer にならない) | **採用** → n14 (`except* X: raise`) を追加、3.10 では skip、TryStar 規則は保証限界へ | — |
| F9 | B nit 4 | 時刻表記の不一致 | **real、訂正済み** (推定時刻を mtime へ置換。事前登録 22:09 → author 投入 22:10 → 実装 22:17 の順は保たれている) | — |
| F10 | A/B | 変換後の外側追跡・MAYBE 未変換経路・with・guard・結果名再束縛・finalbody 内 check | scope 外 (段 4 裁定 9〜11 のとおり、裁定パッケージ) | — |

## R3 の締め (fail-closed、production 4 箇所は影響なし — A が引数・Name store・module Assign を実 file で確認済み)

- **R3a:** 変換再送出の変換先 Name は、本 file の module scope ClassDef (件数 1) であり、かつ `module_assignments` に無く、かつ現 scope の局所束縛名 (R3b の集合) に無いこと。満たさなければ「その他」= False。
- **R3b:** 局所束縛名の集合 = 現 scope とその字句的親関数 scope (`_lexical_scopes(scope)` の `<module>` 以外) の各 body の `_potentially_bound_names` ∪ 各 scope の引数名 (posonlyargs / args / kwonlyargs / vararg / kwarg) ∪ `global_nonlocal_names`。
- **R3c:** `raise <as 名>` を bare とするのは、handler body (入れ子 def/class/lambda の本体を除く) で as 名が束縛されない (`_potentially_bound_names(tuple(handler.body))` に含まれない) ときだけ。含まれれば「その他」= False。

## 追加 test (fix 子が書く、既存 19 例と production pin の期待値は変えない)

正例: (p8) n7 と同じ source に module scope `class ChildError(X): pass` を足しただけ (ClassDef 有無だけが違う対) → covered。
負例 (各 1 理由、`[("BACKOFF_FIXED", sink, "reachable")]`):
- (n13) 関数内 `X = ValueError` の後 `except X as exc: raise PilotErr('r') from exc` (module scope `class PilotErr(RuntimeError)`) — 局所再束縛規則の専属 (規則を外すと DEFINITE 変換で受理される)。
- (n14) `except* X: raise` — TryStar 規則の専属 (3.11 未満は skip)。
- (n15) module scope `class PilotErr(RuntimeError): pass` の後に `PilotErr = X`、内側 `except X: raise PilotErr('r')`、外側 `except X: pass` — R3a の専属。
- (n16) `def build(build_fn, genome, ChildError=X)` + module scope `class ChildError(X)`、`except ChildError: pass` の後 `except X: raise` — R3b (引数) の専属。
- (n17) module scope `class ChildError(X)`、内側 `except X as exc:` の body が `exc = ChildError('r')` → `raise exc`、外側 `except ChildError: pass` — R3c の専属。

## 変異 matrix (本走前に fix 後の実 bytes で anchor 再検証、DW-M07)

M0 (comment、SURVIVED)、M1 (n_pilot 握り潰し、7 node)、M2 (bool 恒真 → 記録される全負例 = n8 以外・n10/n14 は 3.11 のみ)、M3 (bare→NONE、n2)、M4 (末尾 Raise を内部 Raise へ、n4)、
M5 (finally 脱出検査除去、n6)、M6 (文の値限定除去、n8)、M7 (変換先 ClassDef 限定除去、n9)、M8 (未知名→NONE、n7)、M9 (外側追跡停止 `[-1:]`、n11)、M10 (handler 脱出検査除去、n5)、
M11 (局所再束縛判定除去、n13 + n16)、M12 (R3a の再代入除外を外す、n15)、M13 (R3c の as 名再束縛検査を外す、n17)。
1 走目は上の予測集合で KILLED 登録し、MISMATCH が出た変異はその走を probe と明記して観測集合で再登録・再走 (F920 の手順)。
