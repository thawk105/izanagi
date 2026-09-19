---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: dw-a1-sized-attempt2
seq: 2
---

## {{D:a1-sized-attempt-0002-refused-at-submit}}. A-1 sized attempt-0002 の 1 attempt 認可は既存 submit 経路の gate で停止条件に達し、gate を緩めずに裁定パッケージへ返す

**決定:** ユーザー裁定 (2026-09-19) は A-1 balanced5 sized study (`paper-story-a1-20260901-balanced5-sized-v1`) の attempt-0002 を
独立再現として 1 attempt 認可した (非認証 lane 維持、formal 昇格なし、どこかの層で落ちたら再投入せず報告して止める)。
既存 submit 経路を 1 回実走したところ、`_assert_no_prior_v3_bench_start` が qsub の前に
`prior attempt reached the bench barrier; group rerun is prohibited` で拒否した。次のとおり扱う。

1. 停止条件に達したとして再投入しない。計測 attempt は開始されておらず (intent・attempt root・qsub いずれも未作成)、durable base・
   attempt-0001 の証拠・公開 leaf・事前登録・policy・source 契約の bytes は不変である。
2. この gate は commit `abff80d1b` が「分割で開く規律 2 の穴 (測定済み workload の再投入) を塞ぐ」ために入れた防壁であり、
   認可済みの独立再現と失敗後の再走を区別する入力を持たない。本 wave は gate の緩和・先行 attempt の証拠の移動や削除・policy / durable base の
   変更のいずれも行わない (絶対規律 2、DW-STOP)。
3. 認可された実行手続は submit 層で停止条件に達したので、同 study の次の投入には改めて認可が要る (D2120 項 3 と同じ形)。
   「qsub に達していないから同じ認可で再度 submit してよい」とは読まない。
4. 同 study の 2 本目を投入可能にする経路は本 wave の scope 外であり、設計択一 (択 1 = exact な認可記録を入力に取る gate 解除、
   択 2 = 別 study として登録、択 3 = 行わない) と推奨 (研究目的を「同一配置の反復」と確定し択 1 を 1 attempt 限定で) を
   `output/insights/2026-09-19/a1-sized-attempt2/README.md` §7 の裁定パッケージとしてユーザーへ返す。AI は自律採用しない。
5. results 系列稿・2 attempt の並記・図は測定値が無いので作らない。attempt-0001 稿の限定 L-A1S-4 は残る。

**理由:**

- 拒否は driver の gate による構造的なものであり、環境 (queue・node・hydrate・pin) ではない。投入前照合 21 項目はすべて成立していた。
- gate の受理集合を広げる変更は規律 2 由来の防壁の保護範囲を変えるので、AI の裁量で行わない。相談 3 本 (正しさ境界・手順・パッケージ点検)
  のいずれも「今回だけ通す」案を支持しなかった。
- 拒否を予測でなく実走で確定した (F29 型の回避)。実走は intent 書込と qsub の前で止まるので副作用が無いことを code と現物で確かめた。

**却下した選択肢:**

- 先行 attempt の barrier 証拠を base から退避して submit を通す — 証拠の改変で gate を迂回する形。
- submit-tree を attempt-0001 と同じ commit に置いて materialize の排他公開先を通す — submit 層で拒否されるため到達しない。
  また事前登録 §6.1 の「一度しか作れない宛先」の意味を tree の選択で迂回する疑いが残る。
- policy の durable base / 公開先を変えて別 base に attempt-0002 を置く — policy の bytes は事前登録・source 契約・driver 定数が束縛しており、
  束縛の全面改版になる。
- 本 wave で gate に認可入力を実装する — 「既存 submit 経路」「追加 gate は scope 外」の裁定に反し、規律 2 由来の防壁の変更には
  ユーザーの明示裁定が要る。
