## 負例の到達性

以下、`E`＝`orchestrator/campaign/reflux_result_evidence.py`、`L`＝同 `loop.py`、`U`＝`orchestrator/tests/test_reflux_result_evidence.py`、`I`＝同 `test_reflux_campaign_issuer.py`。brief・plan・逐語資料は指定された wave directory 内を指す。全射影ファイルは読めた。実走はしていない。

**refuted：plan の型負例が前段拒否で恒真になる、という懸念。**

| 負例 | 到達経路と判定 |
|---|---|
| official subclass | `_issue_producer_record` は capability の型確認後、producer を直呼びする（U:407、414）。有効 context なら E:1209 を通り、E:1213 に届く。loop の検査は通らない。 |
| exploration subclass | 同上。有効な exact 探索 layout で先に WAL を作り、object だけ置換する設計なので、subclass の `ensure()` による別拒否を混ぜない（plan:45、56）。 |
| duck object | 同上。`root`・`wal_file` の属性を読む前に E:1213 が拒否する（plan:65、E:1213）。 |
| `str`／`Path`／`None` | 同上。属性不足による別エラーより前に E:1213 に届く（plan:66）。 |
| projection 直呼びの上記負例 | E:534 → E:447。context・capability・root 検査も、WAL reader もこの gate より前には無い。 |

**refuted：root 外負例が必ず手前で拒否される、という懸念。** plan は producer 直呼びを指定しており、L:303 の包含拒否を避けている。E:1220 の capability、E:1245 の receipt 等を既存の有効 helper で満たし、**evidence root 自体も明示的に作成**すれば、E:1101・1102 の directory open を通って E:1110 に届く（plan:48、67）。`_producer_context` 自体は directory を作らないため、`context = _producer_context(...)` だけでは不十分である（U:269、291）。

**unverified／nit：gate を緩めた後の WAL 内部。** 射影には WAL 実装が含まれない。E:452 の呼出しと、その後の `wal_file` 読取りは確認できるが、plan:46・157–158 の「WAL API に型拒否はない」は、この射影だけでは独立検証できない。M1/M2 の成立確認には `ordered_attempt_frames` とその内部読取り経路の追加確認が必要である。

## 変異の単一理由性

述語だけを変更し、plan:19 の共通エラー文言は保持する前提で判定する。

| 候補 | 静的に予想される赤の test 関数 | 判定 |
|---|---|---|
| M1：内側 `isinstance` | `test_ordered_wal_projection_refuses_layout_subclasses` の両型 | **unverified**。外側 gate を通らない設計は適切。WAL 内部で代替拒否されないことの確認が残る。 |
| M2：内側 `hasattr` | `test_ordered_wal_projection_refuses_duck_layout` の両形、および上記 subclass の両型 | **unverified**。複数 node でも、すべて「同じ型 gate の緩和で拒否消失」なら単一理由性に反しない。WAL 内部確認が残る。 |
| M3：内側を旧 exact 型へ | `test_campaign_producer_issues_real_wal_projection_and_resolves_interval[exploration]`、`test_real_run_campaign_exploration_issues_rejected_record` | **refuted**：射影内に重複拒否による恒真化は見当たらない。E:1213 を通過後、E:1285 → E:447 で過剰拒否する。 |
| M4：外側を旧 exact 型へ | 上記探索正例二つに加え、`test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes` | **real／nit**：plan:160 の観測集合には root 外負例が漏れている。 |

M4 の追加 node は、包含エラーを期待する plan:67 に対して E:1213 の型エラーが先に出るため赤になる。これは「発行拒否が消えた」証拠ではなく、**拒否地点が前に移った**証拠である。事前登録では追加 node と理由を明記し、探索正例による過剰拒否の検出と区別する必要がある。

登録しない候補についても、次を区別する。

- **real：外側 gate だけの緩和は、型負例では観測 node 0 件になる候補。** 有効な他入力なら E:447 が同じ型エラーを返すため、producer の subclass／duck 負例は赤にならない。brief:15 の単独 kill 主張を plan:166 が訂正した判断は妥当。
- **real／nit：root 包含 gate 除去は、重複拒否があっても必ず SURVIVED になるわけではない。** E:1110 を除去すると E:1173 の別文言で拒否され、plan:67 の厳密な `match` は赤になる。ただし受理集合は広がらない。plan:168 の登録除外は妥当であり、この赤を実効 gate の kill と数えてはいけない。
- **refuted：複数 node が赤になること自体が複数理由性、という解釈。** 問題は代替拒否や文言差による赤の混入である。前 wave の三変異除外も、後段条件が前段で保証済みだったことが理由である（insight:72–74、109–111、DW-M01:3–5）。

## 正例の到達性 (単体・統合)

