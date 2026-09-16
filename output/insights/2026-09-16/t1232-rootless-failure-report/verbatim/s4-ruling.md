# 段 4 裁定 — [T-1232] failure-only build report の root 無し独立検証

基準 commit: d97c423bdd14e0b416cb4f585d350e6c2b251287。
入力: 親 brief (`brief.md`)、段 2 plan (`artifacts/.../s2-plan.md`)、
段 3 レンズ A (`s3-lensA.md`)、レンズ B (`s3-lensB.md`)。
`C` = `orchestrator/campaign/autonomous_trial_completeness.py`、
`P` = `orchestrator/campaign/p3_autonomous_workload_trial.py`、
`T` = `orchestrator/tests/test_autonomous_trial_completeness.py`。

## 1. 中心の択一に対する裁定

両レンズと plan が同じ択一を親へ返した。**「非 certifying の診断検証」という新しい契約を認めて進めるか、
従来の成功集合維持を必須として案を戻すか。**

**裁定: 前者を採る。** 理由は 3 つ。

1. 依頼は「failure-only の build report を root 引数なしで**独立検証できるようにする**」である。
   対象 report は現行では root の有無にかかわらず受理されないので、**受理を 1 つも増やさない案は
   依頼を 1 mm も満たさない。** 成功集合が増えること自体は、依頼の内容そのものである。
2. 依頼が置いた歯止めは「**束縛検査の一律撤去**には広げないこと」である。閉じた厳密述語・明示 opt-in・
   非 certifying 署名・既定経路の無改変を満たす経路は、一律撤去ではない。
3. certifying 受入 (`assert_trial_registry_acceptance`) は不変であり、レンズ A が bypass の成立を
   3 方向から検査して反証した (`trial_registry.py:6264` / `:6290` は chain と cross-binding を直接呼ぶ)。

**ただしレンズ A の条件を全面的に容れる。** opt-in であることと `certifying:false` であることを、
「受理集合不変」の証拠に使ってはならない。**成功集合が増えることを親が明示的に認めた変更として
記録する** (worklog・insight・receipt の 3 箇所)。「path identity だけ省略した成功」という説明は禁じる。

## 2. 親 brief の訂正 (親自身が現物で裏取り済み)

| brief の記述 | 裁定 | 現物の根拠 |
|---|---|---|
| (P2)「root 省略で失われるのは path identity 束縛 (a) だけ」 | **refuted。撤回する。** | identity を持つ失敗 cell は root 有りでも拒否される。campaign dir 不在なら `C:4255`、dir はあるが Layer-3 不在なら `C:4374`〜`:4379` が `cross-binding-build-population` で無条件に落とす |
| 実測 3 が挙げた producer テスト (`test_p3_autonomous_workload_trial.py:8800`) | **refuted。正例にならない。** | `:8806`〜`:8837` が completeness・digest chain・`layer3_report.render` (admitted を返す fake)・`assert_campaign_layer3_chain` を monkeypatch で無効化している |
| 実測 3「残る穴は partial cell 経路だけ」 | **refuted。狭すぎる。** | 正常 return 後の admission 失敗 (role-invalid `P:4246`〜`:4252`、cell 内 wall-budget `P:4117`〜`:4133`) も failure-only report を作る |
| scope「編集面はこの 2 file だけ」 | **訂正。3 file。** | `orchestrator/tests/acceptance_duration_ledger.json` を含む |
| 実測 4 の (a)(b)(c) 分解 | **chain の failure 分岐についてだけ real。** standalone 全体の説明としては誤り | `_path_identity` (`C:525`) は root に依存せず、(b)(c) は宣言 root に対して実行される。しかし cross-binding が別要件で先に落とす |

**T-1232 の不整合は依頼文より広い。** producer は publish 前に `verify_s8c_cross_binding` を
呼ばない (`P` 内の呼び出し 0 件、受入側 `trial_registry.py` だけが 2 箇所で呼ぶ)。
したがって **producer が publish できて standalone verifier が原理的に受理できない report が存在する。**
これが本 wave の直す対象である。

