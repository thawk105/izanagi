## 総括

- コード差分は、観測済み thread_spawn 親の T-936 固有の拒否を実際に解消している。
- [T-886] の全走査、限定 fast path、SHA 検査、件数非 1 の拒否は意味上維持されている。
- ただし A4 実 corpus 測定は裁定の測定契約を満たさず、現在の land 証拠には使えない。
- R1 は別原因として切り分け可能だが、「実害が完全に消えた」という表現は観測済み thread_spawn 型に限定すべきである。
- pytest は実行していない。静的検査と既知 2 ID への限定 production probe のみ実施した。

## 所見

1. **[must-fix] A4 測定が production の全走査・例外境界を検証していない**

   - **判定:** real
   - **再現:** [probe_production_corpus.py](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/probe_production_corpus.py:53) は `_session_meta_rows` を memo 化し、同ファイル 88 行目以降で ID ごとの候補ファイルへ事前に絞っている。全 ID に対する `_find_rollout` 呼出しはなく、直接呼んでいるのは pin 5 label と T-936 の 2 ID だけである。絞り込みの全ファイル比較も 10 ID の抽出で、例外を握り潰している。
   - **再現:** production の `_session_meta_rows` は [読取失敗を空集合にする](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:232) うえ、JSON parse 失敗も内部で捨てる。この helper を包んで「例外 0」と数えても、裁定 A4 が求めた読取・parse 例外の列挙にはならない。また既存テストは、無関係ファイルの `ValueError` でも pin 無し全走査が失敗する契約を固定している [test_codex_reasoning_ab.py:2965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2965)。候補絞り込みはこの経路を観測しない。
   - **再現:** A4 JSON には「旧述語で一意だった全 ID の返り path が一致する」という比較がない。さらに 09:42 と 09:43 の probe 間で、同じ 3,646 file なのに path＋size digest が変わっており、live corpus の安定性も確認されていない。
   - **成果物影響:** 見落とした無関係ファイル例外や旧 path からの逸脱があれば、receipt の受理集合・`rollout_path`、golden の入力 rollout、prompt の参照元が変わるのに、現 A4 は緑を返せる。
   - **推奨:** 現 A4 を erratum として保存し、安定した corpus に対して、絞り込み・memo・例外握り潰しなしで全 ID を production `_find_rollout` へ直接通す。前後の全内容 digest、旧実装との path 完全一致、raw JSONL の読取・parse 異常、symlink・inode、変更 ID の consumer 検査、pin 5 label の候補・SHA・fast/fallback 経路まで記録する。

2. **観測済み thread_spawn 型では T-936 固有の実害が消えている**

   - **判定:** real
   - **再現:** `019fd52d…` を限定して production helper へ通すと、旧述語は親 1＋子 3の 4 file を候補にした。新述語では子 3 file が除外され、親 1 file に解決した。親について `_session_meta_rows` と consumer の `_rollout_details` が数える `session_meta` はともに 1 行で、`id == session_id == thread_id` も成立する。
   - **再現:** [collect_run](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3100) は旧状態では `_find_rollout` の `rollout count is 4` を `failure_reasons` へ積む。新状態では親を読み、[件数 1 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3114) と直後の identity 検査を通る。
   - **成果物影響:** 修正がなければ、この親 run は `rollout_path=null`、`valid=false`、`RC_SESSION` となり、正当な receipt が受理集合から落ちる。
   - **推奨:** 判定式は維持する。ただし「receipt 全体が必ず valid」ではなく、「T-936 に由来する rollout 解決・meta 件数・identity の拒否が消える」と記録する。

