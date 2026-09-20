## 所見ごとの対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A-1 / B-4 | closed（静的） | `mutation-spec-v1-probe.json` は m1 を certification SHA 比較へ照準し、m6a＝legacy の A-6 受理、m6b＝current-full の A-6 除外に分割。裁定と一致する。`test_a6_pin_drift_is_rejected` は変更前 hash を保持し、m6a の fixture は certification／manifest の study を揃えている。未知 study の冗長 gate は段6裁定に明記され、11件の変異対象から外れている。実測 node 集合の確定は別途必要。 |
| A-2 | **partial** | fig5／6／7 の着地 bytes に差分なし。修正前後の `_caption`／`_artist_series` からの再構成も各着地値と一致。一方、`build_provenance` が再生成する A-2 current-full に top-level `study` を加える旨は、[plotting README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/README.md:125) に未記載。worklog 本体・archive にも対応記録を確認できず、裁定が要求した書き分けは未完了。 |
| A-3 / B-3 | closed | `test_landed_fig11_repo_closure_and_caption_when_present` に study／status／effects／median／外部 path 集合の直接照合が追加された。実データでも全項目一致。README「再現できるのは…」は validator の自己整合・hash 検査と、この直接照合を区別している。`validate_repo_closure` 本体は不変。 |
| A-4 / B-5 | closed | README fig11 は `STUDY_PROFILES` の2 study と `CANONICAL_SHA256` の3 leaf を区別し、実装の表件数とも一致。arm／workload 表記を訂正し、作図規約節を短縮。参照先の fig5「作図規約への適合」には実際に §1 の限定例外・D1074 が記載されている。 |
| B-1 | closed | 現 provenance の caption と README が「throughput が median に最も近い rep の1点」を明記し、稿 §2.3・§4 限定6と一致。WAL の abort 率 `0.1547 / 0.145` も provenance と一致。 |
| B-2 | closed | `_caption` の A-6 枝と着地 caption は正しさの観測・性能の非認証・reject による証拠非取消を3文に分離。artifact hash／compile-out と `src_token`／翻訳単位全体の限定を追加し、既存の記録保持の限定と合わせて稿 §4 限定4(i)〜(v)に対応。固定文 test も追随。 |
| B対応表：時刻の出所 | closed | `campaign claim recorded at` を追加。値 `2026-09-07T16:29:41.491476+00:00` は raw-manifest の `campaign_claims.rr95.claim.created_utc` と一致。JST は翌日01:29:41で、稿の実行日と整合し、scheduler Created と混同していない。 |
| B対応表：限定2 | closed | 他の read 比率・機体・CCBench pin・CC protocol へ外挿しない文を追加。稿 §4 限定2と一致し、固定文 test にも収録。 |
| A：削除候補 | closed | 裁定どおり axes 数の冗長条件と `'four'/'two'` を維持。互換既定、study 検査、caption_source、既存 test も残る。README の重複説明は短縮され、producer 迂回や fixture 一般化は追加されていない。 |

派生値は原データから再照合した。2 cell・1 workload・各5標本・外部6 file、median `10,088,796 / 9,505,248`、median 比 `−0.057841193339621455`（表示 `−5.7841%`）が一致する。tracked 入力3件と外部6件の hash も一致した。README の成果物 hash 3行は現物から再計算して全件一致した。

| 成果物 | 再計算した SHA-256 |
|---|---|
| PNG | `6781f24be93699c7443b784ec5167a7ab1b590c6d7a89fa07fc68504b6fd1549` |
| PDF | `dcaf1b26d5153c650ea12f8b49773239a12a8a4cbc6d967d1e7399af4701df26` |
| provenance | `3f57baff302c43d9dede1e4c48ee94c011e3befe964928ec2283895eaeb22f16` |

caption 全文は README と一致し、現 `_caption` からも一致して再構成できた。稿 §0／§2.3／§4 限定1〜12との照合では、新たな過剰主張は認めない。限定9の一部と限定10は省略されているが、該当対象との比較や測定時 policy bytes の不変を主張していない。限定11は凍結稿と後発図を区別し、限定12の perf 不使用は維持している。

退行検査では、生成器の変更関数は `_caption` のみで、変更は A-6 枝内に限定される。受理・拒否経路は不変。test の変更も、新設済みの caption 固定文・禁止語の2関数と着地 test の直接照合追加だけで、その他の期待値は不変だった。

変異11件の `old` は、対象ファイル内に**各1箇所**存在する。m5 の新固定文への追随、m6a／m6b の分割も一致する。m4 の不可視追加 axes、m7 の request／claim 同時変更を含め、静的には新たな単一理由性の疑義を認めない。probe の全件 `SURVIVED` 登録は探索用であり、正式走の成功証拠とは数えていない。

## 新規所見

無し。A-2 の文書未反映は既存所見の残件であり、fix による新規退行ではない。

## 総括

**NO-GO：段6裁定の表は、A-2 の文書対応が partial のため未閉鎖。**
plotting README と worklog に「着地 fig5／6／7 は不変、再生成 A-2 current-full は `study` を追加」を明記する必要がある。
その他は静的範囲で closed、regressed は無し。値・hash・caption・A-2 互換射影は再照合済み。
pytest・正式変異走の成功は本レビューでは主張しない。