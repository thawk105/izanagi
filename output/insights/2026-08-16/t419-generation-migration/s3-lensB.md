```text
## 判定 (GO / NO-GO): NO-GO

活性化単独では、g2 floor protocol の発行入口と既存 silo 証拠の公開再検証入口が閉じたままになる。seam と復旧条件を先に land すべきである。

## 所見

### B-01 / g2 floor protocol 発行が循環で詰まる

主張: g2 活性化後、現行の official 経路では g2 protocol を発行して floor v2 を開始できない。

証拠: builder は current lookup と current validation を使う (`orchestrator/campaign/s8b_floor_campaign.py:629-659`)。しかし freeze 先は既存の `output/s8b-freeze/floor_protocol.json` 固定 (`:746-794`) で、writer は create-only (`:686-722`)。実凍結領域への任意 path 書込みも拒否される (`:725-743`)。admission は旧 path 固定 (`orchestrator/campaign/certified_writer_admission.py:206-214`)、PBS wrapper も旧 path 固定 (`tools/pegasus/floor_campaign.sh:947-965`)。

成果物影響: g2 の床値再測定、selector seal、certified campaign が到達不能になる。

推奨: versioned protocol path、raw hash、bundle hash を receipt、admission、wrapper、driver 全てへ通してから activation する。path と approval authority は activation 前に新決定で固定する。

### B-02 / silo の完全な歴史検証入口が current binding で壊れる

主張: g1 の silo frozen bytes は保持されても、公開 `verify-result` は g2 活性化後に g1 artifact を歴史検証できない。

証拠: frozen silo は g1 contract hash を記録している (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:12,570`)。`validate_current_bindings` は常に `lookup("pegasus")` の current calibration/hash と比較する (`orchestrator/campaign/silo_ladder_rung1.py:3541-3572`)。CLI の `verify-result` も `validate_evidence` 後に必ず current binding を実行する (`:4857-4865`)。

成果物影響: silo proof chain は bytes を失わなくても、通常の完全検証入口からは `current calibration/pin binding mismatch` になる。

推奨: 記録 hash を使う historical verifier と、current eligibility を検査する live verifier を公開 API と CLI で分離する。

### B-03 / campaign identity と receipt の世代束縛が不完全

主張: v2 campaign lock には hash があるが、全入口の campaign identity には `environment_contract_sha256` が必須化されていない。

証拠: floor submit receipt の top-level keys に protocol path/hash がない (`tools/pegasus/submit_floor.sh:353-368,475-485`、`orchestrator/campaign/certified_writer_admission.py:27-31`)。T126 control protocol も env hash を持たず (`orchestrator/qualification/t126_control_v1.json:7-14`)、admission は current registry の意味フィールドだけを比較する (`certified_writer_admission.py:344-382`)。oracle の legacy manifest は `run_contract` が無ければ receipt 検査を省略する (`s8b_oracle_report.py:1257-1271`)、WAL の legacy lock も hash が無ければ戻る (`wal.py:1040-1062`)。

成果物影響: 同じ `pegasus` tag の g1/g2 が旧 WAL、layout、qualification identity を共有し、混成世代を検出できない入口が残る。

推奨: legacy を current admission に昇格させず、全新規 receipt と campaign preimage に contract hash と activation receipt を必須化する。

### B-04 / activation record は正規経路で巻き戻せない

主張: record だけ、head だけ、または誤った serial 2 を land すると authority 全体が fail-closed になり、通常の issue tool では復旧できない。

証拠: record は一時 file を hard-link no-replace で publish する (`tools/issue_env_contract_activation.py:45-140`)。loader は全 record の連番、predecessor、terminal serial、terminal hash を exact 検査する (`env_contract_activation.py:365-416`)。authority load が失敗すると current registry も作られない (`env_contract.py:519-545`)。発行 tool 自体が最初に `current_activation_state()` を読む (`issue_env_contract_activation.py:178-212`)。

成果物影響: head と record の片側だけの commit は再起動後に全 current authority を停止し、誤った record の削除や上書きは chain 規約を破壊する。

推奨: record と head の同一 commit に加え、land 前の full-chain 検査、誤 record の forward fix 方針、未発行状態の abort 手順を明文化する。

### B-05 / 一部の移行テストが production 自己参照になる

主張: proposed positive tests の一部は production registry が誤っていても、同じ誤値を期待値として採用して緑になり得る。

証拠: serial 2 fixture は `ec.GENERATIONS` から hash を組み立てる (`orchestrator/tests/test_env_contract_activation.py:275-295`)、その結果を同じ production `GENERATIONS` と比較する (`:1564-1571`)。g2 resolver positive 化の対象も production hash を直接読む (`orchestrator/tests/test_env_contract.py:618-621`)。plan 自身も g1 golden で `GENERATIONS[0]` 参照を指定している (`s2-plan.md:283`)。

成果物影響: registry、activation record、期待 hash が同時に同じ誤値へ動いた場合、移行の実体と bytes pin を独立に検出できない。

推奨: g1/g2 hash、serial 2 canonical bytes、active rows、state hash を production 外の literal または独立計算入力で固定する。

### B-06 / 親 brief の焦点走は静的には再現不能

主張: brief の (8) の rc=1、赤 9 件、2 file 限定、attestation 全緑は親の一時変異実測にのみ依存する。

証拠: brief は一時変異の実測として記録している (`brief.md:54-69`)。plan も pytest 未実行と明記している (`s2-plan.md:293-301`)。コードから g1 固定テストが赤になる理由は導けるが、rc、件数、他 file の緑までは導けない。

成果物影響: このレビューで blast radius の件数を独立確認済みとして扱えない。

推奨: 実装後に許可された test runner で再測定し、親の 9 件を静的結論と分離して記録する。

