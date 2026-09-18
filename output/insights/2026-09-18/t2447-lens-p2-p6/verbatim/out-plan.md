## plan (E ごとに file:line、逐語、byte 差)

E1〜E7 の旧文は現行ファイル内でそれぞれ一意に一致した。UTF-8 の置換部分を再計算した結果、byte 差はすべて親の実測値と一致する。以下の行番号は編集前。コードブロック内部の改行を置換に含み、ブロック末尾の共通改行は変更しない。

**E1 — `docs/dev-wave/workers.md:13`、DW-S03、L1.5、100 → 209 bytes、差 +109。**

置換前:

```text
正しさ境界と整合・実効性を分け、親 brief 自身も検査対象だと明記する。
```

置換後:

```text
正しさ境界・整合と過剰・削除（追加が実測欠陥か研究前進に対応するか、削除・局所修正で
済まないか）に分け、親 brief 自身も検査対象だと明記する。
```

現行13行目はこの旧文の後に `brief の file:line、前提、` が続く。**行全体を置換せず、この部分文字列だけを置換する。** 後続の検査項目を保存する。

**E2 — `docs/dev-wave/workers.md:50–51`、DW-S06-A、L1.5、142 → 169 bytes、差 +27。**

置換前:

```text
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
所見ゼロの扱いは `DW-M02`。
```

置換後:

```text
1 本は `DW-S03` の過剰・削除レンズに固定する。
実装面に Codex `role=author` のないハンクがあればレビューで代替せず停止する。
```

49行目の reasoning pin は独立した行のまま保存する。

**E3 — `docs/dev-wave/workers.md:69`、DW-S06-C、L1.5、125 → 64 bytes、差 −61。**

置換前:

```text
成立した条件の operations と `DW-G05` を適用し、成果物影響を書けない所見を must-fix にしない。
```

置換後:

```text
成立した条件の operations と `DW-G05` を適用する。
```

**E4 — `docs/dev-wave/workers.md:59–60`、DW-S06-B、L1.5、213 → 114 bytes、差 −99。**

置換前:

```text
実装子契約の継承では権限、reasoning/sandbox、テスト弱体化禁止、受理集合、期待赤、波及報告、段 4 の
規模上限を省略せず、超過は所見が閉じても差し戻す。
```

置換後:

```text
実装子契約の継承では段 4 の規模上限も省略せず、超過は所見が閉じても差し戻す。
```

**E5 — `docs/dev-wave/core.md:93`、DW-S04、L1、126 → 235 bytes、差 +109。**

置換前:

```text
scope 外の real 所見は実装せず、設計択一・所見・推奨案を裁定パッケージでユーザーへ返す。
```

置換後:

```text
scope 外の real 所見は実装せず、研究前進か実測欠陥の根拠がある所見だけ設計択一・推奨案付きの
裁定パッケージでユーザーへ返し、無い所見は起票せず insight に記録する。
```

96–97行目の変異免除条件・受入全走義務は変更しない。

**E6 — `docs/dev-wave/core.md:126`、DW-S09、L1、113 → 70 bytes、差 −43。**

置換前:

```text
再試行・停止は `DW-O23` に従い、正式な停止時だけ main HEAD と既存 branch を報告する。
```

置換後:

```text
正式な停止時だけ main HEAD と既存 branch を報告する。
```

**E7 — `docs/dev-wave/operations.md:3–4`、preamble、L1、162 → 92 bytes、差 −70。**

置換前:

```text
発火条件の正本は入口の条件dispatch、成立時の実行手順だけは本書。
該当節を操作直前に読み、停止条件を迂回しない。
```

置換後:

```text
発火条件の正本は入口の条件dispatch、成立時の実行手順だけは本書。
```

DW-O28 は変更しない。

| 層 | 再計算した差 | 親提示の現行値からの着地 | 残余 |
|---|---:|---:|---:|
| L1 | +109 −43 −70 = **−4** | **10,618 / 10,625** | 7 |
| L1.5 | +109 +27 −61 −99 = **−24** | **9,672 / 9,696** | 24 |

置換差は独立に再計算した。層全体の基準値は親の射影値を使用しており、全 reference を対象にした再実測とは区別する。

## D227 照合 (原資ごとに要素対照表)

**E3: 成立。欠落要素なし。**

