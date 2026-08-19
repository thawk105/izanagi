# クロスプロトコル対応 (TicToc/Cicada) のタスク定義 — 実装しない裁定 (2026-08-20)

- **wave 種別:** `/dev-wave クロスプロトコル対応で、TicToc, Cicada対応をタスクとして定義してほしい`。
  ユーザーは明示的に「このdev-waveで一気にやるつもりはない (規模がデカすぎる)」と範囲を限定した。
  段 4 で **実装しない** と裁定し `4→7→8→9` を採った。
- **実装差分:** なし (コード 0 byte、docs のみ)。変異 matrix は対象外 (`DW-S04`)。受入全走は免除されないため別途実施し、結果は worklog に記録する。
- **基準 commit:** `f5677a66`。branch `worktree-synchronous-orbiting-harbor`。
- **成果物:** 本 insight (技術調査 + タスク分解) + `docs/phase3.md` 後続段item 7 の拡張。新規 T 番号は発行しない (理由は §7 冒頭)。

---

## 1. 依頼の分解 — 「クロスプロトコル対応」は 2 つの独立した strand

このプロジェクトの「クロスプロトコル対応」は、実は技術的に独立した 2 つの取り組みを指しうる。
ユーザー依頼の「TicToc, Cicada 対応」がどちらを主眼にしているかは本文からは一意に決まらないため、
両方をタスク化した上で明示的に区別する。

| strand | 中身 | 何を verify するか | 主な参照 |
|---|---|---|---|
| **S1 (native trace-hook)** | TicToc/Cicada 自身のネイティブ実行を verifier に通す | TicToc/Cicada 自身のコード | `docs/phase3.md:272` (must 表)、headline 2 定義 (`docs/phase3-main-experiment.md:19-28`) |
| **b2 (カタログ化→移植)** | TicToc/Cicada の最適化技法を **silo の EVOLVE-BLOCK** へ着想移植する | 依然として silo (既存 trace-hook で足りる) | D32 (`docs/decisions.md:709-729`) |

S1 は主実験 headline 2「クロスプロトコル stock 最良 (mocc/tictoc/cicada 等の同一 workload 最良)」
(`docs/phase3-main-experiment.md:27`) の前提であり、「trace-hook の無い protocol は verify 不能で
COMMIT に到達しない」(`docs/phase3.md:272`) ため、TicToc/Cicada を stock 比較対象に使うにはまず
これらを verify 可能にする必要がある。b2 は roadmap 層2(b) の「他 CC の最適化を CCBench コーパスから
移植する」で、**対象が silo の EVOLVE-BLOCK である点が S1 と異なり、TicToc/Cicada 自体を verify
可能にする必要がない** — アイデアの出所として読むだけで、silo 側の既存 gate 一式がそのまま効く。

D32 はこの 2 つを「cicada/oze への空間拡大 (**S1 移植を伴う**) と束ねるのが自然」としてまとめて
段7 に予約しているが (`docs/phase3.md:389`)、実装コストは非対称 (b2 は S1 の blocker をほぼ踏まない)
ため、下記 §7 では両 strand を別グループとして分解した。

---

## 2. 現在の gate 状態 — 段7 (cross-protocol) はまだ発火していない

- **D32 (2026-07-03 ユーザー承認):** 移植 (b2) を「主実験後の拡張予約」に降格し、着手時の一歩目を
  「カタログ化の試作 1 枚」と定めた (`docs/decisions.md:709-729`)。phase3.md 後続段item 7 が
  同じ内容を「(8b + 層3の後に再判断)」として保持している (`docs/phase3.md:35`, `:382-390`)。
- **現状 (2026-08-19 worklog 末尾 (713) 時点):** 8c (workload 駆動セッション非依存化) は
  bounded MVP 実装済みだが正式実験・resume は未完で、直近 wave は段8c 正式系列の起動条件
  (§6 前提条件 1〜12) の棚卸しに費やされている (`docs/worklog.md:3387-3442`)。層3 は
  事実層 v2 まで完了だが機序仮説層は設計凍結のみで実装は v3 に繰延 (`docs/phase3.md:510-517`)。
  すなわち **「8b + 層3の後」という発火条件はまだ満たされていない。**
- `DW-G04` (条件付き機能の発火 gate) に照らすと、発火条件を満たす artifact path / 計測 ID を
  今 brief に書けないため、**今回書けるのは設計メモ (タスク定義) までである。** これが
  「今回は実装しない」裁定の直接の根拠であり、ユーザーが指定した「規模が大きいので一気にやらない」
  という制約とも一致する。

---

## 3. [T-109] (2026-07-26) precedent — MOCC 1 protocol だけの生死実験が 3 レンズ全て NO-GO だった記録

