結論は **NO-GO（現プランのままでは実装不可）** です。32 通りの raw-byte membership と行分割は妥当ですが、marker と C++ 枝の外枠が受理述語に入っておらず、正準行を無効化・上書きした source が通ります。また `true` の扱いと経路 inventory は段 4 裁定が必要です。

### F1 — marker の存在判定が fail-open

severity: **must-fix**

根拠: 正本 patch の marker は逐語的には [patch:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:86) と [patch:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:106) ですが、parser は非 anchor の `search()` と末尾非拘束 regex を使います。[diff_quarantine.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:564) [diff_quarantine.py:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:573) plan は双方 0 件を no-op にします。[s2-plan.md:96](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/verbatim/s2-plan.md:96)

負例カタログ:

| ID | 入力 | 提案 validator の結果 | 必要な結果 |
|---|---|---|---|
| N01 | marker の前置を tab、0 space、`// note: ` に変更 | `search()` が拾い accept | reject |
| N02 | BEGIN/END の大小を双方 `evolve-block-*` に変更 | 双方 0 件として no-op | trigger 骨格の他 token が残るので reject |
| N03 | BEGIN 前に `/*`、END 後に `*/` を置き block 全体をコメント化 | parser はコメント構文を見ず、正準 hole 行なら accept | reject |
| N04 | marker ID を `silo-backoff-trigger-gating-shadow`、または ID 後に NUL/junk | `\b` 後が非 word なので対象 marker として accept | reject |
| N05 | marker 行だけ CRLF、hole 行だけ LF、または END 行の最終 newline を削除 | parser が正規化し hole bytes は一致するため accept | marker bytes も正準化するなら reject |
| N06 | UTF-8 BOM をファイル先頭または marker の直前へ置く | `utf-8` は U+FEFF として復号し、非 anchor 検索が accept | reject |
| N07 | NUL を hole 外、または marker ID 後へ置く | 復号可能で hole exact に影響せず accept | reject |
| N08 | 正規 marker を双方削除し、trigger 骨格と任意の述語だけ残す | marker 0 件として no-op、source はコンパイル可能 | reject |

現在の stock 木が marker 0 件なのは実測どおりですが、それは現 pin の一点についてだけ真です。marker 0 件を「stock または非 trigger」と一般化できません。trigger patch には marker 以外にも `BACKOFF_TRIGGER_GATING`、`IzanagiAbortReason`、`izanagi_gate_pass` という検出可能な骨格があります。[patch:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:38) [patch:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:79)

成果物影響: marker を消した非正準 source が build・verify を通り、`certified=true`、選択 variant、report の mask 表示、ledger の source/receipt SHA が実際の gate 意味と食い違います。

### F2 — parser は「正準行の位置」を返すだけで、実効 C++ 枝を証明しない

severity: **must-fix**

根拠: parser は最初の任意 `#if/#ifdef/#ifndef`、最初の `#else`、最初の `#endif` を順に拾い、条件式・nesting depth・frame bytes を検査しません。[diff_quarantine.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:566) [diff_quarantine.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:580) [diff_quarantine.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:590) 一方、正本は `#if BACKOFF_TRIGGER_GATING` と、END 後の gate 呼出しです。[patch:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:101) [patch:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:107)

負例カタログ:

| ID | 入力 | 提案 validator の結果 | 実効動作 |
|---|---|---|---|
| N09 | `#if BACKOFF_TRIGGER_GATING` を `#if 0` に変更し、hole は正準行のまま | accept | 正準行は dead。既存 else と END 後の呼出しで二重 backoff になり得る |
| N10 | `#ifdef OTHER_MACRO` / `#ifndef OTHER_MACRO` | accept | candidate genome と無関係な枝になる |
| N11 | parser が拾う最初の `#endif` 後、END 前に別の active `#if` と代入を追加 | accept | `frame_text` は検証されず、後置代入が有効 |
| N12 | END と `if (izanagi_gate_pass)` の間に `izanagi_gate_pass = false;` | accept | 正準 hole の結果を上書きし backoff を抑止 |
| N13 | 最初の END 後に大小を変えた同 ID の第 2 block を置く | uniqueness は 1 組と数え accept | 第 2 block が実効述語を上書き |
| N14 | target block 内の frame 部分へ別 marker ID の block を入れ子にする | target ID の件数は一意なので accept | nested active branch が述語を変更可能 |
| N15 | 同一大小・同一 ID の第 2 block | plan の uniqueness が reject | これは補強 1 が閉じる正しい control |

