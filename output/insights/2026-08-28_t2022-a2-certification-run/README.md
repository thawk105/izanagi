# [T-2022] A-2 fan-out 4-cell certification 実走

## 結論

attempt `t2022-20260828c` の4 cellはすべてcorrectness certifiedだったが、adopted backoffは両workloadでstockを下回った。outer certification statusは`reject`である。性能差を成功・tieへ読み替えない。

| workload | stock median TPS | adopted median TPS | effect |
|---|---:|---:|---:|
| rr5 | 2,527,542 | 1,355,011 (`fixed10`) | -46.3902% |
| rr50 | 3,662,448 | 1,248,603 (`fixed5`) | -65.9080% |

各cellはlegacy correctness 1回とfull-scale correctness 5回がすべてpass。性能は別のtrace-disabled build/runで5 samplesを取得した。anomalyは0、performance statusは4 cellすべて`complete`。

## 実行identity

- source commit: `639c1dbad4b00d8c51993a653cfc1ebfd22cf300`
- CCBench pin: `511c953`（full HEAD `511c9538e4e8efa54b45cda62e72389ed3b706ec`）
- policy SHA-256: `42bfee487c9e517b9876fbb41f8a4b4de53266ced1543263087bbd637ecc897e`
- protocol SHA-256: `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4`
- rr5 request: `954194.nqsv`、Elapse 3671s、bnodeはreservation receipt参照
- rr50 request: `954195.nqsv`、Elapse 3594s、bnodeはreservation receipt参照
- submission/completion/acquisition/raw-manifest SHA-256: `c89d2acd...a0104d29` / `b7b1538a...fa5b1026` / `05fd829c...4614cb6` / `12d8be7a...05a7c35`

durable authorityは `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c/`。tracked materializationは `output/insights/2026-08-24_paper-story-a2-certification/`。`certification.json` SHA-256は`f685b40d194c9e4b40eed6337b294f38a7ff4aef731829317fd2e83940fbda40`。

## 実走で閉じた欠陥

1. pre-existing `t2022-20260827` はqueue待ち中にlive worktreeが消え、source digest不能。
2. `t2022-20260828` はpolicy `SILO`が実source `cc/silo`と不一致で4 cell identity-error。
3. `t2022-20260828b` はfull pinとshort authorityの不一致、およびBACKOFF_REPRO capability未配線で4 cell admission-error。
4. `t2022-20260828c` の初回collectはLustre上の`RENAME_NOREPLACE` EINVAL。既知site fallback修理後、同じacquisitionの再提示だけでpublishした。

失敗attemptはすべて別leafのまま保持し、成功attemptへ混ぜていない。`t2022-20260828`と`...b`は各々finish-groupをexact 1回実行し、raw manifest無しのcompletion/acquisitionで閉じた。attempt cも両終端後にfinish-groupをexact 1回だけ実行した。

## 開発検査

- focused: 103 passed、consumer/meta 4 passed、protocol 73 passed、admission 118 passed、materialize 83 passed、spawn inventory 2 passed。
- mutation final matrices: baseline PASSED、M1〜M12の12/12 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。probeの期待node訂正とhash転記失敗はjob dirに保全した。
- acceptance: queue既定900sのinfra失敗後、D612 opt-in 3600s/600sでchild-green。spawn inventory追随後の最終全走は記録commit後に再実行する。

## 既知限界とscope外

- correctness run argvは既存pipelineが独立記録しない。report自身の`independent_observation_limits`に明記し、独立観測を主張しない。
- sibling driver failure時のpartial raw anomaly lattice、attempt選別一般化、publish fallbackのnon-cooperating writer耐性は本waveで拡張しない。
- A4 noise floorはopen、global minimalityは確立していない。今回の結論はexact 2点 protocol内のrejectに限定する。