過去に一度、cross-protocol trace-hook 移植 (S1 strand) の実装可能性が調査されている。対象は MOCC
(TicToc/Cicada ではない) で、段 2 プラン + 段 3 敵対レンズ 2 本のすべてが **NO-GO** と判定した
(`output/insights/2026-07-26_s1-cross-protocol-gate-survey.md`、逐語 =
`output/insights/2026-07-26_s1-cross-protocol-consultations.md`)。TicToc/Cicada は protocol が
異なるが、S1 strand を塞いでいた構造的 blocker の大半は protocol 非依存 (buildcache/gate/qsub 権限の
話) であり、今回の TicToc/Cicada タスク定義に直接転用できる。**今回、各 blocker の現状 (2026-08-20)
を実測し直した:**

| # | T-109 (2026-07-26) 時点 | 2026-08-20 実測結果 |
|---|---|---|
| D16 trace-hook の配置 | 却下 (branch 必須、out-of-tree patch は却下対象) | **一部解消。** 2026-07-26 のユーザー裁定で D16 に「一回限りの試作例外」が追記された — cross-protocol 対応の**最初の trace-hook 試作に限り** out-of-tree patch を認める (`docs/decisions.md` D16 追記)。**射程は試作 1 回限り**であり、TicToc/Cicada のどちらか片方だけがこの例外を使える。二本目は本採用 (branch 移送) を要する |
| D87/D86(3) — AI は `qsub` しない | 絶対禁止 | **不変。** `docs/decisions.md` D87(1): 「実 submit artifact ID の確認は人間の明示 qsub を待つ。AI は qsub しない」。correctness run の実測はいつも人間手番 |
| buildcache/`source_digest` の ALLOWLIST | silo 専用 3 件のみ、mocc patch を拒否 | **不変 (今回 grep で再確認)。** `orchestrator/campaign/source_digest.py:79,82`: `EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")` / `ALLOWLIST = frozenset({"cmake/Options.cmake", "include/backoff.hh", "cc/silo/transaction.cc"})`。TicToc/Cicada の hook も同じ理由で拒否される |
| D23 — `Options.cmake` の preprocess digest gap | 「cicada/oze 拡張で protocol 写像が load-bearing になった段へ繰延」(潜在リスクとして先送り) | **その段が実質今にあたる。** `docs/phase3.md:1395-1402` が cicada 拡張を名指しで trigger 条件にしている。TicToc/Cicada の buildcache 対応に着手するなら D23 の恒久解 (identity 側を hook 非依存にする) も同時に片づける必要がある |
| [T-088] との実行順序 | 承認済み・未実行の human turn を新規ファイル追加が割る懸念 | **この特定の懸念は解消済み。** 床値実測 ([T-011]) は 2026-08-12 に完了し、後続 wave も多数 land している (`docs/phase3.md` checkpoint 該当箇所)。ただし「新規ファイルが `clean_scan_digest` の preimage を変える」という一般的な教訓自体は今も有効 — 次に承認待ちの human turn がある局面では同じ点検が要る |
| SPACES へのprotocol登録 + calibration + between-run floor | 未着手・休眠 | **不変。** 既存の段6 dormant (b) と同一項目 (`docs/phase3.md:359`)。TicToc/Cicada 双方に要る共有基盤 |
| `Integrity.clean()` の非対称ゲート (silo 専用 2 カウンタ) | 未解決 (所見 A-5) | **不変。** `lock_coverage_violations`/`permutation_violations` は silo の `#if TRACE` assert だけが emit する (`orchestrator/verifier/model.py:101-142` の 9 カウンタのうち 2 つ)。新 protocol に同等の lock/version 保持 assert を設計しないと、同じ壊れ方でも protocol によって受理集合が非対称になる |

**結論:** D16 は緩んだが、buildcache/source_digest の protocol 非対応という**最も重い blocker は
今も残っている**。TicToc/Cicada のどちらであっても、S1 strand の実装に先立って共有基盤
(下記タスク (a)(c)) を解消する必要がある。

---

## 4. 並行稼働中のセッションへの注意 (2026-08-20 時点)

本 wave 開始時点で `trace v2 protocol mocc migration` という別セッションが並行稼働している
(`ListAgents` 実測、未 land)。名称から MOCC の trace-hook 移植 (T-109 と同じ対象、S1 strand) に
取り組んでいる可能性が高い。local main には 2026-08-20 時点でまだ mocc/tictoc/cicada 関連の commit
は無い (`git log` 実測、直近 30 commit に該当なし)。

**下記タスク (a)(c) (buildcache 拡張、Integrity 非対称ゲート解消) は MOCC 向けに同じ設計判断を
要る可能性が高い。** 着手前に main の該当 land 結果を確認し、二重実装を避けること。既に解決済みなら
その設計をそのまま TicToc/Cicada へ適用するのが最短経路になる。

---

## 5. TicToc の技術構造 (直接ソース確認、2026-08-20)

