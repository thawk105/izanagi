# [T-142] テスト価値の二層化 — 実装なし裁定と再裁定パッケージ (2026-07-28)

dev-wave (段 1〜4 実施、段 4 で「本 wave では実装しない」を裁定、段 5・6 スキップ)。
逐語 = `output/insights/2026-07-28_t142-review-verbatim/`。基準コミット 78eedcb。

## 1. 裁定の現在地と本書の位置づけ

- T-142 は 2026-07-28 (36) の裁定 (3) で**採用済み**。条件 = 「省略する検査が受理集合を
  変えないことを機械的に示せる範囲に限る」。出自 = 外部相談の提言 3
  (`output/insights/2026-07-27_external-consultation-scope-and-axes.md` §1-3、§1-8 が保留した
  lazy 検証とは別物という整理を含む)
- 本 wave は実装に入る前の実測と敵対検証で、**裁定時点で未見の新事実** (§4) により
  「条件を満たす実装域に価値が存在しない」ことが判明した。DW-S04 に従い親は不採用とせず、
  新事実付きでユーザー再裁定へ差し戻す。**本 wave のコード変更はゼロ**

## 2. 実測 (全て既存 WAL の読取集計。新規計測なし)

方法: `output/campaigns/*/runs/wal.jsonl` 全 30 本の stage/ts/payload を集計
(スクリプト = 逐語 dir の `count_abort_reasons.py` / `count_frontier.py`)。

- **評価の段別コスト**: S2 verify 中央値 117.3 s (n=111、min 74.6 / max 332.5)。legacy verify
  ≈ 12 s、bench は構成により 2.5〜77 s、cached build 0.3 s。bench 併走点 (n=78) での S2 比率
  中央値 79.8%、S2 を省略した場合の理論倍率中央値 4.95 倍 (range 1.85〜9.15、レンズ 1 所見 11)
- **abort 分布**: 476 評価で abort 15 件 (build-error 12 / trace-timeout 1 / non-serializable 1 /
  screen 1)。**bench 失敗による abort は 0/78**。唯一の non-serializable は red-consumer 正例
  campaign (意図的破壊の検出確認) であり、実探索での verify 赤は 0 件
- **frontier 比率**: commit 426 件中 new-best (その時点の fitness 最大更新) は 50 件 = **12%**。
  「S2 を new-best 昇格時だけ実走」なら歴史上 **S2 の 88% (376 回 × ~117 s ≈ 12.2 時間) を省けた**
- 注意 (レンズ 1 所見 11): 上記は campaign/config 混合の記述統計であり、将来分布への一般化には
  paired ablation が要る。また S2-red 候補は bench に到達せず打ち切られるため
  「bench 失敗 ∩ S2 赤」の同時頻度は WAL から識別不能 (0 と主張してはならない)

## 3. 段 2/3/4 の要約 (全文は逐語 dir)

- 段 2 プラン (codex): 裁定条件を厳密に満たす唯一の形は**案 B** = 順序を legacy → bench → S2 に
  替え、S2 を省くのは「bench が正常完了しなかった候補」だけ。受理述語は L∧S∧B = L∧B∧S で不変。
  D58 screening の floor 棄却をループへ再利用する案 (A/A′) は certified になり得る集合を縮め
  条件違反、と判定。親 brief の誤り 2 件を検出 — (i) D36 決定 4-2 の「共通 AND ヘルパ」は現物に
  完成形で存在しない (`wal.records_by_stage()` は最後勝ちで AND に使えないと docstring が自警)、
  (ii) base driver `p3_s4_loop` は legacy-only で S2 が無い
- 段 3 レンズ 2 (実効性): **案 B の削減は実測 0/78 = ゼロ**。「良い候補」判定が性能を見ておらず
  価値による二層化になっていない。COMMIT 集合の完全不変と大幅短縮は現行受理規則の下で論理的に
  非両立。成果物契約 (roadmap の最終成果物 = certified 選択・stock/tie・試行台帳) は全 COMMIT
  集合そのものではない → 保証対象の再定義がユーザー裁定事項。実装時 blocker として
  `layer3_report.py` が COMMIT 無し bench TPS を runs へ全射影する経路を特定
- 段 3 レンズ 1 (正しさ境界): certified≠COMMIT (do_bench=False は bench なしで COMMIT、
  「certified だが測定不能で aborted」は正規状態)。L/B/S は順序非依存の固定関数ではない
  (lock・probe・settle・熱状態)。真理値表 helper は恒真になり得る (tag は S2 実体を証明しない)。
  `wal.replay()` は COMMIT 存在だけで committed 化する。「受理集合」は V (correctness-certified) /
  A (COMMIT) / O (選択・報告出力) の三分が要る。取り残し consumer の具体列挙
  (replay / p3 duplicate / critic / layer3 / p2 report / s6 / s8 / plotting / freeze / guided)
