## M1: `.py` への欠陥再導入

- 所見: 机上適用時の失敗 node 完全集合は裁定どおり `POS`, `NEG`。`POS` は `.pbs` と `.py` の不一致で例外になり、`NEG` は `.py` 同士が一致して期待した例外が発生しない。
- real か refuted か: refuted
- 根拠 file:line: [s4-adjudication.md:119](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:119)、[test_t316_sandbox_probe.py:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1436)、[test_t316_sandbox_probe.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1526)、[test_t316_sandbox_probe.py:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1545)
- 成果物影響: 裁定の mutation ledger、検出 node 集合、帰属はいずれも変更不要。
- 提案: 事前登録どおり `KILLED`, `{POS, NEG}` とする。

## M2: `condition_meaning_gate.py` への取り違え

- 所見: 机上適用時の失敗 node 完全集合は裁定どおり `POS` のみ。`NEG` でも比較は不一致になるが、期待する同一文言の `ValueError` が発生するため、その node は失敗しない。
- real か refuted か: refuted
- 根拠 file:line: [s4-adjudication.md:120](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:120)、[test_t316_sandbox_probe.py:1437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1437)、[test_t316_sandbox_probe.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1450)、[t316_sandbox_backend_probe.py:2338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2338)
- 成果物影響: `POS` が比較対象の正しさを単独で識別し、受理集合の誤った記録を防ぐ。
- 提案: 事前登録どおり `KILLED`, `{POS}` とする。

## M3: 比較条件の無効化

- 所見: `if False:` では `POS` は後続 hash 検査を満たす一方、`NEG` は期待した例外が発生せず失敗する。期待集合は裁定どおり `NEG` のみ。
- real か refuted か: refuted
- 根拠 file:line: [s4-adjudication.md:121](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:121)、[t316_sandbox_backend_probe.py:2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2339)、[test_t316_sandbox_probe.py:1552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1552)
- 成果物影響: 比較行が消えた受理集合の拡大を `NEG` が検出する。
- 提案: 事前登録どおり `KILLED`, `{NEG}` とする。

## M4: 例外文言の変更

- 所見: `POS` は影響を受けず、`NEG` だけが完全一致 regex を満たさない。期待集合は裁定どおり `NEG` のみで、受理集合ではなく診断感度の pin である。
- real か refuted か: refuted
- 根拠 file:line: [s4-adjudication.md:122](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:122)、[t316_sandbox_backend_probe.py:2340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2340)、[test_t316_sandbox_probe.py:1553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1553)
- 成果物影響: 受理集合は不変だが、利用者と台帳が観測する診断契約の変更を検出する。
- 提案: `KILLED` と記録しつつ、裁定どおり diagnostic sensitivity pin と明記する。

## M5: spool hash の引数変更

- 所見: 比較通過後は両 path の SHA-256 が同値なので、`runtime_pbs` と `repo_pbs` のどちらを再計算しても返却値は同じ。`POS`, `NEG` とも観測差がなく、期待 node は空集合。
- real か refuted か: refuted
- 根拠 file:line: [s4-adjudication.md:123](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:123)、[t316_sandbox_backend_probe.py:2339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2339)、[t316_sandbox_backend_probe.py:2344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2344)
- 成果物影響: receipt の `runtime_pbs_spool` 値と受理集合に変化はない。
- 提案: 事前登録どおり等価変異 `SURVIVED`, 空集合とする。

## 単一理由性と過剰決定

- 所見: M1〜M4 の各失敗理由は対象変異に一意に帰属できる。job id、root、hostname、nodefile、commit、dirty の先行関門は helper が満たすよう構成され、同じ入力を重ねて拒否しない。環境不成立時は base 自体が失敗するため mutation 固有の過剰決定ではない。
- real か refuted か: refuted
- 根拠 file:line: [test_t316_sandbox_probe.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1425)、[test_t316_sandbox_probe.py:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1493)、[test_t316_sandbox_probe.py:1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1519)、[t316_sandbox_backend_probe.py:2306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2306)
- 成果物影響: mutation ledger の kill 理由を対象比較へ一意に帰属できる。
- 提案: DW-M01/M03 の単一理由性を充足として扱う。

## [恒真ゲート]

- 所見: 追加 2 test が `_execution_binding` を通らずに成功する経路はない。helper の `git` 不在、dirty、path 配置などの assert が先に失敗する条件は構成できるが、いずれも test 自体の失敗になる。`NEG` の `raises` 節にも helper は含まれない。
- real か refuted か: refuted
- 根拠 file:line: [test_t316_sandbox_probe.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1430)、[test_t316_sandbox_probe.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1513)、[test_t316_sandbox_probe.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1533)、[test_t316_sandbox_probe.py:1553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1553)
- 成果物影響: helper の早期失敗が比較実装を未実行のまま成功扱いにし、受理集合を偽装することはない。
- 提案: 変更不要。

## fixture の脆さ