3. **R1 は残るが、観測済み T-936 とは原因を分離できる**

   - **判定:** real
   - **再現:** `019f690c…` は旧述語で 2 候補、新述語で親 1候補になる一方、親 rollout の `session_meta` は 4 行である。したがって `_find_rollout` は成功しても、`collect_run` は `session_meta count is 4, expected 1` を追加し、receipt は無効のままである。
   - **成果物影響:** R1 を直さなければ compaction/resume 型は受理集合へ入らず、修正前後で失敗理由、`rollout_path`、rollout SHA、場合によっては primary RC だけが変わる。
   - **推奨:** R1 は裁定パッケージとして明示的に返す。選択肢は現行 fail-closed、完全一致行だけの重複除去、先頭行権威化でよい。後二者は受理集合を広げるため独立レビューを条件にする。T-936 land の blocker にはしないが、普遍的な「実害完全解消」とは書かない。

4. **3 caller と [T-886] の経路に新しい契約破壊はない**

   - **判定:** real

   | caller | 修正が効く経路 | 効かない・不変の経路 |
   |---|---|---|
   | `collect_run` | pin 無し全走査で、子による親候補の水増しを除去する | 親自体が複数 meta、parse/read 問題、後段 receipt 不整合の場合 |
   | `render_prompt` | pin candidate が述語不一致または SHA 失敗で fallback した場合、新全走査が親を一意化しうる | 正常な名前 candidate＋SHA 成功は従来どおり fast return。既定では後段 SHA も再検証する |
   | `derive_independent_golden` | author/fix1/fix2 の fallback 全走査で同様に効く | 正常 fast path は不変。`verify_source_sha=False` では既存 R3 が残る |

   - **再現:** pin 無し経路は [全 `rollout-*.jsonl` を最後まで列挙](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:356) し、件数非 1 を拒否する。fast path は SHA 検査成功後だけ return する。`derive_independent_golden` と `render_prompt` の既定経路は返却後にも SHA を検査する。
   - **成果物影響:** この差分による pin 5 label の正常解決先、golden bytes、rendered prompt bytes の変更はない。
   - **推奨:** R3 の「SHA 失敗後の全走査 return」は既存欠陥として scope 外に維持し、今回直したようには記録しない。

5. **改名は repo 内では安全だが、commit message の caller 件数は最終 tree と一致しない**

   - **判定:** real、nit
   - **再現:** 変更前は定義 1＋production 3＋test 31、commit tree では定義 1＋production 3＋test 43 である。追加された 12 test caller を含め全 caller の第 2 引数は positional。monkeypatch double も positional で呼ばれ、signature introspection はない。payload の `session_id` は変更されていない。
   - **成果物影響:** repo 内の実行値・受理集合・参照への影響はないため nit。
   - **推奨:** 段 7 の記録では「改名前に列挙した既存 test caller が 31、commit 後は 43」と是正する。private helper を keyword で呼ぶ repo 外利用だけは speculative な互換破壊だが、land blocker にはしない。

6. **4 file は 2 型ではあっても、独立な fork producer の標本としては薄い**

   - **判定:** speculative（将来実害。判定式の順序感受性自体は real）
   - **再現:** 親行コピー 3 file は同一親由来の兄弟であり、実質 1 producer episode である。実装は `source` や fork marker を読まず、「子 meta が先、親コピーが後」という順序へ依存する。既存の逆順 fixture が、順序が変われば正当な親検索を 2 件拒否へ戻すことを固定している。
   - **成果物影響:** 別 Codex versionや別 fork producerが親行を先に書けば、正当な run が再び receipt 受理集合から落ちる。
   - **推奨:** 実測では件数ヒストグラムだけでなく、全 fork/subagent file を producer/version、親 ID、meta 順序、lineage 深さで分類する。変更された全 IDについて、旧・新候補集合、解決 path、consumer meta 件数と identity を記録し、可能なら元の launch artifactで `collect_run` を再生して T-936 関連 failure reason が消えることまで確認する。

## land 判定

**NO-GO**

コード差分そのものに新しい blocker は見つからなかったが、裁定 A4 を満たす実 corpus 測定が未成立である。所見 1の測定を全走査のまま差し替え、旧 path 完全一致・例外列挙・corpus 安定性・consumer 検査が通れば、コード面は CONDITIONAL-GO から GO へ進められる。