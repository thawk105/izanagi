## 所見

1. **must-fix — F の preview 手順が起動できない。** `p3_s4_loop_policy.py:60-66,83,284` は `--preview-diff` でも auditor 必須の proposal を読みます。一方、`docs/phase3-silo-policy-runbook.md:52-59` は auditor を呼ぶ前に coder だけで preview する手順です。**反例:** `{"coder": {...}}` を preview に渡すと schema で拒否されます。**影響:** 初回の `working_diff` と digest を得られず、auditor 入力も確定できません。**代案:** preview 専用に coder 部分だけを閉じた schema で読み、run 時だけ auditor を必須にする。

2. **must-fix — `--no-build` の正常候補が結果返却まで進めない。** `p3_s4_loop_policy.py:206-207` は `dry-pass` で WAL を作らず、同 `:244-246` は直後に WAL 必須の `require_admitted_campaign` を呼びます（`artifact_admission.py:1346-1349`）。**反例:** 新規 campaign の正しい候補を `--run-iteration ... --no-build` で実行する。**影響:** 台帳に履歴と checkpoint が残った後に例外となり、配線確認の結果と critic digest が得られません。**代案:** dry-pass は admitted view を要求せず結果を返す。digest が必要なら WAL を作る契約を別途明示する。

3. **should — 履歴が失敗分類を潰している。** `p3_s4_loop_policy.py:213-218,149-155` は build error、trace timeout、非直列化などをすべて `outcome="aborted"` とし、`verifier_digest` も verdict と二つの bool だけにします。**反例:** build が失敗した候補と performance verify で落ちた候補。**影響:** 次の coder に渡す自系列履歴とレポートで両者を区別できず、設計 §3.2 の分類が失われます。**代案:** `EvalResult.notes`、`verify_result` と WAL の構造化理由から分類を射影する。自由文をそのまま coder に渡さない。

4. **should — M-E1 は構文 gate の kill を単独で証明しない。** `p3_s4_loop_policy.py:121-129` では構文拒否時の `compiled` が `None` です。構文拒否だけを受理扱いに変えても、次の compile 分岐が拒否します。`test_p3_s4_loop_policy.py:154-159` は subtype を見るため赤になります。**反例:** 登録済みの `x++` fixture。**影響:** 受理集合が変わらない変異を kill と数え、構文 gate の検出力を過大報告します。**代案:** compile まで進める単独変異に再照準し、受理集合の変化を確認する。現状は診断 pin と記録する。

5. **should — M-E4 の期待 node が呼出し点を測っていない。** 上限 26 は loader (`p3_s4_loop_policy.py:83`) と veto (`:130-133`) の二か所にありますが、`test_p3_s4_loop_policy.py:85-97` は loader だけを検査します。**反例:** veto 側だけを 21 に戻し、型 22 の auditor reject を gate に通す。**影響:** policy driver の実際の受理経路の退行を見逃し、変異 matrix の期待 node が不完全になります。**代案:** 型 22〜26 を含む verdict を `policy_gate` まで通す fixture を追加し、二層の必要性を確認する。

6. **nit — IR と config の再検査を整理できる。** `p3_s4_loop_policy.py:80-82` の `validate_ir` は `parse_policy_ir` 内の呼出しと重複します。`default_cfg`、`drive_iteration`、`run_one_iteration` の admission policy bind も同じ policy なら冪等です（`ident.py:84-98`）。**反例:** 正常な IR と通常の CLI 実行。**影響:** 現状の受理集合は変わりませんが、重複した判断点が増えます。**代案:** parser の一回の検証と、campaign identity を確定する一か所の bind に寄せる。

## 実装子の報告の主張の検証

core 報告の gate 順序、既定 21 と本 driver の 26、共有 `quarantine` 不変更、初回履歴なしでの coder 入力生成は差分と一致します。ただし「配線済み」は所見 1・2 の CLI 経路まで成立した意味には取れません。role 報告の adapter 未配置は子作業時点の状態であり、対象 commit には adapter 3 件が入っています。報告どおり、実 compiler と変異の単一理由性を実走で確認した証拠はありません。本レビューも指定に従い静的検査のみです。

変更の大枠は plan v2 に対応します。IR parser、auditor 上限の引数化、二つの proposal 契約、二つの reject subtype、build entrypoint、driver、coder role 2 本、auditor 改訂、登録簿、固定 coder spec は名指しされた範囲です。`_reject` と履歴射影も指定された WAL と自系列入力に必要です。追加の汎用 gate や台帳を削除対象として特定できませんでした。320 行の driver と 197 行の test には、所見 1・2 の実行経路と所見 3 の結果分類の確認が欠けています。

## 変異 M-E1〜M-E11 の単一理由性の見立て

M-E1 は所見 4 により **kill 不成立**。M-E4 は所見 5 により **期待 node 未確定**。M-E2、M-E3、M-E5〜M-E11 は静的には対応 fixture が見えますが、単一理由性と失敗 node の完全集合は未実走なので確定できません。P-E1 を diagnostic pin とする区別は `docs/dev-wave/mutation.md` の DW-M03 と整合します。

## 再発しうる失敗の型

`docs/failures.md:21` の型タグでは、M-E1 の診断だけを kill と数える経路が **[恒真ゲート]**、runbook と CLI の preview 契約の食い違いが **[ドリフト]** に当たります。他の型タグの再発は、この差分からは認定しません。

## 総括

**NO-GO。** must-fix は、① auditor 前に coder だけで preview できるようにすること、②初回 `--no-build` の `dry-pass` が正常に返るようにすること、の 2 件です。加えて、F の履歴分類と M-E1・M-E4 の変異登録を修正してから検出力を主張してください。