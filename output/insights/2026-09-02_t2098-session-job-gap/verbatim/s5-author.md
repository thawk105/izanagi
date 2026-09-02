## 実装したもの

[tools/analyze_t2098_session_job_gap.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2098-session-job-gap/tools/analyze_t2098_session_job_gap.py:1) を新規作成しました。

- stdlib のみ、Python 3.10 対応
- 入力は stat と read-only open のみ
- 内容を読むのは accounting stderr と `receipt.json` のみ
- 出力は `sessions.csv`、`shards.csv`、`summary.json` の3本
- K=2/3、両 accounting filename 系統、欠測・曖昧性・排他除外を処理
- `--output-dir` が入力 root 配下なら、書込み前に exit 2
- commit、add、既存ファイル編集は未実施。`git status` は新規ファイル1本のみ

## 実走と oracle 一致

最終実走コマンド:

```text
/usr/bin/python3.10 tools/analyze_t2098_session_job_gap.py \
  --root /work/SFC/tanab/.izanagi-acceptance-shards \
  --output-dir /tmp/t2098-session-job-gap-py310.W34vps \
  --scheduler-timezone Asia/Tokyo \
  --d1320-cutoff-scan
```

exit 0。oracle の8値は完全一致しました。

- `S=457`
- `Jmax=442`
- `Env=443`
- `Skew=1`
- `Rpair=15`
- `Rout=14`
- `head=0`
- `tail=14`

出力は指定3本のみ、U+0300〜U+036F は source・出力とも0件です。

## 除外と層別

実走時 inventory は737 sessionで、主集合679、排他除外58でした。

- 排他除外: dispatch-intentsなし13、marker不備33、accountingなし12
- K別: K=2 が320、K=3 が359
- 月別: 2026-08 が558、2026-09 が121
- 主集合中央値: `S=339s`、`Jmax=328s`、`Env=328s`、`Skew=1s`、`Rout=13s`、`Rpair=14s`
- login collection: 全体で `off_path=691`、`on_path_candidate=0`、`indeterminate=46`

D1320 は再現しませんでした。2026-08-29 cutoffでは `(586, 1, 26, 559)` となり、両方の S 定義で中央値338秒でしたが、目標 `(568, 1, 18, 549)` と一致しません。このため集計式は「同定できず」と出力しています。

## 独立検査の分類

- `identity`: `Rpair = Rout + Skew` は679行すべて ns 差0
- `self_consistency`: inventory閉包とNQSV時刻順序はいずれも pass
- `diagnostic`: queue wait差、argmax一致率、Elapse差を分布出力
- `falsifiable`: oracleはpass、D1320 cohort再現はfail

恒等式は検証ではないこと、collection分類から臨界経路非寄与を断定できないことも `summary.json` に明記済みです。

## 波及可能性

repo全体をファイル名で検索し、この新規スクリプトへの caller/import は0件でした。共有fixture、既存consumer test、既存CLIへの接続もなく、静的な波及面はありません。

## 未了・既知の限界

- root はsnapshotではなく、実走時は仕様記載の743ではなく737 sessionでした。
- 主集合はcomplete-caseであり、長時間側が欠測しやすい可能性があります。
- `head` / `tail` は時計offset込みのraw値です。
- 保存測点がないため、`Ended → handled` をpoll・収集・mergeへ分割していません。
- D1320は合わせ込まず、再現不能・式同定不能として残しています。

## 総括

実装・Python 3.10実走・oracle完全一致まで完了しました。repo内の変更は、親が退避する予定の新規スクリプト1本だけです。