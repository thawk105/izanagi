## 総括

- **凍結された A2/A5 を忠実に実装しているが、その凍結式自体に候補昇格の反例が残っている。**
- 無効な `id` を持つ先頭行が正当な file を veto し、別の重複 file を一意候補へ昇格できるため must-fix。
- 変異 M3 の最初の killer は事前登録と一致せず、M8 は具体的な node が未登録である。
- 既存テストの弱体化、pin 無し走査の打ち切り、走査件数上限は検出しなかった。
- pytest は指示どおり実行していない。以下は commit `2e2cb838` の静的検査結果である。

## 所見

1. **[must-fix] 無効な先頭 `id` が正当な候補を消し、別 file を一意に昇格させる**

   **判定 (real):** real。実装は A2/A5 と一致しているため、これは実装逸脱ではなく凍結式そのものの欠陥である。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:294) は無効な `id` を `None` にする一方、[宣言判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:308) ではその `None` が `own != X` を満たす。

   **再現:** target を `P` とし、2 file を置く。

   ```python
   # rollout-0.jsonl
   b'{"type":"session_meta","payload":{"id":null,"session_id":"P"}}\n'
   b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'

   # rollout-1.jsonl
   b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'
   ```

   `rollout-0` は後続行により `owns_P=True` だが、先頭行により `declares_P=True`、先頭の own は無効なので `first_owns_P=False` となり拒否される。`rollout-1` だけが残り、`_find_rollout(root, "P")` は曖昧性を拒否せず `rollout-1` を返す。旧実装なら両方が一致して 2 件拒否だった。同じ問題は、先頭 payload 非 dict、後続 `P/P`、さらに `C/P` の並びでも成立する。

   **成果物影響:** `collect_run` が thread `P` に属する別 rollout の行・ledger 情報を受理でき、run receipt、試行台帳、集約結果および certified arm の根拠が別 file へ差し替わりうる。

   **推奨:** A2/A5 を再裁定するまで land しない。無効 identity を単なる `NO_MATCH` として候補集合から消すのではなく、resolver 全体の `INDETERMINATE` として `RC_SESSION` に倒すのが安全である。少なくとも上記 2 file の回帰を追加し、片方を消して他方を昇格させないことを固定する。

2. **[must-fix: 検証台帳] M3 の最初の killer が事前登録と異なり、M8 は node が非具体的**

   **判定 (real):** real。erratum E1 自身が M3 を逆順型 B と片側 veto の両方が殺すと認めているが、事前登録表は片側 veto を「最初」としたままである。

   **再現:** M1〜M8 をファイル順に静的追跡すると次になる。

   | 変異 | 実際の最初の killer | 判定 |
   |---|---|---|
   | M1 | `...payload_identity_semantics` の `distinct-fields` | 登録どおり |
   | M2 | `...disambiguates_fork_with_copied_parent_meta` | 登録どおり |
   | M3 | `...fork_with_parent_meta_first_remains_ambiguous` | **登録した片側 veto より先** |
   | M4 | `...disambiguates_fork_with_copied_parent_meta` | 登録どおり |
   | M5 | `...non_string_id...` の `null` | 登録どおり |
   | M6 | `...payload_identity_semantics` の `reordered-keys` ケース | 登録どおり |
   | M7 | `...preserves_zero_and_duplicate_failure` の 2 件ケース | 登録どおり |
   | M8 | focused 走なら `...payload_identity_semantics`。file 全走なら module fixture を最初に要求する先行 test で setup failure | **登録が具体的 node でなく非一意** |

   M3 では [逆順型 B](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2291) が [片側 veto](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2317) より先に収集される。

   **成果物影響:** 変異台帳の M3 killer 参照が誤り、M8 は runner 範囲によって参照が変わる。`DW-M08` の期待 node 完全集合照合が偽赤になるか、誤った検出力帰属を台帳へ記録する。

   **推奨:** M3 の最初の killer を逆順型 B に直し、完全集合には逆順型 B と片側 veto の双方を登録する。M8 は runner argv を確定して具体的 node を事前登録してから本走する。

3. **[nit] 新規 test のうち 3 本は wave 前実装でも通る**

   **判定 (real):** real。ただし保存回帰としては有用で、テスト削除を勧める所見ではない。

   **再現:** 旧述語 `id == X or session_id == X` でも次の test は期待どおりになる。

   - [逆順型 B](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2291): 親 file と子 file の双方が `P` に一致し、2 件拒否。
   - [片側追記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2317): 両 file が `P` に一致し、2 件拒否。
   - [真の重複](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/orchestrator/tests/test_codex_reasoning_ab.py:2363): 同一 `P/P` 2 file が2件拒否。

   型 A、型 B 正順、非 str `id`、pin 型 A/B、反転した `distinct-fields` は旧実装を殺す。

   **成果物影響:** なし。純増検出力の集計だけが過大表示されうるため、DW-G05 により nit とする。

   **推奨:** 3 本を保存回帰または M3 専用として記録し、「wave 前実装を倒す新規 test」には数えない。

