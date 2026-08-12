read-only sandbox のため `$D/s6-revB.md` へは書き込めない。以下を同ファイルの完成本文とする。コード変更・テスト実行は行っていない。

# 段 6 レビュー B — scope 逸脱と記録の誠実さ

## 1. GO / NO-GO 判定

**NO-GO。must-fix 6 件。**

実装 commit の主要 8 項目は存在するが、裁定パッケージには Q1・Q2・Q3 の過大主張、production 結線済みと誤読させる記述、次 session への重要な申し送り漏れがある。

## 2. must-fix

### MF-1 — Q1 は性質の異なる B1〜B4 を「schema に入力が無い内部矛盾」と一括している

- **所見:** B1 は主張どおりだが、B2〜B4 は同型ではない。特に B3 を schema v2 の peer pointer 不足という内部矛盾へ分類した根拠は成立していない。
- **根拠:**
  - B1: schema には `cmake_cache` の値 object と `compile_commands` pointer しかなく、CMakeCache raw pointer は無い（`receipt-schema-v1.json:94-171`）。§6.3 は実体再読を要求する（`record-items-v2.md:600-608`）。
  - B2: 個別の `intent_ref` は実在する（`receipt-schema-v1.json:1092-1138`）。欠けるのは authoritative な母集合・namespace・create-only provenance であり、「入力そのものが schema に無い」より狭くないが、schema v2 だけが解法とは証明されていない。
  - B3: lensA は receipt-set consumer が pilot/main の両 path を受けて比較する具体経路を提示している（`s3-lensA.md:33-39`）。親の「producer 以外の誰が path を決めるか未定義」「producer path を信じると §8 違反」は `s4-adjudication.md:28-32` の独自推論であり、両レンズ原文からは導けない。示せるのは canonical receipt-set namespace が未定義ということまでで、schema 内 peer pointer が必須とは限らない。
  - B4: transcript raw pointer 自体は存在する（`receipt-schema-v1.json:941-955`）。欠けるのは canonical byte grammar、authority binding、数値実装契約である。
- **成果物影響:** ユーザーが不要な schema 再発行を選び、D282 pin と受理集合を過剰に動かす。
- **要求:** Q1 を B1=raw pointer 欠落、B2=外部母集合 authority 欠落、B3=receipt-set discovery/consumer 契約未裁定、B4=raw grammar・binding 未裁定へ分解し、「4 件とも同じ schema 入力欠落」という主張を撤回する。

### MF-2 — B5 の refuted 根拠は引用箇所と一致しない

- **所見:** `record-items-v2.md:803-813` は経路 3 の偽 raw に限定された残余であり、「観測終了から exec まで他の作業なし」を明示的に引き受けた逐語ではない。
- **根拠:** B5 の義務は `record-items-v2.md:623-630`。一方 `:803-813` は marker も性能 run も無い `post_performance_failure` と偽 kernel raw の話である。より一般的な producer 偽造残余は `:817-821` にあるが、package はそれを根拠にしていない。
- **成果物影響:** 検出不能な hidden work を「承認時に明示的に引受済み」と誤記し、§6.5 の保証範囲を無裁定で狭める。
- **要求:** `:803-813` による refuted 主張を撤回する。`record-items-v2.md:817-821` に含まれると判断するなら、その解釈と「validator は記録内整合だけを保証する」という上限を明記し、必要なら canonical decision に問う。

### MF-3 — Q2 は flat union の不成立を「平坦な manifest 全般の不可能性」へ一般化している

- **所見:** 親が否定したのは「D282/D291 の role を一つの `approved_blobs` 集合へ union する形」と「D291 の 2 role だけにする形」の二つだけである。
- **根拠:** D282 は payload projection の exact 一致を要求する（`docs/decisions.md:12874-12879`）。D291 の 2-role 閉包は「本 decision が承認する集合」についての scope である（`docs/decisions.md:13441-13468`）。decision-qualified な別 field を持つ単一 flat object、namespaced projection、二 manifest 等を禁止する逐語はない。package 自身も二 manifest が成立すると認める（`package.md:106-109`）。
- **成果物影響:** ユーザーへ設計択一を返す前に namespaced projection を「唯一」と誤って既成事実化する。
- **要求:** 「共有 `approved_blobs` flat union は両立しない」へ主張を限定し、表現全般の不可能性・唯一性を撤回する。

