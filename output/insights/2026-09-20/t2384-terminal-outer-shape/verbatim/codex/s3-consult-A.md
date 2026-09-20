## 所見一覧

| id | 重大度 | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| A01 | nit | brief | P1 の active-attempt 閉包だけでは「production は terminal を二重に書かない」の証明にならない。pipeline の終了経路と recovery の対象選別を併記すべき。 | 提案 gate の受理集合・reason・receipt への誤変更は確認できないが、一意性の根拠が過大になる。 |
| A02 | nit | brief | P2 の M5 等価性は「gate を stage 比較より前に置いた結果」に限定されない。同じ gate が後続して必ず評価される場合も最終判定は等価。 | 現 plan の成果物は変わらないが、変異の等価理由が配置に不必要に依存する説明になる。 |

## 各所見の根拠

以下のコード位置は指定 worktree 基準。静的確認であり、pytest・変異走は実施していない。

**1. production と受理集合**

提案 helper は terminal の外枠・件数・末尾性に限定され、payload の内容や中間の非 terminal record の外枠を閉じない。D1730 の範囲に収まる。

| producer | 外枠・型・payload | 新 gate |
|---|---|---|
| commit | `pipeline.py:2538–2574`。payload に attempt、`verify_configs`、計測値・契約等。`wal.py:1313–1320` の receipt 追加も payload 内。 | 通過 |
| prebuild abort | `pipeline.py:1775–1779`。payload は reason、error、attempt。 | 通過 |
| 通常 abort | `pipeline.py:1917–1926`。payload は reason、attempt、admission receipt と追加診断等。 | 通過 |
| recovery abort | `wal.py:2437–2439, 2651–2653`。同じ外枠、dict payload。 | 単一 attempt の末尾なら通過 |

共通して `wal.py:409–430` が exact 5 key を生成し、variant／env_tag、有限数 ts、dict payload を検証する。`wal.py:1591–1593` の通常 ts は `time.time()` の float。JSON 復号後の型は提案の exact type 検査と整合する。fixture の整数 `0` も受理される。

ここでの「通過」は**新しい外枠 gate の通過**である。prebuild abort 等は既存の reason／verify 検査を満たすとは限らず、production abort 全般が `P6Unavailable` へ進むという意味ではない。

**2. P1 と A01：重複の読み**

`_wal_trigger` は `reflux_formal_consumer.py:1001–1007` で対象 stage の record 数を 1 に限定する。terminal も commit／abort を合わせた終端種別として数える読みが同型である。

- 同一 stage の重複だけを拒否すると、`commit → abort` を許してしまう。
- JSON 重複 key は `reflux_origin_artifacts.py:98–104` で拒否済み。
- attempt 混在は `reflux_result_evidence.py:1636–1637` で拒否済みなので、件数検査は同一 attempt 内の終端一意性を対象にできる。

ただし `s1-brief.md:10` が挙げる `wal.py:2355–2371` は、terminal を見たら active 集合から除く処理であり、それ自体は二重 append の禁止機構ではない。

補完する根拠は、prebuild abort が返る `pipeline.py:1786`、通常 `_abort` が返る `:1932`、verify 内の abort 結果で評価を終了する `:2436–2437`、abort 済みの commit を拒む `:2530–2531`、recovery が active attempts だけに追記する `wal.py:2627–2671`。確認した通常経路に terminal を二件生成する経路は見つからなかった。

DW-O13 の 490 件は外枠の観測を支持するが、attempt ごとの一意性の実測は **commit 16 件のみ**。plan `:169` の限定は適切。

**3. 負例13件の到達順**

共通経路は、canonical projection 解決 → FC05B → FC05A／FC05C → FC06 → verifier policy → 新 FC07 gate → 既存 attempt／outcome 判定。

`_rewrite_wal` は `test_reflux_formal_consumer.py:480–492` で source・projection・参照 hash を同期する。canonical-list 経路は `reflux_result_evidence.py:1585–1586` で外枠の再検査を受けない。FC05C の trigger と FC06 の member topology は各負例で保存される。

