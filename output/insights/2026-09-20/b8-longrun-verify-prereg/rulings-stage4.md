# 段 4 裁定 (親、2026-09-20 13:5x JST) — 軽量版 (段 2・3 省略) の plan v2

前提: docs-only、実装面差分ゼロ (DW-S04 により変異 matrix 免除、受入全走は段 7 後に投入)。段 2 plan・段 3 相談は省略
(DW-C00 の既定軽量版)。段 6 は一次資料から不在・数値を書き起こす docs wave なので read-only review 1 本を残す。

## 採用 (brief の P1〜P5 をそのまま plan v2 とする)

- **P1 対象:** 案 A (S-1 最終候補 g_rl / g_rt) を推奨、案 B (fixed-5 / fixed-10) を代替として並記し、択一は発効時に D 番号で記録する。
  両案を 1 cohort にしない (採るなら別仕様)。推奨理由は本文 §2.3 の 3 点。案 B を選ぶ正当条件 2 つも本文に置く。
- **P2 種:** S-1 層 2 の登録定義 (独立 process の自己シード) を採用。記録項目 = rep-id・PID・開始時刻・argv・node・binary sha・identity・trace 規模。
  seed 注入は前提条件にしない (D16 の別変更単位、identity が候補と別 bytes)。paper-story 仕分け (2) がこの定義を認めるかは発効時の確認事項。
- **P3 長時間:** extime ≥ 6 s を必要条件、校正 {6, 10} s 昇順、verifier wall ≤ 1800 s、未完走 = indeterminate、共通部分の最大、空なら候補なし
  (3 s へ丸めない)。系列長での代替 (3a)、verifier 容量改善を前提条件にする 10 s 固定 (3c)、上限撤廃 (3d) は不採用で理由を本文に置く。
- **P4 費用:** fixed-5/10 の 6 s 校正実測からの外挿 (案 B、1 候補、24 verify ≈ 13,000 s ≈ 3.6 h) を「算術」として置き、案 A の値は予測しない。
- **P5 判定:** D2160 項 3・5 を継承 (判定集合 = 本走 ∪ 校正完走 verdict、pass / 失格 / 未確定、本走未完走は同一 trace で 1 回再検証、anomaly は再検証なし)。
  失格時の扱い (案 A: S-1b の記述へ限定を追記、案 B: A-2 / T-1998 / A-6 の記述へ追記、bytes は不変) を §6.3 に置く。

## 統計文の扱い

「反例を作ってから書く」を適用し、書かない文 4 つ (1−εⁿ、長さ 2 倍 = 露出 2 倍、累計時間 = 1 走の長さ、自己シードは全部異なる) を
§1.3 に反例付きで列挙した。効能の主張は書かず、条件・仮定として登録する。

## 自分の否定命題のうち実測で支えていないもの (レビューに反証を求める)

- 「案 B では B-8 にならない」— paper-story 2026-09-20 §8 B-8 の仕分け文の読解。反証を歓迎する。
- 「1 走内でだけ進む状態 (epoch・TID・GC) は走をまたいで引き継がれない」— CCBench の構造の読解 (process ごとに DB を作り直す)。反証を歓迎する。
- 「seed 値は stdout・trace のどこにも出ない」— gflags 定義と random.hh の読解。trace の書式まで全部は追っていない。反証を歓迎する。
- 「`std::random_device` の実装は toolchain 依存で外部観測できない」— 一般知識。本文では実測しないと明記。

## scope 外 (実装せず、裁定パッケージにもしない)

- runner の改版、案 A の試走 (build・identity)、verifier の容量改善、seed 注入、phase doc / paper-story の編集。
- 本書専用の解析 consumer、機械 gate の新設。

## 成果物

- `docs/b8-final-candidate-longrun-verify-preregistration.md` (新規)、`docs/README.md` の 1 bullet。
- 記録: insight `output/insights/2026-09-20/b8-longrun-verify-prereg/README.md` + codex/ 逐語、spool fragment (worklog・decisions)。
