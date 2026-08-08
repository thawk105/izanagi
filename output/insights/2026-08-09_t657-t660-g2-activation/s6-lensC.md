## 所見

### C-1 — must-fix — M5 は受理集合の kill ではなく診断文字列 pin

根拠: [env_contract_activation.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:355)、[test_env_contract_activation.py:476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/tests/test_env_contract_activation.py:476)、[s4-adjudication.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-t660-g2-activation/s4-adjudication.md:94)

M5 の「変更前は SURVIVED、新設 node だけ KILLED」は、空 chain の拒否そのものを無効化する変異では成立しない。guard を素直に無効化すると `rows` が未束縛のまま [env_contract_activation.py:417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/env_contract_activation.py:417) へ進み、`UnboundLocalError` が漏れるため、変更前の production node も `EnvContractError` を捕捉できず KILLED になる。一方、変更前を SURVIVED にするには `ActivationRecordError` の理由だけを変える必要があり、それは DW-M03 上の acceptance kill ではなく diagnostic sensitivity pin である。

成果物影響: 変異台帳／受入レポートの M5 が `KILLED` から diagnostic sensitivity へ変わり、空 chain の受理集合を新テストが単独で防御したという過大な証明を除く。

修正案: exact-message 変異を旧・新両方へ走らせ、M5 を「旧 SURVIVED／新 KILLED の diagnostic sensitivity pin」として kill 集計から分離する。受理集合の kill を要求するなら、空 chain を実際に受理させる変異を別登録し、その場合は変更前 production node も KILLED になる期待へ修正する。

## その他の攻撃結果

- never-active 2 node の head=1 合成化は弱体化ではない。実 authority では全登録 hash が ever-active になったため負例が存在せず、合成 authority は production resolver、実 catalog、実 calibration を通る。ever-active gate を除去すれば両 node は赤になる。
- valid suffix の移動も同じ production loader/head-pin を通り、head=2 正例と source-head 引渡し node が別途あるため、元の拒否述語は保存されている。
- calibration 全世代走査は強化。既知集合は長さ 1、未知 self-failure の即時 assert、最終 exact set equalityがあり、新しい不整合を暗黙に吸収しない。
- tail deletion は `00000002.json` 削除後も genesis が残り、最初に serial 不一致が発火する。空 chain に mask されない。M1 時だけ state-hash 不一致へ移る。
- silo test は記録 contract hash、calibration path/SHA、gap attestation の相互束縛を保持しており恒真ではない。
- `00000002.json` は serial 2、genesis predecessor、linux g1、Pegasus g2で、独立再計算した state hash `398b1920…bed8` と head 定数が一致する。`00000001.json` は HEAD bytes と一致し、`INITIAL_BYTES` も保存されている。
- 残存 head=1 は genesis・issuer・合成 authority、g1 literal は歴史 evidence/floor golden。current consumer は動的 lookup。追加の取り残しは見つからなかった。
- 変更は production 1 file、test 4 file、新規 record 1 fileだけ。production silo、docs、output/floor、genesis、commit は未変更。

## 総括

**NO-GO**

- must-fix: C-1 — M5 を acceptance kill として数えず、diagnostic sensitivity へ再分類する。
- M1〜M4、head=2、historical silo、authority内容、scope境界には静的な追加所見なし。
- pytest・変異実走は未実施であり、緑とは判定していない。