| 負例 | 上流通過と新 gate での停止理由 |
|---|---|
| root attempt shadow | `_rewrite_wal:474–476` が root だけ更新し、payload の不一致を残す。resolver は root 優先で通過、新 exact keys で拒否。 |
| extra root key | attempt に影響せず通過、新 exact keys で拒否。 |
| missing env_tag | attempt に影響せず通過、新 exact keys で拒否。 |
| missing ts | 同上。 |
| missing variant | 同上。 |
| ts-bool | canonical JSON と attempt 検査を通過、新 ts 型検査で拒否。 |
| ts-str | 同上。 |
| variant-int | 上流は terminal variant の型を検査せず、新 variant 型検査で拒否。 |
| env-tag-none | 同様に新 env_tag 型検査で拒否。 |
| payload-only stage | payload attempt を保存し、trigger にはならない。新 exact keys で拒否。 |
| duplicate abort | 全 record が同一 attempt。新 terminal count で拒否。 |
| commit before abort | 同一 attempt、trigger 不変。新 terminal count で拒否。 |
| nonterminal after abort | 末尾にも正しい payload attempt が残る。件数は 1、末尾性で拒否。 |

手前で止まってしまう負例は見つからなかった。ただし payload-only stage と nonterminal-after-abort は既存 stage 判定でも FC07 になる。**reason の一致だけでは新 gate の実効性を証明しない**が、plan は M02 と等価 M09 を区別しており、この点を誤認していない。

**4. P2・A02：M5 と合成変異**

`_wal_field` は `reflux_formal_consumer.py:1095–1099` で、root に key が存在すれば値が `None` でも root を返す。exact keys 通過後は root stage が必ず存在するため、`terminal.get("stage")` と同値。反例はない。

`s1-brief.md:11` の配置に関する因果説明は強すぎる。gate を stage 比較の後に置いても、root stage がない record は最後に同じ FC07 で拒否される。今回の前置き配置自体に問題はない。

M02 は次の順で KILLED になると予測できる。

1. payload-only stage は resolver・FC05C・FC06 を通過。
2. gate 無効化により外枠検査を通過。
3. payload attempt は一致。
4. M5 が payload の abort stage を読む。
5. 保存した reason／verify が既存検査を通過し、`P6Unavailable` に至る。
6. FC07 rejection を要求する test が失敗する。

**5. P3：fallback を残す判断**

brief 追補 `:23` と plan `:171` が正しい。死ぬのは stage の payload fallback であり、attempt／verify_configs／reason／verify は payload から読む必要がある。

後者を gate 後で同じ欠落時挙動の payload 直読みに置き換えても、受理集合は変わらない。ただし D1730 は他の判定式を変えないと指定しているため、現 plan の維持方針が適合する。stage まで payload 直読みにすると、通常の production record を拒否するため同値ではない。

**6. P4：型述語の到達性**

| 述語 | 判定 |
|---|---|
| payload が dict | 非 dict・root attempt 無しなら resolver で拒否。root attempt 有りなら exact keys で拒否。型述語を単独除去する M07 は等価。 |
| ts が有限 | 非有限値は `strict_json_loads` の定数拒否・値検証・canonical 検査で拒否。M08 は等価。 |
| variant が str | canonical-list 経路で整数等が到達可能。M10 は非等価。 |
| env_tag が str | 同経路で `None` 等が到達可能。M11 は非等価。 |

「述語を実行できない」ではなく、**その述語だけが拒否理由になる不正入力を到達させられない**という意味で等価登録するのが正確。M09 の末尾性除去も既存 outcome 別 stage 判定が残るため等価である。

**7. fixture と他 consumer**

`reflux_origin_fixture_builder.py:396–464` は exact 5 key、str／str／整数 ts／dict payload、trigger 一件＋abort 一件なので新 gate を通る。

指定4 test file を stage literal、terminal 定数、ordered WAL、fixture builder 参照で検索した。

- `test_p3_autonomous_workload_trial.py:10728–10745` は fixture の source bytes／records を保存して参照先を移す。terminal 外枠は変えない。
- `test_trial_registry.py:1218–1227` の独自 commit は exact 5 key、有限 float、dict payload。`:1237–1245` で receipt 付き書込みへ渡すため、外枠の不適合はない。
- `test_reflux_origin_client.py:82` は fixture builder を利用。独自 WAL terminal 外枠の構築は見つからない。
- `test_reflux_originless_compatibility.py:13` は P3 helper を間接利用。独自 WAL terminal 外枠の構築は見つからない。

新 gate によるこれらの回帰要因は静的には見つからなかった。実走結果は親の12 file 焦点走で確定する必要がある。

## 総括

must-fix **0件**、should **0件**、nit **2件**。
最重要の確認点は terminal 一意性であり、通常 producer／recovery 経路に過剰拒否となる反例は見つからなかった。
負例13件の到達性、M5 単体等価・合成 KILLED、型述語の等価分類は plan を支持する。
ファイル変更・pytest・変異走は未実施。
