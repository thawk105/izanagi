結論は、P1 の定義自体は採用できますが、親 brief の実測には `DW-O23` の分類漏れがあります。現行 dispatcher に従う正しい値は L1=20,061 bytes、L2=5,137 bytes です。実装案は L1 ceiling=20,200、L2 単節 cap=1,000、L2 節数 cap=14 とします。

実装・ファイル変更・テスト実行は行っていません。以下は静的調査に基づく段 2 plan v1 です。

## provisional 裁定への所見

| 親案 | 判定 |
|---|---|
| P1 | L1 を「段 dispatch の無条件節」とする定義は採用。ただし `.claude/commands/dev-wave.md:75` の `DW-O23` は無条件なので、18,938 という実測は誤り |
| P2 | 独立した手書き L1 集合より、段 dispatch を「無条件」「条件付き」に分け、既存 `STAGE_DISPATCH_CONTRACT` をその和から導出する方が壊れにくい |
| P3 | 単節 cap だけでは節数を増やして無制限にできるため不十分。現行節数 14 の cap も置く |
| P4 | 個別 file cap は撤去。ただし閉包・読取・allowlist 用の path registry は必ず残す |
| P5 | 18,938/1,123 前提は不採用。訂正後の実測から 20,200/1,000/14 を採る |

根拠は [DW-C00](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/docs/dev-wave/core.md:5) の定義と、[段 dispatch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/.claude/commands/dev-wave.md:56) です。段 9 行は `DW-O23` を「成立した条件」「commit するなら」と限定していません。

## 1. 現行 gate の全経路

`main()` は [tools/check_docs.py:3167–3172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:3167) から `_check_command_docs_guard()` を無条件に呼びます。

| 要素 | 定義・読取経路 | finding | pin/test |
|---|---|---|---|
| `REFERENCE_LIMITS` | [175–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:175) で4 fileと個別 capを宣言。`all_limits` へ [2651–2658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2651) で混ぜ、[2685–2691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2685) で個別超過を拒否 | `{rel}: {size} bytes > 予算 {limit}` | `test_dev_wave_reference_limits_pin_adjudicated_caps` [956–962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:956)、個別境界 [1385–1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:1385)、N22 [776–810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:776) |
| `REFERENCE_LIMITS` の閉包用途 | key 集合を expected references に変換する [2590–2600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2590) | 未登録実体 [2601–2605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2601)、登録済み不在 [2606–2611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2606) | `fifth_reference` / `nested_reference` / `non_md_reference` / `registered_reference_deleted` [3709–3731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3709) |
| `REFERENCE_LIMITS` の読取 registry 用途 | `all_limits` に入ることで UTF-8、symlink、regular-file、section、land-helper 検査用 `decoded` を作る [2661–2692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2661) | invalid UTF-8、unsafe/non-regular、必須 H2 欠落・孤児など | `invalid_utf8` / `symlink` / `non_regular` と section positive controls |
| `REFERENCE_LIMITS` の allowlist 用途 | `NORMATIVE_DISPATCH_ALLOWLIST` を [393–395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:393) で構成 | allowlist 外参照を [3048–3055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:3048) で拒否 | `dispatch_allowlist` [3732–3739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3732) |
| `DEV_WAVE_AGGREGATE_BYTES` | [253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:253) で25,200。cap-sum helper と実 byte 合計の双方へ渡る | 合計超過は [2701–2706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2701) の `合計 ... > hard ceiling` | aggregate pin [971–973](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:971)、N22 aggregate、`aggregate_over` meta case |
| `_check_dev_wave_reference_cap_sum` | [2534–2551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2534)、guard 冒頭 [2558–2562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2558) | `個別 cap 総和 ... > aggregate ceiling ... の1.10倍` | reject [976–992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:976)、exact accept [1279–1293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:1279) |
| `DEV_WAVE_REFERENCE_CAP_SUM_MAX_PERCENT` | [257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:257)、比較 [2541–2550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2541) | 上記 cap-sum finding | aggregate pin と110% exact/plus-one tests |

