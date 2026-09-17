---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2710-t080-series-inquiry
seq: 2
---

## {{D:t080-series-deferral}}. t080 e2e 群の別系列化は、受理集合の同値条件が成立するまで採らない

**決定:** D2104 項 28 が求めた 3 材料 (被覆対応表・利用時拒否の実効性・移動後の最遅 shard wall) を取った上で、
t080 e2e 群 (D700 / D701 の 6 function / 11 node) の別系列化を**本 wave では採らない**。受理集合は変えず (D2068)、
`growth_test_holds.py` 保留の実 repo 直接検査は復帰させない。採否は、次の条件が別 wave で成立した時点でユーザーへ諮り直す。

1. 完走記録は runner 由来で真正に発行され、対象 commit・系列版・期待 node 集合・selected / finished・node 別 terminal・
   開始 / 完了時刻を持つ (D2002 条件 1)。
2. 期限検知 (24 時間) は起動側の記録に依存せず、利用の無い期間の未起動・queue 停止・途中死も検知する (D2002 条件 2)。
3. 利用時拒否は、verifier / adapter / driver の `gate_check` と `run_block` / holdout CLI の legacy 分岐 / floor の verifier 注入と
   独立な境界 / report の検証済み利用 / 受入受領証 / land の再判定の**全境界**で効き、診断 (系列自身・修理) から検証済み利用への
   昇格境界を持つ (D2002 条件 3)。
4. 関連入力の閉包は、git 可視の `output/` (fixture が複製する)、builder の docs 入力、非 ignored untracked、`external/ccbench` の
   実 checkout、freeze hold の版を含めて定義し、その変更で系列を焦点走へ加える (D2002 条件 4)。
5. 毎走受入の gate 4 は `U = C − M` の exact partition とし、gate 2 / 3 は C 全体で維持する (D2003)。
6. D701 の probe は維持し、M 本体の完走は別の terminal 証跡で担保する。
7. freeze hold の解除版を有効化する前に、その期待値を伴う M を完走させる (F485 の同日追随漏れの再演防止)。
8. 起動契約 (誰が・いつ・どの計算ノード経路で走らせ、失敗をどう回収するか) が repo 内の文書で決まっている。

**理由:**

- **受理集合の同値性が示せていない。** 現行は M の緑が同じ tip・同じ走で観測される。別系列にすると「≤24 時間前に関連内容が同じ
  記録で緑」へ変わり、関連内容の閉包を tree OID で完全に表す設計が無い。closure A (`orchestrator` + `tools` + `external`) は
  `output/` を含まず、現行 e2e が base 構築時の複製で拾う「前回完走後に land された conjunction file」を旧証跡では検査しない —
  これは D2068 が whitelist 案を却下した拒否経路そのものである。
- **利用時拒否は判定器単体では負例 11/11 を拒否するが、production 配線前で実効性は部分的。** 迂回路が 6 経路残り、昇格境界が
  未設計である。「模擬 11/11 = 実効性成立」とは言えない。
- **D700 の却下理由 (i) は現在も真。** CI / cron / timer は不在で、D2002 が認める外部 scheduler も起動主体・失敗回収が決まって
  いない。決まらないまま移せば F485 の「未実行が露見しない」に戻る。
- **費用対効果は 1 session のモデル値でしか示せない。** 移動後の最遅 shard wall は α 247.2 / β 251〜254 秒、感度 228〜265 秒で、
  300 秒を切るとは断定できない (D357 / D2068)。closure A でも main の前進の約半分 (7 日で 59/126) で系列の再走が要り、同期なら
  利得が消える。
- **述語単位の重複は代替にならない。** 毎走に残る単体検査は helper を直接呼ぶか gate を stub しており、stub-free の発行・verifier
  全体・public gate・実列挙・実 ccbench 比較の結合は M 固有 (D700 の「受理集合が異なる」の具体化)。

**却下した選択肢:**

- **条件を満たす前に移し、機構を後から足す** — D2002 が F485 の再演として却下済み。
- **closure A で束縛して費用を下げる** — output の穴を持ち規律 2 に反する。closure B (A + `output`) も docs 入力・untracked・
  ccbench checkout・hold 版を表さず完全閉包ではない。
- **述語が重複している行を毎走から外す** — 表で示せた重複は述語単位で、結合検出は残る。部分削除でも受理集合を縮める (D700)。
- **T-2750 の成分粒度変更で代替する** — 負荷は均等化 (6,052.7×3) するが最長 node 240〜252 秒が残り 305〜318 秒級 (モデル値)。
  別系列化の代替ではなく、先に実測すべき独立の手である。
- **本 wave で判定器を production に配線する** — 追加 gate・検査・台帳は依頼の scope 外。
