# [T-1223] 段 4 裁定 + プラン v2 + 変異事前登録

## 所見の裁定

| # | 出所 | 所見 | 判定 | scope |
|---|---|---|---|---|
| 1 | B-1 | 深さ 1 要求は production 契約 (受入前の再帰初期化) と整合せず未立証 | **real** | 内 (P1 撤回) |
| 2 | A-1 | `initialized` は内容実在を保証しない (正しい HEAD の空 worktree が通る) | **real** | **外** (起票) |
| 3 | A-2 | `collect_run` / `make_packets` / freeze CLI は snapshot を再検証しない | **real** | **外** (起票) |
| 4 | A-3 | 負例が独自 spec 専用で、production の `spec=None` 経路を実行で固定しない | **real** | 内 |
| 5 | A-4 | oracle key 集合を固定するテストが無く、key 漏出を変異が殺さない | **real** | 内 |
| 6 | A-5 | 親の「source hash pin 無し」実測は誤り (`apparatus-pin.json` が反例) | **real** | 内 (記録のみ) |
| 7 | B-3 | 負例が `git_object_closure=False` だけで production 経路 (True) を固定しない | **real** | 内 |
| 8 | B-4 | delimiter 判定・複数 top-level の変異帰属が不成立 | **real** | 内 (設計変更で一部消滅) |
| 9 | B-2 | plan の正例が「nested 未初期化を受理」を固定してしまう | **real** | 内 (1 と同時に解消) |
| 10 | B-5 | 成長負債と実装面 scope は問題なし | 追認 | — |

## 裁定 1 — (P1) を撤回する。要求は「manifest の全行が `initialized`」とする

親の provisional (P1)「深さ 1 だけ要求」は撤回する。親が一次資料で裏取りした反証:

- `tools/dev_wave_wait.py` の `_submodule_readiness_preflight` は `git submodule status --recursive`
  相当の出力の `-` / `U` を受入 claim 前に rc=2 で拒否する。
- `docs/pegasus-runbook.md:858-861` は受入投入前の `git submodule update --recursive` を要求する。
- `docs/archive/worklog-phase3-0815-558.md:460-464` ([T-1124]) は、非再帰 init で
  `external/ccbench/third_party/shirakami` が未初期化のまま残り受入が rc=2 で止まった事例を
  独立 2 wave で記録し、`--init --recursive` への是正を起票している。

したがって「正当に運用された作業木 = 全深度 initialized」であり、全深度要求は production を壊さない。
壊れるのは**受入すら通せない状態の作業木から作った snapshot** であり、それを oracle が
正規と認定しないことこそ本 wave の目的である (規律 2)。

**副次効果:** 深さパラメータと深さ算術を持たないので、レンズ B 所見 4 の「兄弟 path 誤認
(`deps/a` と `deps/ab`)」と plan のリスク 1・2 が**構造的に消滅する**。

**レンズ A は「全深度を要求しない裁定を支持する」と書いたが、その根拠は
`docs/dev-wave/operations.md` の非再帰起動手順だけで、受入 preflight の実装を見ていない。**
実装 (`dev_wave_wait.py`) と runbook が要求する状態を優先する。

## 裁定 2 — spec に緩和 key を新設しない。検査は無条件

plan の `require_initialized_submodule_depth` key は採らない。理由は 2 つ。

1. 規律 2: caller が spec 経由で受理集合を広げられる lever を新設しない。
2. A-3 の「独自 spec 経路だけ固定して production が fail-open に戻る」型の回帰を構造的に消す。

`_snapshot_spec` は変更しない。検査は `verify_snapshot` 内で `expected` を参照せずに行う。

## 裁定 3 — scope 外の real 所見 2 件は実装せず起票する

- **(A-1) `initialized` は内容実在を保証しない。** `_submodule_worktree_state`
  (`tools/codex_reasoning_ab.py:934-972`) は「submodule path が Git top-level」かつ
  「`HEAD == gitlink_commit`」なら initialized を返し、`.git` marker と期待 admin dir の束縛、
  index と `HEAD^{tree}` の一致、worktree bytes と index の一致を検査しない。
  親 repo 側で `submodule.<name>.ignore=all` を設定すれば root の status / numstat も汚れない。
  **成果物影響:** 空または改変済みの CCBench を読んだ試行が「pin 済み」として trial ledger・
  材料レポート・proof chain に載りうる。本 wave の穴 (未初期化) を塞いでも残る。
  **scope 外の理由:** 三者照合は `_submodule_worktree_state` と manifest 層の受理集合・
  実行コストを変え、本 wave の不変条件 3 (manifest 層を温存する) と衝突する。
- **(A-2) 中間成果物層が再検証しない。** `collect_run` (`3029-3052`, `3464`) は launch receipt の
  oracle SHA を転記するだけ、`make_packets` (`5054-5117`) は manifest を直接読み `verify_manifest` を
  要求しない、append/freeze/reveal CLI (`5616-5641`) は snapshot gate を通らない。
  **成果物影響:** 正規 supervisor 経路の certified decision は閉じるが、receipt・材料 packet・
  verdict freeze は未認証 snapshot 由来でも生成できる。
  **scope 外の理由:** 3 つの別 layer への gate 追加であり、本 wave の 2 file scope を超える。

## 裁定 4 — 親 brief の実測誤り (A-5) を訂正して記録する

brief の「`tools/codex_reasoning_ab.py` の bytes を pin する台帳は無い」は**誤り**。
検索を `--include=*.py` に限ったため、tracked artifact
`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` の `tool_sha256` を落とした。

