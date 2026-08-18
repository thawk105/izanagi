---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t715-memo-failclosed
seq: 1
title: [T-715] 択 (b) を実装した — prewarm は不在から新設、敵対レビューが恒真ゲートを 1 件、変異が検出穴を 1 件出した (コード + docs、branch worktree-dev-wave-t715-memo-failclosed)
---

## 本文

- **裁定の前提 3 点が実測で覆った** (詳細は `output/insights/2026-08-18_t715-prewarm-failclosed/`)。
  1. 「prewarm を前提化する」の prewarm は**実装が存在しなかった**。repo の Python 全件で 0 件で、
     現存したのは遅延 memo だけだった。本 wave が新設した。
  2. 解決 1 回は 15.3 秒 (login) / 19.70 秒 (計算ノード無競合) で、08-10 package の
     「数百秒規模」ではない。2026-08-12 裁定の凍結検証保留 3 件が効いている。保留が解ければ戻る。
  3. 08-10 package の「wall は real-repo group の直列和で説明でき、その 96% は 2 node」という
     律速モデルは崩れている。group の直列和は 125.5 秒 / 69 node で wall より短く、
     現在の律速はスループット (直列総和 5,991.2 秒 ÷ wall 173.10 秒 = 実効 34.6 worker)。
- **穴そのものは健在だった。** 本番 resolver 1 回で `search_repository` が発火し、
  untracked と ccbench submodule を含む 13,565 file を実際に列挙・読取していた。実装理由は成立する。
- **裁定文の「worker 起動前」は xdist では実装不能**と分かり、barrier を「test body が 1 本も
  走る前」へ縮小した。理由と却下案は {{D:receipt-memo-prewarm-barrier}}。
  **この縮小はユーザー裁定の字面からの後退なので、報告で明示した。**
- **敵対レビューが恒真ゲートを 1 件出した (Critical)。** 段 5 実装は公開端の fail-closed を
  serial 分岐でしか守っておらず、公開 `real_repo_receipt()` に「xdist UID があるときだけ
  production resolver へ倒す」分岐を足すだけで新設検査も変異も全部すり抜けられた。
  AST の caller 検査も名前 1 つしか見ておらず、別名・`getattr`・module 属性を read-only probe で
  すり抜けられることが実証された。fix で公開 2 endpoint × UID 下の 3 障害を負例に加え、
  AST を到達しうる呼出し全般へ広げた。
- **変異が検出穴を 1 件出した。** MT2 (`_cache_store` の例外再送出を消す) が 1 巡目で SURVIVED し、
  落ちた node が 0 件だった。既存検査が `_cache_store` 自体を mock で差し替えて失敗を注入しており、
  実関数の本体が 1 度も実行されていなかった。実 `os.replace` を失敗させる負例を足して
  再走で KILLED になった (1 巡目 KILLED 3 / MISMATCH 2 / SURVIVED 1 → fix 後 KILLED 4 /
  MISMATCH 2 / SURVIVED 0)。MISMATCH 2 件は過剰決定と期待の片落ちで、事前登録は書き換えていない。
- **段 3 の敵対レンズ 2 本が 1 度、codex の利用枠切れ (`You've hit your usage limit`) で
  出力ゼロになった。** 恒久的な枠切れではなく並行 wave との取り合いで、再投入で通った。
  失敗は 4 秒・token ゼロで安価なので、同種の即死は再投入して確かめるのが正しい。
- **dev-wave 改善候補 (段 8)**: 基準値のための全走を受入形と区別して走らせる方法が
  手順に無い。`--durations` / `--junitxml` を足しても受入形判定は True のままだった
  (受領証を作らない直呼びなので実害は無かった)。docs 予算が 3 層とも満杯のため本 wave では
  編集せず、ユーザー裁定へ返す。

## 次の一手差分

### carry

- [T-715]
