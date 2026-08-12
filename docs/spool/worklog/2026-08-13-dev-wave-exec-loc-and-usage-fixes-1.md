---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-exec-loc-and-usage-fixes
seq: 1
title: 実行場所分類を台帳へ反映し、wave 使用量 collector の 2 バグを直した — class は unknown 据置、collision 誤判定は usage dominance で解いた (コード + docs、変異 5/5 KILLED、branch worktree-dev-wave-exec-loc-and-usage-fixes)
---

## 本文

ユーザーが実行場所分類の**選択**を AI へ明示委任した (rulings 第 7 束、「あなたが適切なところを
選んでください」) のを受け、別 job が計算ノードで得た実測を台帳へ反映し、併せて使用量 collector と
ledger の 2 バグを直した。

- **分類は `unknown` 据置とした。** 指示は `local-ok` として反映することだったが、2 つの理由で
  据え置いた。(a) 実測は §7.0 の canonical な専有 scope 手順ではなく共有 service cgroup の
  delta sampling である。(b) 測ったのは ledger 既定 argv (25 file) で、本番 helper が渡す
  `--max-files=1000` の cap 境界を測っていない。**hook の受理 bit は 1 つも変わっていない。**
  変えたのは `reason` / `primary_gate` / `evidence` の 3 field だけである。
- **`local-ok` にできない構造的理由も別にある。** `tools/pegasus_admission_registry.py` と
  `hooks/guard_bash.py` は非 `tools/pegasus/` path の `local-ok` を禁止しており、
  専用 negative test 3 本が張られている。この禁止は「適用 path を広げても受理集合は単調に縮む」
  (D175 決定 6) を成立させている当の機構なので、撤去せず {{D:exec-loc-classification-unknown-hold}}
  として据置を裁定した。
- **evidence の数値は 2 度直した。** 一次資料 README と依頼文はどちらも最大 delta を `20.6 MiB` と
  書いていたが、`842317824 − 821682176 = 20,635,648 bytes` は **19.7 MiB** であり 20.6 は MB 値だった。
  さらに敵対レビューが「5 valid runs」表記の問題を指摘した — ledger 6 走はすべて command `rc=2`
  (当時の collision 誤判定) であり、5 は「成功した走」ではなく「正の delta を得た sample 数」である。
  最終 evidence には測定 commit `04d85f93`、1,045 file 中 25 file・4,728,545 bytes・`limit_reached`、
  非 certifying であることを書いた。一次資料 README には原文を残したまま erratum を追記した。
- **collision 誤判定は「降格」ではなく dedup で解いた。** 並列 subagent の transcript へ同一 model call
  が複製されると `message_id_collision` で rc=2 になり使用量が 1 件も記録されなかった。
  親の初案「終端 usage 全一致なら同一」は敵対レビューが**実データで反証**した — 実入力には
  同一 message.id で終端 `output_tokens` が 10933 と 3 の群 (streaming 途中の部分 snapshot) がある。
  採ったのは **usage dominance** で、支配 candidate が存在しなければ従来どおり fatal に倒す
  ({{D:message-id-replica-dominance}})。既存 negative test の期待値は 1 文字も変えていない。
- **collector は内側 argv の等号化と rc の fail-closed 化を行った。** 外側 argv の正規化は
  敵対レビューの指摘で**採らなかった** — 未知 option・argparse の省略形・単独 `-` を値として飲み、
  受理集合を広げるためである。`blocked` は「login と確証できた」を rc=3、「site 証拠が壊れている」を
  rc=1 に分けた ({{D:usage-collector-exit-code-contract}})。

**scope 外の real 所見 4 件を裁定パッケージへ返した** (`output/insights/2026-08-13_exec-loc-and-usage-fixes/s4-rulings-package.md`)。
最重要は **R-1: registry の class を何に変えても段 9 の収集は login で blocked のままである** —
`collect_wave_usage.py` は site だけを見て admission registry を参照しない。D233 決定 4 の理由文が
書く「分類が済んだ時点で同じ契約のまま収集が始まる」という結線は実装されていない。

**工数と異常:**
- codex 子 9 本 (plan 1 / consult 2 / author 3 / review 2 / fix 1)。うち review 2 本は
  `admission_registry.json` の未コミット差分で hook 配線検証に弾かれ launcher_error で 2 回失敗し、
  統合 commit 後に再投入して成功した。
- 待ち手が producer 生存・成果物不在のまま exit 0 を返す事象を 1 件観測した ({{F:waiter-zero-before-artifact}})。
- 段 5 は `DW-S05-A` の「単位ごとに worktree を分ける」を実行できなかった。隔離背景セッションは
  sibling worktree への git 操作が guard に拒否されるためで、代わりに所有ファイル集合を素集合にし、
  各子へ所有外編集と git 操作を明示禁止し、統合前に `git diff --stat` で所有範囲を検証した。

**実測:**
- 焦点走 (4 ファイル): 実装後 741 passed / 1 skipped、段 6 fix 後 **754 passed / 1 skipped**、rc=0。
- 変異: **5/5 KILLED**、MISMATCH 0、SURVIVED 0、baseline PASSED。
  期待 node は `DW-M08` に従い初回を probe と明記して実測から再導出した (probe 台帳も残した)。
  MUT-3 (dominance を常に真) で `test_incomparable_usage_replicas_remain_fatal` が落ちず、
  同 fixture が dominance 以外の gate で過剰決定されていることが判明した (`DW-M03`)。
- **未確認として残るもの:** 実 1,045 file 入力の 30 collision 群を現行 resolver へ通した確認は
  していない。敵対レビュー A が stderr 30 行を型分類し (1〜2 = sidechain 等値、3 = 一意支配、
  4〜30 = root-root 等値)、静的には全群が解けると評価しているが、実走は分類の手番が閉じるまで行わない。

## 次の一手差分

### 新規

- {{T:usage-collection-site-wiring}} **P1・ユーザー裁定待ち**: 段 9 の使用量収集を login で受理する
  結線 (registry × hook × site_policy × collector) を作るか、D233 の理由文から
  「分類が済んだ時点で収集が始まる」を削って実装と説明を一致させるかを決める。裁定パッケージ R-1。
- {{T:nonpegasus-local-ok-allowlist}} **P2・ユーザー裁定待ち**: 非 `tools/pegasus/` path へ
  `local-ok` を付けるための exact allowlist を作るか否か。裁定パッケージ R-2。
- {{T:classification-delegation-scope}} **P1・ユーザー裁定待ち**: 分類実測の手番委任の射程。
  計算ノードでの非 canonical 測定を補助証拠として台帳へ入れてよいか、その線引きを規範へ書くか。
  裁定パッケージ R-3。
- {{T:admission-argv-scope}} **P2・ユーザー裁定待ち**: 分類を argv 単位にするか path 単位のままにするか。
  測定対象を本番 caller の argv に合わせるのが親推奨。裁定パッケージ R-4。
- {{T:ledger-real-input-verification}} **P2・新規**: 実 1,045 file 入力の 30 collision 群を
  現行 resolver へ通して全群が解けることを確認する。実行場所の手番が閉じてから計算ノードで行う。
- {{T:incomparable-fixture-overdetermined}} **P3・新規**: `test_incomparable_usage_replicas_remain_fatal`
  の fixture が dominance 以外の gate で過剰決定されている。単一理由へ差し替えるか冗長 gate と明記する。
