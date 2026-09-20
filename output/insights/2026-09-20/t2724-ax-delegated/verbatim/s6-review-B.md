## 検査範囲

`947fd160a..ca3907e57` の4 commit、未 commit docs、指定資料・実測ログを検査した。pytest・loader・full scan は実行していない。digest はファイルを変更せずメモリ上で独立再計算した。

以下、repo 内の path は worktree 相対、`J/` は指定 job directory 相対。

## RB-1 — real・must-fix：決定 fragment が研究上の解釈まで裁定済みにしている

**箇所:** `docs/spool/decisions/2026-09-20-dev-wave-t2724-ax-delegated-1.md:25`

「AI が自己承認した世代」「論文で『人間が批准した holdout』とは書かない」「影響は B-2 / B-3 側に限る」は、`J/ruling-13-2x.md:3` の逐語からは導けない。裁定はユーザーによる委任と AI による record 作成を定めている。A commit 本文も「承認の主体はユーザー」と記しており、「自己承認」という断定とは一致しない。

ここは「ユーザー裁定に基づき AI が A/X を作成した。人間による commit 操作を証明するものではない」までに限定する。論文での批准の呼称・独立性・主張への影響は、必要なら裁定パッケージ候補へ戻す。

同 fragment `:36` の「採らない案」は、none の偽装、複数 trailer、hook 解除、role/product 必須化については逐語裁定と整合する。問題は上記の研究上の解釈を「決定」に含めた点である。

## RB-2 — real・must-fix：B-7 の授権説明が決定 fragment に反映されていない

**箇所:** 同 fragment `:32`、`J/s4-ruling.md:24`

fragment は依然として「D2166 と同じ根拠と扱い」とだけ書く。文字どおり「同一手続」とは書いていないが、B-7 が要求した次の限定が抜けている。

- A/X 導入の事前授権から必然となる期待変更。
- 赤を見る前に更新対象3 literal を固定。
- 独立レビュー、変異2件、追加・1 byte 変更・A欠落・X欠落の負例。
- 未実施の検証は未実施と記録。

D2166 の旧測定維持・新 phase 非成立という扱いは引き継げる。一方、別 context に送った先例の手続まで同一視しない説明へ局所修正すべきである。

## RB-3 — real・must-fix：受入所要の不変を根拠なく一般化している

**箇所:** `J/s4-ruling.md:23`

「6 node は hold のまま」から「受入所要は不変」は導けない。今回、通常受入に入る補完2本と trailer 正負例・parameterize も増えている。hold が維持するのは対象6本の通常受入での実行状態である。

親ログは次を示す。

| ログ | 対象・結果 | pytest 所要 |
|---|---|---:|
| `J/focus-held1.log:359` | 変更前期待値の6本、6 failed | 78.22秒 |
| `J/focus-held2.log:42` | 修正6本＋補完2本、8 passed | 103.26秒 |

両方とも `gen_S` への dispatch であり、login 実測ではない。対象集合も違うため、この比較から増減や不変を判定できない。

「6本の hold は維持。通常受入所要は未検証」と訂正すべきである。「本 wave では launch memo を足さない」は scope 判断として妥当だが、恒久的に不要という性能結論ではない。author 報告は実走・未実走を分けており、同種の一般化は認めなかった。

## RB-4 — refuted・修正不要：scope 外への実装上の滲み

**箇所:** `orchestrator/campaign/s8b_ratified_freeze.py:558`、`:596`

既存関数を AST 比較した結果、変更された production 関数は `_assert_user_commit` だけで、新規関数は `_user_commit_trailer_problem` だけだった。

hook 本体、CLI、鍵署名、床値、certification、W-4/W-5 の実装、`_launch_validate`、`_JOURNAL_KEYS`、hold、memo 実行ロジックの変更はない。B-10 job の変更も定数1 literal に限る。

`role=author` や `product=codex` の必須化はない。文法複製と同期テストは s4 の明示採用事項であり、追加の一般的 gate・台帳ではない。

## RB-5 — refuted・修正不要：新 B-10 pin は A/X だけで説明できる

**箇所:** `orchestrator/tests/test_backoff_extended_sweep.py:1671`、`:2014`、`tools/pegasus/b10_backoff_grid.sh:22`

独立再計算で一致した。

| 対象 | file数 | digest |
|---|---:|---|
| 現 tree | 22 | `92099c87e93536ebecf28e85ebf60222716e0b20c179c94e50dc2fb15ef2f8bb` |
| A/X の2件だけを除いた対照 | 20 | `6a4ee1ef58e7e9968a11bf9f2d1e0a5badca46bec5e7bf2b44aec63fa2f52415` |

対象 directory 内の Git 差分も A/X の追加2件だけ。算法・対象 directory・完全一致比較・前後の `fail 2`・`completion.json` は不変である。

sorted path＋NUL＋bytes の入力列は、通常 file の追加、1 byte 変更、A欠落、X欠落で変化する。SHA-256 の衝突を除けば digest は不一致になる。今回もメモリ上の4対照で全て不一致を確認した。これは親の変異 harness 実走を代替するものではない。

A/X は各追加1件、X の親は A ちょうど1件。両 script の `open("xb")` を現物確認し、A blob の SHA は pointer 内の `approval_sha256=3787d97b…` と一致した。trailer も各1行の構造化形式である。

## RB-6 — refuted・修正不要：P3 の2拒否を両方 (ii) とする分類は妥当

