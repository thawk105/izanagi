静的判定は **NO-GO** です。削除変異と gate 誤配線は検出できるようになりましたが、レビュー B が併記した「tolerance の固定値化」を検出できず、must-fix の根本原因が一部残っています。pytest・変異は実走していません。

## 因果と代表性

tolerance 上書き削除について、fix の因果は成立します。

- dynamic-pre は中央値 `2101`、外れ値 `3079.456`、差 `978.456`。
- 100% の許容差は `2101` なので self-pass。
- 5% の許容差は `105.05` なので self-fail。
- static-pre/post は差がそれぞれ `6`、`19` で 5% でも pass。
- acquisition receipt は physical=48、fixture の affinity=2 と cpuset=2 が一致し、static 比較は clock を除外、calibration も成功形なので、別理由による過剰決定はありません。

したがって [cli.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:551) の上書きを削除すると gate が通り、[test_calibrator_certify.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:564) の `assert rc != 0` が落ちます。static-pre/post への誤配線も同様に検出します。

job-staging との照合では、5 件の `attestation-pre.json` はすべて tolerance=100、48 標本、中央値2101で、47個の2101と1個の外れ値という形でした。負例の `3079.456` は [実 attestation-pre](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/job-staging/0:867876.nqsv/attestation-pre.json>) の実値です。48標本 fixture は対象 field について producer-reachable です。

ただし完全な実 profile の複製ではありません。実データは affinity=48、cache entry=145、同 job の static/pre/post はすべて5%で self-failです。fixture の static/post pass は誤配線を識別するための単一理由な合成値であり、この差自体は must-fix ではありません。

## 回帰と恒真性

snapshot と現在差分の比較では、fix 後の変更は二つのテストファイルだけです。既存 `assert` の緩和・反転・skip・削除はありません。

共有 `_profile()` は「logical=2に3標本、tolerance=5」から「logical=2に2標本、probe tolerance=100」へ変わっています。既存成功系の入力意味は変わりますが、producer-reachable 化と上書き前 placeholder の再現であり、CLI 通過後は従来どおり5%の self-passです。既存成功条件を甘くする回帰とは判定しません。

[test_env_contract.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:462) の `checked_entries == 2` は固定値との比較なので恒真ではなく、単純な追加・削除を検出します。内容同一性そのものは件数 pin の責務ではありませんが、現在の二 entry は loop 内の self-consistency、既知例外集合、lookup golden、legacy exact 集合で別途拘束されています。pair set が alias を一件へ畳む局所的弱点は従来どおり backlog として残ります。

## 総括

| 所見 | 判定 | 根拠 |
|---|---|---|
| B must-fix: 実 probe の100%、48標本、3 profileと上書き・誤配線検出 | **partial** | 上書き削除と static-pre/post 誤配線は検出。しかし定数 `5.0` への固定化が生存する |
| B nit: `visited == set(REGISTRY)` の恒真性 | **closed** | 独立な固定件数になり、現 registry の追加・削除で赤になる |
| B backlog: pair set が exactly-one-entry を局所証明しない | **partial** | 件数 pin だけでは同一 pair の alias を数えない。現 suite では他の exact/golden が補完し、must-fix ではない |
| A must-fix: M1 は構文を保つ no-op | **closed（fix 側の確認範囲）** | fix 前後で production gate は不変。fix は M1 手順へ触れていない。親は `pass` 等で変異する必要がある |
| A の refuted 攻撃: consumer drift、publish bypass、恒真自己比較、issuer 共通化 | **closed** | production 差分が fix 前 snapshot から変わっておらず、攻撃は real に戻っていない |
| B の refuted 攻撃: registry各攻撃、golden vector不足、scope過大、既存成功系reject | **closed** | golden/production は不変。registry 件数 pin は追加防御で、受理集合を広げていない |

新規の残存 must-fix は [test_calibrator_certify.py:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:368) です。CLI 引数・policy計算・artifact期待がすべて `5.0` のため、production の代入を次のように固定化しても新正負例の全数値条件が維持されます。

```python
profile["effective_clock"]["tolerance_pct"] = 5.0
```

実 Pegasus の [calibrate-argv.json](</work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/job-staging/0:867876.nqsv/calibrate-argv.json>) は `2.0` を指定しています。固定化を見逃すと、artifact tolerance が2%から5%へ変わり、serialized hash・registered path/SHA、runtime receipt の受理集合、certified 選択、材料レポート、試行台帳の環境参照が変わります。少なくとも二つの異なる CLI tolerance を通し、各 artifact に入力値が保存されることを pin する必要があります。

回帰は、製品実装・既存期待値については認めません。共有 fixture の意味変更はありますが、緩和ではありません。`regressed` と判定した既存所見もありません。

**land 判定は NO-GO** です。上記固定値化経路を閉じ、その後に親が計算ノードで対象テスト、meta-test、M1 の構文有効な no-op 変異、変異 matrix、受入を実走してから再判定すべきです。