担い手は `docs/dev-wave/core.md:82–83`、DW-G05:

```text
scope/must-fix は、放置時に成果物（certified 選択・レポート・台帳）の値・受理集合・参照がどう
変わるかを 1 行で示す。示せない must-fix は nit/backlog とし、追加 review を起動しない。
```

| 削減対象の逐語・要素 | 担い手の逐語 | 判定 |
|---|---|---|
| 「成果物影響を書けない」 | 「放置時に成果物…の値・受理集合・参照がどう変わるかを 1 行で示す」「示せない」 | 影響の内容と記述単位まで具体化 |
| 「所見を must-fix にしない」 | 「示せない must-fix は nit/backlog とし」 | 分類変更として包含 |
| 「成立した条件の operations と `DW-G05` を適用」 | E3後も同じ適用義務を保持 | 欠落なし |

同一読点は入口74行目の段6 Uによる DW-G05 必読。縮約後は `DW-G05` への参照だけを残し、must-fix 判定を再掲しない。機械検査を削減理由にしていない。

**E4: 成立。固有の規模上限は削減できないため保持する。**

入口83–84行目:

```text
段 6 で fix を codex へ再投する子は、段 5 の実装子契約 `DW-S05-A`、`DW-S05-B`、`DW-S05-C` を
全文継承する。段 6 時点で成立している全条件の `DW-Oxx`をfix 操作の直前に読む。
```

| 削減対象の逐語・要素 | 担い手の逐語 | 所在 |
|---|---|---|
| 「権限」 | 「権限は入口の凍結境界に従う。」 | workers:29、S05-B |
| 「reasoning/sandbox」 | 「codex は `reasoning=medium`、`sandbox=workspace-write` とする。」 | workers:25、S05-A |
| 「テスト弱体化禁止」 | 「fixture への現行 hash 差し込みなど、テストを甘くして緑にしない（F27）。」 | workers:39、S05-C |
| 同上・期待値変更 | 「xfail 化せず、既存テストの期待値も変えない。」 | workers:30、S05-B |
| 「受理集合」 | 「指示外の受理集合変更をせず、scope 前に現行の受理・拒否挙動を明記する。」 | workers:44、S05-C |
| 「期待赤」 | 「親・他単位の成果物が land するまで意図的に赤になるテストを」「xfail 化せず、既存テストの期待値も変えない。赤の内訳を完了報告に明記する。」 | workers:29–30、S05-B |
| 同上 | 「親 docs が未 land なら期待赤の finding 集合を事前指定し、他は回帰として報告する。」 | workers:45、S05-C |
| 「波及報告」 | 「完了報告に所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。」 | workers:43、S05-C |
| 「省略せず」 | 「全文継承する。」 | 入口:84 |
| 「段 4 の規模上限」「超過は所見が閉じても差し戻す」 | 他の担い手へ移さずE4後にも逐語保持 | workers:59–60 |

同一読点は入口72行目の段6 Uで S05-A/B/C を必読とし、83–84行目で fix 子への全文継承を要求することで成立する。

単一正本化は、削除対象の列挙を S05-A/B/C の契約へ戻す形で成立する。S06-B:62–63 の fix 固有の厳格な期待値禁止は今回の削減対象に含めない。

**E6: 成立。欠落要素なし。**

入口123行目:

```text
段9は `DW-O23` に従い、競合時は再試行する。
```

DW-O23、operations:180–183:

```text
成功は`landed`/`already-landed`だけ。postcondition failureは停止。stale/busyは終了せず、
他sessionの処理中dirtyは非接触で終端を待つ。新main監査、固定SHAのwave-side merge、
条件再評価を既存branchで行いlandedまで再試行する。
他session所有物、rebase、force、remote、pushで解消しない。
```

| 削減対象の逐語・要素 | 担い手の逐語 | 判定 |
|---|---|---|
| 「再試行」 | 「競合時は再試行する」「landedまで再試行する」 | 包含 |
| 「停止」 | 「postcondition failureは停止」「stale/busyは終了せず」 | 停止と継続を具体化 |
| 「`DW-O23` に従い」 | 入口の「段9は `DW-O23` に従い」 | 同じ適用先・同じ段 |
| 「正式な停止時だけ main HEAD と既存 branch を報告する」 | E6後も保持 | 欠落なし |

