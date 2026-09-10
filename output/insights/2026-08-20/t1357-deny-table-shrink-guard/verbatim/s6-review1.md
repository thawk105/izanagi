1. 転記照合

- `test_coder_effect_gate.py:69` ↔ `coder_effect_gate.py:58` — **refuted / nit**。5カテゴリ（18+35+18+18+7=96）を全件照合し、綴り・所属・重複とも一致。転記欠陥なし。

2. AST guard

- `test_coder_effect_gate.py:149` — **refuted / nit**。指定の `DictComp` は `ast.walk(assignment.value)` で検出される。既存 `AnnAssign` を `Assign` に単純変更した場合も `StopIteration` でテスト失敗となり、緑通過はしない。
- `test_coder_effect_gate.py:149-165` — **real / must-fix**。最初の `AnnAssign` しか検査せず、後続の再代入を無視する。安全な注釈付き代入の後に、`_FROZEN_DENY_IDENTIFIERS = { ... for ... in DENY_TABLE }` を置けば false green になる。
- 同じ箇所は代名詞経由も検出しない。例えば `_SOURCE = DENY_TABLE` の後に `dict(map(lambda rule: ..., _SOURCE))` とすれば、comprehension も禁止名もなく、自己参照なのに通過する。

3. 意味 probe

- `test_coder_effect_gate.py:135`、`coder_effect_gate.py:352`、`:593` — **refuted / nit**。各 probe は identifier 1個＋`(` `)` `;` に分かれ、`__asm__` も通常の identifier、`filesystem` も同様に正しく lookup される。focus log `:327` でも全155件が passed。

4. 既存テスト

- `test_coder_effect_gate.py:112`、`:168` 付近 — **refuted / nit**。`_CATEGORY_PROBES` と一意性テストの内容は変更されておらず、focus run 155 passed により既存挙動への退行は確認されない。

5. plan v2 / M6

- `s4-ruling.md:46-56` と実装 — **refuted / nit**。対象ファイル限定、96件 probe、件数 sanity check、既存テスト併存、既知残存コメントはいずれも plan v2 と一致。
- `s4-ruling.md:67` と `test_coder_effect_gate.py:142` — **real / must-fix**。M6 が production と frozen literal の `"fork"` を両方削除するなら、frozen の件数は96から95になり、`sum(...) == 96` が失敗する。したがって M6 の新テスト結果は **SURVIVED ではなく KILLED**。変異登録かテスト設計を修正すべき。

## 総括

AST guard に自己参照の false-green 経路があり、fix が必要です。  
さらに M6 の予測は現行の件数 sanity check と矛盾します。  
このまま変異 matrix へ進めず、少なくともこの2点を修正してください。