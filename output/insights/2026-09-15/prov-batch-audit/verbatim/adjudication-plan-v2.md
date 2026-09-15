# 段 4 裁定 + plan v2 — 全史 provenance 監査のデータ取得一括化

## 0. 親が段 3 の後に自分で実測して閉じた事項

| # | 内容 | 結果 |
|---|---|---|
| A-1 | plan 提案の取得コマンドを**全史 10443 件**で `git show -s --format=%s` / `%B` と突合 | **subject mismatch 0 / message mismatch 0**。framing の NUL 数 31329 = 3N で exact 一致。一括 7.73 秒 対 per-commit 507.83 秒 (16 並列) |
| A-2 | `tools/codex_reasoning_ab.py` の hash pin の用途 (L-3) | `TRACKED_HASHES` に `check_ai_provenance.py` は**含まれない**。`_LEGACY_CASE_HASHES` は過去ケースの snapshot 記録で、`test_task_manifest_binds_frozen_provenance_to_literal_values` は **literal 同士**を照合するだけ。現行 file を計算しない |
| A-3 | 現行 bytes を計算して pin する検査の有無 | **0 件** (`sha256` / `read_bytes` / `digest` / `hashlib` と `check_ai_provenance` の同居検索が空) |
| A-4 | `tools/mutation_harness.py:1400` の「同名実装」 | `_dispatch_timeout_overrides` (D612 の dispatch timeout 上書き)。**本 wave が触る取得層と無関係**で、meta-test で照合される別経路 |

## 1. 所見の裁定

| 所見 | 判定 | 採否 | scope | 措置 |
|---|---|---|---|---|
| **S-1** 「対象集合が同じなら被覆等価」は不成立 (blocker) | **real** | **採用** | 内 | 親 brief の論証を**撤回・訂正**する (下記 §2)。plan の OID ごと文字列比較は必須要件へ格上げ |
| **S-2** 改修後コード内 differential は共通弱体化を検出しない | **real** | **採用** | 内 | **変更前コードを独立に走らせる全史旧新比較を必須**とし、削減不可とする |
| **S-3** 変異 #3・#4 は受理集合差と断定できない | **real** | **採用** | 内 | 変異分類を `DW-M08` に従い再設計 (下記 §4) |
| **S-4** `%s` 境界 fixture を具体 bytes で固定 | **real** | **採用** | 内 | 子が実測した継続行規則を実装へ渡す (下記 §3) |
| **L-1** 84.7 % から「全史 5 秒」は導けない | **real** | **採用** | 内 | 効果見積もりを撤回・訂正 (下記 §2)。主張は「取得 subprocess を 2N → 1」に限定 |
| **L-2** 「受入 1 投入につき必ず 2 監査」はコードと不一致 | **real** | **採用** | 内 | merge 後監査は `behind > 0` のときだけ。条件付きで記録 (下記 §2) |
| **L-3** consumer 波及の全列挙が未完 (blocker) | **real** (提起時点) → **親が A-2〜A-4 で閉じた** | 採用 (確認済み) | 内 | 停止機構は動的束縛のみ。checker 改修を禁止する静的 pin は存在しない |
| **L-4** 成長比例は消えず定数が下がるだけ | **real** | **採用** | 内 | 記録の主張を弱める。`_ai_agent_values` 維持の理由は「証明費用」であって「残存コストが小さいから」ではない |
| **L-5** メモリは同時保持数を測る必要 | **partial real** | **採用 (縮小)** | 内 | 32 worker は**スレッド**で辞書を複製しない。48 個の全史 checker 同時起動は導けない。段 6 で peak RSS を 1 度測るに留め、streaming は実装しない |

**scope 外と裁定した real 所見**: なし。段 3 が挙げた裁定パッケージ候補 (残存 parser 最適化、`%P` の一括化、
streaming 移行条件、他コストの同梱) はいずれも**本 wave では実装せず**、段 7 で裁定パッケージへ送る。

## 2. 親 brief の訂正 (S-1 / L-1 / L-2 を受けて撤回する主張)

1. **撤回**: 「範囲を変えないので被覆等価は自明に成立する」。
   **訂正**: 被覆等価が成立するのは「**監査対象 commit 集合が同一**」**かつ**「**各 commit へ渡る
   subject / message が OID ごとに同一**」の両方が成り立つときだけである。後者は自明ではなく、
   A-1 の全史突合と、plan の OID ごと検証 (framing・件数・OID 集合の exact 一致、不成立なら全廃して
   既存経路へ) が担保する。D908 の等価性要求は対象集合の維持だけでは満たせない。
2. **撤回**: 「約 10 秒 / 約 5 秒」「2 桁速くなる」。
   **訂正**: 確定しているのは「**正常経路の message 取得 subprocess を 2N 本から 1 本へ減らす**」という
   構造的事実と、A-1 の「一括 7.73 秒 対 per-commit 507.83 秒 (16 並列)」である。全史 wall の削減幅は
   **実装後に同一 HEAD・同一設定で旧新を測って確定する**。逐次 n=200 の費目比率を 32 並列の wall へ
   直接適用しない。
3. **訂正**: 受入 1 投入の監査回数は「preclaim は到達した attempt ごとに 1 回、**merge 後は
   `behind > 0` のときだけ** 1 回」。したがって投入あたり 0〜2 回で、merge なしなら概算 473 秒
   (監査比 28.3 %)、merge ありなら 607 秒 (44.2 %)。「6 投入で 27 分」は上限側の条件付き値であり、
   merge 回数に応じて約 13.4〜26.8 分である。
4. **維持**: 「216 日で 480 秒関門」は**予測モデルであって実測ではない**と明記する。13.3 ms/commit は
   一点の `wall/N` で固定費と傾きを分離していない (D274 自身が同じ限界を述べている)。
   関門 480 秒の実在は `tools/dev_wave_land.py:2958` で確認済み。到達日は断定しない。

