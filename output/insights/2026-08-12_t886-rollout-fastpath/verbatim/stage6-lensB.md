## 総括

**判定: BLOCKER。** 現行差分では、実 corpus の pin 済み 5 呼出すべてで fast path が発火することを静的・read-only に確認した。したがって改善がゼロという実装上の反例は現時点では構成できなかった。

一方、親が登録した M10 を新規テストは殺せない。また、default の `benchmark_snapshots` 経路だけを slow path に戻す変異が全新規テストを通過できる。性能回帰を緑のまま見逃せるため、段 6 は閉じられない。pytest・計測は実走しておらず、緑や倍率は主張しない。

## 所見

### 1. BLOCKER — M10 は登録どおりには検出されない

対象: [_find_rollout](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:295)、[permission test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1790)、[ruling §4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/ruling.md:91)

**反例変異:**

```python
except (OSError, ValueError, ValidationError):
    pass
```

この変異は以下をすべて通過できる。

- `PermissionError` は `OSError` なので permission test は通る。
- injected `ValueError` も fallback する。
- SHA mismatch の `ValidationError` も fallback する。
- `KeyboardInterrupt` は捕捉しないので BaseException test も通る。

しかし親が A1/R2 で明示した `MemoryError` は伝播し、fast attempt 全体を speculative にする契約を破る。実装子の「M1〜M10 を outcome/RC 差で検査」という[報告](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/stage5-author.md:11)と食い違う。

**成果物への影響:** verify 無効経路が偶発 `MemoryError` で false refusal し、certified 選択・レポート・台帳を生成できず、受理集合の fail-closed 挙動も親裁定と一致しない。

**提案する対処:** `_verify_rollout_sha` に `MemoryError` または独自の通常 `Exception` subclass を送出させ、候補 1 本の broad fallback が同じ path を返す outcome test を追加する。permission test は OSError 境界用として残す。

### 2. MUST-FIX — default fixture の発火保証がない（F90 再発）

対象: [derive wiring test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:2005)、[render wiring test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:2033)

**反例変異:**

```python
# derive
pinned_label=label if not verify_source_sha else None

# render
pinned_label=case if not verify_source else None
```

新規 wiring tests はどちらも明示的に `False` を渡すため通る。直接 `_find_rollout(..., pinned_label=...)` を呼ぶ残りの新規テストも通る。一方、`benchmark_snapshots` は default `True` なので 5 呼出すべて旧 broad scan に戻り、改善はゼロになる。出力は同じなので既存 correctness tests も緑になりうる。

さらに arbitrary-depth test の POS/NEG/author/fix1/fix2 parameterization は、各 case で `_install_rollout_pin` が production pin を合成値へ上書きする。コードは label ごとに分岐しないため、5 case 中追加 4 case の増分検出力はゼロであり、「全 production label を検査」という保証にはならない。

**成果物への影響:** certified bytes は同じでも fixture が再び timeout 級になり、受入全走が成立しないまま高速化レポートだけが残りうる。

**提案する対処:** wiring tests を `verify=True/False` の両方へ parameterize する。加えて production label 集合を上書きしない contract test、または default caller が必ず 5 label を渡す probe testを置く。

### 3. MUST-FIX — 2 順序だけでは cache 差を相殺できない

対象: [ruling §5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/ruling.md:126)、[glob_scaling.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/glob_scaling.json:1)

**反例構成:**

1. 最初の A→B で A が directory/data cache を暖め、B が warm。
2. 続けて B→A を行うと、先ほどの cache が残っているため B も A も warm。
3. これは「A cold/B warm」と「B cold/A warm」の対称配置ではない。2 pair だけでは時間ドリフトや共有 login node の外乱も推定できない。
4. 並行 wave の `dff79a0c` / `be5018eb` は `_filesystem_file_set` も高速化しており、現 worktree HEAD には未取込だが main には入っている。before と after の base が違えば全走 wall が混成効果になる。

**成果物への影響:** certified 選択自体は変わらないが、性能レポートと受入判断が cache 順序または並行 wave の改善を T-886 の効果として誤記録する。

**提案する対処:** 両版を同一 base commit 上に置き、非計測 warm-up 後に ABBA/BAAB を複数 block 実行する。raw order、中央値、散布、commit、corpus manifest を保存する。全走 wall も `_filesystem_file_set` の版を両側で固定する。

### 4. MUST-FIX — 「metadata walk の係数を約 N 倍削減」は機序と一致しない

成功時も narrow `Path.rglob` は同じ sessions tree を最後まで歩く。削減される主要項は、無関係 rollout の open・stream・session-meta candidate parse であり、directory metadata traversal 自体の係数ではない。

`glob_scaling.json` が示すのは 2,946 file の walk 約 17 msだけで、before/after `_find_rollout`、named narrow glob、総 bytes、測定時刻を含まない。このファイル単独から N 倍は認証できない。

**成果物への影響:** report/worklog が改善機序を誤記すると、将来の corpus 成長予測と受入全走の見積りが不正確になる。

