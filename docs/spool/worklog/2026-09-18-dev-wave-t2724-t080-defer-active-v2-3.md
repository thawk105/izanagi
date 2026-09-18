---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2724-t080-defer-active-v2
seq: 3
title: [T-2724][T-2776] 中断成果を回収しA-3整合とfixture切離しを記録する (コード + docs、branch codex-dev-wave-t2724-t2776-recovery)
---

## 本文

- ユーザー指定の旧tip `e2b3cc483`、未commit insight/spool、隔離子木を調査した。
  着手時local main `b2037abfa`から専用Codex木を作成。対象の既存producerを二重起動していない。
- final mutation A/Bのdone=0を回収し、spec/head/stdout hashと失敗node完全集合を照合した。
  旧tipでbaselineは双方247 passed、負例12 KILLED、等価対照1 SURVIVED、不一致0。
  新統合tipで変異を再走したとは記録しない。production3fileと対象4testは旧tipとbyte同一。
- 独立read-only Codex 2レンズは新規実装must-fixなし。旧NO-GOを解消根拠にした記録の参照を訂正。
  「中断走に2 errors」の指摘は原log/failure digestでrefuted、旧summaryの集計誤りをerratumにした。
- mainも変更した共有testはmain側を保持して統合し、隔離Codex authorが同じsinkの位置2箇所を追随。
  初回merge-message検査のauthor不足拒否を、親による実装修正やtrailerの偽装で迂回していない。
- 設計は {{D:t080-layer2-delegation-bound-to-live-validation}}。旧作業中の障害は
  {{F:long-reader-registration-starves-real-repo-gate}} とF100/F106再発に記録。
  監査・変異・到達範囲は `output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md`。
- 同名file内容交換のsingle-tenant残余、base構築の親root読取り、実A/X後の正例未実測を維持する。
  chain/X2/Gの取り込み・発効は別wave。保存枝を残し、改善実装・次wave・pushは実施しない。
- 統合tip `423bef885`の29file焦点走はrequest6381、2713 passed / 36 skipped、失敗0、pytest所要309.71秒。
  docs/Codex agents検査とspool dry-runは成功、三軸走査は両holdout hit0・陽性199。
- 同tipのfull provenanceは11468件・新規違反0・既知56件。修正後焦点レビューもGOで4項目closed。
- 共有test単独走の初回はrequest6404が900秒のqueue待ち上限に達し、child未開始でrc16。
  job不在・producer/待ち手の終了を確認後、同tipをrun_tests.pyの既定配置判定で再走した。
  最終受入は既存のqueue待ちoverrideを3600秒、待ち手の全体上限を10800秒とする（検査内容は不変）。
- sink単独再走はbounded localで71 passed / 2 skipped、70.85秒、rc0。
- d899c86aaの受入は25153 passed / 69 skipped / 12 setup errors、child rc1・waiter rc70。
  全12件がT-1259のmodule fixtureからのGit未追跡走査30秒timeoutで、当該test/probeに今回の差分はない。
  同tipの正規runner単独走でも同じargvで51 setup errors（247.47秒、rc1）となった。
  DW-O18に従い受入2を投入せず正式停止。成功受領証はなく、main landと対象清掃は未実施。
  赤はF945再発として記録し、既存T-2790の設計・検証を越えてtimeout/hold/除外を変更しない。
- 9月19日、ユーザーからmain landまでの続行を指示された。同じ目的の修復を続行し、
  main `0ab4627d4` に入ったT1259の既存module snapshot配置修復（T2780/T2504）を採用した。
  隔離Codex authorがconftestとserializationの両側変更を合成し、`98f06e374`で統合。
  T1259の30関数/51caseとT080 receipt8関数/8node・接続20nodeを保持し、timeout/hold/除外は不変。
  計算ノードの焦点5fileは8813.nqsvで331 passed /1 skipped、37.14秒。統合後full provenanceは
  11578件・新規違反0・既知56件。最終受入の成否はこの記録後の共通受領証で確定する。

## 次の一手差分

### 完了

- [T-2776] A-3整合waveに同梱し、宣言集合だけを除いたreplay base、実scan正負例、両木焦点走と変異の検出力を回収した。
  remaining: none
  base: b067abb4f95284ceb22f15ff41177f43071cfa7599705f5eff671db62c65d008

### 更新

- [T-2724] **P1・A-3整合実装とT-2776は完了、chain/X2/Gの取り込みは別wave**:
  receiptの履歴・静的検証・epoch・invalid拒否を維持し、同一root/HEAD/世代で成功したactive v2のfull validationへ層2だけ委譲する。
  保存branchのchain/X2/Gをfold後mainへ取り込んで受入・landする作業、続く人間A/Xの発効は未実施。
  `worktree-dev-wave-t2724-freeze-g1-gen` tip `229982652` とchain/X2保存枝を維持する。
  D2120項2(a)は有効、(b)のA/Xはユーザーcommit、(d)記録済み、(e)の退避とT-1851 cleanup残件、(f)のT-750管理は維持。
  本waveで新たなoracle/floor性能測定はしていない。証拠は `output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md`。
  base: d606da65974428b31dbc6ba8461b6e6ed28b8b3aac969a04b9279ec3b13a4777