親が実測した現況: 同 pin の値は `58f1176e...`、現行 HEAD の tool は `64045cfa...` で
**本 wave 以前に既に乖離済み**。Python からの live consumer は 0 件 (`apparatus_pin` /
`apparatus-pin` の py 参照なし。`tool_sha256` の py hit は変異 harness 自身の同名 field)。
したがって pin は歴史記録であり、**更新してはならない**。本 wave は同 pin を触らない。
worklog には「T-1223 後の tool は T-181 certified rerun の装置 identity とは別物」と記録する。

## プラン v2 (実装子への指示)

編集面は `tools/codex_reasoning_ab.py` と `orchestrator/tests/test_codex_reasoning_ab.py` の 2 file のみ。

1. `_snapshot_spec` (`695-712`) は**変更しない**。
2. `verify_snapshot` の `submodule_manifest` 確定後・既存 pin 照合 (`1693-1700`) の前後いずれかに、
   `enforce_closure` 分岐の**外**で次を行う。
   - `submodule_manifest` の**全行**を走査し、`row["initialization"] != "initialized"` の行ごとに
     `reasons` へ 1 件追加する。reason には path を含め、既存 reason 文言と重複しない語で書く。
   - `expected` を参照しない (緩和 key を作らない)。
3. oracle dict (`1703-1724`) は**変更しない**。新しい key を足さない。
4. テスト (`orchestrator/tests/test_codex_reasoning_ab.py`) に次を追加する。実 repo を clone しない。
   `benchmark_snapshots` を引数に取らない。既存 fixture・既存テストを変更しない。
   - **負例 N1**: top-level submodule を gitlink 登録だけして worktree も admin dir も作らない
     合成 snapshot を、独自 spec (`git_object_closure=False`) で検証 → `ValidationError`。
     reason に当該 path が現れることを固定する。
   - **負例 N2**: 同じ snapshot を `git_object_closure=True` の独自 spec で検証 → `ValidationError`。
     (production 経路が closure 有効側であるため、片側だけの固定を許さない)
   - **負例 N3**: top-level を 2 つ持ち、片方だけ初期化済みの合成 snapshot → `ValidationError`。
     未初期化側の path が reason に現れる。**先頭行だけ検査する実装を殺すため、
     未初期化側を manifest 順で後ろに置く。**
   - **負例 N4**: `spec` を渡さない production 経路の固定。`monkeypatch` で
     `TOOL._snapshot_spec` を合成 spec を返す関数に差し替え、`TOOL.verify_snapshot(snapshot, "POS")`
     を **spec 引数なし**で呼んで `ValidationError` を確認する。
     (`spec=` 引数は正規 seam だが、本テストの目的は「spec を渡さない経路」の固定なので使えない。
     DW-O14 に従い最後の手段として monkeypatch を採り、理由をテストの docstring に書く)
   - **正例 P1**: 全 submodule が初期化済みの合成 snapshot → 従来どおり oracle が返る。
     さらに **oracle の key 集合を exact に固定する** (新しい key が漏れていないこと)。
   - **正例 P2**: submodule を 1 つも持たない合成 snapshot → 従来どおり通る
     (空 manifest で恒真に落ちないこと = 過剰拒否がないこと)。
5. `_git_closure_reasons` / `_submodule_inventory` / `_submodule_worktree_state` /
   `_assert_submodule_manifest_sha256` / POS-NEG 突合は**変更しない**。

## 変異事前登録 (B-057、実装前に凍結)

negative (gate を壊す変異。全件 KILLED 期待):

| ID | 変異位置 | 変異内容 | 期待して落ちる node |
|---|---|---|---|
| M1 | 新 gate の判定式 | `!= "initialized"` を `== "initialized"` へ反転 | N1, N2, N3, N4 が fail / P1, P2 も fail |
| M2 | 新 gate 全体 | gate を削除 (fail-open へ戻す) | N1, N2, N3, N4 |
| M3 | 新 gate の位置 | `if enforce_closure:` の内側へ移す | N1 (closure=False 側) |
| M4 | 新 gate の loop | 全行走査を先頭行のみへ変更 | N3 |
| M5 | 新 gate の記録先 | `reasons.append` を oracle dict への key 追加へ置換 | N1, N2, N3, N4, P1 (key 集合 exact pin) |

positive control (承認外の過剰拒否を検出する。DW-M01):

| ID | 変異位置 | 変異内容 | 期待して落ちる node |
|---|---|---|---|
| M6 | 新 gate の判定式 | 判定を恒真化し全 submodule を拒否 | P1, P2 |

**単一理由性の確認 (DW-M01):** 新 gate の入力 (`submodule_manifest` 行の `initialization`) を
前後で拒否する層は無い。`_submodule_inventory` は 2 値を返すだけで拒否せず、
既存 pin 照合 (`1693-1700`) は既定 spec 経路では `None` で不発、
`_assert_submodule_manifest_sha256` は `2476` で verifier の**後**に呼ばれる。
POS/NEG 突合 (`3866-3911`) は同値比較なので、同じ未初期化 hash 同士なら通る。
したがって新 gate を無効化したときの赤理由は新規 node に一意に帰属する。

**期待 node の完全集合は、実装完了後の実 node 名で段 6 に再導出する** (DW-M08、F33)。
上表の N1〜N4 / P1〜P2 は設計上の対応であり、node 名の権威一覧は `--junitxml` で取る。
