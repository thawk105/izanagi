---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2124-s1-epoch-historical
seq: 1
title: [T-2124] D1387 に従い S-1 の epoch gate だけを歴史 purpose へ移した — E0 拒否は局所で残し、実関数を通る負例で初めて固定した (コード + テスト、branch worktree-dev-wave-t2124-s1-epoch-historical、変異 4/4 KILLED)
---

## 本文

- ユーザー裁定 D1387 の実装。3 消費者のうち S-1 の epoch gate だけを
  `CERTIFIED_ACCEPTANCE` から `HISTORICAL_RAW` へ移した。`replay.load_landscape` と
  `s8b_oracle_report` の epoch 証拠は移していない。`artifact_admission.py` は 1 byte も変えていない。
- 受理・拒否の変化は 1 点だけである。正しい v2 / E1 に対して現行閉包が取得できない場合、
  変更前は `E1-stale / current-closure-unavailable` で拒否し、変更後は
  `E1 / recorded-closure` として受理する。段 3 レンズ A が
  `_require_verifier_epoch_for_purpose` の全分岐を列挙し、これ以外の緩和が混入していないことを
  実物で確認した。これは D1387 が明示的に許した緩和である。
- **依頼文が名指しした対象 file が実測で外れた。** 依頼文は
  `orchestrator/campaign/s1_direct_comparison.py` 周辺としていたが、同 file 1353 行に
  `epoch` の出現は 0 件で、gate は `s1_report.py` にあった。段 3 の両レンズが実経路でも
  同 module に epoch 判断の別形が無いことを確認した。
- **E0 拒否は本 wave まで実関数の位置で pin されていなかった。** `test_s1_report.py` の
  autouse fixture が対象関数を module 全体で固定 E1 の lambda へ差し替えており、既存の E0 負例も
  同関数自体を monkeypatch して合成例外を投げていた。本 wave が実 callee 経由へ直した。
- **親 brief の実測 1 件が過大一般化で、段 3 の両レンズが独立に捕らえた。** 親は
  「`output/campaigns/` 30 件全部が v1 なので既存 30 件の S-1 出力は 1 byte も変わらない」と書いたが、
  S-1 が読むのは freeze と `ROLES` から決まる 4 campaign だけで、`--output-root` は repo 外の
  正規 root も指せる。訂正後の主張は「repo 内 official root の canonical S-1 campaign 4 件は
  いずれも v1 lock で、epoch 判定は変更前後とも E0 拒否」である。
- **段 2 プランの一部を段 4 で不採用にした。** 拒否 reason envelope 全体の exact dict 比較と
  `identity_scope` / `excluded_scope` の literal 固定は、(a) 既存 node がすでに同じ変異を殺すため
  検出力を増やさず、(b) 稼働中の T-733 が同 scope 文字列を 24 path から 62 path の文言へ
  変えているため、literal を書けば正しい実装でも T-733 着地時に落ちる。
  編集面の重複検査 (32 worktree、committed 差分と未 commit dirt) は path の重複しか見ないため、
  この型を捕らえない。詳細は insight。
- 段 3 レンズ 2 本・段 6 レビュー 2 本。段 6 のレビュー A は所見ゼロ、レビュー B は 4 件
  (real 1・nit 3)。real の 1 件は scope 外と裁定し、実装せず裁定パッケージへ送った。
  fix 子は起動していない (実装面の修正を要する所見が 0 件のため)。
- 変異 matrix は probe (全件 SURVIVED 期待で観測 node を回収) → 本走の 2 段で回した。
  本走は 4/4 KILLED、SURVIVED 0、baseline PASSED、期待 node と完全一致。
  4 件とも 1 node ずつで検出され、単一理由性を実測で確かめた。
- 一次資料: `output/insights/2026-09-02_t2124-s1-epoch-historical/`
  (brief、段 4 / 段 6 裁定、子出力の逐語、変異 spec と走行結果)。

## 次の一手差分

### 完了

- [T-2124] D1387 の実装を終えた。S-1 の epoch gate だけを歴史 purpose へ移し、
  `E0 / v1-authority-absent` の拒否は局所で残して実関数を通る負例で固定した。
  replay と oracle は移していない。変異 4/4 KILLED。
  remaining: none
  base: 552814eeb4d1c4903570f293c02404414002871db1d018f01e2c344dedd1e19a

### 新規

- {{T:oracle-epoch-consumer-closure}} **P2・新規**: D1387 が今回の対象から外した
  `s8b_oracle_report` の epoch 証拠について、consumer 閉包を read-only で確かめる。
  保存済み証拠と capability を維持したまま可用性だけ外せる根拠が一次資料に無い、という
  D1387 の判断が現在も成り立つかを実物で検査し、結果を裁定へ返す。
- {{T:s1-epoch-identity-assert}} **P3・新規**: S-1 の epoch gate の正例へ、返った epoch の
  `campaign_verifier_epoch` が同じ lock bytes から独立に導いた記録診断のそれと一致する
  assert を 1 本足す。現在は state と reason_code しか見ておらず、同じ state / reason_code を持つ
  別の有効な 64 桁 SHA へ差し替える変異が全テストを通り抜ける。
  成果物影響は `hard_gates.certified.campaign_verifier_epochs` が別の closure を指す
  epoch identity を載せうること。本 wave が作った穴ではなく (変更前は実 callee を通る
  テストが 1 本も無かった)、実在欠陥でもないため本 wave では実装せず裁定へ送った。
