## consumer 取り残し

以下は静的検査の結果です。ファイル編集・git 状態変更・pytest 実行は行っていません。参照の略記は次のとおりです。

- `D`：`orchestrator/campaign/s8b_oracle_driver.py`
- `T`：`orchestrator/tests/test_s8b_oracle_driver.py`
- `R`：`orchestrator/campaign/s8b_ratified_freeze.py`
- `P`：射影された `s2-plan.md`
- `B`：射影された `stage1-brief.md`

**B-1 — severity: should／判定: real（未使用引数）、refuted（既存 consumer が削除を妨げる）**

core の `ratified` を残す必然性は、既存 consumer からは見つかりません。

- public→core は **5 callsite**：`D:619,632,646,655,677`。`ratified=` を渡すのは `D:624,638` だけ。
- `test_s1_known_axes_freeze.py:1145` の kwargs は `verified` までで、`ratified` は含まない。
- `T:2859` の core 直呼びも `ratified` を渡さない。
- `T:5146,5230` の recording fake は `_gate_check_validated` の差し替え先（`T:5174,5249`）。core の引数削除とは独立。
- `real_repo_ratified_memo.py:37` は **public** 引数の説明。public signature を維持すれば変更不要。

**推奨：** 親の P2 削除案が既存 consumer との整合上は成立します。ただし、plan が優先した「core へ `ratified=` を直接注入して構造化 refusal」を受入条件として維持するなら、保持案も成立します。その場合は「既存互換性のため」ではなく「この負例を維持するための未使用引数」と明記してください。削除案なら、直接注入負例を public の `ratified=`＋二読 race に置き換える方法があります。

**B-2 — severity: nit／判定: real**

docstring 改訂は行単位で計画されていますが、開始行が一行ずれています。

**根拠：** `P:99` は `D:429〜435` を置換対象としますが、古い説明は `D:428` の「`ratified` … は v2 経路」から始まります。`D:488〜489` のコメントも、現状では独立した bytes/active 照合を説明しています。

**推奨：** docstring は **`D:428〜434` 全体**を置換し、v2 枝のコメントも exact token 必須という実装に合わせてください。public の loader 説明と memo docstring は残してよいです。

## 最小差分と scope

**B-3 — severity: should／判定: refuted（P1 維持が過大変更という懸念）**

core の freeze 再読を残す推奨は妥当です。

**根拠：**

- `D:615` の初読失敗後、`D:459` が再読する。
- 再読失敗の例外は `D:461`、known-record 欠落は `D:511〜522`、null 診断は `D:524〜527` で集約される。
- 再読を単純撤去すると、初読失敗→v1 再読成功の経路も失う。初回例外を渡す方式では、二回目の例外本文を保持できない。
- `P:114〜121` は受理集合・refusal 集合・追加編集範囲を比較している。

**推奨：** P1 維持。約22行の v2 枝置換と docstring 修正に集中する方が D1872 の局所修正に合います。新しい production helper、dataclass、public signature 変更、library 強制、caller 閉包テストは不要です。

**B-4 — severity: should／判定: refuted（sha 条件を全部削除してよいという案）**

sha 比較には恒等比較がありますが、条件全体の削除は同値ではありません。

**根拠：** token 使用時は `D:452〜453` で同じ ratified の document/hash を採用するため、`freeze_sha != launch_validated.ratified.sha256` は通常の値では恒偽です。一方、`R:750〜762` の dataclass は constructor で `sha256=None` を拒まず、現行 `D:503` はこれを拒否します。

**推奨：** plan の保守的な保持案を支持します。整理するなら `freeze_sha is None` は残す必要があります。この比較を requested path と active 世代の独立照合と説明してはいけません。

## 新規 test の実効性

**B-5 — severity: should／判定: refuted（plan の負例が旧コードでも同じ拒否になるという懸念）**

P3 の hash 一致 fake と局所 patch を揃えれば、修正前後を弁別できます。

