# [T-2436] 段 1 brief — verifier `_reasons()` の WW 交差を key 順に整列する

**研究前進。** A-2 certification の receipt / reference digest と constraint class は verifier の
anomaly 出力から導かれる。同一 trace が process ごとに別 digest を出す限り「正しさシグナルは
再現可能」(絶対規律 3) が成立せず、rejected witness を成果物として引用できない。止めている実測は
段 1 probe: 共通 WW key を 6 個持つ 2-transaction trace で `PYTHONHASHSEED` 0/1/2/3/4/777 が
**6 通りの ww key 順と 6 通りの result digest** を出した (`anomaly_count` は全 seed で 1)。
最小差分は `_reasons()` の WW 交差 1 箇所の整列。完了判定は「同一 trace が異なる seed で同一 bytes を
出すテストが緑」かつ「anomaly の受理集合が不変」。

**scope (本題の実装だけ)。**
1. `orchestrator/verifier/dsg.py` `_reasons()` の WW ループ (`u_writes.keys() & v_writes.keys()`) を
   key 昇順に整列する。
2. その整列を撃つ正例テストを足す。既存 golden は 1 edge に ww 2 本以上を持つものが 0 件なので、
   足さなければ変異が SURVIVED になる。
- 成果物影響 (`DW-G05`): 放置すると同一 trace が process ごとに別 constraint class・別 receipt /
  reference digest を生む。

**scope 外。** wr / rw 枝の変更、consumer 側での正規化、gate・検査・台帳・一般化の新設、
live resume 互換のための source binding 緩和 (D1388 で却下済み)。

**確定済みユーザー裁定。** D1817 (整列する。限界明記案と全理由の大書換えは却下)。
D1388 (closure epoch 変化で drift した campaign は再走で作り直す。本 wave の作業ではない)。
D95 (実装面は Codex `role=author` が書く。親は直接編集しない)。

**不変条件。**
- 規律 2: anomaly の検出条件・受理集合は一切変えない。edge の reason **集合**は不変で順序だけ決める。
- 凍結成果物の再発行なし。追跡済み JSON / JSONL 全件を parse した結果、anomaly edge に reason を
  持つのは 6 件 (`2026-08-26_mocc-g2-repro/runs/{19,24,30,31,32}/verifier.json` と
  `p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl`) で、**ww 2 本以上の edge は 0 件**。
- closure membership 不変。`campaign_lock.py:59,128` ほかの dsg.py 出現はすべて path 列挙であり
  内容 hash ではない。現行 blob sha256 の live pin は repo 全体で 0 件 (実測)。
- dsg.py は enforcement source closure 内なので、**commit 前の焦点走の赤を実装の回帰と読まない**
  (`contract-loader-drift`)。

**(P1) 親の provisional 裁定・攻撃対象 — テストの型。** 「多重 WW edge の reason key 列が sorted と
一致する」だけを assert すると、未修正実装でも seed 次第で偶然緑になる。**異なる `PYTHONHASHSEED` の
subprocess を 2 つ以上走らせて report bytes / digest の一致を見る型**を既定とする
(repo 先例: `orchestrator/tests/test_s8c_preregistration_predicates.py:2952`、
`orchestrator/tests/test_s8b_floor_campaign.py:12052`)。段 3 はこの択一を攻撃せよ。

**(P2) 実測済みだが攻撃対象 — scope の十分性。** 同 probe で rw 枝の理由順は 6 seed すべて `123456`
で安定し、変動したのは ww だけだった。wr 枝は rw と同じ `Txn.reads` list を走査する。
よって WW 交差だけの整列で足りると判定した。

**成果物の形。** `orchestrator/verifier/dsg.py` の 1 箇所の変更と、`orchestrator/tests/test_verifier.py`
への新規テスト (必要なら fixture)。docs は段 7 の spool fragment。

**分割方針。** 正しさ防壁 (verifier) に触るので `DW-C00` の既定の軽量版は選べない。
段 2 プラン子 1 本、段 3 敵対相談 2 本 (lane sol / luna)、段 5 実装子 1 本 (Codex author)、
段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
