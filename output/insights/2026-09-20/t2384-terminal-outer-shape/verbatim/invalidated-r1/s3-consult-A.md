## 所見一覧

| id | 重要度 | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| A1 | nit | brief | P3 の「payload fallback が死ぬ」は逆。attempt・verify 等では root 読取りが死に、payload fallback が必要になる。plan §6 は訂正済み。 | 現 plan は既存式を保存するため、受理集合・reason・receipt への影響なし。 |
| A2 | nit | brief | P4 の「非 dict payload は常に FC07 以前で落ちる」は誤り。正しい root attempt があれば resolver を通り、新 gate の exact keys で落ちる。 | M7 の等価性という結論は維持され、成果物への影響なし。等価性の説明だけが不正確。 |
| A3 | nit | brief | P1 の active-attempt 閉包は既存 terminal を認識する処理であり、それ自体が重複追記を禁止する機構ではない。producer の分岐・return と recovery の対象選択を併せて根拠にすべき。 | 確認した production 経路に二重 terminal は見つからず、現 gate による追加の誤棄却は示せない。 |

## 各所見の根拠

**1. 受理集合と production の適合性**

plan の変更は既存 FC07 の前に条件を追加する積集合であり、受理集合を広げない。payload の key 集合、variant・env_tag の値の一致、他 record の外枠まで閉じていない点も D1730 の範囲に収まる。

[wal.py:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2384-terminal-outer-shape/orchestrator/campaign/wal.py:409) の `_record_to_line` は、外枠を正確に `{variant, stage, env_tag, ts, payload}` として生成する。variant・env_tag は str、payload は dict、ts は bool 以外の有限数に制限される。JSON 復号後は exact str / dict になるため、producer 側の `isinstance` と plan の `type(...) is ...` の差は反例にならない。`wal.py:1592` の既定 ts は `time.time()` の float で、gate を通る。

| production 経路 | payload の形 | 新 gate |
|---|---|---|
| commit：`pipeline.py:2537–2580` | attempt、verify_configs、admission receipt、fitness 等。WAL 側で commit receipt も追加 | 通る。payload key 集合を閉じていない |
| prebuild abort：`pipeline.py:1775–1779` | reason、error、attempt | 通る |
| 通常 abort：`pipeline.py:1917–1926` | reason、attempt、admission receipt、extra、任意の workload | 通る |
| recovery abort：`wal.py:2437–2439` | recovery 用 dict、float ts | 通る |

ここでの「通る」は**新しい外枠 gate**についてである。prebuild abort 等が既存の reason / verify 検査まで通るという意味ではない。plan §6.7 はこの区別を正しく保っている。

**2. P1：重複の読みと terminal 一意性**

D1665 は trigger stage record の件数を数えている。同型適用として、commit / abort を合わせて terminal record が 1 件と読むことは妥当。同一 stage だけの重複禁止では `[commit, abort]` を残す。JSON 重複 key は `reflux_origin_artifacts.py:98–104` が先に拒否するため、今回の新 gate の対象にならない。

[wal.py:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2384-terminal-outer-shape/orchestrator/campaign/wal.py:2355) は terminal のある attempt を active 集合から除く。recovery は `2560–2586` で残った active attempt を選び、`2651–2671` で prospective topology を検証して追記する。したがって既に閉じた attempt への recovery 追加はこの経路では起きない。

pipeline の `_abort` は 1 件 emit して結果を返す（`1912–1932`）。呼出し側は直接 return、または返された abort 結果を伝播する（`2185–2188`、`2304–2321`、`2435–2437`）。fanout でも local abort 後は remote outcome の投影前に return する。commit は aborted result を拒否する（`2529–2531`）。確認した経路に、同じ attempt へ terminal を 2 件書く分岐はなかった。

A3 は [brief:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/s1-brief.md:10) の根拠の省略についてであり、P1 の gate を変更する理由ではない。resolver が attempt 混在を拒否するため、別 attempt の正常 terminal を数えて誤棄却する経路もない。

**3. 負例 13 件の到達性**

共通の判定順は、resolver → FC05B range 検査 → FC05C → FC06 → 新 FC07 gate → 既存 FC07 attempt・outcome 検査（`reflux_formal_consumer.py:1433–1450`）。

[_rewrite_wal:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2384-terminal-outer-shape/orchestrator/tests/test_reflux_formal_consumer.py:468) は source bytes・range・projection・hash を同期する。root attempt がある場合は root を更新して `continue` するため、root-shadow 負例の payload の異なる attempt は保存される。

