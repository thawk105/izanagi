## 所見一覧

1. **real — M5 の old anchor が一意でない。**
   `    "AGENTS.md",` は `tools/check_docs.py:714`（rulings）と `:739`（next-tasks）の **2 件**。ほかの M0〜M4・M6 の指定 anchor は各1件でした。先頭一致で置換すると rulings を変異させ、既存 rulings pin の赤を M5 の成功と誤認できます。是正は、`CODEX_NEXT_TASKS_SKILL_LITERALS = (` を含む anchor へ限定することです。

2. **refuted — 予算・literal・guard 引数の不整合、恒真 pin。**
   `tools/check_docs.py:733` の定数と `:6596` の呼出しは一致しています。独立再計数では **23 literal 全件が現物に存在**しました。存在検査なので複数回現れる literal も適合します（`:5250` 付近）。

   | 現物 | bytes（末尾 LF 込み） | 最長行 |
   |---|---:|---:|
   | next-tasks SKILL.md | 5,458 | 223文字 |
   | agents/openai.yaml | 208 | 85文字 |
   | next-tasks command | 26,950 | 83文字 |
   | skill-self-improvement.md | 5,997 | 84文字 |

   YAML は期待定数と bytes 完全一致。5,460 は固定上限であり、現物に3 bytes 足せば超過します。現物から実行時に上限を作る恒真条件ではありません。是正不要です。

3. **refuted — fixture と定数の同時縮小を独立 pin が見逃す。**
   fixture は確かに checker 定数から合成します（`orchestrator/tests/test_check_docs.py:972`）。しかし `:9864` の pin は、期待する2 paths、予算、23 literal、YAML、H3集合を手書きしています。比較右辺は対象定数を参照していません。`TextLimit` 型の利用は期待数値の独立性を損ないません。是正不要です。

4. **real（nit）— 負例 needle はすべて専用ではない。**
   `orchestrator/tests/test_check_docs.py:7605` の YAML needle は既存2 case、`:7606` の adapter needle も既存2 caseと同一です（`:7695`、`:7756`、`:7766`、`:7767`）。byte needle にも既存の一般 needle `bytes > 予算` が含まれます。

   ただし各 case は個別 fixture で baseline=0、変更後の finding=1 を要求します（`:9994`）。現実装の変更先も next-tasks に限定されており、直ちに誤受理する欠陥ではありません。厳密な finding 帰属には、追加2 needleへ対象 path、adapter には欠落 literal も含める方向が適切です。

5. **refuted — 負例が別の理由も同時に発火する／adapter 削除先が違う。**
   合成 SKILL は **686 bytes、最長45文字**。`AGENTS.md` は frontmatter 後の **8行目に1件**で、指定 `replace` 後に欠ける必須 literal はこれだけでした（`orchestrator/tests/test_check_docs.py:7434`）。byte 超過は改行だけで埋めます（`:6479`）。5 case は静的にはそれぞれ H3欠落・byte超過・YAML不一致・literal欠落・未登録fileの1理由に対応します。実走結果は未確認です。

6. **refuted — 裁定外の受理集合変更・commit 混入・数値不一致。**
   実装差分の既存定数変更は `REQUIRED_SELF_HEADINGS` だけで、guard 本体の AST は変更前と同一です。受理条件の変更は、next-tasks H3登録と skill guard登録の2系統です。H3追加は `_SELF_SECTIONS` を通じた段8参照集合にも波及しますが、同じ登録の帰結です（`tools/check_docs.py:877`、`:942`、`:3465`）。

   `wc -c` は command **26,950**を返し、`:2559` の exact pin と一致。docs commit 前後で `$ARGUMENTS` は **0→0**、frontmatter は同一、最長行は **83≤100**。routing も bytes 同一でした。

   実装 commit **`e9a4efeaed3858acd28839f3dacc115a85f91b97`** は指定の実装2 fileだけです。docs commit は **`835a2dc33bea60f6169d008dd6cc00550b1b3145`**。指定された両 diff は対応 commit の差分と一致し、実装2 fileの現物も実装 commit と一致しました。是正不要です。

7. **未確認 — テスト・変異の実走結果。**
   `s5-author.md` は通常テストの開始前拒否と変異未実走を明記しています。本レビューでも pytest・checker・変異は実行していません。以下はコードから導いた失敗箇所であり、観測済みの KILLED 判定ではありません。

## must-fix と nit の振り分け

- **must-fix：M5 anchor の限定。** 放置すると next-tasks の受理集合を変えず rulings を変異させ、別契約の検出を成果として記録する可能性があります。
- **nit：YAML／adapter needle の対象明記。** 放置しても現行5 caseの単一理由性は崩れませんが、同じ文言の別 finding を区別できません。
- **記録上の修正：専属検出と baseline 失敗の区別。** 放置すると M1・M6 の広範な赤を、専用負例が狙った分岐を検出した証拠として過大評価します。
- **実装本体の must-fix：なし。** 静的に確認した範囲では、裁定外の受理条件変更はありません。

## 変異 M0〜M6 の専属性の判定

`PIN` は `test_codex_next_tasks_skill_contract_pins_exact_surface`、`PC[...]` は `test_command_docs_guard_positive_controls[...]` を指します。

| 変異 | anchor件数 | 静的に予測される結果・専属性 |
|---|---:|---|
| M0 | 1 | コメント句読点だけなので等価。SURVIVED予測。実走未確認。 |
| M1 | 1 | PINのH3集合比較で失敗（`:9906`）。PCは孤児H3により **baseline assertion（`:10000`）で先に失敗**。新規pin自体で検出可能ですが、新規nodeだけの赤にはなりません。 |
| M2 | 1 | skill側4 PCが finding消失により変更後rc assertionで失敗。H3削除PCは影響なし。PINは呼出しを検査しないため通過する構造です。 |
| M3 | 1 | PINの予算比較（`:9871`）と `PC[codex_next_tasks_skill_byte_over]` が失敗。指定した新規検査で直接検出できます。 |
| M4 | 1 | PINのYAML比較（`:9900`）で失敗。さらに fixtureも `Next Taskx` になるため、`PC[codex_next_tasks_skill_openai_changed]` の `Next Tasks` 置換が空振りし、変更後rc assertionで失敗します。PINだけの赤ではありません。 |
| M5 | **2** | **意図した tuple を変更した場合**、PINのliteral比較（`:9875`）で失敗。fixtureからもAGENTSが消えるので adapter削除PCは空振りして失敗。先頭一致では rulings を変更し、既存 rulings pinが赤、新規PINは通過するため、その結果はM5の証拠にできません。 |
| M6 | 1 | PINのfile集合比較（`:9867`）で失敗。fixtureはFILESを参照せずYAMLを書き続けるため、**全PCが未登録YAMLによるbaseline失敗**になります。実repoでも同じ未登録実体 finding が出る構造です（`tools/check_docs.py:5178`）。 |

M6では `test_dev_wave_dispatch_accepts_self_all_sections` のように合成repoの正常終了を要求する既存nodeも赤になります（`orchestrator/tests/test_check_docs.py:3702`）。これらを専用PINの検出結果と区別してください。

## 総括

**NO-GO — 変異検証の受入について。** M5 の指定 anchor が2件に一致し、別skillの赤を誤って採用できるため、対象限定が必要です。

実装本体は静的には裁定と整合しています。anchor修正後の変異実走では、新規PINによる直接検出、負例の空振り、baseline失敗を分けて記録してください。テスト・変異の成功は本レビューでは未確認です。
