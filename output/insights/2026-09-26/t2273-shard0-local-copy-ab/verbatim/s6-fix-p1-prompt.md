単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

作業木 (あなたが編集してよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe (branch author-t2273lc-probe-fix1)
所有 path (これ以外を編集しない): `tools/t2273lc_run_series.sh`、`tools/t2273lc_run_measure.sh`、`tools/t2273lc_run_warm.sh`、`tools/t2273lc_ab_analyze.py`、`tools/t2273lc_gate.conf`
これらは使い捨ての計測 probe で repo には land しない。docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — 段 4 裁定の「計測の事前登録」。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s6-ruling.md — **段 6 裁定と erratum E1 (collection・割付の照合条件の訂正)。これが本 fix の仕様の正本。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s6-review-a-out.md、s6-review-b-out.md — レビュー所見 (A1・A3・B1・B2 が対象)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/codex/s5-author-p-out.md — 前回の実装子の報告。
- 回帰確認用の前回実データ (読み取りのみ): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/runs/、submissions.log、measurement-tips.json。

## 直すこと (これだけ)

1. **E1:** 集計器の collection / 選択の照合を erratum E1 のとおりに変える。A 走どうし・B 走どうしは完全一致。A と B の間は nodeid 多重集合差が「A のみ = 空」「B のみ = `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_visible_output_uses_one_snapshot` の 1 件ちょうど」。共通 node の shard 割付 (3 shard の selected) は A と B で完全一致、新規 1 件の入った shard は記録だけ。満たさない走・対は無効として理由を出力する。許す差分 nodeid は集計器の定数 1 つ (または引数) にし、それ以外の差を許す一般化はしない。前回データ (T-2825) の回帰確認では差分 nodeid が無い形でも動くこと (許す差分は「ちょうど指定の集合」ではなく T-2825 回帰時は空集合を渡せる形でよい)。
2. **B2:** 未使用の残骸 (`Decimal` の import、`ESTIMATE_NOTE`、`all_rows` など前回の台帳集計の名残で本 wave が使わないもの) を削除する。
3. 判定式・閾値・順序・門番・land 条件・5 分別判定は変えない。s4-ruling.md と s6-ruling.md に無い判定・閾値・分岐を足さない。

## 規約

- 既存の検査 (門番、flock、submissions 突合、HEAD・clean の前後照合、温め前提) を緩めない・消さない。
- 回帰確認: 前回 T-2825 の実データに当て、W_0 と対差が前回 README §6 の走表 (482.215 / 334.439 / 310.663 / 511.326 / 374.494 / 344.931、対差 147.776 / 200.663 / 29.563) と一致すること。出力はファイルに書かず標準出力へ。E1 の新しい照合を、合成した小さな入力 (A のみ差あり / B のみ 1 件 / B のみ 2 件 / 共通 node の割付差) で正例・負例とも確かめる (合成入力は /tmp 等に作らず Python の inline で組んで標準出力で報告する)。
- `bash -n`、Python の構文検査を通す。実受入の投入・dispatch はしない。

## 出力形式

- `## 変更`
- `## 実走` (回帰確認と E1 の正例・負例の結果)
- `## 総括` (3〜6 行)
