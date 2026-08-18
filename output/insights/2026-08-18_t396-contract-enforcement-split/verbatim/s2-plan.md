必読 2 枚はともに全文を読めた。現行 `a160f4aa` を静的に追検証し、dev-wave の DW-S02、DW-M01 に沿って計画化した。結論は、P1 は「5 種の残余がある」という意味では成立するが全項目が完全未執行という読みは不正確、P2 は支持、P3 は前例部分のみ支持である。以下はすべて静的調査で、テストは未実走である。

## 1. 執行状況の対応表

### 実 caller 閉包

現行 sort 軸は次の順で proposal を処理する。

`load_proposal_file` (`orchestrator/campaign/p3_s4_loop_sort.py:349-380`)  
→ `drive_iteration` (`:383-439`)  
→ `run_one_iteration` (`:418-421`, 本体 `:289-344`)  
→ template 適用 (`:321`)  
→ `_quarantine_and_audit` (`:145-238`)  
→ `L.quarantine` (`:155-156`)  
→ `DiffQuarantine.validate()` (`orchestrator/campaign/p3_s4_loop.py:229-245`)  
→ `scan_host_effects()` (`:245-274`)  
→ auditor deny-only veto (`p3_s4_loop_sort.py:157-163`)  
→ sort SWO oracle (`:165-223`)  
→ `run_campaign` (`:328-332`)  
→ `evaluate` の source identity / build admission (`pipeline.py:789-831`)  
→ build (`:896-947`)  
→ post-campaign artifact admission (`p3_s4_loop_sort.py:424-427`)。

親 brief `s1-brief.md:53-57` が明示していなかったものは次の 3 点である。

- `assert_closed_proposal_schema` (`p3_s4_loop_sort.py:364-366`)。ただし `implementation` を opaque string として受ける形状 gate で、C++ 意味 gate ではない。
- `source_digest.resolve_evidence` と build admission (`pipeline.py:792-827`)。前者は identity と include 集合、後者は provenance を検査する。
- `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` (`p3_s4_loop_sort.py:424-427`)。現行 main の post-campaign gate だが、C++ closed-region 意味検査ではない。

いずれも以下の残余分類を閉じない。

### 「gate が無い」と結論する前の全 gate 否定

| gate | 現行の検査内容 | closed-region 残余を閉じない理由 |
|---|---|---|
| hook | designated source への書込面のみ。内容は検査しない (`hooks/README.md:132-158`) | sort proposal の C++ 意味を見ない。agent 自身も tools なし (`coder-v4-autonomous-sort.md:23-26`) |
| proposal structural/schema | closed JSON schema、`implementation: str` (`p3_s4_loop_sort.py:118-127,349-380`) | C++ 本文は opaque |
| diff quarantine | file/hole containment (`diff_quarantine.py:443-488`) と directive/comment/backslash byte gate (`:491-522`) | 型、呼出意味、有限 loop、latent throw は解析しない (`:14-23`) |
| effect gate | 5 個の identifier deny 規則、malformed、明示的無条件 loop (`coder_effect_gate.py:58-120,527-562`) | 実装自身が有限 blacklist と残余を明記 (`:9-18`) |
| auditor gate | verdict、schema、diff digest を照合し、reject/uncertain のみ狭める (`auditor_gate.py:190-231`) | machine 自身は C++ 意味を判定しない。auditor prompt は正しさ違反を reject する (`auditor.md:32-36`) が、その返答を肯定的安全証明には使わない |
| SWO structural gate | 単一の非修飾 `sort(...)` 文 (`sort_swo_oracle.py:486-548`) | comparator 式内部の宣言・制御・call は解析しない |
| SWO runtime oracle | 有限 corpus の relation、corpus mutation、発火例外、CPU 制限 (`sort_swo_oracle.py:720-803,1020-1099,1221-1262`) | 任意入力への証明ではなく有限反例探索。`ORACLE_CONTRACT_ID` は `:1332-1339` |
| source identity | preprocess identity、include HEAD 一致 (`source_digest.py:669-688,894-906`) | `__DATE__` 等は identity churn になるだけで拒否ではない (`:23-24`)。call/loop/throw の意味は見ない |
| build admission | provenance receipt。sort 固有 C++ 意味検査なし (`build_admission.py:615-675,678-764`) | raw-byte 特別検査は trigger 軸のみ (`:170-219`) |
| compiler/build/verifier | valid C++、実 workload で観測した正しさ | valid な残余を policy 違反として拒否する rule ID はない。偶発的な compile/runtime failure は完全執行ではない |
| artifact admission | campaign admission と verifier epoch (`artifact_admission.py:1077-1103`) | build 後の成果物 view gate であり、source 意味 gate ではない |

