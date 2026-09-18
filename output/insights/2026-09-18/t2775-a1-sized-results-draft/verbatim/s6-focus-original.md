## 判定と参照先

**11 件中 closed 10 件、partial 1 件、regressed 0 件。別途、fix の副作用による新規 must-fix が 1 件あります。**

以下の行番号は確認した現物です。

- **D**：[結果稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md)
- **G**：[生成器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/tools/plotting/plot_a1_sized_paired.py)
- **T**：[test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/orchestrator/tests/test_plot_a1_sized_paired.py)
- **R**：[paper-story README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/docs/paper-story/README.md)
- **F**：[figures README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/docs/paper-story/figures/README.md)

## 所見ごとの対応表（DW-O16）

| 所見 ID | 判定 | 根拠（file・行・逐語） | 残り |
|---|---|---|---|
| A-M1 | closed | D:256–258「anomaly 数は `arms.<name>.correctness_evidence` には無いが」「`payload.anomalies` (計 6 件、いずれも 0)」。result の各 workload に実在する。 | なし |
| A-M2 | closed | D:14–15、331、421–423、441。「記録 insight §3 が記録した job dir file の mtime」「本稿はこの時刻を再計測していない」。accounting／WAL 由来という旧記述は除去された。 | なし |
| A-M3 | closed | D:324「存在確認後から rename までの非協力的な書き手との衝突不在は、この記録からは確認できない」。publish の保証・限界と整合する。 | なし |
| A-M4 | closed | D:313 の出所が「本稿の利用範囲 (§0.3)、policy `authority`、事前登録 §1.1 / §7.2。投入・再投入の認可主体は D2044 項 8 / D2120 項 3」。stale 注記を根拠にしていない。 | なし |
| A-S1 | **partial** | D:298–301 は「その転記方式に対する個別の扱い」「hash を本稿へ追記しない」と明示した。一方、R:243 は F36 の説明だけで、系列規則への例外を追記していない。 | R:255–256「数値は図の provenance JSON から転記し、転記元の SHA-256 を文書に書く」が無条件のまま。R:243 に、数値と hash の転記元は result.json とする個別扱いを追記する。 |
| A-S2 | closed | D:48–49「照合先は claim-evidence `2026-08-26.md` の C1 行、本 attempt の測定値ではない」。指定 C1 行に旧 3 値が存在する。 | なし。親が退けた D19 案は採用されていない。 |
| A-N1 | closed | D:126–128「intent の canonical digest (`intent_sha256`)」「intent file 全体の bytes の SHA-256 は §5.2 の `0c3aadae…`」。双方を独立に再計算して一致。 | なし |
| B-MF1 | closed | G:397 は `_require(provenance["generator"]["path"] == GENERATOR_PATH, "generator path mismatch")`。G:382 の生成時 hash 記録は残る。T:370–378 はコメント変更後の hash 相違と closure 成功を確認する正例。 | なし |
| B-MF2 | closed | T:381–385 が PNG/PDF の repo 相対 path を完全一致で固定し、T:479 が着地 test から呼ぶ。T:388–412 に別 directory の同名画像への差替え負例。 | なし。全ファイル欠落時の迂回は後述の新規所見。 |
| B-S1 | closed | T:482–488 が fig9 節の hash 行を抽出し、`len(rows) == 1`、64 hex、`rows[0] == _hash(path)` を検査する。provenance を含む 3 ファイルが対象。 | 最終着地 bytes に対する実走は未実施。現状の placeholder 自体は予定された中間状態。 |
| B-S2 | closed | T:463–466 の `interval = json.loads(columns[5])`、長さ 2、両端の `math.isclose(..., rel_tol=1e-9, abs_tol=1e-6)`。実データの 6 端点も独立再計算と一致。 | なし |

A-S1 の残りは既存の should であり、新規所見には重複計上しません。

## 親が追加した派生値・命題の再検算

| 対象 | 現物での確認 |
|---|---|
| anomalies 6 件 | result.json を Python で読み、3 workload とも `wal_evidence.records` が 10 件、その `[2]` と `[5]` が `stage="verify_done"`、`payload.anomalies=0`。計 6 件を確認した。 |
| 約 15 分の出所 | 記録 insight README:43、49 と MANIFEST.tsv:23–24、28 に `06:30:16`／`06:45:38` の mtime 記録がある。差は **922 秒＝15 分22秒**。現在のファイル mtime を当時の時刻と見なす再計測はしていない。 |
| intent canonical digest | producer の `_submission_intent_digest` と `_canonical_json_bytes` に従い、`intent_sha256` を除外し、キー順ソート・indent 2・末尾改行で再計算。**`7eb404861e9a5336c6169445885a7083c12f801ade5068e9b1ad09ad025a2750`**。intent field と submission field の双方に一致。 |
| intent file bytes hash | 複製 `receipts/attempt-0001.intent.json` の bytes を hash 化。**`0c3aadaea83f0fe1c7a31777d26bf992fbd46d64f6e1ed12a2de2cc6f67923d2`**。D:407 と MANIFEST に一致。 |
| C1 旧 3 値 | [claim-evidence C1 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/docs/paper-story/claim-evidence/2026-08-26.md:123) は write-heavy「38.3% 高く」、balanced「11.3% 高く」、read-heavy「6.6% 低かった」。D:48 の +38.3%／+11.3%／−6.6% と対応する。 |

