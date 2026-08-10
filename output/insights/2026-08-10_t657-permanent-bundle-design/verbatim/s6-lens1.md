# 敵対レビュー

**結論: NO-GO。** 静的検査のみ実施し、ファイル変更・pytest 実行はしていない。

本書が「exact 仕様ではない」と明記している点は確認した。ただし以下は単なる実装詳細不足ではなく、本文がすでに真だと主張する digest、commit topology、完了判定、不変条件、既存拒否についての反証である。

## 段3所見の逐件対応

| 段3所見 | 本文への対応 | 判定 |
|---|---|---|
| [A-R1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:7) | G_f/A_f 分離を [§5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:97) に導入 | 分離は反映。ただし exact parent/diff は未定義で R-2 が残る |
| [A-R2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:34) | [§5:125–128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:125)、[§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:132)、Q1 | 反映済み。衝突を未裁定として露出している |
| [A-R3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:60) | [§7.2-1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:163) | 文言のみ反映。拒否 predicate は無い。R-4 |
| [A-R4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:85) | [§8:204–206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:204)、[§10 段5/6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:254) | 順序制約は反映 |
| [A-R5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:109) | [§10:241–245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:241) | 規則名だけ反映。表自身が規則に違反。R-3 |
| [A-R6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:132) | [§7.2-2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:168)、§10 段2 | 候補型・oracle が無い。R-4/R-5 |
| [A-R7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:152) | [§6 E-1/E-2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:132) | 択一は反映。ただし E-1 と §5 が自己矛盾。R-2 |
| [A-R8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:180) | [§5:117–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:117)、[§7.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:176) | Q の名前/hashだけ反映。内容検査なし。R-1 |
| [A-R9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:203) | [本体 §1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:18) と [追記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:15) | 正しく反映 |
| [A-R10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensA.md:223) | §10 段4を定義、Xを段6へ移動 | 大枠は反映。ただし各段の oracle は壊れている。R-3 |
| [B-1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:7) | [§7.3 seal slot](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:176)、[§8-1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:201) | slot 名のみ。空・偽 slot の拒否規則なし。R-1 |
| [B-2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:32) | [§8-2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:204) | bytes/path/namespace/schema の必要性は反映 |
| [B-3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:55) | [§8-3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:207)、[§13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:307) | G-b 不可能性を未裁定制約として反映 |
| [B-4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:77) | §7.2-2 | 型名だけで field/source が無い。R-5 |
| [B-5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:104) | §6 と Q1 | 反映済み |
| [B-6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:129) | §5 と §7.3 | exact lineage/Q semantics は未反映。R-1/R-2 |
| [B-7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:151) | [§7.2-3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:172)、[§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:218) | carrier 名だけ。identity key への参加を検査しない。R-4/R-6 |
| [B-8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:176) | 本体 §1 と freeze 文書追記 | 正しく反映 |
| [B-9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:197) | §7.3 に seal/Q/profile を追加 | preimage が循環・不足。R-1 |
| [B-10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:215) | [本体:13–14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:13) | 本体では反映済み |
| [追加A](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:236) | [§12 Q2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:295) | 名目上のみ未裁定。§5 がすでに人間 A/X を採用。R-7 |
| [追加B](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:252) | [§12 Q3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:298) | 一方で §1/§5 は lockstep topology を固定。R-7 |
| [追加C](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage3-lensB.md:267) | §6、§8-4、§12 B/Q4、§13 | source pin と長寿命 process を分離して反映済み |

## real

### R-1 — B/Q の digest 契約は循環し、偽 Q を拒否しない

**(a) 主張**

本文の「B と Q を bundle digest の preimage に入れる」は、文字どおりなら自己参照で計算不能、非循環に解釈すると Q の意味を何も検査しない。段3 R8/B-6/B-9 は名前だけ反映され、破れ方は残った。

**(b) 根拠**

