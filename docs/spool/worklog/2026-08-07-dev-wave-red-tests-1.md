---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-red-tests
seq: 1
title: repo の赤を全数実測した — テスト本体は全緑で、赤は provenance 監査 1 本だけ。規約内に修復経路が無いので択一を返す (docs のみ、実装差分なし、branch worktree-dev-wave-red-tests)
---

## 本文

- **テスト本体に赤は 1 件も無かった。** 受入形 (引数なし) の全走で
  6837 passed / 20 skipped / 0 failed。`check_docs` / `check_codex_agents` /
  `check_wave_startup` / `ruleops check` / `spool_fold --dry-run` もすべて緑。
  **赤は `check_ai_provenance.py` の全履歴監査 1 本だけ** (1587 件中 6 違反)。
  正本 = `output/insights/2026-08-07_red-test-audit/README.md`。
- **その 6 件は規約の内側では直せない。** 段 3 の独立 codex に「緑へ戻す経路がある」方向から
  攻めさせたが反証できなかった。forward correction は target がコードに固定され枠は消費済み、
  waiver は当該 commit のみで遡及不可、後続の revert / 削除でも相殺されない。誤検出説も否定。
  緑化には履歴書き換え・gate 設計変更・allowlist・waiver 契約変更のいずれかが要り、
  **すべてユーザー裁定の領分**なので親は実装せず択一を返した ({{T:provenance-red-repair}})。
- **親の provisional 裁定 4 件のうち 2 件が敵対検証で覆った。** (i)「この赤は land を止めないので
  blocker でない」は誤り — `dev_wave_land.py` は止めないが `DW-O17` の全履歴監査が commit 段で
  止める契約であり、**6 違反が入った時点から全 wave の commit gate が恒久的に赤**で、
  各 wave が手で帰属して跨ぐ運用になっている。(ii)「`run_tests.py` の 4 gate が選択 flag を
  拒否する」も誤り — 分類するだけで拒否しない。
- **親自身が受入形でない走行を受入と呼びかけた** ({{F:acceptance-shape-silent-gate-skip}})。
  `-rf` を足すと `_is_acceptance_run()` が False になり事前検査 2 件が黙って発火しない。
  同時刻に別 wave も同じ形で走らせており独立 2 例。受入形で走り直して記録した。
- **実装差分を持たない wave である。** tracked な変更は insights の docs と spool fragment だけで、
  コード・テスト・機械設定を 1 行も変えていない。したがって**変異 matrix は射程外**。
  受入全走は「差分の検証」ではなく**依頼そのものの実測**として行った。
- 20 skipped は発生源 23 ファイルに閉じることを別走行 (1389 passed / 20 skipped) で確認した。
  件数は前 wave (271) と同一。個別の skip 理由は `-rs` と `-rf` を並べた後勝ちで取得できず、
  **未取得のまま記録する** (submodule 未取得由来の skip だけは初期化済みで発火していない)。
- `audit_dangling_commits.py` は rc=1 (取り残しあり) だが、これは人間確認向けの報告であって
  検査の赤ではない。裁定 inbox に既出のため新規起票しない。

## 次の一手差分

### 新規

- {{T:provenance-red-repair}} **P1・ユーザー裁定待ち**: `check_ai_provenance.py` の全履歴監査に
  残る 6 違反 (merge commit 5 件の trailer 欠落 + `b0a07672` の実装面 author 欠落) をどう扱うか。
  択一は (1) 現状維持 (2) forward correction の一般化 = 親の推奨 (3) 既知違反台帳
  (4) 履歴書き換え = 非推奨。正本 = `output/insights/2026-08-07_red-test-audit/README.md`。
  併せて `run_tests.py` に「受入形でない走行への 1 行警告」を足すかも諮っている。
  実装はいずれも実装面のため Codex `role=author` が書く。