**根拠となる旧コードの経路：**

1. `D:615` が一回目の例外を受け、`D:619` から core へ入る。
2. `D:459` が二回目の `VerifiedFreeze` を得る。両箇所とも同じ module-global `_load_verified_freeze` を参照するので、一つの `patch.object(driver, ...)` が両方を捕捉する。
3. 合成 resolution が `never-issued` なら `D:245〜246` で adapter は `None`。
4. floor/budget が `{}` なら `D:477` の v1 枝を通らず、旧 `D:496` が static loader を呼ぶ。
5. fake の sha が一致すれば `D:503` の refusal は発生しない。
6. known-axes verify を no-op、manifest を省略すれば残る refusal はなく、`D:191〜197` により **旧コードでは `allowed=True`**。
7. 修正後は missing-token refusal が一件となる。

direct core の片側 null ケースは旧コードでも null refusal で拒否されますが、旧コードには missing-token refusal がないため、exact 集合で弁別できます。

**推奨：** plan の P3 を採用。`AssertionError` fake は旧コードが `D:499〜502` で refusal に変換するため、受理差の中心的な証拠には hash 一致 fake の方が適切です。

**B-6 — severity: should／判定: refuted（tmp root のままで exact 集合を固定できるという前提）、plan は対処済み**

無加工の tmp root では、receipt と known-axes の追加 refusal が発生します。

**根拠：**

- `t080_freeze_migration.py:2288` は receipt の有無より先に `_capture_head` を呼び、`:639` から Git を実行する。Git repo 外なら通常は `receipt.git_error`。
- `D:170〜182` はこれを invalid resolution にし、`D:191` が gate refusal に合流させる。
- `known.json` がなければ `s1_known_axes_freeze.py:984〜985` が `FreezeError`、`D:522` が `known-axes-freeze-verify:` を追加する。

**推奨：** `P:153〜155` の resolver 差し替えと known-axes no-op を維持してください。この限定された fixture なら **集合＋件数の exact 固定が可能**です（既存形式は `T:285〜292`）。「含む／含まない」へ弱める必要はありません。

**B-7 — severity: nit／判定: refuted（合成型構築・新規登録が必要という懸念）**

合成型の直接構築はテスト内で許容されます。新規 file に real-repo／xdist 登録も不要です。

**根拠：**

- `R:754〜756` の禁止対象は production module。
- `test_s8b_ratified_freeze.py:2668〜2678` の静的テストは `campaign/*.py` だけを走査。
- `T:2826〜2838` に既存の直接構築例がある。
- `conftest.py:2145〜2152` は登録済み real-repo node に resource 属性・group を付与する。合成 object と局所 patch のみなら該当資源を使わない。
- `tools/acceptance_shards.py:396〜404` は未登録の新規 node に既定重み **1秒/node** を与える。shard の手動登録は不要。

**推奨：** driver が保持する module の型を使ってください。plan は9関数ですが parameterize 後は少なくとも14 node、loader error を2例外×3形状にすると18 nodeです。したがって shard 重みは14〜18秒相当になります。これは実所要ではなく割付け値であり、「全体1秒級」「受入5分以内」は後段の実測事項です。

## 焦点集合の完全性

**B-8 — severity: should／判定: real（第一焦点集合は全 consumer 集合ではない）**

plan は主要 consumer を拾っていますが、第一焦点集合を「全部」と扱うことはできません。

**根拠：**

- `T:1793` の直接 public consumer  
  `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` は第一焦点リストにない。
- `_run_v2` consumer の `test_transient_prepare_failure_retries_once`（`T:4603`）、report 統合（`T:5985`）、post-run store（`T:6051`）なども第一焦点外。
- plan 自身が `P:267` でこれらを受入全走へ送っており、検査からの完全脱落ではない。

二段の helper 追跡も成立します。