公開 leaf 3 ファイルと policy の SHA-256 も G の pin 表と一致しました。親の `draft-check-2.txt` は `PROBLEMS: 0` ですが、上記の確認はその報告だけに依存していません。

## fix の副作用と残存する検査

**段 4 §5 の生成器の入力受理集合は広がっていません。** 段 5 patch から復元したソースと現物を比較すると、生成器の変更は generator の現行 SHA-256 比較を除く 1 箇所だけです。`load_leaf`、CLI、統計計算、描画、caption は不変です。

closure の次の照合も実体として残っています。

| 照合 | 現物 |
|---|---|
| 入力 4 ファイルの pin | G:133–139。`validate_repo_closure` は G:395 で `load_leaf` を呼ぶ。 |
| completion map と現物 hash | G:144–147 |
| caption_source の現 SHA-256 | G:140–141 で取得し、G:398–400 の `tracked_inputs` 比較で照合 |
| cells の再計算と比較 | G:207–242、398–400 |
| artist／caption の再投影 | G:408–409 |
| 画像の形式・共通 prefix・現物 hash | G:401–407 |
| 着地 path の完全一致 | T:381–385、479 |
| README の着地 3 ファイル hash | T:482–488 |

既存の数値・分類・負例の期待値は変更されていません。ただし、**既存の着地 test の skip 条件は変更されています**。これが次節の副作用です。

fix 2 の `startswith("landed output paths mismatch")` は、新規負例に対する pytest の比較説明追記への対応です。path 完全一致の assert と、例外が出なければ失敗する `else` は維持されています。親の赤ログも、path 不一致の検出自体は成功し、その後のメッセージ完全一致だけが失敗したことを示します。

**M0〜M12 の anchor は維持されています。** author 報告の全 anchor を現物と照合し、複数行は外側の字下げをそろえて比較して、それぞれ 1 箇所を確認しました。M0 は無変異、M1〜M12 の対象式・文は変更されていません。変異実走による kill 判定は今回行っていません。

## 新規所見 — must-fix

**F-MF1：着地後に 3 ファイルすべてが欠落しても、closure 検査が skip される。**

- **根拠:** [T:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2775-a1-sized-results-draft/orchestrator/tests/test_plot_a1_sized_paired.py:475) の逐語は `if not any(path.exists() for path in paths):`。README の掲載状態や実値 hash を確認する前に skip する。段 5 にあった `and prefix.name not in readme` が除去されたため、着地後に README を残して PNG・PDF・provenance の 3 本をすべて失うケースも赤にならない。
- **影響:** 着地済み bundle の全欠落が検査失敗にならず、path・SHA-256・caption・cells の全照合を迂回する。
- **是正案:** 生成前だけ skip できる条件に限定する。例えば「3 本とも未存在、かつ README の 3 hash 行が指定 placeholder のまま」の場合だけ skip し、それ以外は 3 本の存在を必須とする。最終状態では skip 分岐を除去する方法でもよい。

段 6 裁定が生成前の skip を認めたことは確認しています。問題は現在の未着地状態ではなく、**その条件が最終着地後の全欠落にも成立し続けること**です。

## 新規所見 — should / nit

- **should：0 件。** 既存 A-S1 の README 側追記が残っています。
- **nit：0 件。** レンズ B の caption 説明の訂正は F:885–886 に反映済みです。

## 総括

**着地を止める。**

既存 must-fix 6 件は閉じました。対応表は **closed 10／partial 1／regressed 0**。新規所見は **must-fix 1 件**で、着地 bundle 全欠落時の skip を生成前だけに限定する必要があります。

親の焦点ログは **60 passed／1 skipped、14.51秒**。現物でも fig9 の着地 3 ファイルは未存在で、最終 bytes の closure 成功を示すログではありません。修正後、予定どおり最終生成・README 実値化・着地 test・変異 probe を確認してください。

今回は読み取りと再計算のみを行い、ファイル変更・pytest 実行はしていません。