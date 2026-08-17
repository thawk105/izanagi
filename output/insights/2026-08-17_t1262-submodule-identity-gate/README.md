# [T-1262] initialization 判定が submodule の内容の実在を保証していなかった

- wave: `worktree-dev-wave-t1262-submodule-identity`
- 実施日: 2026-08-17 (JST)
- 起票元: worklog archive 604 の `[T-1262]`。[T-1223] が scope 外に置いた三者照合の本体
- 逐語: `verbatim/`、変異台帳: `mutation-spec.json` / `mutation-result.json`

## 何が問題だったか

`tools/codex_reasoning_ab.py` の `_submodule_worktree_state` は
「submodule path が Git top-level」かつ「HEAD == gitlink」で `initialized` を返すだけで、
**worktree の内容を一度も見ていなかった。**

親 repo 側で `submodule.<name>.ignore=all` を設定すると root の status / numstat が汚れないため、
**正しい HEAD を持つ空の CCBench が snapshot oracle を通る。** 結果として、空または改変済みの
CCBench を読んだ試行が「pin 済み」として trial ledger・材料レポート・proof chain に載りうる。

## 親が段 1 で実測した受理形

合成 snapshot を `_seal_git_object_closure` で封緘したのち攻撃し、
`verify_snapshot` を `git_object_closure: true` (production の既定値) で呼んだ結果。

| # | 攻撃 | 結果 |
|---|---|---|
| A | 空 CCBench: `read-tree --empty` + worktree 全削除 + `ignore=all` + 再 seal | **受理** |
| B | worktree の bytes 差し替え + `ignore=all` | **受理** |
| C | `HEAD^{tree}` に無い index entry を追加 + `ignore=all` | **受理** |
| D | `.git` marker を rogue admin dir へ差し替え | **受理** |
| A' | A から `ignore=all` を外した形 | 拒否 (`dirty set mismatch` / `numstat mismatch`) |
| A'' | A から再 seal を外した形 | 拒否 (`git fsck exited 2`) — 内容照合ではなく偶発 |

`_seal_git_object_closure` は seal 時に `submodule.*` の config section を消すが、
`verify_snapshot` は不在を再検査しない。したがって **`ignore=all` は封緘後に設定できる。**

## 何をしたか — 契約の宣言と 8 系統の検査

**契約:** initialized submodule の worktree bytes が、pin された commit の canonical checkout の
bytes と 1 byte も違わないこと。**clean filter を通した等価性ではない。**

1. marker と admin dir / common-dir の束縛 (期待 admin path の全成分が非 symlink)
2. index と `HEAD^{tree}` の一致 (`diff-index --cached`。`git write-tree` は使わない)
3. worktree の生 bytes と index blob id の一致 (git を起動せず `sha1(b"blob %d\0" + bytes)`)
4. worktree の非 directory file 集合と index path の一致 (走査エラーは fail-closed)
5. tracked path の全成分が symlink を経由しない
6. local config の key 名 allowlist (封緘前は transport 系のみ追加で許可)
7. 内容を決める git 呼び出しへの `--no-replace-objects`
8. object format が `sha1` であること

**oracle dict へ field を 1 つも足していない。**

## なぜ生 bytes 照合にしたか (段 2 プランの path-aware hash 案を覆した)

段 2 のプランは `git hash-object` による path-aware hash (clean filter 適用後の blob id 比較) を
推した。親はこれを覆して生 bytes 照合を確定させた。理由は 4 つある。

1. gate が守りたいのは「試行が実際に読んだ bytes が pin どおりか」である。
2. path-aware hash は **CRLF へ一括変換した worktree を受理してしまう** (clean filter が吸収する)。
   生 bytes 照合は拒否する。
3. path-aware hash は外部 clean driver を**起動しうる**。封緘済み snapshot の中で未検証の外部
   program を走らせることになる。生 bytes 照合はどんな filter も起動しない。
