## 対応表

以下、`I` は `output/insights/2026-09-21/t2826-modify-timing-resume/`。Python による読取り・再計算と、`c45717613` → `05f232b2c` の README 差分を確認した。

| 所見 | 判定 (closed / partial / regressed) | 根拠 | 残る問題 |
|---|---|---|---|
| 1：R8 の候補抽出 | closed | README §3・§4.9・§6。`I/verbatim/acceptance-root-stat.txt` 全行と `I/raw/job-out/<cell>/cell.txt:start_epoch,end_epoch` から、birth による全11セルの候補0を再現。原裁定 `t2826-shard-plugin-modify-timing/verbatim/s4-ruling.md:68` の候補条件と一致。 | 採取時点に残る session に限定した判定。削除済み session や外乱一般の不存在は証明しない。採取時刻の誤記は新規所見1。 |
| 2：R6 の待ち条件欠落 | closed | README §4.7・§6。`job-out-aggregate.json:cells[].probe.workers.*.times`、`cells[].xdist` から適合・時間関係・待ち増加を再計算し、両 half とも成立。保存 `R6.prediction-*.pass` の不足も明記。 | 集計器自体の欠落は残るが、今回の判定は補正され、保存出力との違いも説明済み。 |
| 3：11セルの有効性の量化 | closed | README 結論1・§3・§6。`job-out-aggregate.json:cells[]` は xdist 10セルで rc 0、48 worker、`probe.complete=true`、`collection_mismatch=false`、欠落・無効理由なし。warm は rc 判定として分離。 | なし。 |
| 4：96% の帰属表現 | closed | 題・結論3・§4.3で事前登録判定と事後集計を分離。`job-out-aggregate.json:R2.<cell>.leaves` と `cells[].xdist.modify.median` から定義・値を再現。`principal_leaves=[]`。 | なし。 |
| 5：T-2825 B の引用範囲 | closed | README §5。`t2825-ledger-refresh-ab/README.md:107`、`:109`、`:112` の有効 B は 63.0／63.5／64.4秒。 | なし。 |
| 6：実施記録の出所不足 | closed | README §1・§2 N6・§3・§9。`s5-author-receipt.json:actuals.model_calls,actuals.wall_clock_s,codex_exit_code`、前後 status の各0 byte、stat 全行の最新 mtime を確認。649秒には scheduler `Elapse` の量名が付いた。 | 前後 clean は観測時点の証拠であり、途中の全時点を監視した証拠ではない。 |
| 7：W_w−M の丸め | closed | README §4.7。`job-out-aggregate.json:cells[].xdist.pre_entry−cells[].xdist.M` の原精度差は 11.409930〜14.864107秒。 | なし。 |
| 8：R4 の独立確認範囲 | closed | README §6、特に `README.md:156` が、段6レビューの確認範囲を保存 hash と照合実装までに限定。`s6-review-out.md` 所見8と整合。§9も report 本体の非収録を明記。 | report 本体・gw0配列からの独立再計算は未実施。この限界が明示されたため所見は閉じる。 |

## 再計算

**R8：全行・全11セル**

`acceptance-root-stat.txt` の全2,207行を読み、各 `cell.txt` の原精度 epoch に対して `start_epoch−900 ≤ birth ≤ end_epoch` を評価した。

| cell | 再計算した候補数 | README §3 |
|---|---:|---|
| warm | 0 | 一致 |
| S1-a | 0 | 一致 |
| S2f-a | 0 | 一致 |
| S3u-a | 0 | 一致 |
| S3f-a | 0 | 一致 |
| S3cf-a | 0 | 一致 |
| S3cf-b | 0 | 一致 |
| S3f-b | 0 | 一致 |
| S3u-b | 0 | 一致 |
| S2f-b | 0 | 一致 |
| S1-b | 0 | 一致 |

| 項目 | 再計算・添付記録 | README | 判定 |
|---|---|---|---|
| session数 | 2,207 | 2,207 | 一致 |
| birth 0 | 0件 | 0件 | 一致 |
| 最新 birth | 2026-09-21 17:16:52 JST | 17:16:52 | 一致 |
| 最新 mtime | 2026-09-21 17:38:58 JST | 17:38:58 | 一致 |
| 採取時刻 | `acceptance-root-stat.taken.txt:1` は21:27:27 JST | §3・§6は21:27:18 | **不一致** |

「原裁定どおり」と呼べるのは、**採取時点に存在する session に対する候補抽出条件**である。候補が0なので、候補の JUnit／report から区間を取得する後段は今回不要。原裁定は採取時刻や削除済み session の復元までは要求しておらず、その追加要件を満たさないことだけで逸脱とは判定しない。README §3・§6の残存 session 限定を含めれば閉じられる。