### 現行 5 bullet の分類

| 現行 bullet / 部分集合 | 判定 | 機械が拒否する形 | 素通りする残余 | 根拠と規則 ID |
|---|---|---|---|---|
| 1. ヘッダ、型/関数、マクロ、グローバル追加 | **bullet 全体は部分執行** | hole 外の追加、hole 内 directive、単一 `sort` 文の外側への追加 | comparator 式内部の local class、nested lambda、補助 callable | containment は `DiffRejectSubtype.FRAME_ALTERED/OUTSIDE_REGION` (`diff_quarantine.py:41-48,443-488`)。directive は `HOLE_ESCAPE/content-directive` (`:73-77,491-496`)。単一文は `ORACLE_CONTRACT_ID/not-a-single-sort-statement` (`sort_swo_oracle.py:486-548`)。型/補助 callable の semantic rule ID は**ない** |
| 1a. 新しいヘッダ | **完全** | hole 内 `#include`、hole 外 include 追加 | なし | `HOLE_ESCAPE/content-directive`; include HEAD 固定は `source_digest.assert_includes_match_head`、独立 rule ID なし (`source_digest.py:669-688`)。既存 fixture は `test_diff_quarantine.py:252-278` |
| 1b. マクロ | **完全** | `#define` 等の生 directive | なし | `HOLE_ESCAPE/content-directive`; `%:` も検査 (`diff_quarantine.py:51-55`; fixture `test_diff_quarantine.py:263-297`) |
| 1c. グローバル変数 | **完全** | hole は `TxExecutor::validationPhase()` 内 (`patches/silo-sort-variant.patch:34-63`) かつ outer 単一文。namespace/global 定義には到達できない | local/static local は「global 追加」ではない。別途 nondeterminism の有限観測対象 | `FRAME_ALTERED/OUTSIDE_REGION`、`ORACLE_CONTRACT_ID/not-a-single-sort-statement` |
| 1d. 型/関数 | **部分執行** | outer 文の外に置く追加 | comparator 式内部の valid な local class、nested lambda、member callable | oracle は raw candidate TU を compile するだけ (`sort_swo_oracle.py:1529-1539`)。有効 C++ を禁止する semantic rule ID は**ない**。該当する完成 fixture も**ない** |
| 2. 生の前処理指令 | **完全** | 行頭空白後の `#`、`%:`、`??=` | なし | `DiffRejectSubtype.HOLE_ESCAPE/content-directive` (`diff_quarantine.py:51-55,491-496`)。effect gate が benign directive を通して structural gate に委ねることも test 済み (`test_coder_effect_gate.py:146-149`) |
| 3. `//`、`/*`、行末 backslash | **完全** | literal/raw string 内を含む byte 一致、物理行末 backslash | なし | `HOLE_ESCAPE/content-comment-line`、`content-comment-block`、`content-line-splice` (`diff_quarantine.py:62-79,503-522`)。fixtures は `test_diff_quarantine.py:300-339` |
| 4. 非決定ビルトイン | **部分執行** | finite corpus で relation が同一 process 内または process/order 間で変わる形 | 有限 6 観測で relation が安定した時刻・乱数・状態依存 | `ORACLE_CONTRACT_ID/relation-varies-within-process` (`sort_swo_oracle.py:1083-1097`) と `relation-varies-across-process-order` (`:1234-1252`)。fixtures は `test_sort_swo_oracle.py:47-49,224-235,1090-1119`。effect `DENY_TABLE` に time/random rule はない (`coder_effect_gate.py:58-105`) |
| 5a. 既存 silo API のみ、副作用 call 禁止 | **部分執行** | 列挙 identifier と、finite corpus の bytes を変える comparator | 列挙外で corpus/relation を変えない call。API allowlist 自体はない | `host-effect.process-shell.v1`、`file-stdio.v1`、`network.v1`、`sleep-block-thread.v1`、`escape-hatch.v1` (`coder_effect_gate.py:58-105`) と `ORACLE_CONTRACT_ID/corpus-mutated-by-comparator` (`sort_swo_oracle.py:1073-1082`)。fixtures は `test_coder_effect_gate.py:25-29,67-88`、`test_sort_swo_oracle.py:213-221` |
| 5b. straight-line / loop 禁止 | **部分執行** | literal-true `while`、condition 空または literal-true の ordinary `for`、CPU 制限超過 | bounded / range-for / data-dependent loop が有限上限内に完了する形 | `host-effect.unconditional-loop.v1` (`coder_effect_gate.py:108,527-562`) と `ORACLE_CONTRACT_ID/candidate-run-cpu-limit-exceeded` (`sort_swo_oracle.py:1042-1048`)。拒否 fixtures は `test_coder_effect_gate.py:165-193`。現在通る形は `:154-159` |
| 5c. 例外送出禁止 | **部分執行** | finite corpus の comparator 呼出中に実際に発火した例外 | corpus で発火しない条件付き throw | harness catch は `sort_swo_oracle.py:775-794`、拒否は `ORACLE_CONTRACT_ID/candidate-comparator-threw` (`:1051-1061`)。candidate throw の専用 fixture は**ない** |

