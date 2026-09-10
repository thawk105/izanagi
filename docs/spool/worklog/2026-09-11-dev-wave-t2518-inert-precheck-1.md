---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2518-inert-precheck
seq: 1
title: [T-2518] 実装差分ゼロで既存経路の接続不足を記録する (docsのみ)
---

## 本文

- ユーザーの既存機構限定 precheck として、接続を確認できない場合の記録分岐を採った。
- CLI・A→B→C適用・依存ソース・generic dispatchは実在。依存供給後に当該木とclean stockをCLIへ渡す既存入口は確認できなかった。
- configure/build/測定は未起動。gflags不足のconfigure-failedをstock-inert-mismatchや意味の赤に読み替えていない。
- T-2417のprobe・13macro witness・production関門は変更せず、実装面差分は0。
- 初回に残した専用googletestの未確定HEADは、再開時に欠落ローカル参照の作成と標準submodule初期化で復旧した。共有main・remote・hook設定は非変更。
- 関連テストはrun_tests.py経由で164 passed / 38.00秒。初期化・resume startupもrc0。テスト無効化は0件。
- 初回最終受入は23047 passed / 68 skipped / 21 error。初回中断のfetch-pack保持マーカーが専用googletestに残り、snapshotの不要object整理を妨げていた。親の復旧漏れとしてorphanなマーカー1件を除去した。
- 復旧後の焦点テストは991675.nqsv/bnode033で1 passed/17.05秒。Pre-running待ちで親がrunnerを中断した記録(rc16)とchild正常終了(rc0)を分け、終端後にholdを解除して受入を再走する。
- 詳細 = `output/insights/2026-09-11/t2518-inert-precheck/README.md`。inert実測そのものは未完としてT-2518を更新する。
- dev-wave改善候補は初期化エラーの元Git診断への導線。handoffへ記録のみ、改善実装・次wave起動・pushは行わない。

## 次の一手差分

### 更新

- [T-2518] **P2**: A+B+C適用木のinert要求とclean stockのsupply比較は未実測。
  既存経路precheckでは、依存prefix/FetchContentの供給と当該CLI入力をつなぐ入口を確認できなかった。
  最小の接続を別の実装単位で用意するかを判断し、接続成立後だけ計算ノードで実測する。
  13macro witness新設・production配線は含めない。根拠は2026-09-11のT-2518 insight。
  base: 490edf10a7c7b67d48eea51c3042dec0baa5ae76a7f4c8a3042a35471239ad92
