# 判定と確認範囲

**NO-GO。新規所見は must-fix 1 件、should 2 件です。** 主な問題は変異検査の帰属と代表性です。静的読解では、claim 非所有 process を測定へ通す新経路や、stock の成功条件の緩和は確認できませんでした。

**未実走・静的読解です。** 指定資料・現物・実測ログを確認しました。ログの失敗 node 集計は **B-4 wiring 23、job contract 74、結合検査 3、合計 100** です。提示された「18／72」は全失敗 node 数とは一致しません。既知の赤は新規件数に含めません。

# R1 — M4 は台帳検査の削除だけでは偽造 session の受理にならない

**重大度: must-fix**
**位置:** `orchestrator/campaign/loop.py:143–146`、`orchestrator/tests/test_campaign.py:14285`、段 4 裁定 §3 M4。
**放置時の影響:** 実際の受理集合が広がらない変異を「発行証明の防壁を破った変異」と数え、変異台帳の KILLED の意味を誤る。
**型タグ:** [テスト代表性]

発行台帳の membership 検査を削除しても、直後の `_AUTHORIZATION_SESSIONS[session]` が残ります。同型の未発行個体は `KeyError`、foreign の `{}` は `TypeError` で止まります。この参照は `try` の外なので、負例が要求する `ExecutionGuardError` にもなりません。

従って、テストが赤になっても「偽造 session が受理されたため検出した」とは言えません。copy 系にも独立した拒否があります。

**推奨:** M4 の単純な guard 削除は登録から外すか、「発行済み個体の binding を同型の別個体にも使わせる」性質変異へ具体化してください。同じ PID・binding・claim record のまま object identity だけを失わせ、同型コピー負例を帰属先にする必要があります。例外型が違うだけの赤を、権限受理の拡大として集計しないでください。

# R2 — M18 の H 群検査は session の到達を検査していない

**重大度: should**
**位置:** `orchestrator/tests/test_p3_s4_loop.py:10701`。
**放置時の影響:** session 転送が壊れても H 群の構文検査が緑になり、転送の実効性を示す台帳が過大になる。
**型タグ:** [テスト代表性]

現検査は代入文と `**campaign_options` の存在を確認するだけです。例えば、代入後・呼出し前に `campaign_options.pop("authorization_session", None)` があっても、この検査は通ります。

結合正例には実委譲 spy があり、この見落としを補います。しかし、裁定で H/M18 に予定した「両 `run_campaign` に同じ S が届く spy」とは別物です。

**推奨:** H 群にも、両 resolved 関数を実行し、`run_campaign` だけを捕捉する検査を置いてください。campaign lock 作成前で捕捉すれば A-R1 と両立します。現検査を維持するなら、M18 の保証を「指定した代入削除の検出」に限定し、実効転送の証拠は C1 に帰属させてください。

# R3 — 初回 claim エラーの変換が C2 の期待と一致しない

**重大度: should**
**位置:** `orchestrator/campaign/loop.py:154`、`:238`、`orchestrator/tests/test_campaign.py:14454`、段 4 裁定 §3 C2。
**放置時の影響:** 拒否される入力集合は変わらないが、claim 競合の診断と変異結果の例外分類が変わる。
**型タグ:** [ドリフト]

`try` は再利用検査だけでなく、未束縛 session の初回 `_authorize_measurement` も囲みます。そのため `ClaimError` は `ExecutionGuardError` に包まれます。`__cause__` は保存され、原因は失われませんが、`claim_path`・`existing_record` 等を最上位例外から読む consumer には異なる契約になります。

S 無しの 2 回目は引き続き直接 `ClaimError` です。一方、C2 で session 経路内から再取得させる場合、裁定の「`ClaimError` で赤」は現在の変換と一致しません。

**推奨:** 初回取得の例外を従来どおり透過させるか、変換を採るなら C2 の期待を「最上位 `ExecutionGuardError`、原因が `ClaimError`」へ訂正してください。C1 と C2 を同じ例外型として集計しないこと。

# 既知の赤 — 是正方向と同型の見落とし

**静的目録:** validator を明示 keyword parameter にして直接呼ぶ修正は妥当です。`p3_b4_wiring_probe.py:884` の未解決 callable 拒否を緩めたり、session 関数を inventory から除外する修正は不適切です。単に `kwargs["pre_write_validator"](identity)` と書き換えて解析器に見えなくするより、既存の parameter 呼出しとして表現してください。新しい `_run_stock_cli_step` も生成経路の逆到達集合に含まれることを確認対象にしてください。

