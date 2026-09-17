## 段 1 brief (親) — [T-2491] 閉包検査 injected-* 経路を fail-closed へ (D1882 の実装)

- **研究前進:** 土台 (正しさ防壁)。閉包検査 `test_define_sink_cross_product_has_no_unreviewed_ungated_member` は
  「CC variant を build する全 sink が測定条件の関門 (condition evidence) に支配される」を静的に保証し、材料レポートの
  条件 evidence 主張 (D1198 / D1845 の実効範囲記録) の土台である。F918 は injected-* 経路でこの保証が「call の位置と
  第 1 引数名」しか見ておらず、拒否を握り潰す実装 (`except: pass`) でも緑のままだと実測した。放置すると、条件を満たさない
  build の record が拒否されないまま certified 経路へ流れうるのに閉包検査は緑を出す (DW-G05: 受理集合が変わる)。
  完了判定 = F918 の変異 m04 と同じ置換で閉包検査が赤 (KILLED)、production の injected sink 4 つは covered のまま、
  既存の分類 pin は不変。
- **scope:** `orchestrator/tests/test_ccbench_spawn_sites.py` の名指しの判定 1 箇所 (下表) の fail-closed 化 + その正例・負例 test +
  変異事前登録。production (`orchestrator/campaign/*.py`) は変えない。campaign 経路 (`_campaign_checked_root` /
  `returned_evidence_names`) は変えない。追加 gate・新しい台帳・族全体の共有機構 (import 真正性・shadow・支配関係の静的検査) は scope 外 (D1882 が却下、D1869)。
- **確定済みユーザー裁定:** D1882 (弱い一致だけでは被覆済みに数えない、fail-closed 側へ寄せる、名指し分だけ変える)、D1869 (最小形)、
  引数: 着手直前の local main から fresh worktree / Codex author (D95) / 変異事前登録 / 規律 2 を緩めない / 本題の判定修正だけ。
- **一次資料 (逐語は verbatim/):** D1882、D1869、F918、T-2154 の変異台帳 (m04 の置換文字列と当時の期待 node)。
- **変更面 (実アンカー、main 38353207f):**
  | 場所 | 現状 | 変更 |
  |---|---|---|
  | `_PythonGateFlow.coverage_for_sink` 2164〜2190 行 (`matching_checks`) | `sink.lineno < line < boundary and checked_name == result_name` だけで `coverage | patch_macros` | 一致 call が「握り潰されていない」ときだけ被覆に数える |
  | `_PythonGateFlow._record_expression` 1723〜1730 行 | `returned_evidence_checks[scope].append((lineno, result_name))` | 3 要素目に「握り潰されていない」判定 (bool) を足す |
  | `_PythonGateFlow._flow_statement` 1866〜1897 行 (Try 分岐) | handler を flow するだけ | `statement.body` を flow する間だけ enclosing handlers を stack に積む (scope ごとに空から開始) |
  | `_PythonGateFlow.__init__` 1583 行 | `returned_evidence_checks` の型注釈 | 3 要素へ |
  | 定数 1218〜1222 行付近 | `_RETURNED_EVIDENCE_HELPER` / `_MODULES` | helper の error class 名 `DriverError` と、それを捕まえうる組込み名の表を足す |
  | 新規 test (2900〜3200 行の synthetic 群の隣) | campaign 経路の負例のみ | injected 経路の正例・負例 (下記 P5) と production injected sink 4 つの covered pin |
- **production の injected-* sink (実測、main):** s1_direct_comparison.py 1208 (`prepare_cell_fn`、check 1218) / 1288 (`evaluate_fn`、check 1295)、
  s8b_oracle_driver.py 1788 (`evaluate_fn`、check 1801)、s8b_oracle_n_pilot.py 997 (`build_fn`、check 1018) = covered 38。
  s8b_floor_campaign.py 4722 = deferred (台帳、触らない)。各 check を囲む try の handler 順 (実測):
  s1 1204-try = `(WalAppendError, WalFramingError)`→raise / `_SortSwoOracleRejected`→swallow (DriverError の**子** class) / `DriverError`→raise / `Exception`→swallow;
  s1 1281-try = WAL→raise / `DriverError`→raise / `Exception`→swallow; s8b_oracle_driver 1775-try = WAL→raise / `S1DriverError`→`raise OracleDriverError(...) from exc` / `Exception`→swallow;
  n_pilot 1017-try = `S1DriverError`→`raise PilotError(...) from exc` のみ。helper (s1 358 行) の raise 文 7 箇所はすべて `DriverError(`、`class DriverError(RuntimeError)` (s1 113 行)。
- **不変条件:** (i) 規律 2: 受理形を増やす向きの変更は不採用。判定できない形は「被覆に数えない」(fail-closed)。(ii) production 4 sink は covered のまま、
  `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` の pin と繰延べ台帳 (8 entry) は不変。(iii) campaign 経路の既存 test 群 (2900〜3200 行) は不変。
  (iv) 本 wave が名指す判定以外の共有機構を変えない (D1869)。(v) 保証限界 (with による抑止、局所 alias、条件 guard の反転) は code comment に明記し、名乗らない。