4. **登録漏れの生存変異と条件付き配線の穴**

   **判定 (real/speculative):** speculative。現実装には存在しないが、以下の実装ミスは追加 test をすべて通り抜ける。

   **再現:**

   - `id is False` のときだけ `session_id` へ fallback する変異。A5 は bool も禁止しているが、追加 test は null、0、空文字だけである。露出入力は  
     `b'{"type":"session_meta","payload":{"id":false,"session_id":"P"}}\n'`。
   - payload dict の行だけを数えて「先頭」とする変異。追加 fixture は先頭 payload 非 dict を含まない。
   - `owns_target` が立った後の `declares_target` を無視する変異。  
     `U/-`、`P/P`、`C/P` の順なら正規式は拒否するが、この変異は受理する。
   - `pinned_label` が指定されたものの `eligible=False` の全走査だけ旧 OR 述語を使う条件付き配線。新規 pin test は eligible、他の新規 test は pin 無しであり、既存の ineligible-pin test は単一 `P/P` なので新旧を識別しない。

   **成果物影響:** 現実装には影響なし。ただし将来この形へ退行しても検査が緑になり、候補受理集合または ineligible-pin の解決結果が変わる。

   **推奨:** 所見 1 の fix 時に bool、先頭 payload 非 dict、own 後の遅い declaration、ineligible pin の型 A/B を追加する。これらを mutation 登録漏れとして扱う。

5. **decode・読取失敗は候補を消して別 file を昇格させる既知の fail-open**

   **判定 (real):** real。ただし段 4 の R2 として明示的に scope 外へ送られた既存欠陥であり、本 commit が導入したものではない。

   **再現:**

   ```python
   # rollout-0.jsonl
   b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\n'

   # rollout-1.jsonl
   b'{"type":"session_meta","payload":{"id":"P","session_id":"P"}}\xff\n'
   ```

   2 本目は `UnicodeDecodeError` として silent skip され、1 本目だけが返る。2 本目の `open("rb")` を `PermissionError` にしても同じである。

   周辺ケースの静的結論は次のとおり。

   - 巨大な単一行による未捕捉 `MemoryError` は通常は処理停止であり、受理への経路ではない。
   - 同一 inode の複数 path は重複件数として数えられ、1 件へ dedupe されないため拒否側。
   - symlink file は解決先が root 外でも受理される。既存 pin test がこの挙動を明示的に固定しているため、root confinement が要件かは別裁定が必要。
   - `target_session_id=None` を直接渡すと、無効 `id:null` の `own_session_id=None` と衝突して一致しうる。ただし現 production caller は str 定数または str 検査済み thread ID である。

   **成果物影響:** 読取不能または decode 不能な重複候補が現れた場合、別 rollout が一意に昇格し、receipt・レポート・台帳が誤った rollout を参照しうる。A4 の現 corpus では該当 file、symlink、重複 inode はいずれも 0 件。

   **推奨:** R2/R3 を「閉じた」と記録しない。別 wave で三値判定へ移す。現在の T-936 land blocker は所見 1 と 2 であり、この既知残余だけを理由に scope を無断拡張しない。

## 照合結果

- `_session_meta_rows` は有効な `session_meta` dict だけを返す。payload 非 dict の行も list には残るため、`enumerate` が `continue` より前にある現実装では位置 0 を保持する。
- type 不一致による `continue` は production helper の出力では到達不能。空 list は全 flag が偽のまま拒否される。
- `git show` の test 削除行は旧 test 名の 1 行だけ。期待値反転は `distinct-fields` だけで、他 9 variant の正例 assert は維持されている。旧 node 名への外部参照も見つからなかった。
- pin 無し経路は依然として `rglob("rollout-*.jsonl")` を全件走査し、早期打ち切り、head 制限、件数上限、filename による同一性判定は追加されていない。
- pin candidate、pin からの full-scan fallback、pin 無し full scan はいずれも現在は同じ `_rollout_matches_session` を呼び、実コードに旧 OR 述語は残っていない。

## land 判定

**NO-GO**

凍結式自身の候補昇格反例を再裁定して回帰を追加し、M3/M8 の変異事前登録を具体化するまで land すべきでない。