## 所見一覧

- BLOCKER — 出力 3 ファイルを追従書込みで開くため、既存の symlink または hardlink を介して入力 artifact を切り詰められる ([script:1431](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:1431))。影響: `--output-dir` が root 外でも入力内容と成果物を破壊できる。
- MAJOR — 会計候補を request ID に束縛せず prefix 一致だけで列挙し、正本の `_log_candidates` と選択意味が異なる ([script:311](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:311), [dispatcher:1672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/pegasus/dispatch_compute.py:1672))。影響: 再利用 directory の古い log を採用するか、複数 hit として有効 session を除外し、推定値と受理集合が変わる。
- MAJOR — shard 集合を `0..max(observed)` とし、K が 2 または 3 であることを確認しない ([script:321](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:321))。影響: 完全な K=4 以上の異常 session が主集合へ入り、全分布を変えうる。
- MAJOR — D1320 の不完全 session に、仕様にない `max available H → max available F → session mtime` fallback を導入している ([script:644](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:644))。影響: 現成果物でも 46 session の cutoff 所属が追加仮定に依存し、`reproduced=false` は裁定だけから導けない。
- MAJOR — D1320 の marker 完全性を regular-file status ではなく mtime の有無だけで判定する ([script:564](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:564))。影響: directory や symlink の marker を D1320 完全集合へ入れ、件数と両中央値を変えうる。
- MAJOR — `shard-N` など中間 path の symlink を拒否せず、`O_NOFOLLOW` は最終 file にしか効かない ([script:363](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:363))。影響: root 外の会計・receipt・metadata が入力として混入し、値と参照先が変わる。

## 推定量の実装

主集合での式は裁定どおりです ([script:626](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:626), [script:664](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:664))。

- `S = max H - min F`
- `Jmax = max(E-C)`
- `Env = max E - min C`
- `Skew = Env-Jmax`
- `Rout = S-Env`
- `Rpair = S-Jmax`
- `head = min C-min F`
- `tail = max H-max E`

NQSV 時刻は秒から正確に `10^9` 倍され、mtime は ns のままです。符号反転もありません。

`identity_rpair_diff_ns` は別の観測による検証ではなく、同じ `S`、`Env`、`Jmax` から作った代数的恒等式です。全行 0 は自己満足ですが、script 自身も `identity` と明記しており、仕様上の扱いは正しいです。

quantile は `ceil(p*n)` です ([script:725](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:725))。ただし偶数 `n=2m`、`p=0.5` では rank は `m` なので、中央 2 値の上側ではなく下側を取ります。実例として K=2 の S は 160 番目が 333 秒、161 番目が 334 秒で、報告値は 333 秒です。

## 会計 parse

両 filename 系統は見ていますが、dispatcher と同値ではありません。

- `izdw-shard-N.e*` と `dispatch.sh.e*` の両方を prefix 検索する。
- 0 hit は `accounting_missing`、2 hit 以上は内容を読まず `accounting_ambiguous`。
- dispatcher は現在の request ID から有限個の exact path を生成するのに対し、解析 script は request ID を解析・照合しない。
- `Created` 欠落は後段で `missing_created` として主集合から除外する。
- `Request Name` 欠落は除外せず auxiliary counter にだけ入れる。

`one_field` は file 全体を検索し、同一 label が複数あれば `parse_error` にします ([script:204](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:204))。追記された複数 summary から末尾を選ぶ処理はなく、どれも採りません。

`Wed Sep  2 02:24:47 2026` は受理され、曜日も実日付と照合されます。`ZoneInfo("Asia/Tokyo")` を使うため OS または Python の tz database に依存します。2026 年の Asia/Tokyo には DST がないので今回の timestamp に fold/gap はありませんが、固定 `+09:00` 実装ではありません。

## 除外規則

主集合の除外条件と優先順位は裁定に一致します。排他理由は unreadable、dispatch-intents、marker、会計欠落、曖昧、parse、Created、Ended、scheduler 順序、login 順序の順です。