### MF-4 — Q3 は D291 の成立事実と D292 の効果を誤記している

- **所見:** 「3 文書の凍結承認 + fold は D291 として既に起きた」は偽である。また D292 が失効させるのは自動解禁としての十分性であり、3 文書承認を将来の解除条件候補から排除してはいない。
- **根拠:**
  - RP-4 の 3 文書は新 core v2・追補 B 再発行版・追補 P 草案（`output/insights/2026-08-11_t139-manifest-land2/package.md:116-140`）。
  - D291 の approved blob は 2 role ちょうど（`docs/decisions.md:13369-13377,13441-13447`）。追補 P blob は明示的に未承認（`:13392-13393,13462`）。
  - D292 が定めるのは解除権限と手続きだけで、解除条件の中身は定めない（`docs/decisions.md:13583-13588`）。
  - `b03` consumer を書かず §S7 #7 を [T-793] へ委譲する部分は D292 と衝突せず、有効なままである。
- **成果物影響:** 未成立の凍結を成立済みと記録し、将来の解除条件候補まで失効済みと誤認させる。
- **要求:** 「RP-4 の条件だけでは自動解除できず、別 canonical decision が必要」に修正する。3 文書承認が成立済みという記述を撤回し、委譲部分は維持する。

### MF-5 — 「休眠コードではない」は production caller の実体と食い違う

- **所見:** Git hardening は既存 module の穴を塞ぐが、その module を通る production 経路は存在しない。
- **根拠:** production 検索では `load_approval_payload` と `compose_core` は定義しかなく、`read_pinned_blob` の caller も同じ preregistration foundation 内部だけである（`orchestrator/preregistration/approval_payload.py:166-171`、`orchestrator/preregistration/erratum.py:668-684`）。`orchestrator/preregistration/` 外の非 test caller は 0 件。lensA/C も production sink 不在を明記する（`s3-lensA.md:115-133`、`s3-lensC.md:153-165`）。
- **成果物影響:** 現行 production gate が保護されたと誤読されるが、production の受理集合は動いていない。
- **要求:** `README.md:39` と `s4-adjudication.md:93-97` を「穴は既存 foundation にあるが、その穴を通る production 経路もまだ無い」に修正する。

### MF-6 — Q4 は防壁を発火させる production call edge を申し送っていない

- **所見:** 指定された4要件は `package.md:172-182` に入っている。しかし両レンズの中心所見だった production caller、B6 の第三 consumer、writer sink の支配点が落ちている。
- **根拠:**
  - official producer→writer と persisted receipt→validator→consumer の call edge（`s3-lensA.md:115-120`）。
  - 材料 report consumer による独立全履歴走査（`s3-lensA.md:58-64,108-113`、`record-items-v2.md:654-667`）。
  - canonical destination、binding mint、writer/consumer での repository/common-dir 再照合（`s3-lensA.md:153-160,185-190`）。
  - PBS preflight・driver・collector・`verify_receipt` 等の欠落（`s3-lensC.md:153-163`）。
  - D291 の full projection、historical rejects、approved values、operational state、role coupling（`s3-lensA.md:219-229`）。
  - `argv_raw` grammar、snapshot metadata/cap、reason branch の未裁定（`s3-lensA.md:137-190`）。
- **成果物影響:** 次 session も foundation-only で終わり、§S7 #1〜#3 が production で発火しないまま「統合済み」と記録される。
- **要求:** Q4 に実 production call edge、B6 consumer、writer sink、D291 全閉包、残る semantic/snapshot 契約を必須 acceptance として追加する。`b03` consumer は追加しない。

## 3. 裁定パッケージの主張 × 原文の照合表

