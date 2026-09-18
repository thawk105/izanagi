# probeを受けた正式specの確定

probe run2（job6417、anchor977cda2ea）はbaseline153 passed/4.85秒、17変異完走。
16件のMISMATCHは事前登録どおり失敗node取得用の期待SURVIVEDに対する結果で、正式KILLEDと呼ばない。
m16のみSURVIVED/rc0。他16件はrc1、失敗node非空。wrapperはterminal=true、shared snapshot一致、teardown成功。

正式specは実測された失敗nodeの完全集合を固定する。m04だけを別走へ分ける。
理由: universal OID sortは、非整列を保証していない他のfixtureでは生成OIDにより追加失敗が変わり得る。
期待集合を緩めず、既登録killer match_legacy[limit_plus_one]（非lexicalをfixture自身が保証）を
正規dispatch wrapperで単独実走する。変異内容は同一、既存テストの期待値/fixtureは変更しない。
他16件はmutation taskでtest_check_branch_landed.py全体を再走する。

baselineごとに緑を要求し、復元・HEAD/spec束縛・失敗集合の完全一致を維持する。
16件本走の外枠は実測job elapsed259秒の3倍777秒を上回る15分（fixture1fileは約5秒/走）。
m04のdispatch待ち上限2時間＋実行10分＋回収余裕を内側timeout10000秒に収める。
意味論とcontract感度の分類はmutation-prereg.mdのまま。
