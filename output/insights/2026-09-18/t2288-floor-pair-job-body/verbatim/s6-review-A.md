## 所見

確認対象は HEAD `20aca300643fc846159d4cfbe069bf43fe562627`。指定資料・patch・現物を静的に照合した。pytest は実行していない。以下、J＝`tools/pegasus/floor_pair_campaign.sh`、S＝`tools/pegasus/submit_floor_pair.sh`、T＝`orchestrator/tests/test_floor_pair_job_contract.py`。

1. **TERM 経路の実行観測が赤のまま。**
   - **対象:** T:289–306、J:167–190、`focus-1.log`。
   - **何が / 正しくは:** 計算ノードの焦点走は **503 passed / 1 failed / 1 skipped**。失敗は `signal_observed` を期待した receipt が `completed` だった点で、rc=7 の回収と保存はその前の assert を通っている。したがって「wait 全体が壊れた」とは断定できないが、B5/B8 の signal 観測は成立していない。送信先 PID・TERM 送信成功・trap 到達をこの snippet 内で切り分け、局所修正する必要がある。sleep 延長や期待値の緩和だけでは閉じない。
   - **影響:** 現状では TERM を受けた job の回収経路を検証済みと扱えず、途中 JSONL を残す終了条件について受入根拠が欠ける。ログ自体は凍結成果物の破損を示していない。
   - **判定:** **must-fix**。この test の削除は §4.4/B5 を満たさない。

2. **signal 後に成功した driver の rc を shell が上書きする分岐は裁定外。**
   - **対象:** J:189–190。
   - **何が / 正しくは:** `DRIVER_RC=0` でも signal を観測すると `JOB_RC` を 143/129/130 に変更する。§4.2 の「driver rc は保存して伝播」、B8 の「記録して再 wait」に対して余分な終了方針である。190 行を削り、signal は `reason` に残せばよい。現行 test は child rc=7 だけなのでこの差を検出しない。
   - **影響:** terminal・summary を正常に書き終えた driver でも job は失敗扱いになり、job rc による運用上の受理集合が狭まる。
   - **判定:** **must-fix**。削除後も §4.2、B8、申し送り 5、規律 2 を満たす。

3. **runbook が同一 HEAD の単位を spec 間にまで拡大している。**
   - **対象:** `docs/pegasus-runbook.md:1667`。
   - **何が / 正しくは:** 「9 job すべて同じ HEAD」は申し送り 2 の「**各 spec の** w1・w2・finalize は同じ HEAD」より強い。S の A1 検査も同 spec 内であり、指定された driver の finalize 検査も同じ単位である。「各 spec の 3 job を同じ HEAD H に固定する」に直すべき。
   - **影響:** 指定資料が要求していない workload 間の HEAD 共通化により、運用上の投入可能集合を余分に狭める。集約の別要件まで本レビューで保証するものではない。
   - **判定:** **should**。強化部分を削っても §2 A1・§4.3、申し送り 2・7 を満たす。

4. **`nm` の window 前段は実用的だが、finalize まで必須にする理由はない。**
   - **対象:** J:216、`floor_pair_driver.py:2117,2995,3113`、裁定 §3 B3。
   - **何が / 正しくは:** window では JSONL 作成後の session 内で trace symbol 検査が走る。`nm` 不在を前段で止めることは、使用不能と分かる窓を消費しないために有効。一方、指定された finalize 経路はその session 処理を通らない。`pgrep` も測定 probe 用であり、`env` は両 shell 自身では呼ばれていない。B3 を見直し、測定専用 command を finalize の必須集合から外す候補になる。
   - **影響:** `nm`/`pgrep` がないだけで、既存 JSONL から summary を生成できる finalize が起動前に拒否される。
   - **判定:** **should**。これは実装だけの逸脱ではなく**裁定自身の過剰**。現行 §4.2 の「9 本」を維持したまま削除したとは言えないため、B3/§4.2 の局所改訂が必要。申し送り 1〜7・規律 2 は維持できる。

