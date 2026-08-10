## 現行実測

| 対象 | 現在値 | 新上限・変更後見込み |
|---|---:|---:|
| `.claude/commands/dev-wave.md:1-118` | 9,457 / 9,500 bytes、最長 137 / 140 chars (`:66`) | 後述の `U/C` 化・P3/P4反映後 9,442 bytes、最長139 chars。余白58 bytes / 1 char |
| `docs/dev-wave/core.md:1-124` | 8,655 bytes | file cap撤廃 |
| `docs/dev-wave/workers.md:1-69` | 4,526 bytes | file cap撤廃 |
| `docs/dev-wave/mutation.md:1-57` | 3,689 bytes | file cap撤廃 |
| `docs/dev-wave/operations.md:1-132` | 8,329 bytes | file cap撤廃 |
| 4冊合計 | 25,199 bytes | aggregate cap撤廃 |

| 層 | 現行・P3/P4後とも | 構成 |
|---|---:|---|
| L1 | 10,625 bytes / 15節 / 余白0 | core全13節、`DW-M01`、`DW-O23`、core/mutation/operationsのpreamble |
| L1.5 | 9,566 bytes / 20節 / 余白0 | workers全8節、`DW-M02`〜`M08`、`DW-O01/O02/O03/O05/O13`、workersのpreamble |
| L2 | 5,008 bytes / 13節 | `DW-O04/O06/O08/O09/O10/O11/O12/O14/O16/O17/O18/O19/O20`。最大 `DW-O09`=935 bytes |

## A. 層分類の機械束縛

### marker方式の択一

| 入力差 | 日本語修飾regex | 明示 `U/C` marker |
|---|---|---|
| 現行の修飾語を維持 | 受理可能 | 移行後に受理 |
| 同義語へ言い換え | exact regexなら赤、緩いregexなら誤分類余地 | marker不変なら緑。自然言語と分類を分離 |
| 修飾語だけ削除 | typed期待値との照合を別途書けば赤。ただし句境界解析が必要 | `C→U` またはmarker欠落として直接赤 |
| 1行中に無条件・条件付きが混在 | `:75` のfragment境界を日本語で解析する必要 | 同一行を禁止し、`U` 行と `C` 行へ分割 |
| 2列行・未知marker | regex方式では従来どおり受理し得る | fail-closedで赤 |

明示 `U/C` markerを採る。

- `.claude/commands/dev-wave.md:59-78`: `種別は U=無条件、C=条件 dispatch 成立時。` を追加し、表を3列化する。mode cellだけを `|U|` / `|C|` と詰め、140 charsを守る。
- `.claude/commands/dev-wave.md:69,74`: 日本語修飾を削り、それぞれ `C` 行にする。
- `.claude/commands/dev-wave.md:75`: `DW-S07` の `U` 行と operations 4節の `C` 行へ分割する。
- `.claude/commands/dev-wave.md:77`: `DW-O04` を落とし、`DW-O17` だけの `C` 行にする。
- 全参照行にexact 1個の `U` または `C` を要求し、欠落・未知値・1行内混在を受理しない。

### checker側

1. `tools/check_docs.py:498-550`

   `STAGE_DISPATCH_CONTRACT` の手書き一面を以下へ分割する。

   - `STAGE_UNCONDITIONAL_DISPATCH_CONTRACT`
   - `STAGE_CONDITIONAL_DISPATCH_CONTRACT`
   - `STAGE_DISPATCH_CONTRACT`: 上二面をstageごとに和集合して機械導出する互換view

   `wave 開始` の無条件集合から `DW-CTX`、段8の条件集合から `DW-O04` を除く。段9の `DW-CTX`、段5/6の `_ALL_OPERATIONS` は残す。

2. `tools/check_docs.py:551-560`

   `CONDITION_DISPATCH_CONTRACT` のpair集合は維持する。併せて条件表第2列の現行逐語を持つ `CONDITION_TRIGGER_CONTRACT` を追加し、`.claude/commands/dev-wave.md:87-109` の「常に」等への書換えも拒否する。

3. `tools/check_docs.py:1714-1719`

   `_DispatchTables` を `stage_unconditional`、`stage_conditional`、`condition_triggers`、不正mode行へ拡張する。従来のflatten済み `stages` は両typed mapから導出する。

4. `tools/check_docs.py:3202-3246`

   `_dispatch_tables()` は段表の第2 cellをexact `U/C` として読む。参照を持つのにmodeがない行、未知mode、同一行の混在は不正として保持し、無条件へfallbackしない。条件表では第2 cellも保存する。

