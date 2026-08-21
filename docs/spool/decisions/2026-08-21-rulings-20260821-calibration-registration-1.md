---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: rulings-20260821-calibration-registration
seq: 1
---

## {{D:ai-calibration-registration}}. rr80/rr20 calibration の取得・検証・登録は AI/ツールが実行できる

**決定:** rr80/rr20 calibration の登録主体を人間に限定しない。AI/ツールは、計算ノードでの
certification job の投入、計測、acquisition receipt の生成、schema・自己比較・品質判定・hash binding
の確認、および合格時の create-only publish を実行してよい。人間が calibration JSON を編集したり、
登録コマンドを手作業で打ったりすることは登録の必須条件にしない。

**理由:**
- 現行の calibrator は、失敗時に publish せず、合格時だけ登録 artifact を作る fail-closed の機械経路を
  既に持っている。人間だけを登録主体とする制限は、この検証を強めず、責任の所在と実行主体を混同する。
- 既存登録2件は rr50 であり、H1/H2 の rr80/rr20 は未登録だった。投入 workload を固定値から安全な
  whitelist 選択へ変え、receipt と job result へ再束縛すれば、手編集なしに同じ検証水準で追加できる。

**不変条件:**
- 測定は compute-node job body で行い、login node から重い実測を直接起動しない。
- binary hash、acquisition receipt、schema、動的 attestation、自己比較、品質判定、publish後の再読、
  create-only semantics は既存のまま維持する。
- この決定は正式 H1/H2 launch、g1→g2 activation、D145 decision 5 の再訪、その他の実験承認を含まない。

**却下した選択肢:**
- AI が JSON を直接作成・編集して登録する方式 — 実測・自己比較・acquisition receipt の証拠を迂回するため不採用。
- rr80/rr20 の未登録を理由に、別の正式実験 gate まで自動的に解除する方式 — calibration registration と
  launch/activation の authority が別であるため不採用。

## {{D:t1461-effective-floor-scope}}. T-1461 は dead wiring の二ファイル限定を越えて実効経路を修正する

**決定:** floor driver が実際に読む依存解決・buildcache 経路、preverified payload の transport、独立 expected
hash、CMake 前の pin 検査、compute-node offline の no-refetch/build 検証までを T-1461 の実装 scope に含める。

**理由:**
- 入口 script の環境変数を追加するだけでは floor driver が読まず、要求された offline build 保証を作れない。
- scope expansion は測定条件を勝手に変えるためではなく、依存 transport と build 前拒否を実際の consumer へ
  到達させるために必要である。

## {{D:t1472-provider-init-c04}}. provider-init failure を C04 の indeterminate 対象へ含める

**決定:** provider の初期化が `run_trial` の `_finish_trial` より前に失敗する経路も、C04 の crash 解釈に
含める実装方針を採用する。失敗時は実験を indeterminate として durable に表現し、再走と成功を混同しない。

**境界:** これは方針の裁定であり、既存の `_finish_trial` 変更だけで実装完了とは扱わない。実装・テスト・受入は
別 wave の責務である。

## {{D:t425-calibration-gate-actor}}. T-425 の正式 launch gate と calibration の実行主体を分離する

**決定:** 正式 H1/H2 launch は T-424/T-272 の要求閉包または D145 decision 5 の明示的再訪、およびその他の
未充足 preregistration / authority 条件が揃うまで閉じる。一方、rr80/rr20 calibration の取得・検証・登録は
上の AI/ツール経路で進めてよく、これを human lockstep の未実施として扱わない。

**理由:** calibration artifact の生成と、正式実験を許可する authority / activation は別の decision surface
である。前者を AI が実行できるようにしても、後者の未充足条件を自動解除することにはならない。

