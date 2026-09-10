# 敵対所見（レンズ B）

pytest・mutation harness は実走していない。以下の `KILLED/SURVIVED` は `s2-plan.md` の期待値であり、実測結果ではない。

結論として、現行パッケージは裁定に不十分。A′・D・E が抜け、F を「閉鎖」と扱う余地があり、frontier を本番リスクの代理値として過大評価している。

## 1. 選択肢集合は不完全

### A′: 固定 fixture の増量

[real] `s1-brief.md:7-10` と `s2-plan.md:183-221` は、固定 fixture の増量を独立案として比較していない。

既存の `FOUR_ENV_CATALOG` (`orchestrator/tests/test_env_contract_activation.py:59-70`) と任意 catalog を受ける `_chain` (`:130-154`) を使えば、`FIVE_ENV_CATALOG` と fifth-env tail failure test を追加するだけの A′-5 が成立する。A′-8、A′-64 と段階化すれば、生成器や Hypothesis なしで frontier を `4→5`、`4→8` へ動かせる。

代替案: A′-5 / A′-8 / A′-64 を別セルとして、LOC・fixture 保守量・mutation frontier を B1 と比較する。

判定を覆す1手: A′-5 の実装量・保守量・検出時間が B1 と同等以上だと示す。

### D: production 側の量化完全性契約

[real] `s2-plan.md:406-458` は AST と bytecode の C しか扱わず、production の実行時契約を候補にしていない。

`_validate_activation_transition` (`orchestrator/campaign/env_contract_activation.py:274-329`) では、走査前に `expected_count = len(successor_rows)` と `expected_changed = len(changed)` を保存し、処理件数と一致しなければ明示的に `ActivationRecordError` を出す形が成立する。`assert` ではなく通常の `if` にすれば `python -O` でも消えない。`changed[:N]` は件数不一致で fail-closed になる。

これは D245 の「個数で正否を判定しない」規則 (`docs/decisions.md:11390-11395`) と衝突し得るため、「遷移の正否」ではなく「完全走査の健全性検査」と明記する必要がある。

代替案: 将来の裁定に、独立した走査件数 guard、または slice 操作を持たない専用 row-container を載せる。

判定を覆す1手: この guard が D245 違反になる、または合法な単一 site `[:N]` 変異を通すことを静的に示す。

### E: mutation spec の恒久登録

[real] 現行 harness は恒久 matrix を自動発見しない。`--spec`、期待 SHA、`--out` を毎回明示する CLI (`tools/mutation_harness.py:1857-1966`) であり、CI の登録一覧ではない。`pytest.ini:1-14` にも mutation 呼出しはない。

さらに harness は spec・ledger・temporary root を checkout 外へ要求する (`tools/mutation_harness.py:585-603`)。したがって repo 内に spec を置くだけでは運用できない。

代替案: 外部 job directory に固定 spec/core hash を保存し、関連 wave の段 4 で必ず再登録する。既知の `SURVIVED` は「安全性を証明する成功」ではなく、明示的な residual warning として別枠にする。

判定を覆す1手: 既存の恒久 spec、所有者、再実行 trigger、anchor drift 時の更新手順が実在することを示す。

### F: docstring の残穴記述

[real] F は選択肢集合に無い。実際の test docstring (`orchestrator/tests/test_env_contract_activation.py:554-556`) は残穴を記述するだけで、検出力を増やさない。

[refuted] ただし、F を correctness closure と扱うのは誤り。T-627 の「保証を謳わないことをもって終端」は、リスク受容の記録であって、正しさ gate の実装ではない。D176 も遷移検査の production 非発火を明記している (`docs/decisions.md:8691-8698`)。

代替案: F を「現状維持・残穴を明示・ユーザーが条件付きでリスク受容」として独立セル化し、「閉じた」という表現を禁止する。

判定を覆す1手: ユーザーが残穴を明示的に受容し、再検討 trigger（env 数、record 数、期限）を裁定する。

### 追加すべき B3 / C3

[unknown] B1/B2 は生成方法、C1/C2 は構文・opcode 方法で分類されているが、独立 oracle と dataflow 検査の差が比較されていない。

