## 総括

**判定: BLOCK。** production 差分は概ね親裁定どおりですが、受理集合の説明に未裁定の拡大があり、M10 と `BaseException` のテストは狙った変異を殺せません。pytest は実走しておらず、以下は静的レビュー結果です。

### [BLOCKER] candidate 自身の一過性例外を再試行し、旧実装が停止した実行を受理する

[fast attempt の catch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:306) は、非候補 file の例外だけでなく、旧全走査でも実行していた candidate の内容照合例外まで捕捉します。

- 反例・構成: [既に追加されたテスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1898)そのもの。candidate の最初の `json.loads` だけ `ValueError`、二回目は成功させる。旧実装は最初の全走査で例外伝播、新実装は fast 側で飲み、fallback で再読して受理する。
- これは「非候補 file を観測しない」差ではない。fast path は例外を実際に観測したうえで再試行している。MemoryError や一過性 I/O failure でも同型を構成できる。
- 成果物への影響: 旧実装なら停止した session から golden/prompt を生成し、certified 選択・レポート・台帳を前進させうる。
- 提案する対処: 親裁定を「fast attempt が消費した一過性例外の再試行」まで明示的に拡張するか、旧述語 `_rollout_matches_session` の例外は伝播させ、SHA・resolve 等の fast 固有操作だけを fallback 対象にする。

### [BLOCKER] M10 の chmod fixture は broad catch を証明しない

[test_find_rollout_pinned_permission_error_is_speculative](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1790) が発生させる `PermissionError` は `OSError` の派生です。

- 反例・構成: `except Exception:` を `except (ValidationError, OSError, ValueError):` に変異する。chmod の `PermissionError` は捕捉され、同テストは正実装と同じ fallback 結果になる。これは親が R2 で問題にした `MemoryError` を捕捉しない narrow catch である。
- 成果物への影響: SHA 読出しの `MemoryError` 等で fallback せず停止する実装を mutation matrix が承認し、正当な certified run を拒否しうる。
- 提案する対処: `_verify_rollout_sha` を直接 monkeypatch して `MemoryError` または `RuntimeError` を投げる fixture にする。この直接 seam は `pathlib` の class 束縛問題を受けない。M10 の期待失敗 node も再導出する。

### [MUST-FIX] `BaseException` テストは `except BaseException` mutant でも通る

[test_find_rollout_pinned_does_not_catch_base_exception](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1832) は `_rollout_matches_session` を「毎回」`KeyboardInterrupt` にします。

- 反例・構成: production を `except BaseException:` に変異する。fast 側の最初の割込みは飲まれるが、fallback が同じ monkeypatch を再度呼び、二回目の `KeyboardInterrupt` が伝播するためテストは通る。
- 成果物への影響: 中断要求を飲む回帰が緑になり、誤った session 選択処理が継続しうる。
- 提案する対処: sentinel を fast 側の一回だけ投げ、二回目は実 helper へ委譲する。正実装は一回目を伝播し、`BaseException` mutant は fallback 成功となるため区別できる。

### [MUST-FIX] pinless の「1 bit も触れない」をテストが証明していない

[test_find_rollout_ineligible_pin_preserves_opaque_session_id](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1747) は結果だけを検査しています。

- 反例・構成: separator 判定を eligibility より前へ移す。fixture の ID は `/` を含むため、その時点で fast を諦めて fallback し、テストは通る。`glob.escape(session_id)` を eligibility 前に呼んで結果を捨てる変異も通る。
- fixture は `]`、大文字、NFC 版も含んでいない。
- 成果物への影響: opaque な `thread_id` が glob/separator 処理へ入り、将来の文字列・platform 条件で pinless session の拒否または誤探索を生みうる。
- 提案する対処: `str` subclass の `__contains__` sentinel、`TOOL.glob.escape` sentinel、`Path.rglob` の pattern 記録を使い、pinless では静的 `"rollout-*.jsonl"` の一回だけが呼ばれることを固定する。

