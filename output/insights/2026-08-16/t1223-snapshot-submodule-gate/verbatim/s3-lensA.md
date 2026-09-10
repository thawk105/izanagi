## 所見

### 1. MUST-FIX: 「initialized」は CCBench の内容実在を保証しない

- **所見:** 深さ 1 gate は「未初期化」を拒否するだけで、親 brief が掲げる「CCBench 実体を持たない snapshot」の受理を閉じ切らない。
- **確信度:** high
- **根拠:** `_submodule_worktree_state` は submodule path が Git top-level で、`HEAD == gitlink_commit` なら即座に `"initialized"` を返す。marker が期待 admin dir を指すこと、index が HEAD tree と一致すること、worktree bytes が index と一致することは確認しない (`tools/codex_reasoning_ab.py:934-972`)。inventory はその live index と worktree の `.gitmodules` を信用する (`984-1034`)。closure の最終検査も index 由来のファイル名集合と実ファイル名集合を比較するだけで、submodule 内の bytes・mode・blob ID を照合しない (`1173-1197`, `1240-1257`, `1427-1434`)。plan の新 gate も `row["initialization"]` だけを見る (`plan.md:26-40`)。
- **成立条件:** 深さ 1 submodule の HEAD は gitlink のままにし、submodule index を空にして worktree を `.git` 以外空にする。親 repo の local config で当該 submodule と submodule diff を `ignore=all` にすれば、root の status・numstat に汚れを出さず、inventory は空 index を正規状態として扱う。schedule 作成前なら、その偽 oracle 自体を pin できる。別案として index とパスを残して payload bytes だけ空にしても、同じ status 抑制下では oracle に内容差が現れない。
- **成果物への影響:** 新 gate 後も、prompt が実際には空または改変済み CCBench を読む試行を「initialized・pin 済み」として trial ledger、snapshot oracle、最終 aggregate に載せられる。これは brief の成果物影響 (`brief.md:80-83`) をそのまま残す。
- **提案:** 深さ 1 の要件を「initialized」ではなく「HEAD tree・index・worktree の内容同一性」にする。required-depth の各 repo で index tree と `HEAD^{tree}`、各非-gitlink entry の mode/blob ID と実 worktree bytes を local ignore 設定に依存せず照合する。さらに `.git` marker と期待 admin dir の束縛も検査する。`initialized + 正しい HEAD + 空 index/worktree` の負例を追加する。

異なる commit は `HEAD/gitlink mismatch` で先に例外となるため通常の Git semantics では通らない (`964-970`)。一方、同じ commit object を持つ別 admin repository は、marker/admin の束縛がないため通りうる。空 directory 単体は拒否されるが、正しい HEAD を持つ空 worktree は上記構成で通る。

### 2. gate は最終認証経路には届くが、中間成果物層には届かない

- **所見:** 通常 supervisor と最終 aggregate は新 gate を踏む。しかし schedule 検査、直接の receipt 収集、packet・verdict 系生成は踏まない。全成果物層が閉じるという主張には scope 裁定が必要である。
- **確信度:** high
- **根拠:**

| 経路 | 発火 | 実効 |
|---|---:|---|
| `1508` | する | build/derive の返却 oracle 前に拒否する。 |
| `2210` | する | `snapshot-before.json` 作成前の起動直前 gate (`2210-2212`)。 |
| `2371` | する | post-run 失敗を `snapshot_unchanged=False` にし、supervisor failure へ送る (`2369-2417`)。 |
| `2475` | する | attempt ledger の予約 (`2531-2542`) より前に拒否する。 |
| `4885` | する | replay 例外は failure reason となり (`4952-4953`)、最終 `decision=None` になる (`4341-4343`, `4403-4409`)。 |
| `5561` | する | CLI は `RC_SNAPSHOT` を返す (`5645-5651`)。 |
| `_assert_submodule_manifest_sha256` | しない | row hash の一致だけで、initialized の意味は検査しない (`1044-1052`)。ただし `2476` では verifier の後に呼ばれる。 |
| POS/NEG 突合 | しない | 64文字 field と POS/NEG 間の同値だけを見る。同じ未初期化 hash なら通る (`3866-3911`)。 |

