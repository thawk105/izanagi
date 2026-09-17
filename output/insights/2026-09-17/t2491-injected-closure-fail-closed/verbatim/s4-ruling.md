# 段 4 裁定 (親) — [T-2491] plan v2 と変異事前登録 (2026-09-17 22:09 JST、mtime で実測。段 5 author 投入 22:10 の前)

裁定 inbox の再走査 (実測): local main は wave 開始後に docs のみ 2 commit 前進 (fd6aea6d1 第 21 回裁定 D2120 全 30 項 + 05eca6af4 fold)。
diff を「閉包 / injected / 2491 / 1882 / F918 / 握り潰」で検索し本件へ触れる項は 0 件。`docs/handoff/` は README + 2026-08-28 の 1 本 (本件無関係)。取り込みは受入前の post-claim merge で行う。

## 所見の裁定 (real/refuted、採否、scope)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| 1 | plan 未確定 1 | s8b_oracle_driver の check は try 2 重、外側 1660 の `Exception→break` で v1 は誤拒否 | **real、採用** → brief v1.1 (変換再送出で追跡停止) で解消。親が probe で 4 箇所の try 連鎖を実測 |
| 2 | plan 5 / lensB | P4 (前提 pin の assert) は追加の検査義務 | **real、採用 (落とす)** — D1869。前提は定数 + comment + 記録に留める。要否は裁定パッケージ候補へ |
| 3 | lensA (a) | 末尾 `raise` の手前に `return` (到達不能 raise) が穴 | **real、scope 内、採用** → handler body (入れ子 def/class/lambda 除く) に Return/Break/Continue があれば被覆に数えない |
| 4 | lensA (c) | enclosing finally の `return/break/continue` が例外を消す | **real、scope 内、採用** → check を body/handlers/orelse に含む全 enclosing try の finalbody (入れ子 scope 除く) に Return/Break/Continue があれば被覆に数えない。変換停止より先に検査 |
| 5 | lensA (h) | TryStar の拒否は変換停止より先 | **real、採用** → enclosing に TryStar があれば被覆に数えない (順序を固定) |
| 6 | lensA (i) | lambda / 内包表記内の call も現 scope の check として記録される | **real、scope 内、採用** → injected の check 記録は `call is returned_evidence_call` (Expr の値 / 単一 Name target の Assign・AnnAssign の値) に限る。F918 の「無条件の文」義務の形 |
| 7 | lensA (l) | `raise SystemExit(0)` を変換と読む | **real、scope 内、採用** → raise 文の形を固定 (下記) |
| 8 | lensA NONE / lensB | NONE の局所再束縛・module 再束縛・優先順位が未規定 | **real、scope 内、採用** → 名前分類の順序と再束縛条件を固定 (下記)。alias chain は **外す** (lensB 推奨、最小形) |
| 9 | lensA (n) | 変換後の外側 `except PilotError: pass` は見ない | **real、scope 外** — 閉じるには 1660 の `if evaluate_started: raise` の flow 証明 (D1882 却下の支配関係解析) か s8b 1788 の繰延べ (台帳変更、scope 外) が要る。保証限界として code comment・記録・裁定パッケージへ |
| 10 | lensB 推奨 2 | MAYBE bare 経路を後続 DEFINITE 変換で打ち切ると未変換 E の外側経路を捨てる | **real、scope 外 (9 と同根)** — 健全化すると s8b 1788 が誤拒否 (WAL tuple は Attribute = MAYBE)。前提 (E の親 class は組込みのみ、外来名は E の親でない) の下では MAYBE は実際には E を捕まえない。保証限界に明記 |
| 11 | lensA (d)(j)(k) | suppress / 条件 guard / 代入名の再束縛 | **real、scope 外** — D1882 却下範囲 (支配関係・値追跡)。裁定パッケージへ |
| 12 | lensA 前提 | helper の明示 raise 8 箇所は base E だが、属性アクセス等の非明示例外は E に包まれない | **real、記録** — 規則の保証は「helper の明示的な拒否 raise (E)」に限る、と comment に書く |
| 13 | lensB 推奨 1 | plan の正例 `except ChildError: pass` は v1.1 で負例 | **real、採用** → 正例は `class ChildError(X): pass` を module scope に置く (NONE)。未知名版は MAYBE 負例として残す |
| 14 | lensB 推奨 3 | M1 だけでは帰属にならず M3/M4 の anchor が旧仕様 | **real、採用** → 変異は author 後の実 bytes で anchor を確定、新旧両走で閉包 node の旧 PASSED / 新 FAILED を示す |
| 15 | lensB scope | production pin は 4 sink の covered 限定、全 injected 集合固定・floor deferred 固定・failures==[] 再 assert は省く | **採用** |
| 16 | lensB scope | 共有 method (`_flow_statement` / `_record_expression`) への限定的な記録追加は D1869 違反でない | **採用** (境界 = 変更する判定と検査義務) |
| 17 | plan | `rg` で `returned_evidence_checks` は 3 箇所 (1583 宣言 / 1727 書込 / 2176 読取) | 訂正を受理 |