- **成果物:** test file 1 本の差分 (Codex author)、変異 matrix (baseline + F918 同一置換 + 判定を外す変異 + 等価 M0)、受入全走緑、insight
  (`output/insights/2026-09-17/t2491-injected-closure-fail-closed/`)、spool fragment (worklog / failures F918 恒久対応の追記 / decisions は段 7 で要否を裁定)。
- **分割方針:** 実装子 1 本 (test file 単独所有)。段 2 plan 1 本、段 3 consult 2 本 (レンズ A: 規律 2 / fail-closed の穴 — 新判定を通り抜ける握り潰し形、
  レンズ B: production 4 sink の誤拒否と D1882/D1869 の scope 逸脱)、段 6 review 2 本。軽量版を採らない理由 = 正しさ防壁の受理集合が変わる (DW-C00)。
- **割れうる前提 (親の provisional 裁定・攻撃対象):**
  - (P1) 「握り潰されていない」の定義: check call を囲む各 try (同一 scope 内、`body` に限る) について、**handler を順に見て helper の error class を
    捕まえうる最初の handler** が再送出していること。捕まえうる = 型なし (bare) / `BaseException` / `Exception` / `RuntimeError` / helper の error class に束縛された名前
    (module scope の `from <s1 module> import DriverError [as X]`、helper を自 module で定義する module では module scope の `class DriverError`)、tuple はいずれかの要素。
    それ以外の名前 (`WalAppendError`、`_SortSwoOracleRejected` 等) は「捕まえない」と扱う。根拠 = helper は base の `DriverError` を直接 raise し、子 class の handler は base を捕まえない。
    捕まえうる handler が無ければ「握り潰されていない」。
  - (P2) 「再送出」の定義: handler body の最後の top-level 文が `ast.Raise` (bare `raise` でも `raise Y(...) from exc` でも可)。`pass` / `return` / 代入 / `if …: raise` (条件付き) は握り潰し。
  - (P3) import 真正性・shadow・支配関係は injected 経路へ足さない (D1882 の却下選択肢)。実測上も `_has_unshadowed_returned_evidence_helper` は helper を**定義する** s1 module で False を返すので、
    流用すると s1 の injected sink 2 つが誤拒否になる。suffix 一致 + 第 1 引数名 + 行範囲の既存条件は残し、その上に P1 を AND する。
  - (P4) 前提の pin: P1 の表は「helper は `DriverError` を raise し `DriverError(RuntimeError)`」に依存する。同 test module 内に、s1 source の helper 本体の raise 文がすべて `DriverError(` で、
    `class DriverError(RuntimeError)` が module scope にあることを固定する assert を 1 本置く (判定の前提であって追加 gate ではない、と親は読む)。反対なら段 4 で落とす。
  - (P5) 正例・負例 (synthetic、injected-build_fn 形): 負例 = `except X: pass` / bare `except: pass` / `except Exception: return None` / `except X: if c: raise`;
    正例 = try 無し / `except X: raise` / `except X as exc: raise Y(...) from exc` / 子 class 風の未知名 handler (swallow) の後に error class handler (raise) がある s1 1208 形 /
    error class handler (raise) の後に `except Exception` (swallow) がある形。production pin = 4 sink が covered、deferred 1 は deferred。
  - (P6) 変異事前登録 (段 4 で確定): M0 = comment 1 行 (SURVIVED)。M1 = F918 m04 と同一置換 (n_pilot `except S1DriverError as exc: raise PilotError(...) from exc` → `except S1DriverError: pass`)、
    期待 = 閉包検査 + 分類 pin test + T-2154 の負例 2 + 冗長 gate (`test_r33_successor_protocol_document_loads_from_repository`、driver bytes pin) + 新 production pin。
    M2 = 新判定を外す (`unswallowed` を恒真に) → 新 synthetic 負例群が赤。M3 = 捕まえうる表から bare except を落とす → bare 負例が赤。M4 = 再送出判定を「Raise を含む」に緩める → 条件付き raise 負例が赤。
    冗長 gate と期待 node は probe 走で観測してから本走に登録する (F920)。
- **受入・実測環境:** 焦点走は `tools/run_tests.py` (login node の headroom 判定で計算ノードへ自動 dispatch されうる、baseline を投入済み)、変異 matrix は
  `tools/mutation_harness.py` (container worktree、spec/out は checkout 外)、受入全走は `tools/dev_wave_wait.py acceptance` (`IZANAGI_ACCEPTANCE_SHARDS=3`)。
