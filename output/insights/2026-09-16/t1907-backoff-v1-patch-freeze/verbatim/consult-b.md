## 所見

- [B-1] 影響テストの棚卸しに漏れがあり、未 commit・変異中の「緑維持」は成立しない  
  判定: real  
  深刻度: must-fix  
  根拠: `orchestrator/tests/test_p3_b4_wiring_probe.py:1521` の `test_source_and_test_are_the_only_non_output_worktree_changes` は `git status --short` を読み、`output/` 以外の変更を同 probe の実装・テスト2ファイルに限定する。新 patch、README の変更はいずれも許容されない。plan:203–223 の8件には含まれていない。さらに `test_login_headroom.py:1602` の `test_ceiling_numeric_literal_occurs_only_in_login_headroom_module` は tracked/untracked 全ファイルの本文を読むため、これも棚卸し漏れ。ただし保存予定 bytes に禁止数値式はなく、こちらは緑維持の予測でよい。  
  一方、指定の正式受入は `tools/dev_wave_wait.py:3889–3901` で clean を要求するので、**commit 済み・clean の通常受入まで失敗すると断定するのは誤り**。  
  成果物影響: テスト対象集合と実行時の Git 状態を区別しないと、受入・変異レポートの失敗原因と期待 node 集合が誤る。  
  提案: 棚卸しに上記2件を追加し、「保存後未 commit」「commit 済み clean」「変異中」を分けて予測する。既存テストの期待値は変更しない。

- [B-2] M1 の期待失敗1件は、runner の収集集合を固定しない限り完全集合ではない  
  判定: real  
  深刻度: must-fix  
  根拠: M1 は新 patch を変更するため、全 suite に B-1 の変更面テストが含まれる場合、裸 token 在庫テストに加えて同テストも赤になる。M2・M3・M5 も同じ変更面テストに反応するため、全 suite に対する SURVIVED 予測は成立しない。`tools/mutation_harness.py:2097–2099` は期待・観測 node の完全一致だけを KILLED とし、差があれば MISMATCH とする。DW-M01/M03/M08 に対して、plan:241 の「既存 suite に対してのみ単一拒否」という限定では不足する。  
  コメント anchor 自体は確保できる。`git show f7a5444 | grep -n -F …` で次の行は blob 内9行目の1箇所だった。

  ```text
  +# izanagi: static backoff magnitude (us) to bypass Cicada's adaptive hill-climb.
  ```

  この行の末尾へ token を足せば、条件指令・CMake mapping・行数を変えない。`test_ccbench_spawn_sites.py:632–682` の define 抽出には新 macro を加えず、`test_p3_s4_loop.py:7847,7871–7878` の未登録 token 拒否に該当する。同じ regex を使う `test_t2187_adaptive_const_probe.py:431` も見つかったが、固定の別 patch を読むため新ファイルには反応しない。裸 token 拒否そのものに日時依存はない。  
  成果物影響: M1 が MISMATCH になり、M2等の「生存によって保存 bytes の検出力不足を示す」というレポートも成立しなくなる。  
  提案: 変異 runner の node 集合を事前登録する。8件などの限定集合を使うなら、その集合に対する検出力と明記し、全 suite の単一拒否と呼ばない。全 suite を使うなら変更面テストによる冗長拒否を記録し、単一理由の証拠から外す。完全集合を確定できない初回は DW-M08 の probe として扱う。

- [B-3] M4「ファイル削除」は現行 harness の spec では表現できない  
  判定: real  
  深刻度: must-fix  
  根拠: `tools/mutation_harness.py:623` は replacement の key を `{file, old, new}` に限定し、`:1049–1070` は固定 HEAD の通常ファイルと working tree の一致を要求する。注入は `:2230` の `write_text`。全文を `new=""` に置換しても空ファイルになり、削除にはならない。未知の `delete` 等の key は起動前拒否となる。  
  成果物影響: 空ファイル化を「欠落の検出力を調べた」と誤記するか、spec が実行前に停止する。  
  提案: scope を広げず、M4 を「全文を空文字へ置換」に変更して意味の違いを明記するか、削除候補を未実施として残す。M2・M3・M5、および空ファイル化版M4を生存期待で登録する場合は、B-2 の runner 条件を満たしたうえで次を使う。

  ```json
  "category": "negative",
  "expected_status": "SURVIVED",
  "expected_nodes": [],
  "hang_risk": false
  ```

  `replacements` は非空、`old` は最終 HEAD 内で一意、`new` は `old` と異なる文字列が必要。M3 は元全文から476a128全文への置換にできる。DW-M04 に従い注入 diff を確認し、SURVIVED を equivalent や保存要件の合格と呼ばない。

