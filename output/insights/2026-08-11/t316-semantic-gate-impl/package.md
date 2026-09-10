# [T-316] 実装段 — 何を実装し、何を主張せず、何を裁定へ返すか

- 生成 wave: `worktree-dev-wave-t316-semantic-gate-impl` (2026-08-11)
- 種別: **実装**。commit `fe893069` (gate 本体) と `ff3afec2` (seam 配線 + auditor factoring + fix 2 巡)
- 上流: 裁定パッケージ `2026-08-09_t316-semantic-gate/package.md` (R1〜R5)、
  計測段 `2026-08-10_t316-sandbox-measurement/package.md`、
  ユーザー裁定 **案 2** (worklog 403)、および本 wave の command 引数 (ユーザー指示)

---

## 0. この文書が答える問い

ユーザーは「裁定どおり案 2 で実装し、coder/auditor 出力への意味 gate を実装して、
valid-schema な注入と `diff_digest` echo が通らないことをテストで固定せよ」と指示した。
本 wave はそれを実装した。ただし**実装したものは案 2 が指定した build 段防壁ではない**。
その差を曖昧にしないことが本文書の主目的である。

---

## 1. 段 1 の実測 — 何が通っていたか

repo 外 probe (`probe_premises.py`) を骨格適用下の実路で走らせた。実行後の tree は clean。

| 注入 (hole 内 1 行) | `DiffQuarantine` | auditor `pass` + digest echo | backoff の value↔literal 整合 |
|---|---|---|---|
| `std::system("...")` | **通過** | **通過** | **通過** |
| `execl("/bin/sh", ...)` | **通過** | **通過** | **通過** |
| `std::ofstream(...)` | **通過** | **通過** | **通過** |
| `while (true) { }` | **通過** | **通過** | **通過** |

既存の注入テストは前処理指令と include の**構造**検査 2 件だけで、効果 (shell / IO / network /
無退出 loop) を見る検査は coder-hole admission 層に存在しなかった。

**この probe が測っていないこと (段 3 レンズ A/B が独立に指摘し、親が採用):**
`_quarantine_and_audit()` も build も呼んでいないため、これは**共有 seam の probe であって
driver E2E ではない**。「auditor pass の後に実際に build へ進む」は静的推論であり実測ではない。
backoff 軸は submodule pin 不一致 (`PIN=028f34d` vs 現行 `d706650`) で骨格適用が fail-closed に
なるため、契約層 (`assert_value_literal_consistent`) しか測れていない。

---

## 2. 実装したもの

### 2.1 単一 seam

hole 実装が source へ届く唯一の点は `p3_s4_loop.quarantine()` である。段 2 プランが
3 driver・2 sweep・direct comparison・extime calibration・autonomous preview の 8 経路を
file:line で棚卸しし、すべてがこの seam を通ることを確認した。

structural quarantine が pass した場合**だけ** `coder_effect_gate.scan_host_effects()` を呼び、
finding があれば `DiffRejectSubtype.HOST_EFFECT` の失敗結果へ変換してファイル書き込みへ
到達させない。reject は既存の `record_diff_reject` / `load_diff_rejections` /
`render_rejections` に相乗りさせ、新しい loader も renderer も作っていない。

### 2.2 scanner が見る bytes

**渡すのは coder の hole 実装そのものであり、骨格を含む `edited_text` ではない。**
骨格全文を渡すと CCBench 固定部の `open` / `read` / `write` / `thread` / `syscall` により
**恒真拒否**になる (段 3 レンズ A が `external/ccbench/include/fileio.hh` 等で実証)。
spy test と、materialized source から marker の hole を再抽出して byte-exact に比較するテストで
機械固定した。変異 M7 (`edited_text` を渡す) がこれを殺す。

### 2.3 auditor

`apply_mandatory_deny_only_veto()` は **既存性質の factoring であり、新規の安全性差分ではない**。
段 3 レンズ A が実コードで示したとおり、変更前から machine reject は auditor より先に返り、
machine pass のときだけ verdict が評価されていた。合成関数が足したのは、mutable dataclass の
**事後書き換えに対する sink での再検証**だけである。docstring は R1 の指定どおり
「mandatory deny-only veto; affirmative security credit なし」で固定し、**「advisory」と書かない**。

---

## 3. 意図的に主張しないこと

- **これは案 2 の build 段防壁ではない。** 案 2 の二択は「source の DSL/IR 化」または
  「build 出力 copy-out の厳格化」であり、有限 lexical な効果 denylist は第 3 の形である。
  段 3 の 2 レンズが独立にこれを blocker と判定した。
- **host-security boundary ではない。** 任意の C++ が起こす効果に対して閉じていない。
- **certified の安全性を主張しない。** sort の reward hack (R2-b 独立 oracle 未実装) は
  この gate の対象外であり、閉じていない。

### 残余 (module docstring に逐語で列挙済み)