したがって insight §7 の 5 残余クラス (`t396-insight.md:106-121`) は現行 main にも残る。ただし「機械は一切見ていない」をクラス全体に適用するのは不正確で、非決定性、副作用、loop、throw は有限部分集合が機械執行されている。P1 の結論は支持するが、分類粒度はこの表へ補正すべきである。

## 2. A の置換テキスト案

### 現行 bytes

`.claude/agents/coder-v4-autonomous-sort.md:84-89` の現行 LF bytes は次のとおり。

```markdown
**Closed-region 制約 (D23 道Y、hook が機械執行する部分と auditor が目視する部分の併用):**
- 新しいヘッダ取り込み・型/関数/マクロ/グローバル変数の追加は禁止
- 生の前処理指令 (`#if`/`#ifdef`/`#define`/`#include` 等) は禁止
- `implementation` 内では `//`・`/*`・行末 backslash `\` を禁止する (文字列リテラル・raw string 内も禁止)。説明文はコード内に埋めず `justification` フィールドへ書く
- 非決定ビルトイン (現在時刻・乱数等) は禁止
- 既存 silo API を呼ぶ straight-line code のみ (副作用のある呼び出し・ループ・例外送出は不可)
```

### 置換後の全文

```markdown
**Closed-region 制約 (D23 道Y、機械執行と auditor 目視の併用):**

**機械執行される項目:**
- 新しいヘッダ取り込み・マクロ・グローバル変数の追加は禁止
- 生の前処理指令 (`#if`/`#ifdef`/`#define`/`#include` 等) は禁止
- `implementation` 内では `//`・`/*`・行末 backslash `\` を禁止する (文字列リテラル・raw string 内も禁止)。説明文はコード内に埋めず `justification` フィールドへ書く
- `implementation` は単一の非修飾 `sort(...)` 文に限る。有限 lexical gate が列挙する host-effect 呼び出しと、明示的な無条件ループは禁止
- 有限 SWO oracle が corpus 変更、relation の変動、または実際に発火した例外を観測した実装は禁止

**auditor が拒否する残余 (機械は見ていない):**
- 新しい型/関数の追加は禁止。外側への追加は単一文構造が機械拒否するが、comparator 式の内部に置く local class・nested lambda・補助 callable は機械は見ていない。禁止は不変であり auditor が拒否する
- 有限 SWO oracle で relation の変動として観測されない非決定ビルトイン (現在時刻・乱数等) は禁止。これは機械は見ていないが、禁止は不変であり auditor が拒否する
- 既存 silo API を呼ぶ straight-line code のみとする。有限 lexical gate の列挙外で、有限 SWO oracle に corpus 変更や relation 変動として観測されない副作用のある呼び出しは禁止。これは機械は見ていないが、禁止は不変であり auditor が拒否する
- 明示的な無条件ループとして検出されず、有限 SWO oracle の実行上限にも達しない bounded / data-dependent loop も禁止。これは機械は見ていないが、禁止は不変であり auditor が拒否する
- 有限 SWO oracle の corpus で発火しない条件付き例外送出も禁止。これは機械は見ていないが、禁止は不変であり auditor が拒否する
```

