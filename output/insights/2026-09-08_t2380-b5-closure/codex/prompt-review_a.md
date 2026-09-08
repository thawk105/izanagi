単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (後継凍結物 1/2、commit 済み。§3.1〜§3.4 が生成器の契約と親裁定の読み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。§3.1〜§3.5、§4.1、§4.5。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py (レビュー対象、未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py (レビュー対象、未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json (生成物、未 commit、939 KB。全文を読まず `python3 -c` や `grep` で抜き取る。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/author_1.md (実装子の報告。読めなければ即停止)

## 役割 — レンズ A: 凍結規則との byte 単位の一致

あなたは dev-wave 段 6 の敵対レビュー者である。**実装を守らず攻撃する。** read-only sandbox なので pytest は走らせなくてよい (静的検査と、必要なら `python3 -c` で生成物を抜き取る読取りだけ)。
**親は自走 harness で 17 test 緑、再生成 bytes 一致、`--verify` の正例 rc=0・負例 rc=1、抜き取り検査 (件数・照合例・control・venue) を実測済み**であり、それらの再実測は求めない。

攻撃すること (所見ごとに `RA-<番号>`、real / refuted の自己判定、根拠の file:line、推奨対応、must-fix なら成果物 (catalog bytes) への影響を 1 行):

1. 部分登録 §3.1 の 85 語の**逐語** (表記・ハイフン・大文字小文字・語順・block 所属) が `catalog.py` の定数と一致するか、1 語ずつ突き合わせる。1 文字の違いも real。
2. §3.3 規則 1〜7 と §3.4 項目 1〜12 の各項目について、実装がどの行で担い、生成物のどの entry で確認できるかを対応づけ、食い違いを挙げる。特に: percent encoding の safe 集合と `,` の扱い、`{POS}`/`{CUR}` の literal、初回 `cursor=*`、DBLP の一度だけの符号化、venue の literal `q`、control の group 化 (singleton / OR / AND)、AND2023 の日付節、配列順 (直列化順) の規則、`registration_blob`、`expected_cardinalities` の key。
3. §3.4 に**無い**読みを実装が勝手に採っていないか (例: 語の trim、大文字化、空白の正規化、term 順の sort、endpoint の変更、追加 parameter)。
4. 生成器が network・時刻・環境変数・cwd・locale・Python の hash seed に依存する経路がないか。`json.dumps` の `ensure_ascii=False` で非 ASCII 文字が出る可能性 (登録語に非 ASCII は無いはずだが確認せよ)。
5. test の期待値が凍結文由来の**独立 literal** か、production の定数・helper・生成物から写した恒真かを 1 test ずつ判定する (自己参照なら real)。`test_checked_in_catalog_matches_rendered_bytes` は catch-all として認めるが、それ以外で production 依存の期待値があれば挙げよ。
6. CLI の契約 (§3.1: 排他・どちらか必須・rc=1・`--verify` は書き込まない) と実装の一致。

## 禁止

- ファイルを書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み 2026-09-07 / 2026-09-08 (1/2) 文書の変更を提案しない。
- 新しい gate・検査・台帳・一般化を推奨しない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論をこの形式で書いて終われ。

## 所見
## 総括