5. `tools/check_docs.py:4033-4073`

   actual/expected双方のkey和集合について、無条件map、条件付きmap、flatten map、condition pair、condition trigger、row countを照合する。片側にしかないkey/pairも必ず finding にする。

6. `tools/check_docs.py:449-467,4033-4073`

   `registered_pairs` と、段U・段C・条件dispatchから得たdev-wave pairの和を双方向照合する。未到達登録節と未登録dispatch節を双方拒否する。

7. 層導出規則は `L1_KEYS={wave開始,1,4,7,8,9}`、`L1_5_KEYS={2,3,5,6}` としてliteral pinする。優先順位は `L1 > L1.5 > L2`。同一節がU/C双方にあればUが勝ち、L1/L1.5双方のUにあればL1が勝つ。

これにより、commandだけの変更はtyped contract差、checker定数だけの変更は実表との差、registryだけの変更は到達性差で赤になる。flatten contractはtyped二面から導出するため、第三の手編集経路を持たない。

## B. 予算の置換

| 現行箇所 | 判断 | 実装 |
|---|---|---|
| `tools/check_docs.py:176-181` `REFERENCE_LIMITS` | 置換 | 削除し、`REQUIRED_REFERENCE_SECTIONS` から導く `DEV_WAVE_REFERENCE_FILES` に置換 |
| `tools/check_docs.py:254` `DEV_WAVE_AGGREGATE_BYTES` | 置換 | `DEV_WAVE_L1_BYTES_MAX=10_625`、`DEV_WAVE_L1_5_BYTES_MAX=9_566`、`DEV_WAVE_L2_SECTION_BYTES_MAX=1_000` |
| `tools/check_docs.py:258` cap-sum percent | 消す | L2 aggregateを持たない裁定と両立しないため削除 |
| `tools/check_docs.py:3416-3433` cap総和検査 | 消す | 関数ごと削除し、層予算helperを置く |
| `tools/check_docs.py:3561-3565` cap総和呼出し | 消す | typed dispatch検証後の層予算呼出しへ移す |
| `tools/check_docs.py:3704-3709` aggregate検査 | 消す | 25,200比較を完全撤去 |
| `tools/check_docs.py:3654-3703` 個別cap/read loop | 置換 | bounded文書のlimit mapと全読取path集合を分ける。dev-wave 4冊はcapなしでもUTF-8・regular-file・symlink・decoded対象に残す |

### registry・allowlist

- `tools/check_docs.py:449-470`: `DEV_WAVE_REFERENCE_FILES = frozenset(REQUIRED_REFERENCE_SECTIONS)` とし、`NORMATIVE_DISPATCH_ALLOWLIST = DEV_WAVE_REFERENCE_FILES | frozenset(SELF_LIMITS)` にする。`docs/skill-self-improvement.md` はallowlistに残る。
- `tools/check_docs.py:3593-3614`: `expected_references` のsourceだけを新registryへ替え、再帰 `rglob("*")`、extra/missing、symlink/non-md検出は維持する。
- `orchestrator/tests/test_check_docs.py:4587-4617`: `fifth_reference`、`nested_reference`、`non_md_reference`、`registered_reference_deleted`、`dispatch_allowlist` の既存正例を維持し、finding文言だけ「層予算registry未登録」へ追従させる。

### 節byte計測

- `tools/check_docs.py:1743-1752` の近傍にraw slice helperを追加するが、既存 `_reference_id_sections()`、`_visible_markdown_lines()` (`:890-1074`)、既存H2検査 (`:3788-3807`) は変更しない。
- 境界は原文の行頭 `## ` のみ。見出し行・原改行・次のH2直前までを節へ含め、`newline=""` で読んだsliceをUTF-8 encodeして数える。
- preambleは、そのfileに存在する最優先層へ1回だけ算入する。L2節しかない将来fileでは、無上限preambleへの逃がしを防ぐためL1へ算入する。
- 全slice+preambleの和が4冊実byte合計と一致することを内部不変条件にする。
- L1/L1.5だけaggregate比較し、L2は各節1,000 bytes比較のみ。節数・L2合計は計測値として得ても拒否条件にしない。

## C. `DW-CTX` / `DW-O04`