**refuted：探索 root の process 内 pin が plan の正例と衝突する、という懸念。** 単体は非空の `os.fspath(evidence_root)`、統合は非空の `output_root` を渡す（plan:88、I:427）。`_resolve_exploration_output_root` は非空引数を layout.py:378–379 で即座に返し、環境変数と pin の検査に入らない。

**refuted：namespace marker を事前に別途作る必要がある、という懸念。** `ensure()` が worktree-container 検査後、namespace marker の作成・既存 bytes 照合を行う（layout.py:578、582、495、513、529）。新規で通常の tmp directory なら設計上成立する。

**unverified／nit：実 runner の pytest tmp 配置。** plan:101 の「worktree 外へ置く」は正しいが、実配置は未確認。既存先例は `tempfile.mkdtemp` を使い（test_campaign.py:1059、9828）、新 test の `tmp_path` 配置まで証明しない。実装後、resolved tmp path が禁止 container 外であることを確認する必要がある。

**refuted：統合で official と同じ root 束縛・record 導出が成立しない、という懸念。**

1. `_drive_required_campaign` が root を作り、一 genome の `_drive_campaign` に渡す（I:529、415）。L:258–279 の context 検査条件を満たせる。
2. L:452 が探索 constructor を選び、L:527 の事前検査と L:542 の materialization に同じ constructor・base を使う。
3. physical root は `<output>/exploration/campaigns/<cid>`（layout.py:594–596）。`context.evidence_root=<output>` なら L:303 と E:1110 の双方を満たす。
4. `expected_record_path` は fixture record の origin・batch・ordinal から導出される（I:310、E:963–967）。layout namespace に依存しない。producer は E:1383 で再導出結果と照合する。
5. physical campaign identity は L:833、origin capability の campaign id は L:326・341 から別々に渡される。探索化のために両者を同一化する変更は不要。

この統合正例に Q2〜Q4 の機構追加は不要。33 本の実行、台帳封印、formal completion までの成立は **scope 外**である（D2017-D2018:45–52）。

## 実装が効く全層

**refuted：plan が射影内の型 gate を取り残している、という懸念。**

経路は次のとおり。

`L:828 → L:335 → E:1213 → E:1285 → E:447`

続いて、

`E:1302 → produce_ordered_wal_projection → E:534 → E:447`

loop wrapper に layout の exact-type gate は無い。plan:10・12 は外側 E:1213 と、二度通る内側 E:447 の双方を変更対象にしている。`_context_roots` の型注釈変更も含まれる（plan:11）。

**unverified：WAL 内部まで含めた無条件の全層保証。** E:452 より先の WAL 実装は未射影であり、そこまで「取り残し無し」と断定できない。これは新しい gate を追加する理由ではなく、既存経路の確認事項である。

## 親の実測値の射程

**real／nit：brief の probe は `run_campaign` の統合到達性を証明しない。** helper は WAL 五 frame を直接記録し（U:335–365）、producer を直呼びする（U:414）。loop の context 検査、authorization の事前 root 束縛、実 layout 選択、評価結果からの発行呼出しを通らない。

また、現在の E:1213 は WAL 読取りより先に拒否する。したがって「探索が WAL 五 frame まで通る」は、helper による作成・別途読取りの確認と、producer 内で WAL を消費できた確認を分けて記載すべきである（brief:8、E:1213、1285）。

追加確認は plan:112 の統合 test で足りる。ただし、実 verifier の rejected 結果、探索 layout、導出 record、三参照の解決まで確認し、**skip を成功扱いしない**こと。既存 compiler helper は依存ツール不在時に skip する（I:100–104）。probe 自体の実行資料は射影に無いため、実測値は親の報告として扱う。

## scope の逸脱

**refuted：指定された scope 外編集の混入。** plan:174–180 は duration 台帳、p3 trial、formal consumer、別 module の exact gate、Q2〜Q4 を明示的に除外する。production 一 file・test 二 file の変更は D2044-item2:5–6 に収まる。

**refuted：探索化しても official と出力 bytes が同一、という主張。** plan:182 は physical root に応じた ref path の差を明記しており適切。brief:6 の「bytes 不変」は、既存入力に対する生成規則・schema の不変として読む必要がある。

## 総括

**must-fix：0 件。nit：変異観測集合・拒否理由の整理、未射影 WAL 内部と実 tmp 配置の確認、親 probe の射程の明確化。** 成果物の受理集合・値・参照を誤って変える production 設計欠陥は、射影内では確認できなかった。

pytest・変異・build は未実行であり、M1/M2 の単一理由性と統合成功は未検証である。

**plan の全面作り直しは不要だが、M4 の追加観測 node と検証範囲を局所訂正してから事前登録へ進むべきである。**