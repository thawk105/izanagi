## 所見

静的検査のみ。ファイル変更・pytest 実走はしていません。

**B1｜整合｜対象: plan「docs 文案」、brief S3｜推奨: must-fix**

§3 は対象ごとの手順を示す一方、新 launcher は複数対象をまとめて受け取る。**全入力対象の検査・detach・branch 削除を終えてから launcher を起動する**という順序が明文化されていない。

launcher の argv は全入力 path を含むため、起動後にそのいずれかを占有検査すると自己占有になる。別の非包含対象だけを検査する場合まで必ず衝突するわけではないが、全対象入りの生存 wrapper があれば衝突する。§1 の禁止は launcher 単独呼出しとは矛盾せず、検査と撤去を包む wrapper が問題になる。

全入力対象について手順 1・2 と必要な直前再評価を完了し、検査呼出し終了後に別呼出しで launcher を実行する順序を明記する。Codex overlay の「各破壊操作直前の再評価」も維持する。

成果物影響: 文書どおり実行しても自己占有で停止する、または一部対象の gate 未完了で撤去を開始する余地が残る。

**B2｜実効性｜対象: brief 完了判定(b)・P3、plan「signal と有界な停止」｜推奨: must-fix**

「親」を **rm の直接親である launcher** と、launcher を起動した shell／tool 実行基盤に分ける必要がある。

