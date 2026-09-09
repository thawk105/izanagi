## 直したもの

- [submit_t2265_perf6.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/submit_t2265_perf6.sh:28)
- [wait_t2265_perf6.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2-perf6/wait_t2265_perf6.sh:103)

## F12 の対応

`qsub` stdout を次の実測文型へ全体一致させ、RequestID だけを抽出します。

```text
Request <RequestID> submitted to queue: gen_S.
```

抽出後も `^([0-9]+:)?[A-Za-z0-9._-]+$` を検査します。文型不一致または不正 RequestID は rc=3 で停止し、stderr に指定マーカーと stdout 全文を出します。

`expected_json` は抽出した RequestID を使用し、コロンをアンダースコアへ置換する既存処理を維持しています。

## F13 の対応

すべての一覧行で RequestID の形式は引き続き検査しますが、STT の既知語彙検査は台帳内 RequestID と一致する行だけに限定しました。

他 job の未知 STT は無視し、自 job の未知 STT は従来どおり rc=4 で fail-closed になります。

## 自分で走らせた検査

- `bash -n submit_t2265_perf6.sh`: rc=0
- `bash -n wait_t2265_perf6.sh`: rc=0
- 実測 `qsub` 文型: rc=0、7 行を記録
  - 抽出 ID: `986814.nqsv`
  - rep 0 の JSON: `stage1-rep0-986814.nqsv.json`
- 空 stdout: rc=3、マーカーと空の生出力を確認
- 別文: rc=3、マーカーと生出力を確認
- 素の ID: rc=3、マーカーと生出力を確認
- 実測文型内の不正 RequestID: rc=3、ID 検査と生出力を確認
- 自 job=`RUN`、他 job=`XYZ`: rc=5
  - `IZ_MAX_WAIT_S=0` による意図した timeout
  - monitoring error は 0 件
  - live 1 行、terminal 6 行、inventory 7 行
- 自 job=`XYZ`: rc=4
  - 未知 STT エラー 1 件、inventory 7 行

最初の submit ハーネス試行は、偽 `sha256sum` が stdin を読まなかったため preflight rc=2 でした。偽物を修正し、上記ケースをすべて再実行しました。

## 未実走・限界

本物の `qsub`、`qstat`、`qdel` は実行していません。job の投入や実 queue での長時間待機も行っていません。

一時ファイルは削除せず、次に残しています。

```text
/tmp/t2265-f12-f13.qi69du
```

## 波及可能性

repo 内で変更したのは指定された 2 本だけです。7 本の cell literal、`elapstim_req=01:00:00`、preflight、台帳形式、inventory、rc 体系、`qdel` 不使用は変更していません。commit、push、git 状態変更も行っていません。

## 総括

F12 と F13 を限定的に修正し、偽 NQSV コマンドによる正常系・fail-closed 系を確認しました。構文検査も両方 rc=0 です。