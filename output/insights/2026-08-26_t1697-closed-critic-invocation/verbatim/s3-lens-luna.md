判定は「現状のまま採用不可」です。静的検査のみで、pytest・CLI 実走はしていません。

### F1 — blocker: 前提条件 3 の gate が正式経路へ接続されない

- **(a) 何が壊れるか** — 新 module の production consumer は存在せず、現行 venue は引き続き道具あり `Agent(critic)` を使う。専用 controller の存在だけで §6.3 を充足済みにすると、実際には閉じた invocation を強制できない。
- **(b) 根拠** — `plan.md:5-9,193-205,209,223`; `docs/phase3-s4b-runbook.md:102-106`; `docs/phase3-b4-reflux-ablation-preregistration.md:181-188`。
- **(c) 最小是正案** — 新 module に sanctioned な薄い CLI を設け、runbook からその route だけを参照する。そこまでしないなら §6.3 は「機構あり、正式経路への採用待ち」とし、§10 から削除しない。
- **(d) 成果物影響** — 現状では certified 選択・材料レポート・試行台帳はすべて不変で、生成した receipt は正式標本に到達しない。

### F2 — blocker: role file pin は避けても I/O contract pin を迂回する

- **(a) 何が壊れるか** — role 名 `critic` の reviewed contract は入力 `digest`、出力 4 field だが、plan は同じ role に `projected_digest` と `result` の新 contract を局所注入する。これは pin 更新不要ではなく、review ledger の外で第 2 contract を作る形になる。
- **(b) 根拠** — `plan.md:15,24,38,70,75-84`; `orchestrator/codex_roles/review_ledger.py:1-5,119-125,208-213`。
- **(c) 最小是正案** — top-level は既存 `{"digest": str}` と既存 4-field output を再利用し、coarse result は型付き digest 本文へ入れる。別 schema が不可欠なら route-scoped pin の追加を裁定パッケージへ返す。
- **(d) 成果物影響** — 未是正では prompt/projection hash が「review 済み critic contract」の参照として信用できず、その receipt を受理集合へ入れられない。

### F3 — blocker: paired 1-step の同一 precursor を検査していない

- **(a) 何が壊れるか** — controller は別 campaign の各 `whiteboard[-1]` と digest を独立に読むだけで、coarse result、緑 digest、初期 snapshot が同一かを pair gate が確認しない。測定差以外の campaign 履歴差を treatment と誤認できる。
- **(b) 根拠** — `plan.md:73,86-91,109-113,138-163`; `docs/phase3-b4-reflux-ablation-preregistration.md:55-64,95-108,162-168`。
- **(c) 最小是正案** — receipt に `precursor_snapshot_sha256`、iteration、coarse result、green-only digest hash を加え、pair 時に equality と「on の赤節以外は off と byte 同一」を要求する。
- **(d) 成果物影響** — 異なる precursor の pair が成立扱いとなり、primary outcome、成立分類、将来の certified 根拠が交絡する。

### F4 — blocker: 事実上の第 2 arm 切替点と nuisance 差がある

- **(a) 何が壊れるか** — arm が `cfg.reflux`、controller constructor、`invoke(arm=)` の 3 箇所にあり、artifact directory と neutral root にも影響する。さらに両 controller は異なる executable、runner、environment を受け取れるのに pair 検査がそれらを比較しない。
- **(b) 根拠** — `plan.md:40-50,65-71,117-136,138-163`; `docs/phase3-b4-reflux-ablation-preregistration.md:100-101,125-132`。
- **(c) 最小是正案** — 共通 sealed pair factory から両 controller を作り、arm は `cfg.search_config["reflux"]` から一度だけ導出する。`invoke(arm=)` を削除し、executable hash、timeout、contract、provider/tool fields の対称性も検査する。
- **(d) 成果物影響** — treatment 以外の実行条件が違う receipt pair が受理され、アーム差の帰属が失われる。

### F5 — mutable state と receipt の snapshot 束縛がない

- **(a) 何が壊れるか** — `invoke()` は任意時点の campaign view と最新 checkpoint を読むため、停止済み campaign や次 iteration 後の状態から、以前の digest/result を再送できる。receipt に checkpoint/WAL/iteration の束縛もない。
- **(b) 根拠** — `plan.md:48-50,73,87-88,140-149`; `orchestrator/campaign/p3_s4_loop.py:1230-1235,1245-1266`。
- **(c) 最小是正案** — 呼出時に expected iteration と CLI 生成 digest hash を要求し、checkpoint hash、WAL prefix hash、`critic_digest_generated=true` を同一 snapshot として receipt に固定する。
- **(d) 成果物影響** — 古い outcome を新しい試行の critic 入力として台帳へ参照でき、停止理由と次 synthesis の対応がずれる。

