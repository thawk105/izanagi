## 対応表

指定6資料を静的照合した。以下、`README`・`log`・`stdout` は対象 insight の `README.md`・`materials/reconstruction-log.md`・`materials/reconstruction-stdout.txt`、`fragment` は指定 worklog fragment を指す。script の再実行・pytest・ファイル書込みは行っていない。

| 残 must-fix | 判定 | 根拠 |
|---|---|---|
| M1 証拠・量化 | **partial** | 新しい件数と走査 (b) は stdout と一致する（下表）。ただし README:47 と log:124 は `reverse_recommendations` の値にも不在の説明を及ぼしている。stdout:76–101 が列挙・範囲照合しているのは **`start_wall` の数値だけ**で、もう一方の値の不在までは裏づけない。 |
| M6 入口表記 | **closed** | README:6–7 は生 stdout の逐語を `reconstruction-stdout.txt`、抜粋・要約を `reconstruction-log.md` と明記。log:6–7、README:155–156 と整合する。 |
| fragment の先取り | **closed** | fragment:43–45 は「1 巡目 NO-GO → 追加実測と fix → 2 巡目の結果は `reviews/s6-focus-2.md`」としており、本レビューの GO を先取りしていない。 |
| 受領証の限定 | **closed** | README:23 は bytes の再検算不可を受領証以外の4 file に限定し、§1 の roundtrip 5行（46–50）と整合。README:107–109 も round 3 の再構成対象である loop_state・AO と、現物が残る受領証を区別しており、§1:57–62 と一致する。受領証の現物の sha・bytes は stdout:8・15、roundtrip の一致 hit は stdout:113 にある。 |

追加量化の照合結果：

| 量化 | 照合結果 |
|---|---|
| 同じ6 root・615 file | stdout:65–72 に対象 root と件数が明記され、README:66–70、log:143 と一致。 |
| 語 hit は24 file | stdout:75 の件数と76–99の24行が一致。log:120 の訂正は正しい。 |
| `start_wall` 数値を持つのは4 file | stdout:80–82・99 の4 file。値は round 2 の `1789681001.1930716` が2 file、round 3 の `1789824041.4768934`、pair の `1789899183.7126458`。log:143–146 と一致。 |
| roundtrip 走行日の epoch 範囲の値は0件 | 上記の値はすべて `1789484400..1789570799` の範囲外で、stdout:100–101、log:147–148 と一致。ただし対象は `start_wall`。 |
| 走査 (b)：round 2 scratch の digest 1件・round 3 digest 0件 | stdout:73–74 は sha 比較と先頭200 B包含の条件を明記し、両方の hit が同じ scratch file 1件。stdout:10 の sha が round 2 と一致することも確認でき、README:60・69–70、log:150–152 と整合。 |

## 新規所見

- **残る must-fix — `start_wall` の証拠を `reverse_recommendations` に広げている。** README:47 の「`start_wall` / `reverse_recommendations` の値」に続く説明と、log:124 の両値の不在断定は、追加 stdout の検証範囲を超える。数値列挙・epoch 照合の説明を `start_wall` に限定し、`reverse_recommendations` は今回の追加実測では未検証とするか、同項目の値と帰属を確認した証拠を追加する必要がある。log:147–148 の限定は `start_wall` についてだけ成立する。
- それ以外に、今回の修正による新しい過大・不整合は認めない。

## 総括

**NO-GO。** 残る must-fix は **M1 のうち、`reverse_recommendations` の不在断定に対する証拠不足／限定不足の1件**。追加量化そのものと、M6・fragment・受領証の3件は closed。