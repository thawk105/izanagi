静的検査のみ実施した。pytest と Web 検索は未実施。`DW-S03` に従い、段 2 プランだけでなく親 brief と実測の一般化も攻撃対象にした。

### fail-open 経路

[B] weak P1 は 2 wave で突破できる

具体的な手順は次のとおり。

1. Wave A で `tools/acceptance_red_registry.json` に将来壊す exact nodeid を追加し、AI が `docs/spool/decisions/` と `docs/spool/worklog/` に整合する参照を書く。期間、5件 cap、canonical JSON は守る。
2. Wave A の checker は旧 `tested_main` を読むため新 entry を使わない。child-green で land すれば、entry と AI 作成の参照が次の main に入る。
3. weak P1 なら `git update-ref refs/remotes/origin/main <Wave-A-land後のmain>` とする。push は不要で、registry blob と台帳参照が同じローカル snapshot に揃う。
4. Wave B でその nodeid を落とす変更を入れる。tested main 単独再走は当然 rc=0、既存 entry により `ratified-known-red` となり、wait と land が通す。

再現/影響: AI だけで「事前登録→ローカル origin 偽装→自分が壊した赤の救済」が成立する。`tested_main` 束縛は同一 wave の後付けしか防がず、任意 nodeid の二段階登録を防がない。

[B] registry のデータを main に束縛しても、解釈器が wave tip なので同一 wave の逃がし道が残る

[s2-plan.md:128](/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1116-known-red-registry/s2-plan.md:128) は loader を `tested_tip` に束縛し、wait/land はその blob identity を照合するだけである。Wave B で新 loader を「空 registry から特定 nodeid の active entry を合成する」実装へ変えて commit すれば、tip blob との一致はむしろ成功する。wait と land は registry を独立に parse しないため矛盾を検出できない。

再現/影響: registry JSON を一切変更せず同一 wave で自己救済できる。署名を追加しても、署名 verifier と公開鍵を同じ wave が変更できるなら同型の突破が残る。

### D316 の三理由

[B] D316 の却下理由は 3 件とも潰せていない

| 理由 | 判定 |
|---|---|
| 赤を残したまま迂回する | **潰せていない。** registry の機能そのものが、赤を修正せず land する例外である。最新裁定で明示的に supersede はできるが、「設計で潰した」とは言えない。 |
| 集合が伸び続け恒久化する | **潰せていない。** 5件 cap は snapshot 上限にすぎない。期限切れ entry の削除・別 nodeid への交換・同一 nodeid の30日ごとの再批准を禁止していない。さらに acceptance receipt は `checked_on` を land へ投影しないため、期限前に作った receipt を main/tip 不変のまま期限後に land できる。 |
| field を書くのは AI 自身 | **潰せていない。** D/worklog、registry、local remote-tracking ref、HEAD pin はすべて AI が作成または移動できる。`_PINNED_GUARD_PATHS` は承認境界ではない。 |

再現/影響: brief の「3点を設計で潰せなければ実装せず裁定へ返す」という停止条件が成立する。現 scope のまま段 5 へ進めない。

### I1〜I7

[B] brief の不変条件には矛盾と不足がある

| 条件 | 静的判定 |
|---|---|
| I1 | 分類表は rc=1 を `non-attributable` に保つので概ね成立。ただし ratified と rc=1 の混在時にも、rc=1 nodeid が従来どおり `red_nodeids` に残ることを明文化すべき。 |
| I2 | **誤り。** 「無い・空・読めないが今日と同一」と「読めないなら rc=2」が矛盾する。また空 registry でも rc=1 は non-attributable であり「全件 attributable」ではない。正しくは「不存在または valid-empty は既存分類を保存、存在するが読取不能・不正なら probe 前に rc=2」。 |
| I3 | registry blob についてのみ成立。loader/checker/wait/land の意味論が tip 制御なので、批准判断全体は main に束縛されていない。 |
| I4 | exact membership の設計は正しい。`startswith` 変異を downstream が独立検出しないため、この一箇所が実効防壁になる。 |
| I5 | loader の全例外を `InvalidInput` へ正規化し、probe 前に読むなら成立。現時点では未実装なので保証ではなく計画である。 |
| I6 | **不成立。** nodeid と SHA は receipt に出るが、land は nodeid が registry の active exact entry だったことや land 時点の期限を独立検査しない。 |
| I7 | CLI/env の字面は満たすが不足。二段階 wave、mutable ref、wave-tip verifier が同等の迂回路として残る。 |

