# 段 4 裁定 — [T-2344] 発行器 6 本 + 発行器起点の 10 本を収載する (85 → 96)

裁定日時: 2026-09-21 08:5x JST。着手 commit `5efd69367`。
**裁定 inbox の再走査:** local main は `21641fee7` へ進んだ (docs のみ 4 commit = DW-M08 の self-run 手順の改訂と記録)。
`orchestrator/campaign` と `orchestrator/reports` の差分は 0 (レンズ B 所見 3 が独立に確認)。rulings-inbox の新着は
`2026-09-21-rulings-full28-verdicts.md` (第 28 回、08:1x) で、12 項に T-2344 は無い。本件を覆す新裁定は無い。

## 1. 所見の裁定

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 capture だけの変異では起動 test は赤にならない (`ident.py:283` の live 検証が残る) | real (plan の変異表) | 採用。§5 で期待 node を admission 側だけにし、起動 test は「後段 live 検証が拒否を維持する対照」として明記 |
| A-2 「exact-85 corpus 0 本」は走査条件を越えた断定 | real (親 measured-facts / brief) | 採用・**must-fix**。文言を「記載した root・除外 dir・mtime ≥ 2026-09-20 21:55 の走査 (08:31〜08:45) では未検出」に限定。再走査も条件と観測時刻つきで書く |
| A-3 収載は記録 blob 整合を検査するが、発行時点・実在 corpus を認証しない (合成 exact-85 も読める) | real (限界の記載漏れ) | 採用。insight の「言えないこと」へ記載。P2 の根拠を corpus 条件充足と混同しない |
| A-4 発行器の収載は全書出し経路に検査を掛けない (B10 report 分岐は現行 capture を通らない) | real (説明の限界) | 採用。insight の「言えないこと」へ経路別の表を書く。`b10_backoff_shape_sweep.py:635` の既存独自束縛と区別する |
| A-5 exact-85 が現行ラップ経由で certified に入る経路 | refuted | 採用。不変条件 1・2 の裏取り。入口分離を維持 |
| A-6 5 grammar の識別衝突 | refuted | 採用。「末尾 11 本削除」は宣言順の削除であり既知 85 になる → 未知 grammar の負例に使わない (歴史 85 の正例 / certified 拒否例に使う) |
| A-7 既存の未知 grammar 負例は維持される | refuted | 採用。既知 5 列との比較と validator 直接負例を維持。順序違いは「集合の未知性」でなく wire 順序検査と説明する |
| A-8 歴史 85 と現行 96 の固定 epoch は区別できる | refuted | 採用。文言は「**変更前の**現行 85 固定値と同一」。epoch 比較で scope / 型 / path 対応の検査を代替しない |
| A-9 brief の変異指定が粗い (union 変異は `KeyError`)。plan の node が一律 drift 汚染という懸念は refuted | real (brief) / refuted (汚染) | 採用。§5 で変異ごとに「変更箇所・binding root・期待失敗段・期待 node」を書く。M0 対照を置く |
| A-10 173 / 77 は probe 条件つきの値 | refuted (規則変更なし) | 採用。insight に probe の規則 (`ast.walk` + package 初期化、D1650 と同規則) と測定 commit を残し、集合・順序の再検算と発見集合の再測定を別証拠として書く |
| B-1 corpus 0 本での無条件収載は裁定の参照関係から導けない。(C) 受入直前に決めるのが最も整合的 | real (根拠の弱さ) / 結論は**不採用** | §2 のとおり (A) 収載を採る。**段 3 後の新実測**が (C) の前提を崩す: 直前 grammar の lock は tuple 前進**後**に固定木から生まれる (exact-63 の 25 本、00:34〜03:53、記録 commit `11d46a74a`)。受入直前に 0 でも land 後に生まれるので、(C) は空白を防げない。D1653 の corpus 条件が収載時点で未充足であることは開示し、decisions fragment に解釈を残す |
| B-2 「実在 corpus 0」は走査結果を越える。件数だけでは grammar の証明にならない | real | 採用 (A-2 と同じ must-fix)。将来 corpus を得たら wire 列と記録 commit の宣言順を exact 照合してから corpus と呼ぶ |
| B-3 「発行器 6 本」は全 certified consumer ではない (`backoff_sweep_report` / `backoff_requested_us` / `b10_backoff_static_tail_formal` / `t1998_stock_inline_pair` / `layer3_report` も certified 経路) | real (一般化の危険) | 採用。文言は「D2194 項 4 が名指しした発行器 6 本」。追加収載はしない (scope 外) |
| B-4 scope 案は D2081 適合。「発行器起点も閉じた」は言えない | refuted / real (将来の言い換え) | 採用。「指定 seed を追加した結果、静的発見集合が和集合と一致した」と限定し、未収載 77 を必ず併記 |
| B-5 受理集合の開示は land までの発生と既存運用を分けるべき | real (brief の条件不足) | 採用。「HISTORICAL_RAW の維持」と「最新 checkout の certified 再解析は救わない」を別々に書く |
| B-6 `s8b_oracle_report` の unavailable 分岐の scope を独立 literal で検査する追随が抜けている | real | 採用。`test_s8b_oracle_report.py` の既存 unreadable test へ現行 96 scope 2 項の独立 literal assertion を足す (test file は 5 → 6)。新 module・gate は作らない |
| B-7 局所修正の漏れ・過剰は P2 以外に無い | refuted | 採用 |
| B-8 変異は 5 群に分け、M0 対照を置く | real | 採用。§5 の群分けと M0 |
| B-9 受入増分は exact-85 の 85 件だけでは見積もれない (6 群の静的外挿で約 14.6 秒、実際は 16 秒以上) | real | 採用。見積りを記録し、受入実走の wall と件数で追認する (shard 並列の wall 予測ではないと明記) |