- topology は B の後に Q を置く: [§5:104–113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:104)。
- 同時に「B と Q を digest preimage に入れる」とする: [§5:117–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:117)、[親裁定 J6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s4-ruling.md:21)。
- §7.3 の実際の列挙には、現 B の raw hash、権限束 `generation_number`、B path/schema が無い。あるのは親束 identity と Q raw hashだけ: [§7.3:176–185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:176)。
- Q の exact schema、検査項目、再計算値、B との対応 predicate はどこにも無い。
- 現行 Python には `ResolvedAuthorityBundle`、`resolve_active_authority_bundle`、`seal_binding`、`ruling_profile`、`authority_bundle_sha256` が各 0 件である。既存 schema は lower freeze 用だけである: [s8b_ratified_freeze.py:94–121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:94)。

**(c) 壊れ方の構成**

1. `Q_fake = {"status":"pass"}` の canonical bytes を先に作る。
2. その raw hashを B digestへ入れ、B commitを作る。
3. 次の Q commitで `Q_fake` を追加する。
4. A は B digestと Q の存在だけを確認する。

Q の再計算規則がないため、自動検査を一度も走らせず段4の digest/cross-pair 条件を通せる。

逆に Q が B identity を検査する正当な receiptなら、`B digest → Q hash → Q の B identity → B digest` の循環になる。さらに権限束番号を変えても §7.3 の列挙 preimage は変わらず、同じ digestを持つ異なる B recordを構成できる。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: 未検査の環境/freeze 組が同じ bundle identity で承認され、certified 選択・report・budget/WAL 台帳が偽 Q または別世代 B を同じ参照として受理する。循環解釈なら正当な束も全件拒否される。

---

### R-2 — §5 topology は自己矛盾し、現行コードでは上位 B/Q/A/X を構成できない

**(a) 主張**

§5 は A/X を「1ファイル追加のみ」と固定する一方、E-1 は X を3-path diffにする。加えて、現行コードで意味のある B/Q/A/X commitを置ける namespace・schema・resolver は存在しない。

**(b) 根拠**

- A/X は各1ファイル追加のみ: [§5:111–123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:111)。
- E-1 の X は公式 record追加、literal編集、上位 pointer追加の3-path diff: [§6:134–144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:134)。
- 「Xまで active pointer は変わらない」とするが、A_f 自体が lower active pointerを追加する: [§5:125–128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:125)。

現行 commit 別の発火点は次のとおり。

| commit | 現行検査 | 構成可能性 |
|---|---|---|
| E | 権威 directory 全件を読み [terminal serial/hash と literalを照合](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:365)。head literalは [serial 1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:373) | `00000002.json` を公式 directoryへ足すと [head mismatch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:408)。外へ置くと loaderが無い |
| G_f | path/schema: [85–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:85)、履歴/provenance: [1090–1101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1090)、親: [948–961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:948) | lower candidateとして構成可能。ただし G exact diff は検査しない |
| A_f | user trailer: [1104–1131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1104)、G≠A・exact 2-path diff: [1189–1211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189) | 構成可能。ここで lower pointer は発効する |
| B | 上位 schema/pathなし | freeze namespace内なら semantic parseされず [その他 fileとして除外](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1160)、official preflightでは [未知 file拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1674)。外なら無視 |
| Q | 同上 | 検査 receiptとして構成不能 |
| A | lower approval namespaceを使うと lower `_APPROVAL_KEYS` と A_f pairingを要求される | 上位 approvalとして構成不能 |
| X | lower active namespaceを使うと lower pointer schema・approval pairingを要求される: [1230–1251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1230) | 上位発効として構成不能 |

**(c) 壊れ方の構成**

E-1 の X を §6どおり3-pathで作れば、§5の1-path規則に違反する。§5どおり上位 pointerだけを追加すれば、environment recordとliteralは旧値なので式1を満たせない。

現行コードだけで3-path Xを作ると、record+literal更新によって環境 g2 は [env loader](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:519) から有効になるが、上位 pointerは誰も検査しない。protocol hashが新 current contractと一致すれば [live admission](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:340) は通るため、B/Q/Aを無視した活性化になる。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: E-1では上位承認なしに current contract/floor参照が切り替わるか、正当なXが形状拒否される。reportの protocol/freeze hash、certified選択の受理集合、campaign台帳のauthority参照が分岐する。

