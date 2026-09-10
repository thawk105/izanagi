## 規則案の比較と推奨

| 案 | 値盲性 | 主な迂回 | D1124 | 新規機構 |
|---|---|---|---|---|
| A. 同一 full `protocol_sha256` の適格 result のうち最小 `run_id` | `run_id` は official path と launch certificate の起動時刻で測定値より先に決まる。資格判定以外では floor 数値を読まない | より早い result の削除・列挙外化。candidate を経由しない g1。`floor_source=A` のまま `generation.floor=B` とする投影差し替え | 両立する。何回測ってもよいが、最初の適格 run だけが強い主張に使える | 0。既存 path、validator、Git tree、generator source を利用 |
| B. 最初に発行された launch certificate の run 固定 | 最も強い。成否や資格判定も見る前に決まる | certificate の削除・列挙外化 | 測定反復は可能だが、最初の run が不適格なら同 protocol の強い主張を永久に回復できない | 0 |
| C. 最新 eligible、または certificate hash 最小 | 各 identity 自体は値盲 | 値を見ながら run を追加し、望ましい identity が勝つまで停止時刻を選べる | 不適合。反復自由が best-of-N 攻撃に変わる | 0 |

推奨は案 A、版名は `earliest-eligible-official-run-id/v1` とする。`s8b_launch_cert.py:147-179` の canonical `run_id` をそのまま比較し、full protocol hash の一致を資格検査で確認する。`proto8` だけの一致は collision を除外できないため選択集合に使わない。

案 B は安全側だが、途中死から測り直せるという D1124 の実用目的を失う。案 C は不採用である。

案 Aでも、単に `floor_source.path` を検査するだけでは不十分である。直接作った g1 が最小 run A を `floor_source` に置きながら、`generation.floor` を B からコピーできる。したがって、選択 identity と `result.floors` からの投影 equality は同じ変更単位で閉じる。

## enumeration の権威と TOCTOU

candidate 生成時と批准時では権威を分ける。

- candidate 生成時の適格集合は worktree filesystem を権威にする。選択対象の result 自身がまだ G に導入されておらず、captured HEAD だけを列挙すると正常な selected result が集合から消える。これは `s8b_ratified_freeze.py:3408-3415` が selected result の introduction set を `{G}` と要求すること、および fixture が G で result と generation document を同時導入する `test_s8b_ratified_freeze.py:1120-1130` からも分かる。
- 批准時は captured activation HEAD `H` の Git tree を集合の正本にする。さらに official namespace の worktree 列挙と H tree の result path 集合を一致させ、untracked official result があれば `floor-selection-enumeration-dirty` で拒否する。これにより ratification 直行時に untracked A を無視できない。
- candidate 時の untracked result は選択集合に含める。ignored file による隠蔽を避けるため、`git ls-files --others --exclude-standard` だけに依存せず、`output/env/<env>/calibration/s8b-floor-official/` を `lstat` / `os.scandir(..., follow_symlinks=False)` で狭く列挙する。
- ratified 強い consumer の実行中に新しい untracked run がある場合は一時的に拒否する。測定自体は止めず、その run を provenance として commit した後に再検証する。これは観測回数制限ではない。

既存 primitive の使い分けは次のとおり。

- `_blob_at_head` (`s8b_holdout_freeze.py:319-330`): captured HEAD の protocol、generator source、批准時の official result blob の権威。filesystem 列挙には使わない。
- `_capture_regular_nofollow` (`:264-289`): candidate 時の result、manifest、journal、および worktree 側の同一 inode regular-file capture。
- `search_repository` (`:591-640`): 従来どおり未知性 scan と `_measurement_closure` (`:1640-1672`) 専用。内容 hit の検索器であり、official result identity の完全な列挙器にはしない。

TOCTOU 対応は以下を要求する。

