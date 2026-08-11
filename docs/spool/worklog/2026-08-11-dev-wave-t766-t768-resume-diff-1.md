---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t766-t768-resume-diff
seq: 1
title: land の rollback は全復元点成功時だけ resume state を削除するようにし、fold dry-run へ --show-diff を足した — 変異 6/6 KILLED (M5 は erratum 再走)、新規 5 件起票 (コード + テスト + docs、branch worktree-dev-wave-t766-t768-resume-diff)
---

## 本文

- **[T-766] と [T-768] を同一 wave で実装した (2026-08-11 の /rulings で 2 件とも (a) 採用)。**
  [T-766] = land の lock 内 fold で rollback の復元点が失敗しても resume state を無条件で
  削除していた欠陥。[T-768] = `tools/spool_fold.py --dry-run` が台帳へ挿入される bytes を
  出さない欠陥。実測・変異台帳・レビュー所見の逐語は
  `output/insights/2026-08-11_t766-t768-resume-diff/` が正本。
- **段 1 の前提実測で欠陥を再現した。** repo 外 probe が実 `_rollback_fold` を temp git repo で
  呼び、ref 復元点を失敗させたところ `failures` 非空のまま `state_path.exists() == False` に
  なった。既存被覆はゼロで、実 `_rollback_fold` を走らせるテストは 1 本も無かった
  (唯一の言及箇所は関数ごと lambda 置換していた)。
- **段 3 レンズ A が、裁定の目的を本 wave では閉じきれないことを示した。** ユーザー裁定は
  `_rollback_fold` の削除条件の変更であり、これは実装した。しかし `apply_fold` は canonical 書込みと
  fragment GC の直後に state を消すため、land がその後に走らせる docs 検査・stage 検査・commit・
  postcondition で失敗すると、**rollback へ入っても残すべき state が既に無い**。これは
  finalize protocol の新設を要する非同値な別設計なので scope 外に裁定し、新規 T として起票した。
  本 wave が閉じるのは state がまだ存在する失敗系統 (ref CAS / read-tree / main moved beyond) である。
- **同レンズは、修正が既存の穴への露出を上げることも示した。** state に land 起源・base・
  tested tip の束縛が無いため、standalone `spool_fold.py` が誤った HEAD 上で resume できる。
  残存 state が増える分だけ露出が上がる。それでも採用したのは、現行のように journal を消して
  台帳を第三状態に落とす方が悪く、land 経路自体は fail-closed で止まるためである。新規 T として起票した。
- **fresh ff 経路の失敗では、state を残しても同じ land では resume できず、active state が
  以後の land を塞ぐ。これは意図した fail-closed として受容した。** 台帳を混在状態のまま次の land へ
  進ませるより、止めて人手復旧へ倒す方が裁定根拠 (台帳の完全性はプロトタイプ基準の例外側) に
  忠実である。運用者が journal を誤って破棄しないよう、rollback 失敗時の reason に所在を足した。
- **段 6 レンズ B が信頼境界の欠陥を見つけた (規律 6)。** fragment は AI が書く外部入力であり、
  `validate_spool_tree` は C0 制御文字を拒否しない。diff payload を無加工で stderr へ流すと、
  ANSI erase / cursor move で **この機能の目的である land 前の目視確認そのものを消去・偽装できた**。
  可逆な `\xNN` escape を入れて閉じた。同じ fix で、行分割が `bytes.splitlines` だったために
  CR・VT・FF・FS/GS/RS・NEL でも切れ、「byte 忠実」の契約と実装が食い違っていた点も直した。
- **親の fix 指示に誤りが 1 件あった。** `fix_b_prompt.md` の F2 で「stderr が 0 byte」と書いたが、
  段 4 裁定 B-3 の要求は「diff を出さず既存の error JSON 経路で終える」だった。第 1 巡は指示どおり
  無言 rc=2 (fail-silent) になり、第 2 巡で transaction-error JSON を出す形へ戻した。
  子は指示に忠実だったので、これは親の記述誤りである。
- **焦点走の赤 5 件は本差分に帰属しない。** `test_exploration_external_root_keeps_wave_clean` と
  実 canonical をコピーする `test_spool_fold.py` の 4 本が赤だったが、**wave の変更を 1 つも含まない
  未変更ツリーで同 5 件を再走して同じ赤を再現**した。焦点走の実行形に固有で、受入全走の形とは
  環境が違う。変異 harness の runner ではこの 5 node を `--deselect` した。
- **変異は 6 件を事前登録し、本走で KILLED 5 / MISMATCH 1 / SURVIVED 0。M5 の MISMATCH は検出力が
  登録より強い方向のズレ**で、親の予測が 1 node 読み落としていた (段 6 fix が hash 行の値照合を
  `gc_paths` へも広げたため、gc 出力を止めると別テストも赤くなる)。初回 ledger は消さず、
  M5 だけを正しい期待 3 node で再走して**期待完全一致の KILLED** を得た。実質 6/6 KILLED である。
  M1 は memory `mutation-must-include-pre-wave-form` に従い wave 前の実コードの逐語 (`else:`) を
  復元する形で登録した。`apply_fold` の早期 unlink は scope 外に裁定したため登録していない
  (SURVIVED を equivalent と誤記録しないため)。
