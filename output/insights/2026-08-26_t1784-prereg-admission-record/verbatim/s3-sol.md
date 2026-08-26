## 総括

最も危険なのは、`test-only` receipt を両腕とも整合的に書き換えると、後から作った record を持つ `certified` 標本へ昇格できる点である。  
plan は先行実走を「塞げない穴」と認める一方、同一 invocation の後差しは拒否できると過大主張している。  
また、正式 pair 検査は `test-only` 同士を成功受理し、公開 `main(..., pair_factory=...)` も同じ成功 CLI schema を出せる。  
自己参照 hash と既存負例の TypeError 弱体化は、plan どおり実装すれば反証できなかった。

## 所見

### 1. certified-only の受理関門が存在しない

- `real / refuted の自己判定`: **real**。`assert_b4_arm_pair()` は両腕の class が同じことしか要求せず、`test-only` 同士を受理する (`p3_b4_closed_critic.py:1393-1405`)。既存テストも明示的にその成功を要求する (`test_p3_b4_closed_critic.py:1139-1146`)。さらに `main()` は公開 `pair_factory` を受け取る (`p3_b4_closed_critic.py:1443-1456`) が、CLI 出力には evidence class が無い (`:1467-1472`)。

- 具体的な破り方: Python から `main(argv, pair_factory=wrapper)` を呼び、wrapper が `create_b4_closed_critic_pair_for_test(executable="claude", runner=subprocess.run, ...)` を返す。record 無しで実 Claude query を行い、real `assert_b4_arm_pair()` を通って `rc=0` と通常の CLI `/v1` 出力を得られる。plan 後は wrapper が渡された `admission_record_path` を無視すればよい。直接 controller 構築については、現行 `_PAIR_SEAL` は import 可能 (`p3_b4_closed_critic.py:108,619-635`) だが、plan の certified と admission の双方向 invariant と invoke 時再検証を忠実に実装すれば、`certified + None` 単独では止まる。通常 API の明確な穴は `pair_factory` と certified-only 検査の欠落である。

- 恒真監査: 宣言済み低層 gate には偽入力を挙げられる。末尾 LF、duplicate key、missing/symlink/untracked record、非祖先 commit、blob hash 相違、`未記入`、3期待値の1桁反転、closure byte drift、`certified + None`、異なる arm record、CLI option 欠落がそれぞれ拒否入力になる。**偽入力を挙げられない宣言済み gate は無し。ただし「正式受理は certified のみ」という gate 自体が無い。**

- 成果物影響: stage 4 や台帳 consumer が CLI 成功または pair comparison だけを見ると、test-only pair が正式 B-4 受理集合へ混入する。

- 修正案: production 用を `assert_b4_certified_arm_pair(on_path, off_path) -> B4ArmPairComparison` として分離し、`evidence_class == "certified"`、全 admission field 非 `None`、同一 binding を固定する。`main(argv=None) -> int` から `pair_factory` を除き、この certified-only 関数だけを呼ぶ。通る正例は、committed record を渡した production factory が作る `/v3` 両腕 receipt である。test-only 検査は `_assert_b4_test_pair(..., _test_seal)` に隔離する。

### 2. 結果取得後の record 作成と両腕昇格を検出できない

- `real / refuted の自己判定`: **real**。plan `s2-plan.md:118` の「同じ invocation の終了後に record を差し替えて成功扱いにすることは拒否できる」は強すぎる。terminal receipt 自身には外部 anchor がなく、start hash や各 artifact hash も同じ可変 terminal に格納される。既存テストは on 側の start と terminal を整合的に昇格した後、off 側がまだ test-only なので失敗する地点までしか試していない (`test_p3_b4_closed_critic.py:1154-1185`)。

