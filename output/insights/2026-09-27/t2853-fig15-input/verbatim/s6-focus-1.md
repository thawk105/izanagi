## 対応表

| 前回所見 | 判定 | 根拠 |
|---|---|---|
| M1 | **partial** | 図 README の入力先と proof chain は修正済み。ただし作図ツール README に「外部原本の閉包」が残る。 |
| S1 | **closed** | insight が、受理される内容は SHA-256 pin で固定され、配置は平坦・混在 layout へ広がったと訂正した。 |
| S2 | **closed** | insight は新 test を `main()` の関数呼び出しと明記し、公開 CLI のプロセス実行を描き直しと区別した。 |
| N1 | **closed** | 図 README は「写しを読むように変える前は」に修正された。 |

## 新規所見

- **F-M1（must-fix）** — [tools/plotting/README.md:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/tools/plotting/README.md:520): `validate_external_sources` を「外部原本の閉包」と説明するが、変更後の着地 test は追跡下の写しを渡す。放置すると成果物の proof chain が実際に検査した入力先と異なる原本を参照する。「入力の 5 file の閉包」などに直し、写しを読む test の説明と揃える。
- **F-S1（should）** — [insight:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/output/insights/2026-09-27/t2853-fig15-input/README.md:53): 「写しだけから」は、生成器が追跡下の稿を `caption_source` として読む限定を落としている。再現に必要な入力の説明が狭くなる。「5 件の観測入力は写しから読み、追跡下の稿も用いて」と限定する。
- **F-S2（should）** — [insight:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-fig15-input/output/insights/2026-09-27/t2853-fig15-input/README.md:51): 「本番との違いは `--evidence-root` の 1 leaf だけ」は差分の *件数と path の集合* については正しいが、各 leaf の値まで同じと読める。対照と本番では生成器 SHA、出力 path、PDF SHA も異なる。「着地図に対する差分 path の集合では」と限定する。

## 検算

| 項目 | 再計算結果 |
|---|---|
| leaf 差 | 本番 **9**＝時刻 1＋生成器 SHA 1＋出力 path・PDF SHA 3＋再現 argv 4。対照 **8**。記録と一致。 |
| leaf 差 0 | **11 key**：`arms`、`artist_series`、`blocks`、`caption`、`comparisons`、`exposure_ratios`、`external_inputs`、`measurement_conditions`、`schema`、`source_inputs`、`tracked_inputs`。一致。 |
| SHA-256 | 入力の写し 5/5 が pin と一致。PNG は着地・本番・対照とも `11f28201…e966` で一致。PDF は着地 `4af67848…`、本番 `47206150…`、対照 `92feb21c…` で不一致。記録と一致。 |
| 変異 | M1〜M3 は **3/3 KILLED**、失敗 node は登録した完全集合と一致。C0 は **SURVIVED**。一致。 |
| 費用 | 変異 **12 job、149 s**。焦点走 **42 s**との合計 **191 s ÷ 3600 ≈ 0.053 node 時間**。一致。 |
| 焦点走 | **142 passed / 1 failed**。失敗は `git status` に載った未 commit の README 2 件を拒否する test で、ログ上の余剰 path もその 2 件。記録の帰属と一致。 |
| 三軸語走査 | hit file 集合は前回 fig1 の一覧と同一。本 wave の file は **0 件**。一致。 |
| 時刻・commit・SHA 接頭辞 | 対照 14:49 JST、本番 14:56 JST、統合 commit `779b984e4cda…` をログ・commit と照合。記録中の script・結果 JSON・生成器の SHA 接頭辞も一致。 |

## 判定

**NO-GO** — 値の検算は一致したが、作図ツール README の proof chain が検査入力を「外部原本」と誤記しており、前回 M1 が部分的に残る。

## 総括

静的検査のみ実施し、テストは実走していない。数値・変異結果・費用に新たな不一致は見つからなかった。