1. official `result.json` path 集合を列挙して `S0` を固定する。
2. selected と、selected より小さい `run_id` の候補を nofollow capture して資格検査する。
3. result、sibling manifest、journal を検査後に再捕捉し、検査時 bytes と一致させる。
4. path 集合を再列挙して `S1 == S0` を要求する。
5. ratified 側はさらに H blob と worktree bytes を一致させる。

名前を変えずにファイル内容だけを検査途中で交換する race、または生成後に一度も記録されなかった run を削除する攻撃は、台帳を禁止した条件では完全には証明できない。これは後述の赤旗とする。

## 編集計画 (file:line)

### `orchestrator/campaign/s8b_holdout_freeze.py`

1. `:47-61` の v2 定数群に次を追加する。

   ```python
   FLOOR_SELECTION_RULE_VERSION = "earliest-eligible-official-run-id/v1"
   ```

   JSON、CLI、artifact には出さない。generator source の `generator.sha256` が既存経路 `:1731-1733` でこの宣言を含む bytes を束縛する。

2. `:249-330` の path/capture primitive の隣に、official namespace 専用の private 列挙関数を置く。

   - protocol の `env_tag` と `protocol_sha256[:8]` で namespace を狭める。
   - `parse_official_run_path()` (`s8b_launch_cert.py:147-179`) を唯一の path parser とする。
   - basename は `result.json` のみ。
   - directory、leaf、途中 component の symlink、非 regular file は拒否。
   - full `protocol_sha256` は result raw を strict parseして確認する。`proto8` 一致だけでは採用しない。
   - path 集合の前後一致を検査する。

3. `_validate_floor_inputs` (`:1348-1637`) は既存 gate の順序を維持する。

   - official path `:1392-1398`
   - protocol/full hash `:1429-1437`
   - binary receipt `:1470-1501`
   - manifest `:1504-1545`
   - journal `:1547-1593`
   - live admission・統計再計算 `:1594-1616`
   - `eligible_for_refreeze is True` `:1617-1618`
   - floor projection schema `:1620-1636`

   `:1620-1636` を private `_project_floor_for_freeze()` に切り出し、candidate と ratified verifier が同じ投影を使う。返り値には既存6要素に `path_info` を加え、再 parseや別の run-id 解釈を作らない。

   この関数自体では選択を再帰実行しない。従来の単一 result 資格 validator のまま保つ。

4. `_validate_floor_inputs` の直後に、selected より小さい `run_id` だけを調べる private selector を置く。

   - selected は呼出し前に全既存 gate を通過済みとする。
   - earlier result の full hash が異なる場合、同一 protocol 集合から除外。
   - `eligible_for_refreeze is False` は除外。
   - `True` を申告した earlier result は `_validate_floor_inputs` の全 gateを通す。失敗を「不適格だから無視」と丸めず、`floor-selection-eligibility-unverifiable` で fail-closed にする。
   - fully eligible な earlier result があれば最小 `run_id` の path を返す。

5. `build_v2_g1_candidate` の `_validate_floor_inputs` 呼出し直後 (`:1721-1725`) に equality を置く。`known_axes`、closure 構築、document projection (`:1726-1765`) より前に落とす。

   新しい candidate 側失敗署名:

   - 型: `FreezeError`
   - mismatch:

     ```text
     floor-selection-rule-mismatch: earliest-eligible-official-run-id/v1: selected_run_id=<B> required_run_id=<A>
     ```

   - path 集合変化:

     ```text
     floor-selection-enumeration-shifted: earliest-eligible-official-run-id/v1
     ```

   - earlier result の資格を安全に決定できない場合:

     ```text
     floor-selection-eligibility-unverifiable: <path>: <既存 reason>
     ```

   `floor_source` は引き続き `:1760-1763` で selected raw bytes を記録し、公開 CLI `:1881-1886` は変更しない。

### `orchestrator/campaign/s8b_ratified_freeze.py`

1. `_verify_generation_semantics` (`:981-1058`) の source blob 検査 `:1014-1022` で、frozen generator blob が上記版定数を exact 1 回持つことを確認する。新しい generation field は作らない。

