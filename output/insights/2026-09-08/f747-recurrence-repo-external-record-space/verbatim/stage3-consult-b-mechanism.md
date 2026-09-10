## 参照実在の照合

結論: 不在 nodeid・実体と無関係な行番号は見つからなかった。

| plan の参照 | 判定 | 現物 |
|---|---|---|
| `tools/check_docs.py:275-289` | 実在 | `TextLimit` は 275–277、`SELF_LIMITS` は 288–290、対象値は 289 の `TextLimit(6_000, 100)` |
| `:743-745` | 実在 | `CODEX_CLEANUP_BRANCHES_SKILL_SHA256 = "268a32ae…d85dea"` |
| `:751-753` | 実在 | `CLEANUP_COMMAND_SHA256 = "b2daf006…61a63"` |
| `:828-839` | 実在 | `REQUIRED_SELF_HEADINGS` は 828–834、`_SELF_SECTIONS` 展開は 835–839 |
| `:5953-5967` | 実在 | UTF-8 byte 数、上限、最長行の検査 |
| `:6352-6372` | 実在 | self-improvement 文書の必須／孤児 H2・H3 検査 |
| `:6535-6544` | 実在 | cleanup skill を `_check_codex_skill_guard` に渡し SHA を検査 |
| `:5193-5200` | 実在 | skill whole-file SHA-256 比較 |
| `:6546-6555` | 実在 | command whole-file SHA-256 比較 |
| `test_check_docs.py:577-708` | 実在 | 独立 SHA 定数と skill／command 全文 fixture |
| `:9742-9772` | 実在 | `test_codex_cleanup_branches_skill_contract_pins_exact_surface` |
| `:9854-9865` | 実在 | skill の 1-byte 変異負例 |
| `:9870-9883` | 実在 | command の 1-byte 変異負例 |
| `hooks/README.md:155-163` | 実在 | repo 外固定発行主体 subtree の拒否契約 |
| `:316-321` | 実在 | 変数展開・script file 越しは不可視 |
| `:402-414` | 実在 | persistent shell、別 process、MCP/apps/plugins、子書込み等の開放面 |
| `:421-437` | 実在 | guard 自身の保守境界。主張核は 421–436、段落末尾は 438 まで |

4 nodeid はすべて一意に実在する。

- `orchestrator/tests/test_check_docs.py::test_codex_cleanup_branches_skill_contract_pins_exact_surface` — 9742
- `…::test_cleanup_command_budget_is_pinned_and_enforced` — 9775
- `…::test_cleanup_skill_one_byte_change_is_rejected` — 9854
- `…::test_cleanup_command_one_byte_change_is_rejected` — 9870

## 所見

### [real] fragment 2 件だけでは、再発を招いた限定表現を残す

根拠は `docs/skill-self-improvement.md:65-66` の逐語である。

> cleanup 本走は共有 command §0/§6 に従い final の候補報告だけで終え、同一実行・継続・自己 spawn では
> repo file/history を変更しない。

前半の「final の候補報告だけ」は十分強い一方、後半が禁止対象を `repo file/history` に限定して見せる。今回の実行者が実際に採った「repo 外ならよい」という読解と同じ軸であり、plan の `plan.md:162,193`「変更なし／fragment 2 件だけ」を壊す。

最小是正は `docs/skill-self-improvement.md:66` の次の置換で足りる。

```diff
-repo file/history を変更しない。
+allowlist 外 state を変更しない。
```

実測上、文書全体は 5993 bytes から 5995 bytes となり、6000-byte 上限内である。checker/test に旧句の逐語複製もない。

成果物影響: cleanup 自己改善の規範的な受理集合から、repo 外の未列挙 mutation を明示的に除外する。

### [refuted] 現行 hook だけで cleanup 限定の memory 拒否を作れる

固定 subtree の先例は実在する。`hooks/guard_write.py:47` と `hooks/guard_bash.py:108` はともに次を module 定数に持つ。

