# fold receipt (追記のみ)

fold 済み fragment の耐久記録。**`tools/spool_fold.py` だけが追記する。人が編集しない。**

同一内容の fragment が別のファイル名で再投入されたとき、それを replay として拒否するために使う
(receipt が無いと、fold 済みの内容が新しい ID で二重採番される)。

各行は 1 fragment に対応する JSON object の bullet で、`content-sha`・identity・採番結果を持つ。

## records
