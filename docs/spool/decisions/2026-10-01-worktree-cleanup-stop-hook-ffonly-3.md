---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-10-01
wave: worktree-cleanup-stop-hook-ffonly
seq: 3
---

## {{D:cleanup-stop-ff-exemption}}. 撤去を促す Stop hook は、main へ ff で揃えただけの木を通す (D2314 項 4 の判定の改訂)

**決定:** `tools/dev_wave_cleanup_stop_hook.py` の判定 (D2314 項 4: branch が作成点から前進し HEAD が `refs/heads/main` の祖先なら 1 回止める) に、
次の全部が成り立つ木を通す免除を足す。それ以外は D2314 項 4 の判定のまま。

1. branch の reflog の最古項の subject が `branch: Created from ` で始まる。
2. それ以外の全項の subject が `merge main: Fast-forward` か `merge refs/heads/main: Fast-forward` と完全一致する。
3. その各項の OID を、`refs/heads/main` の reflog がその項の記録時刻以前 (≤) に指していた。
4. reflog は `--date=unix --format=%H %gd %gs` で 1 回読み、LF だけで割る。subject が空の行は空 subject とし、区切りの欠落を fail-open にしない。
   main の reflog を読めない・解析できないときは免除しない。branch reflog の OID 不正・git の失敗・timeout は従来どおり通す (fail-open)。

**理由:**
- 背景 job の dev-wave は開始時に DW-O20 の `merge --ff-only main` で揃えるので、自分の commit が 0 でも D2314 項 4 の条件が成り立ち、
  turn を終えるたびに誤った撤去の促しが出ていた (F1081、md_34 で 3 回・md_37 で 6 回)。指示どおり撤去すれば作業中の木を消しうる。
- 依頼は「本当に land 済みの木で促しが消える方向の緩和はしない」。subject の完全一致だけでは、作成項の期限切れ、U+2028 を含む subject の誤分割、
  最古項の空 subject の区切り消失、tag `main` や `GIT_REFLOG_ACTION` による同じ subject の生成で、land 済みの木も通ってしまう (段 6 敵対レビュー 2 本の反例)。
  1・3・4 はそれぞれを塞ぐ。3 は main reflog 3,732 項の読み取りで 0.15 秒 (1 点の実測) で、1 呼び出し 2 秒・合計 5 秒の予算内に収まる。
- 3 の比較を `≤` にするのは、main の前進と wave の ff が同じ秒に記録されるのが通常だから (実時計の test 3 件が `<` の変異で落ちた)。

**却下した選択肢:**
- 「reflog に commit 由来の項 (`commit…`) が 1 つ以上ある木だけを止める」(F1081 の恒久対応の例示) — 止める側を列挙する形で、cherry-pick・reset・
  main 以外からの ff で自分の作業を取り込んで land した木の促しが消える。
- subject の完全一致だけ (段 5 の初版) — 上の反例 4 種で land 済みの木が通る。
- 記録時刻・同名 tag・reflog action の改変まで塞ぐ (焦点再レビュー C の反例 3 件) — git の記録の改変が要り、D2314 項 4 の hook は注意喚起であって
  正しさ防壁ではない。旧判定も reflog の削除や `branch -f` には元々負ける (hooks/README.md hook 5 の既知の限界)。
- sha 指定の ff・`pull --ff-only`・`reset --hard main` も免除する — 実 repo の branch reflog の観察で未出現で、免除を広げると land 済みの木を通す余地が増える。

**残る限界:** git の記録 (main の位置・tag・reflog action・記録時刻・reflog 項) を改変した木では land 済みでも通りうる。main の reflog が失効していると
ff だけの木で従来の誤検出が残る。main reflog の読み取りが時間切れになると祖先判定の予算が無くなり通る (この経路に入るのは作成後の全項が ff main の木だけ)。
`hooks/README.md` hook 5 の判定・既知の限界の文言の更新は D427 の経路で行う持ち越しとした。
