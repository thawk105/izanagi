---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t758-docs-corrections
seq: 2
title: land の lock 待ち予算が lock 外の作業に食われる会計を直した (コード + docs、branch worktree-dev-wave-t758-docs-corrections)
---

## 本文

- **着手理由はユーザーの直接指示である。** [T-758] の docs 訂正が全検査緑・受入 child-green まで
  到達したのに land が 42 回連続で失敗し、原因が land 側の構造的欠陥だと実測で確定した時点で、
  「通す構造にして通せよ」という指示を受けた。docs 訂正 (worklog 1482) とは別の変更単位として
  同じ branch で実装した。
- **設計判断は {{D:land-lock-cumulative-wait-budget}} に記録した。** 実装は
  `_run_outside_land_lock` と 2 つの呼び出し側、reason 文の分離、結果 JSON への窓の内訳の追加。
- **親の断定が段 3 の敵対レビューで 6 件倒れた。** 主なものは (i)「累積 180 秒は厳密な上限」
  (期限検査は `flock` 失敗の内側にしかなく、空いていれば超過でも取得できる)、(ii)「A は正しさ
  ゲートに触れない」(内容検査の省略は無いが時間による拒否条件と外側の終了時点は変わる)、
  (iii)「20 件の直接原因」(期限後でも 1 回は試すので、残予算を与えれば成功したかは不明)、
  (iv)「`window_elapsed_s − waited_s` は lock 外時間」(lock 内の preflight・再検証も含む)、
  (v)「fold gate の窓超過は前段の監査が窓を使い切った結果」(唯一の説明ではない)、
  (vi) 集計の不一致 (投入 42 回・status 記録 41 回であって 40 でも 55 でもない)。
- **別 session との相互訂正が 6 往復あった。** 私が倒された分: 77 秒を全史監査の値として誤引用
  (実際は範囲限定版)、rc=29 を「監査中の head 移動」と一般化 (8 回中 1 回だけ。5 回は dispatch
  rc=16、2 回は 480 秒 timeout)、稼働 wave 数を peer session 総数 93 で報告 (実際の稼働は 15)。
  私が倒した分: 相手の「A で 86% 救える」(`initial` を射程に数えた誤り。正しくは 61%、
  順番制と併用で 87%)、「reason 文が虚偽」(`return False` は `except BlockingIOError` の内側なので
  lock は実際に保持されている。誤誘導しているのは `waited_s` の側)、「lock 外の段は 3 箇所」
  (定義を数えた誤り。呼び出しは 2 箇所)、「全史監査が 180 秒に収まった記録は 1 件もない」
  (私の 18 件中 4 件が 56.1〜144.0 秒)、land 数え方の誤検出 (`grep dev_wave_land.py` が
  `test_dev_wave_land.py` に一致し、私の変異走行を land として数えていた)。
- **実装子は 2 回とも pytest を実走できなかった** (`qstat -Q preflight rc=1`、runner rc=16、
  child_started=false)。どちらも「実装済み・未実走」と正しく申告し `closed` とは言わなかった。
  テストの実測は親が行った。段 6 の fix は fixture の欠陥 (合成 `docs/phase3.md` に
  `### 裁定・完了記録` の見出しが無く spool 検証で拒否され、検査したい lock 再取得へ到達して
  いなかった) で、production は無変更だった。
- **親が実走前に orphan hold を 2 箇所から外した。** 発生源は自分の land の rc=29 で、job は
  実際には走って終端していた (`result.json` の `child_rc: 0`、qstat に不在)。`phase=pending-qsub`
  かつ `request_id: null` の一時 file だった。片方だけ外すと受入は rc=16 のままになる。
- 子エージェントは Codex の plan / consult 2 本 / author / fix の 5 本。実装面は Codex `role=author`
  が書き、親は commit と記録だけを担った。

## 次の一手差分

### carry

- [T-2600]

### 新規

- {{T:land-invalid-run-detail-opacity}} **P2・新規**: `spool_fold.py` の declared fold verifier が
  例外経路で `str(exc)` だけを残すため、`git_state.py` の `ReasonCode.INVALID_RUN` を投げる
  22 箇所のどれが発火したか出力から判別できない。別 wave が rc=26 で踏み、git の所要を単独計時
  (3.3 秒 / 予算 30 秒) して timeout 仮説を否定したが、残る候補 (想定外 rc・非 UTF-8 出力・
  SHA 形不正・`worktree list` の record 不完全) を絞る手段がない。構造的拒否の経路は
  `declared.detail` を載せるので、是正は例外経路でも detail を載せること。
- {{T:provenance-audit-never-dispatches}} **P2・新規**: 全史 provenance 監査の dispatch 判定が
  バイト予算だけを見て CPU 時間を入力にしないため、監査 (観測ピーク 630〜686 MB) は予算内に
  収まり続けて構造的に混雑した login node に留まる。実測は login 428〜574 秒 / 計算ノード 61 秒で
  7 倍振れ、land の監査上限 480 秒を超える回が出る。`--force-dispatch` が既に存在し、
  `authoritative = args.rev_range is None` を変えないので射程は狭まらない。ただし dispatch 経路
  そのものの失敗率 (別 wave で rc=16 が 5 回) が未計測で、キュー待ちを timeout から外す是正と
  併せて DW-O13 の母集合が要る。