> `_AUTHORITY_ROOT = "/work/1/SFC/tanab/dev-wave-authority"`

ただし、発行主体 subtree は全セッションで AI 書込み禁止にできる領域である。通常時に書込み用途がある memory subtree へ同じ無条件拒否を移すと、正当な memory 利用まで消える。

現行の通常判定が読む context は次だけである。

- `hooks/guard_write.py:421-429`: `tool_name`、`tool_input`、`cwd`
- `hooks/guard_bash.py:2887-2894`: `tool_input.command` と runtime site

`session_id`、`transcript_path`、prompt、cleanup lifecycle marker を取得・使用する実装は `hooks/` にない。raw payload に将来または別 surface の追加 field が存在し得るかまでは、この実装だけでは証明できないが、少なくとも現在の判定核には渡されていない。したがって親 brief `:52-54` と plan `:122` の「現行 hook は cleanup 中かを識別できない」は実装上裏が取れる。

さらに `hooks/README.md:316-321,402-414` により、固定 path を追加しても script、変数展開、persistent process、MCP/apps/plugins、子の別書込み面は閉じない。

成果物影響: 現行 hook への単純な固定 path 追加は、完全防壁にはならず通常時の受理集合だけを過剰に狭める。

### [real] 「別 tool／外側 runner は可能」は現存防壁としては成立しない

`plan.md:123` は無条件に「**可能。**」とするが、成立条件が実装・発火証拠として存在しない。モデル自身が marker 作成や runner 起動を選べるなら、申告しない実行を止められず恒真な gate になる。

防壁として成立する条件はすべて必要である。

1. cleanup lifecycle をユーザー操作または非モデルの trusted launcher が開始・終了する。
2. lifecycle 状態をモデルが作成・変更・省略できない。
3. Bash、Write/Edit、MCP/apps/plugins、子、既存 persistent process を同じ OS-level confinement に入れる。
4. Git refs・worktree metadata・対象 directory の必要 mutation だけを exact allowlist にする。
5. confinement の設置・attestation に失敗したら、最初の破壊操作前に fail-closed で止める。

`hooks/README.md:362-364` も、類似の closure について「今動いている判定器」を確かめる外側実行器が存在しないと明記する。今回の投影資料にも上記条件を満たす cleanup launcher の実体はない。よって「将来の条件付き設計」ではあり得るが、現況の防壁候補としては不能である。

成果物影響: 現行の accepted mutation 集合は一切狭まらず、runtime enforcement 済みとは報告できない。

### [real] F747 の既存再発検知は今回を捕捉しなかった

`docs/failures.md:20256` の逐語は次である。

> 削除 0・罠・検査赤・外側クラス 2 の各終端を判定する。

今回の事象は削除 19 本、罠なし、検査未実行、cleanup 継続中であり、4 終端のどれにも属さない。したがって既存検知が今回を捕捉する能力はなかった。plan の fragment 草案 `plan.md:149` は発生事実だけを書き、この検知漏れを記録していない。

ただし supersede ではない。`docs/failures.md:15-19` は、同型の新規発生を「再発」、記述だけが後続事実で古くなった場合を supersede と区別する。既存行は「4 終端を判定する」という限定的記述として今も真であり、今回必要なのは再発 bullet 内で被覆外だったことを明示することである。恒久対応 `:20255` も実体へのポインタとしてはなお真だが、実効的な閉包ではなかった。

成果物影響: 現草案のままでは failures 台帳が既知の検知漏れを保持せず、再発検知の参照が実態より強く読める。

### [refuted] fragment の形式違反

形式違反はない。

- key 集合・順序: `schema, ledger, authored, wave, seq`
- 再構成 filename: `2026-09-08-dev-wave-f747-recur-20260908-1.md`
- H2/H3: `## 再発`、`### F747`
- 区切り byte: `20 e2 80 94 20`、すなわち半角空白 + U+2014 + 半角空白
- 日付: `2026-09-08`
- plan 内草案: UTF-8、LF、CR なし、bullet 末尾 newline あり

