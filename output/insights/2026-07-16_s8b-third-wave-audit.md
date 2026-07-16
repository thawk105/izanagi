# 8b oracle 系 第 3 波監査 (2026-07-16) — 現行コードの敵対監査

- **日付:** 2026-07-16
- **対象:** HEAD 3782f5e 時点の 8b oracle 系 — `s8b_oracle_report.py` / `s8b_oracle_manifest.py` +
  `s8b_budget.py` / `s8b_oracle_judge.py` + `s8b_oracle_driver.py` (とそれぞれのテスト)
- **方式:** Claude Fable 5 の workflow — レンズ別監査員 3 (false-green・恒真ゲート / 台帳恒真化 /
  gate fail-open) + 所見ごとに独立コンテキストの反証者 2 名 (不確実なら refuted に倒す規約)。
  反証者 2 名とも維持 = confirmed、2 名とも反証 = killed、割れ = uncertain として親が裁定
- **位置づけ:** 二波監査 (原文消失。記録 =
  `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md`) とは**別成果物・別 ID 系列
  (A3-x)**。二波の real 13 / refuted 11 に混ぜない。原文の復元でも欠落 1 件の補完でもない
- **除外済み既知所見:** §9 承認前検証 (敵対相談 C2、逐語 =
  `output/insights/2026-07-16_s8b-freeze-consultations.md`) で検証済みの 6 件 (freeze design-hash
  不一致 / prediction 検証の raw 非再 parse / 予測生成規律の非発火 / commit pin 形式検査のみ /
  §6 判定量化の未規定 / resume 拒否の迂回) は本監査の再報告対象から除外した

## 所見台帳 (9 所見 → 統合後 8 件: confirmed 4 / uncertain 2 / killed 2)

### A3-1 [confirmed / high / 恒真ゲート・false-green] schedule 外 index の trial window 黙殺で red が隠れる — **本セッションで修正**

`s8b_oracle_report.py` の windows_by_index は全 trial-start から作られるが、消費は schedule 行の
schedule_index の get のみ。schedule に存在しない index を名乗る window は無警告で捨てられる。
correctness-red の attempt を幻の index で記録し正しい index で green を記録し直すと、
definitive_reds 保護を素通りして row=completed/committed・judge=determinate になり、WAL に実在する
red が observations に現れない (全件報告規則の破れ)。反証者 2 名が独立に repro を実行して再現。
姉妹実装 `s1_report.py` は schedule 外 index で明示 raise しており、report 契約の意図とも不整合。
**処置: commit d96a9f0 で window 全数照合 (schedule 外 index の window = protocol violation) を実装。**

### A3-2 [confirmed / medium / テスト代表性 (F15 型)] excluded_reason 経路のテストが皆無 — **本セッションで修正 (テスト追加)**

sys.settrace によるライントレース実測で、`s8b_oracle_report.py` の許可一覧外 reason →
protocol_violation 分岐、correctness-red + excluded の拒否分岐、`s8b_oracle_judge.py` の
excluded_reason 非 null 経路が、テスト全走で一度も実行されないことを 2 名が独立に確認。除外は
観測を統計から取り除く唯一の経路であり、回帰 (任意 reason の受理・除外観測の統計混入) が無検知
だった。**処置: commit d96a9f0 で (a) 許可 reason の全件報告残留と judge の unknown 化、(b) 一覧外
reason の違反、(c) red+excluded の拒否、(d) judge 非 null 経路、を実行するテストを追加。**

### A3-3 [confirmed / medium / F14 型・fail-open] 複数 block manifest で共有 budget 台帳が破綻する — **設計判断待ち**

2 レンズ (manifest-budget / judge-driver) が**独立に同根を発見**。run_block は block ごとに
create-only の台帳生成を無条件に呼ぶため、(a) 設計既定の単一台帳 path では 2 block 目が
BudgetError で例外終了し、しかも campaign-start WAL が台帳生成より先に書かれるため resume 拒否で
当該 block は恒久実行不能になる。(b) 唯一の回避 = block 別 path は freeze の総枠 B_total_seconds
を台帳数分だけ複製し、凍結総予算 gate が block 数倍へ fail-open する。`oracle_shared=true` は
リテラル検査のみで共有計上経路が存在しない。テストは単一 block のみ。現状は gate_check が全経路
refuse (v2 verifier 未実装) のため実害未発生だが、**freeze v2 導入でそのまま発火する**。
処置: 台帳継続 API か「1 oracle = 1 block」拘束かの設計判断が必要 — (b) 再凍結と同時に裁定する。