同一読点は入口81行目で S09 と O23 を段9 Uとして同時必読にすることで成立する。再試行・停止の詳細は O23 に集約される。S09:124 の O23 実行指示も残る。

**E7: 成立。欠落要素なし。**

入口21–23行目:

```text
参照節は command の命令。wave 開始時、段 1〜9 の各段と条件成立操作の直前に条件を再評価して
表の節を読み、前段の推測や F/D 番号の記憶で代用しない。参照先が不在・読取不能・非一意、または
期限までに未読なら、その段・操作へ進まず fail-closed で停止する。
```

入口39行目:

```text
- 規定の停止条件、検査赤、権限・scope・参照不整合を迂回しない。
```

| 削減対象の逐語・要素 | 担い手の逐語 | 判定 |
|---|---|---|
| 「該当節を」 | 「条件を再評価して表の節を読み」 | 条件に対応する節を指定 |
| 「操作直前に読み」 | 「条件成立操作の直前に」＋「表の節を読み」 | 時点・行為とも包含 |
| 「停止条件を迂回しない」 | 「規定の停止条件…を迂回しない」 | 包含し、対象を具体化 |

同一読点は入口の全段・条件操作に対する読み込み契約で成立する。操作契約を入口に集約し、operations preamble の重複を除く。

以上4原資には代替原資を必要とする欠落は見つからなかった。ただし、**「ほかにD227準拠原資がない」とは結論しない。**

E2も削減を含む。削るのは `DW-M02` の参照文のみであり、入口75行目の段6 Uには M02 が残る。M02本文は今回の必読射影にないため、その本文の上位互換性まで独立確認したとは扱わない。

## pin と構造 regex の照合

| 検査・正本 | E1〜E7との関係 |
|---|---|
| `_check_dev_wave_reasoning_effort_pins()`、`DEV_WAVE_REASONING_EFFORT_RE` | E1/E2/E3が検査対象節を編集する。ただし規定値・規定行は保持する |
| `DEV_WAVE_DW_S03_REASONING_XHIGH_LITERAL` | 名前に `XHIGH` が残るが値は **`reasoning=medium`**。S03可視本文の値が `["medium"]`、literalが1件である条件を変更しない |
| `DEV_WAVE_DW_S06_A_REASONING_XHIGH_SENTENCE` | workers:49の独立した完全一致行を保存。E2追加文をこの行へ連結しない |
| `DEV_WAVE_DW_S06_C_REASONING_XHIGH_SENTENCE` | workers:67の独立した完全一致行を保存。E3は69行目だけ |
| `CODEX_FIRST_REFERENCE_LITERALS` | E2の置換範囲に「実装面に Codex `role=author` のないハンク」が含まれるが、置換後にも逐語保持。E4は「親が直接直さない」を保持。coreの2 literalはC00内で編集対象外 |
| `CODEX_AUTHORING_STRUCTURE` | `_check_command_docs_guard()`が入口本文へ適用する。入口34–35行目を変更しないため非接触 |
| `D2_ROLLBACK_STRUCTURE` | 入口25–28行目の期限・invalidate・巻戻し構造が対象。非接触 |
| `D4_FIX_INHERITANCE_STRUCTURE` | 入口83–84行目の全文継承・成立Oxx直前読了が対象。E4の意味的担い手だが、regex対象本文は非接触 |
| `DEV_WAVE_LAND_HELPER`、`DEV_WAVE_LAND_UNIQUE_ROUTE_LITERAL` | E6は同じS09内の別行。S09内のhelper path/literal各1件、coreの節外0件を保持。E7もO23内1件・operations全体1件を変えない |
| `DEV_WAVE_S09_ACCEPTANCE_ORDER_LITERAL` | core:124の完全な受入・監査固定順序を保持 |
| `ALTERNATE_LAND_HELPER_COMMAND`、`DIRECT_MAIN_FF_COMMAND` | 入口への代替land経路を検出する。入口不変であり、新文にも該当commandを追加しない |
| `REQUIRED_REFERENCE_SECTIONS`、`_dev_wave_visible_inventory_is_exact()` | H2を追加・削除・改名しない。節の一意性とdispatch到達性を保持 |
| `_check_dev_wave_model_pins()` | E1〜E7はmodel slug・model正本行を追加、移動、削除しない |
| `_check_dev_wave_layer_budget()` | **全編集がbyte計算に接触する。** E1〜E4はL1.5、E5〜E7はL1。L2節本文は非接触 |

