---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1922-phase3-fold-gate
seq: 1
title: [T-1922] 生成後 phase3 canonical の見送り重複を land 前に拒否し、fold gate の phase3 被覆を閉じた (code + tests + docs、branch worktree-dev-wave-t1922-phase3-fold-gate、kill 6/6・診断 pin 3)
---

## 本文

- 依頼が名指しした 2 つの欠陥を、着手前に現行 tip で再現した。repo 外へ `docs/` と `tools/` を
  複製して実行し、repo と local main は変更していない。既に見送り台帳に在る ID をもう一度
  見送りへ送る fragment を置くと `--dry-run` は `status: planned` を返し、fold を適用した後に
  初めて `check_docs.py` が `docs/phase3.md: 見送り台帳の ID が重複` を出した。
- 発火 path を名指しできた (D1114)。現行 canonical で active な次の一手と見送り台帳の重なりが
  2 件あり、どちらかを見送りへ送る wave は同じ拒否を踏む。今の台帳自体は正常で重複は無い。
- 誤検出の母集合を実測した。見送り台帳の top-level 項目は全件一意だが、継続行に ID が 31 行、
  完了記録側に 10 件ある。行単位の素朴な走査は偽の重複を作る。既存 `_deferred_items()` は
  fence・HTML コメントを除外し完了記録の手前で切るため、検出の意味を書き起こさず再利用した。
- 段 3 の敵対相談が、新しい gate に一度も到達しないまま緑になる負例を見つけた。テスト helper の
  carry 既定値が入ると、手前の `transition-target` 検査で止まる。明示的に空にして是正した。
- 段 6 の敵対レビューが、registry の import 時 digest 自己検査により変異 2 件が意図した検査へ
  届かないことを見つけた。両層変異へ再照準し、変異後 digest を実関数から計算して登録した。
- 変異の期待 node を推測で書かず、全件 SURVIVED 期待の probe 走で観測してから確定した
  (DW-M07)。推測は 2 件外れていた。1 件は land 側の結線検査を落としており、
  もう 1 件は赤にならない検査を挙げていた。
- 段 4 で焦点走を 3 file と裁定したが、変更した production module の consumer を参照関係で
  引くと 10 file あった (DW-O26)。10 file へ広げて実走した。
- 所要時間台帳は触っていない。exact に固定される suite 8 件に本 wave の file は 1 つも含まれず、
  被覆条件も完全一致ではないため、新 node の entry は不要と確認した。
  推測値を性能台帳へ書かずに済ませた。
- ユーザー裁定「gate tool は親が実データで 1 回通すまで完成としない」に従い、義務化は実データ
  通過を確認してから書いた。`--dry-run` は拒否側・受理側の両方を実データで通し、fold gate 本体も
  実 plan で 23.3 秒・内側予算 130 秒に対して通した。
- 義務の置き場は `DW-O23` でなく `docs/spool/README.md` にした。dev-wave 参照文書の L1 予算は
  本 wave の編集前からちょうど満杯 (10625/10625 bytes) で、124 byte の 1 行すら入らなかった。
  D782 の手順に従い既存記述の削減を先に試したが、L1 に安全義務でない削減可能部を見つけられず、
  上限引き上げにも至らせなかった。fold の受理・拒否契約の正本は `docs/spool/README.md` であり、
  同書は既に `--dry-run` の役割を説明していたので、説明を義務へ改める形で収容した。
  **義務の内容は弱めていない。**
- 本 wave の fold は見送り台帳を触らないため、land 時に選択される gate node は 2 件で
  新 node は選ばれない。新 node は焦点走と名指し実行で緑、結線 (見送り fragment → phase3 family
  → 新 node 選択) は land 側の検査が固定し、その検査は変異 M8 で殺されることを確認した。
  gate に phase3 を通すために偽の見送りを commit することはしない。撤回時に fragment 削除が
  commit 区間へ残り、land が `landed-fold-owned-path` で拒否する。

## 次の一手差分

### 完了

- [T-1922] `spool_fold.plan_fold()` が生成後 `docs/phase3.md` の見送り重複を `deferred-duplicate` で
  拒否し、fold gate の `phase3` family を実 canonical node で被覆した。land 前 `--dry-run` の
  義務は `docs/spool/README.md` へ書いた (dev-wave L1 予算が満杯のため)。
  remaining: none
  base: 4a7c829da4cde29d4d56a5d3e42657a0eb3cbdb28f06726a0812c682d0164dea

### 新規

- {{T:fold-plan-outside-land-lock}} **P3・ユーザー裁定待ち**: land の plan 作成を協調 lock の外へ移し、
  fold gate が実 plan の重複を隔離木で検査できるようにするか。段 6 の敵対レビューが
  「検査を `plan_fold()` に置く限り land 時の初回検出は lock 内に残る」と指摘した所見であり、
  real と裁定したが land 状態機械の変更として scope 外にした。現行設計では land 前 `--dry-run` の
  義務化で同じ実害を塞いでいる。