## 3. 段 3 所見の裁定

### レンズ A

| 所見 | 裁定 |
|---|---|
| must-fix 1: 新 opt-in の成功集合は広がる。「path identity だけ省略」の契約では採用できない | **real / 採用。** 上記 1 と 2 のとおり契約を変更する |
| real だが scope 外: `campaign_id` が絶対 path なら `output_root/"campaigns"/campaign_id` が置換され、`campaigns/<単一 ID>` 配下という参照保証は成立しない | **real / scope 外。** 既存 chain の性質であり、本 wave で gate を新設しない (依頼の明示 scope 外)。**ただし receipt と docs で「内部 path 整合」を実際より強く書くことを禁じる** |
| 反証 5 件 (admitted/混在/no-build 流入、persisted Layer-3、registry bypass、厳密 key の恒真、既存 2 免除の暗黙拡大) | **反証を採用。** |
| nit: 負例の発火地点を入口拒否と対象検査到達に分ける | **採用。** 段 5 の契約へ入れる |

### レンズ B

| 所見 | 裁定 |
|---|---|
| must-fix 1: plan §4 の helper 流用 (`C:4279`〜`:4314`) が対象 producer の値域と両立しない | **real / 採用。plan の該当設計を却下する。** 親が裏取り: `_cross_binding_role_events` (`C:3436`) は role-attempt 0 件を `_fail` で落とす。role-attempt があっても `C:4282`〜`:4287` が `provider_artifacts` を必須にするが、producer がこれを書く条件は `arm_binding_digest is not None` かつ artifact root が `Path` (`P:2761`)。exploratory では `arm_execution is None` なので digest は `None` (`P:4177`)。さらに `raw_response_path` すら常には無い (`P:2827` は `FAILURE_PHASE_PRE_RAW_WRITE` 経路) |
| must-fix 2: diagnosis 付き 2 形に、生成器を通る正例が無い | **real / 採用。** 下記 4 の (D) で条件付き裁定 |
| must-fix 3: brief の成功条件を plan の訂正に合わせて確定する | **real / 採用。** 上記 2 で実施 |
| real だが scope 外: 正式 registered 系列は publish 前に `C:1137`〜`:1141` で拒否されるので、本 wave では回復しない | **real / scope 外。裁定パッケージへ。報告で「正式系列も直った」と書くことを禁じる** |
| real だが scope 外: admitted prefix + identity failure は救済されない | **real / scope 外。** root 必須のままが正しい |
| nit: brief の「2 file」と台帳追記の矛盾 | **採用 (上記 2 で訂正)** |
| 反証 6 件 | **反証を採用。** |

## 4. プラン v2 (段 5 へ渡す確定仕様)

plan の「現行挙動の表」「穴の同定」「所要台帳への追記」はそのまま採る。設計は次を差し替える。

- **(A) 既定経路は無改変。** `verify_autonomous_trial_files` を新引数なしで呼んだときの受理・拒否は
  1 つも変えない。これを固定する正例・負例を必ず置く。既存 2 免除 (`C:5054`、`C:5059`) と
  既存負例 `T:2353` は無改変。
- **(B) 明示 opt-in。** 新しい keyword 引数と CLI flag を足す。flag があっても、
  述語を満たさない report は fail-closed で落とす。root 指定時は従来検証をそのまま実行し、
  flag による検査省略を認めない。
- **(C) 述語は閉じた厳密一致。** plan §1 の key 集合方式を採る。`set(...) == {...}` を
  部分集合判定へ緩めない。`do_build is True`、cells 長さ 1、既存の厳密 decision / disposition 述語を再利用する。
