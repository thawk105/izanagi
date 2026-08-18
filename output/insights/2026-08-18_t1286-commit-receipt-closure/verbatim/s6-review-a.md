## 総括

NO-GO。  
`wal.append` の lock 束縛が receipt 自身との自己照合になっており、lock 差替えを実 sink が拒否しない。  
さらに primary issuer と replay の2経路で、実 verifier を走らせず live receipt を生成できた。  
批准 gate、v1 発火、明示 opt-in fixture、既存 `len==2` / `len==4` は維持されている。  
pytest は実行せず、静的検査と書込みなしの in-memory probe のみ行った。

### [RA-1] WAL receipt の lock 束縛が恒真
- 分類: real
- 場所: `orchestrator/verifier/commit_receipt.py:354`, `orchestrator/campaign/wal.py:446`, `orchestrator/tests/test_t1286_commit_receipt.py:159`
- 攻撃または欠落: lock A で receipt を発行後、同じ contract H を持つ有効な lock B に差し替えて `wal.append` する。validator は `core["lock_identity_sha256"]` を同じ receipt の値と比較するだけなので通り、後段 topology も raw lock 全体ではなく contract H しか比較しない。差替え負対照も fix で production sink 呼出しから standalone validator 呼出しへ弱められた。
- 成果物影響: lock B の certified campaign に、lock A に束縛された COMMIT が混入し、選択・レポートが誤った campaign identity を参照する。
- 最小修正: `wal.py:446` から、lock が存在する場合はその raw bytes の SHA-256 を `validate_live_receipt` へ渡す。lockless 正例は維持し、`test_t1286_commit_receipt.py:166` を再び `wal.append` 直接負対照にする。

### [RA-2] caller-built serialized receipt から replay receipt を発行できる
- 分類: real
- 場所: `orchestrator/verifier/commit_receipt.py:201`, `orchestrator/verifier/commit_receipt.py:374`, `orchestrator/verifier/commit_receipt.py:397`
- 攻撃または欠落: caller が `certified=true`、任意 result hash、任意 process-seal hash を持つ dict を作り、公開アルゴリズムで `receipt_id` を計算する。`admit_replay_evidence` は certified view capability を要求せず、この dict から `ReplayVerificationEvidence` を発行し、続いて live `CommitReceipt` を生成できた。
- 成果物影響: verifier 未実走の fitness を guided WAL の certified COMMIT として記録でき、候補選択とレポート値を汚染する。
- 最小修正: `commit_receipt.py:374` で裸の mapping/hash を authority にしない。`replay.py:184-217` の exact `CertifiedCampaignView` admission が発行する非公開 capability と source record を必須入力にし、caller-built dict の負対照を追加する。

### [RA-3] caller-built VerifyResult から primary receipt を発行できる
- 分類: real
- 場所: `orchestrator/verifier/commit_receipt.py:92`, `orchestrator/verifier/commit_receipt.py:133`, `orchestrator/verifier/core.py:160`
- 攻撃または欠落: `VerifyResult(trace_dir="never-read", serializable=True, n_txns=1)` を構築して import 可能な `_issue_verification_capability` へ渡すだけで capability が得られ、live receipt の発行まで成功した。trace parser/verifier entrypoint は一度も呼ばれない。
- 成果物影響: verifier 未実走の variant を新規 campaign/qualification ledgerへ certified COMMIT として投入できる。
- 最小修正: `commit_receipt.py:133` の「既成 VerifyResult を受け取る issuer」を削除し、`core.py:160-168` の実 verifier invocation 内だけで capability を生成する。caller-built `VerifyResult` が receipt に到達しない負対照と issuer call-site census を追加する。

### [RA-4] 単位Bが列挙した既存 consumer test が2本未移行
- 分類: real
- 場所: `orchestrator/tests/test_p3_s4_loop.py:2293`, `orchestrator/tests/test_p3_s4_loop.py:2335`
- 攻撃または欠落: どちらも receipt 無しで production `wal.log(...STAGE_COMMIT...)` を呼ぶため、現在は `_resolve_duplicate` の検査前に `CommitReceiptError` になる。単位B報告で所有外 caller として列挙されたが、後続 fix の変更対象に入っていない。
- 成果物影響: committed duplicate の成功復元・再resolve禁止を受入で検査できず、whiteboard と選択レポートの重複候補分類が無防備になる。
- 最小修正: `test_p3_s4_loop.py:2293,2335` を、歴史 WAL fixture なら `append_legacy_raw_commit`、新規 write の検査なら正規 receipt helper 経由へ移す。

### [RA-5] 批准 gate を通らない production certified-lock 生成経路
- 分類: refuted
- 場所: `orchestrator/campaign/ident.py:234`, `orchestrator/campaign/ident.py:443`, `orchestrator/campaign/campaign_lock.py:255`
- 攻撃または欠落: production の v2 encoder 呼出しは `ident.ensure_campaign_identity` の1件だけで、その直前に批准比較がある。`wal.write_lock` や codec 直呼びは test/support、`s8b_oracle_driver.py` の直接 lock は別形式の v1 one-shot lockだった。現行 closure に対する読み取り probe も台帳0行として実際に拒否した。
- 成果物影響: なし。未批准 closure から production の新 certified lock は生成されない。
- 最小修正: なし。

### [RA-6] 批准 fixture が autouse 化し負対照を殺している
- 分類: refuted
- 場所: `orchestrator/tests/conftest.py:137`, `orchestrator/tests/test_t671_source_binding.py:416`
- 攻撃または欠落: fixture は `autouse=True` ではなく、各正例が `usefixtures` で明示 opt-in している。未批准負対照は fixture を要求せず、`ident.ensure_campaign_identity` の production 経路を直接通して lock bytes 不在まで確認している。
- 成果物影響: なし。未批准 digest の拒否集合はテスト空間でも生きている。
- 最小修正: なし。

### [RA-7] v1 では receipt gate が発火せず、既存設計テストも緩和された
- 分類: refuted
- 場所: `orchestrator/campaign/wal.py:446`, `orchestrator/tests/test_t1286_commit_receipt.py:127`, `orchestrator/tests/test_campaign.py:7119`, `orchestrator/tests/test_t674_qualification_contract_lanes.py:302`
- 攻撃または欠落: repo の lock は32件すべてv1、v2は0件、永続 receipt は0件だったが、sink gate は lock version でなく `record.stage` に掛かる。v1へ receipt 無しで直接 append する負対照も存在する。`len(commit_calls)==2` と `len==4` は不変で、skip/xfail 化もない。legacy receiptless replay/recovery と lockless正例も残る。
- 成果物影響: なし。ただし raw-lock 束縛だけは RA-1 のとおり閉じていない。
- 最小修正: RA-1 の修正のみ。

## nit

- `orchestrator/tests/test_s6_sort_sweep.py:625` と `orchestrator/tests/test_s8a_trigger_sweep.py:834` の docstring は、単位C報告どおり現在も `exact 14-path` のまま。fixture 本体は動的25 pathなので挙動影響はない。