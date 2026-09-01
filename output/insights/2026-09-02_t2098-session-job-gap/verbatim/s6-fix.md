## 所見対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| 全 shard の job span 分布 | closed | pooled 分布と中央値差を追加 |
| 出力 file の追従書込み | closed | `O_EXCL`、`O_NOFOLLOW` で既存 path を拒否 |
| 会計 file の request ID 束縛 | closed | exact path を優先し、読めない場合だけ prefix fallback |
| K の `{2,3}` 制限 | closed | `shard_count_invalid` を排他理由・counter に追加 |
| D1320 fallback 有無 | closed | 両版の件数、中央値、再現判定を別々に出力 |
| D1320 regular-file 判定 | closed | 主集合と同じ判定へ統一 |
| 中間 symlink 拒否 | closed | root から対象まで全構成要素を確認 |

変更は [tools/analyze_t2098_session_job_gap.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/analyze_t2098_session_job_gap.py) だけです。commit、add、stash は実施していません。

## 実走

新規空ディレクトリ `/tmp/t2098-fix-final.paa78L` で次を実行し、exit 0 でした。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/analyze_t2098_session_job_gap.py \
  --root /work/SFC/tanab/.izanagi-acceptance-shards \
  --output-dir /tmp/t2098-fix-final.paa78L \
  --scheduler-timezone Asia/Tokyo \
  --d1320-cutoff-scan
```

結果は 738 session、主集合 679、除外 59、oracle pass です。[summary.json](/tmp/t2098-fix-final.paa78L/summary.json)

同じ出力先への再実行は exit 2 となり、既存 `sessions.csv` の path を含むエラーを出しました。3 ファイルのサイズは再実行前後で不変でした。

## oracle と中央値の変化

oracle 8 値は修正前と完全に同一です。

- `S=457`
- `Jmax=442`
- `Env=443`
- `Skew=1`
- `Rpair=15`
- `Rout=14`
- `head=0`
- `tail=14`

主集合中央値も修正前から変化していません。

| 量 | 修正前 | 修正後 |
|---|---:|---:|
| S | 339 | 339 |
| Jmax | 328 | 328 |
| Env | 328 | 328 |
| Skew | 1 | 1 |
| Rout | 13 | 13 |
| Rpair | 14 | 14 |

修正前実測後に corpus が 737 から 738 session へ増えましたが、追加分は除外側で、主集合 679 件と中央値は不変でした。

D1320 は両版とも全 cutoff で再現しませんでした。2026-08-29 は以下です。

- fallback あり: `(586, 1, 26, 559, median 338)`
- fallback なし: `(559, 0, 0, 559, median 338)`
- 目標: `(568, 1, 18, 549, median 338)`

## 新しい集計 (全 shard の job span)

主集合の全 eligible shard を pooled 集計した結果です。

| n | min | p25 | median | p75 | p90 | max |
|---:|---:|---:|---:|---:|---:|---:|
| 1717 | 11 | 171 | 259 | 341 | 517 | 3844 |

すべて秒です。

- `median(S) - median(pooled job span) = 339 - 259 = 80秒`
- `median(S) - median(Jmax) = 11秒`
- `median(Rpair) = 14秒`
- 後二者は一致しません。

80秒は現在の主集合で歴史的な75秒と同じ形を計算した値であり、D1320 cohort の再現値でも因果分解でもありません。

## 波及可能性

- repo 内 caller: ファイル名・新規 key を参照する caller は見つかりませんでした。
- 共有 fixture: 参照・変更ともありません。
- consumer test: repo 内には見つかりませんでした。
- 外部 consumer: `d1320_reproduction` の下が `with_fallback` / `without_fallback` に分かれ、CSV列も追加されたため、旧構造を直接読む外部処理には波及し得ます。
- 再実行 caller: 出力先は毎回新規空ディレクトリである必要があります。

## 未了・既知の限界

未了の実装項目はありません。

- D1320 exact cohort は両版とも再現していません。
- 走査は snapshot ではなく、実測中にも corpus は変化し得ます。
- 実 corpus では `shard_count_invalid=0`、`path_component_symlink=0` でした。
- request ID を読めず prefix fallback へ落ちた shard は87件です。
- complete-case では長時間側が選択的に欠ける可能性が残ります。
- 出力3本から U+0300〜U+036F が存在しないことも確認しました。

## 総括

指定された7件はすべて実装・実走済みで、oracle 8 値と主集合中央値を維持しました。全 shard の pooled job span 中央値は259秒、現在の主集合での非対差は80秒です。中央値差11秒と paired 中央値14秒は異なり、項別の中央値を分解として扱えないことも出力へ明記しました。