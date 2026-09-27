## 所見

- **A1 — must-fix — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:20)、[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:1458)。** 正例は実際の builder を呼ばない計画なので、「builder が実 repo から直接複製する」変異は対象行を実行せず、殺せない。**修正案:** 小さい repo を使い、実際の builder の複製分岐を通す正例にする。重い後続処理だけを局所的に止め、複製元と結果を検査する。

- **A2 — must-fix — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:5)、[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2979)。** worker の process 環境変数は subprocess に継承される。入れ子の pytest や別 session がその値を残したまま builder を使うと、終了済みの写しを待つ、または親 session の写しを使う。既存コードには `pytest.main()` 再入への対応もある。**修正案:** worker の config に path を保持し、collection 済みの対象 module へ session 限定で渡す。環境変数を使う場合も、新 session の configure 時に継承値を退避・消去し、当該 workerinput がある場合だけ設定して終了時に復元する。

- **A3 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:15)、[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:847)。** 写しの時点を変えると、後から追加・削除された未 commit 可視 file、bytes、mode、mtime が fixture に反映されなくなる。これは受理**規則**を保っても、その session の受理**結果**を変えうる。除外規則と symlink の扱いは実関数の一回目で維持され、通常の `copytree` は file と directory の mode・mtime を複製する。**修正案:** 「受理集合は変えない」という保証を撤回し、時点差を明示的な意味の変更として裁定・受入条件に反映する。

- **A4 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:3)、[probe-source.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/output/insights/2026-09-26/t2273-shard0-precopy-ab/verbatim/probe-source.md:1237)。** probe は `tryfirst=True` の hook で写し thread を起こす。plan は通常順序の conftest hook で早期 memo 起動**後**に起こすため、写しの開始時点が P より遅れうる。背景 thread 内 import の所要も写し開始までの時間に含まれる。**修正案:** 実装の発火順序を probe と揃え、thread 起動時刻から実関数開始までを実受入で確認する。

- **A5 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:4)、[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/conftest.py:2964)。** 180 秒は worker の待ちだけを縛る。I/O が止まった非 daemon thread を無期限に `join()` すれば controller は終了できない。thread 起動前後や marker 書込みの例外時にも片付けを通す必要がある。**修正案:** worker 終了後に join、削除する順序を保ちつつ、join が終わらない場合の有界な終了動作と残存写しの扱いを定める。

- **A6 — should — [s2-plan-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s2-plan-out.md:9)、[test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy/orchestrator/tests/test_s8b_oracle_driver.py:61)。** 対象には `__init__.py` がなく、pytest が使う module 名と指定した package 名の一致は静的には確定しない。controller は別 process なので名前の相違だけで二重 import とは限らないが、import は `sys.path` を変更し、temp root 検査と依存 module import を実行する。主 thread の memo 準備との競合も未確認。**修正案:** 焦点走で実際の module 名、controller の run ID、import 開始・終了時刻を確認する。

## plan への修正案

正例を実 builder の複製分岐へ接続し、環境変数の session 漏れを防ぐ。発火順序を probe と合わせ、時点差を意味の変更として記述する。生成失敗・待ち超過を赤にする方針は測定条件を混ぜない点で妥当だが、失敗走を有効な性能対として数えず、条件別に記録する。180 秒は同じ計算ノード regime で観測した最大待ち 27.1 秒に対して余裕がある一方、controller の join 上限の根拠にはならない。3 shard すべてで作る追加 I/O は replica で未測定なので、実受入の W₁・W₂・Wmax で判定する。

## brief の誤り

[P7] の「受理集合は変えない」は、可視 file の増減や内容変更がある session では成立しない。[P8] の検査項目だけでは builder 統合経路を固定できない。[P5] の 180 秒は worker 待ちの根拠であり、終了処理全体の上限ではない。

## GO 判定

**修正後 GO** — 実 builder を通す正例、session を越える path 継承の遮断、probe と同じ発火順序を先に確定する。

## 総括

静的検査のみ実施し、test は実走していない。実関数による可視性と除外処理は維持できるが、写しの時点変更には実際の fixture 内容を変える経路がある。現 plan の正例では最重要の直接複製変異を検出できない。効果と赤率は実受入の隣接対で判断する必要がある。