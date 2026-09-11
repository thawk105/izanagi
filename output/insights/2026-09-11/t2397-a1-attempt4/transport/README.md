# 実行時transportの保存

authority: none / default_effect: no-state-change。
各nonce directoryは、実行時のsubmission directoryからrequest.json、compute-visible.json、
result.json、receipt.jsonのbytesを保存したもの。移動後のfilesystem同一性を主張しない。

- 987a8aad642db4e1b4cfb12877977633: mutation-source cloneのoutput/pegasus-dispatch。単体群最終、991859。
- 9f1cde117fcf6ee073d5394cdeb64a8c: waveのoutput/pegasus-dispatch。実機群最終、991865。
- b5ad168fc86df7a3443c7fefa6679d12: waveのoutput/pegasus-dispatch。実機正例と制約検査、991844。
- 66100a3feb20ad694ea459c4df3e9f16: waveのoutput/pegasus-dispatch。campaign関連走、991839。
  親receiptはsignal-abort、後に自然完了した子resultはrc0。この差を消さない。

元waveは /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4、
cloneは /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/mutation-source。
測定・判定時の束縛は各request SHAと対応するattempt/wrapperが正本であり、この保存を新しい実行とは扱わない。
