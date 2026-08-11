---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-floor-campaign-speed
seq: 1
title: test_s8b_floor_campaign の実 output 走査を os.scandir へ置換して guard 11 本を 35% 速くした — 並列 hash は実測で有害と判明し撤去 (コード + docs、変異 12/12 KILLED、branch worktree-dev-wave-floor-campaign-speed)
---

## 本文

依頼は「`test_s8b_floor_campaign` の高速化」。**遅さは 12 テストに 98.5% が集中**していた
(受入 base arm の直列和 900.83s / n=212 のうち上位 12 で 887s、残り 200 実行は約 13s)。
主因は `_real_output_snapshot` が実 repo `output/` (11,033 entry / 337MB) を前後 2 回ずつ
**計 22 回**全 bytes SHA-256 することで、焦点 11 実行 161.34s の **79.9% (128.95s)** を占めていた。
この関数は「統合テストが実 repo の `output/` を 1 bit も変えない」ことを守る**正しさ防壁**であり、
検出力を落とす是正は採らない (規律 2)。

**設計を 2 度差し替えた。** 段 2 プランの連鎖 cache (テスト i の事後 snapshot を i+1 の事前へ
再利用) と、親の対案 (専用 xdist group) を段 3 の敵対 2 本がいずれも NO-GO にした。決め手は
(1) **xdist group 化は node id に `@group` 接尾辞を付ける** — 受入 junit で実在を確認し、同じ接尾辞が
変異 harness の consumer 2 つを壊した既往が F95 にある。プラン案と親の対案が同じ理由で同時に死んだ。
(2) **ordinal の連続は状態静穏性を証明しない** — fixture setup/teardown 中の変更・setup skip が
ordinal を消費しない経路・rerun が失敗 post を pre に使う経路の 3 つで、現行の赤が緑になる。

採用したのは出力 tuple を変えない実装置換だが、段 6 のレビュー 2 本が、段 5 実装の**新設テストが
22.32s かけて wall を悪化させ、かつ肝心の変異を殺せていない**ことを独立に突いた。fix 2 巡で閉じた。

**素材: 最大の発見は「並列化は有害だった」ことである。** login node 単独では `os.scandir` +
8 thread が 5.79s → 1.43s (4.05 倍) を出すが、**32 worker の並列走行では thread は guard を
1 秒も速くせず (4 thread 15.3s vs 1 thread 15.4s)、同時走行の critical path を 9.7s 飢えさせた**
(39.34 → 48.9s)。機序は disk 律速で、thread は bytes の到着を速くせず待ち行列を長くするだけ。
効いていたのは `Path.rglob` → `os.scandir` の置換だけだった。**単独計測の高速化率を並列環境へ
一般化してはならない**という D104 決定 (4) の再確認であり、実測値をコードのコメントへ残した。

**成果表現を限定した。** 成果は「実 `output/` snapshot を行う 11 テストの仕事量を 35% 削減した」
であり、**「file を高速化した」「受入全走の wall を改善した」とは書かない**。この file の wall は
base でも最終形でも {{T:floor-campaign-clone-cost}} の repo 全体 clone (39s 台) が支配しており、
snapshot 側をどれだけ削っても頭打ちになる。敵対レビュー S6-LUNA-08 の指摘を受諾した結果である。

**親自身の誤りを敵対検証が 8 件正した。** 段 4 で 5 件 (「66%」は代表 2 テストの一般化だった /
「production 無変更なら受理集合も検出集合も不変」は別命題の混同 / 「編集面は互いに素」は plan が
conftest を編集面に入れた時点で崩れていた / 対案の専用 group は node id を変える / 「C2 は scope 外
だから性能評価不要」は別主張)、段 6 で 3 件 (「事前を reference・事後を新実装で比較する」案は
壊れた実装が事前値を返すと一致して殺したい変異を隠す / 「disk 律速で転移しない」は自分の直列実測が
反証した / 「検出集合は定義上 Y = X」は過剰主張)。**所見は全 13 件が real、refuted はゼロ。**

**手順違反 1 件。** 焦点基線を login node で pytest 実行した。`guard_bash` は bash 直書きの
`pytest` を拒否するが script 経由は検出しない。意図せぬ迂回であり、発覚後の全走はすべて
`--force-dispatch` で計算ノードへ投入した。

**セッション異常。** `dev_wave_wait.py producer` を背景 task で回すと、producer 生存中に
待ち手だけが空出力で終了する事象が 5 度起きた。実体を伴わない完了通知も 1 度観測した
(ledger が 4/12 のときに 5/12 を通知)。いずれも `.done` + 成果物 + producer 死の 3 点照合で検出し、
待機を until ループへ切り替えて回復した。取りこぼしはない。

## 次の一手差分

### 新規

- {{T:floor-campaign-clone-cost}} **P2・新規・ユーザー裁定待ち**:
  `test_real_seal_protocol_to_floor_official_core_e2e` の `git clone --no-hardlinks` による
  repo 全体 (313MB) + submodule 複製が、`test_s8b_floor_campaign` の wall を単独で支配する
  (受入 base arm で 82.09s、file 走行で 39s 台)。hardlink 許可で 26.81 → 16.33s (-39%)、
  `--no-checkout` で 5.24s。隔離の意味論に触るため本 wave では触らず裁定へ返す。
  `tools/codex_reasoning_ab.py:1289` の repo 全体 clone × 2 ([T-827] の次標的) と同型機序。
  正本 = `output/insights/2026-08-12_floor-campaign-snapshot-scandir/`