規律 2 の基準: 受理集合の比較基準は **現行 main** (弱い一致だけ)。v2 は main の injected 受理集合の真部分集合 (既存一致条件を保存し `and unswallowed` を AND する)。
v1 は provisional であり基準にしない (lensA 3 項の指摘に答える)。

## plan v2 — 「握り潰されていない」(unswallowed) の確定規則

E = helper の error class = s1 `DriverError`。前提 (comment に書き、assert しない): helper の明示的な拒否 raise はすべて base の `DriverError(...)`、
`class DriverError(RuntimeError)`。規則の保証対象は「helper の明示的な拒否 raise」だけ。

**R0 (記録):** injected 経路の check は `_record_expression` で `call is returned_evidence_call` (文の値そのもの) のときだけ記録する。
名前 suffix・第 1 引数 Name・行範囲の既存条件はそのまま。記録は `(lineno, result_name, unswallowed)`。

**R1 (enclosing try の収集):** scope ごとに空から始める stack を `_flow_statement` の Try 分岐で管理する。stack の要素は `(try_node, position)`、position ∈ {body, handler, orelse}
(finalbody 内の check は当該 try の要素を積まない)。入れ子 def/class の本体は別 scope なので引き継がない。with body は同 scope なので引き継ぐ。

**R2 (先に落とす条件、順序固定):** 次のいずれかなら `unswallowed = False`。
- stack に TryStar (`type(node).__name__ == "TryStar"`) がある。
- stack のいずれかの try の finalbody (入れ子 def/class/lambda の本体を除く) に Return / Break / Continue がある。

**R3 (handler 追跡):** position が body の try だけを内側から外側へ辿る (handler / orelse 内の check は当該 try の handlers に捕まらない)。各 try で handler を順に見る。
- 名前分類 (優先順位どおり、最初に当たったもの):
  1. **MAYBE**: type が Name でも tuple でもない式 (Attribute / Call / Subscript …)。Name で現 scope が関数のとき `_potentially_bound_names(tuple(body.body))` または `global_nonlocal_names` に含まれる (局所再束縛)。Name で `module_assignments` に含まれる (module 再束縛)。
  2. **DEFINITE**: bare (type None) / `BaseException` / `Exception` / `RuntimeError` / module scope の `from <_RETURNED_EVIDENCE_MODULES> import DriverError [as X]` の束縛名 X / helper を自 module で定義する module (`<module>.require_returned_condition_evidence` が `self.bodies` にある) では module scope の `class DriverError` の名前。
  3. **NONE**: 本 file の module scope `ClassDef` (E 以外、同名 ClassDef が 1 つだけ) の名前。ただし helper 定義 module で `DriverError` が `module_assignments` にある (E が再束縛) ときは NONE を無効化し MAYBE にする。
  4. それ以外の Name (他 module からの import 名、束縛不明) → **MAYBE**。
  - tuple: 要素に DEFINITE があれば DEFINITE、なければ MAYBE があれば MAYBE、全部 NONE なら NONE。
- handler body 条件 (共通): body (入れ子 def/class/lambda の本体を除く) に Return / Break / Continue があれば **False**。末尾 top-level 文が `ast.Raise` でなければ **False**。
- raise 文の形:
  - **bare**: `raise` / `raise <handler の as 名>` / `raise <DEFINITE の E 名>(...)` (`from` の有無不問) → E のまま外側へ。
  - **変換**: `raise <本 file の module scope ClassDef の Name>(...)` (`from` の有無不問、`SystemExit` 等の組込み・Attribute・その他は不可) → 追跡停止、True。
  - その他 (`raise SystemExit(0)`, `raise mod.Err(...)`, `raise 1`) → **False**。
- 判定: NONE は読み飛ばす。MAYBE は bare でなければ False、bare なら次の handler へ。DEFINITE は bare なら外側の try へ (この try の残り handler は見ない)、変換なら True。
  DEFINITE が無いまま handler が尽きたら外側の try へ。stack を使い切ったら True。

**R4 (被覆):** `coverage_for_sink` の injected 分岐は既存の一致条件に `and unswallowed` を AND する。comment を保証内容と限界へ書き換える:
保証 = 「helper の明示的な拒否 (E) を捕まえる最初の handler が再送出し、bare 再送出は外側でも同じ条件を満たす。変換再送出以後・with の `__exit__`・条件 guard・代入名の再束縛・
変換後の例外の外側での扱いは検査しない (D1882 の名指し外、裁定パッケージ)」。

