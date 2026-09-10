# [T-810] 段 1 brief — ノード間性能差の測定 protocol を設計する (実走なし)

**base main:** `9abd23da` / **branch:** `worktree-dev-wave-t810-node-variance`
**前提実測の正本:** `/work/1/SFC/tanab/dev-wave-jobs/t810-node-variance/facts.md` (F-1〜F-7。読めなければ即停止)

## scope

同一 binary・同一 workload を N ノードへ同時投入してノード間分散を得る**新規測定 protocol** の
設計パッケージを 1 本書く。**実走はしない。** 成果物は docs (新規 protocol 設計文書 + 事前登録の
確定部分)。**実装面 (probe / job script / 集計コード) は本 wave で書かない** — 設計が確定してから
別 wave で Codex `role=author` が書く。

## 確定済みユーザー裁定・上位契約

- runbook §7.5 (2026-08-11 ユーザー裁定) が本 protocol の発注元であり、固定すべき項目を逐語で
  与えている: **目的・N・割付け・推定量・成果物へ流入させないこと**を事前に固定してから実施する。
- 同節: 処置と node が一対一の配置は完全交絡なので採らない。job 内で比較が閉じる fan-out は無条件可。
- 絶対規律 4 (スケールを無造作に大きくしない)、規律 1 (trace-disabled で計測)、規律 6。
- B 系並走ガード 3 条件 (`docs/phase3-8b-restart-runbook.md` §0): (i) ノード同居なし、
  (ii) T-139 pilot / 本走 job 走行中はキュー投入を控える、(iii) 裁定帯域は A 優先。
  本 wave は**設計のみで計算ノードを使わない**ため (i)(ii) は自明に充足、投入は受入全走だけで、
  その直前に `qstat` を再確認する。

## 不変条件

- certified 選択・材料レポート・proof chain・凍結 bytes・受理集合・env 契約 generation を変えない。
- 本 protocol が生む数値は calibration record / campaign journal / registered / env 契約の
  いずれにも入らない (F-3 の 3 段は 1 段も踏まない)。
- 既存 protocol (floor / oracle / certify) の schedule と判定を変えない。

## 成果物の形

`docs/` 配下の新規 protocol 設計文書 1 本 + `docs/README.md` の地図行。
worklog / decisions は spool fragment。**docs/pegasus-runbook.md §7.5 の stale 記述 (F-1) の
訂正を含めるかは段 4 で裁定する** (含めると受入全走が要る)。

## 親の provisional 裁定 (攻撃対象。段 3 のレンズはここを最優先で攻める)

- **(P1) 目的の言明。** ノード間分散は T-139 pilot の**妥当性を脅かさない** — F-5 のとおり
  3 arm は同一 cluster 内で測られ、contrast は node 内差だからである。効くのは (a) node 効果が
  乗法的なら contrast に残る倍率分、(b) cluster 間分散を通じた同時信頼領域の幅と必要 cluster 数、
  (c) §7.5 の「job どうしで性能値を比較する fan-out」の可否。目的をこの 3 点に限定する。
- **(P2) 推定量。** 一元配置変量効果 `y_ij = μ + a_i + e_ij` の `σ_a` を主推定量とし、
  報告は `σ_a/σ_e` 比と **`σ_a` の上側信頼限界**、および node 平均の max−min とする。
  点推定だけを返さない (判断に要るのは上限である)。
- **(P3) N と R。** 暫定 N=12 ノード・R=10 反復 (R は F-1 の registered noise_floor と
  同じ 10 反復に合わせて比較可能にする)。N は `σ_a` の上限精度から導く — 段 2 で数式から出す。
- **(P4) 割付け。** node は選べない (scheduler が割当てる)。同時投入で occasion を共通化し、
  binary は**共有 path で 1 回だけ build して bytes を配り**、各ノードで `binary_sha256` を照合する
  (F-2 がこれを必須にする)。各ノードで単独性確認と静穏 preflight を行う。
- **(P5) 非流入。** 出力は repo 外の専用 root に置き、`output/env/*/calibration/**` へ 1 byte も
  書かない。事前登録に「期待ファイル集合」と「生成しない artifact 種」を exact に書く。
- **(P6) 1 occasion の限界。** 同時投入は node 効果と node×occasion 交互作用を分離できない。
  設計はこれを制限として明記し、2 回目の occasion を secondary として事前登録する。
- **(P7) 単一 arm の限界と拡張。** 依頼どおり primary は「同一 binary・同一 workload」1 arm。
  ただし 1 arm では **node 効果が加法か乗法か**、すなわち T-139 の contrast で相殺するかを
  識別できない。同一 job 内で 2 構成を順に測る secondary を事前登録する案を段 4 で裁定する。

## 分割方針

段 2 = 起草 1 本。段 3 = 敵対 2 本 (レンズ A: 統計的妥当性と識別可能性 / レンズ B: Pegasus 上の
実行可能性と非流入の実効性)。段 5 の実装子は無し (docs-only) の見込み。

## 成果物影響 (DW-G05)

未実施なら §7.5 の「job どうしの性能比較 fan-out」は protocol 不在のまま禁止側に留まり、
T-139 pilot の同時信頼領域の幅がノード効果由来かを説明できないままになる。
本 wave 自体は certified 選択・レポート・台帳のどの値も受理集合も参照も変えない (設計のみ)。