この exact replacement だけを施した場合の source SHA-256 は `53bae5325761a1be6bc620a15ce74c5bc4e73de56a7214552ee7f3c6306b1f9f`。NFC かつ U+0300〜U+036F は 0 件と静的確認した。段 3 以降で文言が 1 byte でも変われば再計算する。

編集範囲はこの節だけとする。

- frontmatter と `description` (`coder-v4-autonomous-sort.md:1-7`) は不変。
- 利用可能 API (`:78-82`) は不変。
- SWO 契約 (`:91-101`) は不変。
- 設計根拠その他 (`:126-134`) は不変。

注意点として、auditor の機械 gate は residual の意味検査を証明しない。現行 auditor prompt は正しさ違反の unconditional reject と every-line/context review を要求する (`auditor.md:32-36,75-82`) が、loop、非決定 builtin、latent throw を個別列挙してはいない。この wave は裁定どおり sort coder role だけを触り、auditor role への拡張は行わない。

## 3. pin 閉包の更新手順

### 更新する dict

`orchestrator/codex_roles/review_ledger.py:15-23` の次の 1 key だけを更新する。

```python
# Reviewed 2026-08-18: T-396 A; enforcement ownership only, prohibition set unchanged.
"coder-v4-autonomous-sort": "53bae5325761a1be6bc620a15ce74c5bc4e73de56a7214552ee7f3c6306b1f9f",
```

対象は `SOURCE_FILE_SHA256["coder-v4-autonomous-sort"]`、現行位置は `review_ledger.py:21`。

### 更新してはならない dict

| pin | 現行位置 | 不変の根拠 |
|---|---:|---|
| `ROLE_MANIFEST_SHA256["coder-v4-autonomous-sort"]` | `review_ledger.py:42` | `manifest.json:733-875` を触らない。full manifest pin は `spec.py:566-577` が照合 |
| `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` | `review_ledger.py:53-56` | 共通 template 不変。`spec.py:550-557` が照合 |
| `DESCRIPTION_SHA256["coder-v4-autonomous-sort"]` | `review_ledger.py:64` | frontmatter description 不変。`spec.py:583-593` が source hash と独立照合 |
| `SCHEMA_SHA256["coder-v4-autonomous-sort"]` | `review_ledger.py:100-103` | input/output schema 不変。`spec.py:657-672` が照合 |
| `ROLE_IO_CONTRACTS["coder-v4-autonomous-sort"]` | `review_ledger.py:190-193` | required fields / projection mode 不変。`spec.py:673-683` が照合 |
| `EXPECTED_ROLE_COUNT` | `review_ledger.py:13` | role 増減なし。`spec.py:538-547` が絶対件数を照合 |

### adapter 再生成