## 2. (P2) の裁定 — exact-85 を同 commit で収載する (案 A)

**決定:** exact-85 の歴史 grammar を本 wave の同じ commit で収載する。

**根拠 (段 3 後の新実測、`stale-tree-locks.json`):** exact-85 が main の現行 grammar になった 2026-09-21 00:21 以降にも、旧 grammar (exact-63) の
lock が **25 本** (00:34〜03:53) 記録されていた。書き手は T-2797 の submit-tree で、前進前の commit `11d46a74a` に固定された木である。
すなわち **直前 grammar の corpus は、tuple が main で前進した後に増える。** 現在 main を基点に走る並走 wave の木は、本 wave の land 後に
exact-85 lock を書きうる。(C)「受入直前に 0 なら収載しない」はこの発生を防げず、後から収載すれば D2193 が名指しした空白 (exact-62 のとき 8 日) が再発する。
25 本が今 HISTORICAL_RAW で読めるのは、前段が exact-63 を同 commit で収載したからであり、同じ機序が exact-85 にも要る。

**非対称性:** 収載の受理拡大は HISTORICAL_RAW の exact ordered tuple 1 個に限られ certified へ入らない (A-5 refuted、D1653 の必須条件は corpus 条件以外すべて満たす)。
収載しない誤りは記録を両経路から読めなくする (取り消すには別 commit が要る)。規律 2 は不変。

**開示 (must-fix):** D1653 (D1770 追認) の「実在 corpus が確認できた grammar だけ」は**収載時点で未充足**である (走査条件つきの未検出)。
本 wave は D2194 項 4 / D2193 の「tuple を動かす変更単位には直前 grammar の歴史収載を同 commit で含める」を、直前 grammar に限って corpus 条件より
優先する解釈を採る。この解釈は decisions fragment に書き、insight の裁定パッケージ節でユーザーが覆せる形にする (収載の撤去は exact-85 専用実装と test 群の削除で足りる)。
受入直前に走査を再実行し、条件・観測時刻・件数を記録する (0 本でも記録する)。

## 3. プラン v2 (確定)

段 2 plan を次の補正つきで採用する。

1. `campaign_lock.py`: plan のとおり (tuple 末尾へ 11 行、`:47` comment を exact 96、`T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS` を
   exact-63 literal の後に独立 ordered literal、白名単・兄弟 validator `_validate_t2344_exact85_historical_authority`・歴史 decoder の 5 分岐・docstring)。
   既存 85 の宣言順は 1 行も動かさない。exact-63 / 62 / 24 の validator・分岐・例外文面は 1 文字も変えない。
