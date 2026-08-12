## 総括

**NO-GO。must-fix 1 件、should-fix 3 件、nit 1 件。**

`blobref.py` の直接 digest 比較、S7 v2 の exact grammar、固定 `F_r` 読取、D264 非 export は概ね成立している。一方、`expected_composed_sha256` に元の `str` subclass 迂回が残り、合成 digest の照合を恒偽化できる。

### must-fix

1. **合成後 digest 比較が `str` subclass で迂回できる。**

   対象: [erratum.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:168)

   (a) 攻撃手順:

   - 基底値が `"0" * 64` の `str` subclass を作り、`__eq__` を常に `True`、`__ne__` を常に `False` にする。
   - それを `compose_core(..., expected_composed_sha256=...)` へ渡す。
   - `ComposedCore.require_sha256()` の `self.composed_sha256 != expected` が subclass の比較へ dispatch し、不一致でも正常終了する。
   - 実際に `ComposedCore(..., composed_sha256="1"*64).require_sha256(Evil("0"*64))` が受理された。

   (b) 成立条件:

   - caller が組み込み exact `str` 以外を渡せること。
   - 特に S15 は文書内 `expected_composed_sha256` を持たないため、[erratum.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:690) の caller 値だけが外部 digest 束縛になる。S7 v2 の文書内固定値はこの経路に対する追加防壁になる。

   (c) 成果物への影響:

   - 本来 digest mismatch で不適格になる composition が成功扱いになり、certified 候補の適格性・選択結果が変わりうる。
   - 材料レポートと試行台帳は caller が主張した composed digest と実際の `ComposedCore.composed_sha256` が一致しない状態を「照合済み」と記録しうる。

   `bytes.fromhex` 同様に、比較前に exact `str` へ正規化するか digest bytes 同士で比較する必要がある。

### should-fix

1. **`BlobRef` は構築後の subclass 再注入により、dataclass の `__eq__` / `__hash__` を偽装できる。**

   対象: [blobref.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:84)、[blobref.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:109)

   (a) 攻撃手順:

   - 正規に構築した `BlobRef` の3 fieldを `object.__setattr__` で `str` subclassへ戻す。
   - subclass の基底文字列には攻撃対象の実 path/commit/digestを持たせ、`__eq__` は承認 ref と常に一致、`__hash__` は承認 field の hash を返す。
   - `attacker_ref in {approved_ref}` は `True` になる一方、`read_pinned_blob` は攻撃側の基底 path/commitを Git に渡し、攻撃側 digestと照合する。
   - 模擬 Git 応答による実測では、承認集合 membership が `True` のまま、承認 digest と異なる攻撃者 bytes が返った。

   (b) 成立条件:

   - authority membership を `BlobRef` の dataclass equality/set membership で判定する consumerがあること。
   - 同じ object をその後 `read_pinned_blob` へ渡せること。
   - `object.__setattr__` または constructor を通らない pickle 復元が可能なこと。通常の `dataclasses.replace()` は再正規化され、この攻撃は成立しなかった。

   (c) 成果物への影響:

   - 未承認 blob が承認 ref と等しい扱いになり、certified 選択の材料へ混入する。
   - 材料レポートと試行台帳の preregistration 三つ組または実際に読んだ bytes が、承認値と食い違う。

   resolver実装を要求する所見ではなく、現在の `BlobRef` 値型の比較・再検査契約に対する所見である。

2. **registry 検査は「整合した draft」を拒否せず、composition は全 registered ID を適用する。**

   対象: [erratum.py:639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:639)、[erratum.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:677)

   (a) 攻撃手順:

   - 新しい ID を validator registry と `DRAFT_ERRATA` の両方へ登録する。
   - `_validate_erratum_registry()` は `approved | draft == registered` なので成功する。
   - `compose_core` は各文書について approval membership を確認せず、`_ERRATUM_VALIDATORS[id]` を直接実行する。
   - coherent draft registry が実際に `_validate_erratum_registry()` を通ることを確認した。

   (b) 成立条件:

   - 将来 draft erratum が1件以上登録されること。現在は `DRAFT_ERRATA=∅` なので現2 IDへの即時攻撃ではない。
   - draft ref が `compose_core` に渡されること。

   (c) 成果物への影響:

   - 未承認 operation が core bytesと composed digestを変更し、certified 適格性・選択を変える。
   - 材料レポートと試行台帳の errata 配列へ draft ref が承認済みとして入りうる。

   registry全体の整合検査とは別に、各 `document.erratum_id ∈ APPROVED_ERRATA` が必要である。

