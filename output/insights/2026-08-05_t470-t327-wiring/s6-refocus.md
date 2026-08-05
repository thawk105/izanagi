## 対応表

| 所見 | 判定 | 根拠・判定理由 |
|---|---|---|
| R1-1 | closed | report/run-start の admission 必須・一致・再導出が実装された。`orchestrator/campaign/trial_registry.py:2195-2219`、`orchestrator/campaign/autonomous_trial_completeness.py:379-425`。ただし mutation test の穴は X-3。 |
| R1-2 | regressed | `_finish_trial` の再導出は入ったが、lifecycle token は全 authority field を持つ copyable dataclass のまま。`orchestrator/campaign/trial_registry.py:151-166,1569-1627`。X-2。 |
| R1-3 | regressed | `certifying_input` は追加されたが、generic `build_report()` / `render()` が裸の `True` を受け、receipt なしで発行できる。`orchestrator/campaign/layer3_report.py:392-398,497-498,565-576`。X-1。 |
| R1-4 | partial | sealed public scope 内の T-276 test は復元済み。`orchestrator/tests/test_p3_autonomous_workload_trial.py:1018-1056`。一方、実 `python -m` entrypoint test は今も `python -c` と activation monkeypatch に置換されたまま。`orchestrator/tests/test_trial_registry.py:1253-1283`。 |
| R1-5 | partial | lifecycle は prefix 束縛になった。`orchestrator/campaign/s8c_acceptance_receipt.py:606-613`。しかし registry は全体 hash の exact 比較のままで、後続 manifest 登録で既存 receipt が失効する。`orchestrator/campaign/s8c_acceptance_receipt.py:604-605`、`orchestrator/campaign/trial_registry.py:2330-2333`。 |
| R1-6 | partial | manifest 再 hash は追加済み。だが verifier は参照 bytes の自己整合だけで producer acceptance を再実行せず、任意 bytes の正例 fixture が依然通る。`orchestrator/campaign/s8c_acceptance_receipt.py:591-621`、`orchestrator/tests/test_s8c_acceptance_receipt.py:62-120`。 |
| R1-7 | closed | lifecycle start 後の準備処理と本処理が terminalization 境界に入り、失敗時は indeterminate を試行する。`orchestrator/campaign/p3_autonomous_workload_trial.py:1898-1972,2052-2055`。 |
| R1-8 | partial | lifecycle の committed history 検査は追加済み。`orchestrator/campaign/s8c_acceptance_receipt.py:501-540`。receipt 自体は現在 path の `O_EXCL` と現在 HEAD しか見ず、削除・再作成履歴を検出しない。`orchestrator/campaign/trial_registry.py:2069-2078`、`orchestrator/campaign/s8c_acceptance_receipt.py:598-602`。 |
| R1-9 | parent-pending | docs は親が対応する明示裁定。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/prompt-s6-fix.md:123`。 |
| R1-10 | out-of-scope (親裁定) | U-B。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s4-ruling.md:37`。 |
| R1-11 | out-of-scope (親裁定) | U-A。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s4-ruling.md:36`。 |
| R1-12 | out-of-scope (親裁定) | U-C/U-F。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/s4-ruling.md:38,41`。 |
| R2-1 | closed | acceptance 独立境界でも admission 欠損・不一致・再導出差を拒否する。`orchestrator/campaign/trial_registry.py:2195-2219`。 |
| R2-2 | regressed | production P3 は false を投影するが、generic Layer 3 writer に `True` の無権限経路が新設された。`orchestrator/campaign/p3_autonomous_workload_trial.py:1157-1176`、`orchestrator/campaign/layer3_report.py:392-398,497-498`。X-1。 |
| R2-3 | closed | CLI preflight を通らない programmatic `run_trial(rr80)` が U-4 exact reason を検査する。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2676-2714`。 |
| R2-4 | closed | 下位 helper を fail spy にした m07 test が外側 commit 検査を単独で照準する。`orchestrator/tests/test_trial_registry.py:830-857`。 |
| R2-5 | closed | untracked と HEAD mismatch の reason code が分離され、untracked test は末尾まで一致する。`orchestrator/campaign/s8c_acceptance_receipt.py:598-602`、`orchestrator/tests/test_s8c_acceptance_receipt.py:172-178,231-241`。 |
| R2-6 | closed | 非空 validator と mandatory-reason validator が分離され、それぞれ direct test を持つ。`orchestrator/campaign/s8c_acceptance_receipt.py:210-231`、`orchestrator/tests/test_s8c_acceptance_receipt.py:256-271`。 |
| R2-7 | closed | manifest を含む5種すべてが再 hash 対象。`orchestrator/campaign/s8c_acceptance_receipt.py:604-620`、`orchestrator/tests/test_s8c_acceptance_receipt.py:191-228`。 |
| R2-8 | closed | v3 reader は新 field を required にせず、欠落を非認証として受理する。generator は常時発行。`orchestrator/campaign/layer3_report.py:202-225,497-498`、`orchestrator/tests/test_layer3_report.py:398-408`。 |
| R2-9 | parent-pending | docs は親対応。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t470-t327-wiring/prompt-s6-fix.md:123`。 |
| R2-10 | closed | T-276 は public `run_trial()` が発行した scope 内で再検査される。`orchestrator/tests/test_p3_autonomous_workload_trial.py:1018-1056`。 |
| R2-11 | closed | nodeid 文字列の恒真 meta-test はなくなり、実 verifier の意味的負例へ置換された。`orchestrator/tests/test_s8c_acceptance_receipt.py:161-302`。 |