4. 検証側の `core.autocrlf` / `core.eol` で結果が変わらない (敵対レンズ B の指摘)。

**偽の拒否が出ないことを実測で確かめた。** 実 snapshot が使う CCBench pin
(`BASE_COMMIT` の gitlink `d706650cdb31e442bef45b9b4216951d4fb40969`) を `--no-local` clone して
新規 checkout し、index の 405 entry (`100644`=285 / `100755`=119 / `160000`=1) を照合した結果、
**生 bytes と index blob id の不一致は 0 / 404、mode 不一致 0、object format は `sha1`**、
全件 sha1 の所要は **0.124 秒**だった。

## oracle bytes の不変を実測した

段 6 のレビュー B が「不変性が証明されていない」と指摘したため、親が直接測った。
決定的な合成 snapshot を**同一の絶対 path**で構築し、変更前 (`3a4c3d43` 時点の
`tools/codex_reasoning_ab.py`) と現実装の両方で `verify_snapshot` を呼んだ。

| 量 | 結果 |
|---|---|
| oracle canonical bytes | **917 bytes で完全一致** |
| oracle の key 集合 | 一致 (14 key) |
| `submodules` 行 | 一致 |
| `submodule_manifest_sha256` | 一致 (`6cdc3ab3f8317ef497d6b664dcb41aab2b5d91c571b37e3c6fff66b595641fdc`) |

これが必要だったのは、`submodule_manifest_sha256` を保持する成果物が
repo 外の `/work/1/SFC/tanab/dev-wave-jobs/` 配下に **293 件** (`dev-wave-t181-certified-rerun`
だけで 29 件) あり、oracle bytes を変えると過去 manifest の replay を壊すためである。

## 敵対検証が親の主張を 6 件倒した

| # | 親の主張 | 判定 | 訂正 |
|---|---|---|---|
| A13 | 実 CCBench で偽の拒否 0 件 | **測り直し** | 作業木の pin `511c9538` を測っていた。実 snapshot が使うのは `d706650c`。再測して 0/404 を維持 |
| A17 | pin 閉包は 2 件 | **real** | repo 内だけを数えていた。repo 外の wave 成果物に 293 件 |
| B11 | コード外の tool pin は 0 件 | **real** | `apparatus-pin.json` の tool 全体 hash を見落とし。ただし [T-1223] が歴史記録と裁定済みで実装影響なし |
| A16 | `copy2` は index stat cache を必ず無効化する | **real** | 同一 filesystem では device が変わらず `core.trustctime=false` 等で判定材料から外れる。本裁定は stat に依存しないので設計影響なし |
| A18 | 純増検出力 = 4 vector | **real** | 独立述語は 3 系統。本 wave の追加を含めて 8 系統 |
| A15 | 費用は 1 秒未満 | **real** | 未確定だった。生 bytes 採用により `hash-object` の subprocess 費用が消え、0.124 秒 / repository が採用値 |

**採用しなかった real 所見が 1 件ある (RA3)。** 敵対レビュー A は
「source root repository にも config allowlist を掛けよ」と要求したが、同じ段の
敵対レビュー B が実測で「実 source root には `user.*` と `extensions.worktreeconfig` がある」と
示した。掛ければ **worktree ベースの build がすべて落ちる。**
source root は本 gate の信頼境界の外である (destination の bytes は source の object database から
fresh checkout され、destination 側で生 bytes 照合される)。裁定パッケージへ回した。

## fix が 2 度、実装の順序を誤った

- **1 巡目**: config allowlist を `_submodule_worktree_state` へ移した結果、
  `_seal_git_object_closure` が**自分で config を消す前に**呼ぶ inventory にも封緘後用の厳格な
  allowlist が当たり、計算ノードで **66 failed**。認証の境界は seal ではなく `verify_snapshot`
  であるため、封緘前は transport 系だけ許す形へ直した (9 failed へ)。
