---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2853-repro-package-estimate
seq: 1
title: [T-2853] 再現パッケージの初段を計算なしで行った — 公開対象 6 種の量と保存費、trace の保存・公開方針、再実行の 3 経路 (R1 再判定 / R2 再実行 / G 再生成) を insight にまとめ、一次資料 P0 の 32 / 81 GiB が trace 量でなく verifier のメモリだったことを訂正した (docs のみ、branch worktree-dev-wave-t2853-repro-package-estimate)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): 公開対象ごとに trace 量と保存費を既存記録から仮定付きの幅で見積もり、LLM の再生成と保存済み候補の再検証・再計測を分けた再実行の形を整理する。計算なし、gate・検査・台帳の追加と凍結 chain は scope 外。記録 = `output/insights/2026-09-22/t2853-repro-package-estimate/README.md`。decisions fragment は作っていない (方針は T-2853 初段の設計で、insight §7・§8 を正本にした)。
- 素材: **一次資料 (gap-analysis §4 P0) の「balanced 10 秒で 32 GiB、read-heavy 6 秒で約 81 GiB」は trace の量ではなく改修後 verifier の node peak メモリ**だった (verifier-capacity §4)。trace file は balanced 10 s 2.63〜5.49 GiB、read-heavy 6 s 4.18〜11.89 GiB。
- 素材: 評価経路は 2026-06-19 の初版 (`181a30e75`) から検証後に trace を消している。原本を確認できたのは repo 外 runner が zstd で保全した D2160 検証相 64 走と B-8 30 走の計 78,421,191,580 B と、追跡下の旧形式 (v1) trace 4 file だけ。S-1a の 324 件検証・B-5 試走・K2 手動 loop の原履歴は確認できない。今後の本規模評価は B-5 型完走評価 1 件で保存 1.43〜3.19 GiB (Silo・YCSB・48 thread の 2 系列からの条件付きシナリオ値)。
- 方針 (段 4 の親の決定、「裁定へ返す」は採らない運用で 2 レンズ相談を経た): 今後の論文根拠の実験は作業保管を全量 (zstd) で残し、公開は主張の役割で分ける (検証が主題の実験と anomaly 反復は全 trace、探索比較の certified 反復は標本 + 判定要約の全件)。**この方針で EA&B の要件を満たすかは未確認** (公式規定は保存粒度を定めていない)。標準経路は trace を消すので、全量保管には保全口の実装が要る (未実装)。
- Web 確認 (2026-09-22 08:5x JST、逐語 = insight `verbatim/web-evidence.md`): VLDB Vol.20 EA&B は初回投稿で全実験の再現パッケージのリンクと実行手順が必須。Zenodo は 1 レコード 100 file・50 GB (増枠 200 GB は二次情報のみで未確認)。料金の記述はどのページにも無く、保存費の金額は未確認のまま費用式だけ示した。
- 段 3 (read-only codex 2 本、決定レンズ / 攻撃レンズ、consult・medium): must-fix は A 5・B 5 件 (重複あり)。採用の要点は T1 で要件を満たすとの断定撤回、key 射影を保存の前提から外す、量の幅を条件付きシナリオ値へ、6 対象別の表、図ごとの費用積み上げ。攻撃不成立 (refuted) は、当時のコード同梱が規律 7・凍結 chain 禁止に反するという疑義、R2 = 新しい有限履歴の判定という定義への攻撃、射影で辺が消えるという攻撃、job dir 回収が機構だという攻撃の 4 型。相談 A の「trace.hh v1 と現行 parser が合わず再現手順が成立しない」は一部 real (Silo は transaction.cc で v2 を直接出し保全 trace も v2、追跡下の旧 trace 4 file だけが v1)。
- **親の裁定誤り 1 件:** 段 4 で相談 B の「0 B の verifier.json は 4 走」を、親の自前 awk (`NR>2` で先頭のデータ行を読み飛ばした) の 3 走で「誤り」と覆した。段 6 レビューの must-fix で逆転し、insight §12 に erratum を書いた (段 4 裁定の逐語は保存)。段 8 で F473 (道具が何を数えたか確かめずに引用) の再発として failures へ追記した。
- 段 6: read-only codex review 1 本 (一次資料から事実を再抽出した docs wave なので残す) が NO-GO (must-fix 3: 上の 0 B 件数、P2-5 は replay で trace を生んでいないのに消失一覧へ入れていた・原本の不在の断定が調査範囲を超えた、射影で cycle を再検出できる条件の脱落)。fix 後の焦点再レビューは 2 巡 (1 巡目 NO-GO = closed 8 / partial 2 / regressed 1、2 巡目 GO = closed 10 / partial 1 (nit)、must-fix・should 0)。
- 実装面の差分ゼロ (insight・verbatim・本 fragment のみ) なので変異 matrix は免除 (DW-S04)。受入全走の結果は land の受領証。
- 記録前に local main `ad4bd2bb7` (他 wave の記録と D2219) へ wave branch を fast-forward した (wave 側 commit 0 の時点、T-2853 の base digest は不変)。D2219 項 1 (計算確認の線に開発の検査も数える) を insight §9 に引いた。本 wave の計算ノード使用は受入だけ (≈ 0.25 node 時間 / 回、線の内側)。
- 記録前の走査: 三軸語の走査器 (`s8b_holdout_freeze search`) は rc=1 だが hit 3 件は main に既存の `output/env/pegasus/calibration/s8b-floor-official/` の file で、本 wave の file の hit は 0 (entry 1818 と同じ既存 hit)。
- セッション異常: submodule 初期化が 1 回目 `update-no-fetch` rc=1 (30 秒 timeout 型)、再走で rc=0。Agent (Claude 子) の初回起動 3 本が model 未指定で `hooks/guard_agent.py` に拒否され、sonnet 明示で再投入した。
- 工数: Claude の調査子 3 本 (Explore、sonnet: trace 量の記録・公開対象の棚卸し・再実行経路)、Codex 子 = consult 2 本、review 1 本、focus 2 本。login: du / 集計 script 3 本 (repo 外)・`check_quota`・`zstd -dc` の先頭読み。計算ノードは受入のみ。