`close` / `fsync` 等の未収載 identifier、`File(...)` のように constructor 内部が `open()` を
呼ぶ型経由の間接効果、`2 - 1` のような定数畳み込みを要する無退出 loop header、
macro token-pasting、走査対象より前に取得した function pointer、deny table 外の compiler
extension。`while (true) { break; }` は到達可能性解析をせず**保守的に拒否**する (過剰拒否と明記)。

### scope 外・未閉鎖の層 (段 3 レンズ A の層別判定表より)

| 層 | 判定 |
|---|---|
| 3 driver・2 sweep・direct comparison・calibration・autonomous preview の `quarantine()` | **本 gate が適用される** |
| 手動 patch + `--allow-coder-derived-build`、`p3_s4_red.py`、直接 `run_campaign` / `buildcache` | **scope 外・未閉鎖** |
| `s5_permutation_coverage` の直接 CMake build、shell materializer、任意 binary path | **scope 外・未閉鎖** |
| legacy / v2 cache hit (同一 source・admission なら scanner を経ずに再利用) | **未閉鎖** |
| WAL replay、COMMIT、provenance、known-axes freeze、proof chain | **gate の receipt が無く未閉鎖** |
| build 出力 copy-out、run sandbox、独立 oracle、stage receipt | **scope 外・未閉鎖** |
| `_preview` の `forbidden_identifiers` | **恒偽のまま** |

---

## 4. 検査の信頼性

- **段 3 の敵対 2 レンズ、段 6 の敵対 2 レビュー、焦点再レビューの計 5 本がいずれも NO-GO。**
  blocker 1 + must-fix 8 + nit 1 を閉じた。焦点再レビューは 10 所見すべてを独立に `closed` と判定した。
- **親の 2 主張が refute され撤回された。** (i)「W-2 がなければ auditor 経由で W-1 も迂回できる」
  (ii)「閉じた効果 denylist」。probe の位置づけも §1 のとおり限定した。
- **段 6 の blocker**: `while (1.0) {}` / `for (; 0.5f ;) {}` / `while ('x') {}` が gate を通っていた。
  単一 token で contextual-bool が確定する core literal をすべて扱うよう修正し、負制御を追加した。
- **変異 12/12 KILLED** (SURVIVED 0 / MISMATCH 0 / PARSE_ERROR 0、baseline 緑)。
  走 1 は KILLED 2 / MISMATCH 10 で、原因は親の期待 node の取りこぼしだった (erratum として保存)。
  走 2 は M8 の実測集合に非 collectable node (`@real-repo` suffix) が混ざり collection 検査で停止した。
- **M8 は過剰決定だったので単一理由へ再照準した** (`DW-M03` の第一選択)。旧 verdict 分岐へ戻す
  変異は digest 検査の実行順まで変えるため、呼び出しと sink 再検証を残し veto の効果だけを落とす形にした。
- **M7 / M9 / M11 は受理集合を変えない診断 pin である** (`DW-M08`)。
  M7 = scanner 入力の byte 束縛、M9 = 例外への bytes 反射、M11 = reject subtype 文字列の drift。
  kill としてではなく diagnostic sensitivity pin として読む。
- **過剰拒否を検出する正例を 2 件登録した** (M7、M10)。M10 は deny table に `sort` を足す変異で、
  現行の正常候補 15 件が赤くなることを確認する。
- **偽陽性は 0 件** — 現行の正常候補 (sort 15 件、trigger 全 32 wire、正常 backoff 形) はすべて通る。
  親が段 3 待機中に独立実測し、焦点再レビューが最大 379 bytes / 64 token と独立確認した。

---

## 5. ユーザーへ返す裁定

- **R-1 (核心・要裁定):** 案 2 の build 段防壁として (a) source の DSL/IR 化、
  (b) build 出力 copy-out の厳格化、(c) 本 wave の lexical 効果 gate をもって充当、
  のいずれを採るか。**親の推奨は (b) を次 wave で実装し (c) を defense-in-depth として併置する。**
  理由: (a) は R1 が sort について明示的に却下しており、backoff/trigger だけに入れても sort の
  raw 経路が残る。(b) は sandbox blocker に依存せず今すぐ実装でき、R3-6 の must-fix そのものである。
- **R-2:** `quarantine()` 外の coder-derived build 経路を「非認証成果物」として機械隔離するか、
  残余のまま台帳に明示するか。
- **R-3:** cache / WAL / COMMIT / freeze へ semantic gate receipt を束縛するか (R3-3 / R3-9 依存)。
- **R-4:** `forbidden_identifiers` を producer / consumer / schema から削除するか、
  実 finding schema へ接続するか (段 6 レビューの推奨は削除)。
- **R-5:** 非整数 `coder.value` が `int()` 切り捨てで別 genome に帰属する既存欠陥をどう閉じるか。

**実装段の残り blocker ([T-184] canonical stage matrix 未発行、R3-3〜R3-9、R2-b 独立 oracle 本体)
は変わらず。** 本 wave はそれらを閉じていないし、閉じたとも主張しない。
