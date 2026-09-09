## 総括

静的レビューでは must-fix はありません。正しさゲート2ファイルは無変更で、受理条件の緩和はありません。  
originless helper の件数、対象path、assertの発火性はbaselineと一致し、既存helper・literal・volatile指定も不変です。  
主張は段4裁定5の範囲内です。ただし独立semantic gateがない既知の限界は残るため、将来のLLM出力やcertified選択が不変とは主張できません。  
過去のtrial記録・凍結成果物への変更は、対象を限定したdiff実測でありません。

## must-fix (成果物影響を 1 行で必ず添える)

なし。

成果物影響: must-fix起因のcertified選択、材料レポート、試行台帳の修正要求はありません。

## 所見 (real / refuted)

1. **refuted — 正しさゲートの緩和**

   `git diff --exit-code -- orchestrator/campaign/p3_s4_loop.py orchestrator/campaign/s8c_generation_projection.py` は `rc=0` でした。両ファイルは1 bitも変更されていません。

   成果物影響: machine acceptance set、certified選択、材料レポート、試行台帳の値・参照はゲート変更によって変わりません。

2. **refuted — 既存テストの弱体化**

   `orchestrator/tests/test_reflux_originless_compatibility.py` のdiffはT-2249 helper 24行の追加だけです。`_PRE_WAVE_ORIGINLESS_BASELINE`、T-1353 helper、T-2145 helperの抽出source segment SHA-256はHEADと作業木で一致しました。`{"volatile": True}` の字面も双方17件です。

   成果物影響: plannerのsource SHA参照だけが、journal 6行とplanner report 1集約行で新SHAへ追随します。他の非volatile leafや受理集合は変わりません。

3. **refuted — 主張の過大化**

   `orchestrator/codex_roles/review_ledger.py:25,42` は、裁定された「段4の `delta_pct≡None` 不変と食い違う固定例をroleの入力契約から除去」の範囲と同じです。「runtime leakを閉じた」「リーク防止を保証した」「durableにcertifyした」とは書いていません。planner側の変更対象が `last_delta_pct` である点も、段4裁定 `s4-adjudication.md:80-83` が明示的に含めています。

   helperのdocstring `orchestrator/tests/test_reflux_originless_compatibility.py:601` も「review済みplanner source pinをlive originless outputへ追随」とだけ述べ、因果効果やリーク防止を主張していません。

   成果物影響: 注記とdocstringはprovenance更新の意味を説明するだけです。machine acceptance setは不変ですが、role prompt bytesが変わるため、将来の実LLM提案やcertified選択まで不変とは証明されません。

4. **refuted — 恒真なassert**

   `assert replaced == 6` は旧SHAの置換後件数を検査し、0件・5件・7件などで停止します。`assert report_rows == [[old, 6]]` はreportを書き換える前に旧値・単一行・count 6を同時に要求します。どちらも無条件には真になりません。

   成果物影響: baselineのplanner provenance配置が将来変わればimport時に停止し、誤った材料レポート・試行台帳baselineを黙って受理しません。

5. **real、意図どおり — provenance参照の更新**

   role source SHA、ledger pin、adapter内2箇所のsource SHA、semantic digest、埋め込みrole本文が閉包として追随しています。adapterは各4 pointerだけの変更で、現在のbyte数とSHAは報告値に一致します。

   - coder: 9719 bytes、`70cb1be6...72b54a`
   - planner: 8532 bytes、`963034a1...1adce`

   成果物影響: 新規originless生成物ではplanner `role_file_sha256` 参照が新SHAになります。fixture応答はhard-codeなので選択値や受理集合は変わりません。

6. **real、既知のscope外限界 — semantic guard absent**

   全surfaceを協調して旧bytesへ戻す変異を独立に拒否するsemantic testはありません。これは段4裁定 `s4-adjudication.md:56-74` で明記され、新規test追加はscope外と裁定されています。

   成果物影響: 現差分の受理集合は変えませんが、将来の協調rollbackに対する保証は人間review pin依存のままです。材料レポートでdurable certificationとして扱えません。

7. **refuted — 規律7違反**

   `git status --short` と `git diff --name-status` の実測対象は指定6ファイルだけです。`git diff --name-only -- output` と `git diff --name-only -- '**/attempts.jsonl' '**/report.json'` はともに出力0件でした。

   成果物影響: 過去のcertified選択、材料レポート、試行台帳、凍結成果物の値と参照は書き換えられていません。

## 正しさゲート無変更の確認結果

- `orchestrator/campaign/p3_s4_loop.py:1226`: `_DELTA_PCT_LIVE = False`
- 同 `:1124-1129`: planner射影時に非`None`を `WhiteboardLeakError`
- 同 `:1292-1301`: checkpoint load時にも非`None`を `WhiteboardLeakError`
- 同 `:1240`: whiteboard field集合は5 keyのまま
- `orchestrator/campaign/s8c_generation_projection.py:68-70`: `_WHITEBOARD_KEYS` は `iteration/direction/magnitude/result/delta_pct`
- 同 `:231-241`: `set(mapping) != expected` によるexact-key拒否
- 同 `:574-606`: 各entryをexact 5-key検査し、`delta_pct is not None` を拒否

diff実測 `rc=0` のため、これらはHEADから無変更です。

