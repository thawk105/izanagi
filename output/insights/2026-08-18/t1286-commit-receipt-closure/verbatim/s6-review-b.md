## 総括

**NO-GO。** verifier capability の再利用・非束縛により、無関係な正常 trace から任意 COMMIT receipt を量産できる。  
ambient `PATH` の偽 Git は closure と批准履歴の両方を偽装でき、未批准 digest から新 v2 lock が作れる。  
現行 call graph の独立導出自体は同じ exact 25、S8C exact 3、consumer 更新に到達した。  
pytest は指示どおり実行せず、静的検査のみ。

### [RB-1] verifier capability が operation に束縛されず再利用できる

- 分類: real
- 場所: `orchestrator/verifier/commit_receipt.py:121-135,295-327`; `orchestrator/verifier/__init__.py:16-30`; `orchestrator/tests/commit_receipt_support.py:25-52`; `orchestrator/tests/test_t1286_commit_receipt.py:410-437`
- 攻撃または欠落: `VerificationCapability._assert_intact()` は PID・seal・certified を見るだけで消費済みにせず、variant・operation・sink・lock・workload とも束縛しない。実際、test helper は `g1_serial` の capability を cache して異なる receipt に繰り返し使う。正常 trace を一度検証すれば、`issue_commit_receipt()` の caller が指定する任意の variant/payload/operation 用に別々の receipt IDを量産できる。さらに「production 5 件 census」は `pipeline.py` と `guided.py` しか走査せず、別 production file からの issuer/sink 呼出しを検出しない。
- 成果物影響: 未検証 candidate の COMMIT が verifier evidence 付きとして WAL または qualification ledger に入り、certified 選択・fitness・qualification result の受理集合が増える。
- 最小修正: `commit_receipt.py:92-135` で capability 発行時に operation/variant/workload/sink/lock context を焼き込み、`issue_commit_receipt()` で完全一致と一回消費を要求する。`test_t1286_commit_receipt.py:410-437` は全 production Python を走査し、issuer・replay issuer・両 sink の file/function 集合を固定する。capability 再利用と別 operation への転用を直接拒否する負対照も追加する。

### [RB-2] ambient PATH の偽 Git で批准台帳を合成できる

- 分類: real
- 場所: `orchestrator/campaign/enforcement_source_ratification.py:31-39,149-185,223-304`; `orchestrator/campaign/contract_loader_binding.py:244-292`
- 攻撃または欠落: 両 verifier が `PATH` を許可し、`shutil.which("git")` の結果を無検証で実行する。偽 Git は `rev-parse --show-toplevel` に期待 root、`rev-parse HEAD` に任意 SHA、closure の `cat-file` に実 disk bytes、批准側の `log/cat-file` に対象 digest を含む架空 JSONL を返せる。closure bytes や本物の `hooks/` 台帳を変更する必要がない。
- 成果物影響: 実台帳に無い closure digest が批准済みと判定され、弱化した enforcement bytes で新 certified v2 lock を作れる。
- 最小修正: 両 file の Git 解決を `orchestrator/preregistration/blobref.py:30-40,232-243` と同等の固定絶対 executable・hardening に寄せ、子環境から `PATH` を除く。偽 Git を先頭に置いた `PATH` で fail-closed になる負対照を追加する。

### [RB-3] exact 25 の現行 production call graph は独立導出と一致する

- 分類: refuted
- 場所: `orchestrator/campaign/campaign_lock.py:29-55`; `orchestrator/tests/test_t671_source_binding.py:23-56`
- 攻撃または欠落: 現行の実支配点を再追跡すると、従来 14、S8C 3、批准自己保護 3、receipt 面 5 の同じ 25 に到達した。追加対象は見つからず、25 内の過剰 member もない。ただし RB-1 の公開 issuer/census 穴により、「現在存在する依存集合」としては exact でも、新 producer 追加に対する防御閉包にはなっていない。
- 成果物影響: 現行 25 の member 選択自体による certified 集合の余分な停止や見落としはない。受理集合を増やす実害は RB-1 と RB-2 に分離できる。
- 最小修正: 25 は維持し、RB-1/RB-2 修正後に再導出する。`orchestrator/qualification/t126_evaluation_event_schema.json` は schema 単独弱化では `artifacts.py:963-1092` の exact semantic/receipt 検査を越えられず、追加しない。`orchestrator/qualification/contract.py` も receipt authority ではないため追加しない。

### [RB-4] closure consumer の機能更新漏れはない

- 分類: refuted
- 場所: `orchestrator/campaign/artifact_admission.py:177,743-747`; `orchestrator/campaign/contract_loader_binding.py:74-79,330-391`; `orchestrator/campaign/enforcement_source_ratification.py:81-90`
- 攻撃または欠落: stage 3 時点の production/test-support consumer は、hard-coded fixture の `test_t671_source_binding.py` と `test_artifact_admission.py` が exact 25 に更新され、残りは定数の動的反復なので変更不要だった。新設 ratification module と新設 tests が consumer 一覧へ増えたのも意図どおり。`approval_d291.py` と `test_s8c_preregistration_predicates.py` の無関係な `14` は差分ゼロだった。
- 成果物影響: stale 14-key map による lock codec・E1 admission の誤拒否や、無関係な publication/evidence 契約の破壊は確認できない。
- 最小修正: 機能修正不要。docstring の nit だけ下記参照。

