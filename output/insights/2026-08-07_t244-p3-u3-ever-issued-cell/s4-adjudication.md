# 段 4 裁定 — [T-244] P3 ever-issued cell 台帳 (U-3)

親の裁定。逐語は repo 外 wave job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u3-ever-issued/`) の
`s2/plan.md`・`s3/lensA.md`・`s3/lensB.md`。

## 結論

**実装しない。** 段 5・6 を飛ばし `4→7→8→9` とする。実装差分が無いため、変異 matrix と
実装後の受入全走は対象外である。U-3 は**ユーザー再裁定へ返す** — 親が不採用にするのではなく、
裁定時点で未見だった新事実を添えて択一を戻す。

## 実装しない根拠 (4 点)

### R1 — U-3 (a) の本質は単調性であり、repo 内の台帳では単調にならない

U-3 (a) が防ごうとするのは「successor 世代が意味等価な cell を byte-different に再発行して
使用量 0 の予算を得る」ことである。プランの台帳は authority と**同じ捕捉 commit** から読む。
したがって新しい authority document を書く主体は、同じ commit で台帳の該当 entry を
`(series, cell) → 旧 origin` から `→ 新 origin` へ**置換**できる。置換後は
「台帳に載っている」「origin が一致する」の両方を満たすので gate を通る。
**段 3 の 2 レンズが独立に同じ迂回路を構成した** (A-1 / B-1)。親が plan §6 と
`reflux_origin_ledger.py:1895-1913` を読んで確認したところ、履歴 (parent commit の台帳 blob) と
比較する経路はプランに一切無く、plan §6 自身が「置換は保証外」と明記している。
すなわち実装できるのは「1 commit 内の 2 ファイルの整合」であって「ever-issued」ではない。

**成果物影響:** 実装しても authority の受理集合は「台帳という 2 つ目のファイルとの整合」分しか
狭まらず、U-3 が狙った再発行は受理されたままになる。certified 選択・材料レポート・試行台帳・
proof chain の値は変わらない。

### R2 — 単調性を与える 2 手段は、いずれも既裁定または未実装で塞がっている

単調性を与えるには (i) 外部の append-only anchor か、(ii) 検証可能な predecessor chain
(= epoch router) が要る。
(i) は **U-2 で択一 (a) として明示的に却下され、(b)「同一 clone 内の honest caller に対する
保証と明示的に弱めて名乗る」が批准済み**である。
(ii) は D179 決定 3 / 設計 §4.2 が推奨形として起草したが**未実装**で、実装は設計 wave 送りと
worklog (274) が確定している。
したがって **U-2 (b) と U-3 (a) は現状の実装面では両立しない。**
これは設計パッケージ §9 が「U-1〜U-4 は互いに独立でない」と書いた以上の具体的な非両立であり、
**裁定時点で未見の新事実**として段 4 で扱う。

**成果物影響:** この非両立を解かずに実装すると、名乗り (「全世代重複拒否」) と実装
(「同一 commit の 2 ファイル整合」) が食い違い、proof chain の読者が「全世代履歴を検査済み」と
誤読する。値は変わらないが**記録の正しさ**が壊れる。

### R3 — 台帳を書く主体 (issuer) が存在しない

プランは writer / provisioning API を明示的に作らない。すると最初の entry を誰がいつ載せるかが
未定のまま gate だけが立つ。載せ忘れれば production の authority load が停止し、
現 authority から機械的に再生成すれば R1 の置換をそのまま通す (B-3)。
本番 authority への entry 発行は、U-10 の批准で
「V-2 evidence 正本 + producer topology + 許可された実行経路」の 3 条件成立後の
人間承認 provisioning と定められており、**まだ 1 つも成立していない**。

**成果物影響:** issuer 不在のまま入れると、受理集合に「存在しないファイルを要求する」条件が
増えるだけで、防げるものが増えない。

### R4 — DW-G04 の発火 gate を満たせず、現役 consumer を壊す

現行 production 入力は `authority.origins = []` × 台帳 `[]` で、coverage loop は 0 回、
absent / conflict の分岐は発火しない (A-3)。発火条件を満たす**既存 artifact path も計測 ID も
brief に書けない**。親は brief の (P3) で「既存の同型検査が空 authority のまま存在する」ことを
根拠に発火 gate を満たすと provisional に裁定したが、これは**撤回する** — 既存の
単一 blob 内 cell 重複検査は新 gate とは別条件であり、新 gate の発火経路ではない。
加えて、親が実測したとおり `orchestrator/tests/test_t244_p3_liveness_probe.py` は
`output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` を subprocess 実行して
`returncode == 0` を要求する**現役の受入 consumer**であり、probe は temp repo に authority だけを
commit する。プランの「歴史 artifact なので非互換を記録する」は**事実に反する** (B-2)。

**成果物影響:** 実装すると受入全走が赤になる。放置した場合に変わる成果物の値は無い。

## 所見の裁定表

| # | 所見 | 裁定 |
|---|---|---|
| A-1 | 同一 commit の台帳置換で再発行が通る | **real・採用** → R1 |
| B-1 | 同上 (独立に同型を構成) | **real・採用** → R1 (独立 2 例) |
| A-2 | 同一 clone の linked worktree で台帳差が検出されず proof chain に束縛されない | **real・採用** → R2 |
| B-3 | issuer / producer が無く最初の entry を載せる主体が未定 | **real・採用** → R3 |
| A-3 | production では述語が空虚、発火 gate 不成立 | **real・採用** → R4、親の (P3) を撤回 |
| B-2 | liveness probe は現役 consumer で全走が赤になる | **real・採用** (親が実ファイルで確認) → R4 |
| B-4 | (P1) の「連続する authority document」読み替えは continuity を表現しない | **real・採用** → 親の (P1) を撤回 |
| A-5 / B-8 | schema・test 名・記録予定文言が実装されない履歴保証を名乗る | **real・採用** → 名乗り制限として記録 |
| A-6 / B-9 | 親実測 N5 の一般化過剰 (`duplicate authority origin` は到達不能) | **real・採用** → `parent-measured.md` に erratum 済み |
| B-5 | 複数 entry の負例が無い (`entries[:1]` 変異が生存する) | **real**・本 wave では moot → 将来 wave への入力として記録 |
| B-6 | 変異 M1・M8 は偽 kill、M9 は変異対象が非一意 | **real**・moot → 同上 |
| B-7 | 新 path 固有の境界検査 (symlink / inode / 非 regular) を殺す nodeid が無い | **real**・moot → 同上 |
| A-4 | liveness probe が受理集合から落ちる | **real** — B-2 が「歴史 artifact でなく現役」と訂正。実装しないので発生しない |

## 親の provisional 裁定の帰結

- **(P1) 撤回。** 「世代」を「同一 series の連続する authority document」と読み替える案は、
  continuity を表現する field (predecessor / active pointer / generation) が無いため成立しない。
- **(P2) 撤回。** repo 内 commit 済み artifact を substrate にする案は R1 で破れる。
- **(P3) 撤回。** 発火 gate は満たさない。
- **(P4) は moot。** 実装しないため段 6 のレビュー 2 本は走らせない。段 2・3 は実施済みで、
  この裁定はその 2 レンズの所見に基づく。

## 変異事前登録 (DW-M01)

**登録なし。** 実装差分が無いため、実効 gate へ再照準する対象が存在しない。
段 6 を飛ばすので fix 後の変異走行 (`DW-M07`) も行わない。

## ユーザー再裁定へ返す択一 (推奨付き)

| # | 択一 | 推奨 |
|---|---|---|
| **W-1** | U-3 の substrate をどうするか。(a) clone common-dir に耐久単調な台帳を置く (b) 検証可能な predecessor chain / epoch router に同梱する (c) 単独実装を取り下げ、epoch router の設計 wave の一部として吸収する | **(c)**。(a) は U-2 (b) の trust model を超える保証を単独で名乗ることになり、しかも別 clone・履歴書換えには依然無力。(b) が正しい置き場だが epoch router 自体が未設計 |
| **W-2** | U-2 (b) と U-3 (a) の非両立をどう解くか。(a) U-3 を U-2 の trust model 内へ弱め「事故による再発行だけを防ぐ、故意は防げない」と明記して実装する (b) U-2 を (a) 外部 append-only anchor へ再裁定する (c) U-3 を epoch router 実装後の項目として凍結する | **(c)**。(a) は R3・R4 が残るので今は入れられない。(b) は外部依存の新設で scope が跳ね上がり、D179 決定 4 が「repo 内検査の原理的限界」と認めた範囲を超える判断が要る |
| **W-3** | 「同一 commit の authority ↔ registry 整合」だけを U-3 とは**別名**の防御部品として今入れるか | **入れない**。発火経路が無く (R4)、現役 consumer を壊し (B-2)、防げるものが増えない。D164 の「発火しない検査を防壁として記録する」と D205 の「防御的堅牢化は既定で見送り」の両方に当たる |

## 将来の実装 wave への入力 (実装するときに必ず入れる)

- 複数 entry authority の負例 (先頭のみ登録済み・末尾が欠落 / conflict、順序反転)。
  `entries[:1]` と loop の早期 `break` を変異登録する (B-5)。
- 台帳 path 固有の境界検査 (absent / final symlink / ancestor symlink / directory / FIFO /
  inode swap) と、`_read_regular` 呼出し削除を殺す nodeid (B-7)。
- 変異 M1 は「missing entry を実際に受理させる」形へ、M8 は単独 guard で受理集合を支配しないため
  候補から外し、M9 は parser / committed blob / live read の 3 上限を分割する (B-6)。
- `orchestrator/tests/test_t244_p3_liveness_probe.py` と `liveness_probe.py` の追随を
  同じ D96 変更単位に含める (B-2)。

## 名乗りの上限 (本 wave)

名乗ってよいのは「U-3 (a) の実装可否を段 2・3 で検証し、実装しないと裁定して択一を返した」までである。
P3 充足・部分 P3・provisioning 解禁・多世代開放・cap-lift・certified 選択は名乗らない。
「意味等価な再発行を防いだ」「全世代重複拒否を実装した」とも名乗らない。
D114 の cap=1、D166 の P4 FAIL、P3 FAIL は不変。
