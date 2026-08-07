# 段 4 裁定 — [T-625] 待ち手規約の条件 dispatch

## 所見の裁定

| ID | 出所 | 判定 | 採否 | 理由 |
|---|---|---|---|---|
| B-R1 | レンズ B | **real (blocker)** | **採用** | 第 3 案の**本文**に「待ち条件作成」があり、裁定要約が落としていた。F31 により本文優先 |
| A-1 | レンズ A | real (must-fix) | **採用** | 参照先の誤配線 (`DW-C00`→`DW-CTX`) を殺す独立 literal pin がない。契約側 pin を新設する |
| A-2 / B-R2 | 両レンズ | real (must-fix) | **不採用 (方針)** | 発火条件逐語の lint 固定は `docs/skill-self-improvement.md` の明文方針に反する。受入主張を狭める |
| A-3 | レンズ A | real | **scope 外** | parse 不能な重複行を無視する性質は既存 22 key 全体に等しく成立する既存挙動。`DW-G03` により本 wave では扱わない |
| B-R3 | レンズ B | real (must-fix) | **scope 外・裁定パッケージ** | 効果の観測 field 新設は 3 ファイル外。新規タスクとしてユーザーへ返す |
| A-4 / B-R4 | 両レンズ | real (nit) | **採用 (訂正)** | brief の「既存 23 条件」は誤り。正しくは 22 行 (07 欠番)、追加後 23 行 |
| A-5 | レンズ A | real (nit) | **採用 (実装注記)** | case list 登録漏れは無言で消える。3 箇所すべてへの登録を実装子契約に明記する |
| B-S1 | レンズ B | speculative (nit) | **不採用** | 「通知処理」の限定は裁定本文にない。逐語を採る |

## B-R1 の一次資料照合 (親の実測)

- 第 3 案の**本文** = `output/insights/2026-08-07_t597-dev-wave-budget/s6c-review.md` の「B-02 の判定」節:
  > 背景 producer／待ち手の生成・再利用・停止、通知処理、待ち条件作成の直前に `DW-C00` を再読する。
- 裁定要約 (`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §39、`docs/worklog.md` (294)) は
  「待ち条件作成」を落として写していた。
- `DW-S01` / F31 は「裁定要約が指す decision 本文を開き、食い違いは本文を優先する」と定める。
  したがって**本文の 4 要素すべて**を条件セルに書く。要約に合わせて削らない。
- これは裁定の拡張ではなく、ユーザーが承認した案の本文の復元である。ただし要約との差は
  worklog と最終報告に明記し、ユーザーが異議を出せる形にする (`DW-O12`)。

## plan v2 (確定した実装)

### 1. `.claude/commands/dev-wave.md`

条件 dispatch 表の `| 23 |` 行の直後へ 1 行追加する。逐語:

```text
| 24 | 背景 producer / 待ち手の生成・再利用・停止、通知処理、待ち条件作成の直前 | `docs/dev-wave/core.md`: `DW-C00` |
```

段 dispatch 表の `wave 開始` 行は変更しない (開始時と操作直前の二重 dispatch を意図する)。
`DW-C00` 本文と既存 22 行は 1 byte も変えない。

親の実測: 追加行 = 87 文字 / 147 B (+LF)。追加後 **9056 B** (上限 9500、余裕 444)、
最長行は **137 文字**のまま (上限 140)。予算引き上げなし。

### 2. `tools/check_docs.py`

`CONDITION_DISPATCH_CONTRACT.update({...})` 内、`"22"` の直後へ:

```python
    "24": _pairs(_CORE, "DW-C00"),
```

`_OPERATION_NUMBERS`、`REQUIRED_REFERENCE_SECTIONS`、`STAGE_DISPATCH_CONTRACT`、
`_ALL_OPERATIONS` は変更しない (`24` は operations key ではない)。

### 3. `orchestrator/tests/test_check_docs.py`

(a) guard mutation case `condition_waiter_deleted` を 3 箇所へ登録する
    — mutation 分岐 (`| 24 |` 行削除)、`_COMMAND_GUARD_CASES`、
    `_COMMAND_GUARD_NEEDLES` (`"条件 dispatch '24' が契約と不一致"`)。
    **3 箇所のいずれを落としても無言で消える**ため、実装子は 3 箇所すべてを埋める。

(b) **A-1 への fix**: operations 以外の条件 key (`15`/`21`/`22`/`24`) の参照先を
    literal で固定する pin テストを新設する。fixture と checker が同じ契約から導出される
    自己整合面 (F9 型) を、契約の外延を literal で書くことで断つ。
    `test_operation_contract_pins_exact_section_set` と同じ役割分担で、
    `DW-C00` → `DW-CTX` の誤配線を殺す。

## 受入主張の限定 (A-2 / B-R2 への対応)

本 wave が機械で保証するのは**条件 24 の存在・key・参照節**という構造だけである。
発火条件セルの**文言**は `check_docs` が保持も比較もしない。文言の意味保存は
`docs/skill-self-improvement.md` の明文方針どおり敵対レビューと人間レビューが担う。
worklog にはこの射程で書き、「発火条件が守られる」とは書かない。

## 変異事前登録 (DW-M01)

harness は `tools/mutation_harness.py`、runner は `--runner-mode dispatch` + `--force-dispatch`
(既定 recipe、F155/F156)。各変異は単一理由で、前後に同じ入力を拒否する層を持たないことを
実装後に確認してから本走する。

| # | 位置 | 変異 | 期待 kill node | 単一理由性 |
|---|---|---|---|---|
| M1 | `.claude/commands/dev-wave.md` | 条件 24 の行を削除 | 実 repo の `check_docs` 整合テスト + `condition_waiter_deleted` | 契約にあり入口にない = 不一致 1 件 |
| M2 | `.claude/commands/dev-wave.md` | 条件 24 の参照節を `DW-CTX` へ書換 | 同上 (契約不一致) | 参照 pair の相違のみ |
| M3 | `tools/check_docs.py` | `"24"` の契約 entry を削除 | 入口に余分な key = 不一致 | 契約側の欠落のみ |
| M4 | `tools/check_docs.py` | `"24"` の値を `_pairs(_CORE, "DW-CTX")` へ書換 | **新設 literal pin** | 入口・契約が一致するため構造検査は素通りし、pin だけが赤 |

**新旧両走 (DW-M08)**: M4 は変更前 HEAD 版のテストでは検出できない (pin が存在しない) ことを
示し、新テストの純増検出力の証拠とする。M1〜M3 は旧テストでも赤くなりうるため純増主張に使わない。

## scope 外 → 裁定パッケージ候補

1. **B-R3 (観測 field)**: 条件 24 が読まれ 3 条が守られたことを後から確認できる field が
   worklog / handoff / task-run / supervisor receipt のいずれにも無い。恒久義務化は 3 ファイル外。
2. **A-3 (parse 不能な重複行)**: 条件表の parser は 3 列未満・path regex 不一致の行を黙って無視するため、
   人間には二義的に見える入口を受理できる。既存 22 key 全体に成立する既存性質。
3. **A-2 / B-R2 (発火条件の逐語 pin)**: dev-wave 入口の条件文は機械保護の外にある。
   provenance 側は逐語比較を持つため、方針差の是非自体を裁定に返す。

## 段 5 の分割

3 ファイルは契約 → 入口 → テストで相互依存するため、Codex `role=author` 1 単位の一枚岩とする。
