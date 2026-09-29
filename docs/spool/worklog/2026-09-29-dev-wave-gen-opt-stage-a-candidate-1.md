---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-gen-opt-stage-a-candidate
seq: 1
title: 段 A の試しの候補を競合度順の施錠 (Cicada の write set の競合度順の sort) に決め、次点を開始前の先送り (TsDefer) とした。Q1〜Q8 の区分、受理文法と骨格 API の仕様、小さいモデルの案、計算の見積りを一次資料に固めた (insight のみ、計算なし、branch dev-wave-gen-opt-stage-a-candidate)
---

## 本文

- 依頼: 並行 wave の md_6 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_6.txt`、共通指示 `common-2.txt`)。一次資料は `output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md`。
- 軽量版で段 2・3 を省き、段 6 の read-only レビュー 1 本を残した (設計 docs の wave のため、common-2 §6)。レビュー (gpt-6-sol・medium、9 call・223 秒) は NO-GO で must-fix 3・should-fix 1。親は全件 real と裁定して直した: 3 key の全順列の場面の witness が先頭 key の同じ 12 組で到達不能、INSERT を施錠しない実装と「モデルが全候補を覆う」主張の食い違い (候補が並べ替えるのを UPDATE だけの write set に限った)、2 node 時間の線のために 3 取引の層を後回しにできると読める文 (省かないと書き直した)、低競合の workload の結果の予断。焦点再レビュー (5 call・116 秒) は 4 件とも closed で GO、新しい should-fix 1 件 (INSERT・DELETE の取引で通知の hook を呼ぶかの曖昧さ) を直した。一次資料 §11。
- セッションの異常: `EnterWorktree` の name 形が「Could not read the repository git config to neutralize filter drivers」で失敗し、手動 `git worktree add` (login の負荷 60〜70 で checkout 約 20 分) の後、path 形も worktree 一覧の 10 秒上限で 2 回落ちたので worktree へ直接 cd して作業した。`dev_wave_submodule_init.py` の 1 回目は `update-no-fetch` rc=1 で入れ子の googletest が未初期化のまま残り、開始 gate も NG になった。`git submodule update --init --recursive --no-fetch` の後の再走で両方 rc=0 (いずれも既知の型)。

## 次の一手差分

### 更新

- [T-2899] **P2**: 段 A の試しの候補を決めた (`output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md`)。関門の Q1〜Q8 で、上限つき施錠待ち・乱数つき指数 backoff・開始前の先送り・競合度順の施錠は「そのまま足りる」、BCC は「意味の拡張が要る」(validation の置き換えと版の識別子の形)。本枠 2 つは段階 F の LLM 方策と重なるので外し、編集範囲の小ささで **競合度順の施錠** (Cicada §3.5・Table 2) を選んだ。次点は **開始前の先送り** (TsDefer。骨格を workload 側の driver に置き、共有状態・予定 key 集合・先送りの上限を同時に開くので 2 本目以降)。候補と見積りは [T-2896] に書いた。残りは、次点を開くときの骨格の設計 (同 §3.3 の列挙を起点に)。
  base: 9dae4a2f8b4ef346ea31f8a3378a808c9f4677033cee1c0807a7adb318184001
- [T-2896] **P2**: 段 A の試し 1 本 (D2289)。候補は **競合度順の施錠** に決まった (`output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md`)。施錠の前に骨格が write set の各 tuple の TID word を 1 回だけ読み、候補が返す優先度の降順 → storage → key の全順序で並べてから施錠する。並べ替えるのは UPDATE だけの write set で、Silo の既定の no-wait のまま、関数方策の軸は stock に固定する。名前つきの対照は Cicada の近似 (版が新しいほど先に施錠)。workload は Cicada に寄せた点・既存の write-heavy・低競合の対照の 3 点を結果の前に登録する。計算は pair job 1 本 0.206〜0.220 node 時間で、対照 1 本 × 3 点で 0.62〜0.66、LLM の候補 2 本を足して 1.85〜1.98 node 時間。この仕組みの小さいモデル (同 §5、施錠順を全順列にして点の読みと UPDATE だけの取引について軸の全候補を 1 つのモデルで覆う) の 3 取引の層は省かず評価の前に流し、計算ノードで流すと仮定付きで約 1.6 が加わるので、合計が 2 node 時間以上になり投入前にユーザー確認が要る (同 §6)。開始の前提は [T-2885] (還元判断はユーザー確認待ち) と [T-2884]・[T-2886]・[T-2887]・[T-2888] の着地と、この小さいモデルの反例なし。優先度は親の暫定。
  base: 328b21a905618ea0f1937e6a839f329b6160de6ccbeb9bd9d6ce5b18cc1f7edf
- [T-2886] **P2**: 同関門の受理文法と骨格 API。段 A の試し候補が競合度順の施錠に決まり、仕様を `output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md` §4 に固めた: 候補は提案文字列で受け、policy-C++ v1 の規則のまま型・field・hook の表だけを新しい軸 (仮称 `silo-lock-order-policy`) のものに差し替える。候補には pointer も handle も渡さず、骨格が読んだ TID word の値の写しだけを渡し、決定は「並べ替えるか」と「要素ごとの優先度」の 2 つ。INSERT・DELETE を含む取引では順序を決める hook を呼ばず stock の sort に戻す。trace・counter・集合・tuple・同期の名前は許可リストに入れず、拒否を文法の test に置く。sort 軸の patch とは排他、`NO_WAIT_LOCKING_IN_VALIDATION=1` を build で要求する。既存の policy 系の受理集合を変えない。根拠: 関門 §3.1・§7 の U3。
  base: 09ff7942267db8c7808de15533392f9f3fa721b8893f1664393e03bacc1804fb