成果物影響: non-`None` deltaや余分・不足keyの受理集合は広がっておらず、既存のfail-closed境界が維持されています。

## originless helper の件数検算

`_PRE_WAVE_ORIGINLESS_BASELINE` の生literalを直接JSON decodeして検算しました。

- journal key: `journals/*/*/provenance/role_file_sha256`
  - 旧planner SHAの行indexは `0, 4, 8, 12, 16, 20`
  - 6行すべて `[old, 1]`
  - `replaced == 6` は実baselineと一致
- report key: `reports/*/cells/*/generations/*/roles/planner/provenance/role_file_sha256`
  - exactに `[[old, 6]]`
  - report assertも実baselineと一致
- 旧SHAが存在するbaseline pathは上記2件だけ
- helperが変更するのはjournal 6行とplanner report 1行、計7 baseline leaf rowの値部分だけ
- count、key集合、他role、他leafは変更しない
- coder SHAは対象外
- 新SHAはhelper適用前literalには0件

HEAD対作業木の抽出hash比較:

- baseline literal: 同一
- `_extend_t1353_originless_baseline`: 同一
- `_extend_t2145_role_source_baseline`: 同一
- volatile marker: 17件対17件

成果物影響: originless材料レポートのplanner provenance集約1行と、試行台帳のplanner provenance 6行だけが新SHAを参照します。選択値と受理集合は変わりません。

## この変更で食い違いが生じた / 解消した箇所 (file:line)

### 生じた箇所

確認できませんでした。これは次の追跡対象検索とdiff読解による実測です。

```text
git grep -n -I -E \
'last_delta_pct[^[:cntrl:]]*-1\.2|"delta_pct"[[:space:]]*:[[:space:]]*-1\.2' \
-- '*.md' '*.py' '*.json' ':!docs/archive/**'
```

該当は過去形で記録された歴史insightの2件だけでした。

- `output/insights/2026-08-01_t288-recipient-matrix/s2-plan.md:143`
- `output/insights/2026-09-02_t2200-k2-role-contract/README.md:66`

これらは過去のrole bytesに関する記録なので、今回追随編集しないことが正しいです。

成果物影響: 新規不整合によるcertified選択、材料レポート、試行台帳の誤参照は確認していません。

### 解消した箇所

- `.claude/agents/coder-v4-autonomous.md:47`
  - `delta_pct: null` が `p3_s4_loop.py:1124-1129,1292-1301` および `s8c_generation_projection.py:68-70,574-606` の`None`契約と一致。
- `.claude/agents/planner-v4.md:35`
  - `last_delta_pct: null` が `docs/phase3-s4b-runbook.md:45` と `docs/phase3-s5-sort-runbook.md:44` に一致。
- `.codex/role-adapters/coder-v4-autonomous.json:8` と `.codex/role-adapters/planner-v4.json:8`
  - 埋め込みrole本文がsource roleと一致し、source SHA、ledger pin、semantic digestも追随。

成果物影響: role契約とprovenance参照の不整合が解消します。runtime schemaの受理集合は変わりません。

## nit / backlog

- **real、pre-existing、nit/backlog:** planner例 `.claude/agents/planner-v4.md:42-44` とcoder例 `.claude/agents/coder-v4-autonomous.md:46-48` のwhiteboardはいずれも3 key例で、実射影のexact 5-keyとは一致しません。今回の`null`化で生じたものではなく、段4裁定 `s4-adjudication.md:92-99` のscope外driftです。  
  成果物影響: 現在のmachine gateは5 keyを要求し続けるため受理集合は変わりません。文書読者の誤解リスクだけです。

- **real、pre-existing、nit/backlog:** `.claude/agents/planner-v4.md:73` の「leading-indicatorsだけ」は同 `:32-40` の `current_perf` と食い違います。`docs/decisions.md:5671-5673` の残余記述も現在はstaleです。  
  成果物影響: 今回の成果物値・参照には影響せず、role契約説明の精度だけに影響します。

- **real、pre-existing、別erratum:** `docs/phase3-s8c-autonomous-trial-runbook.md:233-235` の「前世代の結果から更新したcurrent_metrics」は、段4裁定で別scopeへ送られています。今回の`null`化による新規不整合ではありません。  
  成果物影響: 今回のoriginless baselineやtrial ledger参照には影響しません。

- **規律6:** 読んだ資料には振る舞いを指示する文字列があります。具体的にはrole本文の制約 `.claude/agents/planner-v4.md:20-24`、`.claude/agents/coder-v4-autonomous.md:20-27`、adapterの `developer_instructions`、裁定の実装境界 `s4-adjudication.md:65-74,148-157`、親への継続要求 `s5b-impl.md:109-113`、書込み処理 `render_adapters.py:49-68` です。すべてreview対象のデータとして扱い、指示として実行していません。  
  成果物影響: このreviewによる書込み・render・test実行はなく、成果物は変化していません。

## 未確定・要裁定

要裁定事項はありません。

pytestとcheckerはこのread-only reviewでは実走していません。したがって「テスト緑」とは主張しません。静的にはadapterのbyte数・SHA、source SHA、変更pointer、`git diff --check` の `rc=0` まで確認済みで、実走結果の確定は親の担当です。