- 版 ID は `TsWord{lock:1, absent:1, delta:15, wts:47}` の bit-packed union。単一版
  (`external/ccbench/cc/tictoc/include/tuple.hh:13-38`)。`rts() = wts + delta` (同 `:37`) —
  validation の read-timestamp 拡張は **delta の前進だけで新しい物理版を書かない**。
- 構造としては silo/mocc に近い「1 tuple = 1 現在版の bitfield」型の単一版 OCC であり、
  [T-109] の MOCC 版 ID 移植 playbook (§1.3〜1.4 の read/write set 写像設計) をテンプレートとして
  転用しやすい。
- **未検証 (次のタスクで確認要):** rts 拡張パスが trace-hook の「新版 = 新 commit」という前提と
  衝突するかどうかの実地確認。旧 [T-109] 逐語 (`output/insights/2026-07-26_s1-cross-protocol-consultations.md:40`)
  は `cc/tictoc/transaction.cc:425-440` 付近の挙動を「推測」と明記しており、本 wave でも実装コードの
  読解までは行っていない (今回確認したのは `tuple.hh` の構造のみ)。

## 6. Cicada の技術構造 (直接ソース確認、2026-08-20 — [T-109] では未分析)

[T-109] は mocc/tictoc/ermia の版 ID 表現だけを比較し、cicada は分析していない
(`output/insights/2026-07-26_s1-cross-protocol-gate-survey.md:37-43` の表に cicada の行がない)。
今回初めて構造を確認した:

- **真の多版 (MVCC)。** 各 tuple は `Version{rts_, wts_, next_ (linked list), status_}` の連結リストを持つ
  (`external/ccbench/cc/cicada/include/version.hh:25-38`)。`status_` は
  `{invalid, pending, aborted, precommitted(now unused), committed, deleted, unused}` の列挙型
  (同 `:15-23`)。
- `wts` は **ハイブリッド物理時計** から生成される。`ts_ = (localClock_ << 8) | thid` で
  `localClock_` は `rdtscp()` (ハードウェア TSC) 由来 (`external/ccbench/cc/cicada/include/time_stamp.hh:24-40`)。
  silo/mocc のような epoch ベースの論理カウンタではない。
- **silo/si/mocc/tictoc が共有する「1 tuple = 1 現在版の bitfield」という前提が Cicada には成立しない。**
  read set がどの `Version` オブジェクト (連結リストの何番目) を指すかを明示しないと trace-hook の
  R/W emit を設計できない。ガベージコレクション (古い version の回収、`cc/cicada/util.cc` に実装あり)
  との相互作用も検討対象になる。

**結論: Cicada は既存 playbook (単一版 protocol 前提) の延長では書けない、構造的に新規のケースである。**
D32 が指定する「カタログ化の試作 1 枚」を Cicada に充てるなら、それは技術検証を兼ねた feasibility
調査になる — この判断は技術的合理性があり、単なる思いつきの割り当てではない。

---

## 7. タスク分解

**新規 T 番号は発行しない。** 段7 の発火条件 (D32 = 8b+層3後) が現時点で成立しておらず、
`docs/phase3.md` 後続段 item 7 は既に (T 番号を持たない) 登録済みの予約項目であるため、
下記タスクは T 番号レジストリ (D70) ではなく item 7 自身のプロース内 lettered sub-item として
`docs/phase3.md` へ追記する (段6 dormant (a)-(j) と同型の扱い)。段7 が発火した時点で、これらの
sub-item から着手順に dev-wave を切り出す。**各項目は概ね 1 dev-wave 規模になるよう分割してある。**

### Group A — 共有基盤 (S1 strand、TicToc/Cicada 双方に必須)

- **(a) buildcache/`source_digest` の protocol-aware 化。** `ALLOWLIST`/`EVOLVE_BLOCK_SOURCES`
  が silo 専用 3 件に固定されている制約を解消し、観測者効果二重検査 (diff-of-diffs、TRACE=0 の
  `nm` symbol 検査) を新規 protocol の trace-hook にも効かせる。D23 が「cicada/oze 拡張で load-bearing
  になった段」に明示的に予約していた繰延先がここ (`docs/phase3.md:1395-1402`)。§4 の並行 mocc
  migration セッションの結果を先に確認すること。
- **(b) SPACES への tictoc/cicada 登録 + protocol 別 calibration + between-run floor 対象別再実測。**
  既存の段6 dormant (b) (`docs/phase3.md:359`) と同一項目。統合先はここ。
- **(c) `Integrity.clean()` の非対称ゲート解消設計。** `lock_coverage_violations`/
  `permutation_violations` が silo 専用 emitter 由来である問題 ([T-109] 所見 A-5)。新 protocol に
  同等の lock/version 保持 assert を設計しないと、同じ壊れ方でも protocol によって受理集合が
  非対称になる。TicToc (単一版) と Cicada (多版) では設計がおそらく別物になる。
