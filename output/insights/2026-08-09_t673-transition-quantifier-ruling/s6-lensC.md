# 段 6 敵対レビュー — レンズ C（測定器の正しさ）

結論から言うと、登録済みの直接 `[:N]` 変異に対する A′/B1/B2/C1/C3 の静的検出予測は概ね正しい。G fixture は no-op や catalog mismatch による偽 kill ではない。

ただし、C1 の負制御事前登録は実装と矛盾し、C3 は「全走査」を検証していない。B2 と sibling import の隔離も未固定であり、このままでは裁定パッケージの closure・コスト比較を信用できない。

テストは実走していない。以下の赤/緑はコードから構成した条件であり、実測結果ではない。

## 1. 候補別の検出力と fixture 因果

| 候補 | 静的判定 | 根拠 | 成果物影響 |
|---|---|---|---|
| A′ | `[real]` G/P とも `N<8` で赤、`N>=8` で生存する。G 変異では G node に加えて P node も赤になる | G は末尾 `env-007` が `g2→g1` (`3912c7fc:orchestrator/tests/test_t673_probe_aprime.py:48-63`)。P は全 env `g1→g2` で predicate が末尾だけ False (`同:66-81`) | A′ frontier は 8 でよい。ただし G の failed-node 数を 1 と数えると過少で、実際は G/P の 2 node |
| B1 | `[real]` G/P とも `N<64` で少なくとも一つ赤、`N=64` は生存する | M ごとに末尾 downgrade (`…b1.py:36-56`)／末尾だけ False (`同:64-82`)。M=64 を含む (`同:13-14`) | frontier=64 は維持できる。G の node 数には P 系と位置変種も含めなければ検出力を過少計上する |
| B2 | `[real]` collection できる条件下では G/P とも `N<64` で赤、`N=64` は生存する | 明示例 M=64 (`…b2.py:50-51,84-85`) と同じ末尾 witness (`同:52-75,86-107`) | 検出 frontier は B1 と同じ。ただし collection error と分離できない限り値は「未測定」に留める必要がある |
| C1 | `[real]` 登録された直接 `successor_rows[:N]` / `changed[:N]` は N に関係なく同じ 1 node を赤にする | iterator を exact `ast.Name` に限定 (`…c1.py:125-130`)。slice は `ast.Subscript` | 直接 literal mutant の kill 数は成立するが、意味的 closure とは数えてはならない |
| C3 | `[real]` G の直接 `successor_rows[:N]` は全 N で赤、P は全 N 生存する | slice の `__getitem__` が必ず例外 (`…c3.py:18-22`)。gate への sentinel 注入は G のみ (`同:43-51`) | 「G の直接 slice 検出」は成立する。「P も閉じる」「全走査を保証する」は不成立 |

### 別 gate による偽 kill

`[refuted]` A′/B1/B2 の G fixture が no-op 判定や catalog 照合で別理由の赤になる疑いは成立しない。

- G fixture は先頭から末尾直前まで `g1→g2` なので、登録 N はすべて N≥1であり、`changed` は空にならない。したがって no-op (`env_contract_activation.py:293-297`) は発火しない。
- `_chain` は各 row の hash を渡された catalog の同 generation から取得する (`test_env_contract_activation.py:130-154`)。各候補は同じ catalog を `_chain` と `_validate` の双方へ渡しているため、catalog 照合 (`env_contract_activation.py:384-394`) を通る。
- A′ の明示 hash はすべて 64 lower-hex (`…aprime.py:12-45`)。B1/B2 は `sha256(...).hexdigest()` (`…b1.py:16-28`, `…b2.py:29-41`)。
- P fixture は全 env が変化し、predicate は末尾だけ False である。

成果物影響: 直接 mutant に対する A′/B1/B2 の kill は truncation 因果として数えてよい。catalog/no-op による水増し補正は不要。

`[real]` ただし未登録の `N=0` まで外挿すると、G は `changed=[]` から no-op に落ち、期待 regex 不一致で赤になる。これは truncation witness ではなく別 gate 由来である。

成果物影響: 現行 `{1,4,8,63,64}` の数値は不変だが、「全 N」へ一般化してはならない。

## 2. C1/C3 の恒真・偽陽性

### C1