`parse_template_file` の最初の END での打ち切りは [diff_quarantine.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:602) にあります。exact pair uniqueness は N15 には効きますが、N11〜N14や hole 外代入には効きません。

最低限、marker block の directive bytes・`#if` 条件・frame 順序を閉じ、`izanagi_gate_pass` への追加代入が対象 hole 外に存在しないことを検査する必要があります。共有 parser をそのまま semantic parser とみなすのは不可です。

成果物影響: report/ledger が「mask M の canonical predicate」と記録しても、実バイナリは dead branch、二重 backoff、または後置上書きの別実装となり、certified 選択と oracle/floor 値の帰属が壊れます。

### F3 — raw physical-line splitter の写し自体は正しい

severity: **nit（懸念は refuted）**

根拠: text reader は universal-newline 後に `split('\n')` します。[diff_quarantine.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:557) raw 側は `\r\n`、lone `\r`、`\n` を同じ個数の delimiter として消費し、CR を payload に戻します。[pipeline.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:83)

短い静的列挙でも、`A`・CR・LF の長さ 0〜6 の全列について logical/raw 行数の不一致は 0 件でした。

- LF: 行番号一致、正準 payload は accept。
- CRLF/lone CR: 行番号は一致し、payload 末尾へ CR が残るので hole は reject。
- EOF newline の有無: 双方とも同じ末尾要素を持つ。
- BOM/NUL: 行数をずらさない。

したがって plan の [s2-plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/verbatim/s2-plan.md:76) の分割ロジックに off-by-one はありません。ただし F1 の mixed-newline は「marker/frame bytes を比較しない」ため通るので、別問題です。

成果物影響: splitter をこのまま写しても certified・report・ledger の値は変わりません。ここを誤って修正すると、逆に CRLF 拒否を弱めます。

### F4 — missing root/file の no-op は不要で、marker absent だけが実 bypass

severity: **must-fix**

根拠: `SourceEvidence` は public dataclass であり、exact 型でも `resolve_evidence()` 由来とは証明しません。[source_digest.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:99) `_source_map` も型と receipt 化しか見ません。[build_admission.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:116)

| 状態 | validator | production の後続 |
|---|---|---|
| source root 不在 | plan では `FileNotFoundError` no-op | 通常は `git status` が先に fail-closed。[source_digest.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:761) |
| target file 不在 | plan では no-op | `EVOLVE_BLOCK_SOURCES` の `_read` で fail-closed。[source_digest.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:580) [source_digest.py:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:640) |
| readable target、marker 0 件 | no-op | stock は正常。一方 marker を削除・大小変更した trigger source も resolve/build まで進める |

missing root/file は通常の 5 経路では完了 build を作れません。しかし fabricated `SourceEvidence` なら derive/require で receipt を発行でき、その receipt は意図どおり live I/O なしで replay できます。[build_admission.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:656) [wal.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/wal.py:1115)

`PermissionError`・`EIO`・`ENOTDIR` を reject へ変える補強は正しい一方、`FileNotFoundError` は「非 axis」の証拠ではありません。正常 stock は target file が読めるため、missing root/file を reject にしても brief の stock 不変条件には反しません。

成果物影響: missing root/file では通常 certified 値は作られませんが、偽の admission receipt は発行可能です。marker absent bypass では非正準 source の certified 値・report・ledger が実際に生成されます。

### F5 — `izanagi_gate_pass = true;` は literal 33 番目として受けてはならない

severity: **must-fix**

根拠: template default は [patch:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:102)、emitter は必ず `kUnset` から始まります。[reflux_ir.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/reflux_ir.py:131) Coverage はこの template をそのまま適用して `_build` します。[s8a_trigger_coverage.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_coverage.py:257) Frequency driver も同じ `_build` を使います。[s8a_trigger_freq.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_freq.py:147)

順位は次です。

1. **(iii) typed な二状態 admission**
   - `Candidate(mask)` は 32 通りだけ。
   - `SkeletonCharacterization` は frozen template＋許可済み instrumentation/misattr patch chain の exact state と、既存 generator receipt/input の一致を条件に template default を受ける。
   - 通常 sweep、S-1、oracle、floor、extime、binding 付き candidate では `true` を必ず拒否する。
   - env/CLI escape ではなく、独立した閉じた受理状態なので禁止事項に触れない。

