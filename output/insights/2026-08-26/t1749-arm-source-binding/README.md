# [T-1749] 宣言 arm から build・bench された CCBench source への因果束縛 — 逐語と限界

wave: dev-wave-t1749-arm-source-binding
実装 commit: 1e10a081
base local main: 53c61414

---

## 1. 親が実測した原典事実

### 1.1 述語は指紋の元データに逐語で残る (関連付け検査が成立する根拠)

段 3 レンズ B は「preimage 内の代入が proposal 由来の述語と exact 一致することを検査せよ」と
提案したが、根拠に挙げた byte 数 (5,822 / 23,716 / 34,530 / 64,070) は **素の checkout の値**で、
materialize 後を測っていない。素の木では preimage 中の `izanagi_gate_pass` は **0 件**である。

親が template patch を実適用 + 即時復元する probe で決着させた。

| 対象 | 素の木 | template patch 適用後 |
|---|---|---|
| `cc/silo/transaction.cc` 正規化後 bytes | — | 25,452 |
| 同 `izanagi_gate_pass` 出現 | 0 | 6 (2 マクロ文脈 x 3 出現) |
| 3 source 連結 preimage bytes | 64,070 | 65,806 |
| `sha256(preimage)` | `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` | `c259314e2fce09177c5568abffe37e37b785c3ea5c5acbb360efc9a7c4f18636` |
| `source_digest.compute()` | 同上 (一致) | 同上 (一致) |

compiler は `g++-12` (既定の `g++-13` はこの login node に不在)。
probe 後の worktree と submodule は `git status` で clean を確認した。

### 1.2 `emit_predicate` の値域 (恒真化しない根拠)

全 32 mask を実行し、返り値が常に `izanagi_gate_pass = <式>;` の**完全な代入文**であることを
確認した。長さ 72〜379 bytes。**bare `true` を返す mask は 1 つも無い。**

したがって未 materialize の skeleton (`izanagi_gate_pass = true;`) は、32 mask のどれに対しても
関連付け検査を通れない。

### 1.3 強制ソース閉包が編集面を決めた

`campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` は exact 25 path。
`artifact_admission.py` が記録済み closure blob map と現在の map を照合し、
不一致なら `CERTIFIED_ACCEPTANCE` を `E1-stale` (`recorded-current-closure-mismatch`) で拒否する。
`verify_s8c_cross_binding` 自身がこの照合を通るため、**閉包 file を 1 byte 変えると
既存 campaign が全部読めなくなる。**

段 2 plan は閉包内の 2 file へ書き込み経路を足す設計だった。これを不採用にし、
閉包の外だけで閉じる設計へ寄せた。

### 1.4 事前登録契約 JSON は条件凍結の保護 hash 対象

`s8c_preregistration.py` が契約 file path を宣言し、
`evidence_contract_sha256` → `protected_sha256` を記録して不一致で
`record-protected-mismatch` を投げる。`DECIDER_VERSION` は
「core/evaluator/projection の受理意味を変える変更は同じ commit で版を bump する」と明記。
かつ評価器は 1.3 の閉包の**中**にある。

---

## 2. 連結規則の characterization golden (変更前の現物から採取)

`source_digest._digest(parts)` の現行値。`NUL` = `chr(0)`。

| parts | sha256 |
|---|---|
| `["alpha", "beta carrot", ""]` | `915b28ce3367127f137e980ca567a3113a63f37b9609add39a8290cbd682b354` |
| `["x"]` | `2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881` |
| `[]` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `[chr(233), chr(26085)]` | `f40dc8347e446af4a45697131fbc865dfef051dce15b903de7253da24b9a84cd` |
| `[chr(101) + chr(769)]` | `bf12767b0f2a56b2190075bae8169f656e3ce8d6357d4aff184bc6c7ea48f9f6` |

区切り・順序・UTF-8 encode のいずれを変えてもこの hex は一致しなくなる。
`compute` の抽出が byte 同一であることは、この表と 1.1 の実木 anchor 2 点で固定した。

---

## 3. この実装が証明すること・しないこと

| 辺 | 証明の種別 | 内容 |
|---|---|---|
| proposal bytes → predicate digest | `consumer-rederived` | consumer が proposal を decode し mask と digest を再計算する |
| preimage bytes → source digest | `consumer-rederived` | consumer が artifact bytes を再ハッシュする |
| predicate ↔ 実体の関連付け | `consumer-rederived-textual-materialization` | マクロ文脈ごとの gate 行多重集合が期待と完全一致することまで |
| attempt topology | `producer-self-consistency` | 走行側が書いた値どうしの照合 |
| build 実行 | `producer-execution-contract` | producer の実行時契約に依存する |

**閉じていないこと (裁定パッケージへ返す):**

1. **実行到達性。** 宣言した述語が実際に実行されることは証明していない。
   非到達化 (代入前の `return`) や別変数による実効分岐は、受入時点に checkout も compiler も
   無いため consumer 単独では閉じない。
2. **実 compiler 入力層の A→B→A。** 現設計は可変 checkout の前後 snapshot であり、
   build 中の source 差し替え・誤った build root・汚染 cache binary を排除できない。
3. **leaf 受領証本体の永続化と後段再検証。** 現在は outer receipt に SHA だけが残り、
   後段 verifier は cross-binding を再実行しない。
4. **事前登録契約の `field_paths` 拡張。** 1.4 の理由で本 wave では行わない。
   契約の記述が実装より弱いままである。
5. **gate 本体を強制ソース閉包へ入れるか。** 受入照合器・受領証は現在 closure の外にある。

---

## 4. 変異 matrix (最終巡)

baseline PASSED、**9/9 KILLED・SURVIVED 0・MISMATCH 0**。
spec は `mutation-spec-final.json`、台帳は `mutation-ledger-final.json`、
probe 巡は `mutation-ledger-probe.json`。

probe 巡 (全件 SURVIVED 期待で観測 node を集める) で 1 件が実際に SURVIVED した。
E1 の mask 等式である。`expected_predicate_sha256(mask)` は mask の純関数なので、
**digest 等式が mask 等式を含意する冗長 gate**であった。最終巡では両層同時変異
(`M02B-E1-PREDICATE-PAIR`) へ再照準し KILLED を確認した。

段 3 レビュー A が「既存の別 gate が先に赤にするため新設行の変異を捕まえない」と
原典付きで反証した 5 件 (WAL topology、bench topology、WAL→artifact 片側、
proposal→attempt 交差、missing bytes) は登録していない。

---

## 5. 実測した所要

| 対象 | 実測 |
|---|---|
| 焦点走 (2 file、462 件) | 62 秒 (dispatch 込み) |
| 全走 | 16,580 passed / 60 skipped |
| 変異 matrix 最終巡 | 10 走 (baseline + 9)、約 14 分 |