`[real]` cardinality assert 自体は発火する。FunctionDef は exactly-one (`…c1.py:93-103`)、全 `ast.For` は exactly-two (`同:105-109`)、各 target も exactly-one (`同:110-123`) である。

成果物影響: loop 消失・単純な decoy 追加を黙って通す測定器ではない。

`[real]` しかし段4の「decoy loop は C1 が殺せない」という負制御事前登録は実装と矛盾する。単純な decoy `for` を一つ追加すれば `len(loops)==3` となり、C1 は必ず赤になる (`s4-adjudication.md:154-159` 対 `…c1.py:105-109`)。

成果物影響: 現状の負制御表を実測すると、事前期待と逆の結果になる。C1 の偽陰性・偽陽性件数と採否結論が変わる。

`[real]` C1 が常に赤になる条件を容易に構成できる。

- 無害な第三の `for` を追加する。
- `for ... in tuple(changed)` のような意味保存 wrapper にする。
- 変数 rename を行う。
- 実行されない nested function 内に同名 loop を加える。`ast.walk(function)` は到達可能性を区別しない (`…c1.py:53-54,105`)。

成果物影響: 保守コストと偽陽性率を過少評価する。「構造検査だから安い」という結論は成立しない。

`[real]` 逆に、壊れた gate でも常に緑になる条件がある。

- 関数冒頭に `return None` を置き、既存 2 loop を unreachable のまま残す。
- `limited = successor_rows[:N]` の後、直接 loop は `successor_rows` のままにして body 内で `limited` 外を `continue` する。alias への代入は `_preloop_slice_rebindings_or_deletes` が検出しない (`…c1.py:65-77`)。
- `islice` や helper で実効集合を縮め、見た目の 2 loop だけ保持する。

成果物影響: C1 の値は「登録された iterator 直書き変異を殺す」に限定すべきで、量化完全性の保証値として扱うと裁定が過大になる。

### C3

`[real]` sentinel は直接 slice なら発火する。`successor_rows[:N]` は N が要素数以上でも `slice` 引数なので `_SliceAccessError` になる (`…c3.py:18-22,37-40`)。

成果物影響: G の直接 slice mutant は全 N kill と登録できる。

`[real]` `test_transition_gate_iterates_successor_rows_without_slicing` は「iterates」を検証しておらず、恒真化できる。gate が冒頭で `return None`、または `successor_rows` を完全に無視して `None` を返しても test は通る (`…c3.py:43-51`)。

さらに以下も緑になる。

- `for successor in tuple(successor_rows)[:N]:`
- `itertools.islice(successor_rows, N)`
- `tuple.__getitem__(successor_rows, slice(None, N))`

いずれも override された `successor_rows.__getitem__` を slice で呼ばない。

成果物影響: C3 の exact-mutant kill 数は不変だが、「G の全走査を閉じる」という裁定は撤回し、「当該 subclass への直接 slice 呼出しを検出」に下げる必要がある。

`[real]` 反対に、意味保存の `successor_rows = successor_rows[:]` でも常に赤になる。

成果物影響: C3 にも構文依存の偽陽性コストがあるため、C1だけを refactor-sensitive と評価すると比較が歪む。

## 3. 変異事前登録

### focal expected_nodes

`[refuted]` `mutation-spec-A-focal.json` の expected node 集合に、静的な過多・不足はない。

| mutant | 正しい失敗集合 | 根拠 |
|---|---|---|
| G-N1 | D4, P2, P3, P4 | 最初の 1 env だけが `changed` に入る。D4 と P2/P3/P4 の末尾 witness が全て消える |
| G-N2 | D4, P3, P4 | P2 の false env-b は slice 内なので拒否が残る |
| G-N3 | D4, P4 | P2/P3 の false env は slice 内 |
| G-N4以上 | 空 | focal の最大 env 数は4 |
| P-N1 | P2, P3, P4 | false witness が2/3/4番目 |
| P-N2 | P3, P4 | 同上 |
| P-N3 | P4 | 同上 |
| P-N4以上 | 空 | `changed` の最大長は4 |

D4 は `test_env_contract_activation.py:571-586`、P2/P3/P4 は同 `:921-990`。spec は `mutation-spec-A-focal.json:7-220`。