3. **D282 section境界が Markdown-valid な1〜3空白付き ATX見出しを認識しない。**

   対象: [approval_payload.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:68)、[approval_payload.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:157)

   (a) 攻撃手順:

   - 実D282 fenceを非候補へ変える。
   - その後へ Markdown上はlevel-2 headingである ` ## D999...` と、攻撃者の対象 `text` fenceを置く。
   - parserは空白付き見出しをsection境界と認識せず、攻撃者 fenceをD282所属として受理した。実測結果は `ACCEPT`。

   (b) 成立条件:

   - 任意documentがprivate parserへ直接渡されるか、将来固定pinが更新されること。
   - 現在の公開 `load_approval_payload()` は固定 `F_r` digestを先に検査するため、現blobへの差込みだけでは成立しない。

   (c) 成果物への影響:

   - 条件成立時は攻撃者 payloadのtarget core・6 approved refs・erratum順序・composed digestが返り、certified選択・材料レポート・試行台帳の全preregistration provenanceが差し替わる。

   `_FENCE_RE` と同様、headingにも先頭空白 `{0,3}` を一貫して扱う必要がある。

### nit

1. **alpha descriptor内の深いindent行は、key風でもcontinuation proseとして受理される。**

   [approval_payload.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/approval_payload.py:354) では、例えば `    unknown_key = attacker-value` が直前fieldへ連結される。実測でも受理された。ただし固定 `F_r` digestがあり、新しいtyped keyとして公開されるわけでもないため、現在のcertified選択・材料レポート・試行台帳で変わる値を示せない。指示どおり **nit** とする。

## そのほかの検査結果

- `blobref.py` の通常constructor経由では、path/commit/sha256はexact `str`へ正規化される。
- `bytes.fromhex` は `bytes` subclassと`__index__` objectを拒否し、`__hash__`を使用しない。再注入された`str` subclassでも基底hex bytesを使うため、直接digest比較自体は迂回できなかった。
- `_validate_repo_relative_path` の再帰はexact `str`への最大1回で停止する。特殊subclassでは`TypeError`になりうるが、無限再帰は構成できなかった。
- S7文書をS15 IDへ詐称した入力と未知IDはいずれも拒否された。S15 grammarからS7の2置換を通す経路は確認できない。
- `較正` exact 2件、locator集合、固定old/new digest、適用後0件はいずれも将来core変更に対してfail-closed。
- `compose_core_from_blobs` は存在しない。`compose_core` のregistry検査はblob読取より前にある。
- D282の偽見出しをbacktick fence内へ置く攻撃は見出しとして数えられず、nested `text` fenceとdelimiter長不一致は拒否された。全角・zero-width変種はcanonical D282見出しへ正規化されない。
- top-levelおよびapproved roleのexact-key検査は集合等値であり、未知と欠落の両方向を検査している。
- `load_approval_payload()` は固定 `D282_DECISIONS_REF` だけを`read_pinned_blob`へ渡す。
- `alpha_reservation` は明示的にliteral descriptorであり、台帳の存在・履歴証明としては扱っていない。
- subprocessをimport前に拒否する実測で、`approval_payload` import時にGit実行がないことを確認した。
- `approval_payload`の型・loaderは`__init__.py`にも`__all__`にも追加されておらず、D264非exportは維持されている。

pytestは実行していない。書込みも行っていない。対象テスト2ファイルには統合commit後の未ステージ変更が存在したため、それらはレビュー根拠から除外し、6ファイルすべて `36937ed4:<path>` のcommit blobを基準に読んだ。新しいscope外裁定パッケージは不要で、consumer条件は既存RP-1、source/pin条件は既存RP-2の範囲に収まる。