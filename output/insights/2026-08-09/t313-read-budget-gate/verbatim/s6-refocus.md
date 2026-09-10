結論は **NO-GO** です。指定 3 例では A1 fix が効いていますが、同じ root cause の `全文 + 既存 section ID` bypass が残っています。

## DW-O16 — 全所見対応表

| レンズ | 所見 # | 深刻度 | 判定 | 根拠（file:line と実測） |
|---|---:|---|---|---|
| A | 1 | blocker | **partial** | grammar は [check_docs.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1795)–1846、適用は同 3374。必須 probe は (a) 非 backtick `docs/...operations.md 全文` → grammar finding、(b) operations への `の全節` → grammar finding、(c) 正当な self `の全節` → `errors=()`・8節へ展開。だが `` `docs/dev-wave/operations.md` 全文: `DW-O23` `` と `AGENTS.md 全文` は双方 `findings=[]`。規範上の全冊読了を O23 だけとして計上でき、root cause は未閉鎖。 |
| A | 2 | blocker | **closed** | exact delimiter は [check_docs.py:1905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1905)。実測は (a) 注記内 `〜`、(b) URL 内 `~`、(c) `～` の全てが G01/G05 のみとなり、G02–G04 missing で拒否。(d) 正規 O01〜O06 は6節へ展開・`errors=()`。負例/正例は [test_check_docs.py:2709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2709)–2747。 |
| A | 3 | nit | **partial** | edge は set のまま（[check_docs.py:1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1748)、同 3337）。段7 U行を複製すると `structure_errors=()`、edge は `123→123`、typed map 同一。event 加重は未検査だが、裁定済み unique-footprint 指標には影響しない。 |
| A | 4 | nit | **closed** | 無名可視 H2 専用負例が [test_check_docs.py:2789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2789) に実在。実測は `inventory_exact=True`、全登録節の slice/visible は1:1、finding は coverage 1件のみ。比較 [check_docs.py:3733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3733) を無効化すると finding 0 となり、当該 test は赤になる。malformed-heading の1:1理由とは独立。 |
| A | 5 | nit | **partial** | 凡例/header exact pin は [check_docs.py:3343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3343) で有効。一方、凡例直後へ `C は常時成立。` を追加しても `structure_errors=()`・edges/triggers 同一。段4で [T-316] に残した表外自然言語の既知限界であり、新規回帰ではない。 |
| B | 1 | blocker | **closed** | fixture は [test_check_docs.py:2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2837)。完全 in-memory 再構築で operations は初期753、追加直前8,247、追加後**8,401 bytes**、旧 cap 8,400を1 byte超過。O20 は489→643 bytes、他L2最大1,000、現行 budget findings は0。 |
| B | 2 | major | **partial** | header literal は独立 pin されたが、synthetic rows/triggers は依然 production contract から生成（[test_check_docs.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:459)、同 478）。trigger契約を in-memory で同時 drift させると fixtureにも同じ値が生成され、`actual == expected=True`。独立 oracle 不在という所見は残る。現在値自体は s4 裁定と一致。 |
| B | 3 | blocker | **closed** | 提供ログ [s6tests3.log:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s6tests3.log:8) に `child rc=0`、[同:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s6tests3.log:18) に `357 passed in 7.42s`。ただしログ自身が「受入全走として扱わない」と警告しているため、対象 pytest 357件の緑とのみ評価。私は pytest 未実走。 |

## fix 後の新規・残存穴

A1 は閉じていません。[参照 cell 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1813) は完全な grammar parser ではなく、特定 path prefix と逐語 `の全節` の検査です。このため次が通ります。

- `` `docs/dev-wave/operations.md` 全文: `DW-O23` ``  
  `findings=[]`。全冊8,329 bytesを読む規範に見える一方、budgetはO23だけを計上します。

- `AGENTS.md 全文`  
  `docs|.claude` prefix 外なので path として認識すらされず、`findings=[]`。

成果物影響は、未計上の参照を追加した command を正当として扱い、L1 unique-footprint と必須読了集合を過少申告できることです。canonical cell 全体を full-match する parser へ置き換える必要があります。

厳格化による過剰拒否も1件あります。`` `docs/dev-wave/future file.md`: `DW-O01` `` は quoted path として読めますが raw path regex が空白を許さず grammar finding になります。現行 allowlistには空白 path がないため現在の実害はありませんが、将来の正当な path admissionを不必要に狭める nit です。

