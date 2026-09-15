## must-fix

なし。今回の JSON について、値の転記・期待値からの捏造・前段エラーの専用拒否への混入は認めませんでした。記録された probe／checker の SHA-256 は現物と一致しています。

## nit

- **compiler 名別集計は独立実体数ではない。** `tools/t1643_has_include_pair_probe.py:441` は requested name ごとに実行し、`:454` でそのまま連結します。`g++` と `g++-11` は realpath・SHA-256 が同一で、それぞれ対照164件を計上しています。裁定どおりの列挙であり修正必須ではありません。**成果物への影響：508件成立を独立compilerによる508例とは読めず、全対照成立の3名称は2実体です。**

## 対照表の読み方への影響

1. **値の由来／S-5：閉じています。**
   `tools/t1643_has_include_pair_probe.py:101` が実 `subprocess.run` の呼出し・返却を観測し、`:189` は今回の stdout の単一 sentinel と `rc=0` からのみ値を導出します。期待値を使うのは取得後の対照判定（`:383`）です。全960 measuredセルを生出力と照合し、不一致なし。**値は今回の観測値ですが、抽出対照単独を起動証明にはできません。**

2. **checker argv：一致しています。**
   実関数を呼ぶ `tools/t1643_has_include_pair_probe.py:358` と、`source_digest.py:1662`／`:1707` を照合しました。全800 checkerセルで `BUILD_FLAGS` の位置、sorted `-D`、末尾 `-x c++ -`、stdin・cwd・env が一致。`#include` 除去も実関数経由です。ただし今回の fixture 自体には除去対象行がありません。**checker列は、このfixtureに対する現物の呼出しを代表します。**

3. **拒否分類：前段エラーは混入していません。**
   `tools/t1643_has_include_pair_probe.py:128` は最内の例外発生位置で分類します。204／60／20件は、それぞれ `source_digest.py:1868`／`:1853`／`:1846` の専用raiseに一致しました。other_error 180件は `_dump_macros` 起因で、g++-9が84、g++-13が84、残る3名称のoperand行が計12件です。**180件をinclude演算子の専用拒否へ合算できません。**

4. **angleのエラー／quoteの0：抽出処理の人工物ではありません。**
   `tools/t1643_has_include_pair_probe.py:143` のfixtureでは式評価後の枝にsentinelを置き、`:195` は非ゼロrcを値にしません。対象4ヘッダについて、動作する3名称のchecker列ではangleが各24件 `rc=1,value=null`、quoteが各24件 `rc=0,value=0`。`-P` のない実 `_dump_macros` でも同じ差です。**この差は記録されたstdin・探索環境での観測であり、実header位置一般へは拡張できません。**

5. **対照508成立／312不成立：帰属は正確です。**
   `tools/t1643_has_include_pair_probe.py:383`／`:387` の判定をデータと照合しました。不成立は各compilerで値対照144件＋guard対照12件。g++-9は `-std=c++20` 不認識、g++-13は不在です。両者にも前処理前のdefine／paste拒否による成立が各8件あります。正負・反転・抽出対照には値取得の固定化や取り違えを検出する意味がありますが、絶対パス対照（`:172`）は相対探索順を保証しません。**全対照成立は実buildとの探索条件一致を意味しません。**

6. **未測状態：今回の記録に0埋め・rc創作はありません。**
   `tools/t1643_has_include_pair_probe.py:375`／`:456` に対応して、compiler_missing 400件は `FileNotFoundError,rc=null,value=null`、compute未測2件も `rc=null,value=null`。preprocess_error 640件は非ゼロrcで、値はすべてnullです。**computeの2件は集約placeholderであり、式別測定ではありません。launch_errorは今回0件で、その実例検証はできません。**

7. **build側の射程は補助観測です。**
   `tools/t1643_has_include_pair_probe.py:279`／`:303`／`:433` のとおり、configure全10回失敗により探索条件は再構成、header列は `/tmp` の相対構造とsymlinkを使用しています。**build-headerも実admission TUの観測ではなく、再構成条件下の補助列です。**

## 裁定パッケージ候補 (scope 外の real 所見)

新規追加なし。既裁定のlegacy compiler非対称・非再帰走査境界について、本レビューから到達可能性を追加認定する根拠はありません。

## 総括

今回の対照表は、記録された環境・fixtureに対する観測として整合しています。`controls_passed=false`、`conclusion=null` も裁定に沿っています。独立compiler数、実build対応、compute観測へ射程を広げない読み方が必要です。

静的検査と保存JSONの照合のみ実施しました。probe・pytestの再実走、ファイル変更はしていません。