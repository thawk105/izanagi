# [T-1907] 旧 backoff consumer のために、式 v1 の patch を別名で凍結した

`authority: none` / `default_effect: no-state-change`

**種別:** 裁定済み項目の実装 + 記録。実装面の差分は新規 file 1 本 (`patches/silo-backoff-fixed-v1.patch`)。
性能・正しさの新規測定はゼロ。

- 日付: 2026-09-16 (JST)
- wave: `dev-wave-t1907-backoff-v1-patch-freeze`、branch `worktree-dev-wave-t1907-backoff-v1-patch-freeze`
- 起点 local main: `0c292eff6f39d797afac7481b89c94de43c07386`
- 実装 commit: `7df8ad9d021ca934e4c1ffbb505abcad2d70b050`
- 裁定: D1098 (2026-08-27、ユーザー裁定)、D1281 (2026-08-29)
- 依頼の要点 (逐語): 「8 件の WAL SHA pin を張り替える移行案は採らない」「対象は既存 v1 の保存に限定する」
  「[T-2647] と backoff 消費側が重なる可能性があるので、段 1 で編集面の重複を実測すること」
  「規律 2 を緩めない」「本題の凍結だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」

## 0. この wave が主張すること・しないこと

**主張する。**

1. 合成枝の式が v2 へ変わる直前の patch (git blob `f7a5444…`) を、bytes のまま別名 1 file で保存した。
   bytes 一致は `sha256sum` / `git hash-object` / `cmp` の 3 通りで親が実測した (§1)。
2. 現行 patch、consumer の参照先、凍結 3 file、旧 sweep の 3 WAL は変わっていない (§4 の sha256 照合)。
3. 追加した file は、`patches/` 直下を走査する既存の在庫検査 2 種の走査対象に入り、既存テストは緑のまま
   (焦点走 10 passed)。未登録の `IZANAGI_` token を足すと既存検査が拒否する (変異 M1 KILLED)。

**主張しない。**

- この file が旧 static-backoff sweep の 3 WAL を**生成したときの bytes** であること。WAL にも lock にも
  patch の版は記録されておらず、生成期の版は初版 `476a128` の時期に当たる (§1)。
- 旧実験の完全な再現、現行 consumer が v1 を使うこと。consumer の配線は変えていない。
- この file の bytes が今後改変されないこと。**bytes を pin する検査は置いていない** (依頼が scope 外とした)。
  変異 M2 (式の改変) と M4 (空 file 化) は、選んだ runner 集合の既存テストでは検出されない (§4)。
- 「旧 consumer の再走で 8 pin が壊れる経路は閉じた」という一般化。段 1 の probe は site 設定を通して
  いない 3 構成を見ただけである (§2)。
- 研究のどこかが本件で止まっていた / いなかったこと。調べていない。

## 1. 凍結した file

| 項目 | 値 |
|---|---|
| path | `patches/silo-backoff-fixed-v1.patch` |
| 取得元 | `4dfd3785b^:patches/silo-backoff-fixed.patch` |
| この bytes を入れた commit | `4f7bb3c76325b7f97a9efda071b92a84732d375e` (2026-07-02) |
| git blob | `f7a54445764025112317151106712bb9d97678ab` |
| sha256 | `35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911` |
| 前提とする元 blob | `cmake/Options.cmake` = `b9a3c740…`、`include/backoff.hh` = `3db8c08f…` |

元 blob は CCBench `6656e93` (旧 3 campaign の lock が記録する commit) と `511c953` (現行 pin) の双方で
同一だった (`git -C external/ccbench ls-tree` で親が実測)。適用・build はしていない。

`patches/silo-backoff-fixed.patch` の版の履歴 (`git log` と `git rev-parse <commit>:<path>`):

