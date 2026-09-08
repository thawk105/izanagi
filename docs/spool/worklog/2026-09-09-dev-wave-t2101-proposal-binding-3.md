---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2101-proposal-binding
seq: 3
title: [T-2101] 提案の束縛を実行ループ側で閉じた — 閉じられたのは bootstrap だけで、登録値が continuation の提案とは別の対象を指すことが一次資料から確定した (コード + テスト + insight、branch worktree-dev-wave-t2101-proposal-binding、変異 10/10 KILLED・期待 node 完全一致)
---

## 本文

- **裁定当時に見えていなかった事実を段 3 が割り、親が一次資料で検算した。** D1343 の「提案」が
  指すのは block 共有の初期 (bootstrap) proposal であり、continuation で driver へ渡る提案は
  アームごとに異なる次の synthesis である。根拠は事前登録 §5.1 の適格性述語
  「初期 proposal が、事前に固定した bootstrap 集合に属する」、同 §の `precursor_hash_mismatch`
  (1 block の両アームは同じ `precursor_hash` を持つ)、および raw record producer が
  `precursor_hash` を registry の `initial_proposal_sha256` から出していること。
  continuation に同じ等式を強制すると両アームに同一提案を強いて treatment を構成的に消すため、
  **親は D1343 を不採用にせず、適用範囲を bootstrap に絞って実装し、continuation の閉じ方を
  ユーザー再裁定へ返した。** 設計は {{D:b4-bootstrap-proposal-binding}}。
- **continuation を閉じられない理由は実測で確かめた。** 唯一の筋である「campaign を種付けした
  初期 proposal の再導出」は、checkpoint が whiteboard 5 field しか焼かず提案の値も実装も
  D39 決定 3 のリーク遮断として意図的に落とすため成立しない。耐久 carrier の新設が要る。
- **親 brief の誤りを 2 件、段 3 が独立に反証した。** (a)「発火条件は今日以降の formal B-4 実行の
  すべて」は誤り — 事前登録 §5 が未記入で admission record も不在のため formal B-4 は開始できない。
  (b)「拒否は実行前」は build / lock / WAL より前までが正しく、その前に単独性検査と Git pin 検査の
  process 起動、launcher の sidecar と campaign directory 作成が入る。いずれも非保証へ明記した。
- **棄却した所見 (refuted):** duplicate key を 3 loader で拒否すべきという提案は採らなかった。
  束縛するのは実行される提案 (parse 結果の canonical 形) であって file の raw bytes ではなく、
  raw bytes の固定性は本 wave が主張しない別命題である。段 3 の他の refuted は
  receipt key の追加・削除による hash 制御 (既存 receipt gate の順序が塞ぐ)、
  3 driver の片肺 (formal main から loader を素通しする経路は無い)、
  campaign lock / WAL / build が照合より先に来る経路。
- **段 6 の敵対レビュー 2 本はいずれも must-fix 0 件。** 親の焦点走で出た赤 2 件はどちらも
  自分の変更に帰属した (canonical 化失敗時の例外型が正規化されていない、静的 import 閉包の
  戸数 pin が 45 から 46 へ増えた)。**戸数 pin の更新は親が裁定した唯一の既存期待値変更である** —
  これは閉包の増加を気づかせる tripwire であって閉包が増えない主張ではなく、依存を関数内の
  遅延 import へ逃がして戸数を保つ案は実在の依存を静的 probe から隠すため却下した。
- **変異は事前登録 13 件のうち 3 件を単一理由性が成立しないため登録しなかった** (insight §4.1 の
  erratum)。登録位置が実装に存在しなかったもの 1 件、他の変異の期待 node と重複するもの 1 件、
  役割が他の 2 変異に吸収されたもの 1 件。残り 10 件は全件 KILLED で期待 node が完全一致した。
  期待 node は推測で書かず、全件 SURVIVED 登録の probe を 2 回走らせて観測 node を集めてから
  本走の spec に焼いた。
- **セッション異常:** 実装子と fix 子は sandbox から `tools/run_tests.py` を走らせられず
  (`qstat -Q preflight rc=1`、`Unknown user-id`、`child_started=false`)、pytest の実走はすべて
  親が行った。変異走は F185 の 3 回目の再発で 2 度中断し、うち 1 回は変異を残したまま止まった。
  復旧は qstat での終端確認 → `git checkout --` で復元し bytes を HEAD と照合 → live hold と
  archive の両方を削除、の順で行った。手動 qdel はしていない。
  **`orphan-holds/` の archive は 1 件でも残ると以後の dispatch を起動前に全部止める** ため、
  live file だけを消しても解けない。
- **エージェント工数:** Codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1)、
  合計 323 model call / 47.1M raw token。内訳は plan 51、consult sol 33 / luna 43、author 81、
  review 27 / 61、fix 27。
- 一次資料は `output/insights/2026-09-09_t2101-proposal-binding/`。

## 次の一手差分

### 更新

- [T-2101] **P2・裁定済み (2026-09-01 /rulings 全件、D1343) → bootstrap は着地、continuation は
  ユーザー再裁定待ち**: 実行ループ側の束縛は bootstrap で閉じた
  ({{D:b4-bootstrap-proposal-binding}})。残るのは continuation の提案束縛で、
  **登録値が指すのは block 共有の初期 proposal、continuation の提案はアームごとに異なる
  次の synthesis** という一次資料の事実 (事前登録 §5.1 と `precursor_hash_mismatch`) により、
  同じ等式を当てられない。ループは checkpoint から初期 proposal を再導出できない
  (whiteboard 5 field しか永続化しない)。閉じるには耐久 carrier の新設かリーク遮断の
  設計変更が要る。一次資料 = `output/insights/2026-09-09_t2101-proposal-binding/README.md` §1〜§2。
  base: 56d444d305b649fd0727e66661e411ef66666b5a5ed9a55056d208f77db677f0

### 新規

- {{T:b4-publication-authority}} **P2・新規・ユーザー裁定待ち**: B-4 の prerun publication は
  どれが権威かを誰が決めるか。publication root は呼び手が実行時に選び、issuer は別 root での
  再発行を防がない。任意の提案 B に対して `H(B)` を持つ registry を別 root へ発行すれば
  bootstrap 束縛も通る。本 wave の検査が拒否するのは「指定された組の不一致」であって
  「事前固定した集合であること」ではない。一次資料 =
  `output/insights/2026-09-09_t2101-proposal-binding/verbatim/s3-consult-sol.md` の S3 / S5。
- {{T:b4-manifest-membership}} **P2・新規・ユーザー裁定待ち**: formal B-4 の母集合は
  analysis manifest の 201 行か、scheduled attempt registry の全行か。現在は manifest 外の
  registry 行でも hash が一致すれば実行でき、raw record producer が後から拒否するまで
  build と WAL は進む。一次資料 = 同 s3-consult-sol.md の S13。
- {{T:b4-binding-guarantee-boundary}} **P3・新規・ユーザー裁定待ち**: 提案束縛の保証境界は
  formal launcher 限定か、B-4 marked config を受ける全 sink か。D1343 の文言は「実行ループ側」
  だが、束縛は proposal loader 内に閉じ `drive_iteration` / `run_one_iteration` の型には載らない。
  一次資料 = `output/insights/2026-09-09_t2101-proposal-binding/verbatim/s3-consult-luna.md` の
  L16 / L23。