### A3-4 [confirmed / low / ドリフト] 全行 binding-refused でも status=completed / rc 0 — **設計判断待ち**

整合性エラー (binding-refused・prepare 恒久失敗) だけが駆動側の成功コードへ転ぶ
(budget-refused=rc 2、未知 abort=rc 非 0 と非対称)。全 12 行拒否 + evaluate 0 回でも
completed/rc 0 を反証者 2 名が再現。下流 report/judge は fail-closed のため certified な
false-green には至らないが、rc 0 を成功と読む自動化は黙って前進し、当該 campaign は WAL 汚染 +
resume 拒否で再実行不能のまま「成功」表示になる。
註: manifest-budget レンズの類似所見 (status 契約ドリフト framing) は「契約が文書化されて
いない・消費者不在」を理由に killed になった。**親裁定: 挙動は同一だが、rc 非対称と resume
焼失を指摘した judge-driver framing を confirmed として採用**し、status/rc の意味論確定を
A3-3 の実行トポロジー設計と同時に裁定する。

### A3-5 [uncertain / low] verify-inconclusive 宣言が build_done ゼロでも受理される

反証者が割れた: 維持側は「committed/build-failed は物理束縛するのに verify-inconclusive だけ
build_done を見ない非対称。honest writer は全 inconclusive reason を build_done 後にしか発火
させないため、build_done==1 要求を足しても偽陽性ゼロ」。反証側は「実 writer はこの WAL を生成
できず、汚染 WAL でも judge は unknown 止まりで green 化せず、protocol_violation にしても同じ
fail-closed 終端」。**親裁定: 実害経路なしを認め修正は見送り、v2 実走前の強化候補 (受理域の
証拠束縛) として記録する。**

### A3-6 [uncertain / low] freeze の hash 検証と実使用が別読込 (TOCTOU)

gate_check の hash 照合と run_block の再読込が独立 read で、budget limits と perf 三軸
(records/threads/ycsb) は未検証の再読込 object から取られる。反証側は「現状 gate は全経路
refuse のため窓に到達不能、freeze 生成も create-only で並行上書き不可」、維持側は「機構欠陥は
実在し、束縛対象が manifest 側 object であって driver 実使用 object でない前提も正しい」。
**親裁定: 現状実害なしだが、v2 verifier 設計要件「検証した bytes の parse 結果を単一 object
として使い回す」として (b) 再凍結の設計に持ち込む。**

### killed 2 件 (全件報告のため記録)

- **budget entry と manifest schedule の無照合 (per-holdout 帰属偽装):** 反証 2 — 台帳へ書ける
  攻撃者は limits 自体を書き換えられるため schedule 照合は防御価値ゼロ。唯一の writer は
  verify 済み manifest から値を写す。docstring の「完全照合」は spent と entries 再集計の突合を
  指し実装どおり。将来の防御深化提案であり欠陥ではない
- **binding-refused 行を含む status='completed' (契約ドリフト framing):** 反証 2 — 「completed =
  全行実行」という契約は文書化されておらず、rc/status を読む orchestration 消費者も現存しない。
  戻り値 JSON 自体に全 events が入っており欠測は検出可能 (→ 実質は A3-4 に統合)

## 裁定サマリと次アクション

| ID | 判定 | 処置 |
|---|---|---|
| A3-1 | confirmed high | d96a9f0 で修正 (window 全数照合) |
| A3-2 | confirmed medium | d96a9f0 でテスト追加 |
| A3-3 | confirmed medium | (b) freeze v2 再凍結と同時に実行トポロジー/台帳継続を設計裁定 |
| A3-4 | confirmed low | A3-3 と同時に status/rc 意味論を裁定 |
| A3-5 | uncertain low | v2 実走前の強化候補として記録のみ |
| A3-6 | uncertain low | v2 verifier 設計要件へ昇格 (単一 object 使い回し) |

還元判断: 対象はすべて izanagi 自身の orchestrator 層であり、CCBench 還元対象なし。