2. **(i) 32 通り以外を一律拒否**
   - 正しさ上は安全。
   - ただし coverage と frequency の再生成を止め、frequency artifact を必須入力とする sweep も再走不能になります。[s8a_trigger_sweep.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:136)
   - scope を広げられない場合の安全側停止案です。

3. **(ii) hole bytes だけを `32 ∪ {true}` とする案**
   - **現状との比較では受理集合を広げません。** 現状は semantic validator がなく、他 gate を通る全 source が受理されます。新集合はその部分集合です。
   - しかし (i) の候補言語との比較では 1 行値を追加する拡張です。
   - さらに file 全体では「1 例外」ではありません。外側の任意 frame・追加代入・コメント化を自由変数に持つ、無限個の source が同じ hole bytes で通ります。
   - materializer が置換を忘れて `true` を残した将来の candidate も通るため、as-written では抜け道がないと証明できません。

(ii) を採るなら、template-derived line だけでなく、characterization producer、generator input、full skeleton/frame、許可 patch chain の exact state へ束縛する必要があります。その時点で実質的に (iii) です。必要な負例は「通常 candidate の `true`」「近傍 whitespace/CR/NUL 変異」「patch chain 以外の `true`」「binding 付き `true`」です。

成果物影響: (i) は coverage/frequency report を更新不能にし下流 sweep を停止します。裸の (ii) は materialize 失敗を正常 candidate として certified にし、report の mask と実バイナリを食い違わせます。(iii) は双方を分離します。

### F6 — class 前検査は妥当だが、二重呼出しは build snapshot を閉じない

severity: **must-fix**

根拠: plan の derive/require 配置は [s2-plan.md:39](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/verbatim/s2-plan.md:39)、現行 pipeline の両呼出しは [pipeline.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:768)、buildcache 境界の require は [buildcache.py:1273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/buildcache.py:1273) と [buildcache.py:1538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/buildcache.py:1538) です。

判定:

- class 判定前: **real**。stock/review/generator/coder の選択で semantic gate を迂回できません。
- derive と require の双方: **real**。発行後から materializer 入口までの恒常的な変更を検出します。
- parser text read と raw bytes read: **未閉鎖**。現行実装同様に別 open なので、構造を A から、hole bytes を B から読む mixed snapshot が可能です。[pipeline.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/pipeline.py:79)
- require と compiler read の間: **未閉鎖**。Coverage の direct CMake は require 後に configure/build を開始します。[s8a_trigger_coverage.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_coverage.py:153)
- buildcache の出口 re-resolve: 恒常 drift は検出しますが、A→bad→A の ABA は検出しません。[buildcache.py:1721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/buildcache.py:1721) `SourceEvidence` 自身もこの窓を明記しています。[source_digest.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:101)

少なくとも validator 内では raw bytes を一度だけ読み、その同一 bytes を UTF-8 decode・marker parse・hole slice に使うべきです。compiler までの ABA は既存の明示的残存境界として、T-897 で閉じないなら「縮めただけ」と記録すべきです。

成果物影響: mixed/ABA が発生すると、binary hash は bad snapshot、receipt の source digest と report/ledger は復元後 snapshot を指し、certified binary の proof chain が切れます。

### F7 — 5 経路の到達事実は real だが、段 2 inventory は誤っている

severity: **must-fix**

現在の production default について、brief の 5 経路が gateway へ到達する事実は real です。ただし plan の表は S8b oracle を落とし、別物を入れています。

| brief の経路 | 実 call graph | plan の扱い |
|---|---|---|
| S8a trigger sweep | `_eval_one` → `run_campaign` → `pipeline.evaluate`。[s8a_trigger_sweep.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8a_trigger_sweep.py:449) | coverage と誤記 |
| S-1 direct | production default `pipeline.evaluate` → call。[s1_direct_comparison.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_direct_comparison.py:674) [s1_direct_comparison.py:869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_direct_comparison.py:869) | 正しい |
| S8b oracle | default `pipeline.evaluate` → call。[s8b_oracle_driver.py:1270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8b_oracle_driver.py:1270) [s8b_oracle_driver.py:1461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8b_oracle_driver.py:1461) | 欠落 |
| S8b floor | derive → default `build_v2` → require。[s8b_floor_campaign.py:1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8b_floor_campaign.py:1175) [s8b_floor_campaign.py:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s8b_floor_campaign.py:1207) | 正しい |
| S-1 extime | derive → `buildcache.build` → require。[s1_verify_extime_calibration.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/s1_verify_extime_calibration.py:336) | 正しい |

