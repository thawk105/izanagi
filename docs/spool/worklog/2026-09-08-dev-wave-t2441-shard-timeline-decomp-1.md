---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2441-shard-timeline-decomp
seq: 1
title: [T-2441] 受入 wall の残余を session timeline で分解した — 残余の 9 割は走を跨いで動かず、D1369 が未計測と書いた約 21.9 秒は consumer を載せた shard 固有の controller 側処理だった。敵対レンズが初稿の 9 件を突き 2 つの結論を撤回した (docs のみ、branch worktree-dev-wave-t2441-shard-timeline-decomp)
---

## 本文

- **ユーザー依頼:** [T-2273] の内訳を `session_timeline` で確定する。受入全走の shard report から
  shard-0 の wall より collection 区間・worker 占有・real-repo lock 保持を引き、残る 95〜207 秒が
  受入形固有か host 差かを判定する。**本題の解析だけで、仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外**、と明示された。稼働中の受入まわり wave (accwall 系) との編集面重複を
  起動時に検査すること、着手直前の local main から fresh worktree を作ることも指示された。
- **判定は出た。全数値と限界は `output/insights/2026-09-08_t2441-shard-wall-decomposition/`、
  設計判断は {{D:acceptance-residual-is-mostly-run-invariant}}。** 残余は
  `collection + dispatch + 実行中の遊び + teardown` に分かれ、その 88〜97% は走を跨いで動かない。
  動く分は主に collection に出る。
- **敵対レンズ 1 本 (read-only) が初稿の 9 面すべてに所見を返し、親は 9 件すべてを real と裁定した。**
  逐語は insight の `consult-sol-verbatim.md`。**うち 2 つの結論を撤回した。**
  (a) 初稿は「残余に未分解の区間は残っていない」を分解が全件 0.0 秒で閉じることから主張したが、
  この等式は成分の定義から代数的に成立する恒等式で、観測の完全性を示さない。
  (b) 初稿は teardown の shard-0 超過を memo session の後始末と説明したが、後始末は
  `pytest_unconfigure` から呼ばれ、受入 report の生成も acceptance plugin の
  `pytest_sessionfinish(trylast=True)` から呼ばれる。**どちらも JUnit plugin が所要を確定した後で、
  測っている区間の外にある。** この 2 件は親が独立に code を読んで確かめた。
  他に「標本最小値は必ず払う下限ではない (58→62 走で 4.0 秒下がった)」「最小値からの超過から
  host の寄与は分離できない」「dispatch 全量を prewarm とは言えない」を採用して主張を弱め、
  「ほぼ全量 collection」を shard-0 では 70% へ訂正し、裾の超過 +20.6 秒の基準の取り違えを直した。
- **依頼文の前提 1 つが、実測で覆るのではなく「今は違う」形で動いていた。** 依頼は残余を
  95〜207 秒とした。2026-09-08 の 62 走で同じ量を測ると shard-0 で 76.8〜123.8 秒である。
  **当時の測定が誤りだったのではない** — 同じ式・同じ源で 09-04/05 の走を測り直すと
  79.0〜207.3 秒になり、**上端は記録と一致する** (下端は 16 秒低く、母集団の取り方が違う)。
  下限は 5 日間ほぼ不変で、裾だけが細っていた。規律 7 に従い当時の値は当時の事実として残し、
  判定は現行分布について行った。何が裾を細らせたかは、当時の走に観測 field が無いため決まらない。
- **測定面の食い違いを 2 つ見つけた。** (1) D1620 は測定面を「canonical 起動の receipt が記録する
  最遅 shard の wall」と定めたが、**receipt (`dev-wave-acceptance-receipt/v5`) に wall の欄は無い。**
  D1620 自身が「receipt の field 名と K の証拠位置の明記」を別の AI 手番として残しており未了。
  (2) 現存する唯一の源である junit の `time` は「session 開始 → JUnit plugin の sessionfinish」で、
  D1620 が言う「collection 開始から teardown 終了まで」**とは一致しない**。右端のずれは本 wave が
  `teardown` として測った量そのもの (2.8〜7.1 秒) である。手番は
  {{T:acceptance-wall-field-in-receipt}} として起票する。
- **解析 probe は repo へ入れていない。** 実装面を親が書けないため 6 本の probe は job dir に置き、
  insight に式・入力の場所・生データ 187 行 (`decomposition.json`) を同梱して再計算できる形にした。
- **編集面の重複検査 (依頼の明示要求):** `.codex/worktrees/accwall-unit-b` が
  `tools/acceptance_shards.py`、`orchestrator/tests/test_run_tests_shards.py`、
  `orchestrator/tests/acceptance_duration_ledger.json`、
  `orchestrator/tests/test_autonomous_trial_completeness.py` を未 commit で改変中、
  `accwall-unit-a` が `orchestrator/tests/host_tree_cache.py` 他を追加中だった。**本 wave は
  これらを 1 行も編集していない** (docs と insight のみ)。重複なし。
- **セッション異常 1 件:** `EnterWorktree` が
  "Could not read the repository git config to neutralize filter drivers" で失敗し、
  `git -C <main> worktree add` へ切り替えて回復した。

## 次の一手差分

### 完了

- [T-2441] 受入 shard の wall 内訳を `session_timeline` で分解した。残余の 88〜97% は走を跨いで
  動かず、動く分は主に collection に出る。D1369 が未計測と書いた最遅 shard 固有の約 21.9 秒は、
  consumer を載せた shard に固有の controller 側処理だった (全量が prewarm とは言えない)
  ({{D:acceptance-residual-is-mostly-run-invariant}})。
  remaining: none
  base: 5de797f036e9418f56d3824d75d5042783c0d8ffcc7699342f1d1b3a0ad7c7f9

### 更新

- [T-2273] **P1・内訳は分解済み → 次の手番は短縮対象の選定 (別 wave の裁定事項)**: 受入全走の
  最遅 shard を 5 分以内へ入れる。残余の内訳は {{D:acceptance-residual-is-mostly-run-invariant}} で
  分解した。走を跨いで動かない部分は shard-0 で 75.6 秒 (collection 50.9 + dispatch 18.4 +
  teardown 6.4)、他 2 shard で 53 秒台。走ごとに動く分は残余の 1 割前後で、主に collection に出る。
  実行中の遊びはほぼゼロ。したがって残る短縮候補は (a) 3 shard 共通の collection 約 51 秒、
  (b) shard-0 の dispatch 約 18〜26 秒 (交絡があり、consumer を別 shard へ寄せた反実仮想の走行で
  分離が要る)、(c) 最大 worker 占有 (中央値 231 秒、D1369 が下界を
  `max(最長単体, 総仕事量 ÷ worker 数)` と定めた層) の 3 つに絞られる。どれに手を付けるかは未裁定。
  base: e094241f4cfa4b325d7f9ca5dc58dbfee0b8356715b7d77d3154271457629c56

### 新規

- {{T:acceptance-wall-field-in-receipt}} **P3・新規**: D1620 が残した手番。受入 wall の測定面が
  receipt のどの field に現れるかを明記する。現物の receipt
  (`dev-wave-acceptance-receipt/v5`) に wall の欄は無く、現存する唯一の源である
  shard の `junit.xml` root の `time` は「session 開始 → JUnit plugin の sessionfinish」であって、
  D1620 が言う「collection 開始から teardown 終了まで」とは一致しない (右端のずれは 2.8〜7.1 秒)。
  field を足すか、測定面の文言を現物へ合わせるかを含めて決める必要がある。
