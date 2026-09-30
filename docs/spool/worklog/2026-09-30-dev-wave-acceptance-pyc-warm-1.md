---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-acceptance-pyc-warm
seq: 1
title: 初回受入でも shard 開始前に pyc をそろえる (md_7) — login collection を preflight 前に前倒しする実装を変異 8/8 KILLED まで固めたが、同時刻対照は 2 対とも不適格で判定不能、事前登録どおり実装は land せず記録だけ land する (docs + insight、実装は branch worktree-dev-wave-acceptance-pyc-warm に保存)
---

## 本文

- 一次資料: `output/insights/2026-09-30/acceptance-pyc-warm/README.md`。判断は {{D:login-collection-prestart-not-landed}}。
- 計算の相談 (2026-09-30、本 wave 中): 合計が約 2.1 node 時間で 2 を超える見込みを land 調整役セッション「manager: parallel land」へ 5 点で相談し GO を得た (ユーザーが 2 node 時間超の判断を同セッションへ委任済み)。条件は「事前登録の判定を結果を見た後で変えない」「受入の赤は帰属判定の前に land しない」「終了時に実測 Elapse の合計を返す」。実使用は計算ノードの job Elapse 合計 4,092 秒 = 1.14 node 時間 (land 用の縮小受入は別)。
- 同日のユーザー通達 (land 調整役の中継): 計算 job は 1 本 5 分程度に分割して多数並行、処置とノードを 1 対 1 に割り付けない。本 wave の対照 (3 shard × 各 5〜6 分、K/H を同時起動) と変異 (1 変異 1 job) は適合していた。
- 段 2 plan 1 本・段 3 相談 2 本・段 6 敵対レビュー 2 本・焦点再レビュー 1 本。段 6 は両レビューとも NO-GO で fix 1 巡 (自前 signal handler と新 process group をやめ従来と同じ意味論へ、失敗時は従来形で取り直す、`text=True` と同じ復号)。焦点再レビューも NO-GO だったが、fix を重ねず親が裁定して閉じた (取り直しの意味は主張の訂正のみ、create-only 衝突と deadline 切れは従来と同じ rc 16 で refuted、割込みの窓と locale 依存 test は backlog)。変異 8 本は最終 tip で全 KILLED (期待 node と完全一致)。
- 棄却: 焦点再レビュー所見 2 (log 公開後の例外で create-only が取り直しと衝突) と所見 4 (timeout 後の取り直しは実行できない) は、どちらも従来経路と同じ rc 16 に落ちるので refuted。
- 異常: 実装子の test が 2 回、親の焦点走でだけ赤になった (parametrize の引数名に pytest の予約名 `request`、代役 `wait_connections` が集合を返し本体の反復中 remove で例外)。どちらも子は pytest を実走していない。変異元 clone の作成で完全 SHA を推測で補完して 1 回失敗した (F1031 の再発として追記)。計測木の `git worktree add` が Lustre の EINTR で 1 回失敗し同じ手順で作り直した。途中で利用上限による中断が 1 回あり、同じ session で再開した。
- 対照の K の赤に、期待赤として事前固定しなかった `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` が加わった (K は設計上 dirty な木、事前実走は対象 file だけだった)。H の対 2 の赤 3 件は負荷の高い計算ノード (load 56.9) での時間依存の失敗で、変更経路に到達しないので非帰属とした。
- 実装を land しないので、記録は main から切った別の木 (branch `record-dev-wave-acceptance-pyc-warm`) で作った。

## 次の一手差分
