## B1

主張: help 文言を末尾へ移す修正は妥当だが、新語句を独立した短い chunk にしなければ折返し安全性は保証できない。

根拠: 現在は新語句が先頭に追加され、後続の折返し位置を変えている [dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/dev_wave_codex.py:94)。`_help_option_block` は改行を空白へ変えるため、`--max-wall- clock-s` を元へ戻せない [test_dev_wave_codex.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_dev_wave_codex.py:76)。argparse は既定の `textwrap.wrap` を使い [/usr/lib/python3.10/argparse.py](/usr/lib/python3.10/argparse.py:661)、textwrap は空白とハイフンだけでなく、`break_long_words=True` により長い chunk を任意位置でも分割する [/usr/lib/python3.10/textwrap.py](/usr/lib/python3.10/textwrap.py:200)。

具体的な失敗シナリオ: 単に末尾へ連結して新語句を直前の日本語と同じ chunk にすると、狭い幅では新語句自身や直前の既存 assertion 対象へ空白が挿入される。次の形なら旧文面を完全な前方 prefix として維持し、新語句を幅 15 の独立 chunk にできる。

```python
"--max-wall-clock-s が 90 未満ならそれに切り下げる "
"(子の起動完了時を起点とする)"
```

textwrap は前方から貪欲に処理して後続 chunk を先読みしないため、同じ表示幅なら既存の `90 秒を上限`、`受理集合に影響する`、`暫定運用値であり測定された最小値ではない`、末尾の `--max-wall-clock-s...` の折返しは従来位置を保つ。新語句も現行幅では一単位で次行へ送られる。既存期待値の変更は不要である。

重大度・成果物影響: must-fix — 現在の唯一の受入赤を残し、段 6 の land を阻害する。production の受理集合には影響しない。

## B2

主張: 変異事前登録の期待 node 完全集合は M1、M2、M5 で不足しており、特に M5 は指名 node より先に別 node が赤になる。

根拠: 表は M1/M2 に単一の「新設 spawn 起点判別テスト」、M5 に既存 exact-duration node だけを指定している [adjudication.md](</home/SFC/tanab/.claude/jobs/a7e13b47/tmp/wave-t1312/adjudication.md:104>)。一方、attempt 1 と retry の両 node は同じ exact `supervision_drain == 0.05` を検査し [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:3559)、診断なし node も同じ時計で poll 数 5 を固定する [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:4271)。DW-M08 は記録 node との完全一致を要求する [mutation.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/docs/dev-wave/mutation.md:54)。

具体的な失敗シナリオ: 静的に得られる期待完全集合は次のとおり。

- M1、M2: `test_evidence_grace_starts_at_spawn_completed`、`test_evidence_grace_starts_at_spawn_completed_on_retry`、`test_evidence_deadline_origin_is_diagnostics_independent`
- M3: `test_evidence_deadline_origin_is_diagnostics_independent` のみ
- M4: `test_evidence_grace_starts_at_spawn_completed_on_retry` のみ
- M5: 上記 spawn 起点 node 2 本と `test_launcher_diagnostics_production_phase_wiring_has_exact_durations`

M5 で別サンプルを取ると診断境界と deadline の差が 1 poll 分ずれ、前二者の `0.05` が `0.04` または `0.06` になる。これらはファイル上も既存 exact-duration node [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:4440) より先に実行される。

重大度・成果物影響: must-fix — mutation spec が現状の表どおりなら、正しく殺した変異を期待集合不一致で fail-close するか、検出力の帰属を誤った変異台帳を作る。

## 独立確認

- `_base_command` は module-local helperで、54 箇所の直接呼出しはすべて位置引数が `tmp_path` だけだった。43 箇所の `_run_case` callerも `**kwargs` で転送する [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:1543)。新設2本だけが `0.05`、既存3本だけが `0.3`、残りは `1.0` の既定を使う。parametrize 7 経路と autouse fixtureにも再束縛はない。実装報告の機能的結論と一致するが、「fixture」という呼称だけは不正確である。
- receipt は schema version 3 [codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:2191)、sidecar は v1 [codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/tools/codex_worker_launch.py:2781) のまま。production diff は時刻サンプルと deadline 起点だけで、field 集合の増減はない。
- `grep -rln` から絞った結果、新 node 名を pin する別ファイルはなく、plain-runner は test file を動的列挙する [test_plain_runner_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_plain_runner_coverage.py:44)。既存ファイルの自走 harnessも全 node を pytest 収集する [test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/orchestrator/tests/test_codex_worker_launch.py:6373)。growth-hold は登録済み key のみを pin しており、新 node の追加対象ではない。
- active docs の該当箇所は、過去の故障機序を記録する F57 [failures.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/docs/failures.md:2125) と新起点を定める D498 [decisions.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1312-evidence-grace-origin/docs/decisions.md:20673) だけだった。旧起点を現行仕様として述べる残存説明も、`docs/dev-wave/**` への追記を要する裁定候補も見つからなかった。
- pytest、変異 harness は実走していない。上記 mutation node 集合は静的帰属である。

## 総括

must-fix は help 折返しと mutation期待 node 完全集合の2件。
help は旧文面を prefix のまま保ち、新語句を末尾の独立 chunk にするのが最小かつ安全。
schema、caller、meta-test、active docs に追加の閉包漏れは見つからなかった。
親による修正後の焦点再走と mutation実測が必要である。