---

### R-3 — §10 は自分で課した「全段に陽性条件」を守っていない

**(a) 主張**

段0・5・6・8は陽性条件を持たず、reject-allで真になる。段1・2・3・4・7も正常 fixture、期待値、比較領域が無く、自己申告または判定者の主観で完了にできる。

**(b) 根拠**

全段陽性規則は [§10:241–245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:241)、各行は [§10:247–257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:247)。

| 段 | 型 | 行単位判定 |
|---|---|---|
| 0 | 書けば自動的に真 | fieldを「新規出力」と書くだけ。正常 schema の受理条件が無く、名指しされた静的 checkerも実在しない |
| 1 | 測定手段なし／主観 | 「固定の負例一覧」の path・内容・reason oracleが無い。「現状の正常入力」も未特定 |
| 2 | 主観 | `registered-inactive` の実型が無く、「ちょうど候補として解決」の観測値が循環定義 |
| 3 | 測定手段なし | 無限の受理/拒否集合の「完全一致」を要求する。source scanはwrapper・alias・間接HEAD取得を証明しない |
| 4 | 主観 | 「正当なA」「Xの候補」のschemaが無い。E/G_f/B/Qのmerge・余分diff・偽Qも完了判定に入らない |
| 5 | 書けば真 | 本文自身が「未定義」。列挙は負条件だけで、reject-allなら観測も存在せず恒真 |
| 6 | 書けば真 | 「段5後」の順序だけ。正常Xの判定式なし |
| 7 | 主観 | 「正常なcampaign」がfixtureで固定されていない。任意の1ケースだけ通せる |
| 8 | 書けば真／測定不能 | 合格条件を後送り。現行は先に [generation≠1を拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:2874) するため、全変異が同じ拒否で緑になる |

**(c) 壊れ方の構成**

- 段0: 任意の架空 fieldを「新規出力」と文書化する。
- 段4: `verify_authority_approval()` を常に例外にし、全負例を緑にする。
- 段5: 全Xを拒否する。未解決profileの拒否も「全観測にbundle ID」も空集合上で真になる。
- 段8: `certificate-generation-scope` を残し、parent/gap/fork/rollback mutationをすべて同じ先行拒否へ落とす。

いずれも表の文言を満たしたと主張できる。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: reject-allを完了扱いするとcertified選択・reportが生成不能になり、恣意的な陽性fixtureを完了扱いすると本来拒否すべきbundleが台帳へ受理される。

---

### R-4 — §7.2 の3不変条件は、違反実装を一件も機械拒否しない

**(a) 主張**

§7.2 は禁止事項を謳うが、§10に対応するschema mutation・identity mutationがない。三項すべて、違反実装を作っても列挙済み完了判定を通せる。

**(b) 根拠**

対象は [§7.2:163–174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:163)。

現行 floor resolverは exact `ExecutionEnvironmentContract` への縮約を要求する: [s8b_floor_campaign.py:340–381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:340)。現行出口もbundle identityを持たず、たとえば budget identityは manifest/freeze/scheduleだけ: [s8b_budget.py:208–227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_budget.py:208)。

**(c) 壊れ方の構成**

| §7.2項 | 違反実装 | それでも通る本文判定 |
|---|---|---|
| 1. lower pointerだけ参照 | Bに正しい `lower_pointer_sha256` と別の `lower_generation_path` を持たせる。validatorはpointer存在だけ確認し、consumerは後者を使う | §10段3は固定path/direct resolver/HEADのsource scanだけ。Bの余分なgeneration field拒否が無い |
| 2. candidate型を出口まで保持 | candidate resolverが通常の `ExecutionEnvironmentContract` を返し、関数名・ログだけ「candidate」とする | 段2の「候補として解決」に型名・field・expected valueが無い |
| 3. bundle identityを出口まで運ぶ | `authority_bundle_sha256` を表示用fieldとして各JSONに追加するが、claim key・run marker path・budget key・verdict計算には使わない | 「持つ」「残る」は満たす。bundle IDを変えてclaim衝突・budget共有・verdict不変になるmutationが無い |

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: 未承認lower generationがcertified材料へ入り、異なる上位bundleのrunが同じclaim/marker/budgetへ合流し、reportと台帳のauthority参照が実使用権限と食い違う。

