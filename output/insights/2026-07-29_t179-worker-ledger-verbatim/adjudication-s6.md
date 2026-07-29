# [T-179] 段 6 裁定 — 敵対レビュー 2 本の real/refuted と fix scope

レビュー A (数値の帰属レンズ) = must-fix 8 / nit 1 / backlog 2、判定「受理不可」。
レビュー B (gate 実効性レンズ) = must-fix 9 / backlog 2 / nit 2、判定「NO-GO」。
どちらも静的検査のみで、pytest は実走していない (`DW-O05`)。緑として数えない。

## 親が実測で裏取りした結果 (2026-07-29)

| 主張 | 実測 | 判定 |
|---|---|---|
| A1: 最終 `total_token_usage` が null だと正常値が 0 に化け strict も緑 | 再現。1050 の session が `cli_reported=0`、`--strict` で **rc=0** | **real** |
| B4: JSON として妥当な非 object 行 (`[]`) が黙って読み飛ばされる | 再現。malformed に数えず `turns=0`、rc=0 | **real** |
| B3: root 不在 / 空 dir / filter 0 件が `--strict` で rc=0 | 3 経路とも **rc=0** | **real** |
| A5: 1 file 内の複数 `session_meta` を融合 | 実データでは全 10 file が meta 1 個。潜在欠陥として real | **real (潜在)** |
| A4: 同一 session_id が 2 file | 実データでは 0 件。潜在欠陥として real | **real (潜在)** |
| A6: 複数 `turn_context` の model を最初の値へ全量帰属 | focus2 (`019facbe`) だけ `turn_context` が **2 個**。ただし両者とも `(gpt-5.6-sol, max)` のため本 wave の数値は不変 | **real (潜在、今回値に影響なし)** |
| A3: `turns` は model turn でなく nonnull `token_count` 件数 | そのとおり。全 10 session で `turn_context` は 1〜2 個、`token_count` は 28〜71 個 | **real (定義の名乗り過ぎ)** |
| A1 の型異常一般 | 実 10 session は全 field 存在・全 int・cumulative 単調・最終 non-null・壊れ行 0 | 実データは健全。**gate の穴だけが real** |

**親の主張の訂正**: 「6 stage 値と総和が一致した = 分類が正しい」は循環である (A7)。
総和一致は誤帰属の対で成立しうる。よって本 wave では stage 正解を
**prompt 逐語から親が独立に導いた session_id→stage 表**で裏取りし、その表を insight に凍結する。
aggregate 一致はその追認にすぎない、と記録を書き換える。

## 採用する fix (scope 内、must-fix)

| # | 由来 | 内容 | 成果物影響 (`DW-G05`) |
|---|---|---|---|
| F-1 | A1, B1 | usage field が欠損・null・非 int なら 0 に畳まず `malformed_usage` issue を立て strict で拒否。`input` / `cached_input` / `output` / `reasoning_output` を record と totals に公開 (T-179 の scope 文が明示要求) | 直さないと実消費 950 が台帳で 0 として確定し、T-181/T-182 の比較根拠が消える |
| F-2 | A2, B9 | `compaction_delta` を因果中立な名 (`cumulative_minus_per_turn`) へ改名。`context_compacted` / `thread_rolled_back` / `turn_aborted` の event 数を列として公開。cumulative 非単調を issue 化 | 直さないと rollback 由来の差を compaction と誤って台帳へ記録する |
| F-3 | A3 | `turns` → `model_calls` に改名し `turn_contexts` を別列で公開。定義を docstring に明記 | 直さないと「434 model turns」が定義不明のまま下流の分母になる |
| F-4 | A4, A5 | session_id を case 正規化して重複判定。1 file 内の複数 `session_meta` を issue 化 | 直さないと resume/分割ログで二重計上または continuation 欠落が黙って通る |
| F-5 | A7, B2 | stage 規則の照合を prompt の**先頭部分**に限定し、本文中の引用 role 文字列に乗っ取られないようにする。複数 stage 競合は `ambiguous` issue。`段6の read-only focused (adversarial) reviewer` が `focus` に落ちること。テストに per-session の stage / model / reasoning の独立期待値を追加 | 直さないと aggregate 緑のまま session→stage が入れ替わる |
| F-6 | B3, B4, B5 | root 不在はエラー。選択 session 0 件は strict 非 0。JSON 妥当な非 object 行を malformed に数える。malformed / meta 欠落 issue は**選択された file に限定**し、無関係 wave の壊れ行で strict を汚さない。cwd 欠落 meta を issue 化 | 直さないと 1 件も読んでいない台帳が健全な成果物として受理される |
| F-7 | B6 | retry group の key に cwd を含め、wave を跨いだ融合を止める | 直さないと別 wave の独立 job が retry として合算される |
| F-8 | B7 | validator 再利用を既存 `check_codex_output.py` の受理集合と**完全同値**にする (size 上限を含む)。両方向 (正常 completed / 短小 / 総括なし / 上限超過) をテストで固定 | 直さないと既存 gate より広い / 狭い受理集合が台帳側にだけ生まれる |
| F-9 | R-B11 | `--stage-map` の unknown 判定を「走査全体に存在しない key」に限定し、cwd filter で選外になった key を過剰拒否しない | 直さないと full-root 用 map の再利用が健全入力を落とす |
| F-10 | B10 | 工数行の探索を該当 entry の本文かつ fenced code block 外に限定 | 直さないと引用された過去値を正本として掴む |
| F-11 | A10 | sessions root と path を `resolve()` して出力 bytes を dataset 単位で決定的にする | 直さないと同一 dataset で台帳 bytes が変わる |
| F-12 | B8, B12 | テストの独立 oracle 化 (human/JSON の期待値を実装から取らず literal で固定) と、下記の変異単一理由 fixture の用意 | 直さないと共通集計層のバグを両 renderer が共有して通る |

