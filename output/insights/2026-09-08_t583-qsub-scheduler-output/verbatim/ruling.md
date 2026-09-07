# 段 4 裁定 — [T-583] qsub の -o / -e を repo 外の file path にする

段 2 プラン、段 3 レンズ A (scope 逸脱・precedent 整合)、レンズ B (負例の恒真性・到達可能性) と、
親の追加実測から、実装する形を確定する。

## 0. 親 brief の誤りの訂正 (両レンズが独立に指摘、親が実測で確認)

- **訂正 1 (real、採用):** brief の「submit directory = qsub 実行時の cwd = **repo root**」は誤り。
  `tools/pegasus/submit_certify.sh` は qsub の前に `REPO_ROOT` へ `cd` しない (script 内の `cd` は
  12・13・27 行の path 解決用サブシェルだけ)。対して `tools/pegasus/submit_floor.sh:664` は
  `cd "$REPO_ROOT"` の subshell で qsub を実行する。**親が両 script を直接 grep して確認した。**
  正しい記述は「返り先は呼出し元の cwd であり、記録済み運用が repo root から投げていたので
  repo root だった」。
- **訂正 2 (real、採用):** brief の「repo 外 root の precedent が 3 箇所で同一」は、**path 導出式**に
  ついてだけ成立する。**scheduler 出力の配置**の precedent は `submit_b10_backoff_shape.sh` だけで、
  `submit_floor.sh` は scheduler 出力を repo 内 `output/` に置いている。配置は B10 側を採る
  (D1291 と runbook §8 が repo 外を要求するため)。
- **訂正 3 (real、採用):** brief の「pin 閉包は不在」「触っている稼働 wave は無い」は全称否定として
  強すぎる。実際に行ったのは (a) 現 file の sha256 literal 検索、(b) path を key にする consumer の
  列挙、(c) `*.sh` を集合で走査する glob consumer の検索、(d) admission registry loader の読解
  (自身の JSON bytes の正規性しか検証していない)、(e) 全 worktree の dirt と `main...HEAD` の
  時刻付き走査。**この探索範囲で pin と重複編集面を発見しなかった**、と書く。
- **訂正 4 (real、採用):** 既存テストが `usage()` を「逐語」で束縛しているという brief の記述は誤り。
  `test_submitter_exposes_only_the_calibration_whitelist` は substring 一致である。
  不変条件としては「該当ブロックを編集しない」で足り、逐語保証を主張しない。

## 1. 争点の裁定 — 封じ込め gate を作るか

**裁定: 作らない (レンズ A 所見 1 を real として採用、P2・P3 とも削る)。**

理由は 3 つで、いずれも実測に基づく。

1. **ユーザー裁定の文面。** D1291 は「直すのは投入時の引数 1 箇所である」、依頼引数は
   「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。rc=2 で拒否する封じ込め判定は
   script の受理集合を変える新しい gate であり、両方に抵触する。
2. **循環。** レンズ B が「負例は恒真でない」と示した根拠は、変異 (m3) 判定を常に true にする・
   (m5) 判定を qsub 後へ動かす、で赤になることだった。しかし **(m3)(m5) はその gate が在って
   初めて存在する変異**である。gate を足し、gate を撃つ負例を足し、その負例が gate を守るから
   gate が要る、という循環になっている。gate 無しで残る変異 (m1)(m2)(m4) は、いずれも
   argv を実走で検査する側のテストが捕捉する (レンズ B の変異対応表がそう認めている)。
3. **守る先が実環境で到達不能。** gate が拒否する状態は「導出式が repo 内を指す repo topology」で
   ある。レンズ A 所見 4 はその経路として submodule を挙げた。**親が実測した**:

   ```
   $ bash tools/pegasus/submit_certify.sh --repo-root <worktree>/external/ccbench --dry-run
   policy not found: <worktree>/external/ccbench/tools/pegasus/policy.json
   RC=2
   ```

   policy 検査 (script 45-48 行) が導出より前にあり、submodule を `--repo-root` に指す経路は
   そこで死ぬ。走行後の `git status --porcelain --untracked-files=all` は空で、副作用も無かった。
   残る経路は `git init --separate-git-dir` の repo だけで、izanagi はその配置を採っていない。
   **これは規律で言う仮想リスクそのもの**である。