層予算はファイルサイズの単純な分類ではない。`DEV_WAVE_L1_STAGE_KEYS` / `DEV_WAVE_L1_5_STAGE_KEYS` と U のdispatch edgeから節集合を作り、L1との重複をL1.5から除く。残りの登録節をL2とし、`_visible_reference_slices()`による節sliceのUTF-8 bytesを一度ずつ数える。

preambleは、そのファイルにL1節があればL1、なければL1.5へ加算する。このためoperationsのE7はL1原資になる。分類済み節とpreambleが実ファイルの全bytesを被覆することも検査する。上限は `DEV_WAVE_L1_BYTES_MAX=10_625`、`DEV_WAVE_L1_5_BYTES_MAX=9_696`、`DEV_WAVE_L2_SECTION_BYTES_MAX=1_000`。

これらの構造検査の通過は、P2/P6の意味保存を保証しない。

## D1893 との意味差

D1893の採用文は次のとおり。

> 段 3・6 のレンズ 1 本を過剰・削除レンズに固定する案と、研究前進か実測欠陥の根拠が無い範囲外所見は起票せず記録のみとする案を採る

**Q1 / E1。**

- 段3を「正しさ境界・整合」と「過剰・削除」に分けるため、既存の2レンズを置換する意図は一致する。3本目を増設しない。
- 括弧内の「実測欠陥か研究前進」「削除・局所修正」は裁定本文より具体的。削除・局所修正は原典にある。研究前進を追加評価の軸に含めるのも裁定の目的に沿う。
- **旧文の「実効性」は明示されなくなる。** 新レンズは追加の必要性・代替策を問うが、「仕組みが実際に効くか」全般の上位互換とは言い切れない。「吸収される」は親の解釈であり、逐語上の保証ではない。
- 推奨する最小修正は、新文の先頭を **「正しさ境界・整合・実効性と過剰・削除」** とすること。候補E1より+12 bytesで、L1.5は **9,684 / 9,696** に収まる。新しい原資を探さず旧観点を保存できる。

**Q2 / E2。**

- 「1 本は…固定する」はD1893の効力語を直接収容する。詳細をS03へ参照させるため、レンズ定義の二重管理を避ける。
- ただし直前の2本義務は「実装 wave」に限定されている。D1893自体にはこの限定がない。**docs-onlyで段6レビューを行う場合の適用が曖昧**になる。
- 親briefの「段6はreview 1本」も点検が必要。その1本を正しさ側だけにすれば採用した過剰・削除レンズが欠け、過剰側だけにすればもう1本の正しさ境界を保持する不変条件との関係が残る。今回の段6も2レンズにするのが解釈差の小さい運用案。
- S06-Cの焦点再レビューは1本のまま。初回敵対レビューの固定レンズと、fix後の焦点再レビューを区別する解釈は自然だが、D1893本文には区別が明記されていない。段4で解釈を記録する。
- 段6 UはS03を直接指定していない。E2の参照を辿り、レビューpromptの必読射影へS03を含める必要がある。既存checkerはleafからの間接委譲の読了まで保証しない。

**Q3 / E5。**

- 根拠なしのscope外所見を「起票せず…記録する」とする主旨は一致する。根拠は研究前進と実測欠陥のどちらかでよく、両方を要求していない。
- D1893の「範囲外所見」に対し、新文は既存文脈の **real所見** を対象にする。refuted所見まで新たなinsight記録義務を広げない解釈であり、この限定は裁定本文には明示されていない。
- 記録先を **insight** に限定するのは具体化。S07の既存insights記録と整合する。
- 根拠ありの所見は裁定パッケージへ返す。**根拠ありなら自動的に起票してよい、という許可ではない。**
- 旧文の列挙から「所見」は消えるが、「根拠がある所見だけ…返し」として返却対象自体は残る。設計択一・推奨案も保持され、実質的な内容欠落はない。
- **適用時点は段4だけに明示される。** 段6以降に初めて見つかるscope外所見にも同じ裁定を適用する運用が必要。D1893は発見段を限定していない。
- `skill-self-improvement.md` routing:25とdev-wave終端:59は、未裁定・大きい変更等を裁定パッケージへ返す既存命令を持つ。根拠なし所見をそこへ迂回送付すれば「記録のみ」の出口が失われる。段4では、**根拠なしのscope外所見は候補記録に留め、routingを起票・裁定送付の迂回路にしない**と明確化する。安全上の停止や実在の権限待ちまで記録だけに落とさない。

