## 作ったもの

[wrapper: scratch/t2853_r2_fig10_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/t2853_r2_fig10_plot.py)

SHA-256:
`4674508a78aa88b87b9b5e73a2f420bbe267209dff62b0549610c76805398877`

原生成器の作業前・作業後 SHA-256 はともに指定値でした。

`f78da66d4666455dec4da843f51c2c3ea5e7b10fbac2e91ede3d680f480b795f`

## CLI と実走結果

共通呼出しは `python3.10 -B scratch/t2853_r2_fig10_plot.py --generator <生成器の絶対path>`。ファイル引数は絶対 path、`--results-document` は repo 相対 path です。

| サブコマンド・主要引数 | rc | 実走結果 |
|---|---:|---|
| `control --measurement-root <原attempt> --reference-provenance <既存provenance> --out-prefix …/fig10_control` | 0 | `artist_series` 全27行完全一致。caption・`tracked_inputs` も既存と一致 |
| `r2 --measurement-root <原attempt> --certification <見立てcopy> --raw-manifest <見立てcopy> --r2-record …/mock-record.json --results-document <R2 insight> --out-prefix …/fig10_mock_r2` | 0 | 見立て入力で描画成功。外部入力・repo閉包検査も通過 |
| `table --original-root <原attempt> --r2-root <原attempt> --r2-certification <見立てcopy> --r2-raw-manifest <見立てcopy> --r2-record …/mock-record.json --results-document <R2 insight> --out …/mock-comparison.md` | 0 | 別々の `load_evidence` が通過。6 workload行・12 cell行を出力 |
| `r2`：record の certification hash 先頭を `b → a` に変更 | 2 | 生成器の `SHA-256 mismatch` で拒否。`fig10_bad_record*` 出力なし |
| 実R2入力での `r2`・`table` | — | **実装済み・未実走** |

成功した描画2本は、元のレイアウト検査も通過しています。表の allocation receipt は各 workload で5 hostを取得し、同じ行に並ぶ複数 host も数えています。

完全な再実行 command は次の成果物内にあります。

- [陽性対照 provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/fig10_control.provenance.json)
- [見立てR2 provenance](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/fig10_mock_r2.provenance.json)
- [見立て対照表](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig10-plot-author/scratch/out/mock-comparison.md)

## caption の差し替え一覧

以下の4置換について、**各原文の出現数が1回であることを描画前に検査**します。不一致なら非0で停止します。control には適用しません。

表内の記号は次の文字列を表します。

- `A`：record の attempt ID
- `R`：実R2では `R2 reproduction-package attempt`
- `Q`：実R2では `separate from original attempt b7f5-20260919a`
- `S`：`docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`
- `D`：`--results-document`

見立て実走では、`R` を `R2 reproduction-package rendering fixture`、`Q` を `uses original inputs; not R2 measurement results` としています。

| 原文 | 置換後 |
|---|---|
| `B-7 material: static backoff fixed 5 us versus stock (no backoff) in three workloads, attempt {A}` | `B-7 {R}: static backoff fixed 5 us versus stock (no backoff) in three workloads, attempt {A} ({Q})` |
| `The outer status is the protocol's conjunction over the three workloads and follows from the negative read-heavy effect; it is not a research verdict.` | `In the original attempt, the outer status was the protocol's conjunction over the three workloads and followed from the negative read-heavy effect; it was not a research verdict. The outer status reported above is copied from this attempt's certification, not a research verdict. Original attempt's results note: {S}; R2 context: {D}.` |
| `This is B-7 material, not a B-7 satisfaction decision (D2044 item 3).` | `This {R} supplies B-7 material, not a B-7 satisfaction decision (D2044 item 3).` |
| `This figure reports a single attempt of five samples per cell;` | `This figure reports one {R} of five samples per cell ({Q});` |

負の read-heavy 効果による outer status の説明は、原 attempt に帰属させています。正しさの別走・限定の説明文は変更していません。

## provenance の扱い

- R2 certification／manifest は実際の絶対 path と `repo_tracked_leaf: false` を記録します。
- 期待 hash と `RECORDED_JUDGMENT` は **record の値だけ**を使用します。wrapper による期待値・判定の自己計算はありません。
- floor 3 file・policy の path と pin は不変です。
- `CAPTION_SOURCE` は record を指し、R2 insight と原結果稿も、それぞれの役割・hash付きで記録します。
- 同じ入力注記・caption差し替えを、元の `validate_repo_closure` が再計算する経路にも適用しています。
- `reproduction` は実際の wrapper 呼出し・cwd・wrapper hash を記録します。

## 現行の受理・拒否挙動

生成器の hash・schema・study・cell順序／identity・5標本・正しさ certified/pass・source binding・trace無効性能標本・rawとの一致・floor条件・レイアウト検査は変更していません。

元の生成器と同じく、正しさ等の条件を満たす原 attempt は outer status が `reject` でも描画できます。検査拒否は理由を出して非0で終了し、検査を外す経路はありません。

実走した負例は指定の certification hash 改変1件だけです。

## 所有外への波及

書込みは以下だけです。

- `scratch/t2853_r2_fig10_plot.py`
- `scratch/out/` の図2組（PNG／PDF／provenance）、対照表、見立てrecord2本、原入力copy2本、matplotlib font cache

生成器・docs・tests・policy・insight・原 attempt 成果物は編集していません。`git diff --name-only` は空でした。commit・子agent起動・テスト新設もありません。

## 未了・懸念

R2 collect先は最終確認時も未作成でした。**実R2データでの描画・表は実装済み・未実走**です。

生成器が代表 abort rate・数値の anomaly count を返さないため、表ではその旨を明記しています。anomaly欄は検査済み serializable verdict の範囲を示し、保存された件数として扱っていません。

## 総括

wrapper の実装、原図との陽性対照、見立てR2描画・表、指定の負例確認まで完了しました。残る実走は、親の collect と record 作成後の実R2入力による確認です。