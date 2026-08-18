# 段 4 裁定 — [T-396] 裁定 A/B の実装

2026-08-18 13:25 JST / 基準 main = `a160f4aa`

段 3 は 2 レンズとも NO-GO。所見を裁定し、プラン v2 を確定する。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A1 | 第 3 bullet の「説明を `justification` へ置く」義務を「完全機械執行」と誤分類 | **real** | 採用 | 内 |
| A2 | 置換案が「内部で処理された例外送出」の禁止を落としている | **real** | 採用 | 内 |
| A3 | 「auditor が拒否する」が auditor 契約へ結線されていない | **real** | 採用 (文言) | 内 + **外** |
| A4 | caller 閉包に S6 / freeze 再実体化が欠ける (ただし live bypass なし) | **real** | 採用 (記録義務) | 内 |
| A5 | (P3) 親の adapter 代行は D95 違反 | **real** | 採用 | 内 |
| B1 | 機械非検査項目が live prompt として許可に読まれうる | **real** | 採用 (前置文) | 内 |
| B2 | = A5 | **real** | 採用 | 内 |
| B3 | pin は bytes の同一性しか証明しない | **real** | 採用 (記録義務) | 内 |
| B4 | B は 5 件の過剰拒否検出力を失う | **real** | 採用 (記録義務) | 内 |
| B5 | C / D の親判断は正しい | 確認 | — | — |
| B6 | D23 / D96 / D344 と衝突なし | 確認 | — | — |
| P0 | **(親所見)** 置換案が回避条件を逐語で書いており D48 偵察 firewall と衝突する | **real** | 採用 | 内 |

**refuted は 0 件。** 両レンズが独立に A5/B2 を must-fix にした点を重く採る。

## 2. 親の誤りの訂正

- **(P1) は粗すぎた。** 「5 項目とも未執行」ではなく、完全執行 4 / 部分執行 4 / 非執行 2
  (原子的義務の粒度)。bullet 5 件と原子的義務を同一視したことが A1・A2 の原因である。
- **(P3) は撤回する。** D95 決定 (3) 「Codex が利用不能なら親が代筆せず、停止してユーザー裁定へ
  返す」(`docs/decisions.md:4258-4259`) が正本。前例 (T-428) は裁定済み waiver ではない。
- brief が権限根拠に挙げた D149 決定 6 は無関係だった (レンズ A・段 2 が独立に反証)。

## 3. プラン v2 — A の置換設計 (段 2 案を差し替える)

段 2 の「禁止文を gate の言葉へ書き直す」形は採らない。A2 (禁止の脱落) と P0 (回避条件の開示) が
その形に固有の危険だからである。代わりに **禁止 5 bullet を 1 byte も変えずに残し、
執行主体の分類を後置する**形とする。これで「禁止を 1 つも撤回しない」が diff で機械的に保証される。

### 3.1 変更する見出し行

現行の見出しは「hook が機械執行する部分と auditor が目視する部分の併用」と書くが、
hook は designated source への**書込面**しか見ず内容を検査しない (レンズ A の gate 表)。
この記述自体が実態より広い主張なので、`(D23 道Y)` だけに縮める。

### 3.2 節の形 (実装子への指示)

```
**Closed-region 制約 (D23 道Y):** 次はすべて生成時に守る**必須禁止**である。
後述の執行範囲は誰が検査するかの分類であり、機械が検査しないことは許可を意味しない。

  (現行 5 bullet を 1 byte も変えずそのまま置く)

**機械執行の範囲 ([T-396] で 2026-08-18 に実測):**
- 機械 gate が拒否する: 生の前処理指令、新しいヘッダ取り込み、新しいマクロの追加、
  新しいグローバル変数の追加、`//`・`/*`・行末 backslash
- 機械 gate の検査が部分的にとどまる: 非決定ビルトイン、副作用のある呼び出し、
  ループ、例外送出
- 機械 gate が検査しない: 新しい型/関数の追加、説明文を `implementation` に埋めず
  `justification` へ置くこと

