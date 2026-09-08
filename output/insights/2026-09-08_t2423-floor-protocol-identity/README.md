# [T-2423] 権威 floor の identity 要素 protocol を build receipt の canonical genome から導出する

2026-09-08。branch `worktree-dev-wave-t2423-floor-protocol-identity`。統合 commit `383d98148`。

権威 floor issuer (`orchestrator/campaign/p3_b4_floor_artifact_issuer.py`) は成果物名の 5 要素 (D1641) の
うち `protocol` を build receipt の top-level key に探していたため、実 receipt では常に
`missing=("protocol",)` で発行を拒否していた。本 wave は protocol を receipt の
`binding.genome_canonical` (binary に束縛された `protocol|flags` 形) から共有 helper
`protocol_from_floor_genome()` で導出する形へ直した。凍結 spec・driver・receipt schema・D1641 は変えていない。

## 依頼の択一 (a)/(b) が偽の前提に立っていたこと

起票文 (worklog 1336 の [T-2423]) と依頼は「protocol は凍結 spec に無く、**build receipt からも導出できない**」を
前提に、(a) spec へ足す / (b) D1641 を 4 要素へ訂正 の択一を置いた。段 3 の敵対相談 (レンズ A) がこれを反証し、
親が現物で確認した。

- portable record (`s8b-binary-admission/v2`) の exact key に `binding` があり (`s8b_binary_admission.py:41-45`)、
  `binding.genome_canonical` は `Genome.canonical()` の `protocol|flags` 形である (`model.py:56-59`)。
- validator は `source.genome_sha256 == sha256(genome_canonical)`、materialization binding との一致、
  `variant_id`・`binding_sha256` の再計算で genome_canonical を binary へ束縛する (`s8b_binary_admission.py:131-147, 356-369`)。
- protocol を取り出す共有 helper `protocol_from_floor_genome()` は既存だった (`genome.py:223-251`)。
- 現行テストは receipt validator を monkeypatch し、実 schema に無い偽の top-level `protocol` key を通していた。
  fixture の genome は非 canonical な JSON 文字列で、実 receipt に在る事実が隠れていた。

段 4 は択一の外の (c) を採った (設計判断は同 wave の decisions fragment `b4-floor-protocol-from-receipt-genome` として記録、番号は fold が付ける)。
(a) は測定された binary の事実から protocol を切り離し人手宣言値で名前を発行できるようにする (規律 2 の向き、
D1374 の却下欄の型)。(b) は D1641 の逐語を減らし、`between_run_floor` が silo / mocc を名前で分ける経路と矛盾する。
**ユーザーが (a) を望むなら再裁定で戻せる。**

## 変更の形

- `_derive_identity`: 各 artifact の receipt を読み (path 解決・sha 照合は従来どおり)、`binding.genome_canonical` を
  `protocol_from_floor_genome` に通して `_identifier` を課す。全 artifact で 1 値のときだけ identity に採り、
  canonical でない・読めない・sha 不一致・混在・**一部失敗** (`protocol_failed` は sticky) はいずれも
  `missing=("protocol",)` で発行を拒否する。
- threads / workload_identifier / campaign_identifier の missing 分岐は到達不能 (loader が cells 非空と
  calibration 一致を、summary validator が campaigns 非空を先に保証する。`floor_pair_driver.py:759-776, 1136-1147`、
  issuer `411-433`) なので削除した。`B4FloorIdentityError`・`missing_identity_elements`・`_authority_value` の
  guard は残す。docstring に「CCBench source の protocol を再検査しない」を明記した。
- tests: receipt validator の monkeypatch を撤去。`test_floor_pair_driver.py` の fixture helper
  (`_portable_build_record` / `_write_inputs`) に後方互換の `genome_canonical(s)` 引数を追加し、既定値の receipt bytes は
  不変 (candidate/reference とも 3095 bytes、sha256 `ce433741…` / `f1795d78…`。HMAC 順序 golden の入力も不変)。
  issuer test に mocc 正例、非 canonical 2 種 (JSON 文字列、未整列 `mocc|B=1,A=2`) + 部分失敗 (candidate canonical、
  reference 非 canonical) の負例、mocc/silo 混在の負例、有効 identity + 非空 missing の guard 正例を置いた。

