---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t1851-c3c-official-floor
seq: 1
title: [T-1851] official 床値 campaign を 3 回実投入し、起動証明書を初めて通して真の blocker を実値で特定した (コード + docs、branch worktree-dev-wave-t1851-c3c-official-floor、変異 M1-M3/M5-M7 登録・M4 は単一理由性に絞れず取り下げ、harness 本走は未実施)
---

## 本文

- ユーザー依頼は「official 床値 campaign を実投入し、試行台帳側 gate の実値域を取る。phase3.md の
  単位 C3c が『official 床値 campaign は投入しておらず、試行台帳側 gate の実値域は未取得のまま
  後続に残る』と明記している。許可表を resolver が選んだ protocol の実 path へ束縛する修正は
  着地済み。投入前に、較正 ([T-2592] / [T-2515]) の着地がこの実走の前提になるかを phase doc と
  decisions で確かめ、前提なら待たずに済む範囲を切り出す。凍結 23 件の bytes・FORMULA_ID は不変。
  規律 2 を緩めない。Codex author = D95。本題の実装だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」。
- **依頼が問うた較正の前提は「前提ではない」。** 有効な pegasus 契約は世代 1 で、その
  `calibration_ref` の現物 bytes が契約の期待 sha256 と一致する。T-2515 が取得した較正成果物は
  phase doc の 1 行からしか参照されず production の consumer が無い。床値 campaign の holdout は
  T-2515 / T-2592 が扱う軸と別である。3 走行はいずれも較正検証を通過して先へ進んだ。
  **ただし段 3 のレンズが親の説明を訂正した** — authority 初期化は activation に載る**全環境**の
  較正を検証するので依存先は 1 件ではない (linux-baremetal のぶんもある)。レンズが両方の現物
  hash 一致を確認した。実機 toolchain の適合は login node では測れない。
- **3 回投入した。** `998882.nqsv` / `999039.nqsv` / `999102.nqsv`。いずれも
  `submit_floor.sh --confirm-official-floor-run` の sanctioned 経路で、承認は D926 の submission
  nonce 束縛で運ばれた。job script sha256 は 3 走行とも 2026-09-09 の初回 official と同一で、
  D926 の literal 保持が効いている。この同一性は D323 違反ではない (D323 は pilot から official を
  開く際の裁定)。
- **起動証明書を史上初めて通した。** 2026-09-09 の走行を止めた
  `launch certificate: freeze allowlist hash 不一致` は 3 走行の driver stderr に 1 行も出ていない。
  **D2013 / D2014 の修正が実機で効いたことの初の観測**である。証明書 file も発行され、
  C3c insight が「未到達」と書いていた面を越えた。発行された `clean_scan_digest` は 3 走行で
  すべて異なり、**digest の preimage が repository の file 一覧を含む** (F39 の性質) ことが
  実測で確認できた。
- **台帳消費はゼロで、bytes で裏取りした。** 共有 admission root の投入前後 snapshot は取得時刻行
  以外完全一致 (件数 10 種、ledger 2 本の行数と sha256、registry namespace、registry / catalog の
  sha256)。段 3 レンズ B の事前判定「registry reservation 前の停止 → 消費 0」が裏付けられた。
  計測枠の上限 120 は 1 枠も焼いていない。**列挙した数量と bytes/hash の一致に限定した主張**であり、
  同件数の内容変更をこの観測は弁別しない (レンズ A の指摘)。
- **試行台帳側 gate の実値域は取得できていない。** 走行は計測段へ到達しない。C3b の 4 分類のうち
  埋まったのは (1) 動的観測の一部だけで、(2) 静的宣言 closure、(3) artifact に所在が無い入力、
  (4) 未発火の枝は依然未観測である。**未観測を到達不能と読んではならない。**
- **代わりに、走行を実際に塞いでいる gate の入力の完全な実値を取った。** 3 走行すべてが cell build
  段の condition gate で `BACKOFF_FIXED:supply-effectuation:preprocess-failed` により停止した。
  1 回目は reason code 2 語しか残らず、失敗本文は job 終了と共に失われた。実装後の 3 回目で全文が
  復元でき、原因は **Masstree の autoconf 生成 header `config.h` が前処理の include path に無い**
  ことだった (`masstree_wrapper.hh:20` の `#include <config.h>` が fatal error)。
  **`BACKOFF_FIXED` の供給失敗ではない** — argv に `-DBACKOFF_FIXED=10` と `-DMASSTREE_USE=1` が
  載っており patch による供給は成功している。T-2515 の過去 job の `configure-failed`
  (patch 未適用経路) とも別原因である。
- **実装は D1912 の欠陥の第 2 実例を 1 箇所だけ直した。** 失敗本文が raise 時点で捨てられる形は
  D1912 が `p3_s4_loop.py` で直した欠陥と同型で、D1912 自身が `DW-G03` (族一般化には独立 2 例) を
  理由に兄弟 driver へ横展開しないと明記していた。official 床値の materializer で再現したので
  条件が満たされ、`s1_direct_comparison.py` だけを直した。設計判断は {{D:condition-detail-both-ends}}。
