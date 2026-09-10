# 段 4 裁定 — [T-2228] plan v2 と変異事前登録

裁定時刻: 2026-09-04 (attempt t2228-20260904a は両 job とも RUN 中、24 分経過)

## 1. 実走の中間事実 (親が現物で確認)

- `jobs/rr5/campaigns/.../runs/wal.jsonl` と `jobs/rr50/campaigns/.../runs/wal.jsonl` に `build_start` が各 1 件。
  `_condition_gate_family_context` は全 cell の腕評価・family 判定・receipts 追加を終えてからしか yield しない
  (`paper_story_a2_certification.py:613-697`) ので、**両 workload で cell-1 の腕・admission・receipts・campaign が実体で発火した**。
- したがって condition gate の層 4 は出ていない。production (driver / gate) の変更は **ゼロ** に確定する。
- 各 record の exact reason code と admission payload は job.stdout 末尾 JSON の `condition_gate_receipts` が届いてから読む。
  それまで予測値を実測値として書かない (lens B)。

## 2. 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 裁定 | 採否 |
|---|---|---|---|---|
| A-1 | lens A | 正例は evaluator だけ差し替え、実 family を通す。family 関数は事前に別名保存し、その戻り値を期待値に使う | real (反証なし) | 採用 |
| A-2 | lens A | stub が呼出し順だけで record を返すと `captured` / `requested_value` の引数変異が生存する。全引数の exact assertion が要る | real | **採用 (must)** |
| A-3 | lens A | 手組み green evidence は実 evaluator が拒否する supply を integrity 緑で偽造できる。実 fixture record を使う | real | 採用 |
| A-4 | lens A | 負例は family/wiring の負例であり実 configure 失敗ではない。そう記録する | nit | 採用 (記録の言い方) |
| A-5 | lens A | owner TU の identity は `owner-tu-unresolved` 検査により classifier 到達時には集合内にある | real (限定付き反証なし) | 採用 (記録) |
| A-6 | lens A | compile argv が相対 path なら分類器が発火しない可能性 | real (静的) | **実走で否定**: 両 WAL の build_start = stock cell が admission を通った。記録に残す |
| A-7 | lens A | 層 4 修正案 (exact path pair 追加受理、owner 補完) は受理集合を広げる向き | real | 採用: 層 4 が出なかったので削除。scope 外 |
| A-8 | lens A | (P1) は campaign 失敗時に admission 証拠が残らない | real | 採用: 正例は stdout receipt の保存まで条件にする。台帳追加は scope 外 (命令) |
| A-9 | lens A | (P4) の「admission 未実行」は誤り。cell-0 の family 判定は実行され `admitted=False` を返していた | real | **採用: brief を訂正** |
| A-10 | lens A | rr50 の一次資料が無い | real | 採用: 親が rr50 stderr を読み、同一の拒否行を確認済 |
| A-11 | lens A | 負例 genome を BACKOFF_FIXED 1 件にして単一理由性を保つ | real | 採用 |
| B-1 | lens B | 両 WAL の build_start = 2 層目以降は発火済み、層 4 なし | real | 採用 (1 節) |
| B-2 | lens B | 正例・負例は同じ test 関数に置く (D1522)。production 相当 genome なら evaluator は各 4 回 | real | **採用**: 正例は production 相当 2 genome (BACKOFF_FIXED + BACKOFF_NOINLINE=0)、負例は BF 1 件 |
| B-3 | lens B | WAL の `build_admission` は condition admission ではない | real | 採用 (記録) |
| B-4 | lens B | cell-0 request は `default_value=-1`、`stock_comparison=True` まで照合する | real | 採用 (A-2 と同じ must) |
| B-5 | lens B | 実 record は monkeypatch **前**に生成する (tempfile 差し替えが evaluator にも見える) | real | **採用 (must)** |
| B-6 | lens B | test 時間の見積りは 1〜2 秒程度 | nit | 採用 (親が実測) |
| B-7 | lens B | brief のアンカー `condition_meaning_gate.py:3707-3770` は誤り。family は `:3885-3947` | real | 採用: 訂正 (親実測: `require_condition_gate_family` は 3885 行) |
| B-8 | lens B | 他 3 driver は同じ evaluator の静的 consumer だが driver 固有経路は未実測と明記 | real | 採用 (記録の文言) |
| B-9 | lens B | (P3) は実走結果により不採用、production 修正ゼロ | real | 採用 |
| B-10 | lens B | duration ledger は触らない | nit | 採用 |
| — | 親 | 「漏れれば全て require_heavy_work_site で拒否」は過大 (evaluator は独自 `_run_process`) | nit | 訂正 |