## 3. plan v2 — 確定する設計

段 2 plan を**基本的にそのまま採用**し、次を追加・格上げする。

1. **取得コマンドは plan のまま**採用する。
   `git log --no-walk=unsorted --stdin -z --format=tformat:%H%x00%s%x0a%x00%B%x0a`。
   A-1 で全史 mismatch 0 を親が実測済み。
2. **fail-closed の全廃 fallback は必須要件**。終端 NUL・フィールド数 `3N`・OID の形式/一意性/
   要求集合との exact 一致のいずれかが崩れたら、**部分結果を使わず全件を既存 `show` 経路へ戻す**。
3. **`_normal_commit_audit` への注入は keyword-only 引数**とし、`ancestry` とは**別引数**にする
   (取得差と ancestry 差を独立に検査できるようにするため)。
4. **逐次 oracle 経路 (`ancestry is None`) には一括結果を渡さない**。独立実装性を保ち、
   等価性テストが自己参照にならない構造を維持する。
5. **`_ai_agent_values` (`:1276`) と `_isolated_parsed_trailers` (`:1215`) は変更しない。**
   理由は「取り分が小さいから」ではなく**証明面を拡大しないため** (L-4 の訂正)。
   `%(trailers)` に `--only-input` 相当が無いことは、段 3 sol が `trailer.inject.*` を実 commit へ
   与えても差が出なかったと実測したが、全設定の等価性は未証明である。
6. **`%s` は git に出させる。** 段 3 sol が実測した現物 `a3168d8552d4…` の規則
   (「継続行の先頭 2 空白を保持し、連結用の 1 空白を加える」= 単純な空白畳み込みではない) を
   fixture の期待値に使う。**未実測の形状を推測で期待値にしない。**
7. **明示 LF は decode 前の git 出力内に置く** (text mode の CRLF 正規化と順序が変わるため)。
8. **記憶量**: streaming は実装しない。段 6 で peak RSS を 1 度測って記録する。
9. **公開出力の不変**: 一括取得の失敗を新しい公開診断にしない。失敗時は既存経路へ戻し、
   既存の例外・順序・rc をそのまま再現する。

## 4. 変異事前登録 (`DW-M01` / `DW-M03` / `DW-M08`、S-3 を反映)

**分類を 3 つに分ける。`DW-M03` に従い、診断文字列だけの赤は KILLED に数えない。**
node は段 4 時点で存在しないため、`DW-M07` に従い **probe (全件 SURVIVED 期待) で観測 node を集めてから
本登録する 2 pass** とする。

### 群 I — 受理集合 / fail-closed 挙動を変える (KILLED 期待)

| # | 注入点 | 変異 | 旧が拒否し新が受理する入力 |
|---|---|---|---|
| I-1 | 一括取得の OID 対応付け | record を 1 つずらして OID へ割り当てる | trailer 欠落 commit A に、正当な commit B の message が割り当たり A が受理される (S-1 の反例そのもの) |
| I-2 | 一括 parser | message を `.strip()` / `.rstrip()` する | 末尾改行の有無で trailer 解釈が変わる commit |
| I-3 | 検証 | framing 不成立時に**部分結果を採用**する (欠落を無視) | 欠落した OID の違反を見逃す |
| I-4 | `:2096` 後 | 一括結果の OID 列で**監査対象を上書き**する | 対象から漏れた違反 commit |
| I-5 | fallback | 取得失敗時に既存経路へ戻さず**空結果で続行**する | 取得が落ちた範囲の違反全部 |

### 群 II — 公開出力 / 例外順を変える (diagnostic sensitivity pin、KILLED に数えない)

| # | 注入点 | 変異 | 期待 |
|---|---|---|---|
| II-1 | formatter | `%s` を body 先頭行へ置換 | 複数行先頭段落 fixture で label が不一致 |
| II-2 | `:2107-2111` | `pool.map` を完了順収集へ | 最初の例外が変わる |
| II-3 | fallback | log / decode 例外をそのまま公開 | rc=2 の診断文言が旧と不一致 |

### 群 III — 構造 pin (性能・独立性。受理集合を変えない)

| # | 注入点 | 変異 | 期待 |
|---|---|---|---|
| III-1 | `:2096` 後 | 一括取得を常に無効化 | findings 同一だが message 用 subprocess 数が `1` → `2N` へ退行 |
| III-2 | `:2096` 後 | ancestry oracle にも一括結果を渡す | oracle 側の `show` 観測が消える (独立性の喪失) |

**登録しないもの**: plan の旧 #3 (区切りを SOH へ) は、本文 SOH が現物 0 件で fallback が意味を保存する
ため、単独では受理集合も出力も動かない。**本文 SOH を含む合成 fixture を足したうえで群 I へ入れるか、
登録しない**。「fallback が意味を保存する変異を KILLED と報告しない」ことを実装子へ明示する。

## 5. 段 5 の分割

実装面は `tools/check_ai_provenance.py` と `orchestrator/tests/test_check_ai_provenance.py` の 2 file で、
取得層と等価性テストは密結合する。**所有を分けず 1 単位・Codex `role=author` 1 本**とする
(`DW-S06-B` の「一枚岩なら理由 1 行」に相当)。

## 6. 受入・検査

- 焦点走: `orchestrator/tests/test_check_ai_provenance.py` + `check_ai_provenance` を参照する consumer test。
- 全史旧新比較は**本 wave 一回の移行受入証拠**として親が実走し、worklog へ書く。**常設 pytest にしない。**
- 変異 matrix は 2 pass (probe → 本登録)。
- 受入全走は `tools/dev_wave_wait.py acceptance`。