**箇所:** `J/p3/after-g1.json:1`、`orchestrator/campaign/s8b_ratified_freeze.py:2047`、`orchestrator/campaign/s8b_floor_campaign.py:7620`

| 実測拒否 | 分類 | 根拠 |
|---|---|---|
| `holdout.unknownness_layer2`、hit 4/4 | **(ii)** | before-g1 にも存在する既存 official 成果物・候補の hit。launch 失敗により完全一致検証への委譲が成立していない |
| `journal-state-invalid`、`reservation-preflight` | **(ii)** | producer が正式に書く event と validator の受理表の不整合 |

official journal の2行目は、producer の `reservation_record` と一致する field 構成を持つ。producer は `launch-start` の後にこれを `_journal_append` する。したがって「未知 event」だけを journal 破損の根拠にはできない。ただし journal 全体の正当性まで証明したわけではない。

段階6の `generation-introduction` も静的に裏付けられる。`:3535` は result の導入集合を `{G}` に限定するが、実導入は `cc82edc8c`。これは**前段を通過した場合の後続 blocker**であり、今回観測した2つ目の launch reason ではない。間に他の拒否がないことも未証明である。

今回の2拒否に (i) の A/X 不備や (iii) の spec 承認拒否は認めない。A/X exact exemption は後段なので、その成功は未確認。

v1 の before/after JSON は完全一致し、既知4拒否のまま。runbook §1.1・§2の表と整合する。

## RB-7 — 条件付き・検証上の留保：帰結の完全閉包までは宣言できない

**箇所:** `orchestrator/tests/test_s8b_oracle_driver.py:4087`、`:4608`、`orchestrator/tests/test_s8b_binding_driftguards.py:319`、`:326`

対象6本の真値変更と補完2本は確認できた。補完は no-active と manifest schema 拒否の exact 集合、prepare/evaluate 未呼出、出力・budget・marker 未作成を検査する。拒否理由の置換だけで検出力を失う変更にはなっていない。

指定された周辺面では追加変更の必要を認めなかった。

- `test_frozen_artifacts.py:171,234`：固定23 key の検査であり、A/X を未知 file として拒否しない。
- `s8b_floor_campaign.py:318,5481`：適合 A/X を chain record として列挙し、digest に含める。
- `s8b_holdout_freeze.py:45`：freeze namespace の既存除外内。既存4 hit は解消しない。
- `test_hooks.py:229`：fixture root の path 拒否検査。
- `test_b10_backoff_grid_job.py:423`：fixture digest に置換。
- `check_docs.py:4033,6417`：dispatch 契約に A/X 依存なし。
- `conftest.py:1739`、`acceptance_shards.py:404`：未登録 duration は欠測として扱い、配分重み1秒にする。実測時間の保証ではない。
- ratified memo の positive control は stub の object 同一性を検査し、実 repo の no-active 固定値を要求しない。

追加の **A/X 起因** consumer は発見しなかった。ただし静的読解と8本の焦点ログだけで、全受入・動的 root 経路・後段 full scan の閉包を保証しない。親の受入全走が必要であり、ここで追加 gate や memo を作る根拠にはならない。

## RB-8 — 条件付き・land 前 must-fix／一部 nit：docs に未完成の参照と古い現在形が残る

**箇所:** `docs/phase3-8b-restart-runbook.md:326,336`、`output/insights/2026-09-18/t2724-freeze-g1-gen/README.md:145`

新規一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md` は検査時点で存在しない。段7で作成予定なら現段階の留保でよいが、参照先を欠いたまま land はできない。そこに P3 の2拒否、後続 lineage は静的予測であること、検証未達を記録する必要がある。

局所修正・削除で済む nit も残る。

- runbook `:327` の「main には載せていない」は chain 導入後の現在形として古い。
- 同 `:347` の「現在は active freeze が無く」は発効後と矛盾する。W-4 の実装変更とは別の文書帰結。
- `s8b_ratified_freeze.py:547` の `_is_none_commit` docstring は「人間 commit か」「C1-6 の二重判定」のまま。関数本体を変えず、逐語 trailer 判定という説明にできる。

一方、改訂注記の A/X SHA・trailer 形、hooks F6a の「認証防壁ではない」、runbook の loader 成功と `allowed:false` の区別は実体と整合する。P2 の5 passed もログと一致し、held 部分を全 bytes 検証済みとは呼んでいない。

追加テスト・定数には、削除を必須とする過剰実装は認めなかった。

## 総括

**must-fix 一覧**

- **RB-1:** 「AI の自己承認」と論文上の主張制限を裁定済みにせず、委任の事実へ限定する。
- **RB-2:** B-10 pin の授権説明を s4 B-7 の限定と検証条件へ更新する。
- **RB-3:** 「受入所要は不変」を撤回し、hold 維持と所要未検証を分ける。
- **RB-8（land 前）:** 参照先の一次資料を作成し、P3 未達と検証範囲を記録する。

**次 wave の裁定パッケージ候補:** official journal producer と validator の契約整合、result 導入順と段階6 lineage の設計択一、必要なら論文での批准・独立性の表現。W-4 の spec 承認は別手番。launch memo の要否は将来の実測後に判断する。

**採否推奨:** 実装差分は支持する。上記の記録修正と親の残検証を条件に採用可。ただし、**批准成功をもって P3 受理達成・wave 完了とはしない**。