### B-07 / T-478 の (a)〜(e) 現況

主張: T-478 の五要素は未実装または部分実装であり、特に (d) は本移行を直接阻む。

証拠: 推奨要件は README §4 の activation receipt、identity hash、versioned predicate、wrapper、独立検査 (`README.md:139-164`)。現況は次のとおり。

(a) 部分実装。activation-derived `REGISTRY` と `authorize` receipt はある (`env_contract.py:519-668`)。ただし floor、oracle、selector、silo の全入口が同じ receipt を受け取らない。阻害: activation 自体は阻まないが、安全な移行入口を阻む。

(b) 部分実装。campaign lock v2 authority には hash がある (`campaign_lock.py:19-25,161-189`)が、campaign preimage 自体は execution authority を覆わない (`ident.py:151-178`)。阻害: base activation は阻まないが、世代混成を防げない。

(c) 未実装。schema/formula はあるが predicate version dispatch と retention はない (`s8b_floor_contract.py:26-34`)。阻害: base activation は阻まないが、将来の歴史 verifier を不定にする。

(d) 未実装。wrapper、admission、driver は旧 protocol path 固定 (`floor_campaign.sh:29-95,947-965`、`certified_writer_admission.py:206-214`)。阻害: floor v2 移行を直接阻む。

(e) 部分実装。旧 frozen manifest は独立 key-set と literal hash を検査する (`test_frozen_artifacts.py:41-49,90-117,234-248`)が、activation bundle の独立 required-role と非空 cardinality 検査はない。阻害: base activation は阻まないが、bundle acceptance の恒真化を許す。

### B-08 / 順序判定

主張: seam 先が正しい。活性化先行は技術的に後から実装できるが、安全な中間状態ではない。

証拠: activation 後は旧 protocol が current validation で拒否される (`s8b_floor_campaign.py:465-535,4626`)、wrapper/admission も旧 path を読む。一方、seam は g1 active のまま current g1 protocol と temporary non-frozen path でテストできる (`s8b_floor_campaign.py:725-743`)。FROZEN_MANIFEST は旧 23 path の検査で、新 path の追加自体を全 repository で禁止してはいない (`test_frozen_artifacts.py:162-179,234-248`)。従って後から新 path を作ることは可能だが、旧 path の置換は不可能である。

成果物影響: 活性化先行では、既存受入面が赤くなり、g2 protocol 発行前に irreversible authority が main に入る。

推奨: versioned seam と独立 golden を先に land、次に record と head を同一 commit で活性化し、その後に human-approved g2 protocol を発行する。

## 親 brief の誤り

- P1 は「live g1 拒否」という意味論は正しいが、「後続段で floor v2 を測ればよい」を到達可能性まで含めて主張しており誤り。現行 producer、admission、wrapper に g2 発行 path がない。
- P3 の「silo evidence も歴史検証できる」は、公開 `verify-result` の current binding を見落としている。`validate_evidence` 単独の成功は proof chain 全体の成功ではない。
- (8) の 9 件という件数は親実測のみ。静的検査からは確認済みと扱えない。
- activation hash `398b...` は誤りではない。`canonical_record_bytes` が sort_keys、compact JSON、ASCII を使い (`env_contract_activation.py:113-127`)、`_state_sha256` が state hash 自身を除外する (`:130-133`)ため、親の入力から再計算した値と一致する。ただし serial 2 file 自体は現 worktree に存在しない。

## プランの誤り

- seam-first の順序自体は正しい。
- しかし `s2-plan.md:217` の「canonical path と approval authority 未確認」は実装前の停止条件であり、activation 後へ持ち越してはならない。
- P3 (`s2-plan.md:223-225`) は silo の完全な歴史検証入口を証明していない。
- §8 の golden 独立性は、production `GENERATIONS` を fixture と期待値の双方へ使う正例を残しており不十分。
- head と record の同一 commit (`s2-plan.md:262-268`) は片側不一致を防ぐが、誤った valid record の forward-only 性と復旧手順までは塞いでいない。

## 攻撃したが崩せなかったもの

- g1 floor protocol の historical resolver は `resolve_by_contract_sha256` と `ever_active` を使うため、current reject とは分離されている (`s8b_floor_campaign.py:446-462,538-543`、`env_contract.py:671-703`)。
- live admission が g1 protocol を拒否すること自体は正しい fail-closed 縮小であり、predecessor 許容は不要である。
- activation record の canonical JSON、末尾 LF、連番、predecessor、head hash 検査は強い (`env_contract_activation.py:167-185,332-416`)。
- v2 campaign lock、reflux source closure、autonomous trial completeness は歴史 contract hash を保持する経路がある (`campaign_lock.py:19-25`、`reflux_source_closure.py:60-90,503-508`、`autonomous_trial_completeness.py:261-275`)。
- 既知例外テストは active entry 数と required entry 数を確認し、synthetic 異常標本も使うため、空集合だけの恒真テストではない (`test_env_contract.py:846-881`)。
- g1/g2 contract hash の独立計算 golden と旧 FROZEN_MANIFEST の literal pin は、現在の形では有効な防壁である (`test_env_contract.py:1124-1153`、`test_frozen_artifacts.py:41-49`)。
```

## 総括

NO-GO。活性化先行では g2 protocol 発行が到達不能になる。  
g1 floor の歴史 resolver は生きるが、silo の完全検証入口は current binding で壊れる。  
floor receipt、T126、legacy oracle/WAL の世代束縛も未閉包である。  
record と head は create-only かつ forward-only で、誤発行の巻き戻し手段がない。  
398b の state hash は実装式から再計算して一致した。  
順序は seam、activation、human-approved g2 artifact の順で固定すべきである。  
pytest と親の焦点走は実行していない。