| 導入 commit・日付 | blob | 位置付け |
|---|---|---|
| `93c32cf38`・2026-06-22 | `476a128…` | 静的 backoff 初版 |
| `b97ee9153`・2026-06-29 | `24c8373…` | `BACKOFF_NOINLINE` を追加 |
| `30c66880b`・2026-06-30 | `90e83b5…` | EVOLVE-BLOCK マーカーを追加 |
| `4f7bb3c76`・2026-07-02 | `f7a5444…` | `BACKOFF_FIXED` 未供給時の `#error` を追加。v2 直前まで。**凍結対象** |
| `4dfd3785b`・2026-08-26 | `06d272b…` | 合成枝の式を v2 へ (`git diff f7a5444 06d272b` は式 1 行だけ) |
| `91a5bfca3`・2026-09-07 | `eb319d8…` | 現行 v3 |

式の行 `double now_backoff = static_cast<double>(BACKOFF_FIXED);` は v1 の 4 版で同一。
「v1 patch」を f7a5444 と同定した根拠は、起票元 (`output/insights/2026-08-26/b10-backoff-shape-orthogonal/ruling-package.md`
の A-2) が「合成枝の式が v1 から v2 へ変わった」ことへの対処を論点にしており、その直接の前像が f7a5444 だから。
段 3 レンズ A もこの同定を点検し、476a128 を選ぶべき論拠は成立しなかった。

旧 3 WAL の先頭時刻 (`date -u -d`): write-heavy と balanced は 2026-06-22、read-heavy は 2026-06-28。
いずれも初版 476a128 の時期に当たる。ホスト帰属は WAL の `env_tag=linux-baremetal` だけでは確定しない。

## 2. 段 1 の前提実測と、その射程

起票時 (2026-08-26) の懸念は「旧 consumer を v2 patch で再走すると、新しい variant 識別子が同じ campaign に
入り、8 件の WAL SHA pin を壊しうる」だった。8 pin の実体は、`output/s1-freeze/measurement_freeze.json` (3)・
`output/s1-freeze/known_axes_freeze.json` (3)・`output/s8b-freeze/holdout_freeze.json` (2) が持つ
`backoff-sweep-silo-{balanced,write-heavy,read-heavy}` の WAL の path と SHA である。

