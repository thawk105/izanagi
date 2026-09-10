## 所見

1. **主張:** 専用 lane は受理集合を実際に広げる。環境 marker だけで D460/D471 が拒否した HEAD pin 選択経路へ切り替わるため、「既存の受理集合は不変」という説明は成立しない。  
   **file:line:** `s2-plan.md:68-75,138-141`、`orchestrator/campaign/s8b_floor_campaign.py:882-901`、`orchestrator/campaign/certified_writer_admission.py:178-223,395-413`、`orchestrator/campaign/floor_submit_receipt.py:15-19`、`docs/decisions.md:19196-19213,19610-19616`。  
   **具体的な失敗シナリオ:** active contract `C` に legacy `(C,P0)` と versioned `(C,P1=HEAD pin)` が並ぶ状態で、同じ receipt と nonce `N` を使う。marker 無しなら exact-one resolver が拒否するが、`IZANAGI_FLOOR_REMEASUREMENT_NONCE=N` なら新 resolver が `P1` を選び、後段が受理する。信頼済み artifact が同一でも ambient env 一つで拒否から受理へ変わる。T-987 がこの exact delta を明示的に上書きしたのか、段 4 で再裁定が必要である。  
   **深刻度:** blocker

2. **主張:** 提案された holdout entrypoint の四重束縛は、四つの独立 authority ではない。path の元となる `(contract_sha256, ccbench_pin)` が supplied document 由来なので、すべてが caller の選択へ従属する。  
   **file:line:** `s2-plan.md:75,113,127,134`、`orchestrator/campaign/s8b_holdout_admission.py:463-490,735-786`、`orchestrator/campaign/s8b_floor_campaign.py:736-739`、`orchestrator/campaign/s8b_floor_contract.py:386-400`、`docs/decisions.md:19200-19208`。  
   **具体的な失敗シナリオ:** HEAD に同じ current contract `C` の versioned protocol `(C,P-old)` と `(C,P-new)` がともに 100644 blob として存在し、実 gitlink は `P-new` とする。caller が古い `(C,P-old)` の record と document を専用 entrypoint へ渡すと、derived path、HEAD bytes、worktree bytes、hash、document はすべて自己整合して通る。current protocol validator も pin を非空文字列としか検査しないため、entrypoint 自身が root-only resolver を再実行しなければ古い pin の claim を作れる。既存 core は内部で固定 `_authority()` を呼ぶため、安全な合流点もプランに示されていない。  
   **深刻度:** blocker

3. **主張:** pilot 限定 lane は、新 pin の一回性 key を消費する一方、v2 再凍結に使える成果物を作れない。一回限りの権利を焼くだけの経路になる。  
   **file:line:** `s2-plan.md:62,72-75,128`、`orchestrator/campaign/s8b_floor_campaign.py:5393-5406,5512-5520`、`orchestrator/campaign/s8b_holdout_admission.py:493-510,868-920`、`docs/decisions.md:18074-18084`、`parent-measurements.md:142-164`。  
   **具体的な失敗シナリオ:** 新 pin `511c...` の dedicated pilot を一度成功させると、全 cell の key `(freeze, holdout, configuration, 511c..., pegasus, floor_role)` が作成される。しかし result は `eligible_for_refreeze=false`。後日 official を開いて同じ protocol で測ると、mode と protocol hash は key に入らないため同じ claim path に衝突し、`FileExistsError` から拒否される。旧 pin と新 pin が分離されるという狭い主張は正しいが、pilot と将来 official は分離されない。  
   **深刻度:** blocker

4. **主張:** attempt record は起動前検査にしか使われず、成功成果物へ durable に束縛されない。記録が後から消えても成功状態が残る。  
   **file:line:** `s2-plan.md:74-75,79,98-99,125`、`orchestrator/campaign/s8b_holdout_admission.py:881-898,1927-1938,1965-2006`、`orchestrator/campaign/s8b_floor_contract.py:52-73`、`orchestrator/campaign/s8b_floor_campaign.py:5110-5127`、`tools/pegasus/floor_campaign.sh:1125-1140`。  
   **具体的な失敗シナリオ:** record を作成し、campaign と専用 holdout entrypoint の照合を通した直後、別 process が `floor-remeasurement-attempt.json` を unlink する。claim、ledger inspector、manifest、result、job-result のいずれにも record の `{path,sha256}` が無く、liveness も record を成功条件にしないため、driver は rc=0 と completed result を残せる。入力と事実の記録が欠けた再測定が成功扱いになる。  
   **深刻度:** blocker

5. **主張:** versioned protocol の測定結果を受け取る v2 consumer が scope から落ちている。専用 lane の producer を作っても、既存 refreeze 経路は必ず拒否する。  
   **file:line:** `orchestrator/campaign/s8b_holdout_freeze.py:1280-1336`、`orchestrator/campaign/s8b_floor_campaign.py:962-986`、`orchestrator/campaign/s8b_verdict.py:1005-1027`、`s2-plan.md:74-78,132`。  
   **具体的な失敗シナリオ:** 仮に versioned protocol `P1` で official、`eligible_for_refreeze=true` の result を作れたとしても、v2 builder は固定 `output/s8b-freeze/floor_protocol.json` の legacy `P0` を読み、result の `protocol_sha256` が `P0` と同一であることを要求する。`P1` は contract/pin が異なるため必ず拒否される。実際の pilot result はその前に official path、mode、eligible の三検査でも拒否される。したがって新しい床値表は ratified freeze に到達せず、verdict は旧表のままである。  
   **深刻度:** blocker

## 反証できなかった主張

- `HELD_CHECK_IDS`、件数、SHA-256 の三つ組を変更または迂回する経路は見つからなかった。`freeze_verification_hold.py:14-48,68-76` は自己整合と `status="held"` を維持し、プランも snapshot 以外へ使っていない。
- `_CHAIN_RECORD_PATTERNS` は変更対象外である。`s8b_floor_campaign.py:3802-3876` は未知 file を拒否し、既存 chain record は path と bytes hash を `clean_scan_digest` に含める。新しい緩い pattern による穴は見つからなかった。
- record は verdict から参照されず、AI reseal は contract と pin 以外を継承するため、現在の scale tolerance や faster/no-difference 境界を直接動かす経路は見つからなかった。
- record producer は driver より前、campaign 側の照合も build・`runner.run()` より前に置く計画であり、計測 inner loop に記録分岐が入る証拠はなかった。
- record schema は固定 literal、hash、制約済み ID が中心で、外部の自由記述 bytes を指示として運ぶ経路は見つからなかった。
- 旧 pin と新 pin は `_key_fields()` の `ccbench_pin` で分離される。崩れたのはその主張ではなく、新 pin の pilot と official が同じ key を共有する点である。
- 標準 submitter は fresh nonce と明示的な `qsub -v` リストを使うため、古い login-shell marker が偶然一致する経路は反証できなかった。PBS が指定外環境を継承するかは repo から確定できず、未確認の懸念に留める。

## 総括

NO-GO。専用 lane は記録追加だけでなく、authority と受理集合を変更している。  
特に pilot が将来 official の一回性 key を焼く点と、record が成果物へ束縛されない点は実走前に塞ぐ必要がある。  
held 三つ組、freeze allowlist、現行 verdict 境界への直接変更は確認しなかった。  
静的検査のみであり、テスト実行、編集、commit は行っていない。