- 具体的な破り方:

  1. test-only factory で exact campaign を実走し、model、prompt、projection、結果を得る。
  2. §5 を埋めて文書 commit D、record commit R を作る。必要なら `GIT_AUTHOR_DATE` と `GIT_COMMITTER_DATE` で過去時刻も記録できる。
  3. 両腕の start/terminal を `/v3`、`evidence_class="certified"`、R の admission field に更新する。
  4. 各 start bytes の hash を terminal へ再記録する。model、prompt、projection は先行実走から転記したので record と一致する。
  5. 両腕とも同じ処理をすれば、片腕だけを昇格した既存負例の最後の拒否理由も消える。

  record commit が query より後である事実は Git graphにも receipt bytesにも残らない。新しい certified invocation を再実行するだけの簡単な攻撃も plan 自身が `s2-plan.md:120-127` で認めている。

- 成果物影響: 結果を見てから固定した値を持つ pair が certified 集合、B-4 レポート、試行台帳へ入り、「事前登録済み」という参照だけが偽になる。

- 修正案: `create_b4_closed_critic_pair(..., admission_token_path: Path)` に外部発行された `SignedAdmissionToken(record_commit, record_sha256, nonce, ledger_sequence, signature)` を必須化し、provider query 前の append-only ledger 登録と署名を検証する。terminal は token hash と nonce を鎖状に保持し、`assert_b4_certified_arm_pair()` が固定公開鍵で再検証する。通る正例は、ledger sequence 42 で query 前に発行された token を両腕が共有する pair。外部 anchor を導入しないなら、証明可能範囲を「repository-local ordering」へ格下げし、事前登録済み certified と呼ばない必要がある。

### 3. §5 完全性 gate は `TBD` や `x` で通る

- `real / refuted の自己判定`: **real**。plan の検査は10欄について空または `未記入` を含む値だけを拒否する (`s2-plan.md:67-76`)。§5.1 が要求する artifact path/hash、予算、母集合、純関数などの型を検査しない。plan は意味的正しさを証明しないと認めている (`:124`) が、エラー名とテスト名は `complete_section5` と表現している (`:91,141`)。

- 具体的な破り方: row 9 だけ正しい model と2 hash にし、残り9行をすべて `TBD`、`N/A`、`—`、または `x` にする。全行が非空かつ `未記入` を含まないため、計画された parser では §6 前提条件1を通過する。

- 成果物影響: floor、PerfConfig、予算、母集合が実在しない標本まで certified 受理集合へ入り、レポートと台帳が無効な artifact 参照を持つ。

- 修正案: `parse_b4_section5(blob: bytes) -> B4Section5Values` を設け、10欄を row 別の型へ変換する。artifact 欄は `repository_path + sha256`、予算は正の整数上限、時刻は timezone 付き形式、row 9 は `model | prompt=<h1> | projection=<h2>` の exact grammar とする。通る正例は、10欄すべてが型検証を通り、row 9 の h1/h2/model が record と一致する文書である。型検証を実装しない場合は関数名とメッセージを `section5_is_syntactically_nonempty` に限定し、§6.1 充足を意味させない。

### 4. Git 検証の環境隔離が plan に無い

- `real / refuted の自己判定`: **real、plan レベルの欠落**。`s2-plan.md:67-76` は ancestry、replace ref、graft、shallow history の拒否を列挙するが、Git subprocess の executable と environment を固定していない。現行 production API は任意の child `environ` も持つ (`p3_b4_closed_critic.py:944-950`)。