重点確認した fallback admission は `test_trial_registry.py` 内の fixture 限定です。欠落 report 用の合成 admission は `orchestrator/tests/test_trial_registry.py:620-630` にしかなく、production は lifecycle を読む前に6 report 件数を拒否し、さらに admission 欠損を拒否します。`orchestrator/campaign/trial_registry.py:2109-2110,2195-2205`。この fallback 自体の production fail-open はありません。

## 新規所見

### X-1

- 深刻度: blocker
- 主張: generic Layer 3 writer が verified receipt なしで `certifying_input:true` を発行できる。
- 根拠: `build_report()` と `render()` は公開 bool 引数をそのまま report に入れ、`acceptance_receipt` は常に `None`。`orchestrator/campaign/layer3_report.py:392-398,497-498,565-576`。receipt gate は別関数にしかない。`orchestrator/campaign/layer3_report.py:507-560`。test も `False` と非-bool しか検査せず、裸の `True` を拒否しない。`orchestrator/tests/test_layer3_report.py:411-428`。
- 失敗シナリオ: 任意の admitted campaign に `render(..., certifying_input=True)` を呼ぶと、schema-valid な `{"certifying_input":true,"acceptance_receipt":null}` が永続化される。
- 成果物影響: Layer 3 reader の受理集合に、receipt と無関係な「認証入力」材料レポートが加わる。
- 提案: generic `build_report` / `render` は false 固定に戻す。true と receipt 投影は `VerifiedAcceptanceReceipt` を必須とする内部経路で同時に行い、`true ⇔ acceptance_receipt非null` の cross-field invariant を検査する。

### X-2

- 深刻度: blocker
- 主張: lifecycle token は seal を保持したまま全 binding field を `dataclasses.replace` でき、fresh issuance ではなく caller が選んだ start row との自己一致しか検査しない。
- 根拠: token の ledger path、trial、run root、二つの hash は全て dataclass field。`orchestrator/campaign/trial_registry.py:151-166`。terminal 側は `_seal` と token 指定 ledger 内の row しか照合しない。`orchestrator/campaign/trial_registry.py:1569-1627`。既存 test は `trial_id` 一項目だけを変更するため、全連動 field の置換を検出しない。`orchestrator/tests/test_trial_registry.py:950-958`。
- 失敗シナリオ: 正規 token A を一つ取得する。別 trial B の well-shaped start row を ledger に用意し、A を B の `trial_id/run_root/start_row_sha256/launch_admission_sha256` に一括置換する。seal は保存され、B の terminal が追記される。acceptance は token の発行履歴を見ず row/report hash の一致だけで受理する。`orchestrator/campaign/trial_registry.py:1965-1990`。
- 成果物影響: receipt の lifecycle prefix と `trials[].report_sha256` が、正規 start-once token を発行されていない trial を参照できる。
- 提案: terminal は start 発行時と同一 object identity の one-shot capability のみ受ける。canonical ledger path を固定し、hash 引数を caller から受けず `token.run_root` 配下から導出する。acceptance でも start `run_root` と report/journal parent を一致させ、全 field 一括置換・別 ledger の負例を追加する。

### X-3