- [B-4] overlap probe の「0」は限定された現況観測であり、全編集面・将来作業の非重複を証明しない  
  判定: real  
  深刻度: should-fix  
  根拠: `probe_overlap.py:33` の対象は同一 Git 管理下の登録 worktree のみ。`:52` で自分を除外し、`:56` は `main...HEAD`、`:69–80` は各 HEAD とディスクの比較、`:83` の untracked 走査は直下 `patches/*.patch` に限る。したがって次は観測外または不完全である。

  - 独立 clone、未登録の作業場所、将来編集予定、未保存の編集。
  - main の変更をまだ取り込んでいない古い branch の、main に対する取り残された差分。三点 diff と HEAD 対ディスク比較では検出されない。
  - HEAD に存在しない untracked README、patches サブディレクトリ、新規の凍結ファイル。
  - index だけにある変更。ディスクが HEAD と一致する staged 差分は読まない。
  - diff 失敗。`:58–59` はエラー文字列にも SURFACE filter を適用するため、失敗表示自体が落ちうる。

  **既存 tracked の `patches/README.md` の保存済み編集は見逃し例にならない。** `SURFACE` が `patches/` に一致し、HEAD 比較で検出される。  
  `docs/worklog.md:2310` と insight:239–248 の残作業は cohort の地位、独立監査、機序、未了解析、論文図などであり、新 v1 patch や `patches/README.md` の編集予定は記載されていない。現在の記述から衝突を予測する根拠はないが、将来も触れないとの保証にはならない。  
  成果物影響: 編集面非重複のレポートが、観測範囲を超えた保証として残る。  
  提案: F5 を「記録時点の登録 worktree に対する、当該比較方法での検出0件」に限定する。128は列挙数で、自分を含む全128箇所を比較したという表現は避ける。提供ログの所見付き見出しは再計数で20件だった。

- [B-5] provenance の結論は正しいが、混合 commit の docs author と scope を具体化すべき  
  判定: real  
  深刻度: should-fix  
  根拠: `tools/check_ai_provenance.py:78,1589,1631` により新 `.patch` は実装面であり、bytes コピーでも Codex author が必要。一方 `patches/README.md` は `:1591–1592` で実装面外となる。`docs/ai-provenance.md:51–53` は Claude 親の manager/integrator/reviewer と docs scope の author を認め、同 role 複数行では全行の scope が必須。plan:197 の「Codex author を記録する」だけでは混合 commit の記録例が不足する。  
  成果物影響: author 2行の scope 欠落なら監査違反となり、Claude の docs 著作を省けば寄与記録が不完全になる。  
  提案: patch・README・insight・spool を1 commit にまとめ、親が管理と docs 著作を担う場合の形は次。

  ```text
  AI-Agent: product=codex; model=unknown; reasoning=unknown; role=author; scope=v1-patch
  AI-Agent: product=claude; model=unknown; reasoning=unknown; role=author; scope=docs
  AI-Agent: product=claude; model=unknown; reasoning=unknown; role=manager
  ```

  分ける場合、patch commit は Codex author と、実質的に寄与した親の manager 等。README・insight・spool だけの docs commit は Claude author でよく、**実装面契約による Codex author は不要**。親が採否・競合解決等を担った場合だけ integrator、独立レビューを担った場合だけ reviewer を追加する。採用された本点検等の reviewer 寄与も別途記録する。  
  上例の `unknown` はモデル等が確定していない場合の値であり、親・実装子の実際の表示値が分かれば置換する。非表示の場合は規約どおり `not-exposed` を使う。

- [B-6] brief の生成日と plan の一部行番号に誤りがある  
  判定: real  
  深刻度: nit  
  根拠: read-heavy WAL の先頭 `ts=1782624851.233902` は `date -u -d` で **2026-06-28 05:34:11 UTC**。追加 commit も `2c59dc3d3 2026-06-28`。brief:12 の「旧3 WAL は6月22日生成」は誤りで、plan の訂正は妥当。plan P3 の逐語位置には次のずれがある。

  | 引用 | 実際 |
  |---|---|
  | `ident.py:141` の `if actual != expected` | 条件は140、141は raise |
  | `ident.py:203` の admission 必須条件 | 204 |
  | `ident.py:373` の完全 preimage 比較 | 379。373は別の v2 lock 拒否 |
  | `ident.py:484` の identity 照合呼出し | 一致 |

  成果物影響: 根拠追跡の参照が別条件を指し、旧実験の生成時期も誤って記録される。  
  提案: brief の日付と引用位置を修正する。preimage 照合が repair より先という結論自体は維持できる。