- **受入全走は記録 commit 済みの最終 tip で 1 走とした。** `tools/dev_wave_land.py` は
  wave HEAD が受入を通した tip と一致しないと `RC_AUDIT` で拒否するため、受入数値を本文へ
  前もって書くことはできない。結果は land 報告に記す。

## 次の一手差分

### 完了

- [T-766] land の rollback は全復元点が成功したときだけ resume state を削除するようにし、
  実 `_rollback_fold` を走らせる故障注入テストを新設した。
  remaining: none
  base: e597a908e669641257699fd343d831a74ba3d65b252996a10cc2e49bc47637c4

- [T-768] `tools/spool_fold.py --dry-run --show-diff` を足し、台帳へ挿入される bytes と
  削除される fragment を land 前に byte で確認できるようにした。運用手順も差し替えた。
  remaining: none
  base: 4f47d97fd3b440e85dd590a399b37cd4104b9d2942eb7ba704f003680e27c8e3

### 新規

- {{T:fold-finalize-protocol}} **P2・新規**: `apply_fold` は canonical 書込みと fragment GC の
  直後に transaction state を消すが、land はその後に docs 検査・stage 検査・commit・postcondition を
  走らせる。この区間で失敗・crash すると rollback へ入っても残すべき state が無い。
  選択肢 = (a) land 専用 journal を分けて finalize protocol を新設する / (b) state 削除を
  land の postcondition 後へ移し `validate_spool_tree` を active-aware にする / (c) 現状維持。
  成果物影響 = (c) のままなら canonical 3 台帳・`FOLDED.md`・fragment GC が反映済みなのに
  commit と journal が無い窓が残り、certified 選択・レポートの proof chain を main history へ
  帰属できない。[T-766] wave の段 3 レンズ A の所見 2。

- {{T:fold-state-head-binding}} **P2・新規**: fold transaction state は fold date・fragment・
  target hash だけで同一性を作り、land 起源・base・tested tip を束縛しない。CLI は state があれば
  HEAD を検査せず読むため、**standalone `spool_fold.py` が誤った HEAD 上で resume できる**。
  [T-766] の修正で残存 state が増えるため露出が上がる。
  選択肢 = (a) state へ land 起源・base・tested tip・rollback ref を束縛して mutation 前に HEAD と
  照合する / (b) land 由来 state の standalone apply を拒否し land recovery のみに限定する /
  (c) 現状維持。成果物影響 = (c) のままなら wave commit と無関係な main HEAD 上で T/D/F 採番と
  receipt を確定でき、台帳・レポート・proof chain の帰属が分離する。段 3 レンズ A の所見 4。

- {{T:rollback-state-inspection}} **P3・新規**: `_rollback_fold` の state 型検査は復元処理と同じ
  `try` の末尾にあるため、path 復元の `RuntimeError` や `_head` の `_Reject`、`OSError` が起きると
  到達しない。「型検査は常に走る」は例外経路では偽である。
  選択肢 = (a) 復元 try/except の後に独立した state inspection phase を置く / (b) 現状維持。
  成果物影響 = (b) のままなら journal 自体の破損が rollback 例外に隠れ、復旧報告が不完全になり、
  誤った手動破棄で台帳の唯一の再開材料を失い得る。段 3 レンズ A の所見 7。

- {{T:rollback-lifecycle-details}} **P3・新規**: rollback lifecycle に 3 つの細部欠陥がある。
  (i) state 作成は `exists()` 確認後に `os.replace` するため broken symlink を黙って置換し、
  並行作成された別 transaction state も check-to-replace 窓で上書きできる (standalone CLI は
  land の協調 lock を共有しない)。(ii) rollback 成功終端の unlink 後に parent directory を
  fsync しない (`apply_fold` の削除は fsync する)。(iii) message cleanup の `OSError` が
  成功 `LandResult` や `RC_FOLD_ROLLBACK_FAILED` を上書きし得る。
  選択肢 = (a) 3 件をまとめて直す / (b) (iii) だけ直す / (c) 現状維持。
  成果物影響 = (c) のままなら台帳 commit の成否と land の報告・peer 通知が食い違う
  terminal ambiguity が残る。段 3 レンズ A の所見 8。

- {{T:dryrun-git-admin-no-write}} **P3・新規**: `--dry-run` の no-write 検査は `.git` を除外して
  おり、`git status --porcelain` の前後一致も status 出力しか見ない。index stat cache・lock・
  その他 admin bytes の変化は検出できない。
  選択肢 = (a) Git admin まで含む snapshot 比較を足す / (b) 現状維持。
  成果物影響 = (b) のままなら dry-run が transaction 周辺を汚す回帰を見逃し、land receipt の
  信頼性が下がる。段 6 レビュー B の nit を real 化したもの。