### F6 — 前提条件 4 は局所的に回避するだけで、強制されない

- **(a) 何が壊れるか** — plan 自身は `run_one_iteration()` の戻り値を使わないので直接干渉はない。しかし、直呼びした caller の標本や異なる `policy_hint` を拒否する admission gate がなく、専用 receipt があるだけで sanctioned CLI 経路だったとは証明できない。
- **(b) 根拠** — `plan.md:73,89-91,224-225`; `docs/phase3-b4-reflux-ablation-preregistration.md:185-188`; `orchestrator/campaign/p3_s4_loop.py:1026-1048,1134-1142`。
- **(c) 最小是正案** — 本 wave では前提条件 4 を未充足のまま明記し、receipt を B-4 ready 証明に使わない。CLI provenance と `policy_hint` 束縛は別裁定パッケージにする。
- **(d) 成果物影響** — 即時の受理集合は空のまま。境界を曖昧にすると、API 直呼び標本が材料レポートへ混入する。

### F7 — `prior_critic_reverse` の ownership が未定義

- **(a) 何が壊れるか** — response parser の exact output schema が書かれていない。`reverse_recommended` を controller が生成・消費すれば既存 ownership を変え、自由文の `recommend` から導けば runbook 決定 2/7 に反する。一方、無視すれば供給規則は未充足のまま。
- **(b) 根拠** — `plan.md:38,61,181-187,225`; `docs/phase3-s4b-runbook.md:102-107`; `orchestrator/campaign/p3_s4_loop.py:1147-1157`; prereg `:189-193`。
- **(c) 最小是正案** — controller は既存 4-field response を検証して main session へデータとして返すだけにし、bool の導出・proposal 書込み・state fold をしない。構造化 bool の新設は contract pin と併せて別裁定へ送る。
- **(d) 成果物影響** — 誤実装時は `reverse-exhausted` と次 synthesis の有無が変わり、試行台帳の停止理由と標本数が変わる。

### F8 — campaign identity 非開示の証明範囲を過大表示する

- **(a) 何が壊れるか** — exact 3 文字列の payload 内不在しか検査しないのに、`campaign_identity_absence_checked=true` として性質 2 全体を閉じた扱いにする。effective prompt、environment、transport metadata、alias・符号化された identity は対象外で、plan 自身も metadata の不可視性を証明しないと認める。
- **(b) 根拠** — `plan.md:58,93-105,149,159,229`; `brief.md:88-89`; prereg `:220-224`。
- **(c) 最小是正案** — field を `exact_identity_literals_absent_from_canonical_payload` に改名し、性質 2 は「payload の exact 値」に限定する。role-view 全体の非開示は別 gate として残す。
- **(d) 成果物影響** — off 汚染を成立扱いにでき、判定不能であるべき block が成立／不成立へ誤分類される。

### F9 — 失敗 invocation と receipt 保存が fail-open

- **(a) 何が壊れるか** — success receipt の fields しか定義されず、timeout、invalid response、CLI failure の terminal receipt、再試行禁止がない。caller 指定 `invocation_id` をそのまま filename に使う設計は上書きや path 脱出も防いでいない。
- **(b) 根拠** — `plan.md:48-50,138-151,181-187`; prereg `:173-174,202-206,218-219`。
- **(c) 最小是正案** — invocation ID を閉じた字種で検査し、exclusive create する。開始 receipt と success/failure terminal receipt、timeout、retry ordinal を必須化する。
- **(d) 成果物影響** — 失敗 role query が予算・台帳から消え、片アームだけの再試行や receipt 差替えが可能になる。

### F10 — §7.2 の残存経路は削れない

- **(a) 何が壊れるか** — 専用 route が閉じるのは Bash/digest CLI の到達だけである。file-drawer、API return、`policy_hint`、別 root、2 件の生存変異は引き続き開くため、「前提条件 3 を閉じた」から §7.2 全体を縮めることはできない。
- **(b) 根拠** — `plan.md:211,219-230`; prereg `:214-224,250-256`。
- **(c) 最小是正案** — §7.2 の 3 項を残したまま、「専用 route の exact capability lowering」だけを追記する。§10 も route 採用前は削除しない。
- **(d) 成果物影響** — 全域 closure と誤読されると、判定不能・protocol violation の集合が不当に狭まる。