### [MUST-FIX] M7 は「非再帰 glob」は殺すが「固定深度」は殺せない

[rglob 深度テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/orchestrator/tests/test_codex_reasoning_ab.py:1668) の candidate は常に `a/b/c/d/e` の同一深度です。

- 反例・構成: `rglob(pattern)` を `glob("*/*/*/*/*/" + pattern)` に変異する。全 label で candidate に到達し、テストは通る。
- 成果物への影響: corpus の階層構成が変わると fast-path 被覆が落ちる F90 型回帰を mutation matrix が見逃す。
- 提案する対処: M7 を逐語的な `rglob→glob` 変異だけに限定するか、複数の異なる深度を独立 case にする。「任意深度をテストで証明」とは記録しない。

## 新規テスト全件の効力

差分には「17 本」ではなく、静的には **18 test 関数・26 parameterized case** あります。

| # | テスト | 判定 |
|---:|---|---|
| 1 | content before returning | M1 を殺す。fast 全削除でも通るため単独の選択証拠ではない |
| 2 | exactly one candidate | M2 を殺す。fast 全削除でも通る |
| 3 | SHA mismatch fallback | M3/M4 を outcome/RC で殺す |
| 4 | SHA pin eligibility | M5 を `_verify_rollout_sha` no-op で適切に隔離 |
| 5 | label/id pairing | M6 を殺す |
| 6 | arbitrary depth | 非再帰 M7 は殺すが、深度 5 固定 mutant は生存 |
| 7 | resolved symlink | M8 を殺す |
| 8 | zero candidate fallback | M9 を殺す。fast 全削除でも通る |
| 9 | opaque pinless ID | 結果は正しいが no-touch を証明しない |
| 10 | glob metacharacters | `glob.escape` 削除を結果で検出 |
| 11 | permission speculative | M10 の broad/narrow 境界を検出不能 |
| 12 | BaseException | `except BaseException` mutant が生存 |
| 13 | encoding/bad rows | duplicate により fast 選択も含めて有効 |
| 14 | ValueError retry | catch/fallback は検出するが、未裁定の受理拡大を固定している |
| 15 | parse count | P1 の fast-block 全削除を直接検出 |
| 16 | unrelated ValueError | 認可済みの非候補例外迂回を有効に検出 |
| 17 | golden wiring | P2 のみ。fast 実装が壊れていても通る |
| 18 | prompt wiring | P3 のみ。fast 実装が壊れていても通る |

P1〜P3 はいずれも diagnostic 枠であり、kill 枠へ混入させてはいけません。実 corpus・skip に依存する新規テストはありません。

## 攻撃したが反例を構成できなかった点

- **新しい通常例外による拒否:** 構成できなかった。separator、escape、rglob、sort、内容 probe、resolve、SHA の `Exception` は catch 内で、fallback 本体は catch 外にある。全走査側の例外は飲まれない。`BaseException` は意図どおり非捕捉。
- **production の pinless 変更:** 構成できなかった。[eligibility](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:301) は先頭で、`pinned_label=None` は第一項で short-circuit する。thread caller は keyword を渡しておらず、`thread_id` は静的 fallback pattern の内容比較にしか触れない。
- **helper 抽出の真理値差:** 構成できなかった。[helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:283) は旧 loop と同じ存在述語。複数の真 row でも path は一回だけ、非 `session_meta`、非 dict payload は同じく不一致となる。
- **resolve・順序・候補数:** `sorted(key=os.fspath)`、`len(candidates) == 1`、内容確認後かつ SHA 前の `resolve()` はすべて存在する。追加の差は構成できなかった。
- **monkeypatch の束縛不発:** 新規テストは `TOOL` の関数/global または実 chmod を使っており、`monkeypatch.setattr(os, ...)` が `pathlib` に届かない既知問題は見つからなかった。
- **既存 seam:** repo-wide grep では `_find_rollout` を差し替える既存 seam は修正された `lambda *args, **kwargs:` だけ。期待値変更はなく、kwargs 非対応の残存 seam は見つからなかった。