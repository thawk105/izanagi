## 所見

- **nit — ADD_ANALYSIS のコメントが scan 経路には当てはまらない。** [transaction.cc:131](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/review/files/cc/cicada/transaction.cc:131) は「read() が計上済み」と書くが、`read_internal()` は [scan からも呼ばれる](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/review/files/cc/cicada/transaction.cc:448)。放置しても G の build・検証値は変わらず、コード中の説明だけが不正確になる。`read_internal()` には計時開始値がない、という説明に直す。

## 判定

**GO。** 静的検査では、commit を止める所見はありません。`read_set_` への登録は promotion より先で、`SINGLE_EXEC` でもこの順序です。ronly から RW へ変わった後は登録済みの読み取りが validation と rts 更新の対象になります。abort 時の inline 版にも返却経路があります。

W5 の flag 宣言・型・待機位置、既定 macro での変更行の無効化、物理行番号の維持にも反例は見つかりませんでした。変更行周辺に新しい `-Wall -Wextra` 相当の警告要因は見当たりません。

## 総括

親の構文 probe は G の 4 文脈すべて `rc=0` と記録しています。これは予測検査です。build、実行時の正しさ、待機時間は本レビューでは検証しておらず、予定された G の実測結果で判定する必要があります。