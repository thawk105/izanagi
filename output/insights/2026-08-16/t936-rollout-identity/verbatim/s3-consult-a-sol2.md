## 総括

- **結論は NO-GO。** 第 2 条件を利用して、一行追加だけで曖昧状態を別 file の受理へ変換できる。
- `M_new(F,X) ⇒ M_old(F,X)` は file 単体では成立するが、件数が 1 のとき成功する `_find_rollout` 全体では受理集合が拡大する。
- 実 corpus probe は proposed fallback、例外処理、fork 判定を正確には測っておらず、4 file からの schema 一般化は支えられない。
- decode・読取失敗を無視する既存 fail-open と、pin SHA 失敗後に未検証で全走査成功へ戻る経路も残る。
- pin 無し全走査を狭める新変更は見つからなかった。pytest は指示どおり実行していない。

## 所見

1. **[must-fix] 「受理集合は真部分集合」と「拒否 2 件を成功へ変える」は両立しない**

   - 判定 (real/speculative): **real**
   - 再現: [brief.md:39](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/brief.md:39) は「現行拒否を新規受理しない」とする一方、同 :41 と [plan:66](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/verbatim/s2-plan-v1.md:66) は 2→1 件化を明記する。入力 bytes は次で足りる。

     ```python
     parent = b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'
     child  = b'{"type":"session_meta","payload":{"id":"C","session_id":"P"}}\n'
     ```

     現行 `_find_rollout(root, "P")` は 2 件で `RC_SESSION`、after 案は parent だけを残して成功する。`M_new` が file 単位で `M_old` の部分集合でも、「一致数がちょうど 1」の成功述語は単調ではない。
   - 成果物影響: receipt の `rollout_path`、`rollout_sha256`、`rollout_inode` が `None` から parent 参照へ変わり、後段を満たせば certified 選択と材料レポートへの包含集合が増える。
   - 推奨: file 候補集合と resolver 成功集合を別々に定義する。「旧 2/4 件から観測済み親 1 件への変換」を明示的な受理拡大として裁定し、「緩和ゼロ」という主張は削除する。

2. **[must-fix] 第 2 条件は、正当な候補を消して別候補を受理できる**

   - 判定 (real/speculative): **real**
   - 再現: 最初に二つの file を同じ bytes にする。

     ```python
     base = b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'
     ```

     この時点では現行・after とも 2 件で拒否する。次に `F_parent` だけへ一行追加する。

     ```python
     injected = b'{"type":"session_meta","payload":{"id":"C","session_id":"P"}}\n'
     ```

     現行は両 file を引き続き一致扱いして拒否する。after は `F_parent` を veto し、手を加えていない `F_other` を唯一の一致として返す。[plan:217](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/verbatim/s2-plan-v1.md:217) の「clean な P/P 2 file」テストではこの形を捕捉できない。候補が一つだけなら追加行は 0 件拒否になるが、競合候補があると受理へ倒れる。
   - 成果物影響: `RC_SESSION` だった試行の rollout・ledger 参照が `F_other` へ切り替わる。`F_other` が残りの検査を満たせば、誤った file の値が receipt、台帳、材料レポートへ入る。
   - 推奨: 未認証の rollout 自身が出す「子孫宣言」を、別候補を消す負の権限として使わない。全走査は維持し、launch/events 側に束縛された file-level identity が得られない限り曖昧状態を拒否する設計へ戻す。この反例を必須負例にする。

