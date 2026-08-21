# 2026-08-21 rulings / rr80-rr20 calibration / main land handoff
- 目的: rr80/rr20 calibration を AI/ツール側で安全に登録できる経路を実装し、裁定と成果を local main へ land する
- 状態: 作業中
- 最終更新: 2026-08-21
- 基準コミット: 46fbce3d7151044c9450bdf3f422ea839e7fcc0f (worktree: worktree-rulings-20260821-calibration-registration)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- `/rulings all` のユーザー裁定内容を確認し、AI/ツール側の calibration 登録方針を明文化した。
- `tools/pegasus/submit_certify.sh` と `tools/pegasus/certify_calibration.sh` の rr80/rr20 workload
  binding 実装、および `orchestrator/tests/test_pegasus_calibration_workload.py` の targeted test を作業中。
- `python3 tools/run_tests.py orchestrator/tests/test_pegasus_calibration_workload.py` は 5 passed。
- `python3 tools/check_docs.py` と `python3 tools/spool_fold.py --dry-run --show-diff` は成功。

## 未完の作業と次の一手 (具体的に)

既存の推奨方針は受け入れる。ただし rr80/rr20 calibration の取得・検証・登録を人間の手作業に
残すことは受け入れない。既存の自己比較、schema、acquisition receipt、hash binding、fail-closed
gate を維持したまま、AI/ツールが計算ノードで測定し、自動 publish できる経路を用意する。

正式 H1/H2 launch、g1→g2 activation、D145/T-424/T-272 の別の承認・閉包をこの較正登録だけで
代行したとは扱わない。

## 現状確認

- `output/env/pegasus/calibration/registered/` の既存2件は rr50。rr80/rr20 は未登録。
- `tools/pegasus/submit_certify.sh` と `tools/pegasus/certify_calibration.sh` は workload を rr50 に固定。
- `pegasus02` は login node として重い計測を直接行わない。queue `gen_S` は利用可能で、計測は PBS job body で行う。
- land lease は別 holder が保持中。holder を奪わず、空くまで land を保留する。

1. script / submitter の実装を commit し、関連テストと受入形検査を完了する。
2. `tools/pegasus/submit_certify.sh --rratio 80` と `--rratio 20` を、clean commit 上で計算ノードへ投入する。
3. job 終了後に collector を compute node で実行し、quality・final receipt・registered artifact を確認する。
4. spool fragment を land lock の中で fold し、受入 receipt が揃ったら local main へ ff-only land する。
5. push は行わない。remote への反映は人間が行う。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- `pegasus02` では重い計測を直接起動しない。queue `gen_S` は確認済みだが、投入は login-side submitter、
  build/calibration は PBS compute job body の責務。
- land lease は別 holder が保持中 (`holder=b73c0a8f1038`、2026-08-21確認)。holder を release/steal せず、
  空くまで land を保留する。
- 既存登録2件は rr50。rr80/rr20 の artifact が無いことを確認してから投入する。rejected attempt の JSON を
  修正して登録してはならない。