2. closure artifact の G/H/worktree 束縛 `:1031-1052` の後、transition 検査 `:1054-1058` の前に g1 専用選択検査を置く。

   - H tree から official result path 集合を列挙。
   - worktree の official result path 集合と exact 一致を要求。
   - selected `floor_source.path` を既存資格 validatorへ通す。
   - earlier eligible result を同じ規則で再導出。
   - selected path と required path を equality 比較。
   - `_project_floor_for_freeze(selected_result)` と `document["floor"]` を canonical JSON bytes で比較。

   新しい構造化失敗:

   - `RatifiedFreezeError.reason == "floor-selection-rule-mismatch"`
   - `cause == "earliest-eligible-official-run-id/v1"`
   - untracked/tree 不一致は `reason == "floor-selection-enumeration-dirty"`
   - 資格不明は `reason == "floor-selection-eligibility-unverifiable"`
   - 投影不一致は `reason == "floor-source-projection-mismatch"`、`cause == "floor-source-projection"`

   これにより `load_ratified_freeze` の経路 `:1368-1378` へ直行しても検査を迂回できない。C07 の `verify_floor_bytes` は `load_ratified_freeze` だけを使うため、この位置が必要である。

3. `_launch_validate` の selected result full validation (`:3222-3269`) 後、既存 binding graph 構築 `:3271-3339` の直前にも同じ二つの equality を置く。

   - required `floor_source.path == result_path`
   - projected `result.floors == ratified.document["floor"]`

   これは caller が手作り `RatifiedFreeze` を渡して `load_ratified_freeze` を飛ばす test/private 経路への防御である。

4. `EQUALITY_CHAIN_ADJACENCY` (`:147-182`) 自体は変更しない。`docs/freeze-permanent-design.md:323-325` が旧 equality chain 不変を要求しているため、選択 equality は binding graph の直前に独立した狭い predicate として置く。

5. historical reverify では current policy を流用しない。`reverify_published_freeze` (`:3506-3515`) は既存どおり recorded contract と `expected_policy=None` の historical admission semanticsを使い、`launch_validate` は current policyを使う。これを実現するための `_validate_floor_inputs` 拡張は private な `historical=False` の一点に限定し、公開 validator framework にしない。

## 通る正例

既存の正例は `orchestrator/tests/test_s8b_holdout_freeze.py:1790-1846` の `test_v2_candidate_build_and_generate_synthetic_g1` である。

fixture は `orchestrator/tests/s8b_v2_freeze_fixture.py:348-493` で、次を満たす。

- official result は `:391-396` の `20260811T000000Z-<proto8>/result.json` 1件だけ。
- result、manifest、journal、admission evidence は `:396-460` で整合する。
- 全入力は `:485-486` で captured HEAD に commit 済み。
- `eligible_for_refreeze` は `:320-345` で bool `True`。
- selected が適格集合唯一の要素なので、最小 `run_id` は selected 自身。
- candidate の `floor` は同じ result の `floors` から投影される。

批准側では `test_s8b_ratified_verify.py:815-830` も、fixture の g1 floor projection を追随させれば同じ一要素規則で通る。

## 負例

以下はいずれも budget、official path、full protocol hash、manifest/journal/binary receipt、live admission、統計、eligibility を通す形にする。

1. candidate の later-run 選択

   - A: `.../20260811T000000Z-261cec1c/result.json`
   - B: `.../20260811T000100Z-261cec1c/result.json`
   - A/B は同一 full protocol で両方 fully eligible。
   - caller は B を `--floor-result` に渡す。
   - 現行 gate は B 単体を受理し、A は measurement closure に正しく入れれば candidate を生成できる。
   - 新規則だけが `selected=B, required=A` で拒否する。

