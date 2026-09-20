## 所見

**NO-GO。主要実装はプラン v2 に沿っていますが、回帰修正と変異定義の訂正、計算ノードの実 TU 証拠が残っています。**

静的検査のみ実施しました。編集・pytest・実 TU 実走はしていません。worktree の `git diff` は `author-impl.patch` と byte 一致し、変更は指定の5ファイルでした。以下、略号を使います。

- **G**：`orchestrator/campaign/condition_meaning_gate.py`
- **T**：`orchestrator/tests/test_condition_meaning_gate.py`
- **C**：`orchestrator/campaign/s8a_trigger_coverage.py`
- **S1**：`orchestrator/tests/test_s1_direct_comparison.py`
- **S**：`orchestrator/tests/test_s8a_trigger_sweep.py`

1. **real／must-fix：docstring の逐語 pin が未追随。**  
   根拠：G:12–18、T:3282–3285。供給40件・枝 witness 21件という現物に対し、test名は38件、assertは18件を要求します。  
   **放置時の成果物：** 正しい登録追加でも所有テストが赤になり、件数の説明も食い違います。

2. **real／must-fix：S1 fixture と未確立持ち越し例の二箇所を直す必要がある。**  
   根拠：S1:697–732、794–804。fixture は GATING を一箇所しか生成せず、持ち越し例は新たに確立対象となった1/0を使っています。  
   **放置時の成果物：** fixture の箇所数修正だけでは、持ち越しtestの期待 `unestablished` が成立しません。43件と残る1件を分けて扱うべきです。

3. **real／must-fix：m4 の登録文言は等価変異で、現在のtest順序も独立帰属を保証しない。**  
   根拠：G:3342–3375、T:1499–1513、`ruling.md` のm4。対照 c=0では、非負のmarker数に対する `selected ≤ N·c` は `selected == 0` と同じです。また直接検査より前に公開evaluatorのreasonをassertするため、schema側の拒否で先に落ち得ます。  
   **放置時の成果物：** 評価側防壁を壊していない変異、または別防壁による失敗を「評価側の検出」と数えます。

4. **refuted／修正不要：不在検査の拡大、N=1互換破壊、`-U`消去という欠落はない。**  
   根拠：G:2299–2307は登録 `#ifdef` に限定、G:2999–3010はN=1のreason/detailを保持、G:4060–4093は対象の `-D` だけを除去します。T:1460、1541以降にも対応検査があります。既存18 entryの値・順序・2-tuple保持はAST比較でも確認しました。  
   **成果物への影響：** この三点を理由に追加機構を導入する必要はありません。

5. **real／nit：新規正例のmeaning実走が重複している。**  
   根拠：T:1359とT:1401は、新規3 macroについて同じfixture・要求・countsを再評価します。後者のsupply/admission検査は必要です。  
   **削除案／DW-G05：** T:1401のsupply/admission assertionを前者の新規macro分へ移し、後者の関数を削除しても、production成果物・受理条件・正例の検査内容は変わりません。

   別N mappingと二つのhelperは裁定済みであり、削除対象ではありません。G:4068の末尾 `-D` 拒否も残します。既存 `_compile_defines` は末尾単独 `-D` を拒否しないため、「先行検査で到達不能」として削る根拠はありません。

6. **real／must-fix：完了証拠はlogin側まで。計算ノード側の実 TU cellは未提示。**  
   根拠：`focus-logs.md:14–28`。計算ノードで走った焦点pytestと、loginで走った実 TU cellは別です。  
   **放置時の成果物：** 「login＋計算ノードで成立」という裁定上の完了条件を、片側の証拠だけで満たしたと報告します。

7. **refuted／実装修正不要：B-4のdirty-tree失敗はgate実装に非帰属。**  
   根拠：`orchestrator/tests/test_p3_b4_wiring_probe.py:1522–1540`。許容する変更はprobeの2ファイルだけですが、現物にはauthorの5ファイルが未commitです。  
   **成果物への影響：** cleanな統合commitで再確認すべき検査であり、許容集合の拡張やtest削除は不要です。

## 赤 2 種の裁定案

**(i) docstring／逐語pin**

供給domainは**40**、枝 witnessは**21**、FIXEDを含む対応集合は**22**です。三者を混ぜない修正にします。

Gの該当部分は次の逐語案です。

```text
Claim boundary: the supply domain contains the 40 patch-derived defines.  The
legacy runtime-meaning witness remains exclusive to ``BACKOFF_FIXED``.  Twenty-one
registered macros additionally have a bounded compile-time witness (21 total): it
```

後続の `#ifdef` 未定義対照・主張限界の説明は維持します。Tのtest名とpinは次へ更新します。