## 次の一手差分

### 更新

- [T-2853] **P1・初段済み (VLDB 差分分析 P6: 再現パッケージ)**: EA&B は初回投稿時に全実験の再現パッケージのリンクと実行手順を要するので、実験と並行で作る。保存するもの = コード、生成パッチ、入出力、探索設定、失敗候補を含む実験データ、図表の生成手順。失敗候補と否定的結果を含めて公開してよく (D2212 項 6)、provenance は粗い粒度 (システム名・モデル表示名・おおよその時期、D320) で足り、凍結 chain は足さない。**初段 (量・保存費の見積り、trace の保存・公開方針、再実行の 3 経路) は `output/insights/2026-09-22/t2853-repro-package-estimate/README.md` で済んだ。** 残り: (1) 今後の論文根拠の実験 (P0・P1・P3・TPC-C) を走らせる前に、標準評価経路へ trace の保全口 (作業保管を全量 zstd で残す) を入れる (Codex author の実装 wave、insight §7・§11)。(2) job dir にだけある論文根拠の実験データ (B-5 試走の台帳・LLM 入出力・報告、D2160・B-8 の保全 trace と runner、K2 pair、A-1 の attempt データ) を cleanup の対象外の保存先へ写す (proof chain を動かさず、写しを official の正本へ昇格させない)。(3) 実験系列ごとの実行手順書と R1 の入力一式 (trace・当時の関連入力・verifier の版)。(4) P1 の関数単位の候補を受ける R2 の入口 (P1 の実装と同じ wave で)。(5) 主要図の再実行は図ごとに「描き直し / R2 / 独立探索のやり直し」を決めて node 時間を積み上げ、2 node 時間以上ならユーザー確認後に投入する (D2212 項 4)。(6) 公開範囲 (全量か役割別か) の最終確定は投稿前のパッケージ組み立て時 (目標投稿 2027-02-01、概要提出 2027-01-25)。
  base: f59b3208729b76a7eb3f6d3c44bc4b9e2244d808b031e7ab1f29237329ec53a0