---

### R-5 — `issuer` と `bundle membership` は実在しない入力である

**(a) 主張**

core結合fieldは実在するが、§7.2-2が「失われる既存情報」として扱う `issuer` と「どの束に属するか」は、現行activation record、GenerationEntry、AuthorizedContractのどこにも無い。新規出力・導出規則とも明記されていない。

**(b) 根拠**

| 本文が名指すもの | 実成果物/型 | 判定 |
|---|---|---|
| `activation_serial` / `activation_state_sha256` | activation record exact keys: [env_contract_activation.py:17–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:17) | 実在 |
| `active_contracts[].generation` | [ActiveContract:38–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:38) | 実在 |
| freeze `generation_number` | [v2 keys:100–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:100) | 実在 |
| lower active pointer exact ref | pointer keysと [ActiveResolution:797–808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:797) | 実在・導出可能 |
| candidate/currentの実型 | `GenerationEntry` は generation+contractだけ: [env_contract.py:172–188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:172) | 非実在 |
| issuer | activation schemaにも `AuthorizedContract` にも無い: [env_contract.py:447–456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:447) | 非実在 |
| bundle membership | 同上 | 非実在 |

権限束世代、B/Q、seal slot、ruling profileは本文中で新設すると読めるため、「既存fieldが架空」という攻撃は当たらない。ただし exact field/output分類は段0へ先送りされている。

**(c) 壊れ方の構成**

現行activation schemaでcandidate recordを表すと、exact key集合は `schema_version/serial/predecessor/active_contracts/state_hash` だけである。[未知keyは拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:189)されるため、issuer/membershipを足せない。省けば§7.2-2を検査できない。

結果として、既存contract hashから通常の `GenerationEntry` を返す実装は、候補をcurrentと同じ型で出口へ流せる。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: 同じcontract hashがcandidate/currentの双方として受理され、X前の環境がWAL・report・certified選択へ入るか、逆に全candidateが拒否されるため受理集合が変わる。

---

### R-6 — §11の最終行は「保存すべき拒否」ではなく、まだ存在しない拒否である

**(a) 主張**

§11の7行中6行には限定付きでも現行対応がある。最終行「bundle IDを持たない成果物」は現行では正常成果物そのものであり、対応検査が存在しない。本文の「いずれもproductionの正しいfail-closed」は虚偽である。

**(b) 根拠**

対象表: [§11:264–279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:264)。

| §11行 | 現行検査 | 対応 |
|---|---|---|
| 同一path別bytes | `_immutable_introductions`: [469–494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:469)、record列挙時呼出し [1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1090) | 存在。ただしlower v2 resolverを通る経路に限定 |
| floor新・prediction/journal旧 | freeze/protocol pin [1432–1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1432)、pre-oracle protocol一致 [1493–1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:1493) | 存在。v1固定 |
| activationだけ進む | current contract resolver [327–390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:327)、live launchでも [2769–2780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:2769) | 存在 |
| record末尾とhead不一致 | [env_contract_activation.py:408–415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:408) | 存在 |
| generationのみ・pointerなし | [no-active:1253–1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1253) | active解決として拒否 |
| 未承認generation | pointer→approval照合 [1230–1251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1230) | lower freezeでは存在 |
| bundle IDなし成果物 | 対応なし | **まだ無い拒否** |

むしろ現行schemaはbundle IDを排除する。

- execution receipt exact keys: [s8b_floor_campaign.py:984–997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:984)
- resultは protocol/freeze/manifest hashのみ: [s8b_floor_campaign.py:2530–2542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:2530)
- run marker identityはfreeze hashのみ: [s8b_run_marker.py:32–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_run_marker.py:32)
- campaign lock authorityも環境側fieldだけ: [campaign_lock.py:19–25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/campaign_lock.py:19)