- 段 4 (親): レンズ 2 の 11 件 = 全 real。レンズ 1 の 12 件 = 11 real、所見 7 (AST 最終形) のみ
  speculative (現行番人の弱さ自体は real)。親 brief P1 = 生存 (解釈明記条件付き)、P2 = 棄却、
  P3 = 充足形再設計要、P4 = 修正採用 (番人テストは置換でなく温存 + 追加が正しい)。
  親実測の一般化 2 件に erratum — 「bench_max_rounds=1 系」の帰属は誤り (loop は既定 3、観測
  round が 1 だっただけ)、「85% / 8 倍」は局所値で n=78 の中央値は 79.8% / 4.95 倍

## 4. 未見の新事実 (再裁定が必要な理由)

裁定文 (worklog (36)) にも相談 insight にも記録がないことを確認済み。

1. **裁定条件を厳密に満たす省略域は実測で空である。** 受理集合 (certified になり得る集合) を
   変えずに省ける S2 は「bench が失敗した候補」の分だけであり、その頻度は歴史上 0/78。
   つまり条件と採用意図 (毎ループの大幅短縮) は現行の受理規則の下で**両立しない**
2. **価値のある二層化は保証対象の変更を要する。** 「最終 selected/stock/tie と正式レポートの
   certified 主張が不変」(出力集合 O の不変) へ保証対象を移せば、S2 の約 88% を省く設計が可能
3. **実装時 blocker**: layer3 material report が COMMIT の無い bench TPS を正式射影に露出する
   (D58 screening が layer3 対象外とされているのと同根。対処には schema 再凍結を伴う)
4. **規律 3 との交点**: 新順序では「bench 失敗 ∩ S2 赤」候補の S2 構造化 red を観測しない。
   頻度は右打ち切りで不明。裁定文言はこの診断機会の減少を明示的に許容していない
5. **語の予約**: 「進化探索」は roadmap で population 実装まで予約された語であり、裁定文の
   「進化探索の毎ループ」を現行 p3 sequential loop に写すことは (相談原文の文脈上自然だが)
   裁定として明記されていない

## 5. 再裁定パッケージ (ユーザーへの択)

**(a) 保証対象を出力集合 O へ移して二層化を実装する (親の推奨)。**
「受理集合」の保証対象を「最終 selected/stock/tie・正式レポート・proof chain の certified 主張」と
定義し直し、S2 は候補が選択 frontier (new-best 等) へ昇格した時だけ実走、COMMIT は従来どおり
全 verify 通過後だけとする適応的 promotion。推定削減 = S2 の約 88% (§2)。前提として必要なもの:
- D58 の適用先拡大に相当する別裁定 (D58 自身が要求)
- layer3 の未認証値遮断 (schema 再凍結、§4-3)
- 規律 3 の S2 診断機会減の明示許容 + 「S2 未実行・未認証」の構造化信号を critic へ返す設計
- V/A/O 三分の decisions 化と、[T-110] (受理集合を変える改修の手続義務) との整合
- 機械的提示の充足形は真理値表でなく「選択・報告が読むのは S2 済み candidate だけ」を機械検査する形
  (レンズ 1 所見 6/7 の恒真化対策を含む)

**(b) T-142 を close する。** 「受理集合を変えない範囲に価値のある省略が存在しない」という実測
(§2) を理由に、コード変更なしで閉じる。いつでも選べる安全側。iteration 単価は現状のまま
(S2 ≈ 117 s が毎回)

**(c) 周辺負債の分離。** どの択でも、(i) D36 決定 4-2 の AND ヘルパ現物化 (replay /
duplicate / critic / layer3 の consumer 共通化) は T-142 と独立の防御負債として別タスクで扱う。
(ii) base driver (`p3_s4_loop`) への S2 追加は二層化と独立の受理述語変更であり別裁定
(足すと base loop は ≈14.5 s → ≈130 s に遅くなる — 検出力とのトレードオフはユーザー判断)

## 6. 射程と反証可能性

- 本書の数字はすべて既存 WAL の読取集計 (方法 = 逐語 dir のスクリプト、再現可)。環境は
  linux-baremetal 系の混合であり、将来の campaign 構成への外挿には paired ablation が要る
- S2 の検出力そのものは疑っていない — D36 gate 3 が「legacy 緑 × S2 赤」の実在を機械実証済み。
  争点は検出力ではなく**実行頻度の配分**である
- 本 wave は実装差分ゼロのため、変異 matrix と受入全走は対象外 (DW-S04 の射程明記)。
  記録 commit 後の検査は check_docs / repo scan invariant / provenance 監査のみ