| 節 | 編集 | 到達性と分類 |
|---|---|---|
| `DW-CTX` | `.claude/commands/dev-wave.md:63` のwave開始行から削除 | `:78` の段9 U行、`:106-107` の条件21/22、入口冒頭 `:16-17` が残る。`REQUIRED_REFERENCE_SECTIONS` (`tools/check_docs.py:449-454`) も維持。段9Uにより878 bytesはL1のまま |
| `DW-O04` | `.claude/commands/dev-wave.md:77` の段8 C行から削除 | 条件04 `:90`、段5/6 C行 `:69,74`、`_OPERATION_NUMBERS` (`tools/check_docs.py:425-428`) が残る。200 bytesはL2のまま |
| 本文 | `docs/dev-wave/core.md:114-124`、`docs/dev-wave/operations.md:27-30` は分割・移動しない | 新ID・consumer更新を発生させない |

`docs/dev-wave/core.md:7-10` は現状「L1=全段の無条件節」でL1.5を表現していない。既存3行合計312 bytesを維持するbyte-neutralな文言置換で、`L1=U常時段`、`L1.5=Uクラス依存段`、`L2=条件節`へ修正する。`DW-C00`=1,059 bytes、core=8,655 bytes、L1=10,625 bytesを動かさない。

L2剪定規範は既に `docs/skill-self-improvement.md:30-33` にあるため変更せず、発火実績検索や義務代替判定の機械化は本waveへ追加しない。

## D. テスト変更

実行したgrep結果:

```text
1648:    assert check_docs.REFERENCE_LIMITS["docs/dev-wave/core.md"].max_bytes == 9_600
1649:    assert check_docs.REFERENCE_LIMITS["docs/dev-wave/operations.md"].max_bytes == 8_400
1650:    assert check_docs.DEV_WAVE_AGGREGATE_BYTES == 25_200
1826:    assert check_docs.REFERENCE_LIMITS == {
1836:        limit.max_bytes for limit in check_docs.REFERENCE_LIMITS.values()
1841:    assert check_docs.DEV_WAVE_AGGREGATE_BYTES == 25_200
2358:    assert check_docs.PROVENANCE_REFERENCE_LIMITS == {
2419:        set(check_docs.PROVENANCE_REFERENCE_LIMITS)
3015:            "PROVENANCE_REFERENCE_LIMITS",
3017:                **module.PROVENANCE_REFERENCE_LIMITS,
4239:            check_docs.REFERENCE_LIMITS[
4594:        for rel, limit in check_docs.REFERENCE_LIMITS.items():
6273:            *check_docs.REFERENCE_LIMITS,
```

| 現行行 | 書換え |
|---|---|
| `orchestrator/tests/test_check_docs.py:1645-1679` | dev-wave個別/aggregate部分を除去し、rulings command capのN22だけ残す |
| `:1825-1842` | 旧3 pinを、4-file registry、新3予算、L1/L1.5 stage key、15/20/13 exact layer pairのliteral pinへ統合 |
| `:1845-1861,2148-2162` | cap-sum 110%の赤/境界緑テストを削除。別軸への名目置換はしない |
| `:2254-2321` | 4 file境界をL1/L1.5/L2単節のexact/plus-one parameterへ書換え、`id="l1"`, `"l1_5"`, `"l2_section"` を固定 |
| `:4235-4242,4593-4595,4622-4761` | `reference_byte_over` と `aggregate_over` のmatrix case・needleを削除。新境界テストと重複させない |
| `:432-510` | synthetic段表をtyped U/C contractから生成し、mixed行を作らない。条件表第2列もtrigger contractから生成 |
| `:4783-4824` | 段5/6のC集合、段9のU `DW-O23`、`DW-CTX` L1、`DW-O04` L2をliteral pin |
| `:6273` | living-doc victim除外を `DEV_WAVE_REFERENCE_FILES` へ変更 |
| `:2358,2419,3015-3017` | provenance固有の別定数なので変更しない |

純増検出力は次の二系統だけにする。

- `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l1]`: 各旧file cap内かつ旧total≤25,200のfixtureでL1だけ10,626 bytesにし、新L1 gateだけが拒否する。既存plus-oneテストの書換えとして置く。
- `orchestrator/tests/test_check_docs.py::test_dev_wave_dispatch_conditionality_retyping_is_rejected[...]`: flattened pair集合を不変に保ったまま、`stage-u-to-c`、`stage-marker-missing`、`condition-always` を試し、typed/trigger差だけで拒否する。既存の「pair削除」positive controlとは重ならない。

L1.5/L2のexact・plus-oneは旧境界テストの置換であり、追加のmatrix caseを作らない。テスト側のbyte生成はproduction helperを呼ばず、対象節へ直接payloadを挿入し、生成後のlayer/file/total値を独立assertする。

## E. 段4向け変異候補