| 主張 | 判定 | 照合結果 |
|---|---|---|
| Q1 B1 | 原文と一致 | CMakeCache raw pointer が無く、§6.3 の三者再読を構成できない |
| Q1 B2 | 誇張 | 個別 `intent_ref` は存在する。欠けるのは authoritative 母集合・namespace・create-only provenance |
| Q1 B3 | 歪曲 | canonical receipt-set 契約は未定義だが、peer pointer を receipt schema に追加することが唯一の解ではない。親の producer-path 論は原文に無い |
| Q1 B4 | 誇張 | transcript raw pointer は存在する。欠けるのは grammar・authority binding・数値実装契約 |
| Q1 B5 refuted | 歪曲 | 引用 `:803-813` は経路3の偽raw限定。B5 そのものの明示的引受ではない |
| Q2 flat manifest 不可能 | 歪曲 | flat union の不成立しか示しておらず、decision-qualified な単一 manifest 表現全般は排除していない |
| Q3 RP-4 失効 | 歪曲 | 自動解除としての十分性だけが失われる。3文書承認は未成立で、条件候補と委譲部分は残る |
| 付録 A | 落とし | Q1 の一括分類、Q2 の不可能性、Q3 の成立済み前提、「休眠でない」の撤回が無い |
| 付録 B | 原文と一致 | owner 観測訂正、部分集合不変、十分性を証明しないという上限は整合する |

## 4. scope 逸脱の有無

### 実装 commit

`db1e77ea` の変更は `orchestrator/preregistration/blobref.py` と新規 test 1 file のみ。manifest、resolver、`PreregBinding`、writer、semantic validator、vectors、snapshot API、D291 parser、`__init__.py` export、owner/digest 検査は紛れ込んでいない。`docs/`・`output/` の commit 差分も無い。

D264 の4名前非 export も維持されている（`orchestrator/preregistration/__init__.py:1-27`、`docs/decisions.md:12185-12190`）。

### RP-2 (a) の8項目

| # | 項目 | 実体 |
|---:|---|---|
| 1 | `PATH` 非継承 | 実在。`_GIT_ENV_ALLOW` から削除 |
| 2 | 絶対 path 起動 | 実在。`/usr/bin/git` 固定と不在 error |
| 3 | ambient `GIT_*` 破棄 | 既存実装。回帰 test 追加 |
| 4 | `GIT_CONFIG_NOSYSTEM` | 既存実装。回帰 test 追加 |
| 5 | `core.commitGraph=false` | 実在 |
| 6 | alternates/promisor 拒否 | 実在。alternates/http-alternates、promisor marker/config、partial clone を拒否 |
| 7 | `--no-pager` | 実在 |
| 8 | `core.fsmonitor=false` | 実在 |

したがって「未充足6・既充足2」の切り分け自体は正しい。

### 裁定表外の変更

`GIT_NO_LAZY_FETCH=1` は段4の8項目に無い scope 逸脱である（`blobref.py:171-185`、`s5-impl.md:9,26`）。

関連する partial/promisor repository はその前に拒否されるため、現実装から独立の受理集合差は示されていない。ただし挙動を変える環境防壁であり、段4未裁定の追加を commit message だけで正当化してはならない。

## 5. should-fix / nit

### should-fix

- `GIT_NO_LAZY_FETCH` は段4へ追補裁定するか、差分から外す。
- `http-alternates` は実装されているが専用負例が無い。項目6の回帰検査として追加対象にする。
- Q4 の選択肢 (a) は `PreregBinding` と raw snapshot API を component 一覧にも明記する。事実欄だけでは session scope から落ちうる。
- 「land しない」は S6 (a) の「複数 session 可・land は最後に1回」と整合し、判定は正しい（`docs/worklog.md:217-218`）。一方、security fix が main に届かない期間、branch の衝突、spool fragment の base/内容陳腐化、untracked package の散逸という損失は README に記録すべきである。

### nit

- 実装子の「8/8」は Git trust root の8小項目であることを明記し、当初の実装 scope 8件との混同を避ける。
- 現在の `output/insights/2026-08-11_t139-manifest-land2-s2/` は未追跡であり、実装 commit が触った証拠ではない。次 session への引継ぎでは所在と所有者を明記する。

## 総括

**NO-GO。must-fix 6 件。**  
最大の risk は、未結線の foundation を production 防壁と誤記し、次 session でも dormant gate を積むこと。  
実装の8小項目と6/2分類は概ね実在するが、`GIT_NO_LAZY_FETCH` は段4外である。  
Q1/Q2/Q3 と README/Q4 を原文の保証上限へ修正してから記録段へ進むべきである。