- **(d) D16 一回限りの試作例外を TicToc/Cicada のどちらに使うかのユーザー裁定。** 射程は 1 回限り
  (§3 表)。§8 (P1) に親の暫定推奨を記載。

### Group B — TicToc (S1 strand)

- **(e) 版 ID (`TsWord`) の trace-hook 設計。** §5 で「未検証」と明記した rts 拡張パスの実地確認を
  含む。[T-109] の MOCC playbook (`output/insights/2026-07-26_s1-cross-protocol-consultations.md`
  §1) を出発点として転用する。
- **(f) trace-hook 実装 + positive control。** [T-109] §4 型 (W mismatch / lockskip / early-unlock
  相当) の故障注入を TicToc 向けに設計する。(a)(c)(d)(e) の後。

### Group C — Cicada (S1 strand)

- **(g) MVCC 版管理の feasibility 調査 (D32 のカタログ化試作 1 枚をここに充てる)。** Version chain
  上のどの version を read/write として emit するかの設計。既存 playbook 非依存の新規調査であり、
  他のどのタスクよりも先に「そもそも Cicada の trace-hook は現実的か」を判定する。
- **(h) ((g) の結果次第) trace-hook 実装 + positive control。** (g) が feasible と判定した場合のみ
  着手する。infeasible なら Cicada は S1 strand を見送り、b2 strand (下記) だけで扱う選択肢も
  (g) の出力に含める。

### Group D — b2 strand (カタログ化 → silo EVOLVE-BLOCK への技術移植)

- **(i) TicToc/Cicada の最適化技法のうち 1 つをカタログ化試作。** 前提/効果/競合の三つ組
  (D32 原文、`docs/decisions.md:709-729`)。**Group A の blocker を一切踏まない** — 対象は
  silo の既存 EVOLVE-BLOCK/trace-hook のままなので、既存 gate 一式がそのまま効く。D32 が指定する
  文字通りの「一歩目」であり、本分解の中で最も安価に着手できる。ただし I5 警告
  (「異なる実装の混合は深い分析には不適切」という CCBench 著者の警告、related-work 参照) に注意し、
  「移植」ではなく「着想を得て silo の文脈で再設計する」水準で扱う。

---

## 8. (P1) 親の暫定推奨 — 攻撃対象、ユーザー上書き可

**推奨順序: (i) → (a)(b)(c)(d) → (e)(f) [TicToc] → (g) → 分岐 [Cicada 着手 or 見送り]。**

理由:
- (i) は既存 gate 群を一切踏まず着手できる最安の一歩で、D32 が指定する「一歩目」そのもの。
  Group A〜C のどの裁定にも先行して独立に進められる。
- TicToc は既存 (mocc/silo) playbook に構造的に近く (§5)、共有基盤 (a)(c) の実地検証として
  Cicada よりリスクが低い。D16 の一回限り試作例外も TicToc に先に使うのが筋が良い — これは
  `DW-G03` (族一般化には独立 2 例) の精神と整合する: 1 例目 (TicToc) で共有基盤を検証してから
  2 例目 (Cicada) で真の汎用性を問う。
- Cicada は真の MVCC で既存 playbook が通用しない (§6)。TicToc で基盤を検証した後の「独立 2 例目」
  として位置づける方が、共有基盤の設計ミスを Cicada の特殊性に帰属させてしまう事故を避けられる。

この推奨は暫定であり、ユーザーが順序を入れ替えても Group A〜D の分解構造自体は変わらない。
特に「TicToc/Cicada のどちらを先に D16 試作例外へ充てるか」(d) は一方向の消費 (射程 1 回限り) を
伴うため、実際に (d) へ着手する時点で改めてユーザー裁定を仰ぐこと — 本 wave の推奨はその場の裁定を
代替しない。

---

## 9. 見なかったことにしていない前提

- 実測 (correctness run を含む一切の Pegasus job 投入) はすべて人間 `qsub` 手番であり続ける
  (D87/D86(3)、不変)。上記タスクのうち実行を伴うものは、どれだけ設計が煮詰まっても最終的に
  人間の qsub を待つ。
- 段7 自体の発火条件 (D32 = 8b+層3完了) が充足したかどうかは、本 wave では判定していない。
  worklog 末尾 (713、2026-08-19) 時点で 8c 正式系列の起動条件棚卸しが進行中であり、8b+層3 完了の
  確認は別途 (worklog 末尾を再確認する) 必要がある。
- 本タスク分解は「対応させる」ことの実現可能性を評価したものであり、対応させる**べきか** (研究上の
  価値が投資に見合うか) の判断は含まない。D32 の非対称性の論理 (移植は未検証仮説、空間外合成は
  実証済み) は本 wave でも覆していない。