- [B-7] subshell・noclobber が repo hook に拒否されるという疑義は、静的には支持されない  
  判定: refuted  
  深刻度: nit  
  根拠: `hooks/guard_bash.py:81–119,2724–2753` の防護対象に提案先は該当しない。括弧は segment 境界であり、それ自体を一律拒否しない。提示された `git show <blob> > patches/...` は保護対象への書込みではなく、`git hash-object` も当該通常パスについて保護対象 allowlist 判定に入る理由がない。`hooks/README.md:79–100` は launcher に live attestation がないことを明記している。  
  成果物影響: 静的判定上、保存 bytes や受理集合への悪影響はない。  
  提案: 提示手順を維持してよい。実際の workspace-write が当該 worktree を writable root とすることは実装時に確認する。`git cat-file blob <同一blob>` でも同じ bytes を得られるが、sandbox の書込み拒否を解消する代替ではない。拒否時は権限境界を迂回せず、失敗を記録する。

## 成立しなかった点検

- **plan が列挙した8件そのものが、clean な追加後に赤になるという攻撃は成立しない。** `_patch_added_define_interfaces` の実在在庫を読む呼出しは7箇所。f7a5444 と現行 eb319d8 の diff は追加式1行の差だけで、非追加行から作る `global_prior_tokens`、define key、non-TU 集合を変えない。裸 token 在庫にも f7a5444 は新 token を加えない。問題は B-1/B-2 の棚卸し範囲と実行条件である。
- **別の新 patch 読者が M1 token 自体を拒否するという攻撃は成立しない。** 見つかった別 regex 利用は固定の別 patch が対象だった。ただし任意動的コードまで含む完全性は証明していない。
- **SHA・blob の誤りは成立しない。** 再計算した f7a5444 の SHA-256 は `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911`、現行 patch は `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a`。凍結3ファイルと3 WAL の SHA も plan の全値と一致した。
- `git rev-parse` で導入 commit `4f7bb3c76325b7f97a9efda071b92a84732d375e`、取得元 `4dfd3785b^:patches/silo-backoff-fixed.patch` の f7a5444、現行 eb319d8 を確認した。指定の `test_ccbench_spawn_sites.py:632`、`test_p3_s4_loop.py:7842` は実際の glob 位置と一致した。
- 現行 SHA の literal は実施した検索範囲で15ファイルに現れた。ただし、literal の出現数だけから全件が機械的 pin であるとは判定していない。
- `.py/.sh` 等に対象を限定する実装在庫検査、固定 ledger 読者、`check_docs.py` の LIVING_DOCS/PATH_REF も確認した。`patches/README.md` の新 SHA と新 patch bytes を照合する既存検査は見つからなかった。

## 未確認事項

- pytest、build、計測、変異 harness、provenance 監査、正式受入、hook の live 発火は実行していない。合格・KILLED・SURVIVED の実測結果はない。
- 最終 mutation spec と runner argv が未提示のため、期待失敗 node の完全性は確定していない。
- author 子の実際の writable root、hook trust、起動経路は未確認。
- 提供 overlap ログを現在の全 worktree に対して再実行していない。独立 clone・未来の編集予定も未確認。
- brief の v1 SHA 参照0件、campaign ID 3組、前像の submodule blob は今回独立再計算していない。
- WAL の実使用 patch bytes とホスト帰属は本点検では確定していない。
- 推測した campaign 直下の `wal.jsonl` は不在だったが、`rg --files` で実在する `runs/wal.jsonl` を特定し、そちらの SHA を照合した。
- ファイル書込みと Git 状態の変更は行っていない。

## 総括

**v1 bytes の別名保存という実装方針を退ける根拠は見つからない。ただし、現行 plan の変異計画はそのまま通せない。**

実装前に、影響テストの棚卸し、変異 runner の収集集合、M1 の単一理由性、M2〜M5 の生存予測、M4 の削除表現を修正する必要がある。保存 bytes・現行 patch・凍結物の SHA は plan と一致した。scope を広げる新 gate・pin test・ledger entry は必要ない。