根拠は `docs/spool/README.md:28-49` と `docs/spool/failures/README.md:43-54`。

成果物影響: 形式だけを理由に fragment の受理集合を変える必要はない。

### [refuted] 予算残 7 bytes という実測値

`wc -c` の実測は 5993 bytes。`tools/check_docs.py:288-290` の上限は `TextLimit(6_000, 100)` なので残りは正しく 7 bytes である。

ただし「是正には意味等価な縮約が同時に必要」という brief `:55-56` の推論は誤りである。上記置換後も 5995 bytes で収まる。

成果物影響: 上限変更も checker 変更も不要。

### [real] 「変更なし」のうち成果物の受理集合へ影響するもの

該当するのは `docs/skill-self-improvement.md:66` である。放置すると repo 外 mutation を許すように読める限定が残る。

一方、certified 選択値や report 値を F747 から算出する経路は投影された checker/test/hook にない。canonical `docs/failures.md` は wave で直接編集しないが、land 時の fold により再発 bullet が挿入されるため、最終台帳が永久に「変更なし」という意味ではない。

## 機械検査の可否

| 層 | 判定 | 根拠 |
|---|---|---|
| `check_docs.py` に条文逐語を追加 | 恒真になる | `:5193-5200,6546-6555` は既に whole-file bytes を固定する。実行時不遵守は観測しない |
| `check_docs.py` で live mutation を検出 | 不能 | 入力は文書・fragment 構造であり session の tool event を持たない |
| hook で memory 固定 subtree を全セッション拒否 | 可能 | 発行主体 subtree の先例は `hooks/README.md:155-163`。ただし正常な memory 書込みも拒否する |
| 現行 hook で cleanup 時だけ拒否 | 不能 | `guard_write.py:421-429`、`guard_bash.py:2887-2894` に trusted lifecycle 入力がない |
| モデル自己申告 marker による条件分岐 | 恒真になる | 申告しない実行を同じモデルが選べる |
| trusted non-model launcher + OS confinement | 可能 | 上記5条件を実装・attest した場合だけ。現況には実体なし |
| before/after snapshot | 不能 | 並行 writer の帰属を分離できず、事後検知であって阻止でもない |
| モデル行動 eval | 可能 | 非阻害の回帰観測としてのみ。live 防壁には数えられない |

## fragment 逐語の是正

形式是正は不要。再発検知漏れを記録する意味上の是正だけを加える。

```markdown
---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-f747-recur-20260908
seq: 1
---

## 再発

### F747

- **再発: 2026-09-08** — branch 削除 19 本の完了後、一般的な自己改善許可を別 dev-wave の明示起動と誤読し、cleanup の同一継続内で allowlist 外の repo 外 memory 2 件と `MEMORY.md` を更新した。既存の再発検知が列挙した削除 0・罠・検査赤・外側クラス 2 のいずれにも該当せず、同検知は本再発を捕捉しなかった。
```

supersede 追記は加えない。

## 総括

- 参照行・定数・4 nodeid はすべて実在する。
- fragment の形式は正しいが、既存再発検知が外れた事実を bullet に追加すべきである。
- 「2 fragment だけ」ではなく、`docs/skill-self-improvement.md:66` の限定表現も置換する案を推す。
- 現行 hook に cleanup 限定の trusted context はなく、単純追加は完全防壁にならない。
- 外側 runner は現況では不能。trusted non-model lifecycle と全 write surface の OS confinement を別 wave で実装する場合だけ可能である。
- 段 4 の択一は「2 fragment + self-improvement 1 行是正で本 wave を閉じ、runtime enforcement は未実装と明記」または「上記5条件を満たす別機構 wave を明示起票」である。