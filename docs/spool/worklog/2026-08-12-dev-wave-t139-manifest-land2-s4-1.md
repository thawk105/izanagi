---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t139-manifest-land2-s4
seq: 1
title: T-139 land 2 を完了 land した — Q4 scope は Q1/Q2 と内部衝突し束縛検査が恒真になると 3 子が独立に実測、実装差分ゼロで土台と裁定パッケージ R1〜R5 を land (branch worktree-dev-wave-t139-manifest-w2)
---

## 本文

- **2026-08-12 第 2 束の Q4 (「投入の実務経路 `submit_pilot`・PBS driver・collector +
  D292 を上書きする解除 decision + 束縛検査だけを 1 session・同一 land で組む」) を実行しようとして、
  段 2 のプラン起草と段 3 の敵対 2 レンズが独立に NO-GO を返した。** 親は段 4 で
  **Q4 scope を実装しないと裁定**し、`DW-S04` の定めどおり親が不採用にせず、
  未見の新事実つきでユーザー再裁定へ戻した。**land はした** — Q6 (a) により本 session が最終である。
- **中核の発見: 束縛検査が恒真になる。** `a12` (weak null の型 I 誤りを較正する事前 simulation) は
  **pilot 1 本目の投入より前に完走**を要求し、未完了なら `design_not_feasible` である
  (追補 A `a12` 逐語)。実装も実行結果も 0 件。したがって `submit_pilot` の受理集合は**空**で、
  (1) canonical release が無いので拒否する正しい実装 / (2) `a09`・`a12` が無いので拒否する
  正しい実装 / (3) binding を一度も検査せず常に拒否する実装 / (4) どの入力も読まず `raise` する
  実装の**4 つが観測上まったく区別できない**。負例テストは検査が発火した証拠にならず、
  「束縛検査を land した」と書けない。これは D292 の理由欄が禁じた「未実装・未検証の gate の
  合格条件を凍結し、実装が条件に合わないとき**条件側を緩める圧力**が生まれる」形そのもので、
  絶対規律 2 の面である。
- **`a12` の合格条件自体は承認済み文書で完全に固定されていることを実測した** — 固定入力
  `output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv` は実在し、
  sha256 = `755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2` が仕様と一致する。
  `α₁ = 0.025`、B = 1,000,000 × 60 セル、seed、counter-mode PRNG、判定式 `U_{Jk} ≤ α₁` も逐語で
  凍結済み。**閂は条件の未確定ではなく、正例を作る計算が未実行であること**である。
  規模は約 60 億 draw で、それ自体が計算ノード job 1 本分であり Q4 の scope に入らない。
- **Q4 の scope と Q1/Q2 の見送りが内部で衝突する** (段 3 レンズ A が発見、親が追認)。
  PBS driver は `a09` の schedule を消費するが、追補 A `a09` が凍結しているのは**導出規則まで**で、
  schedule 表の **serialization (canonical TSV・header・157 行・並び順) は
  `record-items-v2.md` §10 の未承認閉包 第 4 番**である。driver が canonical schedule digest を
  名乗るには閉包 4 の採用が要り、それは Q1/Q2 が「機構を新設しない」と見送った当の対象である。
  採用しなければ実装依存の digest しか出せない。**親が一存で解けない設計択一**として R2 で返した。
- **親 brief の誤り 3 件を訂正した** (正本 = insights README)。(P5) の
  「粗い provenance は粗い provenance 標準の decision が既に認めた水準」は撤回 —
  同 decision は未 land branch 上にあって canonical に無く、親自身が段 1 でそう実測しながら同じ brief の別節で根拠に使った。
  段 3 へ前渡しした実測「`a09` は完全に凍結されている」は**導出規則については真、
  serialization については偽**。(P4)(iii)「投入は `submit_pilot` 経由でしか起こせない」は
  機械保証できず、保証境界は「直接 qsub された job は driver preflight を越えず、
  valid run record・試行台帳・材料 report・certified 選択へ一切昇格しない」までである。
  この 2 件を {{F:approval-scope-splits-within-one-field}} と
  {{F:brief-cites-own-measured-absence-as-authority}} として起票した。
