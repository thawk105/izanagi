## 実装と検証

[tools/t2709_blob_transfer_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2709-unit-probe/tools/t2709_blob_transfer_probe.py) を新規作成しました。959 行。他の repo ファイルの編集・commit・本走・pytest 受入は行っていません。

`sha256sum` の結果:

```text
0e6759231b0e92d082196872288b978ea01ff153cecd77ad701d0de945fcef18
```

最終版で実走した command:

```bash
python3 -B -m tools.t2709_blob_transfer_probe --selftest --source-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2709-unit-probe --work-parent /tmp --out /tmp/t2709-author-selftest-2.json
```

rc=0。20 項目成功、`failures=[]`。三方式の tree/commit 一致、stat 保存、失格負例を確認しました。loose object 数は A=8、C1=4、tree/commit 分=3 でした。

```bash
python3 -B -m tools.t2709_blob_transfer_probe --hold-session-only --source-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2709-unit-probe --work-parent /tmp --out /tmp/t2709-author-hold-2.json
```

rc=0。内部 collection rc=5、158 件 deselected、テスト実行なし。環境維持と module path 一致を確認しました。両実行とも work-root を削除済みです。

修正前にも同じ command を、それぞれ `--out /tmp/t2709-author-selftest.json`、`--out /tmp/t2709-author-hold.json` で実走しました。前者は rc=1（alternates 負例で非数値の `count-objects` 行を処理できず）、後者は rc=0。初回結果を残し、修正後は別 JSON に保存しています。

## 仕様対応表

| 仕様 | 対応関数 | 検証状況 |
|---|---|---|
| §0 起動・環境・cleanup・timeout | `main`, `fstype`, `git`, `build_once`, `save` | 通常起動・cleanup 実走。timeout、拒否分岐は未実走 |
| §1 Git・metadata・計時 | `git_env`, `git`, `status_prod`, `transfer` | 合成 repo で実走 |
| §2 builder・参照抽出 | `hold_session`, `build_once`, `reference`, `measure` | hold・合成参照抽出は実走。実 builder は未実走 |
| §3 再初期化 | `reference`, `reset` | 合成 repo で実走。modules rename は未実走 |
| §4 A/C1/C2 | `select`, `transfer`, `step`, `run_variant` | 合成 repo で実走。本走は未実走 |
| §5 検査 (i)〜(x) | `check_trial`, `variant_checks`, `mutations`, `copy_timed` | submodule 以外は合成 repo で実走。submodule・本走の副次量は未実走 |
| §6 事前実験・設定選択 | `pretrials` | 実装済み・未実走 |
| §7 順序・hash pass | `measure` | 実装済み・未実走 |
| §8 JSON・集計・判定 | `save`, `finish_row`, `summarize`, `main` | JSON 保存は実走。本走集計・判定は未実走 |
| §9 selftest | `selftest`, `require` | 20 項目成功 |
| §10 禁止事項 | `main`, `git_env`, `reset`, `run_variant`, `summarize` | 計測区間・環境・失格保持を実装。本走は未実走 |

## 限界と投入前の確認

- v2 を優先し、selftest は submodule なしです。実 builder、modules の退避・復帰、submodule 内変更検出は計算ノードで確認が必要です。
- timeout と強制終了時の挙動は未実走です。builder 全体に 1800 秒の期限を設けています。
- 裁定の walltime `01:30:00` を確保してください。実測所要時間はまだありません。
- `--work-parent` と `--out` の親ディレクトリは事前作成が必要です。source-root 外を指定してください。今回の `/tmp` は xfs でしたが、計算ノード側は別途確認が必要です。
- 改行を含む path は hash pass を skip し、不足 blob 生成では失格にします。先頭が引用符の path も明示的に拒否します。
- 事前実験に失格がある場合は失敗を保持し、既定 pack 設定へフォールバックした理由を記録します。

## 総括

指定の 1 ファイルを実装し、最終版の selftest／hold-session-only はともに rc=0 でした。本走と実 fixture の submodule 検証は未実走です。性能改善の結論は出していません。