- **2 巡目**: 「単一理由」の exact equality を end-to-end node にも適用したため、
  対象の理由に**加えて**別の理由が併記される node が落ちた (空 index の submodule は
  `git fsck` の unreachable も出す — 親も段 1 probe で同じ併記を観測している)。
  段 4 裁定どおり helper 直呼びのみ exact equality、end-to-end は containment へ戻した (1 failed へ)。
- 最後の 1 件は test 内 helper の signature 不整合という機械的な不具合だった。

## 実測環境の落とし穴 (差分に非帰属)

1. **submodule の再帰初期化が要る。** `git submodule update --init` (非再帰) では
   実 repo fixture の 3 node が `submodule is not initialized` で error になる。
   `--init --recursive` で ccbench / shirakami / googletest の 3 階層を揃えると解消する。
2. **`FORCE_COLOR` の継承。** 親セッションの `FORCE_COLOR=3` が子 process へ継承されると
   pytest の出力に色コードが入り、`test_growth_test_holds_contract.py::test_plain_pytest_delegating_runner_is_not_over_rejected`
   が正規表現を外して落ちる。`env -u FORCE_COLOR -u COLORTERM` で解消することを実証した。
   **この 2 つはどちらも差分に帰属しない。**

## 変異 matrix — 12/12 KILLED、生存 0

`mutation-spec.json` / `mutation-result.json`。runner は `tools/run_tests.py --force-dispatch` の
dispatch recipe、baseline は PASSED (276 passed / 20 skipped)。

| # | 無効化した検査 | kill した node 数 |
|---|---|---|
| M01 | index と `HEAD^{tree}` の一致 (**wave 前の実コードの形 = 空 CCBench が通る形**) | 6 |
| M02 | worktree の生 bytes と index blob id の一致 | 8 |
| M03 | marker と admin dir の束縛 | 3 |
| M04 | common-dir と admin dir の束縛 | 2 |
| M05 | worktree file-set の完全性 | 2 |
| M06 | 期待 admin path 成分の symlink 検査 | 2 |
| M07 | tracked path 成分の symlink 検査 | 2 |
| M08 | local config の allowlist | 17 |
| M09 | object format が `sha1` であること | 1 |
| M10 | 実行 bit / file 種別の照合 | 2 |
| M11 | 走査エラーの fail-closed | 1 |
| M12 | `--no-replace-objects` (replacement ref) | 2 |

**1 回目の走行で 10 件が MISMATCH になった。** 生存は 0 で全件が rc=1 で発火していたが、
親が登録した `expected_nodes` が実際より狭かった。新設 gate を外すと helper 直呼びの node に
加えて end-to-end の node も落ちるためである。1 回目の `failed_nodes` から完全集合 (48 node) を
再導出して登録し直し、2 回目で 12/12 KILLED になった。**1 回目の結果は消していない**
(`mutation-spec.json` は再導出後の版、経緯は本節と worklog に残す)。

**M01 は台帳が要求した「空 CCBench が通る現在の形を再現する正例」である。**
`diff-index --cached` の判定を無効化すると内容照合が存在しない wave 前の形に戻り、
空 index / 空 worktree の submodule 拒否 node が確実に赤くなる。

## scope 外 (裁定パッケージ)

1. **[T-1263]** — `collect_run` / `make_packets` / verdict CLI が snapshot を再検証しない。
   本 gate は `verify_snapshot` と final replay には効くが、receipt・材料 packet・verdict freeze は
   旧 gate で受理された参照を区別できない。
2. **hardlink / TOCTOU** — snapshot 外の hardlink alias で pre/post oracle の間だけ bytes を
   変える攻撃は本 gate では塞がらない。root repo にも同型に存在する既存の境界。
3. **system-level git config** — `_clean_environment` は `GIT_*` と user config を除くが
   system config は残る。repo 外の設定であり本 wave の編集面から届かない。
4. **source root の config allowlist** (RA3) — 上記のとおり。
