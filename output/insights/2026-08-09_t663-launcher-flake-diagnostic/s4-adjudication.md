# 段 4 裁定 — [T-663] / F57 launcher 診断

段 3 の 2 レンズ (A=正しさ境界 / B=実効性) は独立に同じ核心へ到達した。両者を real と裁定する。

## 最重要裁定 — 予算は一切広げない (R6)

段 2 プランの「wall 3→6 / evidence 1.0→2.0 / termination 0.05→0.2 / harness timeout 10→20」を
**全面不採用**とする。理由は 3 つ。

1. **レンズ A が 4 拡大すべてに、拡大後だけ通る具体的回帰を構成した** (A2〜A5)。
   とくに termination 0.05→0.2 は `codex_exit_code == 0` を期待する既存 assert
   (`test_codex_worker_launch.py:587`) を素通りさせ、SIGTERM 応答が 50ms→100ms へ悪化する回帰を隠す。
   harness 10→20 は receipt publication の 10〜20 秒級停滞を accepted で通す。
   これは絶対規律 2 の「検証を甘くして緑にする」に相当する。
2. **提案値の根拠が母集団違い** (A10/B7)。親の実測は login node の 84 receipt であり、
   F57 が起きるのは計算ノード 32〜48 worker・数千件の全走である。さらに親 brief の
   「evidence grace の方が薄い」は誤りで、evidence deadline は
   **session/rollout を発見するまで**の期限 (`tools/codex_worker_launch.py:1176-1178,1239-1248`) なのに、
   親は完了後の総 `wall_clock_s` と 1.0 秒を比べていた。**この brief の主張は撤回する。**
3. **順序が逆** (B7)。診断を入れる目的は「どの条件が落ちたか」を実負荷で観測することである。
   先に予算を広げれば、観測したい発火機会そのものを潰す。**計装が先、値の変更は実 artifact の後。**

したがって本 wave は **fixture harden を行わない**。予算変更の是非は裁定パッケージ (S3) へ回す。

## 採用する must-fix (scope 内)

- **R1 (A1/B3) 受理 conjunct の真理値行を出す。** attempt ごとに `accepted`, `limit_trigger`,
  `evidence_status`, `metering_status`, `codex_exit_code`, `validator_rc`,
  `process_group_residual`, `termination_verified`, `wall_clock_s` を出し、receipt 全体の
  `outcome`, `stop_reason`, `launcher_rc` を添える。表現は「原因」ではなく
  `failed_predicates=[...]` (複数可) とする。
  *成果物影響:* これが無いと validator reject と子 process 異常が区別できず、次の再発でも
  受入 gate の赤を差分へ誤帰属する危険が残る。
- **R2 (A8/B2) 上限付き抜粋にし、一次失敗を絶対に覆わない。** stream は byte 上限つき head+tail、
  `errors="backslashreplace"`、総 byte 数・sha256・切詰め量・path を併記。
  総 message は 16 KiB 以下。診断生成の例外は `diagnostic_status=failed:<type>` として
  同じ例外内へ畳み、`actual rc != expected rc` の 1 行を**先頭**に置く。
  **dispatch は失敗ログの末尾 64 KiB しか中継しない** (`tools/pegasus/dispatch_compute.py:34,759,771`)
  ため、真理値行の短い要約を**末尾にも**繰り返す。
  *成果物影響:* これが無いと非 UTF-8・巨大出力で診断側が例外になり、いま見えている
  `assert 1 == 0` すら消える。
- **R3 (A7) meta-test を恒真にしない。** 専用例外 `LauncherReturncodeMismatch(AssertionError)` を
  定義し、`pytest.raises(...)` で捕捉した `str(exc)` だけを検査する。
  formatter を sentinel へ差し替えて結線を固定する wiring test を別に置く。
  *成果物影響:* 恒真だと「診断が入った」と記録しながら実際は旧来の空 assert のままになる。
- **R4 (B4) 機械置換の境界。** 置換対象は launcher 実行の `completed.returncode` assert のみ。
  checker (`check-receipt`) の rc assert と `receipt["launcher_rc"]` 等の receipt 内 assert は
  削除しない。unordered `[0,2]` を期待する `:1110` は単一期待 rc helper へ機械置換せず、
  2 process をラベル付きで扱う専用経路にする。
  *成果物影響:* 置換しすぎると検出力が静かに落ちる。