- 同じ PGID は、親 PID だけへの signal を自動転送しない。
- 現案が扱うのは launcher 自身が受信する TERM/INT。
- Bash tool の timeout／session 終了が、どの PID・PGID に何を送るかは指定資料から確定できない。shell が残る構成か `exec` で置換されるかも未確定。
- Bash 一般の SIGHUP 処理も条件付きであり、tool 終了＝TERM/INT と推論できない。[Bash の signal 仕様](https://www.gnu.org/software/bash/manual/html_node/Signals.html)

したがって「親停止で必ず道連れ」は現案の証明範囲を超える。TERM/INT 転送という P3 は裁定に沿う局所実装だが、外側の親停止、launcher 単体への SIGKILL、SIGHUP は別途境界を明示する。SIGKILL 限界を docstring に書くだけで無条件の完了判定(b)を満たしたことにはできない。

成果物影響: launcher の単体テストが緑でも、実際の tool 終了後に削除が継続し得る。

**B3｜実効性｜対象: plan「中断負例の推奨案」、親追加 P4 改｜推奨: must-fix**

**実行環境への依存は自己停止 wrapper 案の方が小さい。ただし、現規律のまま無条件採用できない。**

| 観点 | ptrace 案 | 自己停止 wrapper 案 |
|---|---|---|
| 権限制約 | Yama・seccomp・LSM に依存 | ptrace 不要。同 UID の signal と `/proc` 観測が中心 |
| 決定性 | exec stop は有効。ただし TERM 転送の pending 確認前に再開すると削除開始との競争が残る | `T` → TERM pending → CONT の順序なら、その競争を閉じやすい |
| 証明範囲 | 実 rm と送信元 PID を観測可能 | 停止中の wrapper への転送を証明。中断負例では実 rm に到達しない |
| 規律 | 機構を置換しない | PATH 上の rm を差し替えるため、brief が引く DW-O14 との裁定が必要 |
| 受入 | ptrace 不可で核心 node が skip になり得る | `/proc` 不可・実行禁止 mount・signal 制約などは依然確認が必要 |

Yama mode 1 は子孫 tracing を一律禁止しない。mode 2 は capability が必要、mode 3 は TRACEME も禁止する。[Kernel Yama 文書](https://kernel.org/doc/html/v5.16/admin-guide/LSM/Yama.html) また「container なら ptrace 不可」という一般化も誤りで、適用 profile 等に依存する。[Docker seccomp 文書](https://docs.docker.com/engine/security/seccomp/)

PATH 解決は plan の `Popen(["rm", ...])` には適合するが、「固定した実 rm を使用」という fixture 説明とは不一致。採用するなら、限定 wrapper を同期用差し替えとして許容する判断、実 rm による別正例、子専用 env、shell の signal disposition を固定する。`ShdPnd` は送信元を示さないため、ptrace 案と同じ送信元証明とは記載しない。

特に **pending TERM を観測できず KILL で終わった場合は赤**とする。核心 node の skip を受入成功へ含めない。

成果物影響: 核心テストが環境依存で欠落する、または転送を削った変異でも緑になる。

**B4｜整合｜対象: brief 実測6・S1、plan 変更面｜推奨: must-fix**

`tools/README.md` に一覧追記が不要なのは正しいが、同文書は**新規 script の実行場所分類**を要求している。この義務が plan にない。

新 launcher は入力件数・木の規模に上限がなく、未実測。`tools/pegasus/` 外の未登録 script は hook を通り得るが、それは login 実行許可ではない。受入テストを `run_tests.py` 経由で走らせることも、運用時 launcher の admission を代替しない。

分類と利用可能な実行経路を設計に含める。registry の新規登録や exemption を無断で追加することまでは要求しない。

成果物影響: tool は完成しても、想定する login node の cleanup 手順として実行可能か未解決になる。

**B5｜前提｜対象: brief P1・P2・実測1〜4｜推奨: 裁定パッケージ候補**

P1 は支持する。`dev_wave_cleanup.py:869` の撤去は同一 process の `shutil.rmtree` で、DW-O28 も別入口を名指す。

P2 の「docs-only では検査不能」は言い過ぎ。文書契約の検査は可能であり、正当化すべきなのは「再利用可能な実行機構を検査するため固定 launcher を設ける」という選択である。

実測3の `site=None` probe は、その入力と設定における許可しか証明しない。「全環境で guard が止めない」へ広げない。実測4の背景 worker 慣行も、cleanup 起動基盤の signal 契約の証拠にはならない。「repo に launcher が存在しない」「全 worker が同方式」という網羅性は、提示された実測記述だけでは独立確認できない。

成果物影響: 局所実装として妥当な選択を、未証明の必然性で正当化してしまう。

**B6｜前提｜対象: plan timeout・escalation・test 設計｜推奨: 裁定パッケージ候補**

TERM → 5 秒 → KILL → 1 秒 → unknown は、所有する直接子だけを対象にした取消終端処理なら scope 内と判断する。再試行・常駐監視ではない。残存時は「停止を試みたが終了未確認」と報告し、「道連れ完了」としない。

`--timeout-seconds` も既存の「各長い timeout」を実装する範囲には収まる。ただし **既定3600秒を裏付ける guard probe 値は brief にない**。運用上の仮値と明記し、外側 tool の timeout より長く設定すれば内側取消が実行されない点を解決する。

追加テスト時間は未実測で算定不能。5＋1秒は毎回の必須待機時間ではなく、取消に抵抗するケースの上限である。正常経路は早期終了させ、各同期・回収の期限と node 数から最悪時間を積算する。既存全走時間なしに「5分以内」とは判定できない。

chmod 負例の root skip は偽緑回避として妥当。ただし非 root の権限回避 capability も考慮し、skip を failed 契約の証明には数えない。`tmp_path` は通常 repo 外だが、TMPDIR／basetemp の指定次第なので配置を確認する。repo 内 wrapper・一時木は作らない。

成果物影響: 時間上限超過、並列 shard での flaky、または重要負例の未検証が残る。

**B7｜実効性｜対象: plan 変異 M-d〜M-h｜推奨: nit**

M-h を未証明とするのは正しい。M-a の fail-closed 検出は PGID 比較の必要性そのものを証明しない。M-d／M-e は直接呼ぶ判定関数内の変異には効くが、本番制御フローがその関数を迂回する変異まで検出したことにはならない。

成果物影響: 変異の帰属を広げると、実際より強い受入証拠を報告する。

## 効く層の表

| 層 | scope 内／外 | 根拠 |
|---|---|---|
| 新 launcher | 内 | 固定 rm の起動・取消・結果集約。単独では利用を強制しない |
| `/cleanup-branches` §3 | 内 | tool を名指す。全対象 gate 完了と起動順序の明記が必要 |
| Codex overlay | 編集は外、動作への適用は内 | dispatcher 全文を継承する。各操作直前再評価・real prune 禁止も継続 |
| DW-O28 自己撤去 | 外 | `dev_wave_cleanup.py` を直接使用。新 launcher は効かない |
| Bash tool の寿命管理 | 現案では未証明 | tool/session 終了時の signal 配送契約がない |
| prune 防止 | §3 の手順として内 | launcher は prune を実行しない。呼出側の停止義務は文書契約 |

裁定パッケージは、外側親停止までの保証範囲、wrapper 同期の許容範囲、運用時 admission に限定する。DW-O28 の変更、PDEATHSIG、汎用 command、再試行、監視・進捗 framework、prune 自動化は追加しない。

## pin 閉包の追加分

- **必須更新 pin の追加漏れは確認できない。** whole-file SHA 2箇所、synthetic 本文、本文サイズ2箇所、超過 fixture は plan に含まれる。
- `CLEANUP_OCCUPANCY_CONTRACT` と `_has_cleanup_execution_edges` の §1 条件は保存される。
- 自走 harness に `pytest.main` があれば、`test_plain_runner_coverage` の静的条件を満たす。README allowlist 追加不要。
- `test_selection_contract.py` は全 test の登録簿ではなく除外契約。新 test の追加登録は不要。`test_pytest_collection_config.py` にも今回のための登録更新は不要。
- `acceptance_duration_ledger.json` は時間配分の確認対象として plan に追加する。ただし新規 test の存在だけで必須 pin 更新とはいえず、時間値を推測で記入しない。
- pin とは別に、**`tools/README.md` の実行場所分類義務が漏れている**。B4 のとおり。

## byte 勘定の検算

メモリ上で exact 文案を置換して確認した。

| 項目 | UTF-8 bytes |
|---|---:|
| 現行全文 | 6203 |
| 現行手順3／新手順3（末尾改行なし） | 419／432 |
| 差分 | ＋13 |
| ` (branch を解放)` 削除 | −19 |
| 改訂全文 | **6197** |
| 上限／残り | 6204／7 |

86行、最大105文字。SHA256 も一致する。

```text
84a7d15fd2774014654d2e9b43d4b4bc40bc3a0e67afca45581e006915bc4bd8
```

補足削除は `checkout --detach` と §0 の説明が残るため意味を保存する。`6197 + "\n" + "x"*7 = 6205` で超過 fixture も成立する。D782 は削減段階で収容でき、例外・上限引上げは不要。ただし B1 の順序説明を加えた最終文案では再計算が必要。

## 総括

must-fix は **4件（B1〜B4）**。
最重要は **B2：launcher の TERM/INT 受信と、実運用の「親停止」を同一視できないこと**。
byte・既存 pin 閉包は成立するが、運用順序・実行場所・核心テストの成立条件は未解決。
wrapper 案は環境依存を減らすが、DW-O14 と証明範囲を裁定してから採用する。
