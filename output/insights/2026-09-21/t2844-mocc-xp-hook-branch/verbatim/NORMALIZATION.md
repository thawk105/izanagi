# 逐語の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末空白 (space / tab) だけを除去した。可視文字は変えていない。
復元法: 下表の各行番号の末尾に、記録した除去文字列 (`repr`) を戻すと原文の sha256 に一致する。

## compute-1.log

- 原文: 4429 byte、sha256 `6d9a6d6e0b0d78916415173a6f84545b7a0aae9a63e0fce21e6e47bbd7c43006`
- 正規化後: 4428 byte、sha256 `ff3b95a11b14f994c54193e86b2445bd4aade3c9361f312951a550a290b042df`
- 除去 (行番号: 末尾文字列の repr): 30: b' '

## focus-1.log

- 原文: 5572 byte、sha256 `95a70f58a72312148c9444cd5f74bbbd50a55a90638f5e994dbeec03d37402e2`
- 正規化後: 5570 byte、sha256 `0971383039db128dcdff181d6452a428f8de3a460a89c5df6784d2e934519c9d`
- 除去 (行番号: 末尾文字列の repr): 15: b' '、47: b' '

## mk-C-amend.log

- 原文: 2907 byte、sha256 `e0ca787c0e29e0b9c9f2b6d112a30f28cd054ca43fbdef4d8674c13673a1704b`
- 正規化後: 2891 byte、sha256 `1b6877da612ab0c7ea71ffd98c505e621dac1a96fff32ca259f4e442e9693ff2`
- 除去 (行番号: 末尾文字列の repr): 17: b'    '、21: b'    '、27: b'    '、32: b'    '

## mk-C-commit.log

- 原文: 3627 byte、sha256 `fdf81d6156a864550a0b7617c8ba862755cd40190ccdcd7d0079e2b13d596baa`
- 正規化後: 3611 byte、sha256 `dbf676bc39486cac2030859b829a36deb2af98339117a6045c607c52c28abd8e`
- 除去 (行番号: 末尾文字列の repr): 30: b'    '、34: b'    '、40: b'    '、45: b'    '

## verify-candidate.log

- 原文: 1281 byte、sha256 `58cdbc68332aebfe390f6241e683f479bfaabe2be48916212737f55344465a1e`
- 正規化後: 1277 byte、sha256 `88ff6d2f3c85f56cf554464209f098ff010883bcbb266dccc9578106685fc5ba`
- 除去 (行番号: 末尾文字列の repr): 4: b' '、5: b' '、6: b' '、7: b' '