renderer は `orchestrator.codex_roles.spec.render_adapter` (`spec.py:803-873`)。source body は `_developer_instructions` (`:795-800`) に入り、source pin と各 ledger pin は `:815-845`、semantic digest は `:745-792` に反映される。

byte parity は `tools/check_codex_agents.py:223-245`、特に `actual != rendered` の比較は `:241-245`。source body exact-once は `:257-267`。

段 5 の writable 環境では、source と ledger を更新した後、新しい Python process で次だけ実行する。

```python
from pathlib import Path
from orchestrator.codex_roles.spec import get_role_spec, render_adapter

root = Path.cwd()
spec = get_role_spec("coder-v4-autonomous-sort", root)
(root / spec.adapter_relpath).write_bytes(
    render_adapter(spec, root).encode("utf-8")
)
```

`expected_adapters()` (`spec.py:876-881`) で全 13 枚を再生成する必要はない。対象 1 枚だけを `render_adapter` から書く。

### 更新順序

1. agent md の exact replacement。
2. `SOURCE_FILE_SHA256` をその exact bytes の SHA に更新。
3. fresh process で adapter を再生成。
4. B の test 削除はこの連鎖と独立なので前後どちらでもよい。
5. checker を実行。

source だけ先に変える、または SHA だけ先に変えると `spec.py:587-590` が即座に drift とする。`tools/check_codex_agents.py` は import 時に全 role spec を load する (`tools/check_codex_agents.py:34-44`) ため、中間状態で checker/test を起動してはならない。

source と ledger が揃って adapter だけ古い場合は byte parity (`tools/check_codex_agents.py:241-245`) が失敗する。adapter を手編集で合わせず、renderer に body、`source.sha256`、`review_ledger.source_file_sha256`、`semantic_digest` を一括更新させる。

### P3 の判定

P3 は一部だけ支持する。

- sandbox 制約で adapter を親が renderer bytes から適用した前例は実在する (`docs/decisions.md:7950-7953`; `docs/archive/worklog-phase3-0804-188-189.md:297-302`)。
- ただし brief が権限根拠とした D149 決定 6 は、実際には P1 未充足と wiring 時の D96 を定める節である (`docs/decisions.md:7323-7328`)。親による adapter 書込権限そのものの根拠ではない。
- 「拒否を測るためだけに必ず失敗 write を先行する」は renderer/checker の依存条件ではない。段 5 の実作業で正当な adapter write が拒否された場合だけ、その拒否を記録し、renderer 出力を親が review して適用する。
- 現在の段 2 は明示的 read-only なので、意図的な失敗 write は行わない。

## 4. B の正確な編集

P2 の「丸ごと削除」を支持する。

削除範囲は `orchestrator/tests/test_coder_effect_gate.py:151-162`、すなわち decorator、5 個の parameter、test function、pass assertion の全体である。

```python
@pytest.mark.parametrize(
    "implementation",
    (
        "for (int i = 0; i < n; ++i) { values[i] += 1; }",
        "for (const auto& value : values) { total += value; }",
        "while (remaining > 0) { --remaining; }",
        "while (0) {}",
        "for (int i = 0; i < n; ++i) {}",
    ),
)
def test_ordinary_for_range_for_and_data_dependent_loops_pass(implementation):
    assert scan_host_effects(implementation) == ()
```

コメント化、skip 化、parameter の一部残しは採らない。どれも「この形は通る」という受理方向を固定し続けるためである。

削除後の受け皿は次のとおり。

- ordinary `for`、range-for、data-dependent `while` の過剰拒否防止を受け止める test は**ない**。
- `test_single_core_literals_that_are_definitely_false_do_not_match` (`:196-207`) は false、nullptr、zero floating/character literal という狭い性質を残すが、ordinary/range/data-dependent loop の代替ではない。
- 無条件 loop を拒否する姉妹 test はそのまま残る。
  - `test_measured_four_injections_are_rejected` (`:22-34`)
  - `test_explicit_unconditional_loop_headers_are_rejected` (`:165-187`)
  - `test_while_true_with_break_is_intentionally_conservatively_rejected` (`:190-193`)
  - `test_deep_enclosing_parentheses_are_bounded_and_still_rejected` (`:229-233`)
