## 総括

D1195 の要求形に対する実装残差はない。ただし、親の (P1-4)「repo に別導出法がない」は今回の射影だけでは未確認であり、`_GENERATION_SEEDS` の検索件数も7一致行・8出現である。

## D1195 の項目分解

3項目では (b) が二つの責務を含むため、次の4項目に分ける。

1. **A — 権威点の特定**  
   3つの名前付き権威点を具体的な symbol として定める。根拠は `D1195.md:3-4` と、それが踏襲する `D1171.md:3-7`。
2. **B — 逆到達閉包の導出**  
   手書き目録ではなく、解析対象 call graph の逆辺をたどって3点からの逆到達閉包を導く。
3. **C — 閉包による生成経路不在の成立**  
   導出した閉包を実行時遮断目録にし、probe の検査・証拠公開区間で該当関数へ入らなかったことを確認して、限定された範囲内の生成経路不在を導く。
4. **D — 非完全性と除外範囲の明記**  
   完全性を主張せず、解析 module 外および3点へ到達しない生成器が残りうることを成果物へ明記する。

## 項目ごとの充足判定

| 項目 | 判定 | 根拠 `path:line` | 発火経路 `path:line` |
|---|---|---|---|
| A — 3権威点の特定 | 満たす | `orchestrator/campaign/p3_b4_wiring_probe.py:84-88` が certified writer authorization、loop state 永続化、whiteboard 射影の3 symbol を定義。証拠にも `generation_seeds` として全3点を格納する `同:2108`。事前登録上の意味名は `prereg-10.md:7-9`。 | direct CLI の `同:2158-2159` → `main` の `同:1946` → 既定3点で `_build_inventory` を呼ぶ `同:1957-1959` → 証拠構築 `同:2095-2108` → publish `同:2153`。実 main を呼ぶ検査は `test_p3_b4_wiring_probe.py:1022-1035`、3件確認は `同:1071`。 |
| B — 逆到達閉包の導出 | 満たす | 全静的関数の収集は `同:1038-1043`。callee→caller の逆辺構築は `同:1102-1105`、3 seed の投入は `同:1107-1111`、逆辺 BFS は `同:1112-1120`。`_build_inventory` がその結果のみから目録を作るのは `同:1135-1160`。 | `main` の `同:1957-1959` → `_build_inventory` の `同:1135-1141` → `_reason_paths` の `同:1099-1120`。各 seed を除くと対象が閉包から落ちる負例の呼び手は `test_p3_b4_wiring_probe.py:287-320`。 |
| C — 閉包内の生成経路不在 | 満たす | inventory の function code 登録は `同:557-564`、profile hook の設置・seal は `同:569-583`、目録該当 code の call 時に body 前で `OutcomeGenerationError` を送出するのは `同:592-610`。検査後の違反 ledger ゼロ要求は `同:2019-2033`、証拠 schema 側のゼロ要求は `同:1905-1922`。 | `main` が inventory を seal する `同:1959-1965` → seal 後に4検査を呼ぶ `同:1997-2007` → ledger 照合 `同:2019-2033` → publish `同:2153`。実 producer 9本を直接呼ぶ遮断検査は `test_p3_b4_wiring_probe.py:353-408`、実 `main` 経由の遮断検査は `同:411-439`。 |
| D — 非完全性・外部経路の明記 | 満たす | module docstring は解析 manifest 外・3 seed 非到達 producer を除外する `同:4-11`。証拠 JSON は限定範囲を `generation_scope` に記す `同:2109-2112`、外部経路を明記する `generation_scope_exclusion` は `同:2113-2116`、native code 等の除外は `同:2140-2142`。事前登録は `prereg-10.md:17-25`。 | `main` が文言を含む evidence を構築する `同:2043-2152` → `_publish_evidence` 呼び出し `同:2153` → schema 検査 `同:1757` → JSON 書込み・公開 `同:1769-1786`。実 main 証拠の除外文言を読む検査は `test_p3_b4_wiring_probe.py:1022-1038,1071-1074`。 |