production 4 箇所の追跡 (親と lensB が独立に一致): n_pilot 1017 = DEFINITE 変換 → True。s8b 1730 = MAYBE(WAL tuple) bare → DEFINITE 変換 → True (1660 は見ない、R2 で 1660 の finally は無い)。
s1 1218: 1204 = MAYBE bare → NONE 読み飛ばし → DEFINITE bare → 1151 (handler なし、finally に脱出文なし) → True。s1 1295: 1279 → 1204 → 1151 → True。
局所再束縛の確認 (author が実測): `run_role` / `run_block` / `build_binaries` の body で `DriverError` / `S1DriverError` / `_SortSwoOracleRejected` が束縛されないこと。

## synthetic test (author が書く、relative path は `orchestrator/campaign/synthetic_t2491_*.py`、sink は `injected-build_fn`、patch 集合 `{"BACKOFF_FIXED"}`)

正例 (期待 covered、`failures == []`): (p1) try 無し / (p2) `except X: raise` / (p3) `except X as exc: raise PilotErr(...) from exc` (module scope `class PilotErr(RuntimeError)`) /
(p4) s1 1208 形 = `except (wal.A, wal.B): raise` (Attribute = MAYBE bare) → `except ChildError: pass` (module scope `class ChildError(X)` = NONE) → `except X: raise` → `except Exception: return None` /
(p5) DEFINITE bare の外側 try でも DEFINITE bare / (p6) check が外側 try の handler 内にある (その try の handlers は関係しない) / (p7) `raise exc` (as 名) の bare 扱い。
負例 (期待 `[("BACKOFF_FIXED", sink, "reachable")]`、各 1 理由): (n1) `except X: pass` / (n2) bare `except: pass` / (n3) `except Exception: return None` / (n4) `except X: if c: raise` /
(n5) `return` の後の到達不能 `raise` / (n6) enclosing finally が `return` で終わる (handler は `except X: raise`) / (n7) 未知名 `except ChildError: pass` (ClassDef 無し = MAYBE) の後に `except X: raise` /
(n8) check を lambda に包む / (n9) `except X: raise SystemExit(0)` / (n10) `except* X: pass` / (n11) DEFINITE bare の外側 try が `except Exception: pass` / (n12) 関数内で `X = ValueError` の後 `except X: pass`。
production pin: `test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered` — 4 sink (path 末尾・scope・lineno・kind で名指し) の分類が `{"covered": len(patch_sources)}` (literal 38 を焼き込まない)。

## 変異事前登録 (anchor は author 後の実 bytes で確定、probe → 本走の 2 巡、DW-M08 の新旧両走)

runner argv (両走共通、T-2154 と同じ): `python3 tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_s8b_oracle_n_pilot.py orchestrator/tests/test_ccbench_spawn_sites.py`。
harness = `tools/mutation_worktree.py --commit <sha> --runner-mode dispatch --detached`、spec / out は checkout 外 (job dir)。

- **旧走 (commit = main 38353207f):** M1 のみ。期待 KILLED = n_pilot 3 node (`test_injected_build_fn_without_condition_records_is_rejected`、
  `test_build_binaries_uses_binding_flags_and_prepared_records_independently`、冗長 gate `test_r33_successor_protocol_document_loads_from_repository`)。
  閉包 node の緑は「完全一致契約 (余分な赤があれば MISMATCH)」+ log の passed 件数で示す。
- **新走 (commit = 統合 commit):** M0 = comment 1 行 (positive、SURVIVED、期待空)。M1 = F918 m04 同一置換 (n_pilot 1028〜1029 → `except S1DriverError:\n                pass`、元 spec と bytes 照合済み)、
  期待 KILLED = 上 3 + 閉包検査 + `classifies_t2155_production_sinks_exactly` + `t2520_certify_entry_removal` + 新 production pin = 7 (r33 は冗長 gate と明記、帰属証拠から外す)。
  M2 = `unswallowed` を恒真化 → 新負例 n1〜n12 (probe で観測)。M3 = bare handler を DEFINITE から外す → n2。M4 = 末尾 Raise 判定を「body 内に Raise がある」へ緩める → n4・n5。
  M5 = finally の脱出検査を外す → n6。M6 = `call is returned_evidence_call` の限定を外す → n8。M7 = 変換先の ClassDef 限定を外す → n9。
  帰属は各変異につき新負例 ≥1 が専属 killer であること。既存 synthetic 群 (campaign 経路) は M2〜M7 に反応しない (lensB が assertion 単位で確認)。
- 冗長 gate: r33 digest pin (driver bytes)。他は probe で観測してから宣言。

## 裁定パッケージ候補 (scope 外、段 7 で insight に列挙、実装しない)

(9) 変換後の例外の外側追跡 (s8b 1660 の条件付き再送出の flow 証明 or 1788 の繰延べ)、(10) MAYBE の未変換経路、(11) suppress / 条件 guard / 代入名の再束縛、
(2) 前提 pin (E の基底が組込みのみ、helper の raise が E) の要否、helper の非明示例外 (属性アクセス等) の扱い、module alias chain の要否。
