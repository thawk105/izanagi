---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: rulings-20260819-selfimprove
seq: 2
title: /rulings 第2ラウンド — loop.py強制・exec-loc裁定パッケージ残余・docs予算2件をユーザーが推奨通りで一括裁定した (docs のみ)
---

## 本文

- ユーザーから「next-tasks セッションが裁定待ち29件と言っていた」との報告を受け、
  next-tasks セッションへ直接照会した。29 は `next_tasks_snapshot.sh` が出す
  「rulings-inbox 配下で未 land のファイル数」であり、裁定待ちの集計ではなかった
  (次の一手の実装 backlog と混同されやすい語の一致が原因)。
- 折り返し、next-tasks 側のフォークが rulings-inbox 29 件を独自に精査し「未裁定らしき候補」を
  2 件報告した ([T-396]、[T-1183] 問2/問3)。裏取りの結果、両方とも既に裁定済みだった
  ([T-396] は round8 集約ファイル `rulings-full8-19rulings.md` に確定記録あり、
  [T-1183] 問1/問2 は D464/D465 で確定済み)。next-tasks 側は個票単体しか読んでおらず、
  round 集約ファイルとの突合せを欠いていた。
- 裏取りの過程で本物の収集漏れを発見した。詳細は {{F:rulings-staged-recommendation-second-stage-dropped}}。
  [T-330] の再裁定パッケージ (`output/insights/2026-08-16_t330-scr-single-process/s4-adjudication.md`
  = D419 が記帳したもの) は「(c) を先に、その後 (a) を再提示する」という 2 段構えの推奨だったが、
  (c) 完了時に [T-330] という単一 ID ごと active carry から落ち、(a) が 3 日間どの収集経路からも
  見えないまま放置されていた。
- 第2ラウンド (同日、待機中に実施): ユーザーへ (a) を独立評価した推奨として再提示し、
  「推奨通りで、main land まで」の裁定を得た。**(a) を採用**し、
  {{D:loop-py-conditional-single-process-enforcement}} として記録した (D419 決定 3/4 の
  「再訪する」前提を継続する形)。実装は本 wave では行わない (次は実装 wave の起票)。
- 同時に別の裁定パッケージ (`output/insights/2026-08-13_exec-loc-and-usage-fixes/s4-rulings-package.md`、
  R-1〜R-5) の掘り残しを発見した。**R-1 は当初「未裁定」と誤判定した** (grep の構文エラーで
  検索が失敗していたのに気づかず「無し」と扱った、実測不備)。実際には
  [T-1029]/D548 (2026-08-13 round9 #4) で (b) 採用・実装済みだった。
  - R-2 (非 Pegasus exact allowlist の新設可否): R-1=(b) 確定によりその根拠 (R-1=(a) なら
    合わせて設計) が消え、**不採用で決着** (実装不要、prose 記録のみ)。
  - R-3 (委任の射程、`s4-rulings-package.md` の 3 問中 (b) は [T-1031] で既決): 残る
    (a) 恒久性は **「この 1 件限り」** (ユーザーが標準で慎重側に倒す既定方針に整合)、
    (c) D233 決定 4 の書き換え要否は **不要** (D548 が理由文を訂正済みで本体要件は不変、
    という確認で足りる)。いずれも実装不要 (prose 記録のみ)。
  - R-4 (分類は argv 単位か path 単位か): **(b) 測る対象を本番 argv に合わせる**を採用。
    2026-08-05 の [T-482] (b)(c) が同じ層で未決着のまま残っている可能性があるが、本裁定は
    R-4 単独の scope とし、[T-482] 側は次の実装 wave が着手時に再確認する。実装は次wave。
- [T-1407] (dev-wave 作法 5 件、docs 予算満杯) と、本 wave が見つけた rulings.md 予算満杯
  (同節参照) は **同じ問題 (docs 予算の運用方針) のためユーザーがまとめて独立予算審査へ回す**
  と裁定した。個別の (a)/(b)/(c) はまだ選ばない。
- git push (35 commit 未反映) は「都合のよい時に」で承認されたが、AI は push しない規約により
  実行していない。ユーザー手番のまま。
- 記録手順の途中、fold verifier `landed-fold-owned-path` により2回 land が rc=26 で拒否された
  (branch の履歴が main を複数回取り込み、その merge が `docs/spool/FOLDED.md` に触れていたため)。
  main 直上の線形形へ組み直して解消した (再試行や dry-run では直らない型、既知の失敗パターン)。

## 次の一手差分

### 更新

- [T-1407] **P2・裁定済み → 独立予算審査待ち**: dev-wave 作法 5 件は個別の (a)/(b)/(c) を
  選ばず、rulings.md 予算満杯の件とまとめて 1 回の独立予算審査へ回す。次はその審査の起票。
  base: d633fca4586a4b029ca4aee2d30024a4451a210a3893c0ba4e7245d03d56ddde

### 新規

- {{T:loop-py-single-process-conditional-enforcement}} **P2・裁定済み → 実装待ち**: (a) 採用。
  設計は {{D:loop-py-conditional-single-process-enforcement}}。次は実装 wave の起票
  (`loop.py` の該当分岐、関連テスト・変異検査を含む)。
- {{T:rulings-command-budget-for-staged-followup-check}} **P3・裁定済み → 独立予算審査待ち**:
  [T-1407] とまとめて独立予算審査へ回す。個別の (a)/(b)/(c) はまだ選ばない。
- {{T:exec-loc-classification-scope-argv-vs-path}} **P3・裁定済み → 実装待ち**: (b) 採用。
  分類の測定対象を本番 caller が実際に渡す argv (現行の `--max-files=1000` 相当) に合わせる。
  詳細は `output/insights/2026-08-13_exec-loc-and-usage-fixes/s4-rulings-package.md` §R-4。
  着手時に [T-482] (b)(c) の未決着有無を再確認すること。次は実装 wave の起票。