## 採用しない (real だが scope 外 → 記録して次タスクへ)

- **A8** cwd 部分一致では wave の受理集合を固定できない (path 再利用・`-backup` 接尾辞)。
  → 恒久解は launcher が wave manifest / session allowlist を発行すること = **[T-180] の責務**。
  本 wave は代わりに、対象 10 件の session_id を insight に凍結して監査可能にする。
- **A9 / B6 の意味論** prompt hash は retry lineage ではない (同文 = retry とは限らない)。
  → 因果的な retry 同定は launcher receipt が要る = **[T-183] の責務**。台帳は「同文 group」と名乗る。
- **A11** library import 時の自己 pycache。CLI 経路では発生しない。→ backlog。
- **B10 の grammar 一般化** 他形式の工数行 (「Codex 実装 2 + fix 5」等) への対応。→ backlog。

## 変異事前登録の改訂 (`DW-M02` / `DW-M07` の再照準)

レビュー B の指摘を採用し、段 4 の登録を次のとおり改める。**改訂の事実と理由を台帳に残す。**

- **M2 を取り下げ、M2' へ再照準**: `session_id[:8]` 変異は records が list のため登録した
  「session 融合」が起きず、かつ healthy fixture の ID 群と連鎖して赤理由が一意にならない (B 指摘)。
  実効 gate は**重複検出**なので、M2' = 重複判定の case 正規化を外す / 重複 issue を出さない、へ照準し直す。
- **M7 を kill 計上から外す**: retry 正規化の変異は受理集合も fail-closed 挙動も変えないため、
  `DW-M08` に従い **diagnostic sensitivity pin** として別枠に記録する。
- **M4 / M8 は複数 node**: kill は成立するが、失敗 node 集合を全件記録する (`DW-M08`)。
- **M5 / M6 に単一理由 fixture を追加**: M5 は `task_complete` だけが欠落し agent_message は健全な
  fixture、M6 は total のみ不一致 / review のみ不一致の 2 fixture を用意する。
- **新規登録** (F-1/F-6/F-5 の gate が実効であることの証明):
  - **M9**: usage の型異常を 0 に畳む (F-1 の gate 無効化)
  - **M10**: 選択 session 0 件でも strict rc=0 (F-6 の gate 無効化)
  - **M11**: stage 規則を prompt 全文照合へ戻す (F-5 の gate 無効化)

最終 anchor (old 逐語) は fix 後の統合 commit で再検証する (`DW-M07`)。

## fix の分割 (`DW-S06-B`)

**一枚岩 1 単位とする。理由 (1 行): F-1〜F-12 は同じ 3 ファイルの同じ集計層・出力層・テスト層を
相互依存して書き換えるため、所有を割ると patch が必ず競合する。**
横断所見も同じ Codex 実装単位へ寄せ、親は直接直さない。
