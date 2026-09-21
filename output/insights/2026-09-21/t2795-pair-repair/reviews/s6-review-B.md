# 判定

**現状は NO-GO。** 本体の候補→stock 配線に新たな致命的欠陥は見つかりませんでした。ただし、変異の帰属に修正が必要です。既知の赤 3 系統は新規所見に数えていません。

以下は **未実走・静的読解**です。実測については親の job `14717.nqsv` の全文ログを検算しました。

# B1 — must-fix：M4 は現状の登録だと「偽造受理」の変異にならない

**位置:** `orchestrator/campaign/loop.py:144`、`orchestrator/tests/test_campaign.py:14279`、`s4-adjudication.md` §3 M4。

**放置時の成果物影響:** 偽造 session を受理していない変異の例外型変化を、発行証明の防御を検証した KILLED と誤計上する。

発行確認の `if` を削っても、直後の `_AUTHORIZATION_SESSIONS[session]` が残ります。同型未発行個体は `KeyError`、foreign の辞書は `TypeError` となり、認可再利用へ到達しません。負例が期待する `ExecutionGuardError` と違うため test は赤になり得ますが、「偽造・コピー S を受理」という登録上の性質とは異なります。

**推奨:** M4 の単純 guard 削除は、受理集合については冗長な拒否、test 上は診断契約の差として扱い、認可迂回の独立 KILLED から外してください。発行証明の変異を残すなら、未発行個体に既存 binding を誤って流用するなど、実際に所有権を移してしまう変更を exact に定義し直す必要があります。production に救済取得や互換層を追加する必要はありません。

M5 は `close()` を無効化すれば実際に再利用可能になるので、M4 と一括削除する理由はありません。

# B2 — should：H/M18 の静的 pin は session の到達を証明しない

**位置:** `orchestrator/tests/test_p3_s4_loop.py:10706`、`orchestrator/campaign/p3_s4_loop.py:2066`・`:2262`。

**放置時の成果物影響:** session の代入断片が残っていても、実際の `run_campaign` に session が届かない変更を H 群で見逃す。

`test_pair_session_forwarding_at_campaign_calls` が確認するのは、代入文と `**campaign_options` の存在です。その間で options を再初期化したり session key を取り除いたりしても、この test は通ります。また、`drive_iteration` から候補 helper への中継は検査対象外です。

結合正例の `campaign_spy` は両 sink への到達を確認しており、C1 は有効です。ただし、裁定の H/M18 が指定した「両 `run_campaign` に同一 session が届く spy」を静的 pin に置き換えたことは、保証の縮小です。

**推奨:** lock を作らない既存 helper fixture と `run_campaign` stub で、引数の object identity を確認する検査へ置換してください。難しければ H/M18 は「代入断片削除の検出」に限定し、転送の実効性は C1 に帰属させてください。静的 pin と同内容の検査を増殖させる必要はありません。

# B3 — should：焦点走から B-4 の実 consumer が漏れている

**位置:** `orchestrator/campaign/p3_b4_launcher.py:141`、`orchestrator/tests/test_p3_b4_proposal_binding.py:17`、`orchestrator/tests/test_p3_b4_closed_critic.py:617`。

**放置時の成果物影響:** wiring inventory が緑になっても、変更された `main` を使う B-4 起動・proposal 契約の回帰が焦点走では未確認のまま残る。

10 file は session・pair・B-5・主要 inventory を押さえています。一方、今回は `main` の候補処理全体を session/context manager と例外処理の内側へ移しています。B-4 launcher はその `main` を直接参照します。

**推奨:** 次の consumer を焦点走、または後続受入で明示的に確認してください。

- `test_p3_b4_launcher.py`
- `test_p3_b4_proposal_binding.py`
- `test_p3_b4_closed_critic.py`

`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`、`test_campaign_import_invariant.py` も受入対象として確認する価値があります。ただし、検索で参照があるだけの全ファイルを焦点走へ追加する必要はありません。これらが壊れているとは主張しません。

# 既知の赤の是正方向と親の分類の検算

全文ログの `FAILED` node は次の内訳です。

| 系統 | 実数 |
|---|---:|
| `test_p3_b4_wiring_probe.py` | 23 |
| `test_p3_s4_loop_job_contract.py` | 74 |
| `test_p3_s4_loop.py` の結合検査 | 3 |
| 合計 | 100 |

提示された 18＋72＋3 は全失敗数ではありません。

**wiring probe:** 局所変数 `validator` の未解決が後段の cleanup・interdiction 検査も止めています。`_authorize_with_session` に `pre_write_validator` を明示的な引数として渡し、既存 sink と同様に直接呼ぶ修正を推奨します。inventory resolver の一般化や unresolved 呼出しの許可は不要です。単に `kwargs[...]()` に書き換えて目録から呼出しを消す修正も避けてください。

**job contract:** 共通の `proposal` pin 不一致と、`:1462` の独立した K2 行 pin 不一致があります。後者は依然として `"${k2_argv[@]}"` 単独行を数えています。したがって「109 行がすべて同じ根」が「全件を一か所直せば解消する」という意味なら不正確です。同じ shell 行変更に由来しますが、修正箇所は少なくとも二つあります。共通 pin 修正後に欠落集合が単一になることを再確認すべきです。

**attestation:** 「実機観測に入っている」という説明は正確ではありません。`:10754` ですでに `probe_fn=lambda: observed` を渡しています。失敗ログでは expected と observed の samples が同じであり、較正 profile のコピーがそのまま有効な正例観測になる、という fixture の仮定が成立していません。修正するのは代用観測の作り方です。実認可・receipt 再検算・claim・reservation をまとめて stub しないでください。

以上は差分との対応から今回の実装／test 変更起因と判断できます。既存赤という証拠はありません。ただし base の再実走はしていません。

