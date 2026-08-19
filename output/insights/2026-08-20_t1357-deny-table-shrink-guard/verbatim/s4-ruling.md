# [T-1357] 段4 裁定 (親確定・plan v2)

## 所見の裁定

### レンズB
1. (P1) scope選定 (DENY_TABLE限定) — **real (brief正しい)**。採用。role-contract-text/M6本来対象は
   別懸念として worklog へ残す (新チケット起票はしない、次の一手へ記述のみ)。
2. (P2) line151 stale訂正 — **real (brief正しい)**。採用。ただし「無関係な別テスト」は言い過ぎ、
   「現行も loop policy 関連だが bounded loop 通過は固定していない」と worklog では precision を上げる。
3. D96要否 — 推奨A採用: 新Dは必須要件としては起こさない。ただし後述のとおり別動機で1本書く。
4. consumer網羅性 — 見落としなし。確認のみ、追加作業なし。
5. T-1356重複 — 重複なし。確認のみ。
6. superset判定 — 採用 (current ⊇ frozen)。(category, identifier) tuple 構造を維持
   (category移動も検知する「ただ乗り」効果を活かす、裁定パッケージ候補2はA=現plan維持を選ぶ)。

### レンズA
1. 自己参照の実装リスク (意図はrefutedだが実装拘束としてreal) — **採用**。
   frozen literal の RHS を AST 検査する meta-test を追加し、`DENY_TABLE`/`_IDENTIFIER_RULE`/
   `effect_gate`/`RULE_CATEGORY_ALLOWLIST` への Name/Attribute 参照および任意の comprehension を
   構造的に禁止する。
2. カバレッジ数学 — 確認のみ (18+35+18+18+7=96、親が独立に再カウントし一致を確認済み)。
3. superset判定の穴 (構造だけ見て scanner 実動作を見ない) — **採用、設計を差し替える**。
   `current_by_category ⊇ frozen` という構造比較を単体では使わず、
   「frozen の全96 identifier について `scan_host_effects(f"{identifier}();")` を呼び、
   期待 category を持つ finding が実際に出ることを assert する」意味的 probe に置き換える。
   この意味的 probe は構造比較 (identifier が消えれば scan は何も返さない) を内包し、かつ
   `_IDENTIFIER_RULE` 構築や tokenizer 側の破壊も検出するため、レンズAの指摘を根本から閉じる。
   frozen 総数の自己整合 (`sum(...) == 96`) だけは軽量な sanity check として残す
   (DENY_TABLE を参照しない自己完結の検算なので自己参照にはあたらない)。
4. 協調改変 (production + frozen literal を同一 mutation で削る、mutation_harness.py が
   複数ファイル同時変異を実際にサポートしている実測付き) — **real と認定するが、本 wave では
   非 blocking の既知残存として扱う**。理由: (a) 本 wave の直接動機
   (`/dev-wave` 引数の「先頭項だけを潰す」= 単一箇所の局所編集) は採用済みの対策で閉じる、
   (b) 真の M6 対象 (role-contract-text の pin) は (P1) により別懸念として scope 外、
   (c) 暗号的 pin を DENY_TABLE 側にだけ部分導入しても真のリスクは閉じず絶対規律5 (盛らない) に反する。
   段6 で「production から `fork` を削り、同時に frozen literal からも `fork` を削る」協調 mutation を
   追加登録し、**予測 SURVIVED として明記**したうえで実測確認する (隠さず記録する)。
5. frozen literal 改ざん耐性 — 4と同一の残存として扱う。decisions.md への設計記録
   (件数・比較則・既知残存を明記) は書く。ハッシュ pin の新設はしない。
6. P2再検算 — real (brief正しい)、`git show dc87fff7^` / `git show dc87fff7` で親が二重に確認済み。

## plan v2 (確定・段5への指示)

対象: `orchestrator/tests/test_coder_effect_gate.py` のみ。`coder_effect_gate.py` は不変。

1. `_FROZEN_DENY_IDENTIFIERS: dict[str, frozenset[str]]` (category別、5 category・96 identifier、
   親が現物から検算済みの正確な値を作業prompt内に埋め込み、転記誤りを排除する)。
2. 新規テスト: 全96 identifierについて `scan_host_effects(f"{identifier}();")` を呼び、
   期待 category の finding が出ることを assert する意味的 probe (構造比較を兼ねる)。
   加えて frozen 総数 `== 96` の自己整合 sanity check。
3. 新規 meta-test: `_FROZEN_DENY_IDENTIFIERS` 代入の AST を検査し、禁止 Name/Attribute 参照と
   comprehension を拒否する (F42 の自己発掘義務、レンズA所見1の対策)。
4. 既存 `test_each_deny_table_category_has_a_mutation_killing_probe` /
   `test_deny_table_rule_ids_and_identifiers_are_unique` は変更しない (併存)。
5. 新規テスト群の直近に、協調改変 (production + frozen literal 同時編集) は本設計の scope 外の
   既知残存であることを 1-2 行のコメントで明記する。

## 段6 変異事前登録 (最終)

| ID | 対象 | 削除箇所 | 予測 (旧テスト) | 予測 (新テスト) |
|---|---|---|---|---|
| M1 | process-shell | `fork` (production のみ) | SURVIVED | KILLED |
| M2 | file-stdio | `fopen` (production のみ) | SURVIVED | KILLED |
| M3 | network | `socket` (production のみ) | SURVIVED | KILLED |
| M4 | sleep-block-thread | `pthread_create` (production のみ) | SURVIVED | KILLED |
| M5 | escape-hatch | `syscall` (production のみ) | SURVIVED | KILLED |
| M6 | 協調改変 (既知残存の実証) | `fork` を **(a)** production の `DENY_TABLE`、**(b)** test の frozen literal、**(c)** 総数アサーション `96`→`95` の**3箇所すべて**から同時に削除 | SURVIVED | **SURVIVED (予測どおりが合格)** |

M1〜M5 は KILLED を要求する通常の mutation。M6 は「設計の限界を実測で確認する」ための
意図的な mutation であり、SURVIVED が裁定どおりの正しい結果である。
**注記 (段6レンズ1の指摘を受けて明確化):** M6 は (a)(b) の識別子2箇所だけでは不十分である。
`test_frozen_deny_identifiers_total_is_96` が `_FROZEN_DENY_IDENTIFIERS` 自身の内部合計を
`DENY_TABLE` を参照せず検算するため、(c) の総数更新を欠くと合計が95になり、この sanity check が
KILLED を出す (レンズ1・レンズ2が独立に確認)。3箇所すべてを揃えた協調改変だけが
段4裁定どおりの SURVIVED (既知残存) になる。