`collect_run` は launch receipt を検査するが現在の snapshot を再検証せず、receipt へ launch 内の oracle SHA を転記するだけである (`3029-3052`, `3464`)。`make_packets` も manifest の attempts と output を直接読み、`verify_manifest` を要求しない (`5054-5117`)。append/freeze/reveal の CLI も snapshot gate を経由しない (`5616-5641`)。

- **成立条件:** supervisor 以外から `collect-run` や packet 系 CLI を直接使う、または legacy/偽造 manifest を中間成果物として消費する場合。
- **成果物への影響:** 正規 supervisor 経路の試行台帳と最終 certified decision は閉じる。一方、receipt、材料 packet、verdict freeze は未認証 snapshot 由来でも生成できる。
- **提案:** 「aggregate の `valid=true` だけが certified で、中間 packet・receipt は未認証」と明記するか、`collect_run` と `make_packets` に frozen oracle の再検証を要求する。実装しない層は段 4 の scope 外裁定パッケージへ明示する。

### 3. 新規テストは恒久保留されないが、production の既定 spec 経路を試していない

- **所見:** 「新検査が既定受入で一度も発火しない」という最悪形ではない。ただし proposed negative は独自 spec 専用で、全 production caller が使う `spec=None` 経路を動作として固定していない。
- **確信度:** high
- **根拠:** hold は file 単位ではなく正確な node 名単位であり (`growth_test_holds.py:100-115`, `conftest.py:404-413`)、wrapper も登録済み関数名だけを包む (`growth_test_holds.py:568-593`)。plan の新しい二つの名前は registry にないため、計画どおり実装されれば全走で収集される。一方、負例は `spec=spec` を明示し (`plan.md:101-115`)、正例も policy key を明示する (`118-120`)。既定 `_snapshot_spec` は値の assertion しかなく、動作経路ではない。
- **成立条件:** 実装が `spec is None` のときだけ gate を落とす、または将来その分岐が回帰した場合。提案 matrix の全テストが通っても production は fail-open に戻りうる。
- **成果物への影響:** verifier 本体の branch は既定受入で発火するが、`1508/2210/2371/2475/4885/5561` への実効性は静的主張のままになる。特に replay 統合 node `test_verify_replays_complete_fake_codex_experiment` は恒久保留対象である。
- **提案:** monkeypatch した合成 `_snapshot_spec` を `spec=None` で消費する負例を追加する。加えて、少なくとも `2475` が ledger 予約前に拒否する合成 integration test と、replay reason が `decision=None` へ届く未保留 test を追加する。新規 node を hold registry へ入れてはならない。

### 4. oracle key 不変性は設計上は守るが、テストと変異が守っていない

- **所見:** skeleton をそのまま実装すれば oracle bytes は変わらない。しかし計画したテストは policy key の oracle 漏出を検出しない。
- **確信度:** high
- **根拠:** oracle の `manifest_sha256` は返却 dict 全体から作られる (`tools/codex_reasoning_ab.py:1703-1723`)。plan は key を返さないと宣言するだけで (`plan.md:43-45`)、正例は `submodules` の状態しか固定しない (`118-120`)。変異 matrix に「policy key を oracle へ追加」もない。なお brief の `4877` への帰属は不正確で、`4877` が比較するのは `submodule_manifest_sha256` だけである。oracle key 増加で壊れるのは outer `snapshot_manifest_sha256` (`2480-2483`, `4872-4876`) と replay bytes 比較 (`4885-4887`)。
- **成立条件:** 実装時または将来の整理で新 policy key を oracle dict に転記した場合。
- **成果物への影響:** schedule、launch receipt、replay、過去 oracle bytes が変わるのに、新規二テストと提案 matrix は緑になりうる。
- **提案:** 正例で oracle の field 集合を正確に固定し、policy key 不在と `manifest_sha256` の既存構成を検査する。変異 matrix に oracle への key 漏出を追加する。

### 5. 親の「source hash pin はない」という実測結論は反証された

