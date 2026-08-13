## 所見

### R-A1

- 対象 file:line: `orchestrator/campaign/s8b_floor_campaign.py:1531`, `:2221`, `:2290`, `:2554`, `:3798`
- 主張: live の store、portable、resume、floor 実測直前は current policy だけを渡し、receipt の `source.ccbench_commit` と `subject.contract_sha256` を実行中 protocol へ束縛していない。oracle の `s8b_oracle_driver.py:949-957` では両値を照合するが、floor 測定後なので遅い。
- 素通り入力または再現手順: 同じ cell、binding、binary bytes を異なる contract で発行した正当な receipt を用意する。protocol A の resume manifest に contract B の receipt を差し替え、manifest と journal の通常の SHA を再構築する。tuple と binary SHA は同じため floor 側の全 validator を通り、実測まで到達する。ccbench pin だけが異なる場合も同様。
- 成果物影響: protocol A の floor 測定値と `result.json` に、contract B または別 pin を主張する receipt が載る。後段の holdout、ratified、oracle は拒否するが、裁定が要求した floor 測定直前までの連続束縛と floor artifact の受理集合が破れる。
- 重大度: blocker

### R-A2

- 対象 file:line: `orchestrator/campaign/s8b_binary_admission.py:263-267`, `orchestrator/campaign/s8b_ratified_freeze.py:1651-1738`, `:3020-3027`
- 主張: historical reverify は current policy を要求しないだけでなく、全 cell が同一の記録 policy に属することも検査しない。裁定の「cross-cell 整合」より緩い。
- 素通り入力または再現手順: 同じ recorded protocol、pin、contract の下で、旧 policy 発行の receipt と後継 policy 発行の receipt を cell ごとに混在させる。各 outer SHA、subject、binding は正当でも、`expected_policy=None` の個別検査しかないため混在を拒否する比較が存在しない。
- 成果物影響: production producer が一つの `BuildRunContext` から生成できない混成 freeze が `ReverifiedFreeze` として受理され、historical report／judge が参照できる集合へ入る。
- 重大度: must-fix

### R-A3

- 対象 file:line: `orchestrator/campaign/s8b_floor_campaign.py:2212-2254`, `:1550-1584`, `orchestrator/tests/test_s8b_floor_campaign.py:5332-5343`
- 主張: `store_binaries` の全件 preflight は admission と bytes だけで、runtime record 全体を検査していない。`cell_id`、`cached`、`bin_hash_short`、argv、未知／欠落 key などは書込み後の portable projection まで残る。
- 素通り入力または再現手順: 正当な receipt と binary を持つ最後の record の `cached` を文字列へ変える。validator はこの field を読まないため preflight を通り、store bytes と `store_path` が書かれる。その後 `project_built_records()` の `_validate_portable_built()` が拒否する。追加 key や record 側 `cell_id` 不一致でも同型になる。
- 成果物影響: campaign が record 不正で失敗しても `store/<sha256>` と record の `store_path` が残り、F-B8 が防ぐと裁定した stale store を作る。追加テストは receipt が `None` の場合しか覆わず、この経路を検出しない。
- 重大度: must-fix

### R-A4

- 対象 file:line: `orchestrator/campaign/s8b_floor_campaign.py:1507-1508`, `orchestrator/campaign/s8b_binary_admission.py:241-243`, `orchestrator/tests/test_s8b_floor_campaign.py:5325-5329`
- 主張: M1 は単独変異として成立しない。`PORTABLE_BUILT_KEYS` から key を除いても、次の validator が `record.get("admission_receipt")` で同じ欠落を拒否する。
- 素通り入力または再現手順: 事前登録どおり定数から `admission_receipt` を除き、同 key のない record を渡す。exact-key は通るが、直後に「無い/空」で拒否される。テストは `"exact key"` という診断文字列だけが変わるため赤になる。
- 成果物影響: 変異前後で key 欠落 record の受理集合は変わらない。M1 の赤は診断感度だけで、exact-key gate の独立検出力を証明しない。
- 重大度: nit

### R-A5

