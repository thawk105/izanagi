段 2 plan はそのままでは受理できません。`--` の位置自体は正しい一方、受理集合の説明に 2 件の実質的な漏れがあります。

### BLOCKER — option として有効なファイル名では、変化が「異常終了→pass」の一方向ではない

[tools/codex_reasoning_ab.py:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1330) は path を option 位置へ直接置いています。[brief.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/brief.md:64) と [s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:108) は全 leading-dash 名が従来 `ValidationError` だったと一般化していますが、Git 2.34.1 のローカル manpage は `--stdin`、`--stdin-paths`、`-w`、`--path`、`--no-filters` 等を有効な option と定義しています。

例えばファイル名が `--stdin`、ファイル内容が F、継承 stdin が S の場合:

- 修正前はファイル F ではなく S の OID を検査する。
- 修正後は `--` により F の OID を検査する。
- OID(S) が reachable、OID(F) が未混入なら、修正前 reject → 修正後 pass。
- OID(S) が未混入、OID(F) が reachable なら、修正前 pass → 修正後 reject。

したがって混入側も「従来同様 reject」ではなく、受理集合は双方向に変化します。`--` という実ファイル名も、修正前は operand ではなく option terminator になるため同じ境界漏れがあります。

提案テストの `-answer` は unknown-option 経路だけを検出します。最低限 `--` も同じ二相テストへ加え、既知 option 名の従来挙動を plan v2 に明記すべきです。

成果物影響: 現行 built-in spec の certified 値は変わりませんが、放置すると受理集合の記録が偽になり、将来の `spec=` 利用では snapshot の pass/reject、レポート、台帳がファイル内容でなく ambient stdin に左右された事実を見落とします。

### MAJOR — leading-dash symlink は「非 regular file」ではなく新たに pass できる

[s2-plan.md:122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t904-hashobject-sep/s2-plan.md:122) は非 regular file が `is_file()` で除外されるとしていますが、[tools/codex_reasoning_ab.py:1327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1327) の `Path.is_file()` は、regular file を指す symlink にも真を返します。一方、filesystem scan は [tools/codex_reasoning_ab.py:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1102) で `lstat()` し、symlink を通常の allowlist 要素として収集します。

次の custom spec は修正後に pass 可能です。

- `-answer` を snapshot 外の regular file への symlink にする。
- `spec["untracked"]` には加えるが、`spec["hashes"]` / `modes` には加えない。
- 外部 target の blob は object store に入れない。

`untracked` と filesystem allowlist は一致し、[tools/codex_reasoning_ab.py:1490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1490) は `hashes` にない symlinkを検査せず、修正後の `hash-object -- ...` は target bytes を読むため reason が残りません。修正前の `-answer` は option error で fail-closed でした。

`--` 自体は入れるべきですが、path 防壁を必要とするなら Git の偶発的な option error に依存せず、leading dash を許可したうえで「正規化済み・snapshot 内・非 symlink regular・untracked は hashes/modes に対応」を明示検証する必要があります。これは通常名の受理集合も狭めるため、本 wave に黙って混ぜず段 4 裁定対象です。

成果物影響: 現行 built-in spec には到達しませんが、将来/custom spec では外部可変 bytes を参照しながら `files` に対応行のない oracle が valid となり、その snapshot に基づく certified 選択・レポート・台帳を成立させ得ます。

### 危険 path の前後差

| path | 修正前 | 修正後 |
|---|---|---|
| 空文字 | snapshot directoryなので `is_file()` 偽。filesystem missing reason | 同じ |
| `--` | terminator として消費され、実ファイルを検査しない。zero-operand の正確な rc は未確認 | literal operand |
| `-` | lone `-` の parser 挙動はローカル help だけでは未確認 | literal operand |
| `--stdin` 等 | option として stdin 等を処理 | literal operand。BLOCKER の双方向差 |
| 改行 | argv list と porcelain `-z` で data のまま。先頭 `-` でなければ不変 | 同じ |
| `../x` | snapshot 外を hash し得るが filesystem missing で最終 reject | 同じ。先頭 component が `-` なら新たに byte-read 可能 |
| 絶対 path | snapshot 外を hash、filesystem mismatch で reject | 同じ |
| glob | shell を介さないため literal | 同じ |
| NUL | Unix filenameとして不可能。現環境の `Path.is_file()` は `ValueError` を false にする | 同じ |

### P1–P3 と Git 設定

- P1 は repo 内では反証できませんでした。[tools/codex_reasoning_ab.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:54) と [同:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:675) は通常 prefix を固定し、全 production caller は `spec=` を渡していません。replay も [同:4723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:4723) で保存 spec を再注入せず、case から再構築します。
- P2 の `--no-filters`, `--`, path という順序は Git 2.34.1 のローカル synopsis と一致します。
- P3 は上記 2 所見により反証されます。
- `--no-filters` はローカル manpage 上、attributes と改行変換を含む filter を無視します。したがって `core.autocrlf` や `.gitattributes` による通常名 OID の差はありません。stdin hash も `--path` がなければ no-filter が暗黙適用されるため、提案テストの OID 比較は妥当です。

### 正例テストの検出力

提案された `-answer` テストは、対象 1 行の revert を静的には検出します。親実測どおり revert 時は最初の closure 呼び出しが rc=129 で例外になります。

`assert reasons == []` も構造上成立します。隣接テストと同じ sealed fixtureであり、`_one_git_closure_reasons` は未保存の working-tree fileを reason にせず、[tools/codex_reasoning_ab.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/tools/codex_reasoning_ab.py:1165) が `-answer` を expected filesystem set に加えるため extra/missing は生じません。ただし、この 1 例だけでは BLOCKER の既知 option 名境界を証明できません。

pytest は実行しておらず、緑・赤の実測は主張しません。

## 総括

- 最大の危険は、`--stdin` 等で受理集合が双方向に変わるのに一方向拡大と記録すること。
- 次点は、custom spec の leading-dash symlink が外部 bytes を参照したまま pass できること。
- `--` の挿入位置と `-answer` テスト自体は正しいが、`--` など既知 option 名の二相被覆が必要です。