- **条件 dispatch の判定:** DW-O08/O09/O10 非成立 (test file のみ、凍結成果物・producer に触れない、test file の bytes pin 0 件)。DW-O13: 受理形を**減らす**改訂で新設に当たらないが
  「gate 入力の実在」は実測済み (上の handler 順)。DW-O11 非成立。DW-O19 は変異 matrix で成立 → 段 6 前に読む。DW-O14 非成立。

## v1.1 訂正 (段 2 plan の所見を受けて親が実測、2026-09-17 21:57 JST、mtime で実測)

- **訂正 1 (実測):** helper 本体の raise 文は 7 でなく **8 箇所** (369/371/376/379/384/392/396/403 行、すべて `DriverError(`)。s1 の内側 try は 1279 行、s8b_oracle_driver の直近 try は 1730 行 (brief の 1281/1775 は campaign call の行だった)。
- **訂正 2 (実測、plan の未確定事項 1):** check を囲む try は 1 つではない。親の probe (repo 外 script、AST) で enclosing try 連鎖 (外→内) は
  s1 1218 = [1151 (finally のみ), 1204]、s1 1295 = [1151, 1204, 1279]、s8b_oracle_driver 1801 = [1660, 1730]、n_pilot 1018 = [1017]。
  1660-try の handler は `(wal.WalAppendError, wal.WalFramingError)→raise` / `Exception→break 終端 (条件付き raise)`。
  brief v1 の P1/P2 を「全 enclosing try」へ当てると s8b_oracle_driver 1788 が誤拒否になる (plan の指摘は real)。
- **P1/P2 の精密化 (v1.1、provisional・攻撃対象):** E = helper の error class (s1 `DriverError`)。check 文を body に含む enclosing try を**内側から外側へ**辿り、各 try の handler を順に見る。
  - handler 型の分類: **DEFINITE** = bare / `BaseException` / `Exception` / `RuntimeError` / E に束縛された名前 (module scope の `from <s1 module> import DriverError [as X]`、
    module scope の Name 代入 chain、helper を自 module で定義する module では module scope の `class DriverError`)。**NONE** = 本 file の module scope `ClassDef` (E 以外) に束縛された名前
    (E とは別 class であり、E の親 class にはなれない。子 class は base の E を捕まえない)。**MAYBE** = それ以外すべて (Attribute・Call 等の式、他 module からの import 名、束縛不明の名前)。
    tuple = 要素に DEFINITE があれば DEFINITE、なければ MAYBE があれば MAYBE、全部 NONE なら NONE。`except*` (TryStar) の body 内の check は被覆に数えない。
  - 判定: NONE は読み飛ばす。MAYBE は**末尾が bare `raise`** でなければ被覆に数えない (変換再送出も不可、fail-closed)、bare なら次の handler へ。DEFINITE は末尾が `ast.Raise` でなければ被覆に数えない;
    bare `raise` なら E のまま外側 try へ追跡を続ける; `raise Y(...) [from exc]` (変換再送出) なら**そこで追跡を止め被覆に数える** (F918 が配線側へ課した義務の形そのもの)。
    DEFINITE が無ければ E はそのまま外側へ伝播するので外側 try の検査へ続ける。全 try を通れば被覆に数える。
  - 「末尾」= handler body の最後の top-level 文。`pass` / `return` / 代入 / `if …: raise` / `try/finally` や `with` の内側だけの raise は握り潰し扱い (fail-closed)。
  - production 4 箇所の判定 (親の静的追跡): n_pilot 1017 = DEFINITE 変換 → 止。s8b 1730 = MAYBE(WAL tuple) bare ✓ → DEFINITE 変換 → 止 (1660 は見ない)。
    s1 1218: 1204 = MAYBE bare ✓ → NONE(`_SortSwoOracleRejected`) 飛ばす → DEFINITE bare → 1151 (handler なし) → 通。s1 1295: 1279 = MAYBE bare ✓ → DEFINITE bare → 1204 (同上) → 1151 → 通。
  - **保証限界 (名乗らない):** with の `__exit__` による抑止、関数内の局所 alias、条件 guard の反転、変換後の例外 (PilotError / OracleDriverError) の外側での扱い、finally 内の return/break による抑止。
- **P4 は落とす** (plan 推奨どおり)。前提 (helper が E を直接 raise、`DriverError(RuntimeError)`) は code comment と本 wave の記録に留め、独立の assert は置かない。
- **M1 の期待 node** は plan の指摘どおり `test_define_sink_cross_product_t2520_certify_entry_removal` (`failures == []` を assert) も候補に含め、probe 走で完全集合を観測してから登録する。
  T-2154 m04 の負例 2 件の node 名は元 spec (`output/insights/2026-09-09_t2154-n-pilot-prereg-successor/mutation-spec.json`) に実在:
  `test_s8b_oracle_n_pilot.py::test_build_binaries_uses_binding_flags_and_prepared_records_independently` と `::test_injected_build_fn_without_condition_records_is_rejected`。
