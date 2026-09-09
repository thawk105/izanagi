## 直したもの

[submit_t2265_perf6.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:164) のみ修正しました。

## F14 の対応

- `expected_json` に固定接頭辞 `0_` を追加しました。
- 根拠として、既存成果物 20 件すべての実測に基づく旨をコメント 1 行で記載しました。
- 台帳の `pbs_jobid` は従来どおり接頭辞なしの `986814.nqsv` です。
- F1〜F13、cell literal、walltime、wait script には触れていません。

## 自分で走らせた検査

- `bash -n submit_t2265_perf6.sh`
  - exit code: `0`
- PATH の先頭に偽 `qsub` を置いた投入検査
  - 解決された `qsub`: `/tmp/t2265-f14-check.4ouiN1/fakebin/qsub`
  - submit script exit code: `0`
  - 台帳検証 exit code: `0`
  - 記録された submission 数: `7`
  - `pbs_jobid`: `986814.nqsv`
  - 実際の `expected_json`:
    `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/perf/stage1-rep0-0_986814.nqsv.json`

## 未実走・限界

本物の `qsub`、`qdel`、job 投入は実行していません。偽 `qsub` 検査では、preflight 用のパスと依存物を一時 fixture に差し替えて実行しました。

一時ディレクトリは指示どおり削除せず、次に残しています。

`/tmp/t2265-f14-check.4ouiN1`

## 総括

F14 のみを適用し、実際の PBS 成果物名と一致する `stage1-rep<N>-0_<RequestID>.json` が台帳へ記録されることを確認しました。リポジトリ内で変更したのは `submit_t2265_perf6.sh` だけです。