- **段 5 の初稿は実機で誤りが露出した。** `condition_meaning_gate` の argv 用 helper を流用したため
  先頭 500 bytes だけが残り、**コンパイラ診断は末尾に結論が来る**ので実 error 行が落ちた
  (original 1057 bytes の後半 557 bytes)。2 回目の走行でこれが判明し、段 6 の fix で先頭と末尾の
  両方を残す形へ直した。**予算の意味が違うものを流用したのが誤り**で、これは
  {{F:argv-budget-reused-for-diagnostics}}。
- **変異 M4 は単一理由性に絞れず登録から外した** (`DW-M01` / F28)。実装子の実測で、reviewed-spec
  golden の RAW だけを変えると live hash gate より先に RAW 全体の approval pin 比較が
  `approved-spec-hash-mismatch` で拒否することが判った。M4 の赤は live hash gate の証拠にならない。
- **変異 harness の本走は行っていない。** 実装差分が生じたので `DW-S04` の matrix 免除は使えない。
  代わりに 3 回の実機走行で M1-M3 / M5-M7 が守る性質を production 経路で直接観測した
  (1 回目は detail なし、2 回目は先頭のみ、3 回目は先頭と末尾) が、**これは harness による
  kill 判定の代替ではない**。
- **pin 閉包は reviewed-spec golden の hash 連鎖 1 件だった。** `s1_direct_comparison.py` の bytes を
  変えると `test_s8b_oracle_manifest.py` の golden が破れる (golden は live repo から複製した file を
  検証対象にする)。`DW-S05-C` / F27 が「fixture への現行 hash 差し込み」を禁じているため、
  実装子と fix 子の双方に旧値・新値の両方報告と「RAW の変更が 1 field だけ」の提示を義務づけ、
  両者とも bytes 一致を確認して報告した。歴史記録の insight は絶対規律 7 に従い触っていない。
- **段 3 の 2 レンズは実装差分そのものを見ていない。** 実装が必要と判明したのが走行後で、レンズは
  走行前に plan と brief を攻撃した。実装差分への敵対レビューは行っていない。
- 親の断定を 7 点訂正した — (P4) の「二重比較は解消した」は誤りで**同一比較の二重化は残る**
  (hold の効力は主張しない、D1936 項11)、288 は消費可能予算ではなく計測枠上限は 120、
  probe の raw 四値は artifact に所在がある、時間モデルは `buildcache` が configure と build の
  それぞれに 900 秒を渡すので command timeout の単純和は 41940 秒、
  「現行 CCBench pin に `BACKOFF_FIXED` が無いので原理的に緑にならない」は誤り (patch が供給する)、
  snapshot の件数一致は履歴不変を意味しない、(P1) の依存先説明が狭かった。
- 工数: codex 子 5 本 (plan 1 = medium、consult 2 = medium 2 レンズ、author 1、fix 1)。
  段 6 の敵対レビュー 2 本は起動していない。

## 次の一手差分

### 更新

- [T-1851] **P1・裁定済み (D1936 項14) → official 床値の投入は済。次の blocker は Masstree の
  生成 header 供給**: official 床値 campaign を 3 回投入し、起動証明書を初めて通した
  (D2013 / D2014 の実機初検証)。台帳消費はゼロ。**試行台帳側 gate の実値域は依然未取得**で、
  走行は cell build 段の condition gate で止まる。真の blocker は
  **Masstree の autoconf 生成 header `config.h` が condition gate の前処理 include path に
  無いこと**で、実値は `output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md` §4 に
  全部揃っている。`BACKOFF_FIXED` の供給自体は成功している。build 供給の subsystem なので
  本 wave では触らず後続へ残す。
  base: e74260882c9a21ab4475c85b086360612d0854a733419f799b44ae49864ce5f5

### 新規

- {{T:floor-gate-masstree-config-header}} **P1・新規**: condition gate の isolate worktree へ
  Masstree の autoconf 生成 header `config.h` を供給する。official 床値 campaign が 3 走行とも
  `masstree_wrapper.hh:20` の `#include <config.h>` で前処理に失敗して止まっている。
  実値と argv 全文の sha256 は `output/insights/2026-09-15/t1851-c3c-official-floor-run/README.md`
  §4 にある。これが解けるまで試行台帳側 gate の実値域は取得できない。
- {{T:floor-implementation-adversarial-review}} **P2・新規**: 本 wave が着地させた
  `s1_direct_comparison.py` の診断本文保持について、実装差分そのものへの敵対レビューと
  変異 harness 本走を行う。段 3 のレンズは走行前に plan と brief を攻撃したため実装差分を
  見ていない。登録済み変異は M1-M3 / M5-M7 の 6 件 (M4 は単一理由性に絞れず取り下げ済み)。