- production `coder_effect_gate.py` は変更しないため、現時点の受理集合は変わらない。変わるのは「bounded/data-dependent loop は将来も必ず pass」という test 契約だけである。
- live tree を exact test 名で検索した結果、参照は定義自身だけだった。node 数や collection 数を固定する live meta-test は見つからない。削除される collected node は parameter 5 件である。凍結済み `output/` の過去 mutation 記録は編集・更新しない。

## 5. 波及する検査

### 直接影響

- `orchestrator/tests/test_coder_effect_gate.py`
  - B により 5 parameter node が消える。
  - 残る reject 側と false-literal 側を file 単位で確認する。
- `tools/check_codex_agents.py`
  - source pin、rendered adapter byte parity、body exact-once を直接検査 (`:223-267`)。
- `orchestrator/tests/test_codex_agents.py`
  - module import 時点で全 role spec を load (`:18-24`; checker `:44`) するため、pin 中間状態では file 全体が collection 前に失敗しうる。
  - 直接焦点 node:
    - `::test_policy_has_zero_native_and_thirteen_static_dormant_adapters` (`:121-124`)
    - `::test_review_ledger_independently_pins_all_thirteen_sources_and_io_contracts` (`:127-156`)
    - `::test_current_sources_render_byte_exact_and_native_is_empty` (`:159-161`)
    - `::test_all_adapters_pin_model_policy_and_blocked_runtime_activation` (`:164-214`)
    - `::test_source_body_is_embedded_exactly_once_before_product_override` (`:216-230`)
    - `::test_claude_tool_capabilities_are_lowered_without_runtime_tool_claim` (`:233-249`)
    - `::test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced` (`:1199-1215`)
- `.codex/role-adapters/coder-v4-autonomous-sort.json`
  - runtime digest は変わるが、`test_codex_role_runtime.py:468-475` は critic adapter だけを直接使うため焦点 node ではない。role loader の間接回帰として file 全走時に受け止める。

### docs / repository check

- `tools/check_docs.py` の `LIVING_DOCS` に `.claude/agents/` や adapter JSON は含まれない (`tools/check_docs.py:44-79`)。したがって内容への直接検査はない。
- それでも class 3 完了条件として `python3 tools/check_docs.py` は実行する。
- wrapper node は `orchestrator/tests/test_check_docs.py::test_real_repo_clean` (`:9778-9786`)。
- `orchestrator/tests/test_check_docs.py::test_codex_dev_wave_skill_contract_pins_exact_surface` (`:7661-7683`) は dev-wave skill 自体の test であり、この 4 枚には非影響。
- `tools/task_run_check.py:14-21` は `static-check` と `docs-check` をそれぞれ上記 checker へ委譲する。
- commit 後は `python3 tools/check_ai_provenance.py`。これは内容 test ではないが AGENTS.md の完了条件である。

`test_diff_quarantine.py`、`test_sort_swo_oracle.py`、`test_p3_s4_loop_sort.py` は production gate を触らないため直接影響しない。最終 acceptance 全走では当然含めるが、段 5 後の焦点走に必須ではない。

### 段 5 後の焦点集合

すべて `pytest` 直打ちではなく `tools/run_tests.py` を通す。

```text
orchestrator/tests/test_coder_effect_gate.py

orchestrator/tests/test_codex_agents.py::test_policy_has_zero_native_and_thirteen_static_dormant_adapters
orchestrator/tests/test_codex_agents.py::test_review_ledger_independently_pins_all_thirteen_sources_and_io_contracts
orchestrator/tests/test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty
orchestrator/tests/test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation
orchestrator/tests/test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override
orchestrator/tests/test_codex_agents.py::test_claude_tool_capabilities_are_lowered_without_runtime_tool_claim
orchestrator/tests/test_codex_agents.py::test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced

orchestrator/tests/test_check_docs.py::test_real_repo_clean
```

