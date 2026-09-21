---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2344-source-bound-emitters
seq: 1
title: [T-2344] enforcement source closure を 85 → 96 path へ進めた — 発行器 6 本と発行器起点にだけ居る 10 本の和 11 本を収載し、exact-85 を実在 corpus 未確認のまま歴史 grammar として同 commit 収載した (コード + test、branch worktree-dev-wave-t2344-source-bound-emitters、Codex author 1 commit、変異 13/13 KILLED + 対照 1 SURVIVED)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight 冒頭) の範囲で 1 wave。裁定 = D2194 項 4 (次段は発行器先行、記録済み exact-63 成果物の再解析は (c) 現状維持)、
  D2193 (1 段ずつ + 直前 grammar の歴史収載を同 commit)、D1884 / D1075、D1653 / D1770、D2081。一次資料は
  `output/insights/2026-09-21/t2344-closure-emitters/README.md` (brief・実測・plan・相談 2 本・裁定・実装子・レビュー 2 本・変異台帳・probe script の逐語)。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters/HANDOFF.md`。
- 起点 local main `5efd69367` (着手直前、fresh worktree)。実装前に `71e572b3c` を ff-only で取り込み (docs のみ、実装面差分 0)。全段構成 (受理集合が変わり
  正しさ防壁に触るため DW-C00 の独立敵対検証子): 段 2 plan 1、段 3 2 レンズ (real 11 / refuted 8)、段 5 author 1 (9 file)、段 6 レビュー 2 (NO-GO、ただし実装面 real 0)。
- **段 1 の実測で依頼の数え方を確定した:** 「発行器 6 本 + 発行器起点にだけ居る 10 本」は 5 本が重複するので**和 11 本**で、exact 85 → **96** になる
  (`autonomous_trial_completeness` だけは tuple 起点の発見集合に既に居た)。96 本を起点に辿った発見集合 173 は従来の和集合と同一集合で、未収載は 77。
  tuple 起点の 2 段目 23 本との重なりは 0 で、1 本も含めていない。
- **(P2) exact-85 の歴史収載は実在 corpus 未確認のまま行った ({{D:prior-grammar-collected-without-confirmed-corpus}}、裁定パッケージ)。**
  指定走査 (2 root・除外 dir・mtime ≥ 09-20 21:55、08:31〜08:45) で 85-key v2 は未検出。D1653 の corpus 条件は収載時点で未充足である。
  段 3 レンズ B と段 6 レビュー 2 本はこの点を must-fix とし (「既裁定から必然的に導けるように書くな」)、親は根拠を観測・生成可能性・予測・政策判断の
  4 層に分けて書き直し、裁定パッケージへ格上げした。判断材料: 直前 grammar の lock は tuple 前進後にも固定木から生まれうる (exact-63 で main の land 後に
  25 本、ただし同一木の反復で独立証拠ではない)。収載しない誤りは別 commit を要する空白を作り、収載しすぎる誤りは HISTORICAL_RAW の tuple が 1 個増えるだけ。
- 段 3 の主な real: capture だけの変異では起動 test は赤にならない (後段の live 検証が残る) / 「corpus 0 本」は走査条件を越えた断定 /
  収載は発行時点も実在 corpus も認証しない (合成 lock も読める) / `b10_backoff_shape_sweep` の report 分岐は現行 capture を通らない /
  「発行器 6 本」は certified consumer の全数ではない / `s8b_oracle_report` の unavailable 分岐の scope 追随漏れ / 受入増分は 6 群の部分外挿で下限寄り 16 秒。
- 段 6 レビュー A / B はいずれも NO-GO だが、**実装面の real 所見は 0 件**で、must-fix は親の文書 (裁定の根拠の書き方、実測資料の断定、要約の skip 説明) だけだった。
  fix 子は起動せず、親が job dir の資料へ訂正を追記し insight と decisions で閉じた。コード・test は 1 byte も変えていない (対応表は insight §4)。
- **受理集合の変化 (開示):** tuple 前進後の checkout では exact-85 で記録された campaign が certified の decode 段で拒否され、HISTORICAL_RAW でだけ読める。
  新 11 本は certified 受理時の clean committed 要求の対象になる (中央 capture を通る経路に限る。記録時と発行時の bytes 同一は D1163 のまま要求しない)。
  `artifact_admission.py` の bytes が変わるので新規 admission receipt の `validator.sha256` は変わる。
- 変異: 事前登録 14 件 (対照 M0 + 収載追加 3 + 歴史可読性 2 + 未知 grammar 3 + certified 隔離 2 + 歴史 scope 凍結 3)。probe 1 は**親が走行中に repo へ insight 下書きを
  作り untracked 検出で rc=2 中止** (DW-M05 違反、実害は再投入のみ)。probe 2 で 13 件の node を観測し、**M12 (現行 scope 対と 85 map を許す) は SURVIVED** —
  現行 scope 対は歴史 epoch の白名単に無く構築段で先に弾かれる mask だったため、実効 gate (歴史 scope 対と map の対応) へ再照準した M12b を probe 3 で観測し登録した
  (erratum は insight §6)。**final: 13 / 13 KILLED (期待 node 完全一致)、M0 SURVIVED** (M1 304 / M2 204 / M3 1 / M4 87 / M5 85 / M6 3 / M7 3 / M8 2 / M9 1 / M10 1 /
  M11 12 / M12b 1 / M13 88)。M0 の SURVIVED は runner に drift 核が無いことの実測である。
- 検査: 焦点走 f1 (31 file = 変更 test 6 + consumer + 新収載の自 test + DW-O26 の inventory 4 群、job 14685.nqsv) が **4441 passed / 9 skipped / 赤 0**、
  全史 provenance 監査 12268 件・新規違反なし、親の独立検算 (tuple 順序・exact-85 literal・歴史 scope の byte 同一・固定値 4 件) が全項一致。
- 言わないこと: 推移閉包が閉じた・certified 経路が source-bound (未収載 77)・発行器起点も閉じた・発行時 bytes と記録 bytes の同一性・exact-85 corpus が 0 本である。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight §7 に追記)。
- 工数: codex 子 6 本 (plan 1・consult 2・author 1・review 2、gpt-6-astra / medium)、計算ノード job = 焦点走 1 + 変異 probe 3 走 + final 1 走 + 受入全走 (件数は insight §7)。

## 次の一手差分

### 更新

- [T-2344] **P2・裁定済み (D1884、D2193、D2194 項 4) → 発行器先行の次段を実装済み (85 → 96、{{D:closure-stage-emitters-first}})、残るのは tuple 起点の 2 段目と裁定パッケージ 1 件**:
  発行器 6 本と発行器起点にだけ居る 10 本の和 11 本を収載し exact 96 にした。exact-85 は歴史閲覧 grammar として同 commit で収載済み。
  着手時 (2026-09-21、5efd69367) の 96 起点の発見集合 173 に対し未収載 77 が残り、「certified 経路が source-bound である」は推移閉包の意味では引き続き名乗らない。
  次段は D2194 項 4 が定めた順で tuple 起点の 2 段目 23 本。**裁定待ち 1 件** (一次資料 `output/insights/2026-09-21/t2344-closure-emitters/README.md` §8):
  exact-85 を実在 corpus 未確認のまま歴史収載したこと ({{D:prior-grammar-collected-without-confirmed-corpus}}) の是非 —
  (A) 現状維持、(B) 撤去、(C)「直前 grammar に限り corpus 条件を免除する」と明文化。推奨は (C)。
  base: d65c297d1e63e0e13af28024693153b1e3df33f436e82e15309161ff890176c4