## 3. (P) の確定

- (P1) 採用。正例 = attempt `t2228-20260904a` の stdout receipt (保存まで含む)。campaign 失敗時は「到達の間接証拠」までしか言わない。
- (P2) 採用 (形は B-2 / A-1 / A-2 / B-5 で確定)。
- (P3) 不採用 (層 4 なし)。production 変更ゼロ。
- (P4) 訂正: 「2 層目以降」= 旧 cell-0 拒否より後の制御位置 = cell-1 の両腕、cell-1 の family 判定、全 cell admitted 状態、receipts append、context yield、campaign。cell-0 の family 判定自体は旧経路でも実行されていた。

## 4. plan v2 (実装の確定形、Codex author の正本)

編集 file は `orchestrator/tests/test_paper_story_a2_certification.py` **だけ**。production・他 test・docs・fixture・registry は編集しない。

### 4.1 追加する test 関数 (名前は変異事前登録が束縛する。この名前どおりに作る)

`test_condition_gate_family_real_records_positive_then_issued_red_negative`

置き場所: 既存 `_assert_condition_gate_rejection` の直後 (行 563 付近)、独立した関数として。既存 helper・既存 test は 1 行も変えない。

### 4.2 事前準備 (monkeypatch の **前** に行う。B-5)

1. `orchestrator/tests/condition_gate_test_support.py` と `test_condition_meaning_gate.py` が使う `_SUPPLIED` fixture path・compiler 検出 (`_any_cxx` / `_any_cmake` 相当) を再利用し、
   `G.capture_define_inputs(_SUPPLIED, stock_root=_SUPPLIED / "stock")` で `captured` を作る (`G` = 実体 module `condition_meaning_gate`)。
2. driver と **同じ** request を作る: `driver_id` は exact に `"orchestrator.campaign.paper_story_a2_certification:cell-0"` / `":cell-1"`、
   macro ごとに `make_define_request(driver_id=..., macro=macro, requested_value=value, default_value=defaults[macro], stock_comparison=(macro=="BACKOFF_FIXED" and value==-1))`
   (`paper_story_a2_certification.py:618-629` と同型)。declaration も driver と同型 (`:630-654`)。
3. 実 `G.evaluate_define_supply_effectuation(captured, request=..., cxx=..., cmake=...)` と実 `G.evaluate_define_runtime_meaning(captured, request=..., declaration=..., cxx=..., cmake=...)` を
   cell-0 = `{BACKOFF_FIXED: -1, BACKOFF_NOINLINE: 0}`、cell-1 = `{BACKOFF_FIXED: 10, BACKOFF_NOINLINE: 0}` の 2 genome × 2 macro で事前実行し、record を dict に持つ。
   各 record が exact `G.ConditionArmRecord` で `G._validate_arm_record_integrity(record)` (issuer 必須) を通ることを assert する。
   期待: BF=-1 は supply `stock-inert-preprocess-identical` / meaning green、BF=10 は supply `requested-default-preprocess-different` / meaning green、
   NOINLINE=0 は supply green (inert) / meaning `unestablished` `meaning-witness-undeclared`。現行 fixture が別の green reason を返す場合は
   その実測値を assert し、赤なら fixture 側の前提を報告して止まる (テストを甘くしない)。
4. `real_family = G.require_condition_gate_family` を別名保存し、期待 admission を `real_family(supply_list, meaning_list, use_class="paper")` で **独立に**計算する (A-1)。

### 4.3 正例 (production 相当 2 genome、B-2)

- 差し替える leaf は 7 種だけ: `A2.patchharness.checkout`、`A2.patchharness.applied`、`A2.tempfile.TemporaryDirectory`、
  `A2.buildcache.prepare_masstree_fetchcontent`、`A2.condition_meaning_gate.capture_define_inputs` (事前に作った `captured` を返す)、
  `A2.condition_meaning_gate.evaluate_define_supply_effectuation`、`A2.condition_meaning_gate.evaluate_define_runtime_meaning`。
  `require_condition_gate_family`、`make_define_request`、declaration 構築、`canonical_json` は実体のまま。