- **(D) 欠けている束縛は「飛ばす」のでなく「不在を証明する」。** これが plan §4 の差し替えである。
  role/provider/raw の束縛は、**対象 report が実際に宣言しているものは厳密に検査し、宣言していないものは
  その不在を report 側の事実と突き合わせて証明する。** 最低限:
  - journal の role-attempt 件数と `honest_accounting.role_query_count` の一致を要求する。
    0 件なら 0 であることを要求する (「role event が無いから検査しない」は禁止)。
  - role-attempt があるとき、`provider_artifacts` / `raw_response_path` の有無を、
    report 側の事実 (`arm_execution` の有無、event の失敗段階) と束縛する。
    **「あれば検査、無ければ素通り」という presence 条件だけの分岐を書いてはならない。**
  - 段 5 の実装子は、この束縛を producer の現物 (`P:2725`〜`:2870`、`P:4165`〜`:4182`) から導出し、
    導出の根拠を完了報告に file:line で書く。導出できない形は**述語から外して狭める** (広げない)。
- **(E) Layer-3 側は既存 chain をそのまま呼ぶ。** 宣言 root を `_path_identity` で解決し、
  その `parent.parent` を `assert_campaign_layer3_chain` へ渡す。例外を握り潰して成功にする実装は禁止。
- **(F) receipt は検証範囲の申告であり、署名ではない。** 固定 schema で
  `certifying:false`、`campaign_output_root_binding:"not-verified"`、
  `s8c_cross_binding:"not-established"` を含める。**`campaigns/<ID>` 配下という包含関係を
  保証したと書いてはならない** (レンズ A の scope 外所見)。producer report は書き換えない。
- **(G) diagnosis 付き 2 形の条件付き裁定。** 実 finalizer の `layer3_report.render` 失敗から
  diagnosis を生成する正例 (`P:3115`〜`:3128` に到達する走) を作れるなら、許可 key 集合に残す。
  **作るのに生成器を mock する必要があるなら、diagnosis 付き 2 形を述語から削る。**
  どちらを採ったかを完了報告に書く。狭い方へ倒す。
- **(H) 編集面は 3 file。** `C`、`T`、`acceptance_duration_ledger.json`。
  producer・`trial_registry.py`・`verify_s8c_cross_binding` 本体・`assert_campaign_layer3_chain` 本体は無改変。

## 5. 変異事前登録 (DW-M01、実装前に登録)

anchor の逐語と行番号は実装後の最終 commit で `DW-M07` に従い固定する。ここで固定するのは
**機構と期待 node の対応**である。期待 node は完全集合とする。

| # | 殺す機構 (1 箇所) | 期待 KILLED node |
|---|---|---|
| M1 | 診断分岐の opt-in 条件を恒真化する | `test_failure_only_diagnostic_requires_explicit_opt_in` |
| M2 | cell key の厳密一致を部分集合判定へ変える | `test_failure_only_diagnostic_rejects_nonexact_shape[cell-extra]` |
| M3 | 診断 helper の `assert_campaign_layer3_chain` 呼出しを削除する | `test_failure_only_diagnostic_rejects_persisted_layer3[file]`、`[dangling-symlink]`、`test_failure_only_diagnostic_rejects_independently_admitted_campaign` |
| M4 | role-attempt 件数と `role_query_count` の一致検査を削除する | (D) で実装子が確定する負例 node |
| M5 | CLI から新引数を転送する行を削除する | `test_failure_only_diagnostic_cli_emits_noncertifying_receipt` |
| M6 | 診断 dispatch を無効化する (新経路を常に従来経路へ落とす) | 実 producer 由来の正例 node (全件) |
| M7 | admitted cell を弾く条件を落とす | `test_failure_only_diagnostic_rejects_admitted_cell`、`test_failure_only_diagnostic_rejects_mixed_cells` |

**登録しないもの:** receipt の `certifying` field を書き換えるだけの変異 (機構を殺していない)。
既存の共通検査に先に遮られる decision 変異 (単一理由性が立たない、`DW-M01` / F820)。
(G) で diagnosis 付き形を削った場合、diagnosis 関連の変異は登録しない。

