---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2129-spool-carry-wording
seq: 1
title: [T-2129] docs/spool/worklog/README.md の「明示 carry と暗黙 carry は同じ出力を生む」を、fold の時点でその T が active なときに限る条件付きの記述へ直した — 別 wave が先に land して外した T の明示 carry は land lock の内側で transition-target になり受入全走の後に初めて分かる場合がある (docs のみ、branch worktree-dev-wave-t2129-spool-carry-wording、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2129] (P2、entry 1136) docs/spool/worklog/README.md の『明示 carry と暗黙 carry は同じ出力を生む』
  (現 59 行目付近) を、並行 wave で偽になる条件付きの記述へ直す — 別 wave が先に完了・見送りした項を明示 carry している
  fragment は fold が transition-target で止まり、停止は land lock の内側なので受入全走の後に初めて分かる。是正は文言だけ
  とし、tools/spool_fold.py の挙動は変えない (現行の拒否は正しい)。docs のみ。着手直前の local main から fresh worktree。
  本題の文言だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **旧 wave で修正した (README の 1 項目 = 4 行 → 12 行、他の項目は 1 byte も変えていない)。** `tools/spool_fold.py`・`check_docs.py`・
  test は不変。insight は作らず、裏取りの事実は本文に残す。
- 裏取り (login node pegasus02、着手直前の local main `c8e8dc06f` の現物): `tools/spool_fold.py` の `_render_next_actions` は
  `carry` を `新規` 以外の操作として `action_by_id` に入れ、`set(action_by_id) - set(active_by_id)` が非空なら
  `transition-target` (active でない操作対象) を raise する。暗黙 carry (操作なし) は active 集合の走査で stub を描くだけで、
  非 active な T は走査に現れない。起票元の entry 1136 (`docs/archive/worklog-phase3-0901-1135-1136.md`) は両 wave が同じ
  行を独立に読んで裏取りしており、本 wave の読みと一致した。
- 既存被覆の照合: D128 の却下案「全 active ID の明示遷移」と `docs/spool/README.md` の暗黙 carry 規則は「他 wave が新 T
  を先に畳んでも畳める」(追加方向) だけを書く。F233 は同一 fold 内の 2 fragment 衝突。「別 wave が先に land して T を
  外した後、明示 carry が lock 内で止まる」(削除方向) は repo の docs に無く、これだけを純増で書いた。F233 は同じ拒否経路
  の同一 fold 内の型として名前で引いた (新 F・新 D は立てない)。
- 並行 wave の編集面照合: 全 209 worktree を merge-base 基準で走査し、`docs/spool/worklog/README.md` を編集した wave は
  0 件、fragment で [T-2129] に触れる wave は 0 件。base digest は worktree 作成前に main の作業木で
  `spool_fold.py --base-digest` から取った。
- 軽量版 (docs-only)。段 2・3・6 の子はゼロ (設計択一なし、正しさ防壁に触れず、受理集合不変、一次資料からの数値・不在の
  書き起こしも無い — fold の挙動は source 行で裏取り済み)。実装子なし。dev-wave 改善候補 0 (段 8 は無言通過)。
- セッション異常: `EnterWorktree(name)` が既知型 (「git config を読めない」) で失敗し、`git worktree add` を背景で自走
  (27,713 file、約 10 分)。`dev_wave_submodule_init.py` は別 session の同時初期化と重なって tool 内の git timeout (30 秒)
  を超え、`runtime-io-failure: update-no-fetch` rc=1 を返したが、木は揃っており (`git submodule status --recursive` 3 件とも
  `-`/`+` なし) 再走で rc=0。実害なし。
- 検査: `tools/check_docs.py`、`spool_fold.py --dry-run`、`git diff --check`、provenance 監査。受入全走は land 前に 1 回
  (結果は land の受領証)。
- 回収 wave の独立監査で検出時点の断定を限定した。上記依頼の引用は保持するが、実装上は作業木へ反映済みの
  完了・見送りや同一 fold 内の先行 fragment による除外を `--dry-run` でも検出する。未反映の main 側の変化により、
  lock 内で初めて判明する場合がある。README と本 title を条件付きへ直し、spool の挙動は変えていない。

## 次の一手差分

### 完了

- [T-2129] `docs/spool/worklog/README.md` の該当項目を条件付きの記述へ直した。`spool_fold.py` の挙動は不変。
  remaining: none
  base: ead7d7f526564fe74e180bf03ef01eb54ddaa188ae0fd37d633a990871e56c2d
