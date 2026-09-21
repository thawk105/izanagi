## 実施

入力 SHA256 を照合後、指定 main の台帳を base に `--refresh` を実行しました（rc=0）。24,812→26,605件。

記録：[verify.md](t2825-author-l-fix1/verify.md)、[verify.json](t2825-author-l-fix1/verify.json)、[refresh.log](t2825-author-l-fix1/refresh.log)。

## 検算結果

- (a) PASS：生成 SHA256 は測定 B の `27fd84c265373b4039a978ebb074d5b4f71c2d78d935fa76446534881448040f` と一致。
- (b) 一致
- (c) PASS：落ちた312件、うちT-2344追加由来172件、凍結prefix 0件。
- (d) PASS：凍結426件の集合・値・行 bytes が一致。
- (e) PASS：同じ入力の `--refresh --check` はrc=0、bytes不変。
- (f) 不一致：要求のtracked変更1行に対して0行。生成結果がHEAD・indexと一致するため。untracked 10件は所有dir内のみ、所有外変更0件。

## 落ちた node

312件＝T-2344追加由来172件＋その他140件。全名前は [dropped.txt](t2825-author-l-fix1/dropped.txt) に保存しました。

## 未実走

pytest・性能測定・git add／commit／merge は実行していません。

## 総括

main の現物から再生成し、測定 B と同一の結果を確認しました。
凍結426件を値・行 bytes とも保持しています。
落ちた312件の全名前と内訳を記録しました。
(f) は既存HEADとの一致により要求と異なりますが、所有外変更はありません。