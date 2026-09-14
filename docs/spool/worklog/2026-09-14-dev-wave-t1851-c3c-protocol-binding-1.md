---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1851-c3c-protocol-binding
seq: 1
title: [T-1851] official 床値の許可表を resolver が選んだ protocol の実 path へ束縛し、史上初の投入を塞いでいた取り違えを閉じた (コード + docs、branch worktree-dev-wave-t1851-c3c-protocol-binding)
---

## 本文

- ユーザー指示は「3 件を同一 land 単位で実装する。残るのは D1936 項 11 の resolved protocol 束縛の
  修正と C3c の実装。被覆の全単射照合は B2 の scope なので触らない。新規 official 床値本走は含めず
  FORMULA_ID を維持する。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。**official 床値の投入は本 wave では行っていない。** 実値域の供給は後続へ残した。
- 設計判断は {{D:floor-allowlist-binds-resolved-protocol-exact-path}} と
  {{D:private-core-official-seam-falls-back-to-legacy-anchor}}。
- **親が段 4 で書いた前提 1 件が実測で覆った。** plan v2 は「official は必ず公開入口経由で
  authority record を持つ」として record 不在の fail-closed を命じたが、共有 fixture が private core を
  official mode で直接呼ぶため既存テスト 28 件が落ちた。追記の裁定で撤回し、fallback へ直した。
  親の裁定であってユーザー裁定ではない。
- 段 3 は 11 所見中 real 6・refuted 5、段 6 は 11 所見中 real 5・refuted 7。**scope 外の real は
  段 3・段 6 とも 0 件で、ユーザーへ返す裁定パッケージは無い。**
- 棄却した所見: legacy entry の自己 hash 化による恒真化 (直前の `historical_protocol` 比較が必須経路に
  あるため refuted)、世代別 protocol を有界集合へ移すことによる被覆欠落 (refuted)、負例が先行 gate に
  必ず遮られる (refuted)、裁定の fallback が production を弱める (refuted)。
- **レビューの must-fix 1 件を nit へ格下げした。** 正例が起動証明書の file 発行段まで到達しない件は、
  「放置しても成果物の値・受理集合・参照が変わらない」ため。到達範囲は「証明書の構成と strict 検証まで」
  と記録し、file 発行まで検証したとは書かない。
- セッション異常 2 件。(1) 段 6 の fix 子 1 本目が model call 上限 100 に当たり、**編集は正しく
  入れたまま報告を出さずに終了**した。親が差分を現物監査して採用し、レビューへ裏取りさせた。
  (2) 変異 wrapper (`tools/mutation_worktree.py`) が共有木の事後検査で rc=125 になった。並行 session の
  churn が原因で、harness の直接経路へ切り替えた。
- 非帰属赤 1 件の機序を特定した ({{F:narrow-selection-defers-site-neutralization}})。狭い file 選択走に
  固有で、対象 module を一緒に収集すると消える。変更面を基底へ戻しても再現するため本 wave に帰属しない。
- 工数: codex 子 7 本 (plan 1 / 敵対 2 / 実装 1 / fix 2 / 焦点 1)。うち 1 本が上限死、
  1 本が argv 違反で即死 (`--lane` は consult 専用)。
- **段 8 の自己改善は候補 2 件とも「実施しない」で閉じた** (D782 が委任する D730 の手順による)。
  どちらも実測由来だが独立 1 例しかなく、例外収容の 3 例条件を満たさない。上限引き上げはしていない。
  (a) sandbox の子はテストを実走できない (runner `rc=16`、`pytest` は guard 拒否、使えるのは
  test file 末尾の自走 harness だけで、growth hold 対象 file はそれも拒む) — 手順として
  `DW-S05-C` へ足すと L1.5 予算を 195 bytes 超過する。予算の空きは 0 bytes だった。
  (b) `DW-S05-A` の所有 path 限定 patch の手順 (`git add -A` → `git diff --cached` → `git apply`) は
  **隔離 session から実行できない** — guard が子 worktree への git を拒む。本 wave は base blob との
  内容 hash 全数照合 (24676 file) で変更集合を確定し、所有 path だけを byte 等値で複写した。
  是正文を予算内に収めるには当該段落の書き換えが要るが、`test_dev_wave_launch_authority.py` の
  独立照合 6 件がその本文を構造的に読むため赤になる (実測: 編集時 6 failed / 58 passed、
  戻すと 64 passed)。次に同型を 2 回踏んだ wave が D730 の例外条件で収容できるよう証拠を残す。

## 次の一手差分

### 完了

- [T-1946] 試行台帳の proof chain 束縛は単位 A〜D2 で実装済みで、本 wave の許可表修正をもって
  同一 land 単位が揃った。
  remaining: none
  base: b6026ca2c5ce6d3606110ab9f3638991691f440eed75cf1de3052fcb2f94a108
- [T-2107] 床値 campaign から試行台帳の書き手への配線は単位 C3a で実装済みで、本 wave の
  許可表修正をもって同一 land 単位が揃った。
  remaining: none
  base: a425a0ecf26dacbc7cacd87342f5bf3f1d24669c2b859f9675855912b3934507

### 更新

- [T-1851] **P1・項11 修正着地、実値域は未取得**: 起動証明書の許可表を resolver が選んだ protocol の
  実 path へ束縛し直した。受理する path は呼び手が渡した exact 1 件だけで、族ごとの受理はしない。
  凍結 23 件の bytes、FORMULA_ID、凍結保留の全体は変えていない。**official 床値 campaign は
  投入していない。** 残るのは (a) C3c の実値域取得 — official 床値を投入し、契約 9 節が要求する
  試行台帳側 gate の実値域を初めて供給する。凍結世代は 1 件も焼けていないので同じ世代で走らせられる。
  (b) D1909 の後続版整理。
  base: ef32c26c35f54e52ce306d35e1d73cdd76b061390cdd174835dfa563e3381736

### 新規

- {{T:runbook-stale-acceptance-path}} **P2・新規**: `docs/pegasus-runbook.md` の受入節から、
  機構から外れた受理経路の記述を消す。`tools/check_acceptance_reds.py` は file として実在するが
  `tools/dev_wave_wait.py` からの参照は 0 件で、受入は `child-green` だけを受理する。
  廃止語の禁止検査は `docs/dev-wave/operations.md` にしか掛かっていない。