**R6：保存された合否フラグから独立に再計算**

worker の `cf_entry/cf_exit`、JUnit起点、早期 memo の正常復帰から `pre`・W・M・待ち中央値を再構成し、保存 `xdist` 値との一致も確認した。

| 項目 | 再計算 a / b（秒） | README §4.7 | 判定 |
|---|---|---|---|
| Δpre | 27.322724 / 26.145505 | 27.32 / 26.15 | 一致 |
| ΔW | 44.575411 / 44.527809 | 44.58 / 44.53 | 一致 |
| \|pre−M\| | 0.353586 / 0.320738 | 0.354 / 0.321 | 一致 |
| S3f 待ち中央値 | 0.022632 / 0.023838 | 0.023 / 0.024 | 一致 |
| S3cf 待ち中央値 | 18.941873 / 20.239721 | 18.94 / 20.24 | 一致 |
| 待ち増分 | 18.919242 / 20.215883 | 18.92 / 20.22 | 一致 |

両 half で W(S3cf)<M、Δpre<ΔW、|pre−M|≤2、待ち増分>0。全8セルの適合残差も +0.016943〜+0.353586秒で、README の +0.017〜+0.354秒と一致する。

**W_w−M・share・T-2825**

| 項目 | 再計算値 | README 値 | 判定 |
|---|---|---|---|
| 非cfの6セルの W_w−M 範囲 | 11.409930〜14.864107秒 | 11.41〜14.86秒 | 一致 |
| resolve share和：S2f-a | 0.963337408 | 0.963 | 一致 |
| 同：S3f-a | 0.962073957 | 0.962 | 一致 |
| 同：S3f-b | 0.966079592 | 0.966 | 一致 |
| 同：S2f-b | 0.961518806 | 0.962 | 一致 |
| T-2825 有効Bのpre | 63.0／63.5／64.4秒 | 同左 | 一致 |
| T-2825 有効A/Bのpre範囲 | 62.6〜64.4秒 | 同左 | 一致 |

share和の定義は `(median(resolve.1)+median(resolve.2))/median(modify)`。worker ごとの2葉合計の中央値ではない。4セルすべてで最大葉は resolve.1、その share は0.483445〜0.493431で、単一葉≥0.5の事前登録条件を満たさない。

**正規化記録**

記録された行末 bytes をメモリ上で復元し、18ファイルすべてについて、正規化後と復元後の byte 数・SHA-256を照合した。

| 項目 | 再計算値 | 記録・README | 判定 |
|---|---|---|---|
| ファイル数・変更行数 | 18 file・41行 | 同左 | 一致 |
| 原文 bytes 合計 | 22,589 | 表の合計22,589 | 一致 |
| 正規化後 bytes 合計 | 22,524 | 表の合計22,524 | 一致 |
| 除去 bytes 合計 | 65＝17×1＋24×2 | 表と整合 | 一致 |
| s6-review-out.md | 24行×2 byte＝48 byte | 9,823−9,775＝48 | 一致 |

`s6-review-out.md` の復元SHA-256も記録された原文hashに一致した。未正規化の別原本との直接比較ではなく、保存本文・復元指定・原文hash間の整合確認である。

**所見6の添付値**

receipt は model call **30回**、`actuals.wall_clock_s=767.138340545`、`codex_exit_code=0`。README の30回・767秒・0と一致。前後 status はそれぞれ実際に **0 byte**。

## 新規所見

1. **主張:** R8 の採取時刻が添付記録と9秒ずれている。
   **根拠:** `I/README.md:38`（§3）と `:153`（§6）は21:27:18。`I/verbatim/acceptance-root-stat.taken.txt:1` は **2026-09-21 21:27:27 JST**。指定資料から21:27:18の根拠は確認できない。候補抽出にはセルの開始・終了時刻を使うため、候補数の結果は変わらない。
   **重大度:** **nit**。
   **修正案:** §3・§6を添付記録の21:27:27へ統一する。21:27:18が採取開始なら、その出所を添え、開始・終了などの区別を明示する。

指定された追加箇所に、これ以外の新しい数値誤り、値なし前方参照、事前登録判定の変更は見つからなかった。R8の「重複なし」は、§3・§6の検知範囲を伴う判定として扱う。

## 総括

所見1〜8は **closed 8件、partial 0件、regressed 0件**。
新規所見は **nit 1件、must-fix 0件**。
指定の派生値・量化・正規化記録は一致し、採取時刻だけが不一致だった。
**GO**。ただしR8は残存 session を対象とする判定であり、外乱一般の不存在を保証しない。