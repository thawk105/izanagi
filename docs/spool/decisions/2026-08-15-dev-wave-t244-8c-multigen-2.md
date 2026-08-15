---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t244-8c-multigen
seq: 2
---

## {{D:multigeneration-whitelist}}. 8c の世代間還流は key 集合を保ったまま更新経路を断ち、診断値だけを supervisor が機械射影して運ぶ

**背景:** 2026-08-13 のユーザー裁定は「世代間で運んでよいものは descriptor + abstract whiteboard +
critic 二層射影 (勝ち筋の値は落とし診断数値は保持、recommend 除外) に限る」と閉じた列挙をし、
許可の根拠を「人間ループが世代間で運んでいたものと同じだから」に置いた。D114 の承認上限 1 を 2 へ上げる。

**決定 (1): `current_perf` / `leading_indicators` / `baseline` の key と shape を全世代で維持し、
世代を跨ぐ更新経路だけを断つ。** `_role_metric_payloads` は workload あたり 1 回だけ、初期 metrics
定数で呼び、結果を deep copy で凍結する。全世代の payload はその凍結 snapshot から組み立てる。
段 3 のレンズ A は閉列挙を優先して 3 field の削除を支持し、レンズ B は削除が世代 1 の payload bytes を
変えて D121 P8 と規律 2 を破ると判定した。**両方 real であり、本決定は第三の形でどちらも満たす** —
世代 1 の payload bytes は base と byte 単位で一致し (planner 1146 bytes / coder 1729 bytes、SHA 一致を実測)、
世代 N の測定値が世代 N+1 へ渡る非白名単経路は消える。

**決定 (2): critic の自由文は第二層へ 1 byte も通さない。診断値は supervisor が source metrics から
canonical に再構築する。** critic に metric を選ばせない。運ぶのは (i) 固定順の診断 4 値
(`abort_rate` / `latency_ns` / `llc_miss_rate` / `ipc`)、(ii) `uncertainty` の非空 bool、
(iii) `reverse_recommended` の bool、(iv) source generation 番号だけである。
`recommend` と `avoid` は完全除外する (`avoid` は負の recommendation なので同格に扱う)。
`throughput_ops_sec` は射影対象から構造的に外す。段 3 のレンズ A が指摘したとおり、
critic に metric の有無を選ばせると 4 bit + 1 bit の隠しチャネルが残るため、選択権を渡さない。
自然文への正規表現適用は採らない (言い換えと数値表現で漏れる)。

**決定 (3): validator の期待値は payload と別経路で導出する。** 段 6 の敵対レビュー 2 本が独立に
「caller が payload と期待値へ同じ実体を渡すため、両方書き換えれば通る」= **恒真** と判定した。
凍結 snapshot の deep copy を期待値として渡し、payload 側とは object を共有しない。
whiteboard origin も payload と別に authoritative state から再構成する。
`None` の hardcode は採らない — 既存 pre-wave テストが目印値の疎通を exact 比較で証明しており
(F69 が推奨する形)、hardcode するとその検出力が消えるためである。

**決定 (4): validator 通過は sealed receipt として durable に残し、completeness が独立再検証する。**
receipt は canonical payload SHA-256、allowlist digest、固定 literal・nested key・metric nullness・
whiteboard origin・critic projection の安全な射影とその SHA、seal を封印する。
completeness は production validator を呼ばず独自定数で再計算する。
これが無いと validator 呼出しを 1 行消しても journal / report の自己整合だけで通る。

**決定 (5): 正直な計数は「数えて出す」だけとし、停止 gate を作らない。**
`role_query_count` は `provider.invoke` の呼出し回数と定義する (外部 query 数と混同しない)。
auditor の pre-audit skip は呼んでいないので数えない。duplicate record の bench は current-attempt 0。
bench は pipeline の `bench_wall_s` を唯一の値源とする。注入 delegate の走行は accounting の
権威から除外する。**上限で止める gate・警告 threshold・性能早期停止は 1 つも足さない** —
予算値が未確定なので、止める値を機械側が決めると未裁定の受理集合変更になる。

**決定 (6): `SCHEMA_VERSION` (role payload 共用) は bump せず、`REPORT_SCHEMA_VERSION` だけ上げる。**
D217 が schema bump を却下した理由 (全 role の payload bytes と hash が変わり旧 artifact が
verifier と台帳の受理集合から外れる) がそのまま効く。report schema は role payload に入らない。

**保証の限界 (これ以上を主張しない):**
- **「人間ループと同一」とは名乗らない。** 運ぶのは人間ループが運んだものの**部分集合**である。
- `reverse_recommended` の 1 bit と診断 4 値は**明示的に許可された情報**であり、ゼロ漏洩は名乗らない。
- planner→coder の 3 field は構造上維持されるが**意味的な非干渉ではない**。
  direction 3 値 × magnitude 3 値の 9 記号で順位を符号化できる。保証は「3 field 以外を渡さない」に限る。