成果物影響: focal matrix の expected-node mismatch 補正は不要。G が P node も落とすという親の4ケースの主張は正しい。

### full-file survivor

`[refuted]` 既存ファイル内に5 env以上の catalog/fixture はない。最大は `FOUR_ENV_CATALOG` (`test_env_contract_activation.py:59-70`) であり、`_chain` の各 state 長は catalog 長に固定される (`同:136-145`)。ファイル自身も N≥5 を未保証と明記する (`同:554-568`)。動的な production fixture `_actual_serial2` も現在の `ec.GENERATIONS`、すなわち2 envだけである (`同:178-195`)。

成果物影響: `test_env_contract_activation.py` だけを runner に指定する限り、G/P の N≥4 全8件 SURVIVED という事前登録は維持できる。

`[real]` ただし runner を test directory／全 suite に広げると、probe commit 上の C1 が N≥4 も殺し、B2 が collection errorを起こし得る。spec 自体は runner scope を拘束しない (`run_matrix.sh:8-25`)。

成果物影響: full-file survivor 8件が KILLED/MISMATCH/collection error に変わり、A の frontier 結論を丸ごと壊す。

## 4. collection 副作用

`[real]` B2 を含む directory/full-suite collection は、Hypothesis 未導入環境で他候補まで実行不能にする。import は module top-level (`…b2.py:12-14`) であり skip seam がない。

成果物影響: A′/B1/C1/C3 の結果まで error になり、候補別検出力・時間の4セルが欠測する。各 option は exact file/node scopeで収集しなければならない。

`[real]` Hypothesis 用 `PYTHONPATH` を全 option に共通注入すると、pytest entry point plugin の import/collection overhead が B1/A′/C1/C3 のコストにも混入し得る。

成果物影響: 検出 frontier は変わらないが、「追加依存のコスト」比較が過小になる。B2だけ別環境 identity として記録すべきである。

`[real]` sibling import は pytest 既定 import mode に暗黙依存する。全候補が `from test_env_contract_activation import ...` を使う (`…aprime.py:9`, `…b1.py:10`, `…b2.py:16`, `…c1.py:14`, `…c3.py:11`)。`conftest.py` は tests directory を `sys.path` へ追加しない (`conftest.py:30-40`)。`pytest.ini` も import mode を固定していない (`pytest.ini:12-14`)。

壊れる条件は以下。

- `--import-mode=importlib`
- 別 checkout の同名 module が先に `sys.modules` へ入る
- tests directory より先に別の `test_env_contract_activation` が見つかる

特に C1 は誤った `REPO_ROOT` を取得すると、scratch mutant でなく wave tree の未変異ファイルを読む。

成果物影響: 最悪の場合、C1 は全 mutant を生存と誤判定し、B1/A′も別 checkout の activation を検査するため、matrix 全体が無効になる。

## 5. 候補間干渉

`[refuted]` B2 collection と sibling import を除けば、5候補を同一 process/run に置くことによる直接的な状態干渉は見つからない。

- `_chain` は毎回新しい records/listを作る (`test_env_contract_activation.py:130-154`)。
- catalog は `MappingProxyType`。
- 各候補の module 名は異なる。
- B1 の重複 id `M2` 等は module/function を含む nodeid 上では衝突しない (`…b1.py:31-35,59-63`)。
- B2 の `_VERSION_REPORTED` は表示だけ (`…b2.py:19-26`)。
- monkeypatch、activation global、catalog globalを書き換える候補はない。

成果物影響: 正常に個別収集できれば、候補順序や `_chain` 再利用による kill 数の補正は不要。

`[real]` plain `_run()` を同一 Python process から連続呼出しする方式は、pytest再入と `sys.modules` cache に依存するため、上の sibling-import誤束縛条件を再導入する (`各候補末尾の _run`)。

成果物影響: self-runner をコスト測定に使う場合、後続 option が先行 checkout の helper を再利用し、検出値が順序依存になり得る。

## 6. 測定の隔離

`[real]` branch ancestry は現在守られている。機械確認結果は次のとおり。