```python
def test_module_claim_names_the_exact_40_define_supply_domain() -> None:
    assert "supply domain contains the 40 patch-derived defines" in G.__doc__
    assert "Twenty-one\nregistered macros additionally have a bounded" in G.__doc__
    assert "compile-time witness (21 total)" in G.__doc__
```

既存の独立集合pinがあるため、別の件数専用testは追加不要です。

**(ii) S1の44件**

fixtureの最小修正には、**test内の独立期待値**を推奨します。

```python
count = {"BACKOFF_TRIGGER_GATING": 12}.get(request.macro, 1)
for site in range(count):
    variable = f"condition_fixture_{request.macro.lower()}_{site}"
    # 現行の #if / #else 本文を一箇所ずつ追加
```

requested木・stock木の両方に適用します。変数名も一意にしてください。

`condition_meaning_gate._declared_site_count(request.macro)` を使う案も、S1を単なるconsumer fixtureと位置付ければ成立します。ただしproductionの誤ったNへfixtureが自動追随します。独立表は一項目で済み、今回はこちらが妥当です。汎用の登録簿再現helperは不要です。

持ち越しtestは入力だけを次へ変更します。

```python
(("BACKOFF_TRIGGER_GATING", 0),)
```

根拠は次の経路です。

- S1 productionの既定値は0：`s1_direct_comparison.py:183,198–214`。
- GATING 0/0ではfactoryがNone：G:1020。
- 既定値一致はstock inert供給比較：G:1032–1041、2614以降。
- S1 helperはstock木も準備し、実evaluatorへ渡す：S1:652–670。

したがって、**supply green／meaning unestablished／admitted／未確立一覧にGATING**という既存assertは維持できます。これは静的に成立する修正案であり、修正後の実走確認は必要です。

`focus-logs.md:10` の「実 requestでは成立しない」は**GATING 1/0に限れば正しい**ですが、0/0まで否定する説明は訂正してください。macroが登録済みでも、全要求値対に宣言があるわけではありません。

**(iii) B-4**

未commit dirt由来と裁定します。gate修正へ帰属させず、統合commit後に再走してください。現在の赤を緑として計上することもしません。

## pin 表

`git grep` と現物・差分を照合した結果です。

