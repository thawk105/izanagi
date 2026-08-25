---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1669-floor-ledger-recovery
seq: 1
title: [T-1669] 床値の marker からの ledger 復旧と、検証済み recovery 後の次 ordinal 認可を admission で閉じた。設計は段 3 の敵対 2 レンズが親の暫定裁定を否定して差し替わった (コード + テスト、branch worktree-dev-wave-t1669-floor-ledger-recovery、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

**段 1 で 2 つの行き止まりを repo 外 probe で再現した。** marker だけ在って ledger 行が無い状態で
入場券を使い直すと `attempt ticket was already consumed` で拒否され、その cell は二度と測れない。
規約どおりの再試行申請を書いても `retry attempt lacks its canonical failed planned trigger` で
拒否される。床値経路には n-pilot 経路にある marker からの ledger 再構築が無いことも現物で確認した。

**段 3 の敵対 2 レンズが独立に親の暫定裁定 (P1) を否定し、採用した。** 親は「復旧の記録を
admission 側の journal に置き、それを次 ordinal の根拠にする」と暫定裁定していた。2 本とも
別々の道筋で「それは『前の attempt は放棄された』という状態主張であり、D796 が禁じた二重権威に
なる」と結論した。payload に terminal status も失敗理由も持たせなくても、次 slot を開く根拠に
した時点で状態主張になる、という指摘が決め手だった。差し替え後は復帰手順書の真偽表を
そのまま実装する形になり、cut 6 (同一 attempt の再発行) と cut 10 (registry の検証済み recovery)
を**分けたまま**閉じた。詳細は {{D:floor-cut6-reissues-same-attempt}} と
{{D:floor-next-ordinal-needs-registry-recovery}}。

**段 6 の敵対 2 レンズが、焦点走が全緑のまま「実装が production 経路から一度も呼ばれない」ことを
独立に検出した。** 再開処理が `session-start` のある seq を forward-only で飛ばすため復旧の
入口へ到達せず、再試行 producer も新しい根拠を読まなかった。新設テストが低層 API の直接呼出し
だったため到達不能を隠していた。これは {{F:green-focus-run-hid-unreachable-implementation}}。

**規律 2 に触れる穴も 1 件あった。** 「検証済み recovery」の信頼の根を、検証対象の受領証自身から
採っていた。任意の authority で自己整合させた registry が受理される形である
({{F:verified-artifact-chose-its-own-trust-root}})。admission に pin した許可集合を導入し、
今日は空集合にして production では fail-closed で発火しないことをコードで強制した。
登録先は scheduler accounting collector を作る作業である。

**親の裁定が招いた退行と行き止まりが 2 件出た。** 「消費側と最終検査側に同じ厳しさを」という
指示が、(a) 候補を絞ってから数える形を生んで受理集合を広げ
({{F:narrowing-candidates-before-counting-widened-acceptance}})、(b) 「最新の retry start で
あること」を履歴の再検査にも課して、連鎖 recovery の正当な履歴を全部落とした
({{F:same-gate-both-sides-broke-valid-history}})。後者は**静的レビュー 3 本が検出できず、
親のテスト実走だけが赤にした**。恒久対応は {{D:same-gate-different-time-is-not-asymmetry}}。

**fix は 3 巡で収束した** (上限どおり)。1 巡目が到達不能と authority pin、2 巡目が退行の巻き戻しと
retry 側 cut 6、3 巡目が時点依存述語の分離。

**変異は probe 相で 3 件生存し、テストの穴だった。** 注入の実在 (置換対象 1 箇所・差分 hash 相異・
rc=0) を確認したので等価変異ではない。実装を 1 byte も変えず負例 3 関数を足して閉じ、本走で
9/9 KILLED にした。生存の型と erratum は
`output/insights/2026-08-25_t1669-floor-ledger-recovery-mutation.md`。
段 6 のレビューが現物で判定した「前後の層に吸収されて単一理由性を持たない」7 件
(A1 / A3 / A4 / A5 / A7 / A8 / B6) は `DW-M01` に従って登録を取り下げ、実効 gate へ再照準した。

**親の段 4 裁定文の記述を 1 件訂正する。** 「D796 を 1 mm も動かさない」は、旧 `valid=False` 経路と
registry の空 `retryable_failure_reasons` の**既存の**不整合まで解消したように読める。
本 wave はその不整合を増やさないだけである。段 6 のレビューの指摘どおり親の記述が過剰だった。

**scope 外として裁定へ返す項目が 5 件ある** (下記 `次の一手` の新規 3 件と、既出の 2 件)。
同一 UID からの marker / journal 偽造は、現行コードでも consumed marker を削除すれば同じ attempt を
無制限に測り直せるため**本 wave が攻撃面を広げてはいない**ことを親が裏取りした。
partial append からの復帰不能も既存かつ普遍 (`_read_run_journal` と `_read_ledger` が
truncated final row を無条件拒否する) で、あらゆる追記に成立する。

## 次の一手差分

### 完了

- [T-1669] 床値の marker からの ledger 復旧と、検証済み recovery 後の次 ordinal 認可を
  admission 側で閉じた。cut 6 は同一 attempt を再発行し retry 枠を消費しない。cut 10 は
  registry の検証済み recovery を trigger として受理する (authority の許可集合は空なので
  今日は fail-closed)。変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0。
  remaining: none
  base: 9eb39215e27dc814383399f20bea95d6ce606e125a83018dfffd41c908656100

### 新規

- {{T:floor-admission-trusted-writer-boundary}} **P2・新規**: admission の marker・journal・
  ledger は同一 UID から書き換えられる。consumed marker を消せば同じ attempt を無制限に
  測り直せる状態が現行でもある。trusted writer 境界の設計を裁定する。
  本 wave はこの攻撃面を広げていないことを実測で確認済み。
- {{T:floor-partial-append-recovery}} **P2・新規**: `_read_run_journal` と `_read_ledger` は
  truncated final row を無条件で拒否する。追記の途中で電断すると journal も attempt-ledger も
  以後すべて拒否され、cell が永久に失われる。あらゆる追記に成立する既存かつ普遍の穴であり、
  create-only record か長さ / hash 境界を持つ修復可能形式への移行を裁定する。
- {{T:dev-wave-reachability-lens-has-no-home}} **P3・新規**: 段 8 の自己改善で
  「実装が production 経路から到達するかをレンズに答えさせる」を dev-wave の正本へ入れようとして
  収容先が無かった。`DW-S06-A` へ 1 文足すと L1.5 予算を 115 bytes 超え、条件成立時に読む
  `DW-O26` は節全体が exact 契約で pin されているため実装面の追随が要る。契約の
  「意味等価にできなければ変更を止めてユーザー裁定へ返す」に従って止めた。
  収容先を既存記述の削減で作れるか、pin を更新するかを裁定する。
  規則自体は {{F:green-focus-run-hid-unreachable-implementation}} の恒久対応に残してある。
- {{T:floor-legacy-retry-vs-registry-retryable-set}} **P2・新規**: 旧 `valid=False` 由来の
  retry と、registry の空 `retryable_failure_reasons` は意味論が食い違ったままである。
  旧経路を廃止すると既存 campaign の受理集合が変わるため、移行の順序と互換境界を裁定する。
  併せて retry 枠を使い切った cell の cut 10 復帰規則も決める。
