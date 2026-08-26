# 段 4 裁定 — [T-1784] admission record

base main 68fc629e (wave 開始時 9463bcbc から前進。受入時に取り込む)

## 裁定表

|#|出所|判定|採否|理由|
|---|---|---|---|---|
|R1|luna F4|**real**|**採用 (plan を却下側へ修正)**|receipt schema を `/v3` へ上げない。v2 は既に `model_snapshot` / `effective_prompt_sha256` / `projection_sha256` (195-199) と `evidence_class` を持つ。昇格は gate の強さを 1 bit も増やさず、併走 wave との重なりを `main` 1 か所から 3 か所へ広げるだけである。admission の束縛は receipt の field ではなく**独立した検証関数**が担う|
|R2|sol #1 / luna F3|**real**|**採用**|正式受理が `certified` に限られる関門が存在しない。`assert_b4_arm_pair` (1393-1405) は evidence class の一致しか見ず、`test-only` 同士を受理する。`assert_b4_certified_arm_pair` を新設し、`main` はこれを呼ぶ。`pair_factory` seam は残すが、seam が返した `test-only` pair では `main` が緑にならなくなる|
|R3|sol #3|**real**|**採用 (縮小)**|§5 完全性の検査は `TBD` や `x` で通る。**型検査を 10 欄へ入れることは本 wave では採らない** — 欄の書式は併走 wave が今まさに決めており、型を先に固定すると相手の記入を壊す。採るのは (a) 10 欄の非空・placeholder 不在、(b) **model/prompt/projection の 1 行だけ**の exact grammar、(c) **関数名・例外文言が「§6 前提条件 1 を充足した」と読めないこと**。残り 9 欄の型検査は裁定パッケージ|
|R4|sol #4|**real**|**採用**|Git 検証の環境隔離が plan に無い。`GIT_DIR` / `GIT_OBJECT_DIRECTORY` / `GIT_ALTERNATE_OBJECT_DIRECTORIES` / `GIT_CONFIG_PARAMETERS` / `PATH` 差し替えで偽 object graph を読ませられる。固定 executable・`GIT_*` 全除去・`GIT_NO_REPLACE_OBJECTS=1`・解決先が repository 内であることの確認を必須にする|
|R5|luna F6|**real**|**採用 (縮小)**|古い §5 blob を指す record が現在の HEAD でも通る。`content_commit` の文書 blob が**検証時 HEAD の同 path の blob と同一**であることを必須にする。これで「古い版の §5 を指す record」は死ぬ。**active record の単一性 (固定 path 1 本)** は文書側の規約なので裁定パッケージ|
|R6|sol #2 / plan 自己申告|**real**|**採用 (主張の格下げ)**|plan の「同じ invocation の後差しは拒否できる」は過大主張。両腕を整合的に昇格されれば検出できない。**証明できる性質を「repository-local な順序」に限定し、module docstring と record schema にそう書く。**「事前登録済み certified」と名乗らせない。外部 append-only ledger / 署名 token は裁定パッケージ|
|R7|luna F5|**real**|**採用 (縮小)**|model 不一致は critic query と envelope 保存の**後**にしか検出できない。出力を見てから record の model 欄を直して再試行できる。**塞げないことを docstring に明記し、不一致は failure terminal receipt に残す。** 実走前 attestation は裁定パッケージ|
|R8|luna F1|**real**|**scope 外・裁定パッケージ**|production factory は B-4 実走の支配点ではない。3 driver からの呼び手 0 件で、`run_one_iteration()` を直接呼べば record も closed critic も通らない。**併走 wave の (A) がこの層を担う。**本 wave が実装したふりをしない|
|R9|luna F2|**real**|**scope 外・裁定パッケージ**|receipt N を driver N の必須入力にすると循環する。proposal への因果束縛 (decision hash → proposal hash) が無い。併走 wave の設計に直接効くので裁定パッケージへ名指しで送る|
|R10|sol #5|**refuted**|—|自己参照は成立しない。record JSON を閉包に入れず validator の Python bytes だけを入れる設計で正しい。ただし**誤って record JSON を閉包へ入れたら全 certified 実走が不能になる**ので、これを固定するテストを登録する|
|R11|sol #6|**refuted (plan 遵守が条件)**|**採用 (固定を追加)**|必須引数化で既存負例が「引数不足の TypeError」で緑になる劣化は、plan の追随方針で防げる。`inspect.signature` で既定値不在を固定するテストを必須にする|
|R12|plan P2 修正|**採用**|—|文書の commit 束縛だけでは §5 が全部「未記入」の版でも通る。R3 の縮小形で塞ぐ|
|R13|plan P4 修正|**採用**|—|test-only factory に record は要求しない。ただし R2 の certified 限定関門で昇格経路を塞ぐ|

## plan v2 (確定した実装方針)

1. **新設 `orchestrator/campaign/p3_b4_admission_record.py`**
   - schema `p3-b4-prerun-admission/v1`。field は plan のとおり。
   - canonical bytes: `sort_keys=True`, `separators=(",",":")`, `ensure_ascii=False`, `allow_nan=False`、
     BOM なし・末尾改行なし。**parse 後に再 canonicalize して元 bytes と完全一致しなければ拒否**
     (duplicate key・未知 key・欠落 key・bool/int 混同を落とす)。
   - Git 検証は R4 の隔離実行で行い、(i) record が検証時 HEAD の tree に exact bytes で在る、
     (ii) `content_commit` が record commit の祖先、(iii) `content_commit` の文書 blob の sha256 が
     `content_sha256` と一致、(iv) **その blob が検証時 HEAD の同 path の blob と同一** (R5) を要求する。
   - §5 検査は R3 の縮小形。関数名は充足を主張しない語にする。
   - **証明範囲を docstring に明記** (R6/R7)。
