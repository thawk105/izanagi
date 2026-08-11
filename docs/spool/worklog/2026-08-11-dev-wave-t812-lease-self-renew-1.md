---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t812-lease-self-renew
seq: 1
title: [T-812] 受入 lease の自己保持 deadlock を閉じた — claim が TTL を更新して held-self を返し、待ち手が受理して進む (コード + docs、変異 15/15 KILLED、branch worktree-dev-wave-t812-lease-self-renew)
---

## 本文

- **裁定 = worklog 424 / rulings-inbox §96 の推奨 3 点セット** (ユーザー発話「推奨通りで」)。
  却下済み代替の「release して取り直す」へは戻していない。
- **段 1 で deadlock を実機再現した** (私有 lease dir、repo 外 probe)。同一 wave の 2 度目の
  `claim` は `held` / `holder_self=true` を返し、**lease の mtime は不変** (TTL が延びない)。
  正本待ち手はこれを受理せず、`max-wait` (本番既定 7200 秒) まで空転して
  `stage=claim-timeout rc=70` で死ぬ。**実害は 4 例目** — land 1 で約 18 分、t756 で約 20 分、
  さらに本 wave の稼働中に **[T-813] wave が同じ経路を踏み、待ち手を迂回して裸形の
  `run_tests.py` を直接投入する回避を取った** (peer advisory で共有された実測)。
- **敵対 2 レンズ + レビュー 2 本で real 所見 22 件、refuted 0。** 最重要は
  **holder が wave slug の SHA-256 先頭 12 桁であって invocation を識別しない**こと。
  `held-self` は「同一 slug の別 invocation」も通すため、**同時受入の窓が開く**。
  裏取りとして **`tools/run_tests.py` に flock は無い** (後段で並行受入を直列化する層は存在しない)
  ことと、待ち手の identity preflight は「branch 名が wave slug で終わる」しか要求しないため
  **別 worktree でも同一 slug を持てる**ことを実読で確認した。capability / fencing は受入の
  受理集合の意味論に触れるので実装せず、機構案を裁定パッケージで返す ({{D:lease-self-renew-scope}})。
- **scope 内で 4 件の補強を追加裁定した。** (i) `_open_lease` が flock **前**の mtime snapshot で
  stale を判定していたため、更新直後の lease を先行 claimant が回収できた — これを塞がないと
  裁定 (1) の TTL 更新が実効を持たない。(ii) `age_seconds` を synthetic な 0 でなく更新後の実
  mtime から再計算する。(iii) **renewal 失敗を例外のまま外へ出すと helper が rc=2 になり、待ち手が
  ownership 未確定 (`UNKNOWN`) のまま cleanup で稼働中の lease を release する** ため、全失敗を
  構造化 `unavailable` + `self-renew-failed` へ畳む。(iv) `status` は lease を変更しない。
- **親の実走が子の見逃した回帰を出した。** 実装子は Pegasus の dispatch preflight 障害で pytest を
  1 度も走らせられず「実装済み・未実走」と申告。親が走らせると **185 passed / 3 failed** で、
  新 guard が **`acquired` (常に `holder_self=true`) まで拒否**していた。子のテストが
  `{"state":"acquired"}` という**実 helper と違う手製 payload**を使っていたため新テスト側は
  全緑で、実 helper を使う既存 3 本だけが露出させた。fix で fixture を実 payload へ統一した。
- **変異 15/15 KILLED、SURVIVED 0、MISMATCH 0** (`--force-dispatch`、2 走目が権威)。1 走目は
  MISMATCH 8 だったが、全件「期待 node 集合が実測より狭い」= 検出力の過大評価ではなく**過小評価**
  であり、実測集合へ補正して再走した。レビュー B が構成した等価変異 3 件 (検査の pre-renew 移動 /
  `fstat(fd)` を pathname `stat` へ差し替え / `status` で一時更新して復元) も KILL される。
- **main 取り込みで防壁 1 件に当たった。** main の docs 予算 wave が `.claude/commands/dev-wave.md`
  を縮約し、同時に **入口の待ち手 consumer 逐語行を `tools/check_docs.py` で exact pin** する検査を
  新設していた。受理集合を `{acquired, held-self}` へ広げると pin が赤くなるので、**検査を緩めず
  逐語だけを追随**させた (実装面のため Codex author が別 commit)。
- **受入窓の飽和を実測した。** 段 9 の受入投入で正本待ち手が **7200 秒 (既定上限) 待って
  `claim-timeout rc=70`** になり、**1 度も受入を投入できなかった**。待機中に holder は 4 回交代し
  (main は `034d7590` → `3f8a12cf` → `d0e912d6` → `b2a95ed6` と前進)、待ち札は 8〜11 枚で推移した。
  待ち行列長 × 1 走 20 分前後という構造であり、**裁定 425 が (d3') シャーディングと (f) land train
  を用意した「飽和」がここで観測された**。本 wave は上限を延ばして再投入した。
- 段 8 の dev-wave 改善候補 1 件: codex 子の `--max-cli-reported-tokens` 既定 1,000,000 は
  読み込みの多い consult を**完了直前に SIGTERM して出力 0 byte にする** (実測 1,017,768、17 分空費)。
  同一 prompt での再投入は job_id が同じで receipt 上書き拒否 rc=2 になるため、prompt を変えて
  投げ直す必要がある。

## 次の一手差分

### 完了

- [T-812] 受入 lease の自己保持を更新可能にし (`held-self`)、待ち手の受理集合を
  `{acquired, held-self}` へ広げ、自己保持で進めない場合を理由付き fail-closed にした。
  runbook §7.3 と dev-wave 入口も整合。変異 15/15 KILLED。scope 外の機構案 6 束は
  {{D:lease-self-renew-scope}} として裁定パッケージへ返した。
  remaining: none
  base: 488733cbaa5b78f4a76bd2bea4318270fe1b8e10fd7c97eeb20d6cc788c54e72

### 新規

- {{T:lease-invocation-fencing}} **P2・裁定待ち (本 wave が返却)**: 受入 lease の holder を
  invocation まで識別できるようにする機構の可否。現状 holder は wave slug の digest 12 桁で、
  `held-self` は同一 slug の別 invocation も通す (`tools/run_tests.py` に flock は無く、
  別 worktree でも同一 slug を持てる)。候補 = invocation capability の lease payload 束縛 +
  release/renew の capability 一致要求 + active-invocation guard。**受入の受理集合の意味論に
  触れる**ため実装前にユーザー裁定。併せて (i) 受入が TTL を跨いだとき rc=0 を返してよいか
  (heartbeat renewal か結果不受理か)、(ii) stale な自己保持を `lost-exclusivity` で止めるか、
  (iii) 連続 renew / 累積保持の上限 (owner 優先と FIFO の折り合い)、(iv) 版混在時に旧待ち手の
  `UNKNOWN` cleanup が同一 slug の lease を release する穴、も同じ束で返す。
  正本 = `output/insights/2026-08-11_t812-lease-self-renew/package.md`