- 対象 file:line: `orchestrator/campaign/s8b_binary_admission.py:295-297`, `orchestrator/campaign/s8b_oracle_driver.py:973-981`, `orchestrator/tests/test_s8b_oracle_driver.py:4521-4551`
- 主張: M5 の `actual == receipt subject` は、validator の `subject == record` と既存の `actual == record` から従う冗長条件であり、単独削除しても受理集合は変わらない。
- 素通り入力または再現手順: `s8b_oracle_driver.py:978-982` だけを削除する。正規の validator が返す全入力では残る二条件が同じ差し替えを拒否する。追加テストは検証済み戻り値を monkeypatch 後に破壊し、production validator の事後条件を満たさない値を注入している。
- 成果物影響: 単独変異前後で実 artifact の受理集合は不変。テストの赤は実在入力に対する fail-closed 変化ではなく、契約違反 mock への診断感度に留まる。
- 重大度: nit

## 裁定との突き合わせ

- root 非依存の派生 receipt、`source_root` のみの除外、canonical outer SHA: 従っている。
- 発行時の sealed `BuildAdmission` 完全検証と binary bytes 再 hash: 従っている。
- live current policy の独立 resolver: 従っている。artifact 内 policy を current expected に使う恒真検査はない。
- live の保存から floor 実測直前までの retained field 束縛: 逸脱している。pin と contract の外部照合が抜けている。
- historical で current policy を要求しない経路分離: 従っており、live への `None` 漏れも見当たらない。
- historical の cross-cell 整合: 逸脱している。policy の cell 間一意性がない。
- (a-1)、(a-2)、(b)、(c)、(d) の通常入力拒否: 現行コードではすべて発火する。ただし M1 と M5 の独立帰属は成立しない。
- store の「全 record を一 byte 書く前に preflight」: 逸脱している。admission 外の record 不正が書込み後まで残る。
- `verify_floor_artifact` への新必須引数なし、freeze entry 権威を ratified／holdout に残す縮小形: 従っている。ただし historical policy の cross-cell 検査は不足する。
- holdout、ratified live、oracle 実走直前の pin／contract／cell／binding 検査: 従っている。
- `buildcache.py`、oracle report／judge、tracked freeze、V1 trust root 非接触: `git status` と全差分上は従っている。
- production issuer 由来 fixture と literal golden 更新: 従っている。skip、xfail、期待値反転は見当たらないが、M1 と M5 のテスト設計は帰属要件を満たさない。
- 保証名を暗号学的証明ではなく連続束縛へ限定する記述: 従っている。

## 変異帰属の再検査

- M1: 不成立。exact-key 変更後も missing gate が同じ入力を拒否し、期待テストの赤はエラー文の変化だけ。
- M2: 条件付きで成立。key は実在するため exact-key は先取りしない。ただし単なる `raise` 削除では後続の Mapping／exact receipt 検査が拒否するため、事前登録どおり明示的な受理反転でなければならない。
- M3: 成立。validator 単体および bytes を読まない floor／freeze consumer では、`subject.binary_sha256 == record.binary_sha256` が対象不一致の実効条件になる。
- M4: 成立。同一 binary、source、entry、binding で cell／holdout だけを変えた入力なら、評価順上 tuple equality より前の検査は先取りしない。
- M5: 不成立。`actual == record` と `subject == record` が残るため対象条件は論理的に冗長で、追加テストは validator の事後条件を mock で破っている。

## 総括

blocker 1 件、must-fix 2 件、mutation 帰属上の nit 2 件を検出した。  
live floor 経路では receipt の contract と ccbench pin が protocol に束縛されていない。  
historical 経路は current policy 非依存という裁定には従うが、異なる policy の cell 混成も受理する。  
store の全件 preflight は record 全体を覆わず、拒否後に stale store bytes を残せる。  
(a-1)、(a-2)、(b)、(c)、(d) の通常拒否自体は静的に確認できた。  
ただし M1 は後段 missing gate に先取りされ、M5 は二つの残存 equality により冗長である。  
M1 と M5 を KILLED と記録してはならず、実効 gate への再照準または冗長 gate としての再分類が必要である。  
pytest は指示どおり一件も実走しておらず、緑とは判定していない。  
現差分はこのまま land 可能とは判定しない。