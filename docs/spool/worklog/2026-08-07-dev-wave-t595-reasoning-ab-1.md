---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t595-reasoning-ab
seq: 1
title: D207 の段 2/3 reasoning=max を機械 pin にした — A/B は実装も実走もしておらず引き下げ可否の evidence は 0 件 (コード + docs、受入 7113 passed / 20 skipped、変異 7/7 KILLED、branch worktree-dev-wave-t595-reasoning-ab)
---

## 本文

- **依頼と成果物の乖離を先に書く。** 依頼は「段 2/3 の `reasoning=max` を `high` へ落とせるかを
  `tools/codex_reasoning_ab.py` の paired・blind・非劣性で評価する」だった。
  **本 wave はその A/B を実装も実走もしていない。max→high の非劣性・引き下げ可否を示す
  evidence は 0 件である。** 実装したのは現行の `max` 記述を守る adoption latch だけで、
  評価装置・protocol・endpoint 台帳・campaign は未実装である。この latch は served model や
  実効 effort を attest しない。certified 選択・材料レポート・試行台帳の評価値は不変である。
  完了・前進・一部実証と読ませてはならない。
- 実走しないと裁定した根拠は {{D:reasoning-ab-endpoint-requires-full-waves}}。
  D207 の endpoint は段 2/3 の下流量であり 1 replicate = 1 本の完全な dev-wave になる。
- 装置は T-181 の focused review benchmark に literal 固定されており、段 2/3 の case family を
  持たない。T-181 の台帳自体が `experiment_complete=false` で、最終版装置での 10 run 再走が未了。
  本 wave はこの未認証性を新設計の根拠へ格上げしていない。
- **親 brief の数値 2 件を段 4 で自己訂正した。** (a) fix 巡回数の分布は `s6-fix*.md` の glob で
  数えており、fix worker 出力でない裁定文書を巡回に混入させていた。(b) 必要 pair 数を「9〜15」と
  書いたが、正規近似だけでも 10 pair 台後半で、過小だった。結論の向き (単一 wave で実走不能) は
  変わらないが、根拠を「pair 数の見積もり」から「endpoint・盲検・実 treatment・解析凍結が
  未閉鎖」へ差し替えた。
- 段 3 の敵対相談は 2 レンズとも NO-GO (must-fix 11 件 / 8 件 + should-fix 1 件)。
  段 6 の敵対レビューも 2 レンズとも NO-GO で、両者が独立に同じ 2 件 (decoy literal による迂回、
  production 委譲の未検査) を突いた。
- **fix は 2 巡回した。** 1 巡目で prose 表記の decoy と production 委譲を塞いだが、
  焦点再レビューが実キー表記の穴を見つけ、親が書き込みなし probe で裏取りした。
  DW-S02 を ``codex `model_reasoning_effort="high"`（例: `reasoning=max`）で`` と書き換えると
  finding 0 で通過した。2 巡目で effort 表記の全形を認識させ、引用行の除去をやめた。
  1 巡目の commit message にあった「2 件を fix で塞いだ」は root cause の完全閉鎖としては
  過大であり、2 巡目の commit 本文で訂正した。
- 段 4 で real と裁定しながら実装しなかった所見 10 件 (A-4, A-5, A-6, A-10, A-11, B-3, B-4,
  B-6, B-7, B-9) は、対象となる新 family / 新台帳 / 新 protocol を本 wave が作らないため
  **未発火**である。**refuted / closed / resolved ではない。** 全件を campaign 設計へ持ち越す。
- 変異は 3 走。1 走目は baseline が dispatch receipt を得られず PARSE_ERROR で中止 (infra 起因、
  変異結果ではない)。2 走目は 6 件中 KILLED 4 / SURVIVED 2。生存 2 件は注入実在を確認したうえで
  他層の mask を疑い、両層同時変異 2/2 KILLED で裏取りした。ただし焦点再レビューがこの
  「冗長層」解釈を反証し、単独で fail-open 反例を構成できることを示したため、fix 2 巡目後に
  再照準した最終走で 7/7 KILLED、全件が期待 node と一致した。
- 段 4 の変異事前登録から「節数ガードの無効化」を外した。節を丸ごと消すと既存の必須節検査が
  先に赤にするため、DW-M01 の単一理由性が成立せず kill 帰属が付かない。
- 受入全走は commit `3772116d` に対して 7113 passed / 20 skipped、rc=0。
- 設計判断は {{D:reasoning-effort-adoption-latch}} と
  {{D:reasoning-ab-endpoint-requires-full-waves}}。
  逐語・変異台帳は `output/insights/2026-08-07_t595-reasoning-ab-latch/`。

## 次の一手差分

### 更新

- [T-595] **P2・ユーザー裁定待ち**: 段 2 / 段 3 の `reasoning=max` を `high` へ落とせるかの
  paired・blind・非劣性 A/B は、**単一 wave では実走できないと確定した**
  ({{D:reasoning-ab-endpoint-requires-full-waves}})。現行既定は
  {{D:reasoning-effort-adoption-latch}} の機械 pin で守られている。
  ユーザーへ返す択一は 3 つ — (a) campaign に着手するか (完全 dev-wave 規模の予算決定)、
  (b) 着手するなら joint (段 2/3 を同時に下げる) か段別帰属か。段別は必要本数が跳ね上がる。
  (c) 着手しないなら、この latch を恒久扱いにして T を閉じるか、保留のまま残すか。
  **どれも決まるまで装置の一般化に着手しない。**
  base: 45174aa00bf924699ab3d9fcee59c6bdf915c847c50edb3a363ac030b8136c14

### 新規

- {{T:reasoning-ab-apparatus-generalization}} **P2・新規、T-595 の campaign 裁定後**:
  `tools/codex_reasoning_ab.py` を case family へ一般化し、full-wave endpoint 台帳と
  protocol 凍結を実装する。**T-595 で campaign 着手が承認されるまで起票のみとし着手しない。**
  閉じるべき前提は装置ファイルの外にある — wave の全 worker を実際に起動する trusted supervisor
  (現行 dev-wave は `DW-O01` の直接 `codex exec` で、`tools/codex_worker_launch.py` の
  production caller は repo 内に存在しない)、外部 custodian の独立 trust root、
  producer 契約の追記先の予算 ([T-597] と束ねる)。段 3 / 段 6 で real と裁定しながら
  未発火のまま持ち越した 10 件を入力にする (逐語は
  `output/insights/2026-08-07_t595-reasoning-ab-latch/`)。