実装後、各変異について「同じ入力を拒否する層が前後にも内側にも無い」ことを確認する。
確認できない変異は登録から外し、実効 gate へ再照準する (`DW-M01`、F28)。

## 6. 裁定パッケージ候補 (real だが scope 外。ユーザーへ返す)

1. 正式 registered 系列の failure report は publish 前に `C:1137`〜`:1141` で拒否されるため、
   本 wave では回復しない。回復させるなら producer と digest 契約の一体改訂になる。
2. admitted prefix + identity failure の混在 report は、root を与えても
   `C:4374` と `C:4911` の条件が両立せず受理できない。
3. `campaign_id` が絶対 path でも `expected_root` の突合せが通るため、
   `campaigns/<単一 ID>` 配下という参照保証は既存 chain にも無い。
4. producer が publish 前に `verify_s8c_cross_binding` を呼ばない非対称そのもの。
   producer 側で呼ぶようにするか、verifier 側で受けられるようにするかは設計択一である。

## 7. 停止しない理由

`DW-STOP` の正式停止条件 (承認前提を覆す新事実で裁定待ち) に当たるか検討した。**当たらない。**
覆されたのは親自身の provisional 前提 (P1)〜(P2) と brief の実測 3 であり、ユーザーの確定裁定ではない。
依頼が置いた歯止め (規律 2、束縛検査の一律撤去禁止、scope の限定) はすべて上記の仕様で守られている。
成功集合が増える点は依頼の内容そのものであり、明示して記録する。

---

## erratum 1 — 変異事前登録の訂正 (2026-09-16、段 6 レビュー後)

`DW-M01` は「同じ入力を拒否する層が前後にも内側にも無く赤理由が一つに絞れることを実装後に確認し、
できなければ登録せず実効 gate へ再照準する」と定める。段 6 レビュー B が現物から mask を示したので、
§5 の登録を次のとおり訂正する。初回登録は消さずここに残す (`DW-M02`)。

| # | 訂正 | 理由 (現物) |
|---|---|---|
| M4 | **再照準する。** 「role 件数と `role_query_count` の一致検査の削除」を取り下げ、**「valid role の raw bytes 検証 (`C:5105` 付近) の無効化」**に差し替える。対は既存 `test_failure_only_diagnostic_preserves_raw_binding` | 件数照合は `C:2924` の非 skipped ordinal 件数、`C:3069` の accounting 照合、`C:3207` の journal/report role 同一性、新述語の valid-only 制約に覆われ、helper 到達時には既に成立している。削除しても対の負例は先行 `C:3069` で落ちるため単一理由性が立たない |
| M7 | **条件付き。** 「admitted cell を弾く条件の削除」は、現行の 2 入力では `C:5041` の `status != partial` と `C:5044` の件数検査に遮られ生存する。段 6 fix で**単一理由の入力を構成できた場合だけ登録**し、構成できなければ登録から外し、外した理由を worklog へ書く | レビュー B が `C:5077` / `T:5878` の対応で mask を示した |
| M1・M2・M3・M5・M6 | 登録を維持する。**期待 node は fix 後の最終 commit で `DW-M07` に従って完全集合へ確定する** | レビュー B の静的予測では M1 は既存 `T:2353` の期待文字列も、M2 は `[diagnosis]` も、M6 は CLI と複数負例も赤にしうる。初回登録の期待 node は不完全である |

## erratum 2 — 段 6 レビューの裁定

### レビュー A