2. 値が同じ A/B から B を選ぶ

   - A/B の `floors`、統計、binary receipt を byte-equivalent にし、run identity だけを変える。
   - 値比較をしていなくても identity rule 違反なので拒否する。
   - 既存 gate は両方とも通る。これにより検査が数値差へ誤って依存していないことも確認できる。

3. candidate を経由しない ratified g1

   - G に A/B の両 run artifactを含める。
   - g1 `floor_source` は later B、`floor` も B から正しく投影する。
   - approval、pointer、source hash、G/H/worktree、lineage を全て整合させる。
   - 現行 `load_ratified_freeze` は selection identity を検査しないため通る。
   - generation-semantics の新規則だけが B を拒否する。

4. source identity は Aだが、generation floor はB

   - `floor_source.path/sha256` は最小 run A。
   - `generation.floor` だけを fully valid な B の projection にする。
   - 現行 ratified validator は `generation.floor` と `floor_source.result.floors` を比較しない。
   - selection identity 検査は通り、追加する projection equality だけが拒否する。

無効な負例として、B の `protocol_sha256` 不一致、`eligible_for_refreeze=False`、manifest不一致、unofficial path は使わない。いずれも既存 gate が先に拒否するためである。

## pin 閉包と既存 test への影響

編集対象は次の閉包に限定する。

- production:
  - `orchestrator/campaign/s8b_holdout_freeze.py`
  - `orchestrator/campaign/s8b_ratified_freeze.py`
- fixture/test:
  - `orchestrator/tests/s8b_v2_freeze_fixture.py:348-493`
  - `orchestrator/tests/test_s8b_holdout_freeze.py:1790-1846`
  - `orchestrator/tests/test_s8b_ratified_freeze.py:940-1172`
  - `orchestrator/tests/test_s8b_ratified_verify.py:478-698,815-830`

批准 fixture は現在 `test_s8b_ratified_freeze.py:1100-1112` で `floor_source` を更新する一方、`floor` を result から更新していない。このまま projection equality を追加すると、同 helperを使う全 launch test が壊れる。期待値を緩めず、fixture g1 の `floor` を `result["floors"]` からproductionと同じ helperで構築して閉じる。

同じ追随が `test_s8b_ratified_verify.py:638-648` の独立 fixtureにも必要である。主な既存 call closure は次のとおり。

- `test_s8b_ratified_freeze.py:1411,1451,1493,1606,1679`
- `test_s8b_ratified_verify.py:757,817,834,844,857,877,939,979,1020,1229,1240,1278,1295,1312,1328,1381-1705,1943-2232,2323-2479`
- stub floor sourceを使う `test_s8b_ratified_freeze.py:2286-2294` は production-shaped `load_emitter_g1` fixtureへ追随させる。

これらは fixture の入力を正規形へ直すだけで、拒否 reason や期待値の緩和は不要である。緩和が必要になった場合は赤旗として停止する。

変更しない pin は次のとおり。

- `output/s8b-freeze/floor_protocol.json`: 18 key、SHA-256 `261cec1c...e74aac`
- `output/s8b-freeze/holdout_freeze.json`: SHA-256 `315b1eb8...bc688`
- protocol schema/constants: `s8b_floor_contract.py:29-64`
- official path grammarと `proto8`: `s8b_launch_cert.py:26-32,147-179`
- frozen pins: `test_frozen_artifacts.py:41-49,90-124,234-248`
- protocol path AST pin: `test_s8b_protocol_builder.py:1228-1248`
-旧 equality chain: `s8b_ratified_freeze.py:147-182`

`floor_protocol.json` を変えないため、test fixture、env reseal artifact、official path の `proto8=261cec1c` 束縛の再 seal は不要である。

`check_docs` については production schema の変更はない。実装段では canonical台帳を直接編集せず、`docs/spool/README.md:24-49,69-90` に従う worklog/decision fragmentだけを追加する。`tools/check_docs.py` の floor固有契約変更は不要である。

C07 閉包も内容変更不要である。