再現/影響: I2 を文字どおり実装すると不存在と読取不能を混同するか、既存 non-attributable 経路を過剰拒否する。I3/I6/I7 の穴は land を通す側に偏る。

[M] bootstrap の receipt nullability が相互矛盾している

checker receipt は「救済 0 件なら `origin_main=null`」とする一方、[s2-plan.md:150](/work/1/SFC/tanab/dev-wave-jobs/2026-08-15_t1116-known-red-registry/s2-plan.md:150) は全 red verdict で registry/origin blob の一致を要求している。不在 registry かつ全 node が rc=1 の `non-attributable-only` では、前者は null、後者は非 null を要求するよう読める。

再現/影響: 実装解釈によって、従来通っていた非帰属赤を bootstrap 中に拒否するか、ratified verdict でも null 証拠を許す。verdict × registry 存否 × ratified 有無の exact matrix が必要。

### 五層の閉包

[B] 五層は名目上 scope に出るが、実効閉包になっていない

| 層 | 状態 | 残る穴 |
|---|---|---|
| checker | scope 内 | wave-tip の checker/loader が批准意味論を変更できる。 |
| 待ち手 receipt | scope 内 | SHA と集合整合は見るが registry membership を独立に再計算しない。 |
| land | 部分的 | identity の照合だけで、registry parse、entry membership、land 時 expiry を検査しない。 |
| registry loader | scope 内 | executable blob の権威が `tested_tip`。 |
| Codex guard | **実効 scope 外** | `_PINNED_GUARD_PATHS` は working bytes と HEAD blob の一致検査にすぎない。[hooks/README.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/hooks/README.md:84) も独立 trust root ではないと明記している。`guard_write` の拒否対象は [guard_write.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/hooks/guard_write.py:154) の `hooks/` 等で、registry は含まれない。 |

再現/影響: worker 起動前に pin が通った後、その worker が registry/loader を編集し、親が commit すれば次回 pin は再び緑になる。承認や書込禁止の証明にはならない。

裁定パッケージへ返すべき scope は、外部 trust root、entry 更新・更新延長・失効手続、base-pinned verifier、land 時の独立 membership/expiry 検証である。

### 恒真・テスト面

[M] 計画されたテストには「自分自身の定数を検査するだけ」の穴がある

- `test_pinned_guard_paths_are_exact_and_independent_of_copy_paths` は tuple への追加しか検査せず、その path への書込み拒否を一度も試さない。live hook probe の protected target も registry ではなく campaign `runs/` である。
- land fixture は `LAND._ACCEPTANCE_RECEIPT_SCHEMA` を使って synthetic receipt を作るため、consumer 単体は通っても wait producer との wire 不一致を隠せる。
- 新 ratified 経路の real checker→wait→land E2E が追加テスト一覧にない。
- negative corpus は、各不正入力が valid nonempty entry から一要素だけ変えた fixture でなければ、全 nonempty registry を拒否する欠陥でも緑になる。
- `test_codex_worker_launch.py::_prepare_authority_repo` は現行6 pathを hard-code しており、新しい pin 2 path の fixture 更新がプランから漏れている。

再現/影響: 各層の unit test が緑でも、新 status の producer/consumer 接続や実際の書込み防止が一度も発火しないままになり得る。

### 事前登録変異

[M] 6候補の静的な単一理由性は次のとおり

| 変異 | 判定と再現/影響 |
|---|---|
| `tested_main→wave_tip` | 指定 checker test は divergent tree fixture なら落ちる見込み。ただし wait/land の tested-main blob 照合が production では mask するため、DW-M01 の end-to-end 実効変異ではない。 |
| expiry inactive 化削除 | 指定 expiry test が単独で落ちる設計にできる。現コード未存在で「削除する1行」が非一意なので、predicate の exact 置換を先に固定する必要がある。 |
| loader error→empty | 指定 malformed testが落ちる。全 probe が rc=1 なら malformed registry を隠して `non-attributable-only` が land まで通るため、実効 fail-open 変異として妥当。 |
| exact→`startswith` | 指定 prefix testが落ち、downstream は整合した偽分類を検出できない。prefix 側だけが valid entryで、exact entry は不存在という単一差分 fixtureなら妥当。 |
| wait の `entries_used` equality削除 | production checker は常に整合 receipt を出すので通常走では変化しない。偽 checker receipt を trust-boundary input と定義するなら有効だが、umbrella testではなく mismatch caseの exact parameter nodeidが必要。 |
| land の空 ratified 許可 | wait producer が先に空集合を拒否するため通常 production では mask される。偽 acceptance receipt を land の攻撃入力とする旨を明示するか、paired mutationへ変更すべき。 |