| 負例 | 上流を通る理由／新 gate の拒否点 |
|---|---|
| root attempt shadow | resolver は正しい root attempt を読む。payload の別値は混在判定に使われず、exact keys で拒否 |
| extra root key | attempt 不変。exact keys で拒否 |
| missing env_tag | resolver は参照しない。exact keys で拒否 |
| missing ts | 同上 |
| missing variant | 同上 |
| ts-bool | canonical JSON に載り、attempt 不変。ts 型で拒否 |
| ts-str | 同上 |
| variant-int | resolver は terminal variant の型を検査しない。str 型で拒否 |
| env_tag-null | 同上。str 型で拒否 |
| payload-only stage | attempt は payload に残る。root stage 欠落で拒否 |
| abort-abort | 同一 attempt、trigger は 1 件。terminal 件数で拒否 |
| commit-abort | 同上。途中 commit の payload は resolver 条件を満たし、件数で拒否 |
| terminal の後に build_start | 追加末尾にも同じ attempt がある。末尾 stage 条件で拒否 |

いずれも trigger・member・topology を変えず、FC05C / FC06 を通る。projection 内の record 追加は、別 projection 間の range 重複ではない。既存 FC07 attempt 式も、仮に先に評価しても通る。**上流で止まって新 gate を検査できない負例は見つからなかった。**

ただし payload-only stage と terminal-before-last は旧 stage 判定でも FC07 になる。前者を gate 無効化単体の kill に数えず、合成変異に帰属させた plan は正しい。後者も gate 固有の有効性証明にはならないが、仕様例としては有効。

**4. P2：M5 の等価性**

`reflux_formal_consumer.py:1095–1099` より、root に stage があれば `_wal_field` は必ず root 値を返す。exact gate を通りながら `terminal.get("stage")` と異なる値を返す record は存在しない。

これは gate が stage 比較の**後**でも、最終的な受理集合・reason・receipt について等価。missing root stage を M5 が通しても、後続 gate が同じ FC07 で拒否するからである。前置きは説明を単純にするが、等価性の必要条件ではない。

合成変異では、gate 無効化 → payload の正しい attempt → M5 が payload stage を取得 → 保存された reason / verify が既存検査を通過 → P6Unavailable と receipt 発行、となる。FC07 と receipt 参照なしを期待する `_assert_reason`（`test_reflux_formal_consumer.py:688–697`）がこれを検出する。

**5. A1／P3：fallback と置換の範囲**

[brief:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/s1-brief.md:12) は説明が逆で、[plan:173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/codex/s2-plan.md:173) の訂正が正しい。

gate 後は attempt・verify_configs・reason・verify が root に存在できないため、それらの `_wal_field` 呼出しは payload を読む。これらだけを同等の payload `.get` に置換しても、gate 通過後の受理集合は変わらない。ただし D1730 の「他の判定式は変えない」に従い、保存する案が適切。

stage まで payload 直読みに置換すれば、payload に stage のない正常 production terminal を拒否する。field を区別せず「fallback は死んだ」と一般化してはならない。

**6. A2／P4：型検査の到達性**

| 述語 | 到達性と変異評価 |
|---|---|
| payload が exact dict | exact 外枠で非 dict なら attempt が取れず resolver の FC05B。root attempt を足せば resolver は通るが exact keys が拒否。型述語だけの無効化 M7 は end-to-end 等価 |
| ts の有限性 | strict JSON の検証・canonicalization が先に拒否。M8 は end-to-end 等価 |
| variant が str | canonical-list 経路で int 等が到達する。非等価であり、新負例が必要 |
| env_tag が str | 同様に null 等が到達する。非等価であり、新負例が必要 |

したがって [brief:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/s1-brief.md:13) の理由は修正対象だが、plan の M7 / M8 等価登録は妥当。「等価」は resolver を含む正式評価経路についてであり、helper を任意の Python 値で直接呼ぶ場合まで含めない。

**7. fixture と他 consumer**

`reflux_origin_fixture_builder.py:409–463` は exact 外枠、str の variant / env_tag、int `ts=0`、dict payload、末尾 abort 1 件なので通る。

指定された 4 test file を grep し、WAL terminal の独自構築も確認した。

- `test_p3_autonomous_workload_trial.py:10728–10745` は fixture の source bytes と records を保存し、参照先を移す。外枠を崩さない。
- `test_reflux_originless_compatibility.py:133–134` は上記 P3 helper を利用する。
- `test_reflux_origin_client.py:82` は fixture repository を利用する。独自の Origin terminal / receipt 構築は WAL terminal とは別物。
- `test_trial_registry.py:1218–1227` の独自 commit は exact 外枠、float ts、dict payload。`1237–1245` で receipt helper を通す。複数 generation の記録は attempt が別であり、同一 attempt の terminal 重複ではない。

新 gate に落ちる正常 fixture record は見つからなかった。これは静的確認であり、回帰テスト成功の報告ではない。

## 総括

must-fix **0 件**、should **0 件**、nit **3 件**。
最重要の訂正は brief P3：payload fallback は attempt・verify 等の読取りに引き続き必要。plan は訂正済み。
新 gate による production 外枠の誤棄却、負例の上流遮断、指定 fixture の不適合は見つからなかった。
M5・M7・M8 の等価性と、gate 無効化＋M5 の kill 予測は静的に支持する。
ファイル変更・pytest・変異走は未実施。実際の kill 集合と回帰結果は親の実測待ち。