- K=2 は破損扱いされず、現成果物でも 320 session が主集合に含まれています。
- outcome 自体を除外条件にしていません。現 snapshot の queue-wait-timeout 18 shard は必要 marker・会計の独立した欠落によって結果的に除外側です。
- 負の head 20 session は保持されています。
- `Started`、receipt、report、junit、login-collection の欠落は主集合を落としません。
- 現成果物は `679 + 58 = 737` で排他的に閉じています。

ただし K 上限未検査と、D1320 だけ regular marker 判定を迂回する問題は所見一覧のとおりです。

## oracle の恒真性

oracle は恒真ではありません。期待値は実装から生成されず、射影された会計値と marker mtime から独立に導けます。

- `S = 02:32:23 - 02:24:46 = 457`
- shard job span は 442、136、365 秒なので `Jmax=442`
- `Env = 02:32:09 - 02:24:46 = 443`
- 従って `Skew=1`、`Rout=14`、`Rpair=15`
- `head=0`、`tail=14`

具体的には shard-0 の Ended が `02:32:08` と解析されれば、`Jmax`、`Env`、`Rout`、`Rpair`、`tail` が期待値から外れ、oracle は fail、終了 code は 3 になります。

## D1320 cutoff 走査

完全 marker session は `max H` の Asia/Tokyo 日付を anchor とし、`date <= cutoff` の包含です。走査対象は観測された anchor 日付だけですが、所属集合はその日付でのみ変わるため、完全 session については十分です。

不完全 session の fallback は script 独自です。現 summary の内訳は `max available H` 9、`max available F` 2、session mtime 35 です。anchor 不在は全 cutoff に含める設計ですが、通常の directory entry には mtime があるため主に stat-error 時だけ到達します。

2 定義は別々に計算されています。

- `median_max_h_minus_min_f_s` は `max H-min F`
- `median_max_h_minus_matching_f_s` は `max_j(H_j-F_j)`

実測 summary でも 2026-08-24 は 332 対 331、2026-09-01 は 339 対 338 であり、同じ値の二重出力ではありません。2026-08-29 は両方 338 秒ですが、件数が `586 / 1 / 26 / 559` で目標 `568 / 1 / 18 / 549` と一致せず、script の採用規則下では fail です。

## 入出力の安全

`root.resolve(strict=True)` と `output.resolve(strict=False)` により、検査時点の通常の symlink、相対 path、`..` は正規化され、output directory 自体が root 配下なら拒否されます ([script:106](/home/SFC/tanab/.claude/jobs/c470891f/tmp/t2098/analyze_t2098_session_job_gap.py:106))。

一方、出力 directory 内に既存の `sessions.csv`、`shards.csv`、`summary.json` symlink または hardlink がある場合は追従して `"w"` で開きます。これが BLOCKER です。

入力側に直接 `mkdir`、`touch`、lock、書込み mode の open はありません。`report.json`、shard/root `junit.xml`、`login-collection.log` は `stat` のみで、内容は開いていません。内容を開くのは会計 stderr と `receipt.json` だけです。ただし中間 symlink による root 外読み出しは防げていません。

## 総括

既存 `sessions.csv` を read-only で引き直すと、主集合 679 件の nearest-rank rank 340 は summary と全て一致しました。

| 量 | 再計算値 | summary |
|---|---:|---:|
| S | 339 | 339 |
| Jmax | 328 | 328 |
| Env | 328 | 328 |
| Skew | 1 | 1 |
| Rout | 13 | 13 |
| Rpair | 14 | 14 |
| head | 0 | 0 |
| tail | 13 | 13 |

主推定量と現在の中央値に数値不一致はありません。ただし、出力 leaf の追従書込みは入力破壊を許し、D1320 の `reproduced=false` は仕様外 fallback に依存します。sandbox 制約に従い pytest と解析 script 本体は再実走しておらず、緑は主張しません。