さらに `REFERENCE_LIMITS` はテスト側の `reference_byte_over` [3366–3373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3366)、`aggregate_over` [3715–3717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3715)、living-doc victim 除外 [4330–4334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:4330) でも読まれています。

## 2. 常時読量の決定規則

### dispatch の機械表現

[tools/check_docs.py:423–475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:423) を次の三層に組み替えます。

1. `STAGE_UNCONDITIONAL_DISPATCH_CONTRACT`: 無条件 fragment の pair 集合。
2. `STAGE_CONDITIONAL_DISPATCH_CONTRACT`: 条件付き fragment の pair 集合。
3. `STAGE_DISPATCH_CONTRACT`: 上記二つの stage ごとの和。既存 command 表照合はこれを使い続ける。

これにより、独立した L1 リストを二重管理せず、

```text
registered_pairs = REQUIRED_REFERENCE_SECTIONS の全 (file, section)
unconditional_pairs = 全 stage の無条件 pair の和
L1 = registered_pairs ∩ unconditional_pairs
L2 = registered_pairs - L1
```

と導出できます。同じ節が無条件・条件付きの双方に現れる場合は L1 が勝ちます。

条件付き側へ分けるのは次だけです。

- 段5・段6の「成立した条件の/all operations」
- 段7の `DW-O12/O17/O18/O19`
- 段8の `DW-O04/O17`

段9の `DW-O23` は無条件側です。したがって現在の集合は次になります。

- L1: core 全13節、workers 全8節、mutation 全8節、operations の `O01/O02/O03/O05/O13/O23`
- L2: `O04/O06/O08/O09/O10/O11/O12/O14/O15/O16/O17/O18/O19/O20`
- L1 35節、L2 14節

`.claude/commands/dev-wave.md` 自身は L0、`docs/skill-self-improvement.md` は今回の `docs/dev-wave/**` gate の対象外です。

### 訂正後の実測

| 構成 | bytes |
|---|---:|
| core 全体 | 8,537 |
| workers 全体 | 4,623 |
| mutation 全体 | 3,682 |
| operations preamble + O01/O02/O03/O05/O13/O23 | 3,219 |
| **L1** | **20,061** |
| operations の残り14節 | **5,137** |
| L2 最大 | **DW-O09 = 935** |

親 brief の 18,938 は `DW-O23` の1,123 bytesをL2へ置いた値です。

## 3. 節の byte 切り出し

[既存 scanner](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:936) `_visible_markdown_lines()` を再利用します。これは code fence と複数行 HTML comment をマスクしつつ、原文中の文字 offset と改行を保持します。現在の `_reference_id_sections()` [1667–1677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:1667) は見出しを除いた本文しか返さないため、byte gate には直接使いません。

[tools/check_docs.py:936–989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:936) の直後に raw slice helper を追加します。

切り出し規則は以下で固定します。

- `_safe_read_text(..., newline="")` の原文を対象にし、改行を正規化しない。
- 可視 scanner 上で行頭が `## ` の H2 だけを境界とする。
- preamble は byte 0 から最初の有効 H2 の直前まで。H1、説明、空行、実在する改行を含む。
- 各節は H2 見出し行の先頭から次の有効 H2 の直前、または EOF まで。
- 見出し行とその改行を含む。
- 次見出し直前の空行は前節に含む。
- EOF の末尾改行は実在すれば含み、なければ加算しない。
- Python文字 offsetで原文を slice した後、`len(slice.encode("utf-8"))` で byte 数を出す。
- fenced/commented fake H2 は境界にしないが、その原文 bytes 自体は周囲の実節へ算入する。
- pair は集合として数え、複数段から参照されても同じ節を重複加算しない。
- 全4 fileの preamble は各1回 L1へ算入する。現在は全 file にL1節があることも構造検査で固定する。

現在の raw regex H2 検査 [2769–2787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2769) は、新 helper の可視 inventory を共有するよう置換します。これにより fence/comment 内の偽見出しが必須節や重複を満たしません。

H2が一つもない file は「全体が preamble、節 inventory は空」と返します。main側は既存の必須 H2 欠落 finding を出し、read-budget計算をskipするため、例外や誤った緑にはなりません。

## 4. file:line 実装プラン

