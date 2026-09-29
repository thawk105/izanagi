## 所見

1. **should-fix — CUSTOM の identity 判定が既存の照合より弱い。** [起動器:1193](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/launch_gcfix_run.py:1193) は命令列の一致だけで合格にします。既存の判定はコンパイルコマンドの一致も要求します（[同:1162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage5/launch_gcfix_run.py:1162)）。放置すると、異なるコンパイル条件で偶然同じ命令列になった比較を、R3 の TRACE=0 identity 合格として記録できます。

## 裁定との対応

- **R1:** 満たす。最上段の wts 判定、任意段数の aborted 走査、非 deleted と null への ERR を確認。変更は `gc_records()` 内だけ。
- **R2:** patch の形と対象は一致。厳密適用の実走は本レビューでは未確認。
- **R3:** spec の build・patch 順・run・expect は表に一致。起動器の run 合否と v3 の C・W 集計も静的には整合。identity の照合条件に上記の不足がある。
- **R4:** onelevel は走査段数だけの変異。count は修理後の走査で aborted を飛ばして回収する場合だけ出力する。
- **R5:** 指定された成果物構成に一致。CI script は F を唯一の親として確認し、依存 pin の照合を維持している。

## 総括

**identity 判定の照合条件を揃えてから確認走行に使うべきです。** 本段は読み取り専用の静的レビューで、build・run・ASan の結果は確認していません。