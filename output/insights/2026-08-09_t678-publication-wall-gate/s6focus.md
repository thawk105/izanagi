## 判定前提

テストは実走していません。親実測の `77 passed` は前提事実として使用しました。MT1〜MT5 は以下すべて静的予測です。

## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| R2 MF-1 — N3 の検出力 | **closed** | wrapper は全 `_write_json_temp` 呼出しを元実装へ委譲し、destination が receipt path と一致する場合だけ記録します（[test_codex_worker_launch.py:2160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2160)）。manifest 等の別 path は数えず、receipt staging は必ず同 helper を通ります（[codex_worker_launch.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:372)、[codex_worker_launch.py:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1647)）。変更前 production は staging で temp を作って削除し、publication helper が再度 temp を作る構造でした（[s5-integrated.patch:156](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s5-integrated.patch:156)、[s5-integrated.patch:281](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s5-integrated.patch:281)）。したがって変更前／MT2 では `AttributeError` ではなく、まず `len(...) == 1` が実数 `2` で落ち、続行すれば final inode も最初の staged inode と不一致になります（[test_codex_worker_launch.py:2178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2178)）。 |
| R1 nit 1 — 例外時の temp 所有契約 | **closed** | 注入条件は `destination == paths["receipt"]` の最初の `os.link` に限定され、それ以外は元の `os.link` へ委譲されます（[test_codex_worker_launch.py:2192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2192)）。最初の例外は production helper 内で発生し、helper の `finally` が所有済み temp を unlink します（[codex_worker_launch.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:459)）。caller は呼出し前に所有権を移しているため、その temp を別経路では消せません（[codex_worker_launch.py:1813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:1813)）。二度目の receipt link、`launcher_error`、rc=2、output 不在、temp 残骸なしを検査しており、恒真ではありません（[test_codex_worker_launch.py:2205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2205)）。注入が receipt publication に当たらなければ rc=0 となり、期待 rc=2 で先に失敗します。 |

## 回帰確認

**回帰は認めません。**

- fix 差分はテストファイルだけで、production への追加変更はありません（[s6-final.patch:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s6-final.patch:1)、[s6fix.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s6fix.md:3)）。したがって production の fail-open 緩和はありません。
- publication failure の outcome、rc、output 不在の既存期待値は維持され、temp 不在が追加されています（[test_codex_worker_launch.py:2206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2206)）。
- fix 前 N3 の helper 引数に対する Path/inode assert は形式上削除されています（[s5-integrated.patch:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t678-publication-wall-gate/s5-integrated.patch:122)）。ただしこれは MF-1 の原因だった signature 依存観測器の置換であり、receipt temp 作成回数、final inode、temp 消滅へ置き換わっています（[test_codex_worker_launch.py:2178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2178)）。MT2 に対する検出力は緩んでいません。
- skip／xfail の追加はありません。外側 timeout は 10 秒のままです（[test_codex_worker_launch.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:542)、[test_codex_worker_launch.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:563)）。4 秒は論理時計 offset で、時間予算拡大ではありません（[test_codex_worker_launch.py:2087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2087)）。

## MT1〜MT5 の予測

| 変異 | 赤になる予測 node | 意味のある赤理由 | 予測 |
|---|---|---|---|
| MT1 — staging 後 late latch 削除 | N1、N2 | staging／published audit で論理時計が超過しても accepted・rc=0 のままとなり、両 node の期待 rc=1 が失敗します（[test_codex_worker_launch.py:2101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2101)、[test_codex_worker_launch.py:2140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2140)）。 | KILLED |
| MT2 — staged temp を捨て、publication 時に新 temp を書く | N3 | wrapper は staging temp を削除前に記録でき、publication temp も二件目として記録します。`len == 1` が `2` で失敗し、final inode も最初の inode と異なります。`None.stat()`／`AttributeError` には依存しません（[test_codex_worker_launch.py:2163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2163)、[test_codex_worker_launch.py:2179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2179)）。 | **KILLED（意味あり）** |
| MT3 — flip 時 output unlink 削除 | N1、N2 | receipt は not_accepted／rc=1 になりますが、公開済み output が残り、output 不在 assert が失敗します（[test_codex_worker_launch.py:2112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2112)、[test_codex_worker_launch.py:2151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2151)）。親事前登録の「N1 のみ」より実際の予測 node は一つ多いです。 | KILLED |
| MT4 — flip 後の receipt 再構築を省略 | N1、N2 | staged accepted bytes と rc=0 が残り、両 node の期待 rc=1 が最初に失敗します。 | KILLED |
| MT5 — latch を常時超過扱い | N4、N3、および既存 accepted 群 | 正常 job が not_accepted／rc=1／output 不在へ過剰拒否され、N4 の accepted／completed／rc=0／output 実在が失敗します（[test_codex_worker_launch.py:1630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:1630)）。 | KILLED |

SURVIVED になりそうな事前登録変異はありません。MT2 は正常入力における receipt／output／rc 自体ではなく、exact-temp reuse の構造契約を検出する node ですが、その赤理由は観測器例外ではなく回数・inode 不一致です。

## 総括

- 残 must-fix: **0件**
- R2 MF-1: **closed**
- R1 nit 1: **closed**
- fix 起因の fail-open、時間予算拡大、skip／xfail、既存成果物 assert の緩和なし
- MT1〜MT5 は全件 KILLED 予測、SURVIVED 予測なし
- MT3 の予測赤 node は事前登録の N1 だけでなく N2 も含む
- 親実測 `77 passed` は前提として採用。変異結果は未実測
- 判定: **条件付き GO**（条件は MT1〜MT5 の実走が上記予測と整合すること）