- evaluator: `s8c_preregistration_evidence.py:2694-2698,2776-2874,3045-3071`
- contract: `s8c_preregistration_evidence_contract.v1.json:267-301`
- invariant: `test_s8c_preregistration_invariant.py:81-88,123-128`
- predicate tests: `test_s8c_preregistration_predicates.py:1268-1481`

`load_ratified_freeze` の名前・公開 surface・C07 の field集合は変えないため、これらは編集せず回帰確認だけ行う。

新規 test nodeid は acceptance duration ledger 未登録でも既存90% coverage契約内に収まる見込みだが、実測後に updater が差分を要求した場合だけ `orchestrator/tests/acceptance_duration_ledger.json` を追随させる。静的計画段では数値を捏造しない。

## 変異事前登録の候補

ASCII の parametrize id 案は次の9件。

1. `min-to-max`: `min(run_id)` を `max(run_id)` に変更。later B負例が KILL。
2. `drop-candidate-check`: `build_v2_g1_candidate` の equality callを削除。candidate A/B負例が KILL。
3. `drop-generation-check`: `_verify_generation_semantics` の選択検査を削除。ratification直行負例が KILL。
4. `drop-launch-check`: `_launch_validate` 側の defense-in-depthを削除。手作り `RatifiedFreeze` 負例が KILL。
5. `skip-untracked-results`: candidate filesystem列挙を H treeだけに変更。untracked earlier A fixtureが KILL。
6. `trust-reported-eligible`: earlier resultの full資格再検証を除去。`eligible_for_refreeze=True` だが統計またはadmissionが壊れた earlier resultで KILL。
7. `drop-floor-projection`: `generation.floor == project(result.floors)` を削除。source A/floor B負例が KILL。
8. `drop-rule-version-pin`: frozen generator sourceの版定数確認を削除。版宣言欠落 fixtureが KILL。
9. `ignore-enumeration-shift`: `S0 == S1` を恒真化。列挙2回目へ earlier pathを注入する race fixtureが KILL。

各変異は第一失敗の reason/cause まで固定し、別の既存 gate が偶然落としただけの KILL を数えない。

## 未確認・赤旗

- 最大の残余は、候補生成時に存在した untracked A を削除してから直接 g1 を作る攻撃である。署名・台帳・墓標を禁止した条件では、消えた filesystem 事実を後から証明できない。H tree と worktree の一致は「現在存在する集合」しか証明しない。これを敵対削除まで閉じる必要があるなら、提示された境界だけでは不可能であり、親裁定が必要である。
- committed A の削除は Git 履歴から検出可能だが、全履歴を適格集合の権威にすると historical artifact validator が必要になり、局所修正を越える。本案では current H treeを権威とし、履歴全域 framework は作らない。
- `_validate_floor_inputs` の current admission semanticsを historical reverifyへ流用してはいけない。candidate/live と historical の resolver分離が狭い private seamで閉じなければ、D7 系の既存 historical testを壊すため停止対象である。
- 非selected run が untrackedのままだと、既存 `_measurement_closure` も captured HEAD blob不在で拒否しうる。これは新規則による観測回数制限ではなく、既存 closure の provenance条件である。繰り返し測定後は全 official artifactを記録してから candidate を作る必要がある。
- official floor run は現 worktreeで0件であり、実データ正例はない。全正負例は synthetic fixtureによる静的計画である。
- pytest、`check_docs`、acceptance は実走していない。緑とは報告しない。

## 総括

`earliest-eligible-official-run-id/v1` を推奨する。candidate 境界で filesystem上の全 eligible runから最小 identityを固定し、ratified generation semanticsとfull binding境界で同じ identityを再導出する。さらに `generation.floor` と selected `floor_source.result.floors` の投影 equalityを追加し、直接 ratificationの値差し替えも閉じる。

変更は production 2ファイルと関連fixture/testに限定できる。公開CLI、artifact、schema、protocol bytes、署名、nonce、台帳、一回性機構は追加しない。