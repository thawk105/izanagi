---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-rejected-witness-closure
seq: 1
title: 8c formal consumer の rejected 枝を production の実在 field へ合わせ、witness を verifier が生成できる形だけに閉じた (コード + テスト + 記録、branch worktree-dev-wave-rejected-witness-closure、変異 22 件中 KILLED 20・登録 SURVIVED 2)
---

## 本文

- **依頼は producer/consumer 不整合の解消で、方向は実測した現物の field 名で決めることだった。**
  ユーザーは「規律 2 を緩めない。不整合の解消だけ。仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外」と scope を固定した。設計判断は {{D:fc07-rejected-witness-from-verify}}。
  成果物は `output/insights/2026-09-07_8c-rejected-witness-closure/`。
- **引数が前提にしていた 2 つの事実が起動時の実測で覆った。** 名指しされた並行 wave
  `dev-wave-t2228-driver-gate-liveness` は `reflux_formal_consumer.py` を触っておらず
  (変更面は pegasus probe と `test_hooks.py`)、一次資料の dir 名も実在しなかった
  (正しくは `2026-09-07_t2353-formal-consumer-terminal-stage`)。どちらも brief で訂正した。
- **親の裁定の根拠 3 件が子の実測で否定され、親が受け入れた。** これがこの wave の中心的な出来事である。
  - 段 3 レンズ A: 「producer が書く boolean は必ず恒真になる」は一般化しすぎ。producer は
    untyped JSON へ潰れる前の `VerifyResult` を持つので偽になりうる値を書ける。方向 (consumer 側で
    導く) は維持し、理由を「producer の自己申告は consumer が独立に検算できる証拠を持たない」へ狭めた。
  - 段 6 レンズ A: 「canonical JSON は float を拒否する」は誤り。有限 float は通り、`2.0 == 2` で
    型検査を素通りしていた。親が自分で実行して確認した。
  - 段 6 レンズ B: 「verifier の出力は決定的」は誤り。`dsg.py` の `_reasons()` は
    `u_writes.keys() & v_writes.keys()` を未整列で走査するため、理由順が process 間で変わる。
    FC07 の検査自体は記録された bytes に対して行うので壊れないが、class の意味は run 依存になる。
    {{T:verifier-reason-order-determinism}} として裁定へ返す。
- **段 5 の実装子は model call 上限 100 に達して SIGTERM で切られ、最終報告を 1 文字も出さなかった。**
  編集は 7 file すべてに完了していた。子の自己申告が存在しないため、段 6 の 2 レンズへ
  「子の主張として信じてよいものは何も無い」と明示して投げ、pin の再計算と単一理由性を独立に検算させた。
  レンズ B は baseline の 7 entry すべてを別 canonicalizer で導き直し、変わるべき 5 件が変わり、
  変わるべきでない 2 件が不変であることを確認した。
- **段 6 の敵対レビューが規律 2 に触る受理穴を 3 件見つけた。** いずれも具体的に通る入力を伴っていた —
  `anomalies=[{}]` が witness class として通る、integrity が汚れた trace の cycle を candidate 起因と
  誤認する、`stats` を丸ごと欠いた payload が通る。fix 2 巡で閉じ、fix 後の焦点再レビューは
  closed 4 / partial 4 / regressed 0 だった。
- **変異の 1 件が等価変異だったので実効 gate へ再照準した。** `type(x) is not int` を `isinstance` へ
  緩める変異が SURVIVED した。`isinstance(2.0, int)` が False で、既存の負例が float を使うためである。
  型検査そのものを取り除く形へ再照準して KILLED を得た。初回の SURVIVED は F245 へ再発として
  追記し、isinstance 版は
  「型の厳密さが負例で pin されていない」ことの実測として登録 SURVIVED のまま台帳に置いた。
- 子は codex 9 本 (plan 1、consult 2、author 1、review 3、fix 2) と spec author 3 本。
  親は Claude で管理・統合・全実測を担った。

## 次の一手差分

### 新規

- {{T:verifier-reason-order-determinism}} **P2・新規**: `orchestrator/verifier/dsg.py` の
  `_reasons()` が `u_writes.keys() & v_writes.keys()` を未整列で走査するため、WW 理由の順序が
  process 間で変わる。同一 trace から異なる anomaly digest = 異なる constraint class が生じうる。
  producer 側の変更なので本 wave では scope 外にした。整列するか、非決定性を限界として
  明記するかを決める。
- {{T:result-evidence-record-producer}} **P2・新規**: result-evidence record 全体に
  production producer が無い。`OriginProducerInputs` の構築は repo 内で test 1 箇所だけである。
  本 wave が閉じたのは WAL 側の不整合であり、record を発行する側が同じ規則で
  `physical_result.constraint_sha256` を導かない限り、rejected の本番 projection は
  端から端まで通らない。
- {{T:witness-type-exactness-not-pinned}} **P3・新規**: witness anomaly の `length` と edge 端点の
  型検査を `type(x) is int` から `isinstance` へ緩めても、現行の負例 (float を使う) では
  検出できない。開くのは bool の穴だけである。変異 `b060.m23-length-exact-int` と
  `b060.m24-endpoint-exact-int` を登録 SURVIVED として残してある。bool 負例を足すか、
  厳密さを要求しない設計に改めるかを決める。
