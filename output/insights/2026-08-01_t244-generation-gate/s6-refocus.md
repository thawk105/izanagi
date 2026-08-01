## 総括

**NO-GO。**

- FIX-3 が `AttributeError` 等の実装バグまで checkpoint 破損へ偽装する catch-all 回帰を開けた。
- A-06 は V10a を下限へ分離した一方、非 `int` gate の独立変異が改訂表から消えており partial。
- B-03 の docs はレビュー中に working tree へ追加されたが未 land。FIX-3 の実装とも不整合なので、まだ閉じていない。
- FIX-1・FIX-2・FIX-4・FIX-5 は、指定された攻撃に対して root cause を閉じている。

## 所見別 対応表

| 所見 | 状態 | 根拠 file:line | 残余 |
|---|---|---|---|
| A-01 | `closed` | [production:184](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:184)、[test:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:100) | `type(...) is int` で悪性サブクラスを `+` 実行前に拒否する。repo 内に `IntEnum` / NumPy 整数を渡す caller は無かった。 |
| A-02 | `out-of-scope-by-ruling` | freshness 読取 [production:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:196)、後続再読込 [production:500](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:500) | 両読込間に reservation/lock はなく TOCTOU は残る。裁定どおり実装対象外。 |
| A-03 | `closed` | production layout [production:658](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:658)、同じ導出式 [test:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:71)、実 state 負例 [test:335](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:335)、正規保存 [p3_s4_loop.py:407](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_s4_loop.py:407) | 名前空間の `A.` 修飾を除き、`run_root / "campaigns" / campaign_id(cfg)` が同一。`save_loop_state()` は `loop_state.json` を実際に書き、期待メッセージも固定している。F21 再演ではない。 |
| A-04 | `closed` | loop と planner 分岐 [production:683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:683)、呼出回数計測 [test:198](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:198)、assert [test:237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:237) | `break → continue` では別例外に落ちず、planner は generation 1・2・3 の計3回呼ばれる。 |
| A-05 | `closed` | 再照準テスト [test:486](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:486)、build 経路 [production:1054](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:1054) | validator 削除時は fixture gate に食われず `competing_bench_pids` poison へ到達する。 |
| A-06 | `partial` | 改訂表 [s6-fix-brief.md:105](/home/SFC/tanab/.claude/jobs/2ba05a50/tmp/t244-wave/s6-fix-brief.md:105)、残る `1.0` node [test:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:112) | V10a は下限、V10b は上限の等価変異へ分かれたが、元 V10 のもう一責務だった「非 `int` 拒否の弱体化」に対応する登録変異が消えた。`1.0` を受理させる独立変異を追加する必要がある。 |
| B-01 | `regressed` | catch-all [production:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:196)、report で外側型だけ保存 [production:958](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:958)、破損テスト [test:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:398) | JSON/schema/leak の素通しは閉じた。しかし loader 内の `AttributeError`・`AssertionError` 等まで `AutonomousTrialError` に偽装し、terminal report では cause が失われる。F37 同型の失敗分類握り潰し。 |
| B-02 | `closed` | A-05 と同じ [test:486](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:486) | 診断差だけの赤ではなく、validator 削除後の build-preparation 到達を poison が検出する。 |
| B-03 | `partial` | 段7担当の指定 [s6-fix-brief.md:122](/home/SFC/tanab/.claude/jobs/2ba05a50/tmp/t244-wave/s6-fix-brief.md:122)、未 land 草案 [decisions.md:5197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/docs/decisions.md:5197) | docs 草案は working tree に現れたが未 commit/land。D96 の同一変更単位、最終文言、docs 検査をまだ確認できない。さらに D112 決定5の限定表現と catch-all 実装が不一致。 |

## fix が開けた新しい穴