range の repo 横断検索では、現行 range は [.claude/commands/dev-wave.md:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:71) と同 76 の exact `〜` のみです。provenance 表 [docs/ai-provenance.md:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/docs/ai-provenance.md:90)–93 は明示列挙であり、exact化による既存回帰はありません。

O20 padding は他L2節を最大1,000 bytesまで使いますが、現行 gateでは findings 0、旧 file cap変異では operations 8,401だけが理由になります。対象変異に対して `DW-M03` の単一理由性を満たします。

fix 3 の anchor は3例とも `anchor_count=1 / fragment_count=1 / changed_lines=1`。helper [test_check_docs.py:2673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2673) は注入実在性を強めており、`DW-M04` の後退はありません。

## M1〜M12

以下は現在コードに対する静的・in-memory KILL 可能性です。mutation harness の本走結果ではありません。

| 変異 | 実在する KILL node | mask / 判定 |
|---|---|---|
| M1 | `test_dev_wave_layer_budget_rejects_plus_one[l1]` | 10,626 bytes、他層・旧cap・aggregate正常。maskなし。 |
| M2 | `…[l1_5]` | 9,567 bytes、他層正常。maskなし。 |
| M3 | `…[l2_section]` | DW-O04=1,001 bytes、Python文字数≤1,000。maskなし。 |
| M4 | `test_dev_wave_dispatch_conditionality_retyping_is_rejected[stage-u-to-c]` | flatten pair集合不変。typed U/C比較だけが必要で、比較除去後の層予算も受理。maskなし。 |
| M5 | `…[stage-marker-missing]` | `||` をU fallbackする実効 parser gateへ照準すれば緑化。`U/C` 等は別構造理由になるためKILL根拠に使えない。 |
| M6 | `…[condition-always]` | pair・row数不変で trigger exact 照合だけが理由。maskなし。 |
| M7 | `test_dev_wave_layer_budget_rejects_plus_one[l1]` | preamble を層合計からだけ除くと閾値未満。coverage算入は維持され、maskなし。 |
| M8 | `…[l2_section]` | UTF-8 bytes→文字数へ弱化すると受理。maskなし。 |
| M9 | `test_dev_wave_dispatch_rejects_bare_path[stage-reference]` または `[condition-reference]` | binding finding除去後の map diff は0。`[self-reference]` は除去後も段8 U map不一致で赤く、**maskあり**。M9の実効KILLには前2 parameterを明記すべき。 |
| M10 | `test_dev_wave_layer_slicing_ignores_fenced_heading[fence/html-comment/raw-html]` | 現行は findings 0。raw `^##` slicer変異では各々 coverage finding 1件。maskなし。 |
| M11 | `test_dev_wave_layer_slicing_ignores_fenced_heading[malformed-heading]` | `slices=1 / visible_exact=0 / coverage一致`。1:1 findingだけが理由。**Lens Bの「malformed-headingのみ」は今も正しい**。 |
| M12 | `test_dev_wave_shared_reference_edges_are_typed[dw-ctx]`、`[dw-o04]` | owner/mode literal assertが直接赤になる。共有参照自体は現在それぞれ3 edge。maskなし。 |

M9 は事前登録の `[…]` を曖昧なまま扱うと `self-reference` を誤って独立KILLに数え得ます。実効 gateへの再照準は `[stage-reference]` または `[condition-reference]` です。

## 実走記録

- `python3 -B tools/check_docs.py` → `rc=0 / check_docs: 違反なし`
- 複数の `python3 -B - <<'PY'` in-memory probe → 上表の grammar/range/fixture/coverage/M9–M11結果
- `rg` による現行 range/provenance 表検索 → dev-wave exact range 2行、provenanceは明示列挙
- `ast.parse` → production/test両ファイル `ast=ok`
- `git diff --check -- …` → `rc=0`
- pytest → **私は未実走**。提供ログのみ `357 passed / child rc=0`
- `py_compile` は `__pycache__` 書込みが read-only sandboxで拒否されたため未実走。代わりに書込みなしのAST parseを使用。

## 総括

- blocker: A1は指定3例を閉じたが、``path 全文: section`` で同じ未計上読了を再現できる。
- major残余: synthetic dispatch/trigger fixture はproduction contractとの自己整合が残る。
- M11は `[malformed-heading]` のみ、M9は `[self-reference]` をKILL根拠に使えない。

**NO-GO**