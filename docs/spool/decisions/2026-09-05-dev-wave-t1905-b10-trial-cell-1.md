---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-t1905-b10-trial-cell
seq: 1
---

## {{D:b10-d1509-decision2-revised}}. D1509 決定 2 を改訂し、read-heavy の道を選ぶ前提だった「安い実行 1 回」の要件を外す

**決定 (D1617 の実施):** D1509 決定 2 の「read-heavy を通す道は、先に律速の内訳と資源を測る
安い実行を 1 回行い、その結果で選ぶ」を改訂し、**安い実行 1 回の要件を外す。** 改訂の理由は
新事実であって要件の充足ではない。道 1 (直列性検査の並列化) が main へ着地し、
道 3 (事前登録を緩める) は規律 2 が禁じているため、選択肢が道 2 (壁時計 24 時間、D1605) の
1 つに潰れた。**打ち切られた campaign の記録から取った実測で要件を満たしたとは書かない。
D1605 の「測定を行ったうえで道を選んだとは主張しない」はそのまま残す。**

**理由:**
- §5.1 の 5 量のうち 2 量しか得ていない記録は規律 7 のうえで「測定済み」と扱えない。
  要件が不要になったなら、満たしたと見なすのではなく決定の改訂として記録する方が、
  後から読む者に正確である (D1617 の理由 1)。
- 決定 2 の目的は「測る前に道を選ばない」ことだった。道が 1 つしか残らない状況では
  選ぶ行為そのものが無く、要件が守ろうとした対象が消えている。

**却下した選択肢:**
- 既存記録からの実測で決定 2 を「満たした」と記録する — 5 量のうち 3 量は成果物に残らず、
  D1605 の主張しない範囲と矛盾する。
- 決定 2 を残したまま read-heavy を投入しない — 論文の read-heavy 正式値が無いまま残る。

## {{D:b10-trial-cell-identity-and-balanced-legacy}}. B-10 の 1 セル試し打ちは formal と別 campaign 同一性で通し、balanced 45 セルは系列限りの digest 集合で集約に残す

**決定:** D1617 (2) と D1480 条件 2 を driver の実行面で満たす形を次のとおり確定する。

1. **試し打ち phase `trial-cell` は本走の driver 本体 (build → 全 verify path → 認証 → perf binary の
   SHA 照合 → 測定 → cell 記録 → trial 専用 report) を 1 変種・1 cell で通し、campaign 同一性を
   `search_tag=trial` と submission nonce で formal から分ける。** report は write-heavy 旧系列・
   balanced 旧系列・read-heavy 現行 formal の 3 campaign しか読まず、試し打ちの記録・WAL・lock・
   trial report は正式系列にも事前登録の判定にも入らない。
2. **試し打ちの cell は block-1 の登録順で最初の登録 shape cell** (reference 3 点を除く。
   現 spec では index 3 `constant-mu2`) とし、値でなく規則を実装する。共通の実行機構に加え
   patch の hole 式経路も 1 回通るためで、`none` (BACK_OFF=0) では後者を踏まない。
3. **試し打ちの成功は自己申告で閉じない。** 試し打ち campaign に既存 record があれば止め
   (再投入は新 nonce = 新 campaign)、exact 1 record であることに加え、record の digest が今回
   書いたものと一致し、`build_attempt_id` と `performance_binary_sha256` が同 job の WAL certified
   attempt と一致し、request ID・nonce・receipt SHA が今回の submission と一致するときだけ rc 0 とする。
   campaign 同一性に nonce を入れるのは、固定 ID だと create-only の missing record が再投入を
   永久に失敗させ、逆に古い成功 record だけで新 job が rc 0 になりうるためである。
4. **balanced 45 セル (campaign 143a3f74、driver bytes sha256 f6246360…) は D1597 の形で集約に残す。**
   campaign ID・旧 analysis commit/sha・旧 binding sha・45 件の内容 digest の exact 集合・45 cell の
   exact 一致を balanced 専用の validator で要求し、write-heavy の validator (execution_host 不在を
   要求し射影する) とは共通化しない。任意 workload を受ける一般 validator や fallback は作らない。
5. **`trial-cell` の workload は登録 workload 一般** (verify/perf と同じ要件)。trial report に
   phase と workload を明示し、read-heavy の投入前提には read-heavy の試し打ち成功だけを使う。

**理由:**
- 設計 §5.2 は試し打ちを「正式系列の一部ではなく、事前登録の判定にも入らない」と定めており、
  同一 campaign へ書いて formal が 44 cell を resume する形は、D1480 条件 1 の「認証と測定を
  同一 job で行う相」と exact-45 の意味を壊す。
- D1597 は「driver を編集するたびに同じ形の限定受理を新しく書く」と定めている。balanced は
  その 2 例目であり、2 例目で一般規則へ畳むと受理集合が暗黙になる。
- 段 3 の敵対相談 2 本が独立に、trial 専用 report の欠落と成功述語の自己申告性を real と指摘し、
  段 6 のレビューが事前配置 record による偽成功を real と指摘した。いずれも親が採った。
- D1480 条件 2 は残り workload 一般の条件であり、D1617 が禁じたのは「balanced の完走を read-heavy の
  試し打ちの代替にする」ことである。phase 自体を read-heavy 限定にすると、消費者の無い特例を
  phase 閉集合へ足すことになる。

**却下した選択肢:**
- 試し打ちを formal と同じ campaign へ書き、本走で 44 cell を resume する — 上記のとおり。
- 試し打ちの cell を `none` 参照点にする — hole 式経路を踏まない。
- write-heavy と balanced の限定受理を workload 引数の 1 関数へ共通化する — D1597 が却下した
  一般規則への滑りになる。
- `trial-cell` を read-heavy 限定にする (段 6 レビュー A の must-fix) — 上記の理由 4。誤認の経路は
  report の workload 明示と投入手順で塞ぐ。
- 試し打ち専用の短い壁時計枠を持つ — phase 別 request 契約の設計になり pin が広がる。
  24 時間枠のまま投げ、queue 待ちを既知リスクとして記録する。
