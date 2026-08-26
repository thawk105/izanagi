---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t782-reviewed-spec-issuance
seq: 1
title: [T-782] 査読済み spec の凍結発行を批准凍結の後へ送り、裁定パッケージを返した (docs のみ、branch worktree-dev-wave-t782-reviewed-spec-issuance、実装差分ゼロ・変異 matrix 免除)
---

## 本文

- 依頼は「査読済み spec を凍結成果物として先に作り、CLI は指紋照合だけ行う」(D840 の択 (b))。
  **実装差分ゼロで終えた。** 裁定の向きは不採用にせず、新事実を添えてユーザー再裁定へ返した。
  一次資料は `output/insights/2026-08-26_t782-spec-issuance-ruling/`。
  設計判断は {{D:spec-issuance-waits-for-ratified-freeze}} と
  {{D:spec-axis-classified-by-binding-layer}}。
- **裁定の前提が 2 つとも今日成立しなかった。** D840 の理由文は 2026-08-11 時点の状態記述を
  引き写しており、名指しされた攻撃 (各 holdout を 1 構成へ間引いて唯一の勝者を作る) は
  cell 完全積の検査で既に塞がっていた。択 (b) の機構自体も同日に実装済みで、
  未了は durable 発行だけだった。D840 は D480 に言及しておらず、D480 が却下した選択肢と
  同じ操作を求めていた。
- **段 4 直前の裁定 inbox 再走査が決め手になった。** wave 走行中に D959 が main へ着地し、
  8b の閉塞を依存の層として記録して、本 wave の対象である schedule authority の無条件 raise を
  「最上流に従属する下流症状であり、順序を入れ替えて先に解除してはならない」と定めていた。
  同 decision は共有 ratified freeze だけが最上流と独立に進められる別線だとも書いている。
  再走査を省いていれば、着地したばかりの順序規定に反する実装を投入していた。
- **段 3 の 2 レンズは合計 20 所見を返し、親は全件を real と裁定した。refuted はゼロ。**
  要の主張 6 件は親が独立に実在確認している。実装しない判断を支えたのは
  (a) 候補 bytes を読む production consumer が repo 内に 1 つも無いこと、
  (b) 凍結対象の binding identity が生成 site 依存で、生成 site と実走 site が違えば
  実走時の再実体化と一致しないこと、(c) 実装しても成果物の値が 1 bit も変わらないこと、
  の 3 点である。
- **親の実測は 3 度書き換わった。** 最初に「binding identity は批准凍結なしでは作れない」と
  書いたが、段 2 のプラン子が共有 producer の実在を挙げて反証した。親は自分で全件検索による
  反証も試みており (過去の campaign 成果物に現行 12 cell の記録が 0 件であることを確認)、
  その検索は正しかったが、**値を計算する経路が別に存在するという可能性を検索対象に含めていなかった**。
  次に「実行環境タグ・時計数・除外理由は repo 権威から導出できる」と訂正したが、
  これも段 3 の 2 レンズが独立に否定した (F151 の再発)。
  凍結 bytes の pin 閉包を「全件列挙した」と書いた点も誤りだった (F301 の再発)。
- **段 3 のレンズに「親自身の実測値とその一般化」を攻撃面へ入れる規律が、本件でも機能した。**
  ただし今回は段 2 のプラン子が先に 1 件目を反証しており、親の一般化が子に覆される経路が
  段 3 だけではないことが実測された。
- **子の工数** (receipt schema 4、全件 accepted・validator rc=0)。段 2 プラン = model call 26 回・
  wall 747.9 秒・output 24,989 token。段 3 sol = 27 回・730.1 秒・27,469 token。
  段 3 luna = 25 回・1016.1 秒・29,609 token。段 5・6 は裁定により起動していない。
- **実装 wave へ引き継ぐ既知の穴を 6 件、実在確認つきで裁定パッケージへ残した** —
  trust root 照合の迂回、canonical path の symlink 経由で査読 diff 外の bytes を承認済みにできる点、
  pin だけあって file が無い状態を現行検査が受理する点、generator の drift を lifecycle が
  見逃す点、新規 test file が偽緑ガードに掛かる点、既存 fixture との二重 assembler。

## 次の一手差分

### 更新

- [T-782] **P1・ユーザー再裁定待ち (2026-08-26、実装せず裁定パッケージを返した)**:
  D840 の向き (b) は維持。着手は共有 8b ratified freeze の発効後へ送る
  ({{D:spec-issuance-waits-for-ratified-freeze}})。返した論点は 4 つ —
  (Q1) D840 の逐語「内容の再導出や束縛検査を持たない」をそのまま実装すると既存の正しさ検査を
  撤去することになるため「消費側へ新たな解釈を足さない」と読み替えてよいか (親推奨 = 読み替える)、
  (Q2) T-782 と共有 ratified freeze の着手順序 (親推奨 = freeze が先)、
  (Q3) 生成 site 依存の identity をどの site で凍結するか、
  (Q4) 既存の producer 設計資産を実装 wave の起点にするか。
  一次資料は `output/insights/2026-08-26_t782-spec-issuance-ruling/`。
  base: 737ed75a874b51b05cf78b0956ad0c86969fdba86a23a60f008465649d4f91cb