- wave tip: `86842ee0c8151a27fc5568c342159572f8447835`
- probe: `3912c7fc9a7e13cfcbc2491878767c548cb3cbd1`
- probe の唯一の parent は wave tip
- `git merge-base --is-ancestor 3912c7fc 86842ee0` は非祖先
- 逆向き `git merge-base --is-ancestor 86842ee0 3912c7fc` は祖先
- `git diff HEAD 3912c7fc` は候補5ファイルの追加だけで、本番・既存テスト差分なし

これは `s4-adjudication.md:163-172` の side-branch 条件を満たす。

成果物影響: 現時点では probe が land 対象 branch の履歴へ混入したことによる production/test byte 汚染はない。

`[unknown]` 候補 option ごとの使い捨て worktree、一意 scratch root、終了時 byte照合は、候補用 receipt/ledger がまだ提示されていないため確認不能。`run_matrix.sh` は label から scratch/out を作るだけで (`run_matrix.sh:8-25`)、label の一意性や既存出力拒否をこの wrapper 自身では強制しない。

成果物影響: 同一 label の再利用で ledger・scratchが混ざると、候補別コスト、commit identity、復元証拠を裁定パッケージへ載せられない。

## 7. V1〜V3 の再検査

### V1

`[refuted]` 「現行本番では遷移検査が一度も呼ばれない」は文字どおりには過大である。

通常 loader が現在の checked-in authority を読む場合は確かに record 1件なので `previous_rows is not None` を満たさない (`env_contract_activation.py:364-401`)。authority も `00000001.json` だけで、active env は2件。

しかし production issuer は prospective serial 2を既存 chainに加えて `validate_activation_records` を呼ぶ (`tools/issue_env_contract_activation.py:195-212`)。この経路では遷移 gate が実際に発火する。

成果物影響: 「現在チェックイン済み authority の通常 load では非発火」へ限定すれば現行成果物不変の結論は維持できるが、「production exposure はゼロ」というリスク評価は撤回が必要。

### V2

`[real]` `changed[:1]` の既存失敗 node は10件で、意味的5件／診断5件という分類は正しい。ledger は `mutation-ledger-v3.json:209-246`。

意味的5件:

- P2/P3/P4 (`test_env_contract_activation.py:921-990`)
- 2番目の non-bool (`同:1053-1065`)
- 2番目の例外 (`同:1068-1082`)

診断5件:

- first false 後の call 継続 (`同:993-1008`)
- first non-bool 後の call 継続 (`同:1011-1028`)
- first exception 後の call 継続 (`同:1031-1050`)
- 各 changed env の call-count (`同:1085-1103`)
- reused hashでの2件目 call-count (`同:775-800`)

後者5件は mutant 後も受理/拒否結果自体は同じで、観測 call 列だけが変わる。

成果物影響: P-N1 の既存検出は「10 node、semantic 5、diagnostic 5」で固定すべきで、kill件数へ10全件を合算してはならない。

### V3

`[real]` AST先例は、対象 loop の直接 `passes[:N]` を全 Nで赤にする一方、意味保存 refactorにも赤になる。

先例は iterator が exact `ast.Name("passes")` であることを要求する (`test_campaign.py:4452-4467`)。本体は直接 `for ... in passes` (`pipeline.py:980-981`)。したがって `passes[:N]` は `ast.Subscript` となり N に依存せず失敗する。`tuple(passes)` は `ast.Call`、rename は別 id なので同様に失敗する。

成果物影響: C1の「直接 literal slice の N 非依存検出」は先例で支持されるが、低保守費用や意味的 robustness の根拠にはならない。

## 総括

must-fix は5件。

1. C1 の負制御を exact patch/spec として再事前登録する。現行の「decoy は生存」期待は `len(loops)==2` と矛盾している。
2. C3 の結論を「全走査保証」から「直接 `__getitem__(slice)` 検出」へ下げる。全走査を主張するなら、実際の iteration countを持つ sentinel が必要。
3. B2 は exact file/node scope と専用 Hypothesis 環境に隔離する。directory/full-suite collection を候補比較に使わない。
4. sibling import を排除するか、import modeと helper moduleの `__file__ == scratch worktree` を preflight で固定する。
5. 全候補について一意 scratch/out、resolved probe commit、終了時 production/test byte一致の receipt が揃うまで、検出力・コスト表を裁定値として確定しない。