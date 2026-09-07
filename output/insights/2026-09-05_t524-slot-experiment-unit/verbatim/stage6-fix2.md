## 直した内容

- R1 — [s8c_acceptance_receipt.py:2013](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/s8c_acceptance_receipt.py:2013): `require_current_verified_receipt` が v5 のみを許可し、その後 fresh verify で attempt registry 束縛を再検査するよう変更。
- R2 — [s8c_acceptance_receipt.py:1543](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/s8c_acceptance_receipt.py:1543): registry の `manifest_sha256` と全行の P を外側 receipt に exact 束縛。[s8c_acceptance_receipt.py:1577](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/s8c_acceptance_receipt.py:1577) で receipt の P 時点の blob が存在し、現 prefix の先頭であり、genesis 1 行だけであることを要求。
- R3 — [s8c_acceptance_receipt.py:1795](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/s8c_acceptance_receipt.py:1795): issuer と同じ `rev-list --all`、全 tree path、strict prefix、graft/replace/shallow 拒否へ統一。別 ref の第二 root 負例は [test_s8c_acceptance_receipt_v2.py:1116](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1116)。
- R4 — [test_reflux_originless_compatibility.py:205](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_reflux_originless_compatibility.py:205): `attempt_registry_prefix_bytes` を hash と同じ揮発根拠で leaf 集合へ追加。
- R5 — [test_s8c_acceptance_receipt_v2.py:1164](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1164): terminal を全件残し、receipt 側の `slot_id` だけを変える M3b 負例を追加。
- R2/R3 用に fixture の genesis を P 時点で追跡するよう [test_s8c_acceptance_receipt_v2.py:140](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:140) を更新。

## R1 の波及

静的検索で確認した production 経路は次の全件です。

- 直接利用者: [layer3_report.py:696](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/layer3_report.py:696) の `build_accepted_report`。
- 間接利用者: 同ファイルの `render_accepted`。
- v1 の通常 verify 正例は維持し、[test_s8c_acceptance_receipt.py:162](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_s8c_acceptance_receipt.py:162) の downstream 期待だけを拒否へ変更。
- v4 の readable 契約は維持し、[test_s8c_acceptance_receipt_v2.py:1032](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_s8c_acceptance_receipt_v2.py:1032) で downstream 到達を拒否。
- [test_layer3_report.py:1718](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_layer3_report.py:1718) は non-certifying 分岐自体を mock で保持。
- [test_layer3_report.py:1742](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/tests/test_layer3_report.py:1742) は実 v1 receipt が書込み前に schema 拒否される期待へ変更。
- 同ファイルの残る参照は unsealed capability 検査 1 件と monkeypatch 利用 7 件で、旧 schema の downstream 到達経路ではありません。

## 変異耐性の自己検査

M3b は receipt の先頭 unit の `slot_id` だけを変更します。registry prefix、全 terminal、report hash、manifest/P 束縛は変更しません。

[s8c_acceptance_receipt.py:1599](/work/1/SFC/tanab/izanagi/.codex/worktrees/t524-fix2/orchestrator/campaign/s8c_acceptance_receipt.py:1599) の projection 再照合だけを無効化すると、後続処理は registry 由来の `derived_projection` を使います。全 terminal がそろい、trial tuple も変えていないため他の拒否は発火せず、テストは `DID NOT RAISE` で赤くなります。

反対に消費検査だけを無効化しても、1599 行の projection 不一致が期待どおり発火します。したがって別理由の赤にはならず、M3b は projection 再照合へ単一帰属します。

## 実走したテスト

実装済み・未実走です。

指定コマンドを `tools/run_tests.py` 経由で試みましたが、`qstat -Q preflight rc=1` により dispatch infrastructure failure、`rc=16`、`child_started=false` でした。0 nodeid が開始されたため、passed とは報告しません。

非テスト検査として、変更 5 ファイルの `py_compile` と `git diff --check` は成功しています。

## 受理・拒否挙動の変化

- v1〜v4 の parse と通常 verify は引き続き可能です。
- downstream capability は v5、現物 registry、外側 manifest/P、P 時点 genesis-only、全 ref 単一 root、projection、全 unit 消費のすべてを満たす場合だけ到達可能です。
- 追加した分岐はすべて拒否側です。既存の受理集合は広がっていません。
- `replicate_index > 0`、`not-consumed`、独立 clone 間の扱いは変更していません。

## 親の裁定が要る点

なしです。契約や期待値を緩める必要はありませんでした。独立 clone 間の best-of-N など、裁定で scope 外とされた面には触れていません。

## 総括

R1 の legacy downgrade を downstream 入口で閉じました。  
R2/R3 は issuer の既存 gate と同じ境界へ揃えました。  
R4 と単一理由の M3b 負例も追加済みです。  
docs、freeze JSON、`CLAUDE.md`、`AGENTS.md` は未変更です。  
commit と push は実行していません。