5. **job body の spec 名と workload/window 対応の再列挙は削除候補。**
   - **対象:** J:91–98。
   - **何が / 正しくは:** §4.2 は binding の存在・形式と mode を求めるが、ここでは S の pin 選択に加えて 3 spec の完全名と window 名をもう一度固定している。S の閉じた引数・pin 表を残し、J は window ID を spec の `windows[]` で exact に引けば足りる。`WORKLOAD` 導出と名称の二重管理を削れる。
   - **影響:** 正規 submitter が生成する入力集合は変わらない。削除すると直接 job に渡した別名の spec は早期名称拒否されなくなるが、driver の sha・HEAD blob・spec 検査は残る。
   - **判定:** **should**。削除後も §4.2 の binding、§4.3 の固定 pin、申し送り 1〜7、規律 2 を満たせる。mode 検査と finalize の `none` は残す。

6. **receipt の stdout hash と qsub rc 専用 file は要求に対して余分。**
   - **対象:** J:111,117、S:239、T:259–260,305。
   - **何が / 正しくは:** §4.2 は create-only result を要求するが `driver_stdout_sha256` は指定していない。driver stdout は既に保存され、凍結 JSONL・summary の権威ある検証にこの hash は使われない。S の `qsub.rc` も最終 receipt の `qsub_rc` と重複する。前者の全量読み直しと後者の追加書込みは削除候補。nonce・HEAD・spec・mode・rc・時刻など実行の対応付けに必要な field まで削る理由はない。
   - **影響:** stdout の再読込失敗や `qsub.rc` の書込み失敗を、測定や投入そのものの失敗として追加判定する経路が増える。
   - **判定:** **should**。削除後も §4.1〜4.3 の所有・create-only receipt、申し送り 5〜7 を満たす。T の field 完全集合 pin も追随して削る。

7. **文字列 test は「拒否の実効性」の証拠にはならず、一部は削れる。**
   - **対象:** T:217–227,228–242,355–361。
   - **何が / 正しくは:** `test_checkout_and_input_binding` の文字列部分は、対象行を到達不能な分岐へ移しても通る。`test_no_build_or_output_replacement` も列挙文字列以外の書き方を扱わず、無害な comment で落ちる。文字列削除には反応するため「全く殺傷力がない」とまでは言えないが、gate の実行検証ではない。checkout の文字列存在 pin は削除候補。binary の合成 bytes 実行検査は残す。ただし 241 行の実行権剥奪ケースは hash 不一致を残したままなので、X_OK 検査の独立した証拠にならない。元 bytes に戻してから chmod すれば局所修正できる。
   - **影響:** 現状では checkout 検査を通らない実装や、実行権検査を省略した実装が test を通りうる。成果物の実際の受理は残存 driver 検査に依存する。
   - **判定:** **should**。削除後も §4.4/B5 の gate 到達・argv・dry-run・child rc 観測は残る。禁止処理の文字列検査を残すなら「静的な限定検査」と説明する。

8. **実投入前に実配送を確認済みにする runbook の順序は成立しない。**
   - **対象:** `docs/pegasus-runbook.md:1661–1663`。
   - **何が / 正しくは:** 実 qsub・8 変数の伝播・実効 walltime・signal 配送を「確認してから」最初の実投入を行う、という文は循環している。裁定 §5 に合わせ「次の測定 wave の初回実行で確認し、結果を記録する」とすればよい。
   - **影響:** 凍結成果物の受理集合は変わらないが、初回投入に達成不能な事前条件を置く。
   - **判定:** **should**。§7.0 の投影行は下記の逐語で正しく、実測済みという過剰主張はない。

   ```text
   | `tools/pegasus/floor_pair_campaign.sh` | `dispatch-required` | `static job-body classification` |
   | `tools/pegasus/submit_floor_pair.sh` | `local-ok` | `static login-side submitter classification` |
   ```

