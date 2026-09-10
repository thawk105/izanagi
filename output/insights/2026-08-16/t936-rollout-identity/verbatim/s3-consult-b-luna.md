## 総括

NO-GO。P1 は `_find_rollout` の候補誤認を減らすが、実 corpus では下流の `session_meta count is 4` が残る。  
pin 無し全走査、pin fast path、SHA 照合は計画上維持されているが、fast path 用の敵対テストが不足する。  
`distinct-fields` 反転は実害修正として妥当そうだが、独立 producer に対する一般化根拠は薄い。  
P3 の `session-id-only` 維持も、観測事例ゼロの互換仮説を仕様化している。  
pytest は実行していない。

## 所見

1. **下流 consumer を scope 外にしたため、実害が残る**

   判定 (real)

   再現: 実 corpus の親 `019f690c...` は正しい親 rollout ですが、`session_meta` が4行あります。P1 適用後は子 file が除外され、親 file が `_find_rollout` から返ります。しかし [`tools/codex_reasoning_ab.py:3090`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3090) で `len(meta) != 1` により拒否されます。`session_id` も設定されず、[`tools/codex_reasoning_ab.py:3397`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:3397) の分類は RC_RECEIPT になります。

   さらに replay では `session_id` が無いため expected session に入らず、[`tools/codex_reasoning_ab.py:4957`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:4957) の session row 集合検査も失敗します。

   成果物影響: 修正しない場合、receipt は `valid=false`・`primary_rc=25` のままで、通常 replay では `experiment_complete=false`、certified 選択・primary judgment・decision が欠落します。拒否理由が rollout count から `session_meta count` に変わるだけです。

   推奨: consumer の扱いを段4の裁定パッケージへ返す。完全一致する重複行だけを安全に正規化するのか、複数行を拒否し続けるのかを決め、異なる行の fail-closed を維持する。P1 だけで実害解消済みとは判定しない。

2. **pin fast path に旧判定式を残す変異を新テストが検出できない**

   判定 (real)

   再現: 追加予定の型A・型Bは pin 無しで呼びます。既存の pin 付き fixture は通常の `id == session_id` だけです。fast path 内だけを旧 OR 判定へ戻し、親を指す子 rollout に正しい SHA pin を付ける変異を考えると、既存テストと追加テストは通りますが、[`tools/codex_reasoning_ab.py:322`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:322) が子 file を返します。

   追加テストの親側 assertion は実装前コードで失敗するため帰属します。一方、子側 assertion単独と pin 経路は帰属しません。

   成果物影響: `render_prompt` や `derive_independent_golden` が子 rollout の prompt・SHA・golden bytes を採用し、材料レポートと proof chain の参照先が変わります。

   推奨: pin 付き型A/B fixtureを追加し、候補内容の判定、SHA 成功、SHA 失敗からの全走査を `verify_source_sha=True/False` の両方で固定する。全走査を狭める変更は不要です。計画の [`tools/codex_reasoning_ab.py:333`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t936-rollout-identity/tools/codex_reasoning_ab.py:333) と SHA 照合の維持自体は妥当です。

3. **`distinct-fields` 反転は必要そうだが、一般意味論の根拠が不足している**

   判定 (speculative)

   再現: このテストは `ee69b5256` で追加され、同コミットと D315 は `payload.id` / `payload.session_id` の OR 判定を不変条件として扱っていました。一方、実 corpus の `id != session_id` は4行すべて `source=subagent` であり、`distinct-fields` は親参照を含む子行の形と一致します。したがって親検索で旧期待を維持するのは誤仕様固定の可能性が高いです。

   ただし、別 producer が `session_id` を所属 root、`id` をローカル実行識別子として正当に使う場合、P1 はその file を拒否します。この producer は corpus で独立に確認されていません。

   成果物影響: その形式が実在すれば、正当な rollout が RC_SESSION となり、試行・レポート材料・certified 候補から欠落します。

   推奨: 反転を採用するなら「Codex subagent の root 参照を除外する意味論」として裁定し、独立 producer の schema 根拠を追加する。単なる OR 条件の破壊として実装しない。

4. **P3 の `session-id-only` 維持は、観測事例のない曖昧な互換性を残す**

   判定 (speculative)

   再現: `id` を持たず `session_id=parent` だけを持つ file では、P1 の fallback がそれを自身の identity と扱います。子固有の `id` が無いため veto も立ちません。現在の `session-id-only` テストは実装前コードでも通り、実 corpus では `id` 欠落が0件です。

   成果物影響: 親 rollout が欠落した単独 file、または将来の pin candidate がこの形なら、子を親として採用し、prompt・golden・receipt の参照が誤ります。

   推奨: id 欠落を本当に後方互換すべきか裁定する。少なくとも「id 欠落の root 参照」を拒否する負例と、正当な id-less producer の正例を分けて追加する。

5. **probe は判定式の比較には使えるが、raw rollout の scanner 実効性を証明していない**

   判定 (real)

   再現: [`probe_predicates.py`](/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_t936-rollout-identity/probe_predicates.py:1) は正規化済み `corpus_meta.json` の `id` と `session_id` だけを読みます。元 bytes の marker 判定、`\u00` escape、UTF-16/32 の行境界、巨大行、malformed 行は消失済みです。したがって、異なる raw file が同じ metadata pairs へ正規化されると probe の結果は同じでも `_session_meta_rows` の候補集合は異なり得ます。

   成果物影響: 見落としがあれば rollout path・SHA・prompt material の選択が変わり、誤った拒否または別 file の受理として certified 結果とレポート参照が変わります。

   推奨: raw file を独立 scanner で再走査し、既存 scanner との file 集合・meta 行集合・encoding・行長・重複 meta 件数を比較する。探索範囲を狭める提案ではありません。

6. **P4 の改名は内部呼出元を壊す証拠がないが、scope を広げる**

   判定 (speculative)

   再現: repo 内の `_find_rollout` 呼出しは positional で、`session_id=` keyword call はありません。monkeypatch wrapper も positional です。したがって内部テストと呼出元の破壊は確認できません。

   成果物影響: 改名しなくても値、受理集合、receipt、レポート参照は変わりません。外部の private keyword caller だけが潜在的に壊れます。

   推奨: `target_session_id` への改名は別 cleanup へ延期するか、private signature の互換性を明記する。本 wave の must-fix ではありません。

## プランへの NO-GO 判定

**NO-GO**

consumer の `session_meta` 多重行処理と、pin fast path の mutation 被覆を解決するまで実装へ進めない。P3・producer 一般化・raw scanner の不足は、別途ユーザー裁定を要する scope 外パッケージとして返す。