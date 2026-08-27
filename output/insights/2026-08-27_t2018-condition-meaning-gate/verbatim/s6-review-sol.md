## 総括

**NO-GO。blocker は 8 件です。**

dirty 現物は `s5-author.patch` と逆適用検査で完全一致しましたが、意味 arm に false-green があり、事前登録 mutation のうち m01/m02/m03/m07/m08 は現状の node では有効な kill を証明できません。

pytest/build は指示どおり実行していません。以下は全て静的判定であり、緑は申告しません。

## Findings

1. **real / high / scope内 / blocker** — result kind が固定されていません。[condition_meaning_gate.py:370](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:370)、[condition_meaning_gate.py:373](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:373)

   - 反例: hole を `std::uint64_t now_backoff = 0x4014000000000000ULL;` にすると、`sizeof` は通り、case=5 の memcpy 結果は double 5.0 の bits と一致します。一方、実 target の算術では整数値を double へ変換するため、backoff は約 4.6e18 になります。
   - 成果物影響: wrong decoder に `MeaningEvidence` を発行する false-green。固定したはずの result kind と finite pointwise witness が成立しません。
   - 最小 fix: `decltype(now_backoff)` が exact `double` であることを `static_assert` し、この整数 bit 注入を拒否する test を追加。
   - mutation: m05 に隣接しますが、現行 F718 node はこの反例を捕捉しません。result-kind 専用 mutation の事前登録が必要です。

2. **real / high / scope内 / blocker** — m02 の effective-value equality は構造的に恒真です。[source_digest.py:1922](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1922)、[condition_meaning_gate.py:320](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:320)

   - 反例: `effective != str(value)` だけを除去しても、正しい RHS では genome override により effective は必ず requested value です。wrong RHS は `cache_name != MACRO` が同じ reason で拒否します。
   - 成果物影響: m02 は SURVIVED します。D1213 の「実効 predicate を負例で確認」を満たせず、effective equality の検出力を主張できません。
   - 最小 fix: m02 を cache mapping identity の mutation に再照準するか、effective value を requested value の再代入とは独立な観測から導出する。
   - mutation: `t2018.m02-supply-value`。

3. **real / high / scope内 / blocker** — m01 は後段 rejection に mask されます。[condition_meaning_gate.py:314](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:314)、[condition_meaning_gate.py:321](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:321)、[test_condition_meaning_gate.py:110](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:110)

   - 反例: missing-mapping の早期 raise を除去しても `cache_name=None` と `effective=None` が後段の `supply-value-mismatch` で拒否されます。
   - 成果物影響: expected node は reason 差で赤になりますが、受理集合は変わりません。DW-M03 上は kill ではありません。
   - 最小 fix: bypass 時に実際に acceptance が変わる predicate へ再照準するか、mask を明示して両層 mutation を登録する。
   - mutation: `t2018.m01-supply-membership`。

4. **real / high / scope内 / blocker** — m03 fixture が marker defect と decoder defect の二重負例です。[test_condition_meaning_gate.py:202](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:202)、[test_condition_meaning_gate.py:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:216)

   - 反例: non-unique marker を許して最後の block を選ぶ mutant は、実 block の `now_backoff=0.0` により `decoded-meaning-mismatch` でなお拒否されます。
   - 成果物影響: node の赤は reason 変更だけで、marker uniqueness の acceptance kill を証明しません。
   - 最小 fix: duplicate/comment decoy を加えても実 decoder は正しいままにし、uniqueness bypass 時だけ PASS する単一理由 fixture にする。
   - mutation: `t2018.m03-marker-authority`。

5. **real / medium / scope内 / blocker** — m07 は acceptance kill ではなく diagnostic sensitivity です。[condition_meaning_gate.py:461](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:461)、[condition_meaning_gate.py:542](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:542)

   - 反例: finite check を除去しても、expected は必ず finite なので NaN/Inf bits は後段の pointwise comparison で拒否されます。
   - 成果物影響: test は reason 差で赤になりますが、gate は fail-closed のままです。KILLED と数えると DW-M03/M08 違反です。
   - 最小 fix: m07 を diagnostic sensitivity pin に再分類する。
   - mutation: `t2018.m07-finite-output`。

6. **real / high / scope内 / blocker** — m08 の compiler fixture は後段 failure に mask され、run failure も覆いません。[condition_meaning_gate.py:422](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:422)、[test_condition_meaning_gate.py:286](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:286)

   - 反例: compile rc 検査を外しても fixture は binary を作らないため、次の実行が `decoder-run-failed` になります。empty success にしても row cardinality が拒否します。
   - 成果物影響: expected node の赤が process-failure acceptance kill を示しません。run rc、run timeout、run stderr は登録 node の射程外です。
   - 最小 fix: 非zero compile rcでも有効 binaryを残す fixture、全rowを出して非zero終了する run fixtureを作り、compile/run/timeout/stderr を別 mutation に分割する。
   - mutation: `t2018.m08-process-failure`。

