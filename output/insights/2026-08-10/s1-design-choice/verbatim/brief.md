# 段 1 brief — S1 設計択一 wave (段 7 cross-protocol の前提)

## scope

現行 main で「別 protocol への trace-hook 移植 (案 A)」と「stock 専用計測経路を規律 2
(別ビルド・別 run) と整合させる設計 (案 B)」の 2 案を、**実装コスト / 検証可能性 /
規律 1・2 との整合**の 3 軸で比較し、択一パッケージをユーザー裁定へ返す。**docs のみ。
本番コード・テスト・probe・script を一切書かない** (ユーザー明示 + 裁定 Q2 = (a)
「実装・実測は択一の裁定後に別途」)。

## 確定済みユーザー裁定

- スコープ B 部分再開 Q2 = (a) (2026-08-10、控え `rulings-inbox/2026-08-10-scope-b-reopen.md`)。
  本 wave は同裁定の W2。
- Q3 = (a) 並走ガード 3 条件 — (i) ノード同居なし (本 wave は計算ノード未使用)、
  (ii) T-139 job 走行中はキュー投入を控える (wave 開始時 qstat: 900495 RUN / 900512 PRR
  を観測、キュー投入しない)、(iii) 裁定帯域は A 優先。
- 不変: 8b の証拠価値限定、絶対規律 1〜6、T-139 追補 A 段階 2 の凍結・blob 束縛、
  roadmap 本体。

## 前提の実測 (DW-S01。ccbench pin = d706650)

- **(M1) si の trace-hook は既に存在する** — `cc/si/transaction.cc:13` が
  `include/trace.hh` を取り込み、`:526`–`:553` に commit path の `#if TRACE` 区画がある
  (版 ID = `(epoch=1, tid=cstamp)` 写像)。silo は同ファイル 13 箇所。
  **したがって phase3.md must 表 S1 行の「silo 内に閉じる」という現状記述は、
  移植の先例が既に 1 本あるという事実を落としている** (承認済み裁定を覆す新事実ではないが、
  コスト軸の前提を変える。段 4 で扱う)。
- **(M2) 遺伝子空間の登録は silo だけ** — `orchestrator/campaign/genome.py:88` の `SPACES`
  は `{"silo": SILO_SPACE}`、`space_for` は未登録で `KeyError`。build 面は
  `ycsb_<protocol>.exe` で parametric (`buildcache.py:500/667/835`)。
- **(M3) verify は COMMIT の必須前段** — `pipeline.py:843`–`873`、trace ディレクトリが空なら
  `trace-empty` abort。trace-hook のない protocol は fitness が WAL に載らない。
- **(M4) 規律 1 の機械防壁は protocol 非依存** — `_has_trace_symbols`
  (`buildcache.py:1021`–`1047`)、`calibrator/cli.py:203` は nm 出力の `izanagi_trace` を見るだけ。
- **(M5) 観測者効果の二重検査は silo 固定** — `source_digest.py:79` の
  `EVOLVE_BLOCK_SOURCES = ("include/backoff.hh", "cc/silo/transaction.cc")`、`:82` の
  `ALLOWLIST` も同 3 ファイル。移植先を編集面に入れるならこの 2 定数の拡張が要る。
- **(M6) ermia の版 ID 罠** — `docs/ccbench-anatomy.md:211`: 版 cstamp が `cstamp<<1`
  (低ビット = SSN flag)、commit 経路 2 系統。si の hook はそのままでは流用不可。
- **(M7) D44 注意** — 案 B は「対抗馬だけ certified 要件を免除する非対称比較」になる
  (`docs/phase3.md:349`–`350`)。

## 不変条件

- 規律 1 (観測者効果の分離)、規律 2 (正しさゲートを緩めない)、規律 3 は本 wave で緩めない。
  **案 B が「verify を通らない計測値」を作る設計である以上、規律 2 との整合は評価軸でなく
  合否条件として扱う。**
- 実装差分ゼロ。凍結 bytes・proof chain・oracle gate の実体には触れない (DW-O08/O09/O10 は
  docs のみのため bytes 変更なし。worklog fragment と insights のみ新規)。
- phase3.md must 表・後続段の本文改訂は本 wave では行わない (択一の裁定後)。

## 成果物

1. 裁定パッケージ 1 枚 (`dev-wave-jobs/dev-wave-s1-design-choice/ruling-package.md`) —
   2 案 × 3 軸の比較表、推奨、択一問、不変事項。
2. worklog fragment (spool 形式)、insights の逐語凍結、必要なら decisions fragment。

## 成果物影響 (DW-G05)

択一を決めないままだと、段 7 cross-protocol は着手できず、**certified 選択結果に protocol
軸の対照行が 1 行も立たない** (M3 により第 2 protocol の fitness が WAL に到達しないため)。
案 B を選んだ場合は、対抗馬側の行に certified の proof 参照が付かない非対称レポートになる
(M7)。この差が成果物 (certified 選択・材料レポート・試行台帳) に出る値の差である。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 案 A は si の先例 (M1) により「新規移植」ではなく「2 本目の展開」であり、
  実装コスト軸で従来想定より安い。ただし移植先が ermia なら M6 の罠でコストは si 比で跳ねる。
- **(P2)** 案 B は規律 2 と原理的に整合しない (verify を通らない値を比較の片側に置く)
  のではなく、**「stock 側を certified の外に出す」ことを明示的に宣言できるなら整合する**。
  争点は整合の可否ではなく、非対称比較が headline の主張として成立するかである。
- **(P3)** 2 案は排他ではなく、案 B を暫定 (scouting) に使い案 A を本比較に使う段階案が
  第 3 の選択肢になりうる。

## 分割方針

段 2 = codex 1 本 (read-only, reasoning=max) が file:line 粒度で 2 案を起草。
段 3 = codex 2 本並列 (異なるレンズ、`gpt-5.6-sol` → `gpt-5.6-luna`) が plan と本 brief を攻撃。
実装面ゼロのため段 5・6 は飛ばし、段 4 で「実装しない」裁定 → 4→7→8→9。