- 2 評価関数の stub は **全引数を exact に検査**してから事前 record を返す (A-2 / B-4): `_captured is captured`、`request == 期待 DefineRequest`
  (driver_id・macro・requested_value・default_value・stock_comparison を含む等値)、`cxx`、`cmake` (supply)、`declaration == 期待 declaration` (meaning)。
  合わないなら `AssertionError`。呼出し順 (cell-0 → cell-1、macro は辞書順) と回数 (supply 4、meaning 4、capture 1、checkout 1、applied 1、prebuild 1、TemporaryDirectory 1) を固定する。
- genome は `A2.SimpleNamespace(flags={...})` でよい (driver は `genome.flags` しか見ない)。`BACK_OFF` は defaults に無いので関門対象外。
- context の yield 内で assert: `len(receipts) == 2`、各 receipt の `supply_records` / `meaning_records` が `[json.loads(r.canonical_json()) for r in ...]` と完全一致、
  `admission` が `json.loads(expected_admission.canonical_json())` と完全一致 (`admitted` True、`record_ids` の順序も一致)、`unestablished_meaning_macros == ("BACKOFF_NOINLINE",)`。

### 4.4 負例 (同じ test 関数の後半、D1522)

- genome は `{BACKOFF_FIXED: 10}` の 1 件 (A-11)。request は cell-0 として driver が作るもの (driver_id `:cell-0`) と同型に作り直す。
- supply record は `G._issue_arm_record(arm="supply-effectuation", terminal_status="red", reason_code="configure-failed", request=req, request_digest=G._request_digest(req, companions), evidence={"detail": "cmake emitted an unused-variable warning"})`
  で発行する (`companions` は `G._validate_define_request(req)` の戻り値から取る)。meaning record は BF=10 の実 green record を再利用する。
- 先に `real_family([red], [green], use_class="paper").admitted is False` を直接 assert する。
- 次に driver context を、上と同じ 7 種の差し替え (record だけ差し替え) で回し、`pytest.raises(A2.CertificationError)`。message に
  `BACKOFF_FIXED:supply-effectuation:configure-failed:detail='cmake emitted an unused-variable warning'` を含むこと、meaning 側 (green) は列挙されないことを assert する。
  負例側も各 leaf の呼出し回数を固定する (supply 1、meaning 1、capture 1)。
- これは **family / wiring の負例**であり実 configure 失敗の再現ではない (A-4)。docstring にそう書く。

### 4.5 触れないもの

`test_paper_story_a2_certification.py` の既存 pin (行 62-90、3242-3258) と既存 helper / test の期待値。`acceptance_duration_ledger.json`。production 全般。

## 5. 変異事前登録 (DW-M01 / DW-M08)

production は変更しないため、本 wave は「テスト強化だけの wave」。DW-M08 に従い、各変異を **新テストあり (本 branch)** と **変更前 HEAD (main 396dc8988 の test file)** の両方へ走らせ、新テストだけが検出する差分を示す。
kill の期待 node は `orchestrator/tests/test_paper_story_a2_certification.py::test_condition_gate_family_real_records_positive_then_issued_red_negative` (完全集合、単一 node)。
旧 HEAD 版では全変異 SURVIVED を期待する (既存テストは関門 4 関数を stub するため)。

| ID | 位置 | 変異 | 落とす assertion |
|---|---|---|---|
| M1 | `condition_meaning_gate.py` 約 3921 `supply_green = all(record.terminal_status == "green" ...)` | `== "green"` → `in {"green", "red"}` | 負例の直接 `admitted is False` と driver の `pytest.raises` |
| M2 | `paper_story_a2_certification.py` 約 670-672 `use_class="paper"` | `"paper"` → `"raw"` | 正例の admission canonical JSON 完全一致 (期待は `use_class="paper"` で独立計算) |
| M3 | `paper_story_a2_certification.py` 約 686-696 receipts dict | `"admission": json.loads(admission.canonical_json())` を削る | 正例の receipt 完全一致 |
| M4 | `paper_story_a2_certification.py` 約 675-680 message | `f"detail={record.evidence.get('detail')!r}"` を削る | 負例の exact substring |
| M5 | `paper_story_a2_certification.py` 約 616 `for macro in sorted(set(genome.flags) & set(defaults))` | 末尾に `[:1]` | 正例の evaluator 回数 (4→2) と record 数 |
| M6 | `paper_story_a2_certification.py` 約 624 `requested_value=value` | `requested_value=defaults[macro]` | 正例 stub の exact request assertion |
| M7 | `paper_story_a2_certification.py` 約 614 `enumerate(genomes)` | `enumerate(genomes[:1])` | 正例の `len(receipts) == 2` |