- 所見: 指定された条件はいずれも refuted。hostname は明示 monkeypatch、runtime と nodefile は解決済みの sibling、root は環境と引数で同一 object、SHA-1 は `GIT_DEFAULT_HASH` で固定される。Git の global/system config と template は隔離され、警告は capture される。同一 process が新規作成する repo なので通常の `safe.directory` 所有権制約にも抵触しない。`Path.is_relative_to` は対象 probe が宣言する Python 3.10 で利用可能であり、古い非対応 Python では早期失敗しても偽成功にはならない。
- real か refuted か: refuted
- 根拠 file:line: [t316_sandbox_backend_probe.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:1)、[test_t316_sandbox_probe.py:1426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1426)、[test_t316_sandbox_probe.py:1428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1428)、[test_t316_sandbox_probe.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1432)、[test_t316_sandbox_probe.py:1452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1452)、[test_t316_sandbox_probe.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1513)
- 成果物影響: 列挙された環境差によって mutation matrix や受理 node が誤って変化する経路は認められない。
- 提案: 変更不要。

## 揮発 payload の焼き込み

- 所見: 実 working tree bytes、実 hostname、実 job id、実行時刻は期待値に焼き込まれていない。fixture bytes、hostname、job id は固定値で、期待 digest は fixture `.pbs` から算出される。commit ID は commit 時刻により変動し得るが、その場で得た HEAD を先行 commit 関門へ渡す setup 値であり、固定 oracle や成果物期待値ではない。
- real か refuted か: refuted
- 根拠 file:line: [test_t316_sandbox_probe.py:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1436)、[test_t316_sandbox_probe.py:1486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1486)、[test_t316_sandbox_probe.py:1516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1516)、[test_t316_sandbox_probe.py:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1536)
- 成果物影響: test 期待値が別 worktree、job、host、時刻へ陳腐化して誤拒否する問題はない。
- 提案: 変更不要。

## 規律 2

- 所見: 正しさゲートの緩和なし。tuple は従来と同じ 5 値・同順序で、`runtime_sha256` はその 5 key と `runtime_pbs_spool` の計 6 key。例外文言、job id、commit、root、login node、nodefile、dirty の関門と順序も不変。実装差分は比較先だけを名前付き `.pbs` 定数へ修正している。
- real か refuted か: refuted
- 根拠 file:line: [s5-impl.diff:184](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:184)、[t316_sandbox_backend_probe.py:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290)、[t316_sandbox_backend_probe.py:2306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2306)、[t316_sandbox_backend_probe.py:2340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2340)、[t316_sandbox_backend_probe.py:2341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2341)
- 成果物影響: 既存 receipt schema、hash key 集合、診断、先行拒否集合は変わらず、正しい `.pbs` spool のみ比較結果が訂正される。
- 提案: 変更不要。

## scope 外の既知所見

- 所見: `condition_meaning_gate` は module import 時に読み込まれ、5 path の Python dirty 検査より前にコードを実行し得る。これは real だが、今回の差分による緩和ではなく段 4 で既に裁定された scope 外の既知事項。
- real か refuted か: real、scope 外、既知
- 根拠 file:line: [s4-adjudication.md:19](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:19)、[t316_sandbox_backend_probe.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:36)、[t316_sandbox_backend_probe.py:2331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2331)
- 成果物影響: dirty な condition gate の import-time 動作が、束縛拒否より前に実行へ影響する余地を残す。
- 提案: 段 4 の裁定候補として維持し、本 wave では実装しない。

## [テスト代表性]

- 所見: 追加 test は実 Git repo を使って `_execution_binding` の Python preflight を直接検査するが、計算ノード上の PBS spool 統合や実行命令列の同一性は代表しない。この制限は real だが、段 4 裁定と実装子報告ですでに明記されている。
- real か refuted か: real、既知の代表性限界
- 根拠 file:line: [s4-adjudication.md:9](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:9)、[s4-adjudication.md:14](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s4-adjudication.md:14)、[test_t316_sandbox_probe.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1533)、[s5b-author-out.md:24](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:24)
- 成果物影響: 単体 test の結果を PBS 統合 certification と誤読すると、実 spool 起動まで証明済みという過大な参照が生じる。
- 提案: 現行どおり保証を「Python preflight 時点の spool と worktree `.pbs` の digest 一致」までに限定する。追加 gate は提案しない。

## 実装子報告と [捏造/幻覚]

- 所見: 報告との静的不一致なし。tuple の値・順序、例外文言、6 hash key は現物と一致し、逐語差分の対象も 2 file のみ。test 定義と全 parametrize の静的展開は既存 127 nodeに追加 2 nodeで計129 nodeとなる。ただし成功 status は実装子の実走報告であり、この read-only review では再実走していないため独立追認はしない。
- real か refuted か: refuted
- 根拠 file:line: [s5b-author-out.md:7](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:7)、[s5b-author-out.md:9](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:9)、[s5b-author-out.md:15](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5b-author-out.md:15)、[s5-impl.diff:1](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:1)、[s5-impl.diff:176](/home/SFC/tanab/.claude/jobs/2b56bf14/tmp/dw/t2503-pbs-binding/s5-impl.diff:176)、[test_t316_sandbox_probe.py:1566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1566)
- 成果物影響: 実装報告と現物の構造・node 数に食い違いはない。親は成功 status を「実装子報告」と「段 6 で独立再走した結果」に分けて扱う必要がある。
- 提案: 捏造または幻覚所見にはしない。段 6 が実走する場合だけ、その結果を独立した検査結果として記録する。

## 総括

M1〜M5 の期待 node 完全集合はすべて段 4 裁定と一致し、単一理由性、恒真回避、fixture 隔離、規律 2 に新規の real 所見はない。real 所見は既知の 2 点、すなわち PBS 統合を代表しない単体 test の限界と、scope 外として既に裁定済みの import-before-dirty 問題のみ。pytest、変異 matrix、編集、commit は実施していない。