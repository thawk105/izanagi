pytestは実行せず、コードを手動traceした所見です。

1. **M1〜M5 の単一削除**

- file:line: `orchestrator/campaign/coder_effect_gate.py:63`, `:73`, `:84`, `:96`, `:103`; `orchestrator/tests/test_coder_effect_gate.py:127`, `:135`, `:136`
- 判定: **real（KILLED）**
- 各 identifier は全96件の意味的 probe に個別出現する。production から1件だけ削除すると `_IDENTIFIER_RULE.get()` が `None` になり、`fork();` 等には loop finding もないため `findings == ()`。該当 probe の `any(...)` が必ず失敗する。
- 段4裁定の「production の単一箇所削除は KILLED」という境界を正しく実装している。
- **must-fix: なし**

2. **M6 協調改変**

- file:line: `orchestrator/tests/test_coder_effect_gate.py:131`, `:142`, `:143`, `:146`
- 判定: **条件付き real/refuted**
- production と frozen literal から identifier だけを削除すると、意味的 probe と AST guard は通るが、総数が95になり `== 96` が失敗する。したがって、この2箇所だけの改変は **SURVIVED ではなく検出される**。これは望ましい追加防御であり **nit**。
- 段3で登録された `production削除 + frozen削除 + 96→95` の3点協調改変なら、新規3テストはすべて通り、段4裁定どおり既知残存となる。**must-fix: なし**

3. **自己参照リスク**

- file:line: `orchestrator/tests/test_coder_effect_gate.py:69`, `:98`, `:146`, `:159`〜`:165`
- 判定: **refuted**
- `_FROZEN_DENY_IDENTIFIERS` は文字列を列挙した独立した dict/frozenset 構造で、`DENY_TABLE` 等から導出していない。AST guard は comprehension と禁止された Name/Attribute を拒否するため、段3が挙げた自己参照実装は失敗する。
- 段4裁定の「独立 literal を AST で拘束する」という境界を満たす。
- **must-fix: なし**

4. **総数96アサーションの独立価値**

- file:line: `orchestrator/tests/test_coder_effect_gate.py:142`, `:143`
- 判定: **refuted（自己参照ではない）**
- assertion は `_FROZEN_DENY_IDENTIFIERS` の値だけを `sum(len(v)...)` で再計算し、`DENY_TABLE` を一切参照しない。したがって、production と frozen の協調削除を除けば、baseline 自身の縮小を検出できる独立 sanity check になっている。
- ただし `96` 自体を `95` に変更すれば通るため、暗号的 pin ではない。これは裁定済みの既知残存であり **nit**。

5. **既知残存のコードコメント**

- file:line: `orchestrator/tests/test_coder_effect_gate.py:125`, `:126`
- 判定: **real**
- “Known residual” として production と frozen literal の同一 commit 協調縮小を scope 外と明記し、段4の adversarial review に委ねている。将来の追加防御余地も誤って閉鎖済みとは主張していない。
- 段4裁定の「協調改変は既知残存として記録する」という境界を満たす。
- `decisions.md` 本体は射影対象外のため未監査。**must-fix: なし**

## 総括

**条件付きではい。** M1〜M5 の単一 production 削除は、全96件の意味的 probe で確実に KILLED になる。  
M6 は `96→95` まで含む協調改変なら裁定どおり SURVIVED、識別子2箇所だけなら総数検査が追加検知する。  
独立 literal、AST guard、既知残存コメントも実装されている。