### F11 — §8 の「証明しないこと」更新案が不足する

- **(a) 何が壊れるか** — 「新 test と receipt が能力遮断を別途固定する」は D824 に対して強すぎる。また plan は §8 の残る 2 限定、T4 が検査しない順序と T3 が実 path 分離を証明しないことの保持を明記していない。
- **(b) 根拠** — `plan.md:207-215`; `brief.md:13-14`; prereg `:242-248`。
- **(c) 最小是正案** — 3 項をそのまま残し、「新 test/receipt が示すのは専用 invocation の declared tools と観測事実だけで、critic role 自体や他 route の能力遮断ではない」と追記する。
- **(d) 成果物影響** — T1-T5 の受理範囲が verifier 順序・実 path・role 能力へ不当に拡張され、材料レポートの証拠参照が過大になる。

### F12 — 負の対照 docstring は更新が必要

- **(a) 何が壊れるか** — `1833` と `1951` の docstring は閉じた invocation を「本 wave の scope 外」と記すため、実装後は歴史的に偽になる。なお `1811` の現物 docstring はその文を含まず、digest の性質だけを述べている。
- **(b) 根拠** — `plan.md:8,201-203`; `orchestrator/tests/test_p3_s4_loop.py:1811-1812,1833-1842,1951-1957`。
- **(c) 最小是正案** — 後 2 本を更新する。残す文は「本 test は harness digest の性質だけを証明し、critic role 自体の能力遮断も専用 controller の実効 lowering も証明しない」。`1811` は現状維持か同じ限定を追記する。
- **(d) 成果物影響** — 放置すると plan が焦点走として示す 3 参照から、閉じた route が未実装だと誙読され、材料レポートの証拠リンクが食い違う。

### F13 — runbook を無変更にすると旧経路を B-4 と誤認させる

- **(a) 何が壊れるか** — runbook は旧 `Agent(critic)` を使いながら、`--reflux off` の別 campaign を LLM ablation と記す。事前登録はその role を off 標本として数えることを明示的に禁止している。
- **(b) 根拠** — `plan.md:8,223`; `docs/phase3-s4b-runbook.md:102-106,124-131`; prereg `:181-184`。
- **(c) 最小是正案** — runbook に「この legacy 手順は B-4 非適格」を明記し、専用 CLI ができた場合のみ別節から参照する。B-4 実走自体は行わなくてよい。
- **(d) 成果物影響** — 旧手順の出力が B-4 行や台帳へ誤登録され、off 標本の受理集合が汚染される。

### F14 — 親 brief の成果物影響が因果を一段盛っている

- **(a) 何が壊れるか** — 「実装しないと B-4 行が空」は正しいが、実装しても前提条件 1、2、4〜8、発効版、実走、acceptance consumer が未実装なので同じく空である。前提条件 3 だけでは論文の機序証拠へ到達しない。
- **(b) 根拠** — `brief.md:5-6,78-82,92`; prereg `:32-48,142-196`; `plan.md:217-230`。
- **(c) 最小是正案** — 成果物影響を「閉じた invocation 候補と route-local receipt が利用可能になる。正式選択・材料レポート・試行台帳は変わらない」と書き換える。
- **(d) 成果物影響** — 未是正では wave 完了だけで B-4 証拠が前進したように記録されるが、実値・受理集合・台帳行はいずれも増えない。

pin 閉包については、新 role file を作らないため `EXPECTED_ROLE_COUNT` と role-name pin 群を直接変えない判断自体は妥当です。ただし F2 の第 2 I/O contract は別問題です。opaque baseline は `test_reflux_originless_compatibility.py:12-13,357-360` で併走所有の autonomous trial 出力を丸ごと固定しており、新 module 単独では波及しません。global `critic` contract を変更すると波及し得るため、route-local に閉じる必要があります。

## 総括

最も重い所見は F1、F2、F3 です。

1. 閉じた controller が正式 venue・runbook・受理 consumer に接続されず、前提条件 3 の充足を強制できない。
2. role file を増やさずに同じ `critic` role の第 2 I/O contract を作り、review pin を迂回している。
3. 同一 precursor、coarse result、green digest の pair equality がなく、estimand が交絡する。

したがって、このプランは現状のまま採用すべきではありません。最低でも route の sanctioned 化、既存 critic contract との整合、paired precursor gate、D824 限定と runbook/docstring の更新を入れてから再レビューが必要です。