| pin／consumer | 根拠 | 判定 |
|---|---|---|
| 登録簿の順序・2-tuple | G:254–319 | 旧18件は値・順序とも保持、末尾＋3 |
| `_COMPILE_TIME_BRANCH_MACROS` | T:33–55 | 同じく旧18件を保持、末尾＋3 |
| `MEANING_SUPPORTED_MACROS` | T:3070–3072〔旧2814付近〕 | `{"BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS}`で追随。tupleはtest内の独立列挙であり、production導出ではない |
| directive・Nの束縛 | T:291–329、1034–1053 | 新規は独立期待表、既存はN=1。弱い「一箇所以上」検査にはなっていない |
| MOCCの一意性・tuple unpack | `test_mocc_mutation_proof.py:177–188`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569–590` | 対象は既存N=1。変更不要 |
| rung1のNone前提 | `test_silo_ladder_rung1_driver.py:101–111` | RUNG1は更新済み。残るNoneはBACKOFF_FIXED -1の別契約 |
| S1 fixture／未確立例 | S1:697、794 | **修正必須** |
| S1 golden | `s1_expected_goldens.py:168,256,318,373` | flags・path・key構造。今回goldenを変更する根拠なし |
| trigger loopのstub | `test_p3_s4_loop_trigger_gating.py:72–83`、production同名module:129 | stubと`declaration=None`は残るが、探索loop配線は明示的scope外。12箇所fixtureへ広げない |
| B-4の47 module | `test_p3_b4_wiring_probe.py:327` | 新module・import追加なし。47を維持 |
| spawn site | `test_ccbench_spawn_sites.py:81,123,222–224` | Gの`_run_process`、coverageの既存site各1を維持。差分にspawn追加なし |
| `check_docs.py` literal | `tools/check_docs.py:3552–3553,4033以降` | runbook／dispatcherの契約。変更5ファイルへの直接参照は検索で検出せず、更新不要 |
| 凍結manifest | `output/s1-freeze`、`output/s8b-freeze` | 変更5ファイルへの直接path一致なし。差分にもmanifest変更なし。歴史hashの追随更新不要 |
| docstring pin | T:3282–3285 | **修正必須** |

主張については、author報告の「実装済み・未実走」「REQUESTED_US残件」「実発火・検出は証明しない」は適切です。`author-impl.md:41–42,56`の「frequency／rung1は自動追随」は**配線上の追随**として読めますが、公開JSON取得済みという意味へ広げてはいけません。

また、G:909の `22-macro supply domain` は既存の古いdocstringです。今回の対応集合22件とは別であり、供給40件へ直す小修正候補です。今回導入の不具合には数えません。

研究前進は次まで確認できます。

| 完了項目 | 判定 |
|---|---|
| 登録簿18→21、対応集合19→22 | 静的に確認 |
| loginのMISATTR／RUNG1／GATING両構成 | 親ログで所定counts・green・admitted・未確立[] |
| I1のSORT／REPORT比較 | 親ログは裁定後の「揮発要素を除く比較」を支持 |
| 全既存macroのcanonical JSON byte一致 | このログからは主張不可。派生digestにも差がある |
| 計算ノードの実 TU cell | 未提示 |
| REQUESTED_US | 未登録の残件 |
| 公開coverage／frequency／rung1 JSON | 未取得として扱う |
| MISATTRの誤帰属発火・検出 | 枝選択witnessからは証明しない |

## 変異 matrix 案

**残すのはm0・m1・m2・m3・修正版m4・m5・m6・m8。m7は必須集合から削除**します。以下のseamは現物の逐語です。G/Cのpathは冒頭定義のとおりです。

| ID | file／old逐語 → 置換案 | 最小の判定対象 |
|---|---|---|
| m0 | G:322 `"BACKOFF_TRIGGER_GATING": 12,` → 同行末尾へ `# declared sites` を追加 | 等価対照。GATING正例がSURVIVED |
| m1 | C:113 `default_value=None if macro == MISATTR_DEFINE else 0,` → `default_value=0,` | Sの実helper `[misattr]`、default観測でKILLED |
| m2 | C:120 `declaration=condition_meaning_gate.declare_define_runtime_meaning(request),` → `declaration=None,` | Sの実helper `[gating]`、宣言型でKILLED。両parameterの二重計上は不要 |
| m3 | G:322 `"BACKOFF_TRIGGER_GATING": 12,` → `"BACKOFF_TRIGGER_GATING": 11,` | TのGATING正例。独立N pinの失敗は補助として別記 |
| m4′ | G:3369付近 `or default_counts != default_expected:` → `or default_counts[1] != default_expected[1]:` | 対照selected検査だけを除去。RUNG1のpartial-default直接検査でKILLED |
| m5 | G:4058 `selected_count=count * int(default_value or "0"), completed_count=count,` → `selected_count=evidence["default"].selected_count, completed_count=count,` | Tの公開schema検査、RUNG1のdefault selected=1でKILLED |
| m6 | G:2299 `if expected_value is None and not stock_identity \` → `if False and expected_value is None and not stock_identity \` | supply単独testの対照`-DM=0`。数値差が残るため検査削除を検出 |
| m8 | G:2300の `and _declared_contrast_is_undefined(request.macro) \` を削除 | T:1460のSORT 1/NoneでKILLED |

補足裁定：

- **m4の原案は削除し、m4′へ訂正。** completedとrequestedの検査、not-discriminating検査は残します。`(2,2)/(1,2)`だけを誤受理させる変更になります。
- **T:1505以降の直接検査を、公開evaluatorの呼出し・assertより前へ移動。** 新test追加なしで、m4′をschema防壁に遮られず検出できます。
- **m5はdefault側の呼出し引数だけを変える。** validator全体のselected検査削除はrequestedまで壊し、狙いが広すぎます。
- **m7は冗長。** MISATTRの独立集合pin・patch束縛・factory正例が既にあり、entry削除によるKeyError等を別の研究成果として数える必要はありません。
- m3の複数失敗、m6の三token形、m5の三macroを独立したkill成果として水増ししないでください。
- 以上は**提案であり変異実走結果ではありません**。baseline修正後、固定commitでnodeidと帰属を確定する必要があります。

## 判定

**NO-GO。must-fixは以下です。**

1. docstringの件数pinと古いtest名を更新する。
2. S1 fixtureをGATING 12箇所へ修正し、持ち越し例を実requestの0/0へ変更する。
3. m4を非等価な変異へ訂正し、直接検査を先に実行して帰属を分離する。
4. 修正後baseline・採用変異・clean commitでのB-4を確認する。
5. 裁定で要求した計算ノードの実 TU cellを取得する。公開driver JSONは引き続き未取得と明記する。

## 総括

三件登録、未定義対照、全宣言箇所の観測という実装は妥当です。追加の汎用機構や凍結pin更新は不要です。残る作業は局所的な回帰修正、変異の成立性・帰属の訂正、計算ノード側の証拠取得です。REQUESTED_USを含む残件(c)全体の完了は主張できません。