## 段 3・段 6 で覆した所見と採った所見

- レンズ A: 前提 N2 (receipt から導出不能) を反証 → 採用、wave の方向そのもの。
- レンズ A / 段 2: threads・workload・campaign の missing 分岐は到達不能 → 採用 (削除)。
- レンズ B: 「凍結 spec の instance が無いから erratum 不要」という親の一般論は誤り (D1765 は prereg の陳腐化に対する規則) →
  採用。正しい理由は「(c) は spec も prereg の記述も変えないので陳腐化が生じない」。
- レンズ B: (a) を採る場合の HMAC golden 再固定の独立導出・台帳被覆・schema v4 → (c) で対象外。台帳無編集での被覆は 99.97%。
- レンズ C: `mocc|A|B=1` が helper を通る (must-fix 主張) → **refuted**。親が実測: それは
  `Genome(protocol="mocc", flags={"A|B": 1}).canonical()` の正準形そのものであり、導出 protocol `mocc` は genome の
  protocol 欄と一致する。issuer だけで拒否すると共有 helper の目的 (consumer 間の解釈統一) に反する。
  Genome の flag 名文法を model 側で締めるかは裁定パッケージ候補。
- レンズ C / D: M8 を `missing.append` 削除で作ると StopIteration で帰属が壊れる → 採用。M8 は
  「`protocol_failed` を見ない」型に定義し、それを殺す部分失敗の負例を fix1 で追加した。
- レンズ D: M6 の期待 node は 2 件 → probe で完全集合を実測して本走に写した。

## 焦点走 (親の実測、計算ノード)

`run_tests.py` で issuer / driver / ccbench_spawn_sites / official_perf_closure / material_report の 5 file。
段 5 patch: job 982981.nqsv、320 passed、rc=0。fix1 後: 321 passed、rc=0。

## 変異 matrix

`tools/mutation_harness.py` (`--runner-mode dispatch --detached`、runner は issuer test 1 file) を probe →
本走の 2 段で走らせた。probe (`mutation-spec-probe.json`、全件 SURVIVED 登録) で観測 node を集め、
その完全集合を `mutation-spec-final.json` に写して本走した。対象 file は issuer 1 本、7 変異とも anchor は file 内で一意。

| ID | 変異 | 殺した node (完全一致) |
|---|---|---|
| M1 | derived protocol を `spec.environment.env_tag` に置換 | 5 (正例 + 負例 4: env_tag が ID として通り identity が組めるため負例も赤) |
| M2 | derived protocol を定数 `"silo"` に置換 | 5 (同上) |
| M3 | `len(protocols) != 1` を `not protocols` に緩める | 1 (`test_mixed_receipt_protocols_are_rejected`) |
| M4 | `protocol_from_floor_genome` を `split("|", 1)[0]` に置換 | 2 (`[unsorted-flags]`、`[partial-noncanonical]`) |
| M6 | filename の `__protocol-` segment を落とす | 2 (filename test、正例) |
| M7 | `_authority_value` の `missing_identity_elements` guard を外す | 1 (有効 identity + 非空 missing の guard 正例) |
| M8 | `protocol_failed` を見ず `len(protocols) != 1` だけで判定 | 1 (`[partial-noncanonical]`、fix1 で追加した負例) |

本走: baseline PASSED、KILLED 7 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0、期待 node 完全一致 7/7。
登録しなかった候補: M5 (receipt sha 不一致で `continue` しない) は producer loader が先に拒否するため帰属不成立。
親 brief の M6' (protocol 欠落時に `"silo"` を推測) は loader の exact key 検査が先に拒否するため帰属不成立。
M8 の旧定義 (`missing.append` の削除) は StopIteration で赤になり受理集合の変化を示さないので採らなかった。