2. `artifact_admission.py`: plan の確定文字列 (現行 96 / 未収載 77 / `2026-09-21 (5efd69367 の source 木、本版の 96 path を起点)` / 173)。
   `T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `_EXCLUDED_SCOPE` は**変更前の現行 2 定数と 1 byte も違わない**独立 literal。
   分岐 4 箇所 + 説明 2 箇所。epoch hash 式は不変、scope を preimage に入れない。
3. `contract_loader_binding.py`: docstring の 85 → 96 のみ (`:2`, `:58`, `:61`)。
4. test (plan の表 + 本裁定の追加):
   - 固定値は §4 の 4 値をそのまま literal で置く。test 実行時に production 定数から再生成しない (D1652)。
   - 新設 node は plan のとおり (codec 4 群、admission 6 群)。`test_t2344_certified_acceptance_rejects_each_emitter_stage_source_drift` は
     **新 11 本だけ**を独立 literal で parametrize し、既存 22 本の node は残す。
   - **追加 (B-6):** `test_s8b_oracle_report.py` の既存 unreadable/unavailable test に、現行 96 scope 2 項の**独立 literal** assertion を足す。
   - 未知 grammar の負例は plan の棚卸しどおり据え置き。**「96 から末尾 11 本を落とした 85」を未知 grammar の負例に使わない** (A-6)。
   - 既存テストの期待値を反転・緩和・skip・削除しない。
5. 変更しない: exact-63 / 62 / 24 の経路、`b10_backoff_shape_sweep.py`、`layer3_report.py` 本体、docs の日付付き既述、lock の再発行。

### 新 validator の禁止 (署名で書く)

`_validate_t2344_exact85_historical_authority(value) -> HistoricalCampaignLockAuthority` は、`value` が次のいずれかなら
`CampaignLockCodecError` を送出しなければならない: `authority` の key 集合が `AUTHORITY_KEYS` と厳密一致しない /
`contract_loader_blob_sha256s` の key 列が `tuple(sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS))` と厳密一致しない
(subset 84 = env_contract.py 除去 / superset 86 = unknown path 追加 / 同数別集合 85 / wire 順序違い / 現行 96 / 現行 96 から 1 本落とした 95 をすべて含む) /
85 path のいずれかの digest が 64 桁 hex でない / `activation_serial` が正の exact int でない。
**通る正例:** 変更前の現行 85 tuple の宣言順で作った v2 authority (既存 fixture `test_artifact_admission.py` の E1 fixture を旧 85 map へ書き換えたもの)。
受理され、宣言順で再構成した blob map と `recorded_contract_loader_relative_paths = T2344_EXACT85_…` を持つ `HistoricalCampaignLockAuthority` を返す。

## 4. 固定値 (親 oracle `oracle-fixed-values.json`、plan と独立に一致)

| 値 | 内容 |
|---|---|
| 現行 96 合成 E1 epoch | `E1:244d998f35b0f7deae215a4053d9dde5acf60fc0775e4ea4c7a315579e7da07a` |
| 現行 96 順序付き path sha256 | `5c2c4a6a45ec44f46d655f1d9c43f1d877d5547fc46ff308fbdaa61df6683af4` |
| 歴史 exact-85 固定 epoch | `E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7` (= **変更前の**現行 85 固定値) |
| 歴史 exact-85 順序付き path sha256 | `bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1` (同上) |

計算規則: fixture bytes = ASCII `epoch closure fixture {i}\n` (i は 1-based 宣言位置)、
epoch = `"E1:" + sha256(b"campaign-verifier-epoch/v1" + Σ(path utf-8 + NUL + sha256(fixture bytes).digest()))`、
path sha256 = `sha256(Σ(path utf-8 + NUL))`。親 oracle は現行 85 で計算した値が変更前の test 固定値と一致することを正例対照済み。

## 5. 変異の事前登録 (DW-M01、実装前)

runner (焦点 file): `test_campaign_lock_codec.py`、`test_artifact_admission.py`、`test_t671_source_binding.py`、
`test_s1_9pair_figure_provenance.py`、`test_s8b_oracle_report.py`。**`test_layer3_report.py` は runner に入れない**
(前段で M0 対照が 5 node を落とした drift 核。layer3 の追随は焦点走の緑が担保する)。
`campaign_lock.py` / `artifact_admission.py` / `contract_loader_binding.py` はいずれも閉包 member なので (F923 / F741)、
**M0 (コメント 1 行だけの変更) を対照として登録し、runner 内で SURVIVED になることを probe で確かめてから final を走らせる。**
KeyError・import error・fixture 破壊・live drift だけで落ちる赤は kill に数えない (DW-M03)。

| # | 群 | 変異 (位置) | 期待する失敗段 | 期待 node の性質 |
|---|---|---|---|---|
| M0 | 対照 | `campaign_lock.py` の comment 1 行を変更 | なし | SURVIVED (drift 核が無いことの確認) |
| M1 | 収載追加 | 現行 tuple から `s8b_oracle_report.py` を除去 (95 本) | 独立 literal 不一致 | t671 / admission の独立 literal・件数 node |
| M2 | 収載追加 | 現行 tuple の末尾 2 path の宣言順を交換 | 固定 epoch / 順序 sha 不一致 | admission の固定値 node |
| M3 | 収載追加 | capture の disk-vs-HEAD 比較を新 11 本だけ素通り (`contract_loader_binding.py`) | certified 受理時の live 拒否消失 | **admission の新 11 本 drift node のみ** (起動 test は対照: `ident.py:283` の live 検証が残るので赤にならない、A-1) |
| M4 | 歴史可読性 | 歴史 decoder の exact-85 分岐を削除 | 正常な歴史入力が codec 拒否 | codec / admission の exact-85 正例 node |
| M5 | 歴史可読性 | exact-85 の committed blob 検証を省略 | blob 拒否消失 | `…rejects_each_recorded_commit_blob_mismatch` |
| M6 | 未知 grammar | 兄弟 validator の wire 比較を superset 許容へ (余分 key を投影で捨てる) | codec 拒否消失 (validator 直接呼出し) | `…rejects_unknown_grammars[superset]` |
| M7 | 未知 grammar | 歴史 authority 白名単を緩め 85+unknown を受理 | 型構築時の拒否消失 | `…authority_requires_exact_declared_order` |
| M8 | certified 隔離 | 通常 authority validator が旧 85 map も**一貫して**構築して返す (96 lookup を 85 に合わせる) | certified 隔離の拒否消失 | `…remains_rejected_by_normal_decoder` |
| M9 | 歴史 scope 凍結 | exact-85 歴史 scope の数値または日付を変更 | 独立 scope literal 不一致 | exact-85 歴史正例 node |
| M10 | 歴史 scope 凍結 | exact-85 scope 対を現行 96 文面へ差し替え | 凍結 scope 不一致 (epoch では検出できない) | 同上 |
| M11 | 歴史 scope 凍結 | exact-85 の epoch 計算順を sorted にする | 固定 epoch 不一致 | 同上 |
| M12 | certified 隔離 | 現行 scope 対と 85 map の組を `_RecordedCampaignVerifierEpoch` が許す | scope / path 対応の拒否消失 | `…epoch_requires_matching_scope_and_paths` |
| M13 | 未知 grammar | 兄弟 validator の宣言順再構成を wire 順のまま返す | 宣言順不一致の検出消失 | codec の宣言順 node |

期待 node は probe 走 (dispatch) で観測して完全集合として登録し、final で完全一致だけを KILLED と数える (DW-M08)。
fix が test を足したら probe を fix 最終 commit で再検証する (DW-M07)。

## 6. 受入と検査の見積り (B-9)

ledger (`acceptance_duration_ledger.json`) の静的外挿で、85 → 96 の逐次 duration 増分は 6 群だけで約 14.6 秒、
新 11 本の certified drift・歴史正負例・layer3 param を含めて **16 秒以上**を初期見積りとする。shard 並列の wall 予測ではない。
受入実走の結果 (件数と wall) で追認する。

## 7. insight の「言えないこと」へ入れる項目

- exact-85 の収載は記録 blob の整合を検査するが、**発行時点・実在 corpus を認証しない** (合成 exact-85 lock も読める、A-3)。
- 発行器 6 本は D2194 項 4 が名指しした seed であり、certified consumer の全数ではない (B-3 が挙げた 5 経路)。
- `b10_backoff_shape_sweep` の report 分岐は現行 capture を通らないので、本収載による追加検査は掛からない (A-4)。既存の独自束縛 (`:635`) とは別。
- 「certified 経路が source-bound」は推移閉包の意味で名乗らない (未収載 77)。「発行器起点も閉じた」と書かない (B-4)。
- corpus 0 本は「記載した走査条件での未検出」であり不在の証明ではない (A-2 / B-2)。
- 173 / 77 は親 probe の規則に依存する測定値で、本 wave が独立に再測定したのは集合・順序の一致まで (A-10)。

## 8. §2 の追補 (段 6 レビュー A-1 / B-1 / B-2 / B-4 を受けた訂正、2026-09-21 09:3x JST)

レビュー 2 本はいずれも「(P2) の収載そのもの」ではなく「根拠の書き方」を must-fix とした。§2 の根拠を次の 4 層に分け直す。

1. **観測 (事実):** 09-20 21:55 以降の指定走査 (2 root、除外 dir、mtime 条件、08:31〜08:45) で 85-key v2 の campaign.lock は
   **未検出**。63-key v2 は 53 本あり、うち 25 本は mtime が exact-85 の main land (00:21) より後 (00:34〜03:53)、記録 commit は
   すべて pre-85 の `11d46a74a` (T-2797 の submit-tree)。**mtime は発行時刻の証明ではない。** 件数分類 (85-key) は exact grammar の
   照合とは別で、exact 照合済みの exact-85 corpus は**未確認**である。
2. **生成可能性 (事実):** 現行 production の capture 経路は clean な木で exact-85 の binding を返す (`exact85-reachable.json`)。
   着手 commit `5efd69367`、`71e572b3c`、確認時の main `959c0f1ca` はいずれも tuple 85 本。85 本の木から campaign を起動すれば
   exact-85 lock が生まれる。
3. **予測 (不確実):** 25 本は同一の固定木による反復であり、「exact-85 でも同じことが起きる」ことの独立証拠ではない。
   land 後に exact-85 lock を書く木が実在し稼働し続けるかは確認できていない。**機序は支持されるが発生は未確認**であり、
   「空白が再発する」ではなく「再発しうる」と書く。
4. **政策判断 (本 wave の裁定):** 上を踏まえ、**直前 grammar については corpus 未確認でも同 commit で収載する**。
   これは D1653 / D2193 の corpus 条件から必然的に導ける結論ではなく、D2194 項 4・D2193 の同 commit 規則と、
   取り返しの非対称性 (収載しない誤りは別 commit を要し、その間 lock が両経路から読めない) を重んじた**本 wave の政策判断**である。
   **裁定パッケージとしてユーザーへ返す** (insight §8、decisions fragment)。撤去は exact-85 の literal・validator・分岐・scope 定数・
   新設 test 群の削除で足り、exact-63 以前と certified 経路には影響しない。

**収載の費用 (B-2、開示):** (a) 記録 commit の 85 blob と整合する**合成 lock** も歴史入口で読める (実在 corpus の認証ではない)。
(b) 歴史型・validator・scope・test 群を恒久保守する。(c)「production に存在した grammar なら corpus 未確認でも事前収載してよい」という
先例を作る。§2 の「非対称性」は収載しない側の費用に偏っていた。

**成果物影響の追加 (B-4):** `artifact_admission.py` の bytes が変わるので、**新規の admission receipt の `validator.sha256` が変わる**
(歴史 campaign を新たに読む場合を含む) ほか、B-4 projection hash の材料にも同 file が入る (D2081 の「保証しない範囲」が既に限界として記す)。
記録済み成果物の bytes は変えない。dirty 拒否が広がるのは**中央 capture を通る経路** (campaign 起動時の capture、certified 受理時の
`capture_contract_loader_binding`) に限る。`b10_backoff_shape_sweep` の report 分岐 (歴史 exact-24 限定) には掛からない。

**見積りの位置づけ (B-7):** §6 の「16 秒以上」は **63 件時点の ledger からの部分外挿による下限寄りの初期見積りで、未追認**。
fixture が 85 → 96 本になる既存 node の増加費用を含まない。受入実走の件数と wall で追認し、並列 wall の予測としては使わない。