## 2. 「負例」の形 (依頼の要求を満たす形)

依頼は「移した先が repo 外であることを検査する負例を同じ commit へ入れる」である。
gate を作らずにこれを満たす形を採る — **script を実走し、qsub へ渡る argv を実際に解析して、
返り先が repo の内側でないことを主張するテスト**。実装を壊して返り先が repo 内へ動けば赤になるので
負例として機能し、source 文字列の一致ではないので恒真でもない。

## 3. 確定した実装 (plan v2)

`tools/pegasus/submit_certify.sh` の変更は次の 2 点だけ。

1. **root の導出** (dirty gate の後、staging 作成の前あたり):

   ```bash
   GIT_COMMON_DIR=$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir) || exit 2
   SCHEDULER_OUTPUT_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/calibration-certify"
   mkdir -p "$SCHEDULER_OUTPUT_ROOT"
   ```

   - `mkdir -p` は gate ではなく、機能が動くために必要な directory 作成である。失敗すれば
     `set -Eeuo pipefail` が落とす。**専用の error message・rc・realpath 正規化・symlink 走査・
     containment 判定は足さない。**
   - 導出式は `submit_b10_backoff_shape.sh:136` / `submit_floor.sh:564` / `floor_campaign.sh:56` と同形。

2. **qsub argv** (現行 176 行):

   ```bash
   SCHEDULER_STDOUT="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stdout"
   SCHEDULER_STDERR="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stderr"
   qsub_cmd=(qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR" -v "$export_spec" "$JOB_SCRIPT")
   ```

**それ以外は 1 byte も変えない。** `usage()`、引数解析、RRATIO 検査、dirty gate の
`':(exclude)output'`、preflight 4 capture、`pre-submit.json` / `submit-receipt.json` の payload と
schema、`--dry-run` 分岐、export 変数。新しい CLI 引数は足さない。

## 4. 確定したテスト (`orchestrator/tests/test_pegasus_calibration_workload.py`)

`test_pegasus_tools.py:1564-1619` の clean git fixture と同型の fixture を使い、
**`tmp_path` 配下に fixture repo を作る**。これにより導出 root は `tmp_path/izanagi-job-evidence/
calibration-certify` になり、実運用の `/work/1/SFC/tanab/izanagi-job-evidence/` を汚さない。
これは必須要件である。

1. **正例** `test_submit_dry_run_passes_scheduler_file_paths_to_qsub`
   - `--repo-root <fixture> --attempts-root <fixture 外> --dry-run` で実走し rc=0。
   - stdout の `qsub command:` 行を `shlex.split` で argv へ戻す。
   - `-o` と `-e` が存在し、直後の値が絶対 path である。
   - basename が `<32桁 nonce>.scheduler.stdout` / `.scheduler.stderr` で、両者の nonce が一致する。
   - 値が root directory 自身と一致しない (file path であって directory でない)。
   - 親 directory が、fixture 自身の `git rev-parse --path-format=absolute --git-common-dir` から
     導いた `<2つ上>/izanagi-job-evidence/calibration-certify` と一致する。

2. **負例** `test_submit_dry_run_keeps_scheduler_output_outside_the_repository`
   - 同じ実走で得た `-o` / `-e` の値について、**fixture repo root と等しくなく、その配下でもない**
     ことを主張する。git common repo についても同様に主張する。
   - 受理の含意: 返り先が repo の外にあるとき、この検査は通り、qsub argv はそのまま構築される。
   - 拒否の含意: 返り先が repo root 自身または その配下へ動いた瞬間に、この検査は赤になる。
   - 通る正例: 直前の `test_submit_dry_run_passes_scheduler_file_paths_to_qsub`。

**主張してはいけないこと** (両レンズが独立に指摘、real として採用):
- 「qsub を実行しなかったことを実証した」— dry-run 分岐は封じ込めとは独立で、何もしない qsub stub
  でも同じ観測になる。テストが言えるのは argv 契約までである。