2. **`p3_b4_closed_critic.py` の統合 (最小)**
   - `create_b4_closed_critic_pair` に既定値なしの必須 keyword `admission_record_path` を足す。
     record 検証は executable 探索・artifact 作成・provider 作成より**先**。
   - projection 期待値の照合は `_prepare_b4_closed_critic_pair` が closure hash を取る位置。
   - prompt 期待値の照合は provider 作成直後 (role query 前)。
   - model 期待値の照合は provider が envelope を検証して返した直後、decision parse より前。
   - `assert_b4_certified_arm_pair` を新設 (R2)。既存 `assert_b4_arm_pair` は**残す** — 既存テストが
     その受理を固定しており、壊すと段 6 で偽の赤になる。
   - `main` は `--admission-record` の必須 option 追加、factory への引渡し、
     `assert_b4_certified_arm_pair` の呼出し、新例外の失敗処理への追加**だけ**。
   - **`projection_closure_manifest()` に validator module を entry として足す。record JSON は足さない。**
   - **receipt schema は `/v2` のまま。`B4ClosedCriticReceipt` の field を変えない (R1)。**
3. **新設 `orchestrator/tests/test_p3_b4_admission_record.py`** と既存テストの追随。

## 不変条件 (段 5 実装子への拘束)

段 1 brief の不変条件 1〜8 をそのまま継承し、次を足す。

9. `B4ClosedCriticReceipt` (182-223) の field を増減しない。`schema_version` を変えない。
10. `_read_verified_terminal_receipt` (1120-) の既存検査を 1 つも削らない・緩めない。
11. `assert_b4_arm_pair` (1393-) の既存の受理・拒否を変えない。新関数として足す。
12. `orchestrator/campaign/claude_projected_provider.py` を変更しない。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後に無い」「無効化時の赤理由が 1 つ」を
実装後に probe で確認し、確認できなければ登録から外して実効 gate へ再照準する。

|ID|変異位置|無効化する検査|期待|
|---|---|---|---|
|M01|record loader|parse 後の再 canonicalize 比較|duplicate key / 未知 key を持つ record が通る|
|M02|record loader|HEAD tree との exact bytes 一致|untracked / working-tree 改変の record が通る|
|M03|record loader|`content_commit` の祖先性|record commit の祖先でない文書 commit が通る|
|M04|record loader|文書 blob の sha256 比較|`content_sha256` 不一致の record が通る|
|M05|record loader|**HEAD blob との同一性 (R5)**|古い §5 版を指す record が通る|
|M06|§5 検査|10 欄の非空・placeholder 不在|全欄「未記入」の文書が通る|
|M07|§5 検査|model/prompt/projection 行の grammar 束縛|record の 3 値が文書と無関係でも通る|
|M08|controller|projection 期待値の照合|期待値と異なる closure で実走が始まる|
|M09|controller|prompt 期待値の照合|期待値と異なる prompt で role query が飛ぶ|
|M10|controller|model 期待値の照合|期待外 model の応答が成功標本になる|
|M11|`assert_b4_certified_arm_pair`|`evidence_class == "certified"` の要求|test-only pair が正式受理される|
|M12|`create_b4_closed_critic_pair`|必須 keyword の既定値不在|record 無しの呼出しが通る|
|M13|git 実行|`GIT_*` 除去と executable 固定 (R4)|偽 `GIT_DIR` の object graph を読む|

**過剰拒否の正例 (受理集合を縮小する wave の必須登録):**

|ID|内容|期待|
|---|---|---|
|P01|10 欄が埋まった文書 + canonical record + 3 値一致 の完全な正例|両腕が成功し、receipt が `/v2` のまま、再検証も通る。**どの gate も過剰拒否しない**|
|P02|`runner=` / `executable=` 注入の既存負例に**有効な record を渡した**もの|拒否理由が `unexpected keyword argument` **だけ**になる (R11)|
|P03|record JSON を projection 閉包へ入れない固定|閉包 entry に record path が現れない (R10)|

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **B-4 実走の支配点 (R8)** — production factory は支配点ではない。`run_one_iteration()` /
   fixture main の直接呼出しを物理的に止めるか、downstream で B-4 名乗りだけを拒否するか。
2. **proposal への因果束縛 (R9)** — closed decision の hash と次 proposal の hash を鎖にする層。
   receipt 所持だけでは treatment を消費した証明にならない。**併走 wave の設計に直接効く。**
3. **外部 anchor (R6)** — append-only launch ledger / 署名済み one-shot token。
   これが無い限り「結果を見てから record を作る」攻撃は repo 内 Git で識別できない。
4. **実走前 model attestation (R7)** — payload 送信前に exact snapshot を固定する層。
5. **§5 残り 9 欄の型検査 (R3)** — 文書の書式が併走 wave で確定した後。
6. **active record の単一性 (R5)** — 固定 path 1 本に限るかどうかの文書側規約。