3. **[must-fix または明示裁定] decode・読取失敗した重複は見えなくなり、残る一件が受理される**

   - 判定 (real/speculative): **real**
   - 再現: 一つ目を正常 file、二つ目を破損 duplicate とする。

     ```python
     good = b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'
     bad  = b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\xff\n'
     ```

     [scanner:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:248) は `bad` の `UnicodeDecodeError` を無視するため、現行・after とも `good` を唯一の一致として返す。open の `OSError` も空行集合へ変換される。さらに [_scan_session_rows:3789](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3789) は `_json_lines` の issues を捨てるため、後段全走査もこの不確実性を回収しない。既存の [decode test:2049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2049) と [unreadable test:2170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2170) は、この fail-open を仕様として固定している。巨大な candidate 行による通常の `ValueError` や `MemoryError` は伝播するので、その経路は受理ではなく停止になる。
   - 成果物影響: 破損・読取不能な duplicate が存在しても receipt と certified 集合では「一意な rollout」として扱われ、failure reason と台帳から不確実性が消える。
   - 推奨: scanner を `MATCH / NO_MATCH / INDETERMINATE` にし、対象候補を完全に読めない場合は拒否する。既存の ignore テストを反転するには scope 拡大またはユーザー裁定が必要であり、「無関係なので触らない」では済まない。

4. **[must-fix] corpus probe は実装予定の述語と実 scanner を同時には測っていない**

   - 判定 (real/speculative): **real**
   - 再現: [probe_predicates.py:4](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/probe_predicates.py:4) は実 corpus を走査せず cache を読む。`cand_E` は `id == X` を必須にするため、次の bytes を拒否する。

     ```python
     row = b'{"type":"session_meta","payload":{"session_id":"P"}}\n'
     ```

     after 案は `own = session_id` の fallback で受理する。さらに cache の可視 producer [probe_t936c.py:14](/home/SFC/tanab/.claude/jobs/47eaa767/tmp/probe_t936c.py:14) は全 `Exception` を無視するが、本体は JSON decode 系二種だけを無視する。fork census も [probe_predicates.py:65](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/probe_predicates.py:65) の `id != session_id` という proxy であり、例えば次の明示的 fork を数えない。

     ```python
     row = b'{"type":"session_meta","payload":{"id":"C","session_id":"C","source":{"subagent":{}},"forked_from_id":"P"}}\n'
     ```

     逆に、単に二値が異なる非 fork 行は数える。symlink、同一 inode、open/parse error、cache の corpus digest も記録されない。
   - 成果物影響: 「3,602 全件で一意」「fork file は 4 件」という証拠が実装予定コードを拘束せず、未測定 schema で rollout 参照や `RC_SESSION` が変わっても検出されない。
   - 推奨: 一つの self-contained probe で実 corpusを直接走査し、本体と同じ例外契約、実際の fallback、予定述語を使う。read/parse error、symlink、device/inode、root、取得時刻、corpus digest を結果へ含め、fork marker と ID 不一致は別集計にする。

5. **[must-fix の設計択一] P3 fallback は certified な後方互換を保っていない**

   - 判定 (real/speculative): **real**
   - 再現: 上記 `session_id` だけの row は after matcherでは一致する。しかし消費側 [consumer:3110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3110) は `id == session_id == thread_id` を要求するため、`id is None` で必ず `session id/session_id/thread_id mismatch` になる。`id` が数値、bool、null の場合も同じである。
   - 成果物影響: certified 選択や材料レポートへの包含は保たれず、変わるのは receipt に rollout path/hashを載せて identity mismatch で落ちるか、探索時点で count 0 として落ちるかという拒否値だけである。
   - 推奨: 最終成果物の契約に合わせ、`id` と `session_id` を非空 str として fail-closed にする。真に legacy schema を認証対象へ残すなら、matcher だけでなく consumer と schema/version 契約を同一 wave の裁定対象にする。「全非 str へ fallback」は採らない。

6. **[条件付き must-fix] 4 file から将来 schema を一般化できない**

   - 判定 (real/speculative): **speculative**
   - 再現: 将来の child が次だけを持つ場合、fallback は child を親 P と扱い、T-936 の重複を再発させる。

     ```python
     child = b'{"type":"session_meta","payload":{"session_id":"P"}}\n'
     ```

     また、fork がコピーされた P/P 行だけを `session_meta` として持ち、child identity を別 record type へ移せば、veto 行がなく親候補として残る。観測されたコピー付き 3 file は同じ親から派生した兄弟であり、独立した schema family の証明ではない。
   - 成果物影響: Codex schema 更新後、正当な親試行が再び `RC_SESSION` で台帳・材料レポートから欠落するか、誤った child path が receipt に選ばれる。
   - 推奨: schema/version ごとの identity 契約を明示し、未知 schema は拒否する。観測 4 file は regression fixture の根拠に限定し、普遍的な fork 規則とは記録しない。