- **R5 (B1) 3 形態を同じ診断契約に載せる。** `subprocess.run` の `CompletedProcess`、
  direct `Popen` (`:1535` ほか)、in-process (`_run_main_in_process`) と、
  `subprocess.TimeoutExpired` を同じ adapter に通す。in-process は stream を持たないので
  「stream 不在」を明示して receipt 行だけ出す。
  *成果物影響:* F57 の既往 node `test_manifest_is_appended_while_correlated_session_is_running` は
  direct `Popen` であり、載せなければ再発しても原因が分からない。
- **R7 (A10/B8) 主張を狭める。** 本 wave は「F57 の launcher subfamily について、次回再発時に
  どの受理 conjunct が落ちたかを観測できるようにした」までしか主張しない。
  **T-190 と F57 は閉じない。T-663 も「原因分離の計装を入れた」で閉じ、原因確定は未了とする。**
  F57 には git timeout・PBS walltime・並行 wave 競合という別 producer が混在する。

## 撤回する親 brief の主張

- 「evidence grace の余裕が薄い (2.3〜4 倍)」は**誤り**。比較対象を取り違えていた (上記 2)。
- 「`max_wall=0.30` probe が機序を確認した」は**正の対照にすぎない**。同じ署名を作れることは
  示すが、実障害の原因が予算超過であることは示さない。F57 台帳の「未確定」は依然として有効。
- 「(P3) 本 wave で T-190 を閉じる」は撤回 (R7)。

## 裁定パッケージ候補 (scope 外・ユーザーへ返す)

- **S1**: 診断が dispatch の末尾 64 KiB 中継を越えて人間へ届くことの機械検査
  (`test_pegasus_dispatch_compute.py` まで scope 拡大)。本 wave は message 側の末尾要約で緩和のみ。
- **S2**: production は最終 publication 後に wall gate を再評価しない (A5)。10〜20 秒級の
  publication 停滞を accepted で通す穴。production 修正が要る。
- **S3**: fixture 予算を広げるか否か。実負荷の receipt を 1 件でも得てから、値と据え置き
  sentinel を根拠付きで決める。
- **S4**: 「フレークが消えた」ことの証明方法 (48-worker 反復受入 N 回)。有限回で不在は
  証明できないため、記録の表現も含めて裁定が要る。
- **S5**: preflight 失敗・publication 失敗で receipt が存在しない経路への早期 receipt (B6)。

## 変異事前登録 (DW-M01 / DW-M08)

本 wave は**テスト強化のみ** (production 無編集) なので、DW-M08 に従い
**新テスト版と変更前 HEAD 版テストの両方**へ同じ変異を走らせ、新テストだけが検出する差分を示す。

| ID | 変異位置 | 変異内容 | 新テストの期待赤 | HEAD テストの期待 | 種別 |
|---|---|---|---|---|---|
| M1 | `tools/codex_worker_launch.py` `_seal_attempt` の `"codex_exit_code"` | 常に `0` を書く | 診断が非 0 の子 rc を示すことを固定する新 meta-test が赤 | 緑 (読む assert は `:587` の `== 0` のみ) | diagnostic sensitivity pin |
| M2 | 同 `"validator_rc"` | 常に `0` を書く | validator 失敗を注入する新 meta-test が赤 | 緑 (読む assert は `:588` の `== 0` のみ) | diagnostic sensitivity pin |
| M3 | `_evidence_status` の返り値 | 常に `"complete"` | evidence 注入の新 meta-test が赤 | 赤 (`:1526,1635,1654,1667`) | 実効 kill |

単一理由性: M1/M2 が触る field を読む assert は `grep` で `:587` / `:588` の 2 箇所だけと確認済み。
M3 は「evidence gate を隠す」という単一理由で複数 node が赤くなる。
anchor の逐語は段 6 の fix 後に `DW-M07` で再検証する。

## プラン v2 (実装子への指示)

段 2 プランの第 1 節 (診断保存) と第 3 節 (meta-test) を、上記 R1〜R5 で強化して実装する。
**第 2 節 (予算) は実装しない。** 第 4 節の波及列挙は維持。第 5 節の production 無編集は維持。

新テスト名は変異事前登録のため次に固定する。

- `test_launcher_failure_diagnostic_reports_failed_predicates`
- `test_launcher_failure_diagnostic_reports_nonzero_codex_exit_code`
- `test_launcher_failure_diagnostic_reports_validator_rejection`
- `test_launcher_failure_diagnostic_reports_incomplete_evidence`
- `test_launcher_failure_diagnostic_survives_missing_or_invalid_receipt`
- `test_launcher_failure_diagnostic_is_wired_to_the_returncode_assertion`
- `test_launcher_failure_diagnostic_is_bounded_and_repeats_summary_at_end`