1. [tools/check_docs.py:175–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:175)

   `REFERENCE_LIMITS` と4個別 capを削除します。path集合は `DEV_WAVE_REFERENCE_FILES = frozenset(REQUIRED_REFERENCE_SECTIONS)` として [374–392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:374) の直後に置き、section registryとpath registryを一面化します。

2. [tools/check_docs.py:250–257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:250)

   旧 aggregate/cap-sum定数を削除し、次を宣言します。

   ```python
   DEV_WAVE_L1_BYTES_MAX = 20_200
   DEV_WAVE_L2_SECTION_BYTES_MAX = 1_000
   DEV_WAVE_L2_SECTION_COUNT_MAX = 14
   ```

3. [tools/check_docs.py:393–484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:393)

   allowlistを `DEV_WAVE_REFERENCE_FILES` から構成し、stage契約を無条件/条件付きへ分割します。既存 `CONDITION_DISPATCH_CONTRACT` とflatten済み `STAGE_DISPATCH_CONTRACT` の外形は維持します。`DW-O23` がL1であることをliteral testでpinします。

4. [tools/check_docs.py:936–989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:936)

   可視H2とraw sliceを返す helperを追加します。既存の fence/comment scannerを変更せず再利用します。

5. [tools/check_docs.py:2534–2562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2534)

   `_check_dev_wave_reference_cap_sum()` とその早期呼出しを削除し、decoded textと共有section inventoryを受ける `_check_dev_wave_read_budget()` に置換します。

   新 finding は三枝です。

   - `docs/dev-wave/**: 常時読量 (L1) N bytes > ceiling 20200 bytes`
   - `{rel}: {DW-id} N bytes > L2 単節 cap 1000 bytes`
   - `docs/dev-wave/**: L2 節数 N > cap 14`

   加えて、L2 pairが条件付きstageまたはcondition dispatchのいずれにも存在しない場合を registry不整合として拒否します。

6. [tools/check_docs.py:2590–2706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2590)

   `expected_references` を新 path registryから作ります。read loopは `TextLimit | None` のspecにし、dev-wave referencesはcapなしでも必ず `_safe_read_text`・UTF-8・regular-file・`decoded` 対象に残します。command/self/provenanceの既存capには触れません。旧個別超過と合計超過 blockを削除します。

7. [tools/check_docs.py:2769–2787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2769)

   必須・重複・孤児H2検査を新しい可視 inventoryへ移します。section構造が完全な4 fileだけをread-budget計算へ渡します。

8. [orchestrator/tests/test_check_docs.py:347–497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:347)

   synthetic dispatch生成を新しいflatten契約へ追従させます。reference本文生成は引き続き `REQUIRED_REFERENCE_SECTIONS` から行います。

9. [orchestrator/tests/test_check_docs.py:3357–3881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3357)

   positive-control matrixの `reference_byte_over` / `aggregate_over` を `l1_byte_over` / `l2_section_byte_over` / `l2_section_count_over` へ置換します。閉包・unsafe-file・allowlist caseは維持します。

10. [orchestrator/tests/test_check_docs.py:4330–4334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:4330)

    living-doc victim除外を新 path registryへ切り替えます。

docs本文とcommand表は変更しません。

## 5. L2 の規律と予算値

| gate | 値 | 現行 | headroom |
|---|---:|---:|---:|
| L1 ceiling | 20,200 | 20,061 | 139 bytes、0.69% |
| L2単節 cap | 1,000 | 最大935 | 65 bytes、6.95% |
| L2節数 cap | 14 | 14 | 0節 |

単節capだけでは `999 bytes × 無制限の節数` が可能です。節数を現行14で固定することで、L2 unique bytesの理論上限は14,000 bytesになります。新節を追加する場合はcount cap変更を独立審査する必要があります。

これは予算値の引上げではありません。

- 旧25,200 aggregateを、より直接的な20,200 L1 ceilingへ置換する。
- 1,000は新しいL2単節軸であり、旧個別file capより小さい。
- 節数は現行値に固定し、増枠していない。
- L2総量の受理拡大は、ユーザーが採用した「総量ではなく常時読量を制約する」択(a)そのものです。

