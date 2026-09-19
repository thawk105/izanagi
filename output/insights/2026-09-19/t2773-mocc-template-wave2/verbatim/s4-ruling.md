# [T-2773] 段 4 裁定 — plan v2 と変異事前登録 (2026-09-19 22:35 JST)

前提: 段 2 plan (`s2-plan.md`、check OK)、段 3 レンズ A (`s3-lensA.md`、must-fix 1 / should 5 / nit 1、refuted 4)、レンズ B (`s3-lensB.md`、must-fix 1 / should 5 / nit 3)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: wave 開始 (21:44) 以降の更新 4 件はいずれも T-2773 / mocc に無関係。local main は `657e1e5a7` のまま。plan と食い違う場合は本裁定が勝つ。

## 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | レンズ A must-fix | 計装 template 版の「本文保存」が機械 check に無い。X 条件恒偽化・P emit 無効化・検査点の移動が TRACE=0 同一性・正常系沈黙・sha 束縛のどれにも捕まらない | **real** (D2134 項 3 の経路共通証拠を新計装へ移すには橋が要る。放置すると機械証拠の意味が変わる) | **採用 → R1** |
| A2 | レンズ A should | DQ は物理行の封じ込めだけで純粋性・一式性・停止性を保証しない (9 形が DQ pass) | real | 採用 → R3 (文章契約と auditor 型 16、n=1 の A2' が同型) |
| A3 | レンズ A | P3 の型・brace・fallback に反例なし | refuted (must-fix 候補棄却) | 記録のみ |
| A4 | レンズ A | 三比較の分離と `#line` 復元値は妥当。保証名の限定 | refuted (+ should の限定は real) | 採用 → R4 |
| A5 | レンズ A should | P1 は妥当だが 12 走は hot 負例発火の証拠ではない | real (限定) | 採用 → R5 |
| A6 | レンズ A should | 全 12 走に `_silent` + 終了状態検査の両方 | real (実装条件) | 採用 → R6 |
| A7 | レンズ A should | auditor 射影に実効 macro context を明記、verify 射影は allowlist field で新規生成 | real | 採用 → R7 (R2 と統合) |
| A8 | レンズ A | auditor 追記の行番号・Silo 保持は整合 | refuted | 記録のみ |
| A9 | レンズ A should/nit | P5/P6 の限定は妥当。plan の「親 P4 七 hunk」引用は brief に無い | real (引用誤り) | 採用 → R12 |
| B1 | レンズ B must-fix | auditor-live 機械要件 (設計 §10 (1)) の read-only 契約・入力射影の構造検査が JSON / consumer 要件に無い | **real** (D2134 項 6 (1) の機械要件。既存 `spec.py` の tools 契約を接続すれば足り、新機構は不要) | **採用 → R2** |
| B2 | レンズ B should | sha 鎖と旧 check 成立の検査を分ける (参照先を開いて 32 / 14 check の成立を確認) | real | 採用 → R8 |
| B3 | レンズ B should | auditor 検査は型番号 / チェックリスト番号の境界で項目別に固定記述を要求、削除・移動を拒否対照 | real | 採用 → R9 |
| B4 | レンズ B nit | pin 3 箇所と semantic_digest は閉じている | refuted | 記録のみ (renderer 出力全体を採用) |
| B5 | レンズ B should | pin 閉包の新たな漏れなし。軸 SOURCE_REL 表への追記は実施対象 | real (実施対象化) | 採用 → R10 |
| B6 | レンズ B should | P5 は束縛 API と対照の実証で、実 consumer の接続実証ではない | real (限定) | 採用 → R16 |
| B7 | レンズ B nit | cache route は mocc owner で評価可 | refuted | 記録のみ (R14) |
| B8 | レンズ B should | 時間は計画値、生死確認 build 数と compute build 数を区別 | real | 採用 → R11 |
| B9 | レンズ B nit | 親 brief の「12 file に pin」は短縮 sha で 15 file、種別を付す | real | 採用 → R12 |

refuted のうち不採用にした所見: なし (refuted は「反例なし」の確認であり、いずれも plan の記述を保つ)。

## 裁定 R1〜R21 (plan v2)

- **R1 (A1、must-fix): 計装 template 版の本文保存を機械 check にする。** 新 driver に `instrumentation_body_preserved` check を置く。入力 = 旧 `patches/instr-mocc-lock-coverage.patch` と新 `patches/instr-mocc-lock-coverage-temperature.patch` の bytes (どちらも実 file から読む)。述語 = (a) 両 patch の `+` 行 (`+++` header と `+#line <n>` 行を除く) の**列**が byte 一致、(b) hunk ごとに「最初の `+` 行の直前の context 行」と「最後の `+` 行の直後の context 行」が旧新で一致 (検査点が対象操作の前後で動いていない)、(c) 新 patch の `#line` 値の列 = 旧 patch の `#line` 値の列 + offset 列で、offset は template 適用後 source の実測 (helper 挿入行数と各 site の増分を、template 適用後の source から `git diff` 相当で数える) から導出し、定数表をコードに焼き込まない。(a)(b)(c) のどれかが崩れたら false。test 側の拒否対照 = X 入口検査を `if (false && …)` に恒偽化した合成 patch → (a) 不一致、P emit の条件を無効化 → (a) 不一致、publish 前検査を `__atomic_store_n` の後へ移動 → (b) 不一致、`#line` を 1 ずらす → (c) 不一致。broken 4 patch の template 上での再走は追加しない (D2134 項 3)。JSON `instrumentation_preservation` に両 sha・比較結果・offset 列を記録する。
- **R2 (B1、must-fix): `auditor_definition` に read-only 契約と入力射影の構造を接続する。** driver は `orchestrator.codex_roles.spec.load_role_specs(root)["auditor"]` (または同等の既存 loader) から tools を取り、`("Read", "Grep", "Glob")` と exact 一致・`Bash`/`Edit`/`Write` 不在を記録する。入力射影は軸 module の 1 関数 `auditor_projection(run_record)` とし、**正しさの形だけ** (verdict、certified、total_cycles、X / P の総数と reason、integrity の各 key) を allowlist で写し、時間・性能・作業量 (`wall_seconds`、throughput、`txns`、`non_insert_writes`、`read_rows`、fitness、WAL、期待 verdict) を含む入力は fail-closed で拒否する (unknown key も拒否)。check 名 = `auditor_definition_read_only_and_projection` (tools 一致 ∧ 射影関数が 12 走の run record すべてを受理 ∧ 拒否対照 (性能 field 混入) が例外)。test 側拒否対照 = tools に `Bash` を足した合成 spec → false、`wall_seconds` を含む record → 例外。n=1 の応答・file 存在で代用しない。
- **R3 (A2): 読取契約の文章化。** 軸 module の `SYNTAX_CONTRACT_FORBIDDEN` は禁止例の列挙であって完全な blacklist ではないと docstring に明記し、auditor.md 型 16 の mocc 追記に「DQ pass は物理行の封じ込めを示すだけで、一式性・純粋性・停止性・読取契約の充足を示さない。列挙にない global、lambda / static、再帰、組込関数、通常式中の TRACE 参照も許可集合 (値渡しの temp / threshold と bool / 整数定数の比較・論理結合) から外れるものとして監査する」を入れる。n=1 の A2' (`FLAGS_clocks_per_us`) はこの型の代表例として reject を期待する (期待値は子に渡さない)。
- **R4 (A4): 保証名の限定。** 比較 (i) の保証名 = 「実 resolver (`source_digest`) が定める正規化前処理 source identity の stock 一致」。比較 (iii) の基準列は実 template 適用 source から独立に前処理して取得し、計装側の復元番号表から生成しない。(iii) は TRACE=1 検査本文の有効性を保証しない (それは R1 が担う)。JSON `identity.*` / `trace0.*` の `claim` 文字列をこの形に固定する。
- **R5 (A5): 12 走の位置づけ。** template ON-B の stock 12 走は正常系対照 (certified & silent) であり、template 上で hot-update 負例が発火したことを主張しない。`hot_path_evidence` は wave 1 JSON の path / sha への参照 (`method = "reference-wave1-negative-control"`) とし、新しい保証名を足さない。4 site 全動的被覆・read-hot・RLL 再試行・DELETE は主張しない。
- **R6 (A6): 全 12 走に `_silent` 相当の内容検査 + benchmark / verifier の終了状態検査を必須。** timeout・異常 rc・verifier record 欠落・txn / write ゼロ・別 integrity 異常は `all_pass=False`。wave 1 の観測専用負例に対する免除は継承しない。
- **R7 (A7): auditor 射影の内容。** 射影 (n=1 用も機械用も同じ関数) には候補ごとの base / source / diff digest、実効 macro context (`MOCC_TEMP_PREDICATE`、`TRACE`、`RWLOCK`、`TEMPERATURE_RESET_OPT`、`KEY_SORT`)、R2 の allowlist field だけを含める。B' へ実走結果を帰属させる前に base + B' の source sha と実走 source sha の一致を確認する。
- **R8 (B2): sha 鎖と check 成立の分離。** `wave1_proof` = path / sha256 と、実際に開いて `all_pass is True` かつ 32 check key が揃いすべて `True` であること。`legacy_proof` = T-2294 JSON の path / sha256 と 14 check の同様の確認。check 名 = `wave1_proof_bound_and_all_pass`、`legacy_proof_bound_and_all_pass`。旧 JSON に新 field は要求しない。
- **R9 (B3): auditor.md の項目別検査。** 軸 module (または driver) が `AUDITOR_MOCC_REQUIRED = {("gallery", 8): "<固定文>", ("gallery", 9): …, ("gallery", 13): …, ("gallery", 16): …, ("checklist", 11): …, ("checklist", 12): …, ("checklist", 13): …}` を持つ (期待文は plan §8 の追記文から各 1 文を抜いた固定 literal、検査対象 file から生成しない)。検査 = auditor.md を「## CC 版 reward hack ギャラリー」節の番号付き項目と「## 何を見るか」節の番号付き項目に分割し、各期待文が**当該番号の項目内**にあること。全文 `"mocc"` 検索や項目境界を無視した一致は不合格。拒否対照 = 追記 1 件の削除、別項目への移動。
- **R10 (B5): `test_campaign.py::test_axis_driver_source_rel_within_edit_surface` の期待表へ `(axis_mocc_temperature, "cc/mocc/transaction.cc")` を追加する (実施対象)。** `p3_s4_loop` から新 module を import しない。B-4 module 数・duration ledger は機械的に更新しない。
- **R11 (B8): 時間と build 数。** compute = build 5 本 (ON-B t1 計装あり / ON-B t0 計装なし / ON-B t0 計装あり / OFF t0 計装なし / 無 template t0) + condition gate + identity + 12 走、job 枠 3600 秒、計画値 600〜1200 秒 (未実測)。login 生死確認は author が用意する資材で必要な組合せ (OFF t0 / ON-seed t1 -Werror / ON-B t0 / ON-B t1 計装あり / ON-B t0 計装あり、旧計装 patch の `git apply --check` rc≠0、新計装版 rc=0、marker parse、DQ 全対照、identity (i)(ii)、論理行列 (iii)) に絞る。benchmark は login で走らせない。
- **R12 (A9 / B9): 親 brief の訂正 (記録)。** (a) 旧計装 sha の出現は HEAD 657e1e5a7 で完全 sha 12 file / 短縮 sha 15 file、うち機械 pin (test / registry / JSON consumer) と歴史記録 (insight README / receipt / log) を区別する — 結論 (旧 bytes 不変) は同じ。(b) 「直書き PIN → 拒否」は表記形式の禁止ではなく**別 OID・別実 source との不一致の拒否**と読む。正しい OID の literal は拒否しない。(c) plan §14 項 1 の「親 P4 の七 hunk を訂正」は brief に無い引用であり、事実は「計装版は 6 hunk・7 復元点」。(d) 任意の直書き経路の閉鎖・全 consumer 経路の閉鎖は主張しない (D2134 項 6)。
- **R13: helper 名 = `mocc_is_hot`** (anonymous namespace、`inline`、`std::uint64_t` 二引数)。`izanagi` を含む名前にしない (`_trace0_record` の nm 計数と混ざる)。hole = `  return temp >= threshold;` の 1 行、B = `  return !(temp < threshold);`。骨格・4 site・Options.cmake 2 hunk は plan §1 の逐語。`IZANAGI_` トークンを template に入れない。
- **R14: condition gate。** `MOCC_TEMP_PREDICATE` は `DefineSpec(ROUTE_CMAKE_CACHE, _MOCC_OWNER, "ycsb_mocc.exe", "patches/mocc-temperature-predicate-variant.patch", inert_values=("0",))`。一意 witness = 外側 guard の comment 付き行 `#if MOCC_TEMP_PREDICATE // file-scope helper` (source 内で完全一致 1 行)。`RELATED_DEFINE_DECODE_MACROS` へ追加。`condition_gate_test_support.py` の `_OPTIONS` に CACHE 行と universal mapping 行を追加。件数 pin は現物を数えて確定 (plan §9 の予測 39→40 / 15→16 / cache 22→23 / Counter 35→36・39→40・25→26・25→26 は実走で確認し、違えば現物に合わせて報告)。実行失敗時に CXX_FLAGS 経路や meaning 省略で緑にしない。
- **R15: PIN の分離。** 軸 module に `PIN = pin.CURRENT_PIN` (探索用、不変) と `PROOF_PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"` (proof 用、full OID) を別定数で置き、新 driver・束縛関数は `PROOF_PIN` を使う。探索用 PIN を e9e477ca へ変えない。
- **R16 (B6): consumer 束縛。** `axis_mocc_temperature.require_proof_binding(proof, *, repo_root, source_rel, template_patch, ccbench_commit, instrumentation_patch)` は束縛 (schema / source / marker / flag / template の repo 相対 path と実 sha / OID / 計装版 path と実 sha / touch set) だけを検査し、`all_pass` は要求しない (循環回避)。`all_pass` の要求は gate test / JSON consumer が行う。3 対照 = 同 bytes の別名・別配置 template → `MoccProofBindingError`、正しい値の literal → 通過 (かつ鍵 (a) が発火)、別 OID の literal → 拒否。JSON `consumer_binding_controls` に 3 対照の実結果を記録し、期待はコード側で固定。実 consumer 導入時の実 checkout 束縛検査は別途 (主張しない)。
- **R17: gate test。** `test_mocc_mutation_surface_requires_auditor_live` の鍵 (a) = `patches/*.patch` の走査で `cc/mocc/transaction.cc` を対象とする hunk の `+` 行に `EVOLVE-BLOCK-BEGIN` が加わる patch の存在 (plan §7 の判定 code)、鍵 (b) = `orchestrator/campaign/axis_*.py` の import で `SOURCE_REL == "cc/mocc/transaction.cc"` かつ `MARKER_ID` と `TEMPLATE_PATCH` を持つ module の存在 (import 失敗は赤)。どちらかで発火し、新 JSON の実在・schema・`all_pass`・全 check True・`compute_checks` 再導出一致・template / 計装 / wave 1 / T-2294 の sha 鎖 (R8)・束縛関数の通過 (R16)・auditor 定義 (R2 / R9)・condition gate の新 driver ID と mocc owner・12 走の集合と終了状態を要求する。負例 = template のみ / 軸 module のみ / 両方 / trace-hook のみ (現 main 状態) の 4 ケースを合成入力で固定 (`test_mocc_template_gate_activation_controls`)。既存 Silo gate (`test_campaign.py:11397`) は変えない。JSON 不在は赤 (skip にしない)。compute 前に親が `--deselect` する node = `test_mocc_mutation_surface_requires_auditor_live`、`test_mocc_template_proof_json_is_complete_and_bound` の 2 つだけ。
- **R18: DQ 対照。** plan §5 の 13 対照 (benign 受理 / stock-frame → frame-altered / fallback・CLL・RLL・validation・X・P・write 登録 477・RLL write 登録 905〜913 → outside-region / directive・comment・splice → hole-escape / bad-anchor → malformed)。diff は実適用 source の対象 1 行を編集して `difflib.unified_diff` で生成、編集位置は一意一致を assert、`marker.source_rel = SOURCE_REL` を明示。X / P 対照は template + 新計装版を head_text にし marker を再 parse。deny-only 対照 4 種 (plan §5 末尾)。compute で JSON `quarantine_controls` に実結果を記録し、pytest は独立期待で照合する。
- **R19: JSON top-level** = plan §4 の列 + `instrumentation_preservation` (R1)。`auditor_definition` は R2 / R9 の内容。`hot_path_evidence` は R5。`n1_*` は置かない。schema `s3-mocc-template-proof/v1`。
- **R20: 段 5 の分割 = author 1 本 (wave worktree 内)。** author 所有 = 新 patch 2 本、軸 module、新 driver、新 test、`.claude/agents/auditor.md` + pin 3 箇所 (`review_ledger.py` / `.codex/role-adapters/auditor.json` / `test_reflux_originless_compatibility.py`)、登録簿・fixture 追随 (`condition_meaning_gate.py`、`condition_gate_test_support.py`、`test_condition_meaning_gate.py`、`materializer_admission.py`、`test_p3_build_authority_cli.py`、`test_ccbench_spawn_sites.py`、`screening_driver.py`、`test_campaign.py` の期待表 1 行)、生死確認用の実装資材 (job dir に置く script)。親所有 = `patches/README.md`、insight、fragments、統合 commit、compute 投入、n=1、記録。旧 driver 2 本・旧 test・旧 patch 5 本・旧 JSON 2 本・`orchestrator/verifier/**`・`patches/ledger.json`・`tools/**`・`conftest.py`・`patchharness.py`・Silo gate は不変。
- **R21: 完了判定 (再掲・限定)。** template に束縛された機械証拠 = 新 JSON の `all_pass` (同一性 3 比較・DQ 対照・consumer 束縛対照・auditor 定義・計装保存・12 走 certified & silent・sha 鎖・condition gate) と、別記の n=1 素材 3 候補。緑でも探索・pin 前進・正式な軸採用は認可しない (D2134 項 9)。

## 変異事前登録 (DW-M01、段 6 で実行。期待 killer node は実装後の login probe で固定し、結果を見てから期待を変えない)

| ID | 対象 / 内容 | 期待 | 主な検査 (候補) |
|---|---|---|---|
| M0 | 新 driver の非契約 comment を等価変更 | SURVIVED | harness の生存対照 |
| M1 | template の stock 枝 (`#else` 側) `>=` → `>` | KILLED | frozen frame / OFF identity |
| M2 | template の site 566 だけ ON 側を旧比較に戻す | KILLED | 4 site 構造契約 |
| M3 | 新計装 template 版の `#line 1204` → `1205` | KILLED | 論理行列 (iii) / R1 (c) |
| M4 | template の helper 外側 guard (`#if MOCC_TEMP_PREDICATE // file-scope helper` … `#endif`) を削除 | KILLED | OFF 前処理本文 / witness |
| M5 | 軸 module の `MARKER_ID` を別名へ | KILLED | 実 marker / frozen bytes 照合 |
| M6 | 束縛関数の template sha 検査を削除 | KILLED | 別名 template 対照 |
| M7 | gate test の鍵 (a) を常に False | KILLED | template のみ対照 |
| M8 | DQ 対照の subtype 不一致を許容 | KILLED | 独立期待 subtype 表 |
| M9 | auditor.md 型 16 の mocc 追記を削除 | KILLED | R9 項目別検査 / sha 束縛 |
| M10 | JSON の template sha を 1 文字変更 | KILLED | JSON consumer |
| M11 | JSON の `all_pass` を false | KILLED | JSON consumer |
| M12a | `condition_meaning_gate` の新 DefineSpec entry を削除 | KILLED | registry 閉包 |
| M12b | `materializer_admission` の新 entry を削除 | KILLED | materializer 閉包 |
| M13 | ON-B 別 identity check を定数 True 化 | KILLED | 入力由来 check 対照 |
| M14 | 新計装 template 版の X 入口検査を `if (false && …)` に恒偽化 (patch bytes) | KILLED | R1 (a) `instrumentation_body_preserved` |
| M15 | `auditor_projection` の allowlist に `wall_seconds` を追加 | KILLED | R2 拒否対照 |

M10 / M11 は JSON commit 後に追加する (wave 1 と同じ)。M12a / M12b は別々に走らせる。sha 不一致だけの赤は検出力として重複計上しない。
