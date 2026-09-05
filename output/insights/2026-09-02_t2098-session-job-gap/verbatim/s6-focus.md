## 7 件の判定

| # | severity | 判定 | 独立判定と成果物への影響 |
|---:|---|---|---|
| 1 | BLOCKER | `closed` | 主集合 shard の `job_span_ns=E_j-C_j` を pooled 集計し、分布、80秒、12秒、paired 14秒を別々に出している。影響: 歴史的75秒と同じ形の量へ回答できる。 |
| 2 | BLOCKER | `closed` | 3出力を `O_WRONLY｜O_CREAT｜O_EXCL｜O_NOFOLLOW` で作成し、既存 path は path 付きエラーで拒否する。影響: 同名 symlink、hardlink、通常 file を追従して切り詰めない。 |
| 3 | MAJOR | `closed` | confirm の `request_id` から、2 stemと正規化3種による exact path 集合を作り、その後に曖昧性を判定する。読めない場合だけ prefix fallback となり、親 v2 の counter は87 shard。影響: request ID がある shard で古い prefix 一致 log が混入しない。 |
| 4 | MAJOR | `closed` | 推定 K が2または3以外なら `shard_count_invalid` を排他除外へ追加する。親 v2 では該当0件。影響: 異常な K が主分布へ入らない。 |
| 5 | MAJOR | `closed` | D1320 を `with_fallback` と `without_fallback` に分け、件数、両中央値、再現判定を独立出力する。影響: fallback 依存の結果を裁定準拠版と混同しない。 |
| 6 | MAJOR | `closed` | `markers_complete` は全 confirm、handled の status が `regular` であることを要求する。fallback 候補も regular file だけから採る。影響: directoryやsymlinkのmtimeを完全 marker として扱わない。 |
| 7 | MAJOR | `closed` | rootから対象までを `lstat` し、symlink component を `path_component_symlink` として shard、session の除外へ伝播する。親 v2 の counter は0。影響: 中間 symlink 経由のroot外読取りを通常の解析入力として受理しない。 |

7件に `partial` または `regressed` はありません。判定は [fix後script](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py) の実装と [親v2 summary](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/run-parent-v2/summary.json) に基づきます。fix子の自己申告には依存していません。

## 回帰

7件と無関係な静的回帰は見つかりませんでした。

- 主推定量は引き続き `S=max H-min F`、`Jmax=max(E-C)`、`Env=max E-min C`、`Skew=Env-Jmax`、`Rout=S-Env`、`Rpair=S-Jmax`。
- 既存除外理由どうしの優先順位は不変。新しい `shard_count_invalid` と `path_component_symlink` だけが、意図どおり marker 欠測より前に加わった。
- oracle の期待8値は不変。親 v2 でも actual と expected が全て一致している。
- quantile は引き続き one-based `ceil(p*n)` の nearest-rank。
- login collection は `off_path`、`on_path_candidate`、`indeterminate` の3分類を維持し、`off_path` でも親を遅らせなかったとは言えない、という `limitation` 文も逐語的に不変。

MINOR — fix前後の親実測は同一 snapshot ではありません。737 session、主集合679件から739 session、680件へ増え、Jmax中央値も328秒から327秒へ動いています。影響: 「同一 corpus で全中央値が不変だった」とは書けません。ただし式の変更による回帰ではなく、静的差分上は式が不変で、実測時刻間の live corpus 増加と整合します。

read-only 制約のため、解析 script や pytest を再実行しておらず、緑は主張しません。

## pooled 集計の検査

母集合は主集合と一致しています。集計条件は `primary_session_included` かつ `job_span_ns` が存在する shard です。主集合では全 shard に有効な C、E が必要なので、後半の条件による追加脱落はありません。

親 v2 の K 別内訳は次のとおりです。

- K=2: 320 session
- K=3: 360 session
- 合計: 680 session
- shard 数: `320×2 + 360×3 = 1720`

したがって `pooled_shard_job_span.n=1720` は主集合680 session と完全に整合します。除外 session の shard は混入していません。

分布は `n=1720、min=11、p25=171、median=259、p75=341、p90=516、max=3844` 秒です。

## 親の算術の検算

すべて正しいです。

- `339−259=80` 秒。
- `(339−327)+(327−259)=12+68=80` 秒。
- paired な `median(S-Jmax)=median(Rpair)=14` 秒は、`median(S)-median(Jmax)=12` 秒とは別物。
- 80秒の二分は中央値間の算術的な恒等式にすぎず、per-session 分解や原因内訳ではない。

最後の `Rout` と `tail` の主張も summary から導けます。

- 680行すべてで `Rout=head+tail`、非零差0。
- head の `n=680、min=-2、max=0` 秒。
- 従って各行で `Rout-tail=head∈[-2,0]`、つまり `｜Rout-tail｜≤2` 秒。

より正確には、「全行で Rout は tail 以下で、tail より最大2秒小さい」です。ただし、この恒等式は代数的自己整合であり、head、tail の時計間 offset を検証するものではありません。

## D1320 の書き方

「cohort は再現しなかったが、中央値338秒は両版、両定義で再観測された」は正しいです。2026-08-29について、

- fallbackあり: `(586, 1, 26, 559)`、両中央値338秒
- fallbackなし: `(559, 0, 0, 559)`、両中央値338秒
- 目標: `(568, 1, 18, 549)`、中央値338秒

両版とも `reproduced=false` であり、338秒の一致は cohort、選択規則、式の同定を意味しません。

259秒とD1320の263秒について書いてよい範囲は次です。

> いずれも shard/job を観測単位として `E_j-C_j` を pooled した中央値であり、259秒が263秒に近いことは、同種の量に対する別 cohort の推定値として大きく矛盾しない、という限定的な傍証である。

一方、「同じ cohort を再現した」「D1320の263秒を更新した」「差4秒なので選択規則も同じ」とは書けません。D1320は549 session、1297 job、今回は680 session、1720 shardであり、母集合が異なります。

## 総括

7件はすべて `closed`、新しい pooled 集計の母集合と `n=1720` も整合しています。親の80秒、12秒と68秒への算術分割、paired中央値14秒との区別、Routが各行でtailの2秒以内という主張はいずれも正しいです。

成果物では、D1320を「cohort再現失敗と338秒の限定的な再観測」、259秒対263秒を「同じ式と観測単位に対する別 cohort 間の弱い数値的一致」までに留めれば、資料の射程内です。