親が `verbatim/campaign-id-probe.txt` で実測したこと (probe 本体は repo 外
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1907-backoff-v1-patch-freeze/probe_campaign_id.py`):

- 旧 3 campaign の lock の内容から、旧 hash `484c663e` / `493813a7` / `610004b9` を 3 件とも再計算で再現した。
  旧 lock は `search_config` に build admission policy を持たず、CCBench commit は `6656e93`。
- 現行 `backoff_sweep.config_for` に admission policy を束縛した 3 構成の campaign id は
  `2899b6a7` / `172b45ad` / `57160b6c` で、旧 id と 3 件とも一致しない。

**射程の限定 (段 3 A-1 を採用して訂正した)。** この probe は `p2_2._campaign_cfg_for_site` を通していないので、
Pegasus 実走の id そのものではない。一方、現行の通常 resume が旧 lock を拒否することには、probe とは独立な
コード上の根拠がある: `orchestrator/campaign/ident.py` の `verify_admission_preimage` は lock の admission
policy が現在の実行文脈と一致しなければ拒否し、`verify_against_lock` は certified 経路で旧形式 lock を
read-only とし、正準 pre-image の完全一致を要求する。`ensure_resumable_wal` は WAL の tail repair をこの照合の
後にしか走らせない。`backoff_repro.py` も admission policy を
束縛する。**これはコードの読解であり、実走では確かめていない。** report 再生成など別経路で旧 campaign に
書込みまで到達するかは確認していない (段 3 A-1)。

親 brief の誤りは 2 つあり、段 2 plan と段 3 が見つけた: (1)「旧 3 WAL は 2026-06-22 生成」の一括断定
(read-heavy は 06-28)、(2)「再走による pin 破壊経路は既に閉じている」「止めている研究は無い」という一般化。

## 3. 編集面の重複 ([T-2647])

`verbatim/overlap-probe.txt` (probe 本体は repo 外の `probe_overlap.py`)。記録時点で `git worktree list` に
載る worktree 128 件 (自分を除く) を、committed = `main...HEAD` の変更名、dirty = 各 HEAD blob とディスクの
bytes 比較、untracked = `patches/*.patch` の 3 方法で見た。**`patches/` と凍結 3 file に触れる検出は 0 件**。
backoff 消費側の他 file に触れる worktree は 20 件あり、本 wave の編集面 (新 patch 1 本と `patches/README.md`) とは
素集合だった。

観測外 (段 3 B-4): 独立 clone、index だけの変更、将来の編集予定、古い branch に取り残された差分。
[T-2647] の残作業の記述 (worklog 1549、`output/insights/2026-09-16/t2647-b10-tail-downstream.md`) は cohort の地位・
独立監査・図などで、本 wave の編集面に触れない。T-2647 が消費する現行 patch (v3) は本 wave で 1 byte も変えていない。

## 4. 検証

| 検査 | 結果 |
|---|---|
| bytes 検収 (親) | `sha256sum` = `35237d31…f911`、`git hash-object` = `f7a5444…`、`git cat-file blob f7a5444 \| cmp -` rc=0 |
| 保護対象の sha256 不変 (親、実装統合後) | 現行 patch `a5e0710c…580a`、measurement freeze `203de36b…`、known_axes freeze `354f4b87…`、holdout freeze `315b1eb8…`、WAL balanced `8ac3f47e…`、write-heavy `9c179331…`、read-heavy `c74d5837…`。段 2 plan 時点の値と全件一致 |
| provenance | 実装 commit の `--message-file` 検査 rc=0、full-history 監査 rc=0 (10,512 件、新規違反なし) |
| 焦点走 (commit 済み clean) | 10 passed、計算ノード request `1591.nqsv`、78 秒 |
| 変異 matrix | baseline PASSED、KILLED 1 / SURVIVED 2 / MISMATCH 0 (期待と 3/3 一致)。`mutation-spec.json`、`mutation-ledger-1.json` |
| 受入全走 | 本記録の commit 時点では未実施。land の必須入力として記録 commit の後に走らせる |

焦点走の 10 node は、在庫 helper `_patch_added_define_interfaces` を呼ぶ `orchestrator/tests/test_ccbench_spawn_sites.py` の 7 件、
`orchestrator/tests/test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`、
および段 3 B-1 が棚卸し漏れとして挙げた `orchestrator/tests/test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`
と `orchestrator/tests/test_login_headroom.py::test_ceiling_numeric_literal_occurs_only_in_login_headroom_module`。

**変異 matrix** (実装 commit `7df8ad9d0` に対し `tools/mutation_harness.py` を wave worktree へ直接適用、
runner = `python3 tools/run_tests.py --force-dispatch` + 上の 8 node、`--runner-mode dispatch`):

| ID | 変異 (`patches/silo-backoff-fixed-v1.patch`) | 期待 | 結果 | pytest 集計 |
|---|---|---|---|---|
| baseline | なし | PASSED | PASSED | 8 passed |
| M1-unregistered-izanagi-token | コメント行末へ ` IZANAGI_FREEZE_PROBE` | KILLED (token 在庫テスト 1 node) | KILLED、失敗 node 完全一致 | 1 failed, 7 passed |
| M2-formula-offset | 式へ ` + 1.0` | SURVIVED | SURVIVED | 8 passed |
| M4-empty-file | 全文を空に (削除ではない) | SURVIVED | SURVIVED | 8 passed |

- M1 は「新 file が既存の `IZANAGI_` token 在庫 gate の走査対象に入る」ことの確認であり、凍結 bytes の正しさの
  検出力ではない (段 3 A-6)。runner 集合内で M1 に反応するのは token 在庫テストだけで、define 在庫の 3 つの
  正規表現 (条件指令・cache 変数対応・CMake interface) はコメント行に当たらない。
- M2 / M4 の生存は、式の改変と内容の喪失を runner 集合内の既存テストが検出しないことを示す。依頼が pin の追加を
  scope 外としたことの帰結であり、equivalent や合格ではない。3 変異は注入 diff の sha256 がそれぞれ異なり、
  走行後の木は clean・bytes 一致・HEAD 不変を親が確認した。
- 冗長 gate: `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` は作業ツリーの
  非 output 変更を一律に拒否し、どの変異でも赤になるので runner 集合から外した (段 3 B-1 / B-2)。
- 見送った変異: M3 (初版 476a128 の全文へ置換) は M2 と同じ類。M5 (README の sha256 改変) は docs で実装面でない。

## 5. 段 2〜4 の経過

- 段 2 plan 1 本 (`verbatim/plan.md`)、段 3 敵対 2 本 (`verbatim/consult-a.md` = 裁定・scope・過大主張、
  `verbatim/consult-b.md` = 実効性・受入・変異)。所見は A が real 2 / refuted 3 / 成立しない 1、B が real 6 / refuted 1。
  scope 外の real 所見は無く、裁定パッケージは作っていない。裁定の全文は `verbatim/s4-adjudication.md`。
- 変更を強いた所見: B-1 (棚卸し漏れ 2 node)、B-2 (変異の runner 集合を固定しないと M1 の期待 node が完全集合に
  ならない)、B-3 (harness の spec は削除を表現できず、M4 を空 file 化へ変更)、A-1 / A-2 (親 brief の一般化の訂正)。
- README は既存の警告文を書き換えず、凍結小節だけを足した (A-4 の限定を最小形で採用)。
- 段 6 の敵対レビュー子は省いた (DW-C00 の軽量版)。設計択一は段 4 で閉じ、実装は blob の bytes 複製で親の
  `cmp` / `git hash-object` が完全に検収でき、正しさ防壁と受理集合に触れないため。

## 6. reader の棚卸し (新 file を読みうるもの)

段 2 plan の P2 表 (`verbatim/plan.md`) と段 3 A-5 の補記。いずれも静的な読解。

- 読んで集計するが判定は変わらない: `orchestrator/tests/test_ccbench_spawn_sites.py` の define 在庫 (glob `*.patch`)、
  `orchestrator/tests/test_p3_s4_loop.py` の `IZANAGI_` token 在庫 (glob `*.patch`)。
- 固定 path で現行 patch だけを読む (新 file を自動選択しない): `backoff_sweep.py`、`backoff_repro.py`、
  `backoff_profile.py`、`p3_s4_loop.py`、`backoff_extended_sweep.py`、`b10_backoff_shape_sweep.py`、
  `backoff_requested_us.py`、`b10_backoff_static_tail_formal.py`、`s8b_expected_materialization.py`、
  `condition_meaning_gate.py` の `DEFINE_SPECS`。
- 登録 entry だけを読む: `patches/ledger.json` の consumer (`silo_ladder_rung1_contract.py`、`projection_guard.py`)。
- 分類する: `tools/check_ai_provenance.py` は `.patch` を実装面と判定する (Codex author 必須)。
- verifier・grammar・source identity (`EVOLVE_BLOCK_SOURCES`) に新 file を取り込む経路は見つからなかった。
  全動的経路の不在を証明したものではない。

## 7. 工数

| 子 | 段 | model / effort | wall | model calls |
|---|---|---|---|---|
| plan | 段 2 | gpt-6-astra / medium | 889 秒 | 15 |
| consult (2 本) | 段 3 | gpt-6-astra / medium | 238 秒、312 秒 | 9、15 |
| author U1 | 段 5 | gpt-6-astra / medium | 126 秒 | 10 |

子の実装 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1907-u1` (branch `impl-dev-wave-t1907-u1`) は
段 9 の撤去対象外で、残置する。