- **所見:** 8 Python file という検索件数は再現したが、「source hash pin なし」という一般化は偽である。
- **確信度:** high
- **根拠:** tracked artifact `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json:4-5` は `tools/codex_reasoning_ab.py` の絶対 path と `tool_sha256` を明示的に pin する。README も装置 SHA を凍結したと記す (`README.md:47-53`)。erratum は認証がその装置 SHA の下だけで成立し、pin は歴史記録として不変だと明記する (`erratum-f176.md:9-14`, `91`)。brief の検索は `.py` に限定していたため、この JSON pin を構造的に見落とした (`brief.md:39-41`)。
- **成立条件:** T-1223 後の tool を旧 T-181 certified rerun と同じ装置 identity として扱う場合。
- **成果物への影響:** oracle bytes の互換性とは別に、tool source identity は必ず変わる。旧 certified artifact の apparatus pin を更新すると歴史記録を破壊し、更新しないまま同じ装置だと名乗ると proof chain が偽になる。
- **提案:** 旧 pin は変更しない。brief の pin 閉包を訂正し、T-1223 後の新規実走または新規認証には新しい apparatus identity を発行する。過去 run を新 tool で replay した結果は「旧装置下の認証」と区別する。

## 親 brief への反証

- **(P1): 一部反証。** 非再帰 startup が深さ 1 までしか一様に保証しない点は `docs/dev-wave/operations.md:141-143` と初期化再帰条件 (`tools/codex_reasoning_ab.py:729-760`) に整合する。全深度 initialized を要求しない裁定は支持する。しかし「深さ 1 initialized が production を壊さず狭められる最大幅」は偽であり、深さ 1 の checkout tree 内容同一性まで安全に要求できる。
- **(P2): 単調性は支持、不十分性は反証。** fallback 1、bool/非正整数拒否、closure 分岐外配置なら新たな accept は生まれない。gitlink 不一致も先行例外のままで、`enforce_closure=False` でも inventory は走る。受理集合拡大は見つからなかった。ただし、その predicate 自体が弱すぎる。
- **(P3): コード所有範囲は維持可能。** 内容同一性 gate と合成テストは同じ二ファイル内で実装できる。ただし中間成果物層の扱いと apparatus pin は、二ファイルで「閉じたふり」をせず段 4 の明示裁定へ出す必要がある。
- **親の reason 0 実測:** 静的コードと inventory/closure の順序から成立し、覆せなかった。probe 自体は再実行していない。
- **親の recursive clone 実測:** 現在は三階層すべて initialized であることを確認したが、「その実行で新規 clone された」という履歴主張は現在状態からは裏付け不能。標準手順が非再帰という一般化は現行 operations が支持する。
- **16 node 恒久保留:** exact node の事実は支持する。「同じ test file の新規 node も保留される」という一般化は成立しない。
- **source pin 不在:** 明確に覆した。`apparatus-pin.json` が反例である。

## 恒真リスク

core gate の新規二 node は、計画どおりの名前なら既定全走で skip されないため、完全な恒真保証ではない。ただし負例が独自 spec だけなので、production の既定 spec 経路に対する保証は弱い。

成果物層ではリスクが高い。既定受入で未初期化 snapshot を `1508/2210/2371/2475/4885/5561` の各 caller に流す新規 test がなく、replay の既存 integration node は恒久保留される。提案 matrix も「initialized だが空」「oracle key 漏出」「中間 packet/receipt bypass」を殺さない。

pytest は実行していない。以上は read-only の静的検査であり、緑とは報告しない。

## 総括

現 plan は「本当に uninitialized な深さ 1」を止めるが、「initialized と名乗る空の CCBench」を止めない。  
MUST-FIX は深さ 1 checkout の HEAD・index・worktree 内容同一性であり、状態名検査だけでは不足する。  
通常 supervisor と最終 aggregate には gate が届くが、collect・packet・verdict の中間層は scope 裁定が要る。  
新規 test は未保留だが、既定 spec と成果物伝播の実行保証が欠ける。  
oracle key 不変の設計は支持する一方、明示的な apparatus source pin の見落としは親 brief の実測反証である。