**job contract:** 欠落集合へ機械的に `proposal` を足す修正は不適切です。無変異の source 自体が `test_p3_s4_loop_job_contract.py:459` の旧 proposal 断片に一致していません。`:708` の変異対象、`:1460` の K2 展開検査も更新が必要です。さらに proposal 断片へ pair 展開を丸ごと含めるだけでは、`pair-argv` と重複して次の二重欠落が生じます。各 pin の責務を分け、無変異の正例を先に緑にしてください。

**attestation:** 観測代用の修正は妥当です。ただし現 fixture は **既に `probe_fn` を代用しています**。`test_p3_s4_loop.py:10749` で較正 samples をそのまま観測値へコピーすることが原因です。比較器はリスト一致ではなく、較正中央値に対して**各観測 sample**が許容幅内かを検査します。ログの `3080.935` は中央値 `2101.0` の範囲外です。

較正中央値を使う合成観測へ直し、実 `attest_and_build_receipt`／`receipt_matches_contract` を維持する方向を推奨します。これなら実認可・reservation・claim・layout・campaign lock・WAL・`pipeline.evaluate` の結合は残ります。

# 防壁・成功条件・残りの変異の評価

- `campaign_claim.py` の SHA-256 は **`2e9c09328078378e4c9475f53e06cd338183373922ff2d83e5bcf218f7fd2dbd`**。leaf の変更、DEAD 再取得、claim の削除・退避、別 root への救済はありません。
- session の台帳・未 close・PID・契約・identity・digest・use class・root・reservation・claim record・receipt・validator 検査は、測定用 `run_campaign` の layout／lock／WAL／evaluate より前です。ただし driver 全体の事前 layout や検疫 reject WAL まで claim 下に置いたとは言えません。保証は裁定 A-R4 の限定を維持すべきです。
- stock は別 context・別 checkout・stock 専用 resolver を使います。policy は dataclass の**値比較**です。成功条件の certified、非 aborted、stock variant、BUILD_START の STOCK、skip／非 STOCK の rc 1 は維持されています。
- pair の禁止組、候補 opt-in、isolation は測定前に拒否されます。stock 単独の B-5 口と、job の未設定／`0` 時の展開 argv に意味上の変更は見つかりません。fixture pair の拒否は prebuild／trap より前です。
- 結合正例は両 variant の WAL 段階、候補→stock 順、同一 S、claim 1 回・record 不変、checkpoint／whiteboard 不変を検査します。実 compiler・checkout・patch の成立を示す検査ではありません。

変異の静的見込みは次のとおりです。

| 群 | 評価 |
|---|---|
| M0 | H の exact node 集合で SURVIVED が必要。lock を作る `two_campaigns_one_claim` は除外する。 |
| M1–M3、M5–M8、M10–M11 | 対応する負例／正例あり。M2 の created_utc、M3 の同 binding 期限切れ、M6 の両 PID 比較をまとめた変異は帰属を分離できる。 |
| M9 | perf 失敗を layout 前に注入するため H 対象にできる。ただし「束縛を遅らせる」具体的編集を確定する必要がある。 |
| M12–M17 | 対応検査あり。value／emit／no-build／B-4 は後段にも拒否があり、追加の単独 guard 削除を独立 KILLED と数えない。 |
| M19–M21 | job consumer 修正後に実 body の起動数・fixture 拒否・既定 argv で判定する。既知の静的赤による KILLED は無効。 |
| C1–C3 | C1 は直接 ClaimError、C2 は R3 の分類調整が必要。C3 は no-bench でも certified になり得るため、正例の BENCH_DONE 必須 assert が意味を持つ。 |

## 総括

**新規: must-fix 1／should 2／nit 0。**

- **must-fix R1:** M4 の変異定義と拒否理由の帰属を修正。
- **should R2:** M18 を実転送 spy にするか、証明範囲を限定。
- **should R3:** 初回 ClaimError の扱いと C2 の期待を一致させる。

**NO-GO。** 既知の赤を consumer 側の契約を緩めず修正し、無変異正例を緑にした後、M0・H 群・commit 群の exact node と拒否理由を確認してください。現段階で claim 防壁や certified 受理集合の新たな破綻は見つかっていませんが、変異による立証は未完了です。