単一理由性は実装後に各変異の赤理由が 1 つに絞れるか確認し、絞れなければ登録から外して再照準する (F820)。
M1 は gate 本体の変異であり、受理集合が広がる向き = kill は fail-closed の保持を意味する。

## 6. gate の禁止 (署名) と通る正例

**禁止**: `_condition_gate_family_context` が、実体の `require_condition_gate_family` が `admitted=False` を返す record 集合に対して `receipts` を作り yield すること。
および、実体 family へ渡す record が、driver がその場で作った request (driver_id・macro・値・default・stock_comparison) と captured tree に対する評価結果でないこと。

**通る正例**: production 相当 2 genome (BF=-1 / BF=10、NOINLINE=0) に対する実 fixture record 4 対で、実体 family が admitted=True を返し、receipts 2 件に record と admission の canonical JSON が入る。

## 5a. 段 6 review A による変異登録の erratum (2026-09-04、fix 前)

review A (正しさ境界と検出力) は実装の実体通過・引数 exact 検査・負例の非恒真性に反証なし。must-fix 4 件はすべて
「M2 / M4 / M5 / M7 は既存テストでも落ちるため、DW-M08 の『新テストだけが検出する差分』にならない」という
**変異登録の不備**であり、コードの fix は不要。DW-M01 (実効 gate へ再照準) と DW-M03 (冗長 gate の明記) で次のとおり改める。

| ID | 旧 | 新 | 落とす assertion (新テスト) | 旧 HEAD の期待 |
|---|---|---|---|---|
| M1 | 同じ | 同じ | 負例の直接 `negative_admission.admitted is False` (driver の `pytest.raises` には到達しない。kill point を 1 つへ訂正) | SURVIVED (既存は family を stub) |
| M2 | `use_class="raw"` (既存 source pin が捕まえる) | receipts の `"meaning_records"` を空 list にする | 正例の receipt 完全一致 | SURVIVED (既存は `len(receipts)` だけ) |
| M3 | 同じ | 同じ | 正例の receipt 完全一致 | SURVIVED |
| M4 | detail を落とす (既存負例が捕まえる) | 拒否 message に green record も列挙する (`if True or ...`) | 負例の `"BACKOFF_FIXED:runtime-meaning:" not in message` | SURVIVED (既存は substring の存在だけ) |
| M5 | macro を 1 つに絞る (既存負例が NOINLINE 欠落で捕まえる) | macro の辞書順を逆にする (`reverse=True`) | 正例 stub の exact request assertion (期待行の順が BF → NOINLINE) | SURVIVED |
| M6 | 同じ | 同じ | 正例 stub の exact request assertion (cell-1 の driver_id) | 未確定 (probe で観測) |
| M7 | 同じ | 同じ (冗長 gate と明記) | 正例の `len(receipts) == 2` | KILLED by 既存 `test_condition_gate_prebuild_runs_once_for_multiple_cells` (`len(receipts) == len(genomes)`)。新規検出力としては数えない |

旧 HEAD 版 (main 396dc8988 の test file) の走行は、attempt `t2228-20260904a` が投入元 tree を使い終えた後に、同 tree (`submit-tree`) で行う (走行中の job が import する tree を変異させない)。
review A の nit (compiler 不在時の skip): 親の node 指定走 (request 976244.nqsv) で当該 node が PASSED と明示されており、SKIP ではない。

## 7. scope 外 (裁定パッケージ候補ではなく、記録のみ)

- receipts の campaign 前保存 (admission 証拠の耐障害性)。命令が禁じる仮想リスク向けの台帳追加。既存境界として insight に書く。
- 他 3 driver の driver 固有経路の実測 (同じ evaluator の静的 consumer であることだけ記録)。
- 分類器の exact path pair 受理・owner 補完 (層 4 が出なかったので不要。出ていれば受理集合を広げる向きなので裁定へ返す形だった)。
