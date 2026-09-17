# [T-2491] 閉包検査の injected-* 経路を fail-closed へ寄せた — 握り潰された返却物検査を被覆に数えない (D1882 の実装)

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2491-injected-closure-fail-closed`
- 基準 commit: `38353207f719acb0871cfe3d9bbe3a02490282bb` (local main、wave 開始時 2026-09-17 21:37 JST)。記録前に main `60b4bd13f`
  (docs のみ 5 commit: 第 21 回裁定 D2120 の fold、[T-1912] erratum) を no-ff で取り込んだ (merge commit `f126933e2`)
- 実装 commit: `125ab5fd1` (Codex `role=author`、test file 1 本、+380/−16) + 段 6 fix `79dd07742` (Codex `role=author`、同 file、+125/−10)
- 起票: `docs/archive/worklog-phase3-0916-1527.md` の [T-2491] 項 (T-2154 wave の段 3 所見と変異 m04 の実測 = F918)
- 裁定: D1882 (弱い一致だけでは被覆済みに数えない、fail-closed 側へ寄せる、名指しした判定だけ変える)、D1869 (最小形)
- 設計判断: 本 wave の decisions fragment (slug `injected-closure-unswallowed-rule`、D 番号は land の fold が付ける)
- 逐語: 本 dir の `verbatim/` (brief・plan・consult 2・裁定・author・review 2・fix・焦点再レビューの prompt と出力、焦点走 log 2 本)。
  `verbatim/` の 7 file (focus1 log、s2-plan、s3-lensA/B、s6-reviewA/B、s6-focus) は `git diff --check` 抵触の行末空白を可逆に除去した (可視文字不変)。
  原文 sha256・bytes・除去した (行番号, 空白) と復元法は `verbatim/normalization.json`
- 変異: `mutation-spec-old.json` / `mutation-ledger-old.json` (main 38353207f 側)、`mutation-spec-new.json` / `mutation-ledger-new.json` (79dd07742 側)

## 何をしたか

`orchestrator/tests/test_ccbench_spawn_sites.py` の閉包検査 `test_define_sink_cross_product_has_no_unreviewed_ungated_member` は、
injected-* kind の sink (呼び手が `build_fn` / `evaluate_fn` / `prepare_cell_fn` を注入する経路) について、「sink の代入名を第 1 引数にもつ
`require_returned_condition_evidence` 系の call が sink 行と次の injected sink 行の間に 1 つある」だけで patch macro 全件を被覆済みに数えていた
(`_PythonGateFlow.coverage_for_sink` の `matching_checks`)。F918 は、この call の拒否を `except S1DriverError: pass` で握り潰しても閉包検査が緑のままだと
実測している。本 wave は D1882 に従い、この名指しの判定だけを変えた。

**新しい判定 (段 4 裁定 R0〜R4 + 段 6 裁定 R3a〜R3c、`verbatim/s4-ruling.md` / `s6-ruling.md` が逐語):**

- R0: 記録する check は「文の値そのもの」の call だけ (Expr の値、単一 Name target の Assign / AnnAssign の値)。lambda・内包表記・短絡式の中の call は記録しない。
- R1: scope ごとに空から始める enclosing try の stack を flow 解析の Try 分岐で持つ (body / handler / orelse を区別、finalbody 内は積まない)。
- R2 (先に落とす): stack に `except*` (TryStar) がある、または enclosing try の finalbody (入れ子 def / class / lambda を除く) に return / break / continue がある → 被覆に数えない。
- R3: position が body の try を内側から外側へ辿り、handler を順に分類する。DEFINITE = bare / `BaseException` / `Exception` / `RuntimeError` / s1 module から import した `DriverError` の束縛名
  (helper を自 module で定義する s1 では module scope の `class DriverError`)、NONE = 本 file の module scope ClassDef (E 以外、件数 1)、MAYBE = それ以外 (Attribute 等の式、
  他 module からの import 名、束縛不明の名前、module / 局所 / 字句的親関数 / 引数で再束縛された名前)。tuple は要素の最強で決める。
  NONE は読み飛ばす。MAYBE は末尾が bare `raise` でなければ被覆に数えない。DEFINITE は handler body に脱出文 (return / break / continue) が無く末尾が `raise` であること。
  raise の形: bare (`raise` / 再束縛されていない as 名 / E 名の再構築) は E のまま外側の try へ追跡を続ける。変換 (`raise <本 file の module scope ClassDef で module / 局所 / 引数の
  再束縛が無い名前>(...)`) は追跡を止めて被覆に数える。その他 (`raise SystemExit(0)`、Attribute、非 Call) は被覆に数えない。
- R4: 既存の一致条件に `and unswallowed` を AND する。受理集合は現行 main の真部分集合。

**production への影響:** injected sink 4 つ (s1_direct_comparison.py 1208 / 1288、s8b_oracle_driver.py 1788、s8b_oracle_n_pilot.py 997) は covered のまま
(親・段 3 レンズ B・段 6 レビュー A・焦点再レビューが独立に静的追跡し一致、新 test `test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered` が pin)。
繰延べ台帳 (8 entry、s8b_floor_campaign の injected sink を含む)・campaign 経路 (`returned_evidence_names` / `_campaign_checked_root`)・production・既存 test の期待値は不変。

**保証と限界 (code comment と本記録に明記、名乗らない):** 保証するのは「helper の明示的な拒否 (s1 `DriverError`) を捕まえる最初の handler が脱出せず再送出し、bare 再送出は外側の
try でも同じ条件を満たす」ことだけ。次は検査しない — 変換再送出 (`raise PilotError(...) from exc`) の後の外側の扱い (s8b_oracle_driver 1660 の `except Exception` は `if evaluate_started: raise`
の条件付き再送出で、静的に追跡すると誤拒否になる)、MAYBE 型の handler が実際に E を捕まえて bare 再送出する未変換経路、`with` の `__exit__` による抑止、条件 guard、代入名 (result_name) の
再束縛、finalbody 内の check 自身の拒否、helper の非明示例外 (属性アクセス等)。再束縛の検査は本 file の module 直下の単純代入・現関数と字句的親関数の束縛と引数・handler body だけを見る。
TryStar 規則は Python 3.10 (login / 計算ノードとも) では `except*` が構文エラーで n10 / n14 が skip されるため実走検証されていない。

## 段 2〜6 の所見と裁定 (逐語は verbatim/、要約)

- 段 2 plan (`s2-plan.md`): brief v1 の「全 enclosing try に P1/P2」は s8b_oracle_driver の外側 1660-try (`Exception→break` 終端) で誤拒否になると静的に指摘 (real)。親が repo 外 probe で
  4 check の try 連鎖を実測 (s1 1218 = [1151 finally のみ, 1204]、s1 1295 = [1151, 1204, 1279]、s8b 1801 = [1660, 1730]、n_pilot 1018 = [1017]) し brief v1.1 (内→外へ辿り変換再送出で停止) へ訂正。
  helper の raise 文は 7 でなく 8 箇所 (親の誤り)。
- 段 3 レンズ A (`s3-lensA.md`): v1.1 を通り抜ける形 14 種を判定。real・scope 内 = 到達不能 raise (a)、finally の脱出 (c)、TryStar の順序 (h)、lambda 内 call の記録 (i)、`raise SystemExit(0)` (l)、
  NONE 分類の再束縛と優先順位。real・scope 外 = 変換後の外側握り潰し (n)、suppress (d)、条件 guard (j)、代入名の再束縛 (k)。「(n) を名指し外と断定して済ませる親の読みは支持しない」。
- 段 3 レンズ B (`s3-lensB.md`): production 4 箇所の追跡は親と一致。plan の正例 `except ChildError: pass` (未知名) は v1.1 では負例 (real、ClassDef 化で解消)。MAYBE bare → DEFINITE 変換で
  打ち切ると未変換 E の外側経路を捨てる (real、(n) と同根)。alias chain は最小形から外す、P4 (前提 pin の assert) は落とす、production pin は 4 sink 限定を推奨。
- 段 4 裁定 (`s4-ruling.md`): 17 所見を real/refuted・採否・scope で裁定。(n) と MAYBE 未変換経路は scope 外 (閉じるには 1660 の flow 証明 = D1882 却下の支配関係解析か、
  s8b 1788 の繰延べ = 台帳変更が要る)、保証限界として明記し裁定パッケージ候補へ。規律 2 の比較基準は現行 main。
- 段 5 author (`s5-author.md`): R0〜R4 + synthetic 正例 7 / 負例 12 + production pin。sandbox では dispatch の `qstat -Q` preflight が失敗し未実走 → 親の焦点走 66 passed / 1 skipped (計算ノード)。
- 段 6 レビュー A (`s6-reviewA.md`): 実装 must-fix 0。裁定の規則どおりだが穴 3 つ = (a) 変換先の module 再代入 (`PilotErr = X`)、(b) 字句的親関数・引数での束縛、(c) as 名の再代入。
  n3 は過剰決定、n7/p4 は一変更対でない、n10/n12 は名付けた規則の専属 killer でない。
- 段 6 レビュー B (`s6-reviewB.md`): 報告と実体の食い違い無し、scope 逸脱無し。M2/M4 の期待集合は author 補正 (M2 = n8 以外、M4 = n4 のみ) が正。追加登録案 (n7 / n11 / n5 killer)。
  親の時刻表記が推定で不一致 (real) → 親が全部 mtime で実測して訂正 (事前登録 22:09 → author 投入 22:10 → 実装 22:17 の順は保たれている)。
- 段 6 裁定 (`s6-ruling.md`): (a)(b)(c) を R3a〜R3c として締める (production 4 箇所に該当形無し、レビュー A が実 file で確認)。p8 + n13〜n17 を追加、変異 M8〜M13 を追加。
- 段 6 fix (`s6-fix.md`): R3a〜c + comment + p8 / n13〜n17。未実走 → 親の焦点走 71 passed / 2 skipped (login)。
- 焦点再レビュー (`s6-focus.md`): must-fix 0。F1〜F3 closed (反例 3 つを独立に組み拒否を追跡)、F5〜F7 partial (p8 は共通 fixture が PilotErr も足すので厳密な一変更対でない、
  n3/n10/n12 の非専属性は残る、spec 反映は射影外)、F4/F8〜F10 closed。nit: p8 の厳密対、comment の射程表現 (module 直下の単純代入・字句的親・handler body、module scope でも global/nonlocal を含む)。
  親はいずれも受理集合に影響しないので記録に留めた。

## 変異 matrix (DW-M08 の新旧両走、`tools/mutation_harness.py --runner-mode dispatch --detached`、計算ノード)

runner argv (両走共通、T-2154 と同じ): `python3 tools/run_tests.py --force-dispatch -q -rf orchestrator/tests/test_s8b_oracle_n_pilot.py orchestrator/tests/test_ccbench_spawn_sites.py`。
harness は job dir 外の使い捨て detached worktree (`/work/1/SFC/tanab/dev-wave-scratch/t2491-injected-closure/{old,new}-tree`、submodule 初期化済み) に対して直接当てた
(共有木 attestation の wrapper は並行 wave 下で成立しないため)。D612 の queue-wait / grace 上書き 1800 / 600。

- **旧走 (main `38353207f`、spec sha `d9c5edf0…`、1 走)**: baseline PASSED (154 passed、76 秒)。M1 = F918 m04 と同一置換 (n_pilot 1028〜1029 の `except S1DriverError as exc: raise PilotError(...) from exc`
  → `except S1DriverError:\n pass`) は **KILLED、赤 = n_pilot 3 node 完全一致** (`test_injected_build_fn_without_condition_records_is_rejected`、
  `test_build_binaries_uses_binding_flags_and_prepared_records_independently`、冗長 gate `test_r33_successor_protocol_document_loads_from_repository` = driver bytes の digest pin)。
  151 passed = **閉包検査は緑のまま** (完全一致契約なので閉包 node が赤なら MISMATCH になる)。
- **新走 (`79dd07742`、spec sha `9b3662fc…`、1 走で完全一致、probe 不要)**: baseline PASSED (178 passed / 2 skipped、105 秒)。M0 (comment 1 語) SURVIVED。M1〜M13 の 13 件すべて KILLED、
  期待 node 完全一致 (matching 14/14、MISMATCH 0、TIMEOUT 0、全 anchor 1 箇所)。**M1 の注入 diff は旧走と sha256 が同一 (`d2542e4c…`)** で、赤は旧 3 node + 閉包検査 +
  `classifies_t2155_production_sinks_exactly` + `t2520_certify_entry_removal` + 新 production pin = 7 node。**同じ変異で閉包検査が旧版 PASSED / 新版 FAILED** = 新テストだけが検出する差分。
- 専属 killer (新 synthetic 負例、`test_define_sink_cross_product_t2491_rejects_injected_swallow[...]` / `..._rebinding[...]`): M2 (unswallowed 恒真) → n8 以外の 14 node (n10 / n14 は 3.10 で skip)、
  M3 (bare handler を DEFINITE から外す) → n2、M4 (末尾 Raise を内部 Raise へ緩める) → n4、M5 (finally 脱出検査除去) → n6、M6 (文の値限定除去) → n8、M7 (変換先の ClassDef 限定除去) → n9、
  M8 (未知名→NONE) → n7、M9 (外側追跡を止める) → n11、M10 (handler 脱出検査除去) → n5、M11 (局所再束縛判定除去) → n13 + n16、M12 (変換先の module 再代入除外を外す) → n15、
  M13 (as 名の再束縛検査を外す) → n17。
- 冗長 gate: r33 digest pin (driver bytes に反応、M1 の帰属証拠から外す)。M1 の意味的帰属 = 閉包検査 + 分類 pin 2 + production pin + n_pilot 負例 2。

## 実走

- 焦点走 (test file 単独): 125ab5fd1 = 66 passed / 1 skipped (計算ノード、75.6 秒)、79dd07742 = 71 passed / 2 skipped (login、77.1 秒)。skip は n10 / n14 (`except*`、Python 3.10)。
- 受入全走: 段 7 の記録 commit 後、land 前に 1 回 (結果は land の受領証と worklog)。

## 裁定パッケージ候補 (scope 外、実装していない)

1. 変換後の例外の外側追跡: s8b_oracle_driver 1660 の `if evaluate_started: raise` を静的に証明する flow 解析 (D1882 が却下した支配関係解析) を認めるか、1788 を繰延べ台帳へ移すか、保証限界のままにするか。
2. MAYBE 型 (Attribute 等) の handler が実際に E を捕まえて bare 再送出する未変換経路 (前提 = E の親 class は組込みだけ、外来名は E の親でない、の下では起きない)。
3. `with` の `__exit__` による抑止、条件 guard (`if enabled:` 内の check)、代入名の再束縛、finalbody 内の check — D1882 の却下範囲 (支配関係・値追跡)。
4. 前提 pin の要否: 「helper の明示的な拒否 raise は base `DriverError`、`class DriverError(RuntimeError)`」を assert で固定するか (D1869 で落とした)。helper の非明示例外の扱い。
5. TryStar 規則の実走検証 (Python 3.11 が要る)。

## 工数

codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、焦点再レビュー 1、全段 `gpt-6-astra`、plan / consult / review は `medium`)。親の実測: repo 外 probe 1 (try 連鎖)、焦点走 2、変異 2 走 (旧 2 run + 新 15 run、計算ノード)、
provenance full 1 本。wave 開始 21:37 JST、fix commit 22:41 JST、変異新走完了 23:33 JST (mtime / ledger の `updated_at` で実測)。