部分的な項目と検査しない項目も禁止は不変である。**機械 gate を通ったことは、
契約を満たした証拠にならない。**
```

### 3.3 この形が満たす不変条件

- **A2 解決**: 「例外送出は不可」は現行 bullet のまま残るので、内部で処理された例外を含む
  全分類が禁止されたままになる。
- **A1 解決**: 「説明配置」は原子的義務として「検査しない」側へ明示的に置く。
- **A3 解決**: auditor を執行主体として名指ししない。結線されていない保証を書かない。
- **B1 解決**: 前置文と末尾文の 2 箇所で「非検査は許可ではない」を明示する。
- **P0 解決**: 執行の**粒度**だけを書き、機械が捕える形と素通りする形を分ける境界条件
  (「有限 corpus で観測されない形」等) は書かない。

### 3.4 実装子への追加指示

分類は段 2・段 3 の主張をそのまま写さず、**実装子が file:line から独立に再導出**する。
食い違ったら黙って書かず、報告して止める。

## 4. プラン v2 — B

段 2 案 (`test_ordinary_for_range_for_and_data_dependent_loops_pass` を decorator ごと丸ごと削除)
を**採用**する。両レンズが「production 不変・受理集合不変・D96 不要」で一致した。
検出力を 5 件失うことは worklog と insight へ明記する (B4)。

## 5. プラン v2 — pin 閉包と権限 (A5/B2)

- 更新するのは `SOURCE_FILE_SHA256["coder-v4-autonomous-sort"]` の 1 key だけ。
  `ROLE_MANIFEST_SHA256` / `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` / `DESCRIPTION_SHA256` /
  `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS` / `EXPECTED_ROLE_COUNT` は不変 (両レンズが独立に確認)。
- `.codex/role-adapters/coder-v4-autonomous-sort.json` は **Codex `role=author` 実装子が書く。**
  親は代行しない。実装子が sandbox 制約で書けなかった場合は、
  **その時点で fail-closed 停止し、ユーザー裁定へ返す** (D95 決定 3)。
- 更新順序は md → ledger → adapter 再生成。中間状態で checker / test を起動しない。

## 6. 記録義務 (B3/B4/A4)

段 7 で必ず書く。

- pin の緑は「本文が review 済み bytes と同一」しか証明しない。5 分類の保持は diff で確認した
  という事実を書き、checker の緑を意味の証明として報告しない。
- B が失う検出力は 5 parameter。受け皿は無い。
- 対応表の射程は **live `CoderProposalSort` build 経路**に限る。S6 sort sweep は固定候補で
  SWO oracle を呼ばず、freeze 再実体化は `prepare_cell` で quarantine と oracle を再実行する。

## 7. scope 外の real 所見 (裁定パッケージへ)

実装せず、段 9 の報告でユーザーへ返す。

1. **auditor の残余が契約へ結線されていない (A3 の根)。** `.claude/agents/auditor.md:21-28,32-36,66-82`
   の入力と checklist に sort closed-region の残余 (型/関数追加、bounded loop、潜在 throw、
   説明配置、非決定性) が無い。本 wave は sort role 1 枚だけを触る裁定なので、auditor role の
   改訂は別 wave。**これを閉じるまで「残余は auditor が拒否する」とは書けない。**
2. **禁止文の保持を意味で守る検査が無い (B3/M7)。** pin と byte parity を意図的に再承認すれば、
   禁止文を 1 行削っても機械は止まらない。閉じるには contract 側の semantic test が要る。

## 8. 変異事前登録 (DW-M01)

実装差分があるため matrix は免除しない。単独適用・primary kill のみ会計する。

| ID | 変異 (1 箇所) | 守る不変条件 | 期待 |
|---|---|---|---|
| M1 | `review_ledger.py` の `SOURCE_FILE_SHA256["coder-v4-autonomous-sort"]` を wave 前の値に戻す | source と独立 review pin の一致 | KILLED |
| M2 | `.codex/role-adapters/coder-v4-autonomous-sort.json` を wave 前 bytes に戻す | renderer byte parity | KILLED |
| M3 | 再生成後 adapter の `developer_instructions` から新設 1 行を削る | source body の exact-once 埋め込み | KILLED |
| M4 | 再生成後 adapter 内の `review_ledger.source_file_sha256` だけを wave 前値へ戻す | adapter 内 pin と独立 ledger の一致 | KILLED |
| M5 | `coder_effect_gate.py` の無条件ループ判定枝を発火不能にする | **wave 前の実コードの形** — 現行の無条件ループ拒否を緩めない | KILLED |
| M6 | `DENY_TABLE` の `file-stdio` から identifier を 1 個削る | 現行 host-effect 受理集合を広げない | KILLED |
| M7 | agent md の禁止 bullet を 1 行削り、pin と adapter も整合させて再承認する | 禁止文の保持 | **SURVIVED (既知の残余)** |

M7 は §7-2 の実証である。DW-M04 に従い、SURVIVED は mutated 内容の diff で注入実在を確認してから
equivalent と扱わず、「守る機構が実在しない」ことの証拠として記録する。

期待 node は DW-M07/DW-M08 に従い、**全件 SURVIVED 期待の probe 走**で観測集合を集めてから
完全集合として再登録する。M1 は eager import による collection failure になりうるため、
node 形が確定するまで KILLED 期待で登録しない。

## 9. 段 5 の分割

編集 4 枚が md → sha256 → adapter bytes の連鎖で相互依存するため素集合に割れない。
**単一の Codex `role=author` 実装単位**とする。段 6 の敵対レビューは 2 本。
