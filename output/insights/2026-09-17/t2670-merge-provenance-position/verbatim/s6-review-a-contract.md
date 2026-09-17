## 所見 (裁定との一致)

**A1 / refuted / nit / 対象: `tools/dev_wave_wait.py:607`, `:3862`**

根拠: 裁定 §3 の指定どおり、監査を `commit-rev-parse` 直後・`commit-message-postcheck` 前へ移設。argv・stage・`diagnostic_reason`・`capture_failure_output` は保存され、`merge_pending = False` は commit 直後に残る。cleanup 実処理は不変。patch 全31 hunk の変更後内容が現物と一致し、差分量も追加170行・削除68行と一致した。

成果物影響: 移設位置・cleanup 権限について、裁定からの逸脱はない。  
推奨 fix: 不要。ただし受理集合の裁定には A4 の訂正が必要。

**A2 / refuted / nit / 対象: `tools/dev_wave_cleanup.py:575`, `ruling-s4.md:10`, `brief.md` の P1**

根拠: cleanup は reflog の各 commit が main の祖先かを検査する。保持した merge が後続 wave tip の祖先として land すれば到達性を保てる。一方、巻き戻した merge が reflog にだけ残れば同検査で拒否される。巻き戻しを採らない理由は妥当。裁定は「2親だから land 適格」という一般化も撤回している。

成果物影響: merge 保持は D1233 と整合する。ただし保持だけで land 適格になるわけではない。  
推奨 fix: 不要。

## 所見 (監査赤後の状態遷移)

**A3 / real / nit / 対象: `tools/dev_wave_wait.py:4203`**

根拠: 通常の cleanup 成功経路では要求された状態になる。

- (a)(e) 監査の非0は `:2181` で `_StageFailure`、`:4167` で捕捉。受領証準備 `:3942`・launcher 投入 `:3963` に到達しない。
- (b) `:4277` から cleanup。`:3358` は ACQUIRED / UNKNOWN のみ解放し、HELD_SELF は保持。解放失敗は `:4284` で cleanup failure として返す。
- (c)(d) `:3862` で `merge_pending=False`。`:3310` の abort 分岐に入らず、HEAD を巻き戻す処理もない。
- (f) `:4205` で一時 message の削除を試みるが、`:4206` は `OSError` を握り潰す。**削除完了の無条件保証は成立しない。** これは既存挙動である。

成果物影響: unlink 失敗時は一時ファイルが残るが、受入投入・受領証発行・land の受理集合は変わらない。  
推奨 fix: レビュー結論・契約説明を「削除を試行する」と限定する。この変更で cleanup 実処理まで拡張する必要はない。

## 所見 (受理集合と checker 意味論)

**A4 / real / must-fix / 対象: `tools/check_ai_provenance.py:864`, `tools/dev_wave_wait.py:3868`, `author.md:12`, `ruling-s4.md:59`**

根拠: **旧位置で拒否され、新位置で受理され得る具体的な入力がある。**

main 側に、既存規則上有効な既知違反登録とその対象 commit が追加され、wave 側の preclaim 監査は緑とする。

1. 旧位置では `merge --no-commit` 後、登録ファイルは index / worktree に存在するが wave HEAD には存在しない。
2. history 監査は `:2433` で `_known_violation_registry()` を呼び、`:866` の `index_names - head_names` により `index-only member does not match HEAD` で拒否する。
3. 新位置では merge commit に登録が入り、HEAD / index / worktree が一致する。他の監査条件も満たせば、その登録を既知違反として扱って受理できる。
4. commit 前に残る message 監査は同 registry 検査を呼ばないため、この差を打ち消さない。

checker の台帳規則を緩和したわけではないが、**位置移動による受理集合の拡大**であり、author の「それ以外の受理条件を維持」は偽。裁定も「checker・台帳コード不変」と「受理集合不変」を区別できていない。

成果物影響: 従来は受入投入前に拒否された、正当な台帳追加を含む main 取り込みが、受入・受領証発行へ進み得る。  
推奨 fix: 裁定と報告にこの旧拒否→新受理を明記し、意図した変更として扱う。実 checker を使う焦点例で確認する。旧位置の監査を復活させて偶発的拒否を保存する修正は不要。

**A5 / refuted / nit / 対象: `tools/check_ai_provenance.py:1776`, `:2360`, `:2477`; `tools/dev_wave_wait.py:3776`, `:3839`**

根拠: 既定監査は HEAD を解決し、`{policy} ∪ rev-list(policy..HEAD)` を選択する。merge 後なら、policy 導入以降の取り込み commit と merge 自身が入る。receipt 再利用も bindings 一致と prefix 集合検証を要求し、delta が選択集合との差集合に一致しなければ破棄する。再利用時も delta を監査するため、preclaim receipt が取り込み分を隠す経路は見当たらない。

preclaim 監査と、MERGE_HEAD を使う commit 前 message 監査は維持されている。merge 自身の違反を新たに拒否することも D2044 / F365 の目的に一致する。

成果物影響: 監査対象の取り込み漏れは修正される。ただし受理集合全体の不変性は A4 により否定される。  
推奨 fix: checker・移設位置の修正は不要。

## 所見 (報告と実体の照合)

**A6 / refuted / nit / 対象: `author.md:46`, `:54`; `orchestrator/tests/test_dev_wave_wait.py:6679`, `:8714`**

根拠: 報告の件数は、表の10関数＋段別展開による13件増＋新規1件＋追加3件＝27件で整合する。新規負例は runner 計数を最初に検査するため、M2 で計数1ならその assertion が赤になる構造も整合する。監査呼び出しは現物に復元され、patch と一致する。

ただし、27件成功・M2 の実計数1・バイト単位復元という**実行履歴自体は静的検査では追認できない**。報告内容との構造的矛盾はない。受理条件に関する報告の不一致は A4 に記載した。

成果物影響: 静的照合からテスト成功を独立認定することはできない。  
推奨 fix: 親の焦点走・変異走で実測を確定する。本レビューではテスト未実行。

## 総括

NO-GO