---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-22
wave: dev-wave-t2854-tpcc-verifier-v3
seq: 1
title: TPC-C 段 1 の verifier 側 ([T-2854] 単位 4) — trace v3 を (表, key) で読み、cycle に表と取引種別を載せ、存在履歴を検査するまで v3 の run は認定しない (コード + テスト + insight、branch worktree-dev-wave-t2854-tpcc-verifier-v3)
---

## 本文

- **何をしたか:** 設計 `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §7.1 の単位 4。verifier が C 10 token・R/W/X/I に表番号を持つ
  v3 を読み、object 経路と compact 経路 (packed / tuple) のすべてで (表, hex) を 1 object とし、cycle の理由に表・節点に取引種別を載せる
  (`core.result_to_dict_v3`)。v2 (YCSB) の受理・判定・出力は不変。受理契約と認定の保留は {{D:tpcc-v3-verifier-contract}}。一次資料
  `output/insights/2026-09-22/t2854-tpcc-verifier-v3/README.md` (各段の逐語 `verbatim/`、変異台帳 `mutation/`)。
- **commit:** `0b0509d6e` (実装、Codex author) → `788657426`・`d1dd82f81`・`99410ebd4` (試験の fix 3 本、Codex fix)。production 4 file は追加 205・削除 61、
  test_verifier.py は 18 試験・追加 490 行 (段 4 の上限 550 / 800 の内側)、既存試験の変更 0 行。
- **段 3 の must-fix (2 レンズ一致):** 設計 §3.3 の存在履歴を検査しないまま v3 を受理すると、「初期に無い key を genesis から読む」「DELETE 版を
  存在する値として読む」trace が certified になる (pipeline は `ycsb_` 以外を trace の前に拒否するが公開 API・CLI は通らない)。段 4 で
  v3 の run を本 wave の verifier では認定しない印 (`Integrity.v3_existence_unverified`) を裁定。**§3.3 の実装とこの印の撤去が、v3 を認定に使う
  前提として残る** (設計 §7.1 の単位表に担当が無い)。並走の単位 1・2 wave [058df1] へ共有済み。
- **レビュー:** 段 3 相談 2 本 (must-fix 1 件で一致、schema 照合の 7 手順を過大として単純規則 1 helper へ)、段 6 review 2 本 (GO・must-fix 0、
  should 4 件 = 試験の実効を採用)、焦点再レビュー 2 巡 (1 巡目 NO-GO = packed / tuple の肯定確認が legacy 枝の内側、fix3 後 GO)。
  refuted = 段 6 レビュー A の 10 項目 (偽の認定・identity・v2 不変・混在・厳格検査・構造化・試験の実体・既存試験の変更) とレビュー B の 5 項目。
- **検査:** 焦点走 (test_verifier.py + verifier を参照する consumer 23 本 + inventory 4 群) 3,532 passed / 3 skipped / 0 failed (`788657426`)、
  単独走 132 passed (`99410ebd4`)、変異本走 19 / 19 が事前登録どおり (事前登録 17 変異すべて KILLED・等価 1 SURVIVED・診断 1 検出、
  probe-1 の M15a / M15b は v2 共有行を変えて既存試験も赤にしたので照準を直した erratum を insight に記録)。AI provenance 全史監査は各 commit 後に新規違反なし。
  受入全走は本記録の commit 後、同じ tip で land 直前に 1 回行う (本エントリの時点では未実施)。
- **計算量 (D2219 項 1 の線):** 焦点走 2 回 237 s + 変異本走 20 走 ≤ 828 s (queue 待ち込み) ≈ 0.30 node 時間に、受入 1 回 ≈ 0.25 node 時間
  (直近の単価の換算) を足して約 0.55 node 時間の見込み。2 node 時間の線の内側なので事前確認は取っていない。変異 probe と単独走は login。
- **異常と救出:** (a) 最初の `git worktree add` が展開中に EINTR で失敗し branch だけ残った。同 branch で作り直した。(b) job dir 作成 (08:54 JST) から
  worktree 完成までに約 11 時間の空白があり、開始 gate は main を取り込んだ後の 19:50 に打った。(c) 起動 wrapper 経由で `--dry-run` したため
  wrapper が .done / .pid を作り、本番の job-id を変えた。(d) 変異用 clone の対象 SHA を短縮形から推測で手打ちし、update-ref が存在しない
  object で止まった (実害なし、rev-parse の値で作り直し)。
- **工数:** Codex 子 11 本 (plan 1・consult 2・author 1・fix 3・review 2・focus 2、全て gpt-6-astra)、Explore 子 1 本 (sonnet、pin 閉包)。
  並走 wave との擦り合わせ 3 往復 (v3 の形、worklog の [T-2854] 項目の更新は後に land する側が両方の成果を統合する取り決め)。

## 次の一手差分