### [RB-5] テスト用批准 root 注入は通常の production 入力には露出していない

- 分類: refuted
- 場所: `orchestrator/tests/conftest.py:137-179`; `orchestrator/campaign/enforcement_source_ratification.py:26,208-235`
- 攻撃または欠落: fixture は opt-in pytest fixture で、production は `conftest.py` を import しない。production API に alternate-root 引数や root 環境変数はなく、相対 path は固定、root は strict resolve と Git top-level 一致を要求する。private module global を任意の同一 process Python が monkeypatch できる点は残るが、それは他の verifier 関数自体も差し替えられる一般的な in-process arbitrary-code modelであり、この fixture 固有の到達 seam ではない。実際の ambient 迂回は RB-2 の `PATH`。
- 成果物影響: 現行 production call から pytest の仮台帳が選択され、未批准 digest が受理される経路は確認できない。
- 最小修正: 必須修正なし。防御強化するなら production entrypoint は root を毎回 module location から導出し、temporary-repo helper は test-only adapter に分離する。

### [RB-6] 受理集合は実際に狭まり、legacy 正例は低層で維持される

- 分類: refuted
- 場所: `orchestrator/campaign/ident.py:234-247`; `orchestrator/campaign/wal.py:408-463`; `orchestrator/qualification/artifacts.py:774-870`; `orchestrator/campaign/replay.py:179-250`
- 攻撃または欠落: 恒真 gate ではない。従来通った「HEAD と disk が自己整合するが未批准の新 v2 lock」「receipt 無し・直列化 dictだけ・同一 receipt 二回目・fork 後流用の COMMIT」「receiptless source を使う guided COMMIT」が今後拒否される。一方、既存 v1 receiptless WAL の `wal.replay/recover_interrupted_attempts`、issuer-bound receipt の lock 無し layout、historical/legacy artifact lane は残る。
- 成果物影響: post-policy の未認証 COMMIT は certified 集合から減り、既存 historical raw/recovery の参照集合は維持される。ただし RB-1 の capability 転用入力はまだ拒否されない。
- 最小修正: RB-1 の負対照を加える。それ以外の compatibility 分岐は維持する。

### [RB-7] S8C 判定器は exact 3 で閉じる

- 分類: refuted
- 場所: `orchestrator/campaign/s8c_preregistration.py:46-48,1571-1641,1661-1726`; `orchestrator/campaign/s8c_preregistration_evidence.py:18`; `orchestrator/campaign/s8c_generation_projection.py:1-15`
- 攻撃または欠落: core は固定名で evidence evaluator と projection を動的 importし、各 live bytes を指定 commit blob と照合する。evidence の project-local import は core のみ、projection は project-local import を持たない pure leaf。evidence が commit tree 内の他 module を読む処理は評価対象データの reachability 解析で、実行判定器 dependency ではない。
- 成果物影響: `s8b_oracle_judge.py` 等の無関係な変更で campaign 全体を停止せず、現行 preregistration verdict を決める 3 module の変更は closure digest を変える。
- 最小修正: なし。

### [RB-8] receipt/closure 関連の設計テスト反転・skip 化はない

- 分類: refuted
- 場所: `orchestrator/tests/test_campaign.py:7082-7119`; `orchestrator/tests/test_t674_qualification_contract_lanes.py:277-302`; `orchestrator/tests/test_t1286_commit_receipt.py:127-407`
- 攻撃または欠落: `len(commit_calls)==2` と qualification の `len==4` は維持され、追加 skip/xfail はゼロ。低層 WAL mechanics の一部 fixture は `STAGE_COMMIT` から `STAGE_BUILD_DONE` へ移ったが、production sink を直接駆動する receipt 無し・serialized dict・duplicate・fork・qualification の負対照が新設されている。`test_coder_effect_gate.py` の assert 削除は取り込み済み T-396 の別契約変更で、receipt/closure の期待反転ではない。
- 成果物影響: 既存の verify 前 COMMIT 検出や qualification producer 数を弱める変更はない。ただし RB-1 の repo-wide census と capability 転用ケースは未検査。
- 最小修正: RB-1 記載の census・転用負対照を追加する。

## 裁定パッケージ候補

- `validate_live_campaign_wal_receipt()` は actual layout の lock を再読せず issuer-burned identity を使うため、同じ receipt を異なる layout/WAL で各一回消費できる。段 4 が ledger 単位の single-use と裁定済みなので本 wave の must-fix にはしない。全 layout 横断一回性が必要なら外部消費台帳が要る。
- `s1_report.py` 等の certified consumer における durable receipt 再検証は段 4 で scope 外。producer 保証だけで十分か、historical raw 型へ限定するかは別裁定。
- 批准台帳を closure 外に置く自己参照回避は妥当。ただし「人間批准の証明」や外部 trust root ではないという段 4 の制限は維持する。

## nit

- `orchestrator/tests/test_s6_sort_sweep.py:625` と `orchestrator/tests/test_s8a_trigger_sweep.py:834` の docstring が `exact 14-path` のまま。fixture 本体は定数を動的反復するため受理集合への影響はないが、`exact 25-path` へ直すべき。