## 直したこと

- **親 F1 — closed:** lost update の key を有効な 16 進 `aa` に修正しました。既存の synthetic Silo proof gate を使い、malformed・framing が 0、lost 側が non-serializable で表 1 の ww / rw を持ち、直列対照が certified になることを確認しました。
- **RA1 / RB1 — partial:** executor の全 case の key を `aa` に修正しました。certified 正例と、notes が witness 不一致の 1 行だけになる対照の assertion は維持しています。executor 試験は未実走です。
- **RA2 — partial:** v2 対照を有効な key と一致する witness を持つ trace に修正し、verifier 単独の `certified` assertion を追加しました。v3 要求による拒否の実走確認は未了です。
- **RB2 — closed:** `_run_trace` に YCSB と TPC-C 段 1 の許可理由、CCBench の計数修正前提、verifier 後の v3 要求を 3 行で記しました。

## 変更行数

production はコメント **+3 行**。試験は **+19 / −8 行**で、指定された上限内です。

## 実走結果

`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` は **141 passed、0 failed**。構文検査と `git diff --check` も通過しました。`test_campaign.py` の対象試験は `tools/run_tests.py` が qstat 事前確認で `rc=16` となり、子試験が起動しなかったため**実装済み・未実走**です。

## 変異の照準 (M2・M8・M11)

- **M2:** 存在詳細の診断 assertion で赤になります。受理集合の変化ではなく、構造化診断の欠落による赤です。
- **M8:** v2 trace が verifier 単独で certified になる assertion を追加しました。v3 要求を外すと後続の認定経路へ進み `abort is None` になる構成です。変異の実走は未了です。
- **M11:** 表 1 の ww / rw assertion で赤になります。受理集合の変化による赤ではありません。既存 v3 試験も赤になり得るため、単一理由性は成立しません。

## 裁定からの逸脱と理由

実装範囲の逸脱はありません。`critic/digest.py` は段 6 裁定どおり編集していません。commit も作成していません。

## 総括

lost update 試験は有効な key と proof gate で再実走し、通過しました。
executor 試験の全 key と v2 対照を修正しました。
pipeline の許可理由コメントを復元しました。
production の実行行は変更していません。
verifier runner は 141 件通過しました。
executor 試験は dispatch の事前確認失敗により未実走です。