親の provisional 裁定への結論は以下。

- **(P1-1): 同意。** 上表 A〜C の経路で成立する。
- **(P1-2): 同意。** 上表 D の3成果物面で明記される。
- **(P1-3): 同意。** D1195 に対する実装残差はない。
- **(P1-4): 未確認。** 射影された実装内には別導出法を見つけなかったが、特定識別子の検索は、その識別子を使わない別実装の不在を証明しない。また今回の単独段 dispatch では repo 全体が射影されていない。

## 残差を埋めるプラン

残差なし。

## 閉包が閉じたと読める文言の検査

検査対象は指定された7ファイルすべて。

- `brief.md`
- `verbatim/D1195.md`
- `verbatim/D1171.md`
- `verbatim/prereg-5.1-driver-axis.md`
- `verbatim/prereg-10.md`
- `orchestrator/campaign/p3_b4_wiring_probe.py`
- `orchestrator/tests/test_p3_b4_wiring_probe.py`

**違反 hit は0件。**

成果物面の確認結果：

- module docstring `p3_b4_wiring_probe.py:7-11` は、解析 manifest 外、seed 非到達 producer、native code、同権限 process を明示的に除外している。
- 証拠 JSON の `generation_scope` は `同:2109-2112` で exact analyzed module set に限定され、`generation_scope_exclusion` は `同:2113-2116` で外部経路を明記する。
- 事前登録 §10 は `prereg-10.md:17` で「probe が閉じない」とし、`同:24-25` で完全目録ではなく3権威点非到達生成器を覆わないと明記する。
- `prereg-10.md:7-10` の「outcome を生成しないことを…保証する」は単独では強い表現だが、同じ節の `同:24-25` が保証範囲を明示しており、完全性主張にはならない。
- `p3_b4_wiring_probe.py:900` の “closed preflight”、`同:1805` と `test_p3_b4_wiring_probe.py:491` の “publish-window-closed” は、それぞれ import preflight と公開区間の状態名であり、生成閉包の完全性主張ではない。

## 全件検索の記録

すべて打ち切りなし。

- `rg -n '_GENERATION_SEEDS' <implementation,test>`  
  **7一致行、8出現**。`test_p3_b4_wiring_probe.py:292` に2出現あるため、親 brief の「7件」は一致行数としてのみ正しい。
- `rg -n 'reverse closure|_reason_paths|reason_path|reverse\.setdefault|逆到達閉包' <implementation,test>`  
  **6一致行**。すべて既知の `_reason_paths` 機構、その reason、成果物文言。
- `rg -n '"authority"|"generation_seeds"|named seed|named seeds|3 権威点|three seeds' <implementation,test,prereg-10>`  
  **9一致行**。
- `rg -n 'generation_scope_exclusion|modules outside the exact analyzed set|producers reaching none|3 権威点のいずれにも到達しない生成器|遮断集合は生成器の完全目録ではない' <implementation,test,prereg-10>`  
  **5一致行**。
- `rg -n -i 'not covered|not claimed|outside the exact analyzed|完全目録ではない|覆わない|閉じない|完全性は主張しない' <implementation,test,prereg-10>`  
  **9一致行**。
- `rg -n -i 'complete inventory|complete closure|fully covered|all producers are covered|no generation path exists outside|生成器の完全目録である|閉包の外.*(ない|存在しない)|全生成経路.*(遮断|不在)|完全性を主張する|閉包が閉じた' <implementation,test,prereg-10>`  
  **0件**。
- 広い語彙検索 `complete|completeness|closed|closure|covered|…|完全|閉じ|閉包|…` を7射影ファイルへ実行すると **86一致行**。`CompletedProcess`、`completed`、publish window などの語彙上の偽陽性を含むため、不在根拠には使用していない。
- 関数・呼び手探索用の複合式 `^def |^class _ProcessGuard|_GENERATION_SEEDS|…|_profile` は実装・検査で **181一致行**。これは経路特定用であり、不在証明には使用していない。

pytest は制約どおり実行しておらず、上記は静的検査結果である。