- 「NQSV が受理し実際に leaf へ書くことを確かめた」— dry-run では観測できない。
  repo 外 `/work` 配下の `-o` / `-e` がこの機体で動く証拠は addendum A4 の B10 実績に留める。

## 5. 変異事前登録 (DW-M01)

対象は `tools/pegasus/submit_certify.sh` の新規 2 ブロック。全 5 件、期待は KILLED。

| # | 変異 | 期待赤 | 単一理由性 |
|---|---|---|---|
| m1 | `-o "$SCHEDULER_STDOUT"` を qsub argv から削る | 正例 (argv に `-o` 無し) | 前後・内側に同じ入力を拒否する層なし |
| m2 | `-e "$SCHEDULER_STDERR"` を qsub argv から削る | 正例 (argv に `-e` 無し) | 同上 |
| m3 | `SCHEDULER_STDOUT` を `"$REPO_ROOT/scheduler.stdout"` に差し替える | **負例** (repo 配下) | 同上 |
| m4 | `-o` の値を leaf でなく `"$SCHEDULER_OUTPUT_ROOT"` (directory) にする | 正例 (basename 不一致 / root 一致) | 同上 |
| m5 | 導出の `dirname` を 2 段から 1 段に減らす | **負例** (root が repo 配下へ入る) | 同上 |

- m5 は「literal を書き換える」のでなく **導出そのものを壊す**変異で、負例が性質を守っている
  ことの証拠になる。
- 変更前 HEAD には m1〜m5 の変異対象行が存在しないため、`DW-M08` の新旧両走のうち旧走は空である。
  この理由を台帳へ書く。
- 冗長 gate は無い (封じ込め gate を作らないため、赤理由は新テストだけに絞られる)。

## 6. real / refuted 一覧

| 出所 | 所見 | 裁定 |
|---|---|---|
| A-1 | plan は D1291 を 3 機構ぶん超過 | **real・採用** (gate/provision/CLI/新 error を削る) |
| A-2 | brief の「cwd = repo root」は code から導けない | **real・採用** (訂正 1) |
| A-3 | floor は scheduler 出力の repo 外 precedent ではない | **real・採用** (訂正 2、配置は B10 側) |
| A-4 | common-dir 導出は submodule で repo 外を保証しない | **real だが到達不能** — 実測で policy 検査に阻まれる。対応範囲を top-level checkout と linked worktree に限定し、一般的安全性を主張しない。gate は作らない |
| A-5 | flat な共有 root は別 wave と同一 leaf path になりうる | **real・残余として記録**。128-bit nonce。予約機構は作らない (scope 外) |
| A-6 | 既存テストは usage を逐語束縛していない | **real・採用** (訂正 4) |
| A-7 | dry-run test は qsub 非実行を実証しない | **real・採用** (§4 の禁止事項) |
| A-8 | 既存 consumer は赤くならない。duration ledger を落とすな | **real・採用** (焦点走は 2 file、`check_docs.py` と ledger は inventory に残す) |
| A-9 | 機体固有 path は repo へ入らない | 攻撃失敗・確認 |
| B-1 | 計画負例は恒真でない | **refuted (前提ごと)** — gate を作らないので該当する負例自体が無くなる |
| B-2 | 正例と負例を対にせよ | **real・採用** (§4 で対にした) |
| B-3 | qsub 非実行の因果は検査できない | **real・採用** (A-7 と同じ) |
| B-4 | 負例入力は到達可能だが事故型とは別物 | **real・採用** (訂正、事故型は正例側が捕捉) |
| B-5 | 「cwd = repo root」は一般に不成立 | **real・採用** (A-2 と同じ、訂正 1) |
| B-6 | dry-run は NQSV の受理を実証しない | **real・採用** (§4 の禁止事項) |
| B-7 | pin 閉包不在は全称否定として強すぎる | **real・採用** (訂正 3)。親が探索範囲を拡張して実測したうえで、書き方を狭める |
| B-8 | 稼働 wave 不在も全称否定 | **real・採用** (訂正 3) |

## 7. 段 5 の分割

編集面は 1 script + 1 test file と小さく、所有は素集合に割れない。Codex 実装子 1 本
(`role=author`、`reasoning=xhigh`、`sandbox=workspace-write`) に両方を持たせる。