- B3: production の許容 env 数上限を前提にした exhaustive state-model test。
- C3: `successor_rows` / `changed` の alias、事前 slice、`islice`、`break`、`zip` まで追う AST/dataflow 検査。C1 自身が pre-slice alias を見逃すと認めている (`s2-plan.md:417-430`)。

判定を覆す1手: B3/C3 が B1/B2/C1/C2 と同値であることを、同一 cost・false-positive matrix で示す。

## 2. 検出力の代理指標が弱い

### frontier は確率ではない

[real] `KILLED/SURVIVED` は、選択した一つの mutant と一つの fixture に対する test response でしかない。harness も実際には expected failed-node 集合の一致を判定している (`tools/mutation_harness.py:1177-1193`)。

知りたい値は少なくとも、

`P(その退行が導入される) × P(テストを逃げる | その退行) × 影響範囲`

であり、frontier はこのうち二項目を測らない。N の出現頻度、変更者が選ぶ実装パターン、record edge の実行頻度、将来の env 数を持たない。

代替案: 実際の defect corpus、過去の review 差分、mutation operator 別の prior、env 数別の exposure を別に記録する。

判定を覆す1手: frontier と escape probability の相関を、過去の実 defect または独立レビュー標本で示す。

### `[:64]` の実価値

[unknown] 現在の production record は `00000001.json` の 1 件、active env は 2 件だけである (`orchestrator/campaign/env_contract_activations/00000001.json:1`)。registry も現状は 2 env (`orchestrator/campaign/env_contract.py:283-304`) である。

現行 loader は 1 record を読むだけなので、`previous_rows is None` のまま `_validate_activation_transition` は呼ばれない (`env_contract_activation.py:364-401`, `env_contract.py:519-530`)。次の record を発行する保守 tool では一つの edge が検査される (`tools/issue_env_contract_activation.py:205-212`)が、これは現在の campaign chain ではない。

したがって `[:64]` は現行 M=2 では identity であり、現実の現在退行ではない。将来 M>64 を許す設計なら意味があるが、その上限・頻度はどこにも固定されていない。`[:4]` の survivor も現在の M=2 では同様に発火しない。

代替案: 「現行本番の correctness」と「将来 M≤63 の scalability backstop」を別の効用として裁定する。

判定を覆す1手: 将来の env 数・同時変更数が 64 近辺に達する運用計画、または過去の実装差分で `[:64]` 型が実際に現れる証拠を出す。

### 失敗位置への依存

[real] B1/B2 は「最後の env を downgrade / false」に固定している (`s2-plan.md:200-207`)。一方 record の rows は env tag 順に整列される (`env_contract_activation.py:217-228`)。

frontier は「N 番目より後ろに不正行がある」場合の値であり、任意の不正位置に対する検出確率ではない。

代替案: 不正 env を先頭・中間・末尾へ移す全位置 matrix、変更 env の部分集合、predicate exception/non-bool を組み合わせる。

判定を覆す1手: 位置を変えても同一 frontier になることを静的または実測で示す。

## 3. 絶対規律との整合

- **A** — `[refuted]` 残穴を残すだけであり、正しさ gate ではない。`s1-brief.md:50-60` の provisional P1/P2 をそのまま終端理由にしてはならない。覆す1手: ユーザーの明示的な residual-risk acceptance。
- **B1** — `[unknown]` stdlib でも、有限 M の外は未検査である。実走なしなので `KILLED` は未確定。覆す1手: mutation ledger で semantic kill と復元後 bytes を確認する。
- **B2** — `[unknown]` Hypothesis は初の「追加 package」だが、初の第三者テスト依存ではない。pytest は既存 (`test_env_contract_activation.py:23`)、xdist も既存 runner (`tools/run_tests.py:1-12`)。覆す1手: dependency policy 上、既存 pytest/xdist を project dependency と数えない根拠を固定する。
- **C1** — `[unknown]` literal `[:N]` には効くが、plan 自身が alias/islice を射程外と認める (`s2-plan.md:425-431`)。覆す1手: pre-slice・alias・helper 経由の negative controls を通す。
- **C2** — `[unknown]` Python/compiler/opcode に強く依存し、`tuple(changed)` や helper 化で false positive/negative が出る (`s2-plan.md:433-450`)。覆す1手: 対応 Python 全版と意味保存 refactor matrix を通す。
- **D** — `[unknown]` production guard は成立し得るが、性能・D245 との整合・改修耐性が未測定。覆す1手: explicit non-`assert` guard の overhead と全 mutation 結果を示す。
- **E** — `[real]` wave ごとの再登録は検査手順にはできるが、production correctness signal ではない。`DW-M01` も実装前登録を要求するだけ (`docs/dev-wave/mutation.md:5-10`)。覆す1手: stage 4 を欠くと fail-closed になる運用を実在させる。
- **F** — `[refuted]` docstring は規律 3 の構造化 signal ではなく、後付けの説明である。恒真 assert を避けているだけで、量化の完全性は増えない。覆す1手: docstring 以外に reject gate または実効 mutation red を追加する。