plan が代入した `between_run_floor` は stock baseline で、trigger 5 経路の一員ではありません。[between_run_floor.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/between_run_floor.py:156)

さらに coverage は独立の追加 consumer であり、frequency もそれを再利用します。したがって「5 件の exact inventory」を全 consumer inventory として固定してはいけません。テストは brief の正しい 5 件の到達を証明し、coverage/frequency の template-state 挙動を別に固定すべきです。`evaluate_fn` / `build_fn` 注入経路について主張できるのは production default だけです。

成果物影響: 誤った AST inventory が緑でも S8b oracle の将来の迂回を検出できず、oracle manifest に未検査 source の値が入ります。また coverage/frequency の破壊を受入で見落とします。

### F8 — P1〜P5 と段 2 補強の裁定

severity: **must-fix**

| 項目 | 判定 | file:line 根拠 | 所見を反映しない場合の成果物影響 |
|---|---|---|---|
| P1 marker 実在で axis 検出 | **refuted**。marker 実在は十分な発火信号だが、marker absent は非 axis の証明でない | [brief:43](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/brief.md:43)、[parser:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:564) | marker 削除・大小変更 source が certified になる |
| P2 derive/require、receipt replay は除外 | **real**。ただし snapshot/ABA を閉じたとは主張不可 | [brief:45](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/brief.md:45)、[wal.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/wal.py:1115) | derive だけなら build 前 drift、require だけなら不正 receipt 発行が残る。replay に入れると過去 ledger が live path 消失で読めなくなる |
| P3 1 行・32 exact で完全 | **refuted**。hole membership は real だが marker/frame/枝/外部上書きと template state が未閉鎖 | [brief:48](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/brief.md:48)、[patch:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:101) | report の mask と実効 C++ 動作が乖離 |
| P4 missing root/file no-op | **refuted** | [brief:51](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/brief.md:51)、[resolve_evidence:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:850) | 偽 receipt を発行でき、marker absent bypass は実 build へ進む |
| P5 build_admission＋tests のみ | **real（所有範囲として）**。ただし helper を evidence-only/class-before に固定せず、characterization state は既存 sealed receipt/input から判定する必要がある | [brief:53](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/brief.md:53)、[build_admission.py:507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:507) | gateway 内で閉じなければ call-site 別例外が増え、consumer ごとに certified/report 値が分岐する |
| 補強 1: marker pair uniqueness | **real（限定）**。同大小・同 ID の exact 重複は閉じる | [s2-plan.md:3](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/verbatim/s2-plan.md:3)、[parser:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/diff_quarantine.py:602) | 最初の END 後の exact 第 2 block が実効述語を上書きする |
| 補強 2: `FileNotFoundError` だけ no-op | **refuted（非 ENOENT の reject 部分だけ real）** | [s2-plan.md:99](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/verbatim/s2-plan.md:99)、[_read:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/source_digest.py:580) | Permission/EIO 隠蔽は防げるが、ENOENT 由来の偽 receipt と TOCTOU no-op が残る |

## 総括

現プランで正しいのは、32 emitter bytes の exact membership、CR を残す raw-line splitter、derive＋require と receipt replay の責務分離、exact marker 重複の拒否です。

段 4 で必ず直すべきなのは次の四点です。

- marker 0 件を無条件 no-op にせず、trigger 骨格の残存を malformed として拒否する。
- `parse_template_file` の位置情報だけに依存せず、marker/directive/frame・実効 `#if`・hole 外代入を閉じる。
- template `true` は裸の 33 番目にせず、閉じた `SkeletonCharacterization` 状態として candidate と分離する。
- 経路 inventory を brief の正しい 5 件へ直し、coverage/frequency を別 consumer として検査する。

pytest・build・Web 検索は実施していません。静的 inspection と行分割の小規模列挙のみで、worktree は無変更です。