再現/影響: 現表のまま「指定テストだけが落ちた」と一般化できるのは実装前には 0 件である。特に中核 P1 の origin blob equality 削除、land-time expiry 削除、authority verifier bypass の変異が事前登録されていない。

### N1〜N4 の一般化

[M] 親の観測値と、そこから導いた保証が混ざっている

| 事実 | 静的評価 |
|---|---|
| N1 | D316 は W1 waiver、D371 は registry の明示却下であり、同一機構の独立2例とは限らない。過去却下の存在自体は正しい。 |
| N2 | v3 receipt に `red_nodeids` があり land が形を検査する事実は正しい。「純増は区別 fieldだけ」は、membership・expiry・authority の land 再検証を落としている。 |
| N3 | **誤り。** pinned だから Codex 子が書けない、は成立しない。[check_codex_hooks.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-known-red-registry/tools/check_codex_hooks.py:306) は HEAD blobとの一致を検査するだけである。 |
| N4 | probe が tested main に作られることと、現 main に registry がないことは事実。「自然に fail-closed」「1 bit 不変」は未実装コードへの一般化であり、schema bytesは確実に変わる。 |

再現/影響: N3/N4 を保証として採用すると、最重要の authority 境界を存在しない Codex write guard と将来コードへ委ねることになる。

### NO-GO 自体への攻撃

[M] 「同じ wave が後から自分を救えない」という限定解釈は成立し得るが、別裁定が必要

この限定語義だけなら暗号署名なしでも構造化できる。最低条件は次である。

- acceptance lease 取得時の main commitから registryを読み、main不変を landまでCAS検査する。
- registry変更 waveは registryを一切利用できず、child-greenのみで landし、entryは次 waveから有効にする。
- consuming waveは checker/wait/land/loaderを変更できないか、実行体を固定 mainまたは外部 digestへ束縛する。
- landが registryを独立 parseし、exact membership、現在時刻のexpiry、履歴上の更新・再登録上限を再検査する。

再現/影響: これでも AI による Wave A→Wave B の事前登録は防げず、人間批准は証明しない。したがって「批准済み」を「target waveより前からmainに存在」と明示的に再定義するユーザー裁定がある場合だけ成立する。

[B] D31 の prompt 規律を P1 の根拠にはできない

D31 はコンテキスト衛生や作業運用を prompt 規律に置く一方、破られても正しさは既存の機械 gate が守るという判断である。今回はその正しさ gate 自身の受理集合を広げ、直接拘束も「機械が確認できる形」と指定されている。

再現/影響: D31 を優先すると、D316(iii) が退けた「AIが authority fieldを書く」状態へそのまま戻る。直接の最新拘束と絶対規律2が優先する。

[B] NO-GO は現 scope について正しいが、「署名を足せば十分」は甘い

真の最小要件は秘密鍵方式そのものではなく、AIが変更できない承認 trust rootである。ユーザー所有の署名、OS権限で保護された外部 attestation、外部承認サービスはいずれも候補になる。一方、公開鍵、verifier、land判定を wave tip が交換できるなら entry署名だけ追加しても無効化できる。

再現/影響: 攻撃 wave が公開鍵を自分の鍵へ差し替えるか verifier を常時成功へ変え、tip blob identityを整合させれば landできる。再 brief では外部 pin、verifier実行体の権威、鍵 rotation/revocation、署名payloadのdomain separationまで scopeに含める必要がある。

## 総括

**NO-GO**

- P1 は現 scope では成立せず、D316 の三理由はいずれも潰せていない。
- weak P1 は registry追加 waveと破壊 waveの二段階、およびローカル `update-ref` で突破できる。
- さらに wave-tip loader/verifier により、registryを変更しない同一 wave の自己救済も可能である。
- I2 は自己矛盾し、I3・I6・I7 は批准判断全体を閉じていない。
- checker／wait／land／loaderは scopeにあるが、landの独立検証と実効Codex guardが欠ける。
- 構造的な「同一 wave 救済禁止」へ意味を縮めるなら、新しい明示裁定が必要である。
- 推奨は実装せず段4へ返し、外部 trust rootとbase-pinned verifierを含めてrebriefすること。
- pytestは指示どおり実行しておらず、緑は主張しない。