## 6. テストの削除・置換・新設

### 既存テスト

| 現行テスト | 変更 |
|---|---|
| `test_dev_wave_reference_limits_pin_adjudicated_caps` | exact path registry、新3定数、L1/L2 exact pair集合のpinへ置換 |
| `test_dev_wave_reference_budget_pins_cap_sum` | 削除。L2節数14のpinへ置換 |
| `test_dev_wave_reference_budget_pins_aggregate_ceiling` | L1/L2/count定数pinへ置換 |
| `test_dev_wave_reference_cap_sum_rejects_above_110_percent` | 削除。L2 count capを13へ下げると現行14節が一 findingで赤になるtestへ置換 |
| `test_dev_wave_reference_cap_sum_accepts_exactly_110_percent` | 削除。現行14節がcount cap exact boundaryで通る正例へ置換 |
| `test_dev_wave_reference_limit_accepts_exact_boundary` | L1およびL2単節の `limit-1 / limit / limit+1` parameterized testへ置換 |
| `test_dev_wave_reference_limit_rejects_plus_one` | 上記へ統合 |
| `test_raised_doc_budgets_still_reject_each_new_limit_and_aggregate` | dev-wave部分を削除。rulings command capの検査だけを別名で残す |

### 新設テスト

- `test_dev_wave_read_layer_pins_exact_pairs`

  L1 operationsが `{O01,O02,O03,O05,O13,O23}`、L2が残り14節であることを独立literalでpinします。

- `test_dev_wave_l1_budget_boundary_minus_one_exact_plus_one`

  L1=20,199/20,200は受理、20,201はL1 finding exact 1件。

- `test_dev_wave_l2_section_budget_boundary_minus_one_exact_plus_one`

  1節=999/1,000は受理、1,001はL2単節 finding exact 1件。見出し行・末尾改行を含む独立byte helperで作ります。

- `test_dev_wave_read_budget_distinguishes_l2_growth_from_l1_growth`

  同じbaselineをL1=20,200にし、一方はL2へ1 byte追加して受理、もう一方はL1へ1 byte追加して拒否。両repoの総増分が同じ1 byteであることもassertします。

- `test_dev_wave_l2_section_count_boundary`

  現行14は受理。copied checkerのcapだけを13にするとcount finding exact 1件。

- `test_dev_wave_l2_registry_rejects_unreachable_section`

  tinyな登録H2を追加するが条件dispatchへ載せず、count capは15にしてmaskを外す。registry不整合だけを拒否。

- `test_dev_wave_section_slicer_ignores_fenced_and_commented_h2`

  fenced `## DW-O09` とHTML-commented同見出しを入れても、実H2はexact 1件で正例。

- `test_dev_wave_headingless_reference_fails_closed_without_traceback`

  referenceをH2なし本文へ置換し、必須H2 findingは出るが例外・budget誤診断を出さない。

`_build_min_repo()` は実際には節見出しを持っています。[`_write_command_guard_docs()` の479–497行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:479) が全 `REQUIRED_REFERENCE_SECTIONS` をH2として生成し、[_build_min_repo:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:648) から呼ばれます。既存 `_pad_to_bytes()` [3330–3334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/orchestrator/tests/test_check_docs.py:3330) も見出しを消さず末尾改行を足すだけです。したがって「見出しなし」は専用負例として新設します。

## 7. 受理集合の変更

| 入力 | 旧gate | 新gate |
|---|---|---|
| 現行repo: total=25,198、L1=20,061、L2最大935 | 緑 | 緑 |
| 現行 `DW-O09` に2 bytes追加: total=25,200、O09=937 | 境界で緑 | 緑 |
| 現行 `DW-O09` に3 bytes追加: total=25,201、O09=938 | aggregateで赤 | L1不変・L2≤1,000なので緑 |
| 現行 `DW-O04` に45 bytes追加: operations=8,401 | 個別file capとaggregateで赤 | O04=245、L1不変なので緑 |
| 合成repo: L1=20,201、L2=4,000、total=24,201。file内訳9,000/4,500/3,500/7,201 | 旧全cap内で緑 | L1超過で赤 |
| 合成repo: total十分小、1個のL2節だけ1,001 bytes | 旧file/aggregate内で緑 | L2単節超過で赤 |
| dispatch/registryを整合更新したtinyなL2節15個 | 旧byte gateは緑 | L2節数超過で赤 |