P4の免除条件、変異matrix義務、正しさ・受理・記録の証拠を扱う規律は変更しない。

## 段 5 の手順

1. 親が段3所見を段4で裁定する。特にE1の実効性保持案、段6のレンズ数、P6の後段適用とroutingの関係を確定する。承認済みD1893そのものを再審議する必要はない。
2. 編集直前に旧文の一意一致と所有範囲を再確認する。docs-only本文は親が編集する。
3. 原資E3・E4・E6・E7を先に適用し、その後E1・E2・E5を適用する。E1は部分文字列置換とし、行末の既存検査項目を保存する。位置の変動に備え、固定行番号ではなく旧文の一致で置換する。
4. `git diff --check` と差分を確認する。変更先は3文書のみ、入口・checker・テスト・DW-O28・変異免除条件に差分がないことを確認する。UTF-8差を再集計する。
5. 親環境で `python3 tools/check_docs.py` を実行する。赤は原因を調べ、pinや予算を緩めて通さない。
6. 親が `tools/run_tests.py` 経由で、brief指定の次の2ファイルを実走する。pytestは直接起動しない。

   ```text
   orchestrator/tests/test_check_docs.py
   orchestrator/tests/test_dev_wave_launch_authority.py
   ```

   関連する具体的nodeidは次のとおり。ファイル全走で含まれるため、別途重複実行する必要はない。

   ```text
   orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pins_accept_current_workers_contract
   orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pins_accept_s06_b_inherited_without_literal
   orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_contract_is_literal
   orchestrator/tests/test_check_docs.py::test_normative_exact_section_pins_accept_real_repo
   orchestrator/tests/test_check_docs.py::test_real_repo_clean
   orchestrator/tests/test_dev_wave_launch_authority.py::test_review_effort_matches_independent_docs_cross_check
   orchestrator/tests/test_dev_wave_launch_authority.py::test_fix_effort_matches_author_docs_cross_check
   orchestrator/tests/test_dev_wave_launch_authority.py::test_focus_effort_matches_independent_docs_cross_check
   ```

7. 親の完了検査として `python3 tools/check_codex_agents.py` を実行する。段6で意味差をレビューし、実装面差分ゼロを確認して既存S04に従い変異matrixを免除する。受入全走は免除しない。
8. 段7以降でworklog fragmentと逐語insightを記録し、記録後の検査を実施する。新裁定がなければdecisions fragmentを追加しない。commit後は `python3 tools/check_ai_provenance.py` で監査し、最終受入は記録・段8のcommitを含むtipに対して行う。

本planでは編集、pytest、checker全走、受入を実施していない。

## 段 3 の論点

**A = 正しさ境界・整合**

1. E3/E4/E6/E7のD227照合に抜けがないか。特にfix契約の全文継承と、E1から「実効性」を消す意味を検査する。
2. D1893の段6レンズ固定はdocs-only・焦点再レビューへどう効くか。親briefのreview 1本と不変条件を整合させる。
3. P6は段6以降の所見にも届くか。自己改善routingで起票・裁定送付が復活しないか。pin・層予算・P4不変も確認する。

**B = 過剰・削除**

1. この変更はD1893が挙げた所見から起票への連鎖を実際に止めるか。「研究前進に対応する」の自己申告だけで全件通過しないか。
2. 追加は既存3節の局所変更で足りるか。新しいgate・台帳・検査・レンズの増設を持ち込んでいないか。
3. insight記録が別名のbacklog・自動起票待ちにならないか。根拠なし所見を記録で終える一方、正しさ義務を削減許可へ反転していないか。

## 総括

E1〜E7のbyte差は親の値と一致し、指定された4原資はD227の3条件を満たす。候補どおりならL1は−4、L1.5は−24 bytesで収容できる。

推奨は、E1の正しさ側に「・実効性」を残す最小修正。この場合もL1.5には12 bytesの余裕がある。段4で解消すべき点は、段6のdocs-only／再レビューへのP2適用と、後段・自己改善routingを含むP6の適用範囲。静的照合のみであり、実走結果は親が取得する。