| 所見 | 裁定 |
|---|---|
| must-fix 1: `"proposal" in generation` なら即 `continue` するため、提案の宣言があるだけで producer 状態の確認を飛ばす (裁定 (D) 違反) | **real / 採用。fix する。** producer は `P:4409` で `arm_execution is not None` のときだけ提案参照を記録する。新述語は `arm_execution` を持つ report を除外しているので、**この形に提案宣言が現れる根拠が無い。狭める方向で拒否する** |
| real だが scope 外: 絶対 `campaign_id` による包含保証の欠如 | **real / scope 外。** 既存 chain の性質。gate を新設しない。receipt は包含を申告していないことをレビュー A 自身が確認した |
| nit: 既存テスト不変・編集面が差分不足で未確認 | **親が閉じた。** テスト file は 256 行追加・**0 行削除**、台帳の削除 2 行は末尾カンマと `nodeid_count` の更新だけ |
| 反証 7 件 | **反証を採用。** |

### レビュー B

| 所見 | 裁定 |
|---|---|
| 機構は空振りでない (外側 2 形・実 producer 3 経路、正例は検証機構を無効化していない) | **採用。** 本 wave の実効性はこれで裏取りされた |
| M4・M7 が生存する | **real / 採用。** erratum 1 のとおり訂正 |
| 期待 KILLED node が不完全 | **real / 採用。** `DW-M07` で fix 後に確定 |
| 負例のうち `[error-extra]`・`[decision-extra]`・`[disposition-extra]` は先行 gate で落ち、新述語の独立防護を証明しない | **real / nit。** 変異 M2 は `[cell-extra]` と `[diagnosis]` で足りる。テストを削らない (既存の入口拒否としては正しい) |
| 所要台帳 23 nodeid が AST 展開と完全一致 | **採用。** |
| scope 外 2 件 (正式系列は回復しない、包含保証は成立しない) | **採用。裁定パッケージへ既に積んである** |
| 反証多数 | **反証を採用。** |

**段 6 fix の scope はこれだけ:** レビュー A must-fix 1 (提案宣言の拒否 + 負例)、および M7 の単一理由入力が
構成できるかの確定。**それ以外の追加はしない。**

## erratum 3 — 段 6 fix の結果と変異登録の確定 (2026-09-16)

- **(F1) closed。** `_verify_failure_only_diagnostic` の `if "proposal" in generation: continue` を
  構造化 `_fail` (`failure-only-proposal`) へ替え、この経路の `_cross_binding_proposals` 呼出しを削除した
  (到達する入力が無くなるため)。負例 `test_failure_only_diagnostic_rejects_declared_proposal` を追加。
  親が差分を検算: 変化は `continue` 1 行の置換 (+ comment 2 行) と呼出し 2 行の削除**だけ**。狭める方向のみ。
- **(F2) 結論: 構成不能。M7 を登録から外す。** fix 子が示した先行 gate は同 verifier の
  `:3146` (非 Mapping decision)、`:3150`〜`:3154` (positive decision は外側 key 集合に必須の
  `pending_critic_disposition` があるため拒否)、`:3165`〜`:3168` (positive でも厳密 failure でもない decision を拒否)。
  したがって新述語まで到達する単一理由入力が存在しない。`DW-M01` に従い登録しない。
- **確定した変異登録は M1・M2・M3・M4(再照準後)・M5・M6 の 6 本。** anchor と期待 node は
  最終 commit で `DW-M07` に従い固定する。
- **所要台帳の 0.0 は正当。** consumer (`orchestrator/tests/conftest.py:1598`〜`:1619`) は
  負値・非有限・bool を拒否するだけで 0.0 を受ける。既存台帳にも 0.0 の項目が 1 件ある。
  親が実走値で上書きする必要はない (かつ台帳は実装面なので親は編集しない)。
  親の検算: 台帳 key 数 23142 = `nodeid_count` 23142、新規 24 件すべて 0.0。
- **焦点再レビュー子は起動しない。** fix 差分が 3 行の狭める変更のみで、両レビュー子が既に周辺を
  静的検査済みであるため。`DW-S06-C` は焦点再レビューを「1 本でよい」と許容するが必須としていない。
  代わりに親が差分を逐行検算し、変異 matrix と受入全走で裏取りする。
