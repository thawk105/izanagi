## 対応表

指定資料 9 本を静的照合した。pytest・再構成 script の再実行、ファイルへの書込みは行っていない。以下、`README`・`log`・`stdout` は対象 insight の `README.md`・`materials/reconstruction-log.md`・`materials/reconstruction-stdout.txt`、`fragment` は指定 worklog fragment を指す。script 本文の独立検証は今回の対象外とした。

| 所見 | 判定 | 根拠 |
|---|---|---|
| M1 | **partial** | README:44–68 に走査範囲・時刻・sha 不一致の根拠が追加された。stdout:71–73 は「6 root / 615 file / 受領証だけ hit」と一致する。ただし、log:120・124 の「23 file」は stdout:75–98 の **24 個の異なる path** と不一致。「全 file に roundtrip の値が無い」は、path 一覧だけでは確認できない。 |
| M2 | **closed** | README:78 は critic-3 の digest・WAL・lock を区別し、受領証と再構成 loop_state だけが bytes で再現可能と限定した。3 巡稿 §2.4 の critic-2／critic-3 行と読取対象が一致。stdout:7–12・23–25・60–61、3 巡稿 §5.1 の round 3 lock 行とも整合する。 |
| M3 | **closed** | README:79 は「完全に再検算」を pair 試行に限定し、3 巡を round 2＝bytes、round 3＝canonical 内容、round 1＝転記値・記録に分離した。3 巡稿 §2.2、stdout:12・19・61・64–65 と整合する。 |
| M4 | **closed** | README:104–126 は data の同一性、critic 読取対象全体の再監査、未作成の完全入力、実送付を分離した。A は系列継続、B は過去証拠への依存縮小、C は現存原本という別の利点を示しており、A 推奨と B/C の合理性は矛盾しない。ただし前提の「だけ」に小さな不整合が残る（新規所見）。 |
| M5 | **closed** | fragment:60–64 と README:84 は A 採用時／B・C 採用時の記録を条件分岐した。fragment:69–71 の新規 T は stale 注記の追記作業で、入力元の裁定を先取りしていない。複製済みの追記は stdout:101–102 と対応する。 |
| M6 | **partial** | log:6–7 と README:152 は「抜粋・要約」と「生 stdout」を分離した。しかし **README:6 は今も log を「実測の逐語」と紹介している**。同じ誤認を起こす入口の修正が残る。 |
| M7 | **closed** | README:20–23 と `reviews/s4-ruling.md`:8–10 は、記録 wave の結論を補正する立場に変更した。原文 §3 の roundtrip 行（48 行）、round 2 行（47 行）、影響説明（51–52 行）を正しく要約している。roundtrip 5 file の sha 記録と round 2 lock の一致は、3 巡稿 §5.1 と stdout:7 で裏づけられる。ただし補正文の bytes の限定に不整合がある（新規所見）。 |
| nit 1 | **closed** | README:44–45 は roundtrip の `materials/planner-input-2.json` に修正済み。3 巡稿 §2.2 巡 1「還流」行・§5.2 と一致。 |
| nit 2 | **closed** | README:125 は 811,956 tps を `current_perf` の実測と記載し、whiteboard の実測とは呼んでいない。 |

量化の照合結果は次のとおり。

| 量化 | 判定 | stdout との照合 |
|---|---|---|
| WAL canonical ref「5/5 一致」 | **closed** | stdout:61・64–65 に一致判定と件数がある。 |
| pair 原本「5/5 一致」 | **closed** | README:61・log:34–43 の 5 種の sha／bytes は stdout:14–19 と一致。消失前の pair 記録への独立再照合は今回の指定資料外。 |
| 複製「6/6 一致」 | **closed** | stdout:101–102 の `copied 6 files` と `all match source: True` に対応する。個別表示は campaign 5 file のみで、claim の個別 sha と MANIFEST 内容はこの stdout には無い。 |
| 「6 root / 615 file」 | **closed** | stdout:72 に同値。 |
| 走査 (a) の sha 一致「0 件」 | **closed** | stdout:73 の hit は受領証 1 件のみ。他の列挙対象について 0 件という記述と一致。 |
| 走査 (b) の「0 件」 | **partial** | stdout:68 は `digest hits in repo insight dirs: []`。ただし、対象 3 dir・全 file・先頭 200 B の検査条件は stdout 自体に出ておらず、条件込みの量化は照合できない。 |
| 「23 file」 | **regressed** | stdout:75–98 は **24 file**。重複を除いても 24。 |
| 「全 615 file に roundtrip の値が無い」 | **partial** | stdout は語を含む path の一覧であり、該当箇所の値や走行への帰属を示していない。 |
| loop_state／AO「bytes 一致で再構成可」 | **closed** | stdout:22–25・48–49 の再構成 sha／bytes／一致判定が、3 巡稿 §5.1 の記録値と一致。 |

## 新規所見

- **must-fix — 走査結果の件数と不在断定。** log:120・124 の 23 を 24 に修正する。README:45・66–68 と log:124 の値の不在については、hit 内容と roundtrip への帰属を確認した根拠を追加するか、「sha 一致 file は見つからず、語の hit は 24 file。roundtrip の値の残存は未検証」まで限定する。走査 (b) も検査条件を確認できる証拠か限定が必要。

- **must-fix — 再レビュー結果の先取り。** fragment:43 は、今回の結論が出る前に「焦点再レビュー 1 本で GO を確認」と記載している。本レビューは NO-GO なので、実際の結果に直す必要がある。新規 T と `更新 [T-2795]` の条件分岐には裁定の先取りを認めない。

- **補正文の不整合。** README:22 の roundtrip 5 file に続く「bytes の再検算はできない」は、受領証を例外にしていない。README:48、stdout:8・73、3 巡稿:424 は受領証の bytes 一致を裏づける。「受領証を除く 4 file」と限定する。同様に README:104 の「原本と同一と言えるのは loop_state と AO だけ」も、受領証を加えるか「再構成対象のうち」と限定する。

- **M6 の修正漏れ。** README:6 の「実測の逐語」のリンク先を `reconstruction-stdout.txt` に直し、log は抜粋・要約として紹介する。

## 総括

**NO-GO。** 残る must-fix は **M1 の証拠・量化の不足、M6 の入口表記、fragment の GO 先取り、受領証を除外していない限定文**。

A/B/C の比較と A 推奨には矛盾を認めない。今回の NO-GO は、修正文書の証拠範囲と記録の正確性に対するもの。