## 4. DW-G05 の過大主張

### 「一切変えない」

[unknown] `s1-brief.md:44-48` の「campaign の値・受理集合・参照を一切変えない」は、候補 test を一時 commit に置き、最後に production bytes と land 集合を照合できた場合にだけ成立する。現時点では実走・最終 land 検査をしていないため、結果としては未確定である。

代替案: base HEAD から final tip までの path manifest、production/test の SHA-256、insights/spool のみ変更という machine-readable receipt を成果物にする。

判定を覆す1手: 最終 tip と base HEAD の production/test byte equality、land path 一覧、mutation restore receipt を提示する。

### 「不正な世代前進が受理されうる」

[real] `s1-brief.md:46-48` は現行状態に対して過大である。正確には、現行 chain では遷移 edge がなく、M=2 なので `[:4]` 以上は実質 identity である。

正確な記述は次のとおり。

> 実装しない場合、現行の certified selection・report・ledger は直ちに変わらない。将来、連続 activation record が導入され、かつ不正行または変更 env が truncation bound より後ろに位置する edge では、退行が受理される残穴が残る。発行 tool の候補検証は現時点でも一 edge だけ実行する。

覆す1手: 現行 campaign chain から `_validate_activation_transition` が実際に呼ばれ、N≥4 が意味を変える入力を示す。

## 5. provisional 裁定への反証

### P1

[refuted] 「B は残穴を移すだけなので実質価値がない」は強すぎる。B は有限・未知の bound まで escape probability を下げ得るし、production の許容 M 上限が定まればその領域を閉じられる。

一方、「有限実行だけで無限の N 族を数学的に閉じられない」は `[real]`。

代替案: `MAX_ENV_COUNT` を正規の production 契約にするなら、B3 の exhaustive test をその有限領域の完全検査と裁定する。

判定を覆す1手: production に M の上限が存在しないこと、または B の escape probability が A と同じであることを示す。

### P2

[refuted] 「閉じられるのは C だけ」は誤り。独立 cardinality guard、slice 禁止 container、production の iterator-consumption 契約は C1/C2 以外の閉鎖手段になる。

ただし、D は本 wave の実装 scope 外であり、ここで実装を勧めるものではない。

代替案: D を将来設計候補として返し、C は「source shape を pin する案」と限定する。

判定を覆す1手: D の guard が合法な `[:N]` 単一変異を検出できないことを示す。

### P3

[unknown] M の cost が無視できるという主張は未測定。plan 自身も `_chain` の `sorted` と production validation の `O(M log M)` 面を認めている (`s2-plan.md:290-306`)。

代替案: M=2,4,8,16,32,64 の p50/p95、full suite 差分、dispatch 時間、メモリ、保守 LOC を分離測定する。

判定を覆す1手: 上記の全値で A′・B1・B2・C の順位が変わらないことを示す。

### P4

[refuted] 「Hypothesis は初の第三者 test dependency」は反証済み。正しくは「初の追加 test package、かつ tracked dependency declaration の新設」である (`s2-plan.md:397-404`)。

代替案: P4 の名称と cost model を「既存 pytest/xdist を除く新規依存」と書き換える。

判定を覆す1手: pytest/xdist を repo の依存とみなさない正式な dependency policy を提示する。

## 6. wave 設計への攻撃

### 候補 test を land しない