# 本体経路と削除の妥当性

静的に追った経路は整合しています。

1. shell は proposal＋`--stock-control` を一つの driver に渡す。
2. 候補 checkout 内で TEMPLATE_PATCH、検疫、condition gate、`run_campaign`。
3. 初回認可成功直後に session を束縛し、評価へ進む。
4. 候補 checkout を退出してから、stock 用 checkout を新しく作る。
5. stock は authority 無しの context・専用 resolver・同じ session を使う。
6. 実 pipeline の結果と WAL の variant／`src_token == STOCK` で `certified-stock` を決める。

候補の quarantine reject では stock が初回 claim を取ります。認可後例外・abort・duplicate-skip では stock 試行に進みます。候補 checkout の退出例外も捕捉範囲内です。`BaseException` は捕捉しません。

各 helper の `applied()` は別 checkout 上で一回ずつです。二重適用の経路は見つかりません。共有 cache についても、候補／stock の genome・source token・admission による区別を崩す変更はありません。

B-5 の `slot_argv` は引き続き `--stock-control` 単独を生成し、pair 用の禁止条件は `run_iteration` との同時指定時だけです。独立 stock 起動と shell 集約の削除は妥当です。fixture＋stock の拒否は裁定どおりの**公開契約の縮小**であり、未使用コード削除とは記録しないでください。

# 過剰・重複と変異の整理

新しい永続台帳、汎用 framework、他 driver の自動 session 化はありません。module-private 発行表は今回採用した所有期間の実装です。

縮小候補は次のとおりです。

- `loop.py:212` の保存 record の PID 比較は、発行 PID 検査と初回 record 作成から同値が導かれます。
- `loop.py:214` の保存 record の protocol digest 比較も、初回保存時の同値と `saved.protocol_digest` 比較に含意されます。

いずれも保存 record が immutable で、同 process 内の任意改変を防壁対象外とする今回の前提によります。削るなら関連変異も合わせて整理してください。claim の**実ファイル読取りと record 全体比較**は削除対象ではありません。

test の小さな重複として、結合正例の checkpoint bytes 一致後の whiteboard 再比較、copy/deepcopy/pickle 各 case で繰り返す raw 未発行個体拒否があります。整理できますが、修復の必須条件ではありません。

変異については次の整理が妥当です。

| 対象 | 判定 |
|---|---|
| M2 | `created_utc` だけの改変は record 比較へ帰属できる |
| M3 | binding を変えず期限切れにする設計は妥当 |
| M6 | 発行 PID と record PID の比較をまとめて外す登録を維持 |
| M9 | perf preflight 例外までで止める test は lock-free の対象にできる |
| M12 | pair×B-5 の専用拒否は独立に残す |
| M19 | 実 shell の起動履歴一件の assert を主たる検出点にする |
| M20 | fixture 拒否の実 shell test を主たる検出点にする |
| M21 | 未設定／0 の既定 argv exact を維持 |
| C1／C2 | F1019 の claim 再取得を検出する異なる配線変異 |
| C3 | claim 成功だけでは足りないことを検証するので維持 |

pair 排他のうち value・emit・no-build・B-4 は後続の stock 排他でも拒否されます。machine-generated も別の前提検査があります。それらを単独 guard 削除の独立 KILLED と数えないでください。

# 文書・pin・F1019 の限定

`tools/pegasus/README.md:369` 以降は、親の予定どおり更新が必要です。具体的には次の記述が現物と異なります。

- stock へ K2 identity argv を別起動で転送する説明。
- 「proposal または fixture」の pair 対応。
- 候補の後に stock driver をもう一度起動する説明。
- stock 起動 argv の禁止一覧と shell が rc を集約する説明。

一つの pair argv と、driver 内部の候補／stock context 分離を説明する形に置換してください。`compute-result.json` には driver の戻り値を透過させます。B-5 の stock 単独口の説明は維持します。

layout 11・`run_campaign` 2・semantic caller 17 file／22 call は、この差分で増える構造ではありません。新規 subprocess もありません。import 閉包の件数が不変でも、今回のような callable 解決の失敗は別に発生するので、件数一致だけを consumer 検証済みとはしないでください。

`docs/phase3.md:495`、paper-story README の現況導線は親の更新予定に含まれています。過去の不成立記録は残し、日付付きの修復結果へリンクする方針で十分です。

結合正例は、attestation fixture 修正後も実認可・同 durable root・claim 一回・同一 WAL・両 arm の BUILD／VERIFY／BENCH／COMMIT を検査する構造です。ただし shell 起動と実 driver は別 test であり、一本の production E2E ではありません。F1019 には次の限定が適切です。

> 認可／claim 結合の再発検査を追加。実 compiler の STOCK 成立、実 checkout／patch と build の統合、Pegasus production pair は未実施。

## 総括

**新規所見: must-fix 1、should 2、nit 0。**

- **must-fix B1:** M4 の例外型変化を発行証明の KILLED に数えない。
- **should B2:** H/M18 を実引数の転送検査へ置換、または保証を静的断片検査へ限定。
- **should B3:** B-4 の launcher・proposal・closed-critic consumer を後続検査へ含める。

**NO-GO。** 本体経路は支持しますが、既知の赤が残り、変異の実効性も未実証です。

**削る候補:** M4 の不適切な独立 KILLED 計上、session 転送の逐語 pin、保存 record の PID／digest の重複比較、checkpoint bytes 比較後の重複 whiteboard assert。

**fix への指示:** validator を明示引数化し、job の共通 proposal pin と独立 K2 pin を両方更新する。attestation は正例観測だけを修正し、実認可・claim を残す。修正後に 100 件の再集計、追加 consumer、M0、H／C 群の順で検証し、production 未実施の限定を文書へ残してください。