**(c) 壊れ方の構成**

現行の正常な result、execution receipt、run marker、budget ledgerをそのまま上位resolver後も使う。すべて既存validatorを通るが、bundle IDは無い。同じfreeze bytesでenvironmentだけ異なる二束はmarker/budget/result identityを共有する。

したがって最終行は保存ではなく新設対象である。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: 異なるbundleのrunが同じmarker・budget・report参照へ合流し、certified選択と試行台帳がどの環境/freeze組を使用したか一意でなくなる。

---

### R-7 — 追加裁定A/Bは「未裁定」と書きながら本文が先に選んでいる

**(a) 主張**

Q2はA/Xの主体を未裁定とするのに§5が両方を人間commitと固定する。Q3は一成分successorを未裁定とするのに、本文の正本範囲とtopologyがEとG_fの同時交代しか表現しない。

**(b) 根拠**

- Q2は主体未確認: [§12:295–297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:295)。
- しかし§5は A/X とも「人間、none trailer」と断定: [§5:109–112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:109)。
- Q3はenvironment-only/freeze-only successorを拒否してよいか未裁定: [§12:298–300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:298)。
- しかし本書の正本範囲は「両者を同時に世代交代」: [§1:20–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:20)、topologyはEとG_f/A_fの双方を必須列にする。
- 一成分successor・rollbackの陽性条件は§10に無い。

**(c) 壊れ方の構成**

- AI主体の上位Xを将来Q2で選んでも、現本文の`AI-Agent: none`規則では拒否される。
- freeze-only successorをQ3で許可しても、§5列では新Eが必須であり、段4の正当列を構成できない。
- 逆に§5を正本として実装すると、ユーザー裁定前に両入力を拒否するlockstep政策が確定する。

**(d) 判定**

**real**

**(e) 区分**

**must-fix**

成果物影響: 上位A/Xの受理主体とrollback・一成分successorの受理集合が裁定結果と食い違い、active bundle pointerおよびreport/台帳が参照する世代が変わる。

## refuted

### F-1 — 親briefのM1/M2自体が誤り、という疑い

**(a) 主張**

M1/M2の実測事実を反証できるか検査した。

**(b) 根拠**

- lower A exact diff: [s8b_ratified_freeze.py:1189–1211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189)
- candidate/user trailer分離: [537–572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:537)
- activation head literal: [env_contract.py:373–379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:373)

**(c) 検査構成**

lower GとAを同一commitにするとtrailerまたは`generation-approval-same-commit`で落ちる。serialを進める現行経路にはliteral変更が必要である。

**(d) 判定**

**refuted**。誤りだったのはbrief P2の「したがってliteral除去必須」という一般化であり、本文§6はこれを訂正している。

**(e) 区分**

**nit（修正不要）**

---

### F-2 — core結合fieldがすべて架空、という疑い

**(a) 主張**

`activation_serial`、state hash、active generation、freeze generationを検査した。

**(b) 根拠**

それぞれ [activation schema](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:17)、[ActiveContract](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:38)、[freeze v2 schema](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:100) に実在する。

**(c) 検査構成**

実recordのexact key集合と本文§3/§7.3を照合した。上記core fieldは一致した。

**(d) 判定**

**refuted**。架空なのはR-5で限定したcandidate metadataである。

**(e) 区分**

**nit（修正不要）**

---

### F-3 — versionedな新pathも履歴不変条件で必ず落ちる、という疑い

**(a) 主張**

過去に存在しない新pathの一度きり追加が拒否されるか検査した。

**(b) 根拠**

履歴条件は各commitのentryが`absent`またはHEAD OIDであることだけを要求する: [s8b_ratified_freeze.py:469–494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:469)。

**(c) 検査構成**

未使用のversioned pathを一度追加すれば、過去はすべてabsent、導入後は同一OIDとなる。落ちるのは同一pathに別bytesが現れた場合である。