7. **real / high / scope内 / blocker** — compiler identity が version 実行と compile 実行へ固定されていません。[condition_meaning_gate.py:391](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:391)、[condition_meaning_gate.py:502](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:502)

   - 反例: resolved path の compiler A が `--version` 後に compiler B へ置換されると、evidence は A の version と同じ pathを記録しつつ、B が TU を compile できます。
   - 成果物影響: compiler identity evidence が実コンパイラを誤帰属し、B が出力を偽造すれば意味 arm も false-green になります。
   - 最小 fix: executable を fdまたは immutable snapshotへ固定し、dev/inode/ctime/hash を全 invocation 前後で検証して evidence に記録する。
   - mutation: 対応なし。compiler identity swap node の事前登録が必要です。

8. **real / high / scope内 / blocker** — `resolve` 後の親directory差替えで root containment を迂回できます。[condition_meaning_gate.py:176](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:176)、[condition_meaning_gate.py:181](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:181)

   - 反例: `candidate.resolve()` 後、`root/include` を rename し、同名を root 外への symlink に置換します。`O_NOFOLLOW` は最終 component にしか効かず、`os.open(resolved)` は親 symlink を辿れます。
   - 成果物影響: evidence の root は checkout 内なのに、source bytes は root 外から取得可能です。また3ファイル間の差替えは各ファイルの before/after stat では検出できません。
   - 最小 fix: root dirfd から各 component を `openat` と `O_NOFOLLOW` で辿るか、`openat2` の beneath/no-symlink 制約を使う。全fdを先に固定し、path identity と ctime を捕捉後にも再確認する。
   - mutation: 対応なし。parent-symlink swap と cross-file swap node の事前登録が必要です。

非blockerとして、generic adapter は `owner_protocol` を計算するだけで渡された `protocol_cmake_text` がその owner のものか検証しません。[source_digest.py:1918](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1918) 現行 gate は silo pathを固定しているため現在の受理集合には影響しませんが、adapter単体では mocc owner と silo CMake text の組合せを mislabeled resolution として返せます。`protocol` または入力path identityを引数へ束縛する境界testが必要です。

また bare `BACKOFF_FIXED` は adapter 上は supplied/effective=1 ですが、gate は `cache_name is None` を `macro-not-supplied` に分類します。[condition_meaning_gate.py:315](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:315) 拒否方向は安全ですが、reason は事実と異なります。bare/unmapped は `supply-value-mismatch` 等へ分離するのが最小 fix です。関連 mutation は m01/m02 です。

## Refuted

- **refuted / scope内** — supply arm と meaning arm は別公開関数、別evidenceで、meaning側は supply result や adapter を参照しません。[condition_meaning_gate.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:293)、[condition_meaning_gate.py:478](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:478) 単一 pass bit もありません。成果物影響なし、fix不要。関連 mutation は m01/m05。

- **refuted / scope内** — F707 baseline は非空 supply tableを保ちながら BACKOFF_FIXED だけを欠き、静的には `macro-not-supplied` へ到達します。F718 は supply green の後、1000.0対0.0で meaningのみ落ちます。ただし上記 m01 mask は別問題です。fix不要、関連 mutation は m01/m05。

- **refuted / scope内** — expected bits は rendered TU に埋め込まれていません。row identity/cardinality、未知/重複row、stderr、rc、timeout、bit単位比較、signed zero はコード上 fails-closed です。[condition_meaning_gate.py:362](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:362)、[condition_meaning_gate.py:434](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:434) ただし result-kind false-green と mutation mask は残ります。

- **refuted / scope内** — fixture hole は supplied/F707 の自己一致だけでなく、patch target-side conditional と照合されています。[test_condition_meaning_gate.py:333](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:333) authority anchor 自体の静的配線は成立しています。関連 mutation は m03。

- **refuted / scope内** — proof kind と module docstring は actual target TU、dynamic reachability、exact build input、driver integration を明示的に否定しています。[condition_meaning_gate.py:2](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:2) 過大主張は確認しませんでした。

- **refuted / scope内** — source_digest の既存 digest 経路は変更されずadapter追加のみ、sort wrapper は旧parser本体と同じ受理拒否を共有 extractorへ移しています。既存test期待値の反転、緩和、skip、削除はありません。author patch と dirty 現物も完全一致しています。pytest未実走のため互換性を緑とはしません。

## Mutation評価

| mutation | 静的評価 |
|---|---|
| m01 | **無効**。後段 mismatch に mask。reason-only red。 |
| m02 | **SURVIVE見込み**。effective equality が恒真。 |
| m03 | **無効**。fixtureが二重負例でreason-only red。 |
| m04 | acceptance差は静的に成立。ただし未実走。 |
| m05 | F718のacceptance差は成立。ただしresult-kind bypassは未捕捉、未実走。 |
| m06 | duplicate側は acceptance差あり。missing側は後段KeyErrorへ落ちうるため分割が必要。未実走。 |
| m07 | diagnostic sensitivityのみ。kill扱い不可。 |
| m08 | compile/run/cardinalityにmask。登録nodeも全process面を覆わない。 |

実走していないため、KILLED、SURVIVED、positive-control green の確定申告はありません。

## GO-NO-GO

**NO-GO — blocker 8件。**