9. **前段重複を driver 変異の検出と数えない、という A6 の限定は必要。**
   - **対象:** S:139–144,173、J:227–229、`floor_pair_driver.py:1197,2676`。
   - **何が / 正しくは:** 例えば loader の spec sha 比較を無効化して不一致 bytes を shell 経由で渡しても、S/J が先に拒否する。finalize の header 比較を無効化して異なる `loaded_head` を渡しても、S の A1 が先に拒否する。その拒否を driver 変異の kill と数えると D2069 が指摘する誤帰属になる。現行 M1〜M10 は shell・登録簿・docs を対象とする限定なので、その限定を保持する。
   - **影響:** shell 経由の拒否集合が同じでも、直接 driver の受理集合の拡大を見逃しうる。
   - **判定:** **情報**。この理由だけで前段を一律削除する必要はない。

## 削除候補表

「裁定改訂」は現行 §4 の要求そのものを減らす提案であり、実装の無断削除とは区別する。

| 箇所 | 重複する上流検査 | 残す/削る | 理由 |
|---|---|---|---|
| J 段1 bootstrap | driver の引数・spec 検査 | binding は残す。名称再列挙は削る | 所見5。job ID 形式・evidence directory 存在は scratch/出力先の直接の前提 |
| J 段2 environment | 同等の包括的整理はない | 残す | §4.2 の明示要求。検査台帳の追加ではない |
| J 段3 interpreter | import 時の失敗 | 残す | bootstrap 実行に必要 |
| J 段4 commands | command 実使用時の失敗 | window の `nm`/`pgrep` は残す。finalize 用集合と `env` は削減候補 | 所見4。B3/§4.2 改訂が必要 |
| J 段5 checkout | loader の HEAD 取得、run_window の runtime HEAD | 残す | **投入時 expected HEAD との一致は driver の loaded/runtime 比較とは別**。queue 中の HEAD 変更を止める |
| J 段6 spec/binary | loader の sha・HEAD blob・binary sha | 現裁定では残す | 既知不正を driver 前で拒否。これ自体に窓保護の独自性は薄いが §4.2 明示要求。finalize も loader が binary を読むので、binary 存在・sha は無関係ではない |
| J 段7 site | `_assert_live_environment`、ただし window のみ | 残す | window では scratch 前の拒否。finalize では計算ノードに統一する裁定の実装 |
| J 段8 time | session 開始時刻検査 | 残す | driver は JSONL 作成後に判定するため、前段は窓 path 温存に効く |
| J 段9 scratch | なし | 残す | §4.2/B2。colon 正規化を含む |
| J 段10 time 再検査 | 段8、session 時刻検査 | 残す | scratch 準備後の時刻で判定する A4 |
| J 段11 driver/wait | なし | wait は残す。rc 上書きは削る | 所見1・2。新しい signal 管理機構の追加は不要 |
| J 段12 result | driver result stdout | receipt は残す。stdout hash は削る候補 | 所見6。create-only と driver rc 保存は必要 |
| S 引数・pin・walltime | driver は workload CLI/pin 選択を持たない | 残す | §4.3。追加引数 `--help` は `-h` の同義で nit 以下、投入集合を増やさない |
| S canonical/detached/clean | root/HEAD は部分重複。detached/全 tracked clean は独自 | 現裁定では残す | 実行 H の運用固定。完全な不変性の保証とは呼ばない |
| S spec/binary | loader の束縛 | 残す | qsub 前の拒否で無駄な割当てを避ける。A6 の shell 検査に分類 |
| S window 時刻 | J 時刻、driver session 時刻 | 残す | 投入時の無駄な割当て回避と queue 後の再判定は役割が異なる |
| S A1 他窓 header | finalize の header exact 比較 | 残す | **申し送り2**。不整合が既に分かる状態で次窓を消費しないため。仮想リスクだけの追加ではない |
| S A5 対象 JSONL 不在 | run_window の出力検査・exclusive create | 残す | **申し送り5**。既存窓への無駄な再投入を拒否。同時投入防止とは呼ばない |
| S finalize readiness | finalize の窓検証・summary exclusive create | 残す | A1/A2。割当て回避が価値。全 record validator の複製はしていない |
| S evidence/dry-run/qsub/receipt | なし | 残す。`qsub.rc` は削る候補 | §4.3/B5。`indeterminate` は A5 の不明時再投入禁止を表すため必要 |
| 登録簿・test_hooks の追加 | 既存 golden による閉包 | 残す | B1 の必要変更。新しい台帳体系は追加していない |

