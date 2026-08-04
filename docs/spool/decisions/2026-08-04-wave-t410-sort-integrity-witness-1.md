---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t410-sort-integrity-witness
seq: 1
---

## {{D:sort-witness-observation-equivalence}}. sort 軸 integrity witness の同値関係は因果同値でなく固定 origin 内の観測同値とする

**決定 (1): `reason` を因果の名前として扱わない。** `P <reason>` の reason は comparator の
壊れ方ではなく、producer 側の**事後検査の分岐名**である。validationPhase の検査は先に
`write_set_` の size を比べ、size が等しいときだけ `rcdptr_` multiset を比べる短絡順であり、
非反射・非対称・非推移のどの comparator 違反も「無傷 / size 変化 / size 同一だが multiset 変化」の
いずれにもなりうる。したがって comparator 法則から reason への写像は関数ですらなく、全射でも
単射でもない。reason を「同じ理由で危険」の意味キーに使うと、材料レポートと次手帰属が
実測していない機序を参照する。

**決定 (2): 閉じた観測コードへ写像する。** `size-changed` は
(size_preserved=false, rcdptr_multiset_preserved=NOT_EVALUATED)、`rcdptr-set-changed` は
(size_preserved=true, rcdptr_multiset_preserved=false) へ写す。生文字列を意味キーにしない。
producer が証明したのは観測 2 点の真偽だけであり、名前から強い保証を読ませない。

**決定 (3): 同値は固定 origin 内で定義する。** D138 は cut key を origin manifest・emitter・
verifier policy・environment contract・IR schema へ束縛し、いずれかが変われば新 origin とする。
裸の `(kind, reason)` を大域キーにすると、emitter 版が変わって検査対象や意味が変わっても
同一クラスへ束ね、旧 origin の証拠が新 origin へ混入する。

**決定 (4): event と class を型として分ける。** dataclass の既定 equality と別に同値キーを
定義すると 2 つの equality が併存し、実効キーへ schedule ノイズが戻る。
発生スレッド・出現順・件数・txn 境界は class に含めない。

**決定 (5): 発生スレッドは payload でなく hint として持つ。** P 行は thread id を持たず、
`trace_<n>.log` という命名規約からの推定にすぎない。収集段で rename されれば断定は誤る。
名前に推定であることを出し、根拠を持たせ、非 canonical 名では欠測とする。
現行 parser の受理集合を変えないため parse error にはしない。

**決定 (6): 未知 reason は捨てず、意味層では fail-closed。** parser は現行どおり任意の 1 token を
受理して counter へ載せる (受理集合不変)。ただし「既知語彙に属さない」ことを構造として保持し、
還流 adapter は未知 reason を契約エラーとする。観測後に新しい危険クラスを自動生成すると、
事前登録していない意味を「対応済み」として扱う経路になる。

**決定 (7): 外部露出は集約する。** 実測で P 行は 1 run あたり最大 879,025 件に達する
(`output/env/linux-baremetal/calibration/s5_permutation_coverage.json` の swap 制御)。
1 行 1 object を WAL・critic・材料レポートへ無制限に流すと、verifier timeout・巨大 WAL 1 行・
critic context の切詰めを招く。露出は reason 別件数と bounded sample とし、
件数の定数固定を受入条件にしない。

**決定 (8): LLM 可視面は閉じた語彙にする。** trace 由来文字列は規律 6 のデータであり、
rejection 描画を通じて critic prompt へ素通しされる。判別子は既知 2 語と unknown に閉じ、
未知語は件数と bounded escaped sample として残す (黙って捨てない)。

**決定 (9): 受理集合不変の証明は実経路で取る。** 手構築した integrity object の比較では、
counter を作る parser/core 自身の変更に発火しない。parse → verify → dict の実経路を通し、
P のみ / 同一 reason 重複 / 複数 trace file / 未知 reason / 非 canonical filename / 極大件数で
旧値と比較する。

**決定 (10): 本 wave では実装しない。** verifier の全 Python が committed qualification evidence の
runtime module binding に束縛されており、witness を verifier へ足すと再束縛検査が必ず赤になる
(実測)。D107 の「後から足す側が退く」は本件では退避先が無く、正規の再束縛経路も無い。
evidence の hash 書換え・binding 検査の緩和・テストの skip は proof chain の falsification として
禁じる。実装可否はユーザー裁定へ返す。

**理由:**
- D138 は「sort 軸の同値関係」を確定していないこととして明記しており、還流契約を sort 軸へ
  適用する前提条件がここにある。実装が塞がれていても、意味契約は先に確定できる。
- 因果同値として名乗ると、producer が証明していない機序を proof chain と材料レポートが参照する。
  観測同値へ落とせば、保証していないものを保証すると書かずに済む。

**却下した選択肢:**
- 生 `reason` を大域の意味キーにする — origin 境界を破り、emitter 版差を同一視する。
- 発生スレッド・件数・順序を同値キーへ含める — schedule ノイズで同じ危険が別クラスになる。
- 未知 reason を parse error にする — 現行受理集合を変え、正しさシグナルを落とす。
- 未知 reason を観測後に新クラスとして自動採用する — 事前登録なしの意味を対応済みと扱う。
- P 行に存在しない txid・key・comparator 座標を witness へ持たせる — 実在しない情報の捏造。
- 実装を通すために evidence の binding を書き換える / 検査を緩める — proof chain の falsification。
- 本件を「実装しない」で恒久的に閉じる — 表現層の発火実績は実在し、塞いでいるのは
  binding の射程であって witness の必要性ではない。