| # | 変異 | KILL node |
|---|---|---|
| M1 | L1比較を恒偽化 | `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l1]` |
| M2 | L1.5比較を恒偽化 | `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l1_5]` |
| M3 | L2単節比較を恒偽化 | `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l2_section]` |
| M4 | typed U/C照合を除きflatten集合だけ比較 | `orchestrator/tests/test_check_docs.py::test_dev_wave_dispatch_conditionality_retyping_is_rejected[stage-u-to-c]` |
| M5 | mode欠落を不正とせずUへfallback | `orchestrator/tests/test_check_docs.py::test_dev_wave_dispatch_conditionality_retyping_is_rejected[stage-marker-missing]` |
| M6 | 条件表第2列のexact trigger照合を除去 | `orchestrator/tests/test_check_docs.py::test_dev_wave_dispatch_conditionality_retyping_is_rejected[condition-always]` |
| M7 | preambleをL1/L1.5合計から除外 | `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l1]` |
| M8 | UTF-8 byte数をPython文字数へ弱化 | `orchestrator/tests/test_check_docs.py::test_dev_wave_layer_budget_rejects_plus_one[l2_section]`。fixtureを1,001 bytesかつ1,000文字以下にする |

全候補にKILL nodeを特定できる。各fixtureでは他層を上限未満に置き、同入力を先に拒否するmaskがないことを固定する。

## 受理集合の変更

### 広がる集合

| 入力 | 旧 | 新 |
|---|---|---|
| 現行 `DW-O04` に72 bytes追加（operations=8,401、全体=25,271、O04=272） | file cap/aggregateで赤 | L1/L1.5不変、L2単節≤1,000で緑 |
| file間でbyteを移し、各層上限を守るが旧file capを超える | 赤 | 緑 |
| L2節を各1,000 bytes以下で追加し、registry/dispatchも整合更新 | aggregate超過で赤 | 節数・L2合計上限がないため緑 |
| 条件行の日本語を言い換えるがU/Cとtrigger pinを変更しない範囲 | regex依存なら赤 | marker分類は不変 |

### 狭まる集合

| 入力 | 旧 | 新 |
|---|---|---|
| 現行L1へ1 byte追加（全体25,200、file cap内） | 緑 | L1=10,626で赤 |
| L1.5へ1 byte追加し、別層を1 byte縮小 | 緑 | L1.5=9,567で赤 |
| 合計/file cap内だがL2の1節が1,001 bytes | 緑 | L2単節capで赤 |
| 2列段表、未知mode、U/C欠落、mixed-mode行 | pair集合が合えば緑 | 構造赤 |
| 条件triggerを同じpairのまま「常に」等へ変更 | 緑 | trigger contract差で赤 |
| wave開始へ`DW-CTX`、段8へ`DW-O04`を再追加 | 現行契約では緑 | typed stage contract差で赤 |

## F. 段4で親へ返す設計択一

| 論点 | 推奨 | 裁定が変わる場合 |
|---|---|---|
| L1/L1.5余白ゼロ | 承認済み「現在値で凍結」どおり0を採用 | 1 byteでも余白を置くなら受理拡大なのでユーザー再裁定 |
| L0 command / self doc | 本waveの層合計から除外し、既存個別capだけ維持 | 現在9,457+5,997=15,454 bytes。合成gateには「selfのどの節を常時と数えるか」の追加裁定が必要 |
| L2節数cap | 置かない | 置く場合の唯一の現在値根拠は13節だが、単節capのみという裁定より狭いため再裁定が必要 |
| `DW-CTX`本文分割 | 行わない | 無人段落を新IDへ分けるなら条件21/22、registry、dispatch、byte baselineを一括再裁定 |
| `DW-C00`のL1.5記述 | 312-byte byte-neutral置換を採る | docs本文を「位置修正のみ」に厳密限定するならlive定義がstaleになるため、実装前に親裁定が必要 |
| L2剪定の機械化 | 行わず `docs/skill-self-improvement.md:30-33` の人間・敵対監査規範に残す | 発火実績索引や義務代替証明のschemaは別wave |

## 総括

- 実装順は、commandのU/C化と位置修正 → typed/trigger contract → registry・raw節計測 → 層予算 → test置換。
- `REFERENCE_LIMITS`、25,200 aggregate、cap-sum検査を撤去し、10,625 / 9,566 / L2単節1,000へ置換する。
- `DW-CTX`は段9UによりL1、`DW-O04`は条件dispatchによりL2のままで、到達不能節は生じない。
- 最大riskは、余白ゼロのlive docs定義とtyped表・checker・literal testの三面driftである。