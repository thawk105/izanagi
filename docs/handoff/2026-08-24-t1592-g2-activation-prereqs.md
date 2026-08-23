# [T-1592] 環境世代 g1→g2 activation 前提条件表
- 目的: activation の必要条件・現在値・証拠・未充足理由・所有者を実測し、活性化せず canonical docs に一覧化する
- 状態: 作業中
- 最終更新: 2026-08-24
- 基準コミット: 768e9fe62e6fecd50280bd95771159947e08c4d8 (worktree: dev-wave-t1592-g2-activation-prereqs)

## 完了した中間成果   (ファイルパス・コミットハッシュつき)

- クラス 3 起動手順、dev-wave dispatcher、`DW-O08`、D431/D437、worklog entry 874 の
  [T-1166]/[T-1488]/[T-1592]、裁定済み T-1488 一次控えを再読した。
- 専用 worktree を local main HEAD から作成し、`tools/dev_wave_submodule_init.py` で submodule を
  再帰初期化した。main checkout は編集していない。
- calibration-registration worktree は main に完全吸収済みと実測した。floor-restart worktree は
  2026-08-24T01:17:41+09:00 観測で branch tip `12c41c8851c3fe90307bdc31b1d55892cc394ea9`、
  受入走行中、作業 tree clean、main 未land だった。本 wave は同 branch が変更した
  `docs/phase3-8b-restart-runbook.md` を触らず、独立した activation readiness index へ置いた。
- 段 2 plan は新規 `docs/env-contract-activation-prerequisites.md` を支持したが、段 3 が
  prospective record の過大評価、段 0 開始順の循環、D716 に無い追加解禁、paired freeze readiness の
  証拠不足を real と判定した。段 4 で全件を採用し plan v2 を固定した。
- plan v2 に従い readiness index と docs map を作成した。activation・上位束・freeze・holdout・
  registry の実体は変更していない。
- 段 6 review の real finding を全修正し、焦点 review は 7/7 closed。焦点テストは
  696 passed / 3 skipped、`check_codex_agents.py` 成功、`check_docs.py` 違反なし。
- 起動時 base の全走は real-corpus digest 1 件だけ赤だったが、並行で進んだ local main では同 nodeid が
  1 passed。stale-base 赤として main 取込み後の正式受入へ送る。

## 未完の作業と次の一手 (具体的に)

1. docs commit を作り、進んだ local main を merge して正式受入を行う。
2. 段 8 自己改善を一度だけ裁定し、段 9 local main land を行う。

## 落とし穴・気づき    (次のセッションが踏みそうなもの)

- activation record の発行、reviewed head 更新、上位束 A/X、holdout 解禁、rr80/rr20 bytes 登録は scope 外。
- `docs/calibration-freeze-authority-bundle-design.md` は上位束の設計正本である。readiness index は
  状態を日付・commit 付き snapshot として転載するが authority にはせず、各正本へ pointer を張る。

## dev-wave 改善候補

1. 段 2 初回 job は prompt に「予算が尽きそうなら途中結論を出す」を含めていたが、
   `max_model_calls=20` の hard cap が output 0 byte のまま process を止めた。caller の上限設定時に
   final answer 用 reserve を見積もる手順、または soft-stop 後に最終出力へ移る実行面を候補にする。
   本 wave では上限を広げた新 job で回復し、dev-wave 改善実装は行わない。
