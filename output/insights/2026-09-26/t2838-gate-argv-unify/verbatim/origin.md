# 依頼の逐語 (2026-09-26、ユーザー直接起動の /dev-wave 引数)

```
[T-2838] 択 A を実施する。受入門番が数える leader を argv の先頭一致 (^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance)
  に統一し、写し元の門番 script を repo 外の 1 本 (/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/) に決める。閾値・周期・lease TTL
  は変えず、repo には置かない。採用前に、走っている受入 process の argv と正規表現が一致する (見逃しが無い) ことを 1 回実測する。採用後、同じ
  probe で閉門の内訳を取り直して記録する。長い待ちが残っても択 B は今は採らず、再提示の材料として記録する。一次資料
  output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md §3・§7。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
```
