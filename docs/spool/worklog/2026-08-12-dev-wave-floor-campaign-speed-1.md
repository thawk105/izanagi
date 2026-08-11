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

**受入全走は 2 failed / 9127 passed / 20 skipped (560.13s、計算ノード dispatch)。
本 wave の対象 file は赤ゼロ (216 テスト全緑) だが、`test_t793_report.py` の 2 node が赤で
land を停止した。** 赤は main 由来である。両テストは `docs/decisions.md` を読み D291 を
supersede する決定 ID が `("D292",)` ちょうどであることを固定しているが、2026-08-12 に
**D305 が land され** `("D292", "D305")` になった。帰属は機械確認済み — `docs/decisions.md` の
最終変更は main 側の land fold、テストを追加した commit と D305 の fold はどちらも main の祖先、
私の 4 commit は当該テストが読む file を 1 つも触っていない。**単独再走でも同じ 2 node が
再現した (2 failed / 7 passed、rc=1) のでフレークではない。** 所有者は T-139/公表層 wave であり、
凍結境界により親は他 wave 所有の実装面を直さない。**推奨は「scan 対象を live な
`docs/decisions.md` でなく凍結 bytes へ固定する」** — D305 自身が
「payload は `F_p` の実 bytes を毎回読んで導出する」と決めており、test が live 台帳を
読んでいること自体が D305 と食い違う。期待値へ D305 を足すだけの対症療法では、
次に D291 を参照する決定が入るたびに再発する。

**ユーザー裁定 (2026-08-12、逐語「既存の赤は免除リストに入れて」) により、既知赤 waiver W2 を
新設して land した。** W1 (F96/F101) は `[T-407]` の land で失効済みで、直近の専用 wave
(archive 395) が「赤いまま免除されているテストは 1 件も無い」ことを確定していたため、
本 W2 が現時点で唯一の既知赤 waiver である。**F101 の恒久対応 (赤を観測したら停止判断の前に
worklog を赤 node 名で検索して成立済み waiver を確認する) を親は当初実施しておらず、
ユーザー指摘で是正した。F101 の同型再発である。**

### 既知赤 waiver W2 (本エントリが条件と失効の正本)

- **対象 node は次の 2 件ちょうど。** これ以外の赤には一切適用しない。
  - `orchestrator/tests/test_t793_report.py::test_deny_only_report_contains_authority_and_both_submission_denials`
  - `orchestrator/tests/test_t793_report.py::test_actual_head_d292_reference_is_reported_fail_closed`
- **原因の釘付け**: 両 node は live な `docs/decisions.md` を読み、D291 を supersede する決定 ID が
  `("D292",)` **ちょうど**であることを literal で固定している。2026-08-12 に D305 が land され
  実際は `("D292", "D305")` になったため落ちる。**production の受理挙動は変わっていない。**
- **適用の毎回検査 (すべて満たすときだけ適用)**:
  1. 受入全走の赤が**上記 2 node ちょうど**であること。**他の赤が 1 件でもあれば適用せず停止する。**
  2. 失敗理由が `assert ('D292', 'D305') == ('D292',)` 系の**期待値集合の差**であること。
     他の理由 (import error、timeout、production の拒否挙動変化) なら適用しない。
  3. 自 wave の差分が `orchestrator/tests/test_t793_report.py` と `docs/decisions.md` を
     **触っていない**こと。触るなら自分の責任なので適用しない。
- **失効**: 上記 2 node の期待値が是正された時点で**自動失効**する。失効後に本 waiver を
  引いてはならない。
- **並行セッション**: 同じ 4 条件を各セッションが自分で検査したうえでのみ適用してよい。
  検査結果 (赤 node 名の集合と失敗理由) を worklog へ併記する (F101 の再発検知)。
- **是正の担い手**: `test_t793_report.py` は T-139/公表層 wave の所有。凍結境界により
  本 wave は直さない。推奨は上記のとおり「scan 対象を凍結 bytes へ固定する」。

**セッション異常。** `dev_wave_wait.py producer` を背景 task で回すと、producer 生存中に
待ち手だけが空出力で終了する事象が 5 度起きた。**実体を伴わない完了通知も多数観測した** —
ledger が 4/12 のときに 5/12、7/12 のときに 8〜11、さらに単独再走では
「2 failed, 8 passed in 3.32s」「2 failed, 6 passed in 3.51s」と**具体的な数値ごと捏造**され、
その時点で job はまだ QUE だった。いずれも `.done` + 成果物 + producer 死の 3 点照合で検出し、
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