7. **[must-fix の plan 記述] pin fast path と全走査は既に同じ答えを返さない。SHA 必須にも抜け道がある**

   - 判定 (real/speculative): **real**
   - 再現: named candidate と off-pattern duplicate を同じ P/P bytes にし、その bytes を label の SHA に登録する。pinned 呼出しは named candidate を返すが、pin 無し呼出しは 2 件で拒否する。既存 [test:2366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2366) がまさにこの差を固定している。同一 inode への named symlink と off-pattern symlink でも、fast は返し、全走査は同じ resolved path を二回数えて拒否する。

     別の反例として、named candidate 一件だけを置き、登録 SHA を誤らせる。[_find_rollout:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:323) は SHA mismatch を飲み、その後の全走査で同じ candidate を一件として未検証のまま返す。通常 CLI caller は後で再検証するが、`verify_source_sha=False` 等ではその防壁がない。

     なお str target について P1 が新規に fast/full 差を作ることはない。new で fast candidate が真なら旧でも真であり、new で偽なら fast は全走査へ落ちる。問題は既存差を plan が普遍的同値のように扱う点である。
   - 成果物影響: pinned golden/prompt の参照は返る一方、同じ corpus の pin 無し receipt 探索は拒否しうる。再検証無効の内部経路では SHA pin と異なる材料が使われうる。
   - 推奨: T-886 は「現行 5 pin で実測一致した限定 fast path」であり、一般的同値保証ではないと plan を訂正する。SHA 失敗 candidate を全走査の成功候補から除外するか、その失敗を伝播するテストを追加する。

8. **[must-fix] 変異の帰属表が未成立で、既存テストによる先殺しと survivor がある**

   - 判定 (real/speculative): **real**
   - 再現: 静的な killer 対応は次になる。

     - 現行 OR 述語への復帰は、追加する型 A より先に、期待反転する既存 `distinct-fields` が殺す。
     - fallback 削除は既存 `session-id-only` が殺す。
     - 一件目だけを返す件数変異は既存 [duplicate test:2030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2030) が殺すため、新しい P/P duplicate 固有ではない。
     - veto 削除は型 B が殺せる。順序依存の即時 return は逆順 variant が追加被覆になる。
     - `isinstance(payload_id, str)` を「key が存在すれば id を使う」へ変える変異は、null・数値 fixture がないため全既存・新規予定テストを通過する。
     - clean duplicate の片方へ C/P を追加して別 file を受理する変異形は、予定テストにない。
     - Type B fixture の `source` と `forked_from_id` はコードが一切読まないため、それらを消す変異は観測不能である。

   - 成果物影響: mutation matrix が新テストの防壁を過大評価し、非 str schemaまたは candidate 削除で誤った rollout pathを返す実装を緑として certified/report 経路へ渡す。
   - 推奨: 段 4 で mutation ごとに「最初に殺す nodeid」を事前登録する。既存 killer は既存へ帰属させ、非 str ID、片側 veto 付き duplicate、SHA 失敗後の一件 fallbackを追加する。意図した after 自身が片側 veto 負例を通せない限り、段 5 へ進めない。

## プランへの NO-GO 判定

**NO-GO**

file 単体の包含証明だけでは、件数 1 ゲートの受理拡大を正当化できない。特に「clean duplicate の一方へ子孫行を追加すると他方が受理される」反例は、第 2 条件を未認証の候補削除権限にしている。resolver 成功集合の明示裁定、veto 設計の修正、probe の再束縛、fail-open と変異負例の処置が済むまで実装へ進めない。