- driftguards `:300` → `_broken_binding_manifest:230` → `T:2509` の `_synthetic_freeze` → `s8b_v2_freeze_fixture.fill:71`。
- 同 fixture の `fill` は `per_pair_floor:39`／`budget:59` を呼ぶデータ構築で、gate を別名で呼ぶ隠れた入口ではない。
- `T:5677` の `_build_v2_repo` は `v2_fixture.budget` と `ratified_fixture.load_emitter_g1` に接続。
- memo は `patch_ratified_loader:112` → `memo_loader:103` → `real_repo_ratified:92`。driftguards `:516,533,558,581` の positive control は plan に含まれる。

**推奨：** 「第一焦点＝代表経路」「残り＝受入全走」と明記し、全 consumer の焦点包含を要件とするなら上記を追加してください。既存 CLI subprocess node は `P:248` に含まれていますが、実コマンドは **`run-block`**（`T:5070`）。今回の `gate-check` transport は新規 in-process node が直接担当します。

## 親の brief の検算

**B-9 — severity: must-fix／判定: real（I1 と I3 の文言不整合）**

brief の I1 を字義どおり読むと plan は違反します。

**根拠：** `B:33〜34` は exact token がある場合だけ「gate predicates へ進める」としています。一方、plan は token 欠落・ratified error の refusal 後も `D:509` 以降の known-axes／floor／budget／manifest 診断を続けます。これは `B:37〜38` の既存 refusal 集合維持のために必要です。

**推奨：** I1 を「exact token なしの v2 は受理しない。拒否理由の集約は継続する」と訂正してください。early return を追加して I1 に合わせると I3 を破ります。これは実装範囲を広げる理由にはなりません。

**B-10 — severity: should／判定: refuted（正規 v2 が adapter で token 必須を迂回するという懸念）**

親の adapter 読解は、正規 loader が返す bytes/document/hash の対応を前提として成立します。

**根拠：**

- 発火には `D:260` の receipt holdout hash 一致が必要。
- receipt は `t080_freeze_migration.py:2134` で schema 検証され、`:443〜450` で `HOLDOUT_RAW_SHA256` に固定される。
- `:48` の定数は実ファイルの SHA-256 と一致した：  
  `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- 対象 freeze は `output/s8b-freeze/holdout_freeze.json:622〜623` で floor/budget とも null。
- adapter 内も `D:268〜277` で raw bytes を再照合する。

**推奨：** adapter 前への新 gate は不要です。ただし、任意に偽造した document/hash の組まで保証したとは書かないでください。

**B-11 — severity: nit／判定: refuted（既存 T の編集が必須）、real（brief の件数誤記）**

調査した consumer には、今回の変更で既存期待値の変更が必須になる node は見つかりませんでした。

**根拠：**

- historical token は `D:436` の型拒否で従来どおり。
- standalone 正常／不正 floor／injected candidate は `D:644,664` の full validation を維持。
- no-active payer は `T:4217` の `run_block` で、core 到達前の処理。
- known-axes 直呼びは既定 v1 freeze。
- private fake と caller 固定は B-1 のとおり独立。

**推奨：** `test_s8b_oracle_driver.py` 非編集方針を維持できます。ただし実行上の緑は未確認です。編集面 **402〜685行は包含範囲として正しい**ものの、P2 保持案なら実変更は docstring と v2 枝に限られます。`B:50` の「4 callsite」は5へ訂正してください。

## 総括

plan の実装方針は概ね成立します。**P1 維持・P3 の hash 一致 fake を支持**します。P2 は既存 consumer の制約ではなく、直接注入負例を残すかどうかの選択です。

必須訂正は **I1 を受理禁止と診断継続が両立する文面にすること**。併せて docstring 開始行、callsite 件数、第一焦点と全走の区別を修正してください。既存テストファイルの編集必須性、adapter による正規 v2 の迂回、新規 file の登録必須性は反証できました。

テストの緑・変異 KILLED・受入5分以内はいずれも未実測です。