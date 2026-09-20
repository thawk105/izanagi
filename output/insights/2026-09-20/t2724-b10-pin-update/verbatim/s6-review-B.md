## must-fix

- **B-1：旧 checkout 全般を拒否するという説明は、実装より強い。** `docs/b10-backoff-static-tail-submission.md:26`、`docs/phase3-8b-restart-runbook.md:326`、`docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md:19`。旧 checkout が自身の旧 submit/job script を使えば、旧 tree と旧 pin は一致する。日付や現行 main を参照して旧版を失効させる機構はない。放置すると、投入手順と決定台帳が「G 無しの旧版実行も機械的に拒否される」と誤って保証する。
  - 根拠：`tools/pegasus/submit_b10_backoff_grid.sh:97` は同じ checkout の job script を選び、`:150` で動的に SHA を算出する。job の `:388` は実行 script・提出 SHA・checkout HEAD の script blob を照合し、`:595` はその script の定数と tree を比較する。
  - **通る正例：** 3 箇所を「**本更新を含む job script は、G を削除した tree や追加・変更のある tree を、測定開始前の digest 検査で `fail 2` により拒否する。旧 checkout と旧 script の組は本更新によって失効しない**」へ限定する。新しい gate の追加は不要。「2026-09-20 以降」も commit／版を基準とした表現にする。

## should

- **B-2：未実走の検証を完了形で台帳へ記載している。** `docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md:35` の「本 wave はその条件で実施した」は、変異 2 件・負例 3 件を含む条件の達成を示すが、レビュー時点では未実走。放置して fold すると、決定台帳に未成立の検証履歴が残る。現時点では予定形にし、実測完了後に結果と証拠の所在へ更新する。

## nit

- `docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md:29`：「唯一の形」は、**G の取り込み、現行の全 file 完全一致検査、B-10 の継続利用を維持する条件下**と限定すると正確。実装上の必要性だけでは授権は導けないが、`:11` に本依頼の明示的な pin 更新指示があり、本 wave の授権不足とは判定しない。
- `docs/b10-backoff-static-tail-submission.md:26`：設計正本 §7 項 5 が指定する clean-scan hit 4/4 の注意は、この文書には追加されていない。runbook 側には記載済みで、実行結果を変える欠陥は認めない。

## 確認済み (問題なし)

- **束縛と旧成果物：** `tools/pegasus/b10_backoff_grid.sh:595`／`:647` は前後の実 tree digest を定数と照合し、`:651`／`:719` は実測値を `completion.json` に保存する。定数更新で既存 completion の記録は変わらない。
- **解析 consumer：** `git grep` で `orchestrator/`・`tools/` を検索した結果、旧値の残存はなく、`freeze_trees_sha256` は上記 producer のみ。解析側の旧値照合経路は見つからない。`b10_backoff_static_tail_formal.py:445` の completion は campaign 内の execution artifact で、`:446` は WAL／lock を照合する。`b10_backoff_shape_sweep.py:756` の script 束縛対象も別の `b10_backoff_shape_campaign.sh`。
- **consumer 閉包：** 更新対象は起動契約の 3 literal。それ以外の旧値出現は測定・検算・失敗履歴。`test_b10_backoff_grid_submit.py:111` は script SHA を動的計算、`test_backoff_extended_sweep.py:1907` は SHA 照合処理の構造検査、`test_b10_backoff_grid_job.py:420` は fixture 定数を使用する。`admission_registry.json:22`、関連 `test_hooks.py`／`test_pegasus_tools.py` に、この job の bytes を固定 SHA で pin する経路は見つからない。
- **docs parser：** `test_b10_backoff_grid_submit.py:305` は指定された `## 2.` 節内の code block を取得する。§1 の追記は parser の入力を変えない。
- **負例 n1／n3：** `test_backoff_extended_sweep.py:2011` は実 filesystem の全通常 file を列挙するため、untracked file 追加も G 削除も digest を変える。指定 test file 内では、ほかに実 freeze tree の走査・file 数・G の実在を検査する node は見つからない。`:945` の dirty 検査は `tmp_path` の別 Git fixture、`:1996` の glob 検査は script 文字列の検査である。したがって、**指定集合では同 1 node だけが赤になる期待は静的に妥当**。ただし、これは test の検出力の証拠であり、job 本体の拒否を実走した証拠にはならない。
- **clean scan：** `docs/phase3-8b-restart-runbook.md:326` の run_dir 3 file＋候補、両 holdout hit 4/4 は、`output/insights/2026-09-19/t2724-chain-land-2/README.md:60` と D2120 項 2 (a)(d) に整合する。G 自体は既存除外 prefix 内。
- **D1789／D1790：** `docs/decisions.md:54183`／`:54204` の対象は発効済み事前登録と測定・解析側の版束縛。`docs/b10-backoff-static-tail-preregistration.md:1054` 以降は登録 commit・文書 blob・spec を束縛し、freeze-tree digest や grid job script の固定 SHA は指定していない。本変更はそれらの書換えではない。
- **merge と検算：** 保存枝 `0a799da6c` と対象 HEAD `16f487936` の `ls-tree` は、freeze tree **20 file**、指定成果物 **8 file（G を含む）**とも一致。`output/` の差分 **524 file は全件、着手前 main `b7f970dfa` と同一 blob**。独立再計算も 20 file＝`6a4ee1ef…`、G のみ除外した 19 file＝`c405c742…` と一致した。

## 判定 (GO / NO-GO と理由)

**NO-GO：B-1 の起動契約の説明を修正するまで。** 3 literal の実装変更、旧成果物との対応、consumer 閉包、merge の完全性には静的な阻害要因を認めない。

## 総括

必須修正は、旧 checkout の拒否を保証する記述の限定。検証完了形の台帳記載も実測状況へ合わせる。pytest・変異・負例・受入は本レビューでは実行しておらず、緑とは判定していない。