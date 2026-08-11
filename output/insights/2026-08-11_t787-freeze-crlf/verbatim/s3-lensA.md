# 結論: NO-GO

単一の JSON value に対する提案 walker は、意図した述語と一致しています。しかし、不変条件 2 は履歴全体では成立せず、malformed shape・過剰拒否・pointer 順序にもテスト上の抜けがあります。静的検査のみで、pytest は実走していません。

## 所見

### 1. [blocker / 裁定要] NUL の全域優先は「1 blob 内」でしか成立しない

次の履歴を構成できます。

1. commit A: CR/LF path 契約と、その wave 前 hash を正しく束縛した legacy g1。
2. commit B: evidence contract を NUL path 契約へ変更。g1 は継承。

現行 NUL-only 実装では A は通り、B で `evidence-contract-path-nul` と B の pointer が返ります。提案後は、祖先順走査 [s8c_preregistration.py:1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1117) の A で CR/LF が先に発火し、B の NUL へ到達しません。[同:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1436)

`prepare_revision()` でも、既存履歴の検証が worktree 契約の hash より先です。[同:1734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1734)、[同:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1745)

必要修正は、次のどちらかの明示裁定です。

- 不変条件 2 を「単一 `evidence_contract_sha256(raw)` 呼出し内」に限定する。
- 履歴・発行 transaction 全体でも NUL を優先する二段検査へ scope を拡張する。

成果物影響: 既に非受理の同一履歴について、`ActivationReport.freeze_reason_code` が NUL から CR/LF へ、直接検証の pointer が B から A へ変わり、report digest と修復参照先も変わります。

### 2. [must-fix] 非 str の外側 `path` で内側走査を止める実装がテストを通る

攻撃入力は次です。

```json
{"path":[{"path":"x\r"}]}
```

外側 `path` の値は list なので受理対象ですが、内側 `/path/0/path` は exact `path` の `str` なので拒否対象です。提案コードは正しく内側まで走査します。一方、実装が「`is_path` かつ非 str なら許可して `continue`」となっても、段 2 の以下はすべて通ります。

- 正規 schema の 38 位置
- `{"path":["x\r"]}` の正例
- 現在列挙された malformed 3 shape

既存 walker が container を必ず下降する性質は [s8c_preregistration.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:355) にあります。`{"path":{"x":[{"path":"x\n"}]}}` のような深い変種も追加すべきです。

成果物影響: この欠陥を持つ実装では malformed 契約の内側 CR/LF path が凍結 hash と `protected_sha256` に束縛され、activation だけが失敗する非対称が残ります。

### 3. [must-fix] 最初の pointer と既存 NUL pointer の文書順が固定されていない

段 2 の併存テストには NUL node が一つしかありません。したがって、次の退行が生存します。

- dict を canonical key 順で走査し、既存の最初の NUL pointer を変える。
- `first_crlf_pointer` を毎回上書きし、最後の CR/LF pointer を返す。

必要な独立 fixture は例えば次です。

```json
{"z":{"path":"x\u0000"},"a":{"path":"y\u0000"}}
{"z":{"path":"x\r"},"a":{"path":"y\n"}}
```

両方とも期待 pointer は文書順の `/z/path` です。`z` → `a` と canonical key 順を逆転させることで、走査順を実際に検査できます。D281 が要求する文書順は [decisions.md:12857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/docs/decisions.md:12857) にあります。

成果物影響: 受理集合は同じでも、凍結失敗が参照する JSON pointer が別 node に変わり、既存 NUL の診断契約と修復対象参照が壊れます。

### 4. [must-fix] 過剰拒否の正例に U+2028 等がない

提案コードの `"\r"` / `"\n"` exact 判定は正しいですが、テストは VT だけです。U+2028 を追加で拒否する正規表現などは生存します。少なくとも exact `path` の内部に以下を置く正例が必要です。

| parsed path | 独立計算した exact hash |
|---|---|
| `x<U+0085>alias` | `70498a1fc93e1c8bca1e9fb3704c66092c73116c46ec41fbbbb4e19bd1ef7c9c` |
| `x<U+2028>alias` | `9f1f6439805f51329f74c0f8ffc286203a3778e46db78e93193336c920805864` |
| `x<U+2029>alias` | `e71bf3d33b9c48d250e90e7840b31fd132887b732ed986034bad2decdf8d5ee8` |
| 文字どおりの `x\ralias` | `e9315e0a6a2f4124200d1fb98fe2f9197b8aaf8ac6f8223d48a7fd85a8296cee` |
| 文字どおりの `x\nalias` | `7a7901d7d26013eb7eae440b3718df6a4087acfa58bc233a25a7a3e9f8d8c178` |