最後の二行が、置換後に新たに狭まる受理集合です。最初のL2増分二例が、ユーザー裁定により意図的に広がる受理集合です。

## 8. 段4用の変異事前登録候補

未実装なので、位置は現行コードの置換anchor、`old` は実装時に固定すべき予定逐語です。

1. **M1 L1比較の無効化** — anchor [tools/check_docs.py:2701–2706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2701)  
   old: `if l1_bytes > DEV_WAVE_L1_BYTES_MAX:`。条件を恒偽化。L1=20,201 fixtureでは閉包・H2・L2が全て適法で、旧個別/aggregate検査も撤去済みなので、手前の拒否はない。plus-one testのrc期待だけが赤になる。

2. **M2 L2単節比較の無効化** — anchor [2534–2551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:2534)  
   old: `if section_bytes > DEV_WAVE_L2_SECTION_BYTES_MAX:`。恒偽化。対象1節=1,001、L1/count正常なので手前の拒否なし。L2 plus-one testだけが赤。

3. **M3 L2節数比較の無効化** — 同anchor  
   old: `if len(l2_pairs) > DEV_WAVE_L2_SECTION_COUNT_MAX:`。恒偽化。test側でcopied capのみ13にし、現行14節・全byte正常とするため、count finding以外は発火しない。

4. **M4 条件到達性検査の無効化** — anchor [tools/check_docs.py:423–484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:423)  
   old: `if unreachable_l2_pairs:`。恒偽化。登録済みtiny H2を1個追加、count capを15にし、必須H2/孤児/byteを全て成立させるので、手前の同入力拒否はない。

5. **M5 `DW-O23` のL1帰属を落とす** — 同anchor／read-budget helper  
   old: `l1_pairs = registered_pairs & unconditional_pairs`。結果からO23だけをsubtract。O23=1,000、他L1=19,201として元実装だけが20,201で拒否する。誤ってL2化したmutantでも単節cap内なのでmaskされない。

6. **M6 preamble算入を落とす** — read-budget helper anchor  
   old: `l1_bytes = sum(len(parts[rel].preamble.encode("utf-8")) for rel in DEV_WAVE_REFERENCE_FILES)`。0へ変異。節本体合計をceiling以下、preamble込みだけ20,201にするため、他gateは拒否しない。

7. **M7 fence/comment maskを外す** — parser anchor [tools/check_docs.py:936–980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget/tools/check_docs.py:936)  
   old: `for visible, offset, newline in _visible_markdown_lines(text):`。raw行scanへ変異。小さいfenced/commented同IDを入れ、mutantだけが `H2 ... 2件` の一 findingを出す。byte上限には十分余裕を持たせる。

8. **M8 UTF-8 byte計数を文字数へ弱化** — read-budget helper anchor  
   old: `len(raw_section.encode("utf-8"))` を `len(raw_section)` へ変異。日本語を含むraw sectionを1,001 bytesかつ1,000文字未満に作るため、構造・L1・countは正常で、L2境界testだけが赤になる。

これらはすべて `_build_min_repo()` のregular UTF-8・exact H2・正規dispatchを土台にし、対象分岐以外のfindingが出ないことを `_finding_set()` exact一致で固定する計画です。

## 総括

- P1の定義は採用するが、`DW-O23` は無条件段9参照なのでL1へ訂正する。
- 正しい現行値はL1=20,061、L2=5,137、L2最大=935、L2節数=14。
- 予算案はL1=20,200、L2単節=1,000、L2節数=14。
- 個別file cap・aggregate・cap-sumは削除し、閉包・読取・allowlist registryは維持する。
- section抽出は既存可視Markdown scannerを使い、見出し・原改行・UTF-8 bytesを厳密に数える。
- docs本文は変更せず、`tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` のみを実装面とする。
- テストは未実行であり、緑は主張しない。