その後に直接 checker を走らせる。

```text
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

この段では test node は 1 件も実行していない。補助的な `tools/run_tests.py --help` 照会は wrapper が pytest へ転送し、利用可能な一時ディレクトリがないため collection 前に停止した。したがってテスト結果はすべて**未実走**であり、緑の主張はない。

## 6. 変異事前登録の素材

各 mutant は単独で適用し、primary kill だけを会計する。

| ID | 1 箇所の変異 | 守る不変条件 | 殺すべき既存 node |
|---|---|---|---|
| M1 | `review_ledger.py:21` を旧 SHA `577af0d4246933f128f77836c7b85786683ed3dbeca01403f9d4b7aa828e941f` のまま残す | source と独立 review pin の一致 | `test_codex_agents.py::test_review_ledger_independently_pins_all_thirteen_sources_and_io_contracts`。実際には eager import (`test_codex_agents.py:24`; checker `:44`) で node 実行前の collection failure になる可能性が高い |
| M2 | final source/ledger に対し sort adapter 1 ファイルを pre-wave bytes のまま残す | renderer byte closure | `test_codex_agents.py::test_current_sources_render_byte_exact_and_native_is_empty` |
| M3 | generated adapter の `developer_instructions` から residual bullet 1 行だけ削る | Claude source.body exact-once embedding | `test_codex_agents.py::test_source_body_is_embedded_exactly_once_before_product_override` |
| M4 | generated adapter の `review_ledger.source_file_sha256` だけを旧 SHA に戻す | adapter 内 ledger と独立 ledger の一致 | `test_codex_agents.py::test_all_adapters_pin_model_policy_and_blocked_runtime_activation` |
| M5 | `coder_effect_gate.py:554` の unconditional branch を発火不能にする | 現行の無条件 loop 拒否を広げも緩めもしない | `test_coder_effect_gate.py::test_explicit_unconditional_loop_headers_are_rejected` |
| M6 | `coder_effect_gate.py:74-75` の `read` identifier だけを deny tuple から削る | 現行 host-effect 受理集合を広げない | `test_coder_effect_gate.py::test_each_deny_table_category_has_a_mutation_killing_probe[file-stdio]` |
| M7 | agent source の residual から「条件付き例外送出も禁止」1 文だけ削る | 禁止文を 1 つも撤回しない | 未 review の 1-file mutant は M1 と同じ source pin gate が機械的に殺す。しかし、pin と adapter まで意図的に再承認した後に禁止文の意味を検査する既存 semantic test は**実在しない** |

M7 は重要な限界である。現行 pin は「review 済み bytes と同じ」を証明するが、「5 禁止が必ず残る」を構文・意味として証明しない。本 wave の 4 枚制約内では新しい semantic test を追加せず、この欠落を mutation 記録へ明記する。

## 総括

- A は closed-region 節だけを機械執行 5 項目と auditor residual 5 項目へ二分し、禁止文はすべて残す。
- 現行 bullet の分類は、raw directive と comment/backslash が完全、残り 3 bullet が部分執行である。
- exact 置換時の source SHA は `53bae5325761a1be6bc620a15ce74c5bc4e73de56a7214552ee7f3c6306b1f9f`。
- B は 5 parameter の pass test を丸ごと削除する。一般的な bounded/data-dependent loop の過剰拒否防止 test は残らない。
- P1 は残余 5 種という結論を支持するが、4 種には有限機械執行がある。P2 は支持、P3 は前例のみ支持し D149 の権限根拠は反証した。
- 未解決点は、auditor prompt が全 residual を個別列挙していないことと、禁止文削除を意味で殺す既存 test がないことである。
- pytest と checker は未実走であり、段 5 後に上記焦点集合と必須 checker を実行する。