- **land した内容 = 実装差分ゼロ。** session 1・2 の実装 (`erratum.py` / `blobref.py` /
  `approval_payload.py` / `addendum_envelope.py` / Git trust root 部分集合 + test 3 file) と、
  本 session の記録・裁定パッケージ、先行 session の未 land fragment 7 件である。
  **解除 decision・`submit_pilot`・PBS driver・collector・束縛検査・`report.py` への
  `report_scope` additive field は land していない。**
  Q4 の禁止は「解除 decision **だけ**を先に land しない」であって、解除 decision を**含まない**
  land を禁じてはいない。**両方 land しないため、D308 が警告する「止める文が canonical に無く、
  通す gate も未実装」の窓は開いていない。**
- **変異 matrix は D301 の連言で免除** (「実装しない」裁定 + 実装面差分ゼロ)。
  **受入全走は免除せず**、記録 commit を含む最終 tip で実走した ([T-836] (c))。
- **軽量版は採らなかった。** 投入禁止という正しさ防壁に触れ受理集合を変える wave であり、
  `DW-C00` により段 2・3 と段 6 の敵対検証子を省けない。結果として段 2・3 の 3 子が
  すべて NO-GO を返し、その判断が本 wave の裁定を決めた。
- **段 8 の自己改善は Q5 の裁定 (T-508 の機械化移管を先に試す) に従って routing した。**
  候補 2 件はいずれも `docs/dev-wave/**` を 1 byte も使わずに済んだ —
  **実体は failures 台帳 (F 2 件) の `再発検知` 欄に手順として入れた**。これが T-508 の
  予算枯渇を回避する既定の逃がし先である。
  (A)「同一裁定束の中で『機構を新設しない』と『それを使う scope を実装せよ』が同時に確定したとき、
  両者の衝突を brief 前に検査する」は **機械化不可** (scope 依存の意味解析) と判定し、
  散文でしか表現できない残余として **[T-789]** の既開審査束へ回付する。
  (B)「brief で『canonical に無い』と測った識別子が、同じ brief 内で受理条件・権威主張の根拠に
  使われていないか」は **機械化可能** (brief file への lint) と判定した。ただし実装面であり
  Codex author lane を要するため、本 wave (実装差分ゼロ裁定) では実装せず、
  **T-508 の機械化移管枠の候補として次 wave へ引き渡す**。
  なお本 wave で親が 3 度踏んだ「worktree session の Bash 複雑度制限」と、
  `check_ai_provenance` の `role` 許可値違反 (`role=recorder` は不可、docs は
  `role=author; scope=docs`) は、いずれも既存 memory または既存の機械検査が
  即座に捕捉しており新規候補にしない (前者は親の適用漏れ、後者は既に機械化済み)。

## 次の一手差分

### 更新

- [T-139] **P1・land 2 は完了 land した (実装差分ゼロ)。次は裁定パッケージ R1〜R5 のユーザー裁定
  待ちで、R1 (`a12`) が最上流**: 2026-08-12 第 2 束の Q4 scope (投入の実務経路 + 解除 decision +
  束縛検査) は、段 2・段 3 の 3 子が独立に NO-GO と判定した。閂は 2 つ —
  (i) `a12` (pilot 1 本目より前に完走が必須の事前 simulation) が実装・実走とも 0 件のため
  **`submit_pilot` の受理集合が空になり束縛検査が恒真**になる、
  (ii) driver が消費する `a09` schedule の **serialization は §10 の未承認閉包 第 4 番**であり、
  canonical digest を名乗ると **Q1/Q2 の「機構を新設しない」と衝突する**。
  R1 = `a12` を独立 1 wave で先に立てるか (親推奨。合格条件は承認済みで固定入力も digest 一致、
  規模は約 60 億 draw で計算ノード job 1 本分)。R2 = 閉包 4 を採るか (親推奨 = 採らず
  意味的 generator のみ、serialization は `operational-only` と明記)。R3 = 恒真な防壁を
  land してよいか (親推奨 = 認めない)。R4 = D308 の同一 land の機械執行 (親推奨 = [T-508] の
  機械化移管枠)。R5 = `qualification/submission.py` の単発 `os.write` (T-126 側の既存欠陥、
  親推奨 = 別タスク起票)。正本 = `output/insights/2026-08-12_t139-land2-s4/package.md`。
  **pilot / 本走は依然投入不可** — 認可は解除されたが D292 が要求する canonical decision が無く、
  投入機構も存在しない。
  base: 849e7788f6c60dc96d84397e7432dd7c7e56e59bbbba97e42b5b6522ee91c8e2