**(d) 判定**

**refuted**

**(e) 区分**

**nit（修正不要）**

---

### F-4 — `new env + old floor` の拒否条件が存在しない、という疑い

**(a) 主張**

現行live admissionにcross-pair拒否があるか検査した。

**(b) 根拠**

protocolの記録hashとresolverが返すcontract hashを一致させる: [s8b_floor_campaign.py:349–369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:349)。ratified launchもcurrent contractだけを許す: [s8b_ratified_freeze.py:2769–2780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:2769)。

**(c) 検査構成**

currentをg2にし、g1 contract hashを焼いたprotocolを渡すとhash不一致で拒否される。

**(d) 判定**

**refuted**。ただし上位bundle自身のcross-pair verifierは未実装である。

**(e) 区分**

**nit（修正不要）**

---

### F-5 — authority precedenceの追記が入っていない、という疑い

**(a) 主張**

段3 A-R9/B-8が最終文書で取りこぼされたか検査した。

**(b) 根拠**

本体は上位/下位を分離し、lower pointer単独解決を禁止する: [本体 §1:27–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:27)。freeze文書にも同じprecedenceが追記された: [freeze-permanent-design.md:15–20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:15)。

**(c) 検査構成**

旧freeze文書だけを正本として読む経路を確認したが、冒頭で上位文書へ明示的に転送される。

**(d) 判定**

**refuted**。consumer cutoverの機械保証不足は別件R-4/R-6である。

**(e) 区分**

**nit（修正不要）**

---

### F-6 — 先送り3件がすでに一方へ全面裁定された、という疑い

**(a) 主張**

S1/S2、G-a/b/c、副作用境界そのものが確定済みか検査した。

**(b) 根拠**

[§8:189–214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:189) と [§12:285–303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:285) は分岐を未裁定として残し、unresolved profileのXを拒否する。

**(c) 検査構成**

S1/S2いずれか、G-b、機械的副作用検査を既定として確定する文は無かった。追加裁定A/Bの先食いはR-7だが、元の三択全体を一方へ倒したものではない。追加Cのsource pinと長寿命processも§6・§8-4・Q4へ分離されている。

**(d) 判定**

**refuted**

**(e) 区分**

**nit（修正不要）**

---

### F-7 — 現waveがすでにg2を活性化または旧branchをmergeした、という疑い

**(a) 主張**

文書作成によって現権限が変化したか検査した。

**(b) 根拠**

現activation recordはserial 1だけである: [00000001.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activations/00000001.json:1)。`output/s8b-freeze` にv2 generation/approval/active recordは0件だった。本体も旧branchをmerge/cherry-pickしないとする: [§14:322–336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:322)。

Git ancestry上、旧branchと現HEADはいずれも相手のancestorではなかった。

**(c) 検査構成**

現loaderはserial 1を返し、lower v2 resolverは`no-active`のままである。旧branchのmergeは成立していない。cherry-pickの完全な不存在はancestryだけでは証明できないため**未確認**だが、レビュー対象文書にその手順は無い。

**(d) 判定**

g2活性化とmergeの疑いは **refuted**。cherry-pick不存在の履歴全体証明は**未確認**。

**(e) 区分**

**nit（修正不要）**

## 総括

最も重い3件は次のとおり。

1. **B→Qの順序と「Q hashをB digestへ入れる」が循環し、Q semanticsも無いため、偽のpass receiptを束縛するだけで承認できる。**
2. **§5の1-path XとE-1の3-path Xが両立せず、現行コードには上位B/Q/A/Xを意味のあるcommitとして構成する検査面が存在しない。**
3. **§10の完了表と§7.2の不変条件がreject-all・装飾field・隠しgeneration参照を落とせず、§11は未実装のbundle-ID拒否を「既存の保存対象」と偽記載している。**

**GO / NO-GO: NO-GO。** 現状の文書を「第1設計段の確定制約」として後続実装waveへ渡すと、実装者は正当なbundleを構成できないか、偽Q・未承認generation・bundle非束縛成果物のいずれかを受理する。