- `run_trial(drive=/providers=/preview=)` の注入 seam と `drive_iteration()` の直接反復は
  D114 のとおり**保証対象外**のままである。本決定は report 上で区別し、accounting の権威から
  除外するだけで、seam を閉じてはいない。
- P9 の一般閉包は行っていない。8c の payload validator が whiteboard entry の exact int iteration・
  範囲・件数・狭義単調増加を検査するのは **8c 経路だけ**で、`state_from_dict` の iteration 整合、
  `project_whiteboard` の in-memory 値域、`layer3_report` の独立 reader は未閉包である。
- s8c C11 は `machine_checkable: false` のまま `EVIDENCE_UNDEFINED` = **未充足**であり、
  cap 引き上げの権威根拠には使えない。sample-plan / cap-lift artifact は作っていない。

**却下した選択肢:**
- 3 field の削除 — 世代 1 の payload bytes を変え、D121 P8 と規律 2 に触れる。
- validator で metric 値を `None` に hardcode — pre-wave の目印テストの検出力を潰す (F69 型)。
- critic の `attribution` を構造化 metric リストへ変更 — critic role の出力契約そのものの変更で、
  role file / effective prompt の SHA と既存 fixture へ波及する。第二層へ自由文を通さない形で
  同じ安全性が得られるため不要。
- 自然文への禁止トークン正規表現 — 言い換え・単位変更・序数表現で漏れる。

## {{D:intermediate-critic-position}}. 中間世代の critic は当該世代の campaign admission 後に置き、最終世代は D217 の形を維持する

**背景:** D217 は裁定 U-8 (2026-08-05 批准、「critic を Layer 3 admission・ledger seal・
proof 書き込みの後へ移す」) のうち **8c に実在する唯一の anchor である Layer 3 admission への
後置だけ**を実装し、「本決定は U-8 を完了させない」と明記した。その後置理由は
「承認上限 1 世代では critic の出力が制御流へ還らない」ことだった。

**実測 (本 wave):** `test_multi_generation_deferred_critic_fails_closed` が
「cap=2 の 2 世代運転は `RuntimeError` (`journal role attempts`) で止まる」を**既にテストで固定
していた**。すなわち承認上限だけを上げても report は 1 件も発行できず、critic の実行位置を
決めない限り多世代開放は 1 件も実行できない。D217 自身がこの帰結を予告している。

**決定: 次世代が存在する場合にのみ、世代 N の critic を当該世代の campaign admission
(`require_admitted_campaign` と再計算 digest の一致) の後、世代 N+1 の planner の前に走らせる。
最終世代の critic は従来どおり cell の Layer 3 admission 後とする。**

- `generations=1` では「次世代」が存在しないため全 critic が最終世代扱いとなり、
  **D217 の批准済み挙動は 1 bit も変わらない。** 新経路は `generations>=2` でのみ発火する。
- critic は **at-most-once** を機械強制する。pending に exact state を持たせ、fallible 処理の前に
  attempt を確定し、最終 drain は既存 role event を持つ generation を再 invoke しない。
- 再計算 digest の exact 一致検査は**中間世代の新経路にだけ**適用する。最終世代は
  admitted campaign から identity projection つきで digest を再構築する base の形をそのまま使う。
  **この identity projection が非干渉の関所**であり、生の variant 名を匿名ラベルへ射影している。

**理由:** U-8 が守る性質は「結果が commit される前に critic が metrics を見ない」ことで、
campaign WAL の commit と `require_admitted_campaign` が世代ごとにそれを与える。
cell の Layer 3 admission は複数世代の集約段であって、個々の世代の metrics の commit ではない。
U-8 が anchor に挙げた ledger seal は D201 / D211 と 2026-08-13 裁定により**作らないと確定済み**で、
永久に存在しない。cell 粒度は D217 自身の実装選択であって批准された粒度ではない。

**名乗りの上限:** **U-8 の完了は名乗らない。** ledger seal と proof issuance への後置は依然未達で、
そもそも作らないと裁定済みである。本決定が主張するのは「中間世代 critic を当該世代の
campaign admission 後に限定して置いた」までである。

**ユーザー裁定へ返す:** 2026-08-13 裁定は D217 / U-8 を「この裁定が動かす既存の記録」に
挙げていない。本決定は**未見の事実に対する親の判断**であり、承認済み運転 (1 世代) の挙動は
不変だが、多世代を実際に開ける前にユーザーの追認を求める。

**却下した選択肢:**
- 世代ごとの子 Layer 3 report / admission の新設 — identity・report schema・admission 単位を
  広げる別タスク級の変更である。
- critic 射影を落とす — ユーザー裁定の scope (d) を未達にする。
- 独立した `generation-accounting` event を zero-work wall stop でも発行する —
  wave 前の terminal event 契約 (内側 event はちょうど 1 件) を破る。作業ゼロなら数える
  query もベンチ時間も無いため、既存の terminal event に欄を載せる形を採った。