[unknown] `s1-brief.md:7-10` の no-land はユーザー scope には従うが、「測って捨てる方が正しい」という比較はない。捨てる場合は将来の再現時に materialize、依存準備、tracked temporary commit、anchor 更新をやり直す。land する場合は CI 時間・保守負荷・B2 dependency が継続する。

plan が測るのは主に focal test と mutation 時間であり、full-suite 差分・revert/replay 時間を測っていない (`s2-plan.md:290-305`)。

代替案: 今 wave では land せず、裁定用の reversible patch、source hash、full-suite delta、再生成手順だけを成果物にする。将来の裁定で land/revert を選ぶ。

判定を覆す1手: no-land と reversible candidate commit の再現コストを同一環境で比較する。

### insights の逐語凍結

[real] fenced code block と SHA-256 (`s2-plan.md:159-181`) は、source bytes の encoding・改行・末尾空白・hash 対象が定義されなければ再現性を保証しない。archive も job directory に実行可能原本を残す運用を前提にしている (`worklog-phase3-0808-318.md:47-50`)。

また harness は固定 HEAD の tracked file と外部 spec を要求する (`tools/mutation_harness.py:543-582`, `:611-696`)。insights のコード片だけでは、将来の HEAD・Python・依存・pytest collection を再構成できない。

代替案: raw probe artifact、source SHA、base commit、Python/pytest/Hypothesis wheel hash、newline policy、rehydration script を一つの manifest に固定する。

判定を覆す1手: insights から再構成した source の SHA が原本と一致し、同じ collection/node 集合を再現することを示す。

## 7. 裁定パッケージに欠ける数値・事実

1. **[real] 将来の M 上限・分布・edge 頻度。** `s2-plan.md:200-221` は M を生成するが、本番の許容上限や activation edge の頻度を測らない。  
   覆す1手: production contract と将来 rollout 計画から `M_max`、同時変更数、edge 数を固定する。

2. **[real] 変異 operator の現実性。** spec は loop header の `[:N]` だけ (`s2-plan.md:72-98`)。`islice`、事前 slice、alias、`break`、`zip`、early return がない。  
   覆す1手: 過去差分・review・mutation corpus から operator 頻度を集計する。

3. **[real] 不正行の位置分布。** B1/B2 は末尾 witness に偏る (`s2-plan.md:202-206`)。  
   覆す1手: 先頭・中間・末尾の全位置 matrix を追加する。

4. **[real] production cost。** 測る `_chain+_validate` は calibration I/O、lazy snapshot、issuer path を含まない (`s2-plan.md:292-306`, `env_contract.py:519-586`)。  
   覆す1手: leaf、loader、issuer の三層を分けて p50/p95 を取る。

5. **[real] C の false-positive 閾値。** 「意味保存 refactor 三件」は列挙されておらず、許容拒否数もない (`s2-plan.md:300-304`, `:425-450`)。  
   覆す1手: refactor の逐語、期待判定、拒否理由を matrix 化する。

6. **[real] B2 の依存運用。** version/hash は予定されているが、wheel 配布、offline install、更新頻度、失敗率、保持場所がない (`s2-plan.md:245-254`, `:290-304`)。  
   覆す1手: 外部 venv manifest と再構築時間・失敗時の裁定を固定する。

7. **[real] E の所有と stale spec 処理。** harness は固定 HEAD anchor を要求するが、将来 refactor 時の更新責任・再登録期限がない (`tools/mutation_harness.py:611-696`, `:1909-1923`)。  
   覆す1手: spec owner、更新 trigger、anchor drift の fail-closed 手順を明記する。

8. **[real] F のリスク受容条件。** 「残穴を受け入れる」場合の env 数・record 数・期限・再開条件がない (`test_env_contract_activation.py:554-556`)。  
   覆す1手: ユーザー裁定で受容範囲と再評価 trigger を数値化する。

## 総括

- 最重: frontier は test-selected mutant の識別値であり、本番への侵入確率ではない。  
- 最重: 現行 production は chain 1 record・env 2 個なので、`[:64]` と N≥4 survivor の現在影響を誇張している。  
- 最重: A′ と production cardinality guard D を落としたまま、P2 を絶対命題にしている。  
- 裁定 package には A′-5/8、D、E、F、独立 oracle B3、dataflow C3 を必ず載せる。