- 具体的な破り方: validator が通常の `git -C repository_root` を継承環境で実行する実装なら、呼出し前に `GIT_DIR=/tmp/forged.git`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES`、`GIT_CONFIG_PARAMETERS`、または差し替えた `PATH/git` を与える。固定した `-C` だけでは、偽 HEAD、偽 object graph、偽 document blob を読ませられる。

- 成果物影響: 実 repository の HEAD に record や文書が無くても、偽 object database 上の binding が certified receipt と台帳へ記録される。

- 修正案: `git_read(repository_root: Path, *args: str) -> bytes` を内部専用にし、固定 executable、空の Git 設定、全 `GIT_*` 除去、`GIT_NO_REPLACE_OBJECTS=1` を使う。取得した worktree/common-dir/object-dir が期待 repository 内であることも確認する。通る正例は、process 環境に偽 `GIT_DIR` があっても、それを無視して実 repository の committed record を検証できるケースである。

### 5. projection の自己参照は成立しないという攻撃

- `real / refuted の自己判定`: **refuted**。入力 JSON record は closure に入れず、期待値を保持しない validator の Python bytes だけを追加する設計なので自己参照しない (`s2-plan.md:16,27`)。現行 closure は controller 自身を含む (`p3_b4_closed_critic.py:501-537`) が、record JSON は含まない。

- 具体的な破り方: 実装 commit A 後に projection H を計算し、§5 を持つ文書 commit D、H を宣言する record commit R の順に作る。D/R が変更するのが文書と record JSON だけなら closure は変化せず、R の実行でも H が維持される。反対に validator または controller を1 byte変えれば H 不一致で拒否される。

- 成果物影響: 修正不要。誤って record JSON を closure に追加した場合だけ受理集合が空になり、全 certified 実走が不能になる。

- 修正案: `test_projection_hash_stabilizes_before_record_commit()` を追加し、A→D→R の正例と、validator byte drift の負例を固定する。通る正例は R の tree にある closure bytesから Hを再計算して record の H と一致するケース。

### 6. 必須引数追加で既存負例が TypeError 偽陽性になるという攻撃

- `real / refuted の自己判定`: **refuted、plan 遵守が条件**。plan は `runner=` と `executable=` の負例へ有効な admission record を渡し、拒否軸を維持すると明記している (`s2-plan.md:97-112`)。これは現行テスト `test_p3_b4_closed_critic.py:466-489,1092-1115` の弱体化を正しく予防する。

- 具体的な破り方: author が追随を忘れれば、record 欠落 TypeError だけでテストが緑になり得る。しかし plan どおり valid record を渡せば、`runner` または `executable` の unexpected keyword が唯一の失敗理由になる。

- 成果物影響: plan 遵守時は無し。追随漏れ時は runner/executable 注入禁止の固定が消え、偽 provider の certified receipt が受理され得る。

- 修正案: `inspect.signature(create_b4_closed_critic_pair)` で `admission_record_path.default is inspect.Parameter.empty` を固定し、各注入負例には共通の valid committed record fixture を渡す。通る正例は、valid record 付き `runner=injected_runner` が record gateではなく `unexpected keyword argument 'runner'` で落ちるケース。

## 親 brief への攻撃

- scope の「実走前に commit された record 無しには開始できなくする」(`s1-brief.md:7-16`) は過大一般化である。test-only factory は real executable と `subprocess.run` を受け取れ、公開 `main(pair_factory=...)` から query を開始できる。証明できるのは production factory を正直に使った invocation に限られる。

- P4 の「test 経路から certified を作れないことは既存テストが固定済み」(`s1-brief.md:63-66`) は反証された。既存テストは test-only pair の受理を要求し、昇格攻撃は片腕までしか検査しない。

- P3/P5 は factory の必須引数と CLI option だけなら正しいが、Python `main` の `pair_factory` seam と certified-only consumer の欠落を一般化から落としている。

- P2 を plan が §5 parser で補強した点は妥当だが、非空・非 `未記入` だけでは「全欄記入済み」を証明しない。

- DW-O13 の実測 hash は反証されなかった。独立再計算は `df37ca0d1e98b4fb2346db751fed0ddf7fc169dd9b863a7ce9ff3b1d87efff46`、entry 数10で brief と一致した。ただし実装後は validator と controller bytes が変わるため、この値を record へ転記してはならない。

- P1 の prompt/projection は事前計算可能、model は response の `modelUsage` で実測するというコード説明も支持される。ただし先行 query から model 値を知る攻撃は防げない。

## 攻撃できなかった面

- 新設予定の `p3_b4_admission_record.py` はまだ存在しないため、実際の Git 呼出し、例外処理、symlink component 検査は実装後レビューが必要。
- 併走 wave が変更中の stage 4 driver と、将来の正式 report/ledger consumer は未検査。
- pytest と実 Claude query は実行していない。静的検査と projection hash の read-only 再計算のみ行った。
- 外部 append-only ledger、署名鍵、trusted timestamp の実配線は本 scope に無く、実現可能性までは検証していない。