**提案する対処:** 定型を「無関係 rollout の内容 scan/parse を除去。directory metadata walk の線形項は残る」に改め、N は実装後の `_find_rollout` paired measurement にだけ付ける。cold cache は倍率を捏造しない判断が妥当だが、黙って省略せず「未測定・効果不明」と明記する。

### 5. NIT — fallback では候補内容も二重走査になる

**反例構成:** 名前一致・内容一致候補の SHA を不一致にする。

この場合、narrow で candidate の session-meta を読む → inner SHA で全 bytes を読む → broad で candidate の session-meta を再読する → verify 有効 caller なら outer SHA でも再読する。親が記録した SHA 二重読みと narrow+broad walk に加え、candidate の session-meta stream も二重化する。

**成果物への影響:** 正常な pin corpus の成果物には影響しないが、破損・permission race・pin drift 時の refusal 遅延が増える。

**提案する対処:** correctness のため fallback を狭めたり cache したりせず、この失敗時コストを記録する。

## 新規テストの個別判定

差分には「17 本」ではなく、**新規 test function 18 本**がある。以下は実走結果ではなく静的判定。

| # | テスト | 判定 |
|---:|---|---|
| 1 | `...checks_content_before_returning` | M1 を outcome で殺す。有效。 |
| 2 | `...requires_exactly_one_named_candidate` | M2 を RC_SESSION との差で殺す。有效。 |
| 3 | `...sha_mismatch_falls_back_to_duplicate_rejection` | M3 と M4 を同一 fixture で殺す。有效。 |
| 4 | `...requires_sha_pin_eligibility` | M5 を殺す。有效。 |
| 5 | `...requires_label_id_pairing` | M6 を殺す。`candidate.exists()` は増分検出力ゼロだが主 outcome は有效。 |
| 6 | `...rglob_reaches_arbitrary_depth` | M7 を殺す。ただし 5 label parameterization の追加 4 case は production 保証として恒真。 |
| 7 | `...returns_resolved_symlink` | M8 を殺す。有效。 |
| 8 | `...zero_named_candidates_uses_full_scan` | M9 を殺す。有效。 |
| 9 | `...ineligible_pin_preserves_opaque_session_id` | 親 matrix の kill は 0。ただし pinless opaque-ID 互換性の regression test としては意味がある。 |
| 10 | `...glob_metacharacters_are_literal` | `glob.escape` 削除を殺す。matrix 外だが有效。 |
| 11 | `...permission_error_is_speculative` | OSError 非捕捉は殺すが、登録 M10 の通常 narrow catch は殺せない。BLOCKER。 |
| 12 | `...does_not_catch_base_exception` | `except BaseException` を殺す。有效。 |
| 13 | `...preserves_session_meta_encodings_and_bad_rows` | pinned path の UTF/bad-row regression を検出。既存 gate が先取りする変異の新規 kill には数えられない。 |
| 14 | `...value_error_retries_with_full_scan` | ValueError 非捕捉と fast block 全削除を殺す。有效。 |
| 15 | `...parses_only_named_candidate_lines` | P1（fast block 全削除）を parse count で殺す。有效。 |
| 16 | `...skips_unrelated_value_error` | 認可済み受理集合拡大を固定。Python int-digit limit 無効環境では false red になりうる。 |
| 17 | `...derive_independent_golden_wires_pins_when_sha_check_disabled` | P2 を殺すが `False` のみ。default `True` slow mutant を見逃す。 |
| 18 | `...render_prompt_wires_pin_when_source_check_disabled` | 親登録 P3 を殺すが、default `True` slow mutantを見逃す。 |

全 test function があらゆる実装に対して完全に検出力ゼロ、という反例は構成できなかった。ただし #6 の追加 label cases、#9 の親 matrix に対する kill、#5 等の装飾 assert は増分検出力ゼロである。

## fast path・波及・並行差分の確認

- `benchmark_snapshots` の 5 本は、POS build の author/fix1/fix2 と POS/NEG render。
- 2026-08-12 の実 corpus 観測では、全 5 session に filename 一致候補が各 1 本あり、session-meta ID と SHA256 も pin と一致した。したがって現差分では全 5 回短絡する。ただしこれは F141 に従い、将来不変条件ではなく点時点観測である。
- pinless `thread_id` caller は eligibility false から直接 broad scan へ進むため、narrow+broad 二重 walk はしない。
- repo-wide `rg` では production caller は pin 付き 2 箇所と pinless `thread_id` 1 箇所だけ。所有外の直接 caller はない。
- `_find_rollout` monkeypatch seam は新規 `observe` 2 本と修正済み `lambda *args, **kwargs` のみで、kwargs 非対応 seam は残っていない。
- `benchmark_snapshots` consumer は fixture の dict shapeだけを使い、返却契約の変更はない。
- 並行 acceptance wave の source hunk は旧行 1034 付近、test hunk は旧行 1050 付近。本差分は source の 280/583/1562 付近、test の 1508/1526 付近で、直接の textual overlap はない。衝突反例は構成できなかった。ただし性能計測の base 混在は上記所見 3 の汚染要因になる。
- M1〜M9 について、指定 fixture を通過する登録 mutant は静的には構成できなかった。M10 のみ反例を構成できた。