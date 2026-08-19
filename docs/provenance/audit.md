# AI provenance — commit 前後の検査と解釈

入口の該当条件が成立したときだけ読む。

## PR-A01 — commit 前の message 検査

message file と staged path を検査し、rc=0 を確認してから commit する。

```bash
python3 tools/check_ai_provenance.py --message-file <path>
```

## PR-A02 — commit 後と範囲監査

既定監査は各規則の内容検出 commit 自身と、その祖先でない HEAD 到達 commit の欠落、排他違反、フィールド順、値と role の形式を検査する。別範囲は
`--range <range>`。導入祖先は legacy とし遡及違反にしない。correction 範囲の権威は `PR-C03`。

```bash
python3 tools/check_ai_provenance.py
```

既知違反台帳 (checker 内の固定 entry) に full SHA と種別が一致した違反は既知へ分離し、**正常時の rc は
新規だけで決まる**。既知は stdout へ出るので `known-violations=N` 付きの rc=0 を緑と読まない。
台帳破損と stale (範囲内 entry に期待種別が無い) は rc=2 で、既知一覧を出さない。

## PR-A03 — 観察データの解釈

この記録は観察データで統制実験ではない。難度・役割・入力が交絡するため、commit 数や成功率だけで
製品・モデルの優劣を断定しない。判断はタスク種別を揃え、手戻り・テスト結果と併せる。
