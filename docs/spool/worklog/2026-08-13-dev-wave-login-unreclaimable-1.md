---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-login-unreclaimable
seq: 1
title: login admission の判定量を回収不能メモリへ変えた — 敵対レビューが ABA の fail-open を摘出し変異 9/9 一致 (コード + docs、branch worktree-dev-wave-login-unreclaimable)
---

## 本文

2026-08-12 rulings 第 6 束の追加指示 (authority: user) を執行した。判定量を user slice の
raw `memory.current` から回収不能量へ変え、{{D:login-headroom-unreclaimable}} として記録した。
**この裁定は D209 決定 3 を supersede する** — 同決定は「reclaim 可能な file cache を差し引く案は
採らない。差し引けば実効許容量はほぼ倍になるが別裁定が要る」と明記しており、今回の指示が
その別裁定にあたる。`docs/pegasus-runbook.md` §7.0 の判定量記述も同 commit で揃えた。

**着手前の実測が裁定の前提を裏付けた。** 観測時点の user slice は合計 12.66 GiB
(file 3.47 GiB、slab_reclaimable 1.70 GiB) で、天井 14 GiB − 予備 2 GiB = 12 GiB を合計が
超えるため、**要求サイズに関わらず必ず dispatch する状態**だった。同時点の回収不能量は
7.54 GiB。実装後は `run_tests.py` 自身の判定ログが
`現在使用量=13592727552、回収不能量=8092152584、判定占有量=8092152584` を出し、
4 GiB の local 予算を予約して login で実走した。**変更は実経路で効いている。**

**段 3 の敵対 2 レンズが独立に段 2 プランの blocker を摘出した。** プランは
`_parse_memory_stat` の `required` を 5 キーから `{anon}` へ縮め、既存 fail-closed テスト
1 node を削除する案だったが、これは「キー欠落で必ず dispatch」だった環境を local 可能へ変える
受理集合の拡大である。親の対案 (既存 5 キーは据え置き、新規 2 キーだけ optional) を採用した。

**段 6 レンズ A が親の対策そのものの穴を見つけた (blocker)。** 親は非原子読み取り対策として
`memory.current` を `memory.stat` の前後で 2 回読み `max(c1,c2)` を基準にしたが、stat 読取中だけ
clean cache が出入りする ABA schedule では両端が同値になり検出できず、回収可能量が基準値を
超えないため snapshot 不整合にもならない。**差だけに頼る設計が原理的に持つ穴**である。
是正として、swap 無し環境で回収不能な `anon + shmem` を下限に併用した。整合した snapshot では
差が必ずこの下限以上になるため**通常運用では発火せず、競合時だけ効く**。

**変異は 9/9 一致した。** 当初 7 本の事前登録に、新設した下限自体を壊す M8 を足した。
probe 走行で **M5 (`required` を `{anon}` へ縮小) が SURVIVED** し、実効 gate を外していたと
判明した。原因は等価性で、`required` を外しても観測組み立てが `stats["file_writeback"]` を
直接参照するため KeyError → 観測失敗 → dispatch となり受理集合が変わらない。**この防壁は
二重に効いていた。** `DW-M02` に従い実効 gate へ再照準し、プランの提案そのもの (required 縮小
+ 直接参照の `.get(..., 0)` 化) を両層同時に注入する M5b を追加登録したところ KILLED になり、
**却下したプラン案が実際に fail-open だったことが実証された**。単層 M5 は消さず
`expected_status=SURVIVED` の等価変異として登録に残した (初回結果を消さない規約)。
M1 / M3 / M4 は期待 node 集合が不完全 (実測は 3 / 6 / 2 node) で MISMATCH になり、probe の
実測値を完全集合として再登録した。

**scope 外として親が裁定パッケージへ回した real 所見が 3 つある。** (1) peak record は
「scope の raw `memory.current` peak」であり新定義とは別 metric だが、旧記録の方が大きいため
現状は fail-closed 側であり、schema 版付けは別裁定とした (診断へ metric 名の明記だけ入れた)。
(2) site 証拠不足で `OTHER` と分類されると login admission 自体を通らない件。
(3) `mutation_fanout` の certified peak policy との関係。

**brief の主張を 1 つ訂正した。** 「約 4.8 GiB まで通る」は `admit` の算術境界としては正しいが、
`MAX_LOCAL_BUDGET_BYTES=4 GiB` の cap、生存予約、前回 peak、queue/site gate が別に効くため
付与額はそこまで届かない。段 6 で実経路を実測して確定した。

**新事実: 本変更は F155 (login からの短時間 targeted 走行が cgroup scope の 1 秒 race に入る)
への露出を構造的に増やす。** 従来は判定量が天井を超えて必ず dispatch されていた走行が local を
選ぶようになるためで、実際に本 wave の再走 1 回が rc=16 になった。恒久対応は F155 既載の
`--force-dispatch` のままとし、新しい機構は作らない。

**この wave の実装タスクは rulings 第 6 束 (branch `worktree-rulings7-20260812`) 側の fragment が
placeholder として保持している。** 他 wave の slug は参照できないため本 fragment では完了扱いに
せず、当該 branch が land する際に済みとして畳むこと。

工数は Codex 8 本 (plan / consult 2 / author / fix 2 / review 2、いずれも `gpt-5.6-sol` 系、
effort は plan・consult が max、author・fix・review が high)、変異 18 run、焦点走 4 回。
**段 3 の初回 2 本 (計 約 30 分・約 750 万 token) は Web 検索で全損した** — 検索イベント行の
重複 key が `stdout_invalid` を立て `evidence_status=invalid` になり、`codex_exit_code=0` で
13,969 bytes の成果物があったのに `-o` はゼロだった。prompt へ検索禁止を明記して再走した。
実装子・fix 子はいずれも sandbox で pytest を走らせられず (予約 lock が read-only、dispatch も
`qstat` が `API EACCTAUTH`) 正しく「実装済み・未実走」と申告し、緑は親が計算ノードで確定した。

## 次の一手差分

### 新規

- {{T:login-peak-metric-schema}} **P3・新規**: local 予算の peak record に metric/schema 版を付け、
  旧 raw-current peak と新定義を混ぜない。現状は旧記録の方が大きく fail-closed 側なので緊急性は
  低いが、無標識のまま定義が増えると監査できなくなる。{{D:login-headroom-unreclaimable}} の
  scope 外として段 4 で分離した。
- {{T:login-site-other-admission-bypass}} **P2・新規**: site 証拠 (qsub/qstat、`/opt/nec/nqsv`) が
  取れず `OTHER` と分類されると login admission を通らずに local 実行へ進む。判定量の定義に
  関わらず効く経路なので、分類失敗時の既定を裁定する。
