# 結論: GO

must-fix 所見はありません。実装は CR/LF を含む exact `path: str` だけを新たに拒否し、段 4 裁定の受理集合・診断契約・hash 不変条件を満たしています。pytest は制約どおり実走していません。

### 攻撃面の確認

- 過小拒否: [走査実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:344) は非文字列の外側 `path` でも dict/list の走査を継続します。root、深い入れ子、malformed shape、`\r`/`\n`/`\u000d`/`\u000a` の escaped 表現を通す経路は見つかりません。
- 過剰拒否: 判定は `is_path and isinstance(node, str)` と NUL/CR/LF の明示比較だけです。非 path field、非文字列 `path`、VT、U+0085、U+2028、U+2029、文字どおりの `\r`/`\n` は受理されたままです。
- NUL 契約: NUL は発見時に即 raise、CR/LF は pointer を保留するため、同一 node 併存、先行 CR/LF＋後続 NUL、複数 NUL のすべてで従来の `evidence-contract-path-nul` と文書順最初の NUL pointer が維持されます。
- 文書順: `{"z":…,"a":…}` では root が `a`、次に `z` の順で push し、LIFO の pop は `z` が先です。canonical 化の `sort_keys=True` は元 dict の挿入順を変更しません。
- 検査位置: [canonical 化成功後、hash 前](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:374)です。escaped CR/LF と lone surrogate の併存は先に `evidence-contract-json` になります。
- hash: `_canonical_bytes`、`_DOMAIN_EVIDENCE`、`_DOMAIN_PROTECTED` は差分外です。標準ライブラリと domain literal による独立計算で、現行 hash は `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471`、38 path に禁止文字は 0 件でした。既発行 g1 の `protected_sha256` pin も `853e6c44…99286e` のままです。
- 恒真性: [独立 hash helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:160) は `json.dumps` と `hashlib.sha256` で再計算し、固定 literal と先に比較しています。domain は production 定数を参照しますが、期待 literal が固定なので定数変異時にも比較は追随せず赤くなり、恒真にはなりません。

### F1〜F7

| 裁定 | 判定 | 固定箇所 |
|---|---|---|
| F1 | 実装済み | 非文字列 `path` 配下の list・深い dict |
| F2 | 実装済み | canonical key 順と逆の複数 NUL／CR／LF |
| F3 | 実装済み | VT、U+0085、U+2028、U+2029、literal backslash-r/n の exact hash |
| F4 | 実装済み | pre-wave hash literal に束縛した CR/LF legacy g1 の validation／activation |
| F5 | 実装済み | root 直下 `path` の CR/LF |
| F6 | 実装済み | 非文字列 `path` の dict 正例 |
| F7 | 実装済み | `b'{"path":"x\\r\\ud800"}'` と LF 版 |

未実装の F 項目はありません。所見ゼロのため、成果物影響を伴う未解決事項もありません。段 6 全体としての最終緑判定には、親による事前登録済み変異 matrix と受入全走が別途必要です。

## 総括

- **GO**
- must-fix / nit ともに所見なし。
- CR/LF path だけが新たに拒否される。
- NUL の理由語・pointer・単一契約内優先順位は維持。
- 文書順 pointer と canonical 化後の検査位置は正しい。
- 現行 hash と既発行 g1 pin は不変。
- F1〜F7 は全件実装・固定済み。
- pytest・変異・受入の実走は親の段 6 作業として未実施。