## 受入全走と、main 側欠陥の取り込み

受入 attempt 1 は `stage=preflight-index-flags` (rc=70、source_rc=128) で止まった。原因は本 wave の差分ではなく
local main c12e25078 の `.codex/worktrees/*` gitlink 混入で、`git submodule foreach --recursive` が
`No url found for submodule path '.codex/worktrees/accwall-unit-a' in .gitmodules` を返す (本 wave が実測)。
同じ根本原因を `dev-wave-research-gate` が `prerun-fingerprint` 段で先に観測して failures fragment へ登録し、
是正は `48837186c` (index からの gitlink 110 本除去 + 既知違反登録) と `cf837838a` (母集団 pin の追従) が担った。

取り込み前に、別セッションの是正を独立 context の敵対監査へ掛けた (規律 6、`verbatim/s6-consult-incoming.md`)。
結論は「是正 commit 群は取り込んでよい」で、根拠は次の 4 点。

- 既知違反 entry の射程は full SHA + 種別 + finding 1 件に限定され、他 commit・将来 commit・同種 2 件目は通さない (D221 の意図どおり)。
- `48837186c` / `cf837838a` はいずれも `product=codex; role=author` の trailer を最終 block に持ち、新しい違反を作らない。
- 現 main の tree の mode 160000 は `.gitmodules` に正規登録された `external/ccbench` 1 件だけ。
- `git rm --cached` は index だけを変え、主 checkout の Codex 子 worktree の実 directory は残る (親が 125 件の実在を実測)。

監査が real と判定した手順上の点も採った。**受入の自動 main merge は preflight より後**に走るため、旧 gitlink を持つ
tip のままでは受入が是正へ到達できない。したがって親が先に main を手で merge してから受入を投入する。
受入 receipt は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2423-floor-protocol-identity/` に残す。

## 残る限界と scope 外

- protocol は「accepted build receipt の canonical genome の protocol 部」であって「CCBench source で確認した protocol」ではない。
  許可リスト・source 束縛 gate は D1696 の再訪条件 (人手の見落とし 1 件) が未成立のため足していない。
- 本 wave 単独では production で権威 floor は発行されない。t2412 (loader の HEAD 不動点、D1774) の着地、実 spec の作成、
  実測 (D1641) が別途要る。依頼文の「この 1 点だけで発行できない」は、コード上の identity の最後の欠落という意味で真。
- 受入所要台帳は編集していない (F903 の衝突点を避ける)。改名・追加した issuer test 6 nodeid は未登録で既定 cost になる。
- 既知違反 entry の `ruling` 欄は「ユーザー承認は事後報告」と書くだけで、どのユーザー裁定で批准されたかを entry 単体から
  特定できない。機械 schema (非空 ruling) は満たすので取り込みを止める理由にはしないが、監査は裁定パッケージ候補として残した。
  台帳は append-only なので entry は変えず、ここに記録する。

## 一次資料

`verbatim/` に brief、plan、敵対相談 2 本、裁定 2 本、実装子・fix 子の報告、レビュー 2 本、
別セッションの是正を取り込む前の敵対監査 (`s6-consult-incoming.md`) の全文。
`verbatim/s6-fix1.md` だけは `git diff --check` に抵触した末尾空白 (markdown 改行の半角空白 2 個 × 2 行、
`## 総括` 節の 1〜2 行目) を除く可逆最小正規化を施した (可視文字不変)。原文は sha256
`828e0badc12212a50691e1934b1eae4f50054d54433b201853478494024b1e07`・2630 bytes、正規化後は
`232da5c60096e0133227c51a49e503076e1898f6070f28a57d2de876d38e476d`・2626 bytes。復元は当該 2 行の行末に
半角空白 2 個を戻す。
`mutation-spec-probe.json` / `mutation-ledger-probe.json` / `mutation-spec-final.json` / `mutation-ledger-final.json`。
受入 receipt は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2423-floor-protocol-identity/` (受入は記録 commit の後に走るため repo に入れない)。
