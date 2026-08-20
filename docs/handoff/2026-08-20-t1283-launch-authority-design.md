# [T-1283] 受入receipt信頼境界・残余(i) 設計 wave
- 目的: D524が閉じなかった残余(i)「tip側待ち手が起動権を保持しlauncherを経由せず受領証を自作できる」を閉じる機構を設計のみ行う (実装しない)
- 状態: 作業中
- 最終更新: 2026-08-20
- 基準コミット: f78556cc68ccd62860d10b09b58ed445250ea386 (worktree: dev-wave-t1283-launch-authority-design)

## 完了した中間成果 (ファイルパス・コミットハッシュつき)
- 段1 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-launch-authority-design/stage1-brief.md`
- 段2 codex plan (rc=0, check_codex_output OK):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-launch-authority-design/stage2-plan-output.md`
- 段3 敵対相談2レンズ (rc=0, check_codex_output OK):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-launch-authority-design/stage3-lensA-output.md`
  (D403整合性・起動権実効性)、
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1283-launch-authority-design/stage3-lensB-output.md`
  (検証法健全性・D569整合性)
- 段4 裁定 (親): 計7所見中5件real。gate案は「残余(i)を閉じる設計」ではなく「narrow・条件付きの
  改善方向」として記録する裁定にした (詳細は decisions fragment 本文)。
- spool fragment (未 commit):
  `docs/spool/decisions/2026-08-20-dev-wave-t1283-launch-authority-design-1.md`
  ({{D:acceptance-gate-launch-authority-insight}})、
  `docs/spool/worklog/2026-08-20-dev-wave-t1283-launch-authority-design-2.md`
  (T-1283 更新)。`python3 tools/check_docs.py` = 違反なし (警告0件、本ファイル修正後)。

## 未完の作業と次の一手 (具体的に)
1. `git add -- docs/spool docs/handoff` → commit (AI-Agent trailer 付き、docs-only なので
   Codex author 不要)。
2. 段8: `docs/skill-self-improvement.md` の発火 gate・routing を適用 (候補があれば記録、
   なければ無言で通過)。
3. 段9: 受入全走が必須 (docs-onlyでも `--acceptance-receipt` は構造上必須、memory
   `zero-diff-wave-still-needs-acceptance-receipt` 参照)。
   `tools/dev_wave_wait.py acceptance` で lease claim → `python3 tools/run_tests.py` を
   背景実行 → receipt 取得 → `tools/dev_wave_land.py` で local main へ ff-only land
   (fold は land が lock 内で実行、wave 側では fold しない)。
4. land 成功後、受入 lease を release し、`tools/collect_wave_usage.py` を実行。

## 落とし穴・気づき (次のセッションが踏みそうなもの)
- **T-1373 は残余(i)の専任 ticket として既に存在し、本日 D569 (ユーザー裁定、(c)現状維持・
  新規実装なし) が下りている。** これを見落として「起動権を外に出す新機構」を無邪気に
  再提案すると D569 を無断で覆すことになる。
- **decisions.md の実際の D571 は本waveと無関係の別決定に既に使用済み。** spool fragment は
  `{{D:slug}}` placeholder で書き、fold が採番するため衝突しない (手で番号を書かない)。
- **decisions fragment 本文に有効な `[T-数字]` を角括弧付きで書いてはいけない**
  (`docs/spool/decisions/README.md` の D70 自己汚染回避規則)。worklog fragment 側は
  角括弧付き `[T-NNN]` が正しい書式 (次の一手の対象そのものであるため)。
- **段3 の2レンズが段2 plan の楽観的想定に real な欠陥を発見した** (gate自身のbootstrap
  例外がwave tip起動権を導入期間中に再導入する、completion protocolのpositive control
  主張が誤り)。これらを反映せず「gate案は残余を閉じる」と記録すると、次にこの記録を読む
  waveを誤導する — 段4裁定で「narrow・条件付き」の記録に修正済み。
