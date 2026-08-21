# [T-1469] 受入lease staleness の事後定量化

- 目的: 「claim前にmerge・受入テストを済ませていたら実際にどれくらいの頻度でmain advanceにより
  無駄になっていたか」を既存記録の事後解析で定量化し、D631 が残した実測ギャップを埋める。
  `output/insights/2026-08-21_t1469-acceptance-lease-timing/README.md` に記録する。
- 状態: 作業中
- 最終更新: 2026-08-21 (段7 fragment作成・dry-run検証済み、段9受入前)
- 基準コミット: 46fbce3d (worktree: dev-wave-t1469-acceptance-lease-timing, 作業ツリー dirty:
  insight README + spool fragment 2本 + 本handoff、未commit)

## stage1 brief

**scope:** 事後解析のみ。新規lease claim・新規acceptance投入・production code変更をしない。
実装面ゼロ (docs-only)、D95によりCodex子は不要 (子ゼロで可)。

**確定済みユーザー裁定:** command引数がそのまま裁定。資料はarchive worklog-0821-793、
T-870 insight、D631/D270、canonical worklog。「同じ手法」= T-870 の事後解析手法
(新規投入せず既存artifactのmtime/ログを読む) を踏襲する、の指示と解釈 (P1)。

**不変条件:**
- 新規測定・productionコード変更・既存値の推測をしない。
- 一次資料 file:line を全数値に付す。
- Rule2 (正しさゲートを緩めない): 結論は「data」であり「D631/D239を緩めよ」という推奨をしない。

**母数と判定規則 (P1、段4で確定):**
- 母数候補: `/work/1/SFC/tanab/dev-wave-jobs/*/acceptance-run.pid` を持つ11 wave
  (T-870と同じartifact系列。`acceptance-child-*.log`のみ持つ323件は claim試行開始timeが
  無く対象外 — 選定バイアスとして限界節に明記)。
- 測定量: T0=`acceptance-run.pid` mtime (claim試行開始)、T1=claim成立時刻
  (PBS submit時刻 or `acceptance-run.done`/`land.pid` mtime)。
- stale判定規則 (P1): `[T0,T1]`区間内に他waveのland commitが1本でもmainへ乗っていれば stale。
  根拠: D270提案は「claim後はfast-forward+再確認だけ」を前提とし、区間内の他land 1本でも
  そのFF前提が崩れ再merge・再受入が要る。
- Δcommits・Δt_waitは`git log`のcommitter dateで既存historyから算出 (新規測定でなく既存値の集計)。

**成果物の形:** insight README 1本 (対象母数・stale判定規則・経過時間分布・
claim-before-mergeとacceptanceの関係・解釈上の限界・一次資料file:line)。
worklog/decisions fragment (spool形式)、本handoff (正常終了時にworklogへ吸収し削除)。

**並列分割方針:** なし。単独 (docs-only、Codex子ゼロ)。

## 完了した中間成果 (ファイルパス)
- `output/insights/2026-08-21_t1469-acceptance-lease-timing/README.md`: clean母数n=7
  (11候補中、複数試行4件を除外)、stale率6/7(85.7%)、Δt_wait中央値2530s、
  claim-before-mergeの現行実装確認、限界8点、file:line一次資料。
- `docs/spool/decisions/2026-08-21-dev-wave-t1469-acceptance-lease-timing-1.md`:
  {{D:lease-preclaim-staleness-evidence}} (D631再訪不成立を記録)。
- `docs/spool/worklog/2026-08-21-dev-wave-t1469-acceptance-lease-timing-1.md`:
  [T-1469] 完了 (remaining: none、base digest確認済み)。
- `python3 tools/check_docs.py` = 違反なし (警告3件は他waveのhandoffも含む既知の
  header書式ドリフトで本waveのregressionではない)。
- `python3 tools/spool_fold.py --dry-run --show-diff` = 成功 (D640割当て見込み、
  他waveの並行landでずれうるため確定値として扱わない)。

## 未完の作業と次の一手
1. 本commit (insight + spool fragment 2本 + handoff更新、AI-Agent trailer付き)。
2. 段9: `tools/dev_wave_wait.py acceptance` でlease claim → `python3 tools/run_tests.py`
   受入全走 (背景実行、docs-onlyでも受入は免除されない、DW-S04)。
3. `tools/dev_wave_land.py` でlocal main へland (ff-only、fold実行)。
4. land成功後にlease release、peer通知、`tools/collect_wave_usage.py`
   (loginでblockされる既知事象、実施記録のみ)。
5. 正常終了時に本handoffをworklogへ吸収し削除。

## 落とし穴・気づき
- 当初`git log --since/--until`のcommitter dateで「main advance」を検出しようとしたが、
  wave branch上のcommitはcommitter dateが「commit作成時刻」であり「main反映(land)時刻」と
  一致しない場合があると判明 (T-1434のpre-claim main取り込みcommitが別waveの待ち区間に
  紛れ込む等)。`git reflog show main`(mainブランチ自身へのref更新だけを記録) に切り替えて
  解消した。reflogは既定でexpireするため、本insightの追試は保持期間内に限られる (insight 5節-4)。
- 複数試行 (retry) waveでは `acceptance-run.pid` の単一mtimeがどの試行に対応するか、
  ファイルmtimeの前後関係だけからは一意に決まらないケースがあった
  (`dev-wave-t1444-pegasus-env-tag`: pidがattempt-7受理後・attempt-8開始前に位置)。
  T-870の3サンプルは偶然すべて単一試行だったため、この曖昧さに遭遇していなかった。
- dev-wave改善候補: 実測なし (**候補ゼロ**)。DW-C00軽量既定の適用・母数選定・reflog切替は
  いずれも本wave固有の分析判断であり、`docs/dev-wave/*.md`の手順自体に欠落・無駄・曖昧は
  見つからなかった。`docs/skill-self-improvement.md`の発火gate・routingは通読済み。
  reflogの知見はdev-wave手順でなく手元memory (`acceptance-lease-contract.md`等) への
  追記候補として段9後に別途検討する。