- 深刻度: must-fix
- 主張: F1 の再導出比較を削除しても、追加された admission test は赤にならない。
- 根拠: production の本質的 anchor は `orchestrator/campaign/trial_registry.py:2206-2219`。しかし test の二変異は「report 欠損」と「run-start 片側変更」だけで、どちらも手前の存在・相互一致検査で拒否される。`orchestrator/tests/test_trial_registry.py:464-497`。completeness も binding の manifest/arm/holdout/campaign/ratio を再導出しない。`orchestrator/campaign/autonomous_trial_completeness.py:411-425`。
- 失敗シナリオ: report と run-start の admission を同時に同じ偽 `manifest_sha256` または arm/campaign へ変更し、lifecycle の admission hash も更新する。再導出比較だけを削除した変異では既存 test が緑のまま receipt が発行される。
- 成果物影響: receipt の report/journal 参照集合へ、受理 manifest と異なる launch binding を宣言する成果物が入る。
- 提案: completeness を明示的に迂回し、report/run-start/lifecycle を同時更新した self-consistent な各 field 変異を追加する。期待 reason は「accepted binding derivation と異なる」を末尾まで一致させる。

## 変異事前登録 m01〜m17 再照合

| 変異 | 再判定 | 遮蔽確認 |
|---|---|---|
| m01 | kill | default-deny の direct/public 負例がある。`orchestrator/tests/test_trial_registry.py:722-733`、`orchestrator/tests/test_p3_autonomous_workload_trial.py:2625-2645`。 |
| m02 | kill | holdout intersection の direct 負例。`orchestrator/tests/test_trial_registry.py:736-747`。 |
| m03 | kill | 値と source 定義を検査。`orchestrator/tests/test_trial_registry.py:715-719`。 |
| m04 | kill | programmatic `run_trial()` と exact reason。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2676-2714`。 |
| m05 | kill | scope 不在を最初の境界で検査。`orchestrator/tests/test_p3_autonomous_workload_trial.py:997-1015`。 |
| m06 | kill | tampered digest の direct helper test。`orchestrator/tests/test_s8c_preregistration_core.py:736-748`。 |
| m07 | kill | 下位 helper spy により外側 anchor が単独。`orchestrator/tests/test_trial_registry.py:830-857`。 |
| m08 | kill | 同一 trial の二度目の start が直接赤。`orchestrator/tests/test_trial_registry.py:931-949`。ただし保証自体には X-2 の別バイパスがある。 |
| m09 | kill | `LOCK_EX` 呼出しを観測。`orchestrator/tests/test_trial_registry.py:976-1011`。 |
| m10 | kill | terminal 欠落の lifecycle 固有 reason。`orchestrator/tests/test_trial_registry.py:1135-1160`。 |
| m11 | kill | 二度目の receipt create が固有 reason で赤。`orchestrator/tests/test_trial_registry.py:1163-1184`。 |
| m12 | kill | untracked と HEAD mismatch が別 reason かつ末尾一致。`orchestrator/tests/test_s8c_acceptance_receipt.py:172-178,231-241`。 |
| m13 | kill | 5参照種を個別に改変。lifecycle は committed prefix を保つ suffix へ再照準済み。`orchestrator/tests/test_s8c_acceptance_receipt.py:191-228`。 |
| m14 | kill | downstream check 削除時には non-certifying receipt が先へ進み test が赤になる。`orchestrator/tests/test_layer3_report.py:431-447`。ただし X-1 の別経路バイパスがある。 |
| m15 | kill | 非空・mandatory を独立 helper test が照準。`orchestrator/tests/test_s8c_acceptance_receipt.py:244-271`。 |
| m16 | 正例保持 | flag 付き非 holdout public run が report まで到達。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2559-2599`。 |
| m17 | 正例保持 | manifest/registry なしの ycsb-a report shape を exact 検査。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2559-2599`。 |

指定された「その一箇所を無効化した場合」の kill されない疑いはありません。ただし m08 と m14 の守る保証には、それぞれ X-2 と X-1 の別経路バイパスがあります。

## 総括

**NO-GO**

- 対応表: closed **11/23**、partial **4/23**、regressed **3/23**
- 別枠: parent-pending **2/23**、out-of-scope (親裁定) **3/23**
- 新規所見: blocker **2件**、must-fix **1件**
- kill されない疑いのある変異番号: **なし**
- ただし保証バイパスが残る変異領域: **m08、m14**

親実測の 277 passed / 0 failed は確認済み前提とした。本レビューでは編集・pytest 実行を行っていない。