成果物影響: 過剰な newline 判定が入ると、本来有効な evidence contract が凍結台帳・proof chain から除外され、該当契約の certified 選択も発行不能になります。

### 5. [must-fix] 親の activation 理由語の一般化と public report が一致しない

有効な v1 shape の全 38 位置は、required 側 [s8c_preregistration_evidence.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration_evidence.py:226) または consumer 側 [同:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration_evidence.py:253) から `_safe_path()` を通るため、直接 loader の理由語は `contract-path-control-char` です。

しかし production registry はそれを一律 `contract-invalid` へ畳みます。[同:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration_evidence.py:690)  
malformed shape では `_safe_path()` より前の schema 検査が発火する場合もあります。

したがって public `ActivationReport` で新たに変わるのは、主に次です。

- `condition_freeze_valid: true → false`
- `freeze_reason_code: valid → evidence-contract-path-crlf`
- `freeze_generation` / `protected_sha256`: 値あり → `None`
- predicates: 従来どおり `ERROR / contract-invalid`
- `effective`: 従来から `false`

legacy CR/LF hash を正しく束縛した g1 fixture を使い、履歴検証と activation report を固定すべきです。単に契約だけを変えて g1 hash を不一致にすると、gate を消しても `record-protected-mismatch` が残り、受理集合反転の証明になりません。

成果物影響: public activation report とその digest の期待値が誤って記録され、凍結 proof の受理反転を後段 `contract-invalid` が隠す恒真テストになります。

## 層の取りこぼし

| 層 | production 経路 | 判定 |
|---|---|---|
| 凍結発行 | `prepare_revision()` → `evidence_contract_sha256()` [s8c_preregistration.py:1745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1745) | bypass なし |
| 履歴検証 | 全祖先の evidence blob → 同関数 [同:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1436) | bypass なし |
| Activation report | `activation_report_at()` → `validate_condition_freeze_at()` [同:1593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1593) | bypass なし |
| Certified consumer | `effective_at()`、さらに利用時再導出 [同:1664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:1664)、[trial_registry.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/trial_registry.py:1217) | bypass なし |

`load_contract_bytes()` と `read_blob_at()` は別の後段防壁であり、凍結発行・履歴検証の代替経路ではありません。追加の層実装は不要です。裁定候補は所見 1 の「NUL 優先の射程」だけです。

## その他の攻撃結果

- 提案 walker 自体を通過する exact `path` / `str` の CR/LF 反例は構成できませんでした。
- escaped `\r`、`\n`、`\u000d`、`\u000a` は parse 後に実文字となり拒否されます。
- valid surrogate pair が CR/LF に化けることはなく、unpaired surrogate は canonical 化で先に `evidence-contract-json` になります。
- Unicode normalization は実行されないため、別 code point が CR/LF へ変換される経路はありません。
- 深さ 993 までは parse・canonical 化・走査が成立し、994 では parser が先に `RecursionError` となりました。hash を返す深部 bypass ではありません。
- HEAD 祖先には distinct evidence contract blob が 1 個だけあり、CR/LF path は 0 件でした。
- 現行 hash `c4f374…` と g1 `protected_sha256=853e6c…` は独立再計算でも一致しました。提案コードは canonical bytes/domain を変えないため値は不変です。

## 総括

- 現状プランは **NO-GO**。
- 単一 JSON tree に対する提案コードの拒否述語は正しい。
- ただし履歴上の CR/LF 祖先が後続 NUL を先取りし、不変条件 2 を文言どおりには守れない。
- 非 str の外側 `path` による内側 path の遮蔽をテストへ追加する必要がある。
- 複数 NUL・複数 CR/LF の文書順 pointer を固定する必要がある。
- U+2028 等と文字どおりの backslash escape を過剰拒否正例へ追加する必要がある。
- 三つの production 層に choke point bypass はない。
- current hash と既発行 g1 protected hash は不変である。