1. **FIX-1 — repo 内回帰なし。**  
   `IntEnum` と NumPy 整数は exact `int` でないため拒否されるが、repo 内 caller は対象テストだけで、実運用は [argparse `type=int`:1044](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:1044) だった。これは意図した契約縮小。ただし外部 programmatic caller への互換性変更である。

   判定順は型 → 絶対範囲 → 承認上限で正しい。bool・非 int・0・11 は従来どおり「1..10 必須」、2..10 は「承認済み上限」となり、既存 `match=` に変化はない。

2. **FIX-3 — blocking な新規穴あり。**  
   `except Exception` は checkpoint データ由来の例外に限定されない。`load_loop_state()` のプログラミングエラーも checkpoint 破損として報告される。専用 loader 例外を導入してそれだけ捕捉するか、少なくとも期待する入力例外へ限定し、`AttributeError` が再分類されない負例が必要。

   一方、except 節は必ず `raise` するため `state` 未定義のまま後続へ進む経路はない。壊れた state を `None` として fresh 扱いする経路もない。

3. **FIX-2 — 新しい穴なし。**  
   helper と production は同じ workload/config/trial/generation から同じ campaign ID を作り、同じ no-build layout を参照する。正規保存は [p3_s4_loop.py:412](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_s4_loop.py:412) で directory を作り、415–417行で JSON を書いて `os.replace` している。負例は `match="既存 campaign state"` なので別理由の例外では通らない。

4. **FIX-5 — 新しい穴なし。**  
   `continue` mutant では invalid planner を記録して次世代へ進み、世代別 raw/journal path も衝突しないため3回呼ばれる。なお mutant の最初の失敗は `planner.calls` assert より前の `len(cell["generations"]) == 1` になるが、これは別例外ではなく3世代を実行した直接結果である。

5. **FIX-4 — 新しい穴なし。**  
   validator 削除時の順序は `argparse` → 正当な `claude-headless` build 分岐 → `competing_bench_pids` poison。provider 生成は [run_trial:921](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:921) 以後なので到達しない。Claude subprocess、provider artifact、checkout の副作用は発生しない。

6. **変異表 — 非 `int` gate の証拠が脱落。**  
   `1.0` を受理させる単独変異と、その期待 node `[1.0]` を改訂表へ戻す必要がある。

## land 前に必ず docs へ書くべきこと

- exact built-in `int` のみを受理し、`IntEnum`・NumPy 整数・全 `int` サブクラスも拒否する API 互換性変更。
- 受理値は現在 `1` のみ。2..10 は未承認、範囲外・bool・非 int は契約違反。CLI default 1 は承認上限定数と意図的に非連動。
- freshness 対象は `loop_state.json` のみ。lock・WAL・provenance 残骸は対象外。
- no-build/build の layout 分離、workload 別 identity、新 trial ID が crash recovery 境界であること。
- stale な1 workload が `supervisor-error` となり、後続 workload も停止すること。
- `drive/providers/preview` 注入、driver 直接反復、TOCTOU race は保証対象外で、T-244 本体は未解決。
- default 変更が campaign ID/root、journal/report budget、候補集合を変えること。
- D106 supersede と全境界テストを実装と同じ commit に含めること。
- FIX-3 を狭めるまでは「読取・decode・schema 失敗だけを包む」と書かないこと。catch-all を文書化するのではなく実装を直すべきである。

## 確認できなかったこと

- pytest と mutation harness は実行していない。親の **24 passed** は前提として採用しただけで、独立再走ではない。
- V1・V12・非 `int` 変異の判定は静的制御フローによる。実測 mutation 台帳は未確認。
- repo 外の programmatic caller が `IntEnum` / NumPy 整数を使用していないことは確認できない。
- TOCTOU の並行再現と、worktree 外・他ホストの checkpoint/artifact は確認していない。
- docs はレビュー途中に並行して追加された未コミット差分であり、最終文言・同一 commit 化・`check_docs.py` は未確認。
- 実施した静的検査は `git diff --check` の `rc=0` のみ。