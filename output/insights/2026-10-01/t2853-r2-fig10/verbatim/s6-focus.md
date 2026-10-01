## 判定

**GO（must-fix 0、should-fix 1）。**

`068f664dd..78b3ff4c9` を静的に確認しました。費用試算・caption・provenance の修正は成立しています。観測した時間範囲の表現に軽微な残件があります。

## 所見ごとの状態

| ID | 状態 | 根拠 |
|---|---|---|
| A-F1 | partial | 影響皆無の断定は撤去済み。原因も推定へ修正。「待ちの間も」という観測範囲の表現が残る（下記 F-F1）。 |
| A-F2 | closed | 約 2.2 を誤りとして撤回。新しい控除項・算式は WAL と会計から再現できた。 |
| A-F3 | closed | 既存の rep 並列化と workload × cell の job 分割を区別。5 分は指示に由来する目安と明記。 |
| A-F4 | closed | 置換 2 を削除。R2 に適用される生成器原文が caption に 1 回存在する。 |
| A-F5 | closed | `tracked_inputs` が snapshot を参照し、その bytes・hash は投入前 commit と一致する。 |
| B-F1 | partial | 汚染否定は撤去済み。F-F1 の文言修正を推奨。 |
| B-F2 | closed | 約 3.3 node 時間の試算と、未実測という限定を確認。 |
| B-F3 | closed | 余分な「3 request ×」を削除。22,995 node 秒と一致する。 |
| B-F4 | closed | 置換 2 の重複説明が消え、outer status の原文は 1 回だけ。 |
| B-F5 | 受容 | §10 に構成を維持する理由と受容判断が明記されている。 |

## 新規所見

**F-F1（should-fix）：probe の観測時点と全期間の観測を区別する。**

[結論 5](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:61) の「待ちの間も、既存の競合 probe は競合を検出せず」は、待機中の監視を読ませます。しかし [pipeline](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/orchestrator/campaign/pipeline.py:1482) の probe は **lock 取得後・bench 開始前**です。「bench 開始前の既存 probe による競合検出は無かった」への修正を推奨します。

また、既存文言として残る [§7 の「全区間で取り合い」](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:185) も、段の時刻だけでは全期間を裏づけられません。「2 巡とも性能検証と bench が直列に並ぶ時刻だった」程度が適切です。影響皆無という主張は撤回されているため、非阻害の記述精度の問題と判断します。

## 検算したこと

WAL の必要 field を jq で抽出し、`bench_done.ts − bench_wall_s − 最後の verify_done.ts` を再計算しました。

| workload | 2 cell の空き合計（秒） | Elapse（秒） | 差引き（秒） | README の丸め |
|---|---:|---:|---:|---|
| rr5 | 1,196.101747 | 1,531 | 334.898253 | 1,196 → 335：一致 |
| rr50 | 943.268963 | 1,527 | 583.731037 | 943 → 584：一致 |
| rr95 | 67.458183 | 1,541 | 1,473.541817 | 67 → 1,474：一致 |

- 丸め前の試算は **3.322460 node 時間**。README の整数では `5 × (335 + 584 + 1,474) / 3,600 = 3.323611`。どちらも約 3.3。
- 各 `job.stderr` の会計から、`5 × (1,531 + 1,527 + 1,541) = 22,995 node 秒 = 6.3875 node 時間`。
- 全 6 cell の `rounds=1`、`settled` の並び、bench 所要 16.816〜16.888 秒を確認。

成果物の SHA-256 は全桁で README と一致しました。

| 成果物 | SHA-256 先頭 |
|---|---|
| PNG | `b91335719138…` |
| 対照表 | `150b13468309…` |
| provenance | `f54adb4802bc…` |

さらに以下を確認しました。

- repo 外の原本と写しが一致。provenance の `cells`・`artist_series` は修正前と不変。
- caption の削除対象断片は 0 件、outer status の生成器原文は 1 回。
- snapshot は `git show e92aeea8f:…/README.md` と bytes 単位で一致し、hash は `70c11b46…`。`tracked_inputs` 全 9 件の hash も一致。
- wrapper の旧版との差分は置換 2 の **8 行削除のみ**。受理条件・期待 hash・判定の扱いに変更なし。
- 「4 箇所」と旧 hash は初版・fix 前の記録として明示され、現行値との混同は見つからない。

## 確かめていないこと

- 描画・閉包検査・負例・テストの再実行。成功記録と静的整合性を確認した。
- lock 所有 PID、待機中の連続監視、局所 lock 化後の実際の所要時間。
- 5 分目安の指示や、別 wave への訂正連絡の原文。
- 前回レビュー済みの全性能標本・正しさ記録の再監査。

編集・commit・子 agent 起動は行っていません。

## 総括

主要な修正は成立し、数値・hash・caption・snapshot の不一致はありません。残件は、probe の観測時点と「全区間」という表現の精密化です。