契約 test 18 関数の判定は以下。

| test（`test_` 省略） | 重複・観測範囲 | 残す/削る | 理由 |
|---|---|---|---|
| `registry_entries` | test_hooks と4 field が重複 | 残す | §4.4/M1 の指定対象 |
| `frozen_spec_pins` | D2138・実 bytes・shell 選択を照合 | 残す | M2、固定入力に直接対応 |
| `pbs_and_walltime_binding` | PBS 静的列＋qsub 配列実行 | 残す | §4.2/4.3 |
| `walltime_values` | mode 別値と秒換算 | 残す | A3、単一決定箇所 |
| `submitter_argument_set` | 正負引数を実行 | 残す | §4.3。`--help` の追加検査は軽微 |
| `window_id_and_fields` | 実 spec の ID・境界読取 | 残す | 段2訂正事項 |
| `window_gate_boundaries` | 同じ窓値を6窓分反復 | 残す | M3。値の重複だけを理由に削る利益は小さい |
| `hostname_gate` | 関数の正負入力 | 残す | M4 |
| `gate_order_and_calls` | site/time/scratch/driver の stub 到達 | 残す | B5/M7。bootstrap〜checkout 全体の到達証明ではない |
| `driver_argv` | mode 別配列を実行 | 残す | B5/M5 |
| `checkout_and_input_binding` | 文字列 pin＋binary 関数実行 | 文字列部分は削る候補 | 所見7。実行権ケースは局所修正 |
| `evidence_and_receipts` | create-only receipt を実行 | 残す。余分な field pin は削る | §4.2/4.3、所見6 |
| `dry_run_has_no_execution` | stub qsub の有無を実行 | 残す | B5/M8 |
| `child_rc_collection` | child rc・TERM を実行 | 修正して残す | 焦点走の実測赤。削除不可 |
| `scratch_name_normalizes_colon` | assignment を実行 | 残す | B2/M9 |
| `submitter_head_consistency_preflight` | 合成 header の正負 | 残す | A1/A5/M10 |
| `finalize_preflight_requires_terminal` | incomplete 許容・欠落拒否 | 残す | A1/A2。成功 terminal だけに狭めていない |
| `no_build_or_output_replacement` | 禁止文字列の静的走査 | 削除候補、または限定を明記 | 所見7。argv・引数の実行 test と重複する部分もある |

提示された login 1.6 秒だけを理由に18関数を過剰とは判定しない。焦点走ログが示す 7.07 秒は複数 file の走行時間であり、18関数単独の時間と混同できない。

## GO / NO-GO

**NO-GO — must-fix は所見1・2。**

TERM 観測の赤を局所修正し、signal 後も driver rc を伝播する形で再確認する必要がある。過剰検査の削減は上表の範囲で行い、driver・spec・集約の変更や新しい gate の追加は不要。

## 総括

実装は概ね plan v2 に沿うが、signal 時の成功 rc 上書きは裁定外である。
焦点走は rc 回収まで通り、TERM 観測理由だけが赤であり、原因は静的読解だけでは確定しない。
A1・A5・window の `nm` 前段には、申し送りに対応する具体的な価値がある。
削減候補は finalize の測定専用 command、名称の二重列挙、余分な receipt 情報、実効性を示さない文字列 pin。
docs は spec 間の HEAD 共通化と初回投入前の確認順序を修正すべき。レビュー中の書込み・pytest・実投入は行っていない。