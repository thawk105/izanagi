# 段 4 裁定 — [T-316] 意味 gate 実装 (親裁定 + プラン v2 + 変異事前登録)

base: main `62ddcc93` (段 3 完了後に ff 取り込み済み)
入力: `s1-brief.md`、`s2-plan-c.md`、`s3-consult-sol.md` (レンズ A)、`s3-consult-luna.md` (レンズ B)
段 3 の 2 レンズはいずれも **NO-GO**。ただし「方向への NO-GO」ではなく
「**この主張のまま実装するな**」への NO-GO であり、両者とも実装の形を具体的に処方している。

---

## 0. 最重要の裁定 — 主張の範囲を縮小し、設計択一は返す

両レンズが**独立に**同じ核心を突いた (レンズ A blocker 1・4、レンズ B blocker 1)。

> ユーザー裁定 案 2 が指定した build 段の別防壁は「source の DSL/IR 化」または
> 「build 出力 copy-out の厳格化」の二択である。**有限 lexical な効果 denylist はどちらでもない。**
> build 防壁として採るなら、それは非同値な**第 3 の選択肢**であり、ユーザー裁定へ返すべきである。

**親裁定 (real、採用):** レンズの指摘は正しい。親 brief の N1 は「denylist は R1 の却下理由に
当たらない」までは正しい (両レンズが独立に追認) が、「だから親が build 防壁として採ってよい」は
誤りである。したがって:

- **(D-1) 実装はする。** ユーザーは本 wave の command 引数で「coder/auditor 出力に対する意味 gate を
  実装し、valid-schema な注入と `diff_digest` echo が通らないことをテストで固定せよ」と明示指示した。
  実装対象は測定済みの攻撃 4 種を hole seam で拒否することであり、これは**受理集合を狭める方向にしか
  効かない**ため、案 2 のどちらの選択肢を後で採っても矛盾しない。
- **(D-2) 主張は「測定済み 4 種に対する受理集合の縮小 (defense-in-depth)」に限定する。**
  成果物・docstring・台帳のいずれにおいても、これを
  **案 2 の build 段防壁である**とも、**host-security boundary である**とも、
  **意味論的に閉じている**とも書かない。レンズ A blocker 4 の処方どおり。
- **(D-3) 設計択一はユーザー裁定へ返す。** 「案 2 の build 段防壁として (a) source の DSL/IR 化、
  (b) build 出力 copy-out の厳格化、(c) 本 wave が実装する lexical 効果 gate をもって充当、
  のいずれを採るか」を裁定パッケージで返す。親は決めない (`DW-S04`)。
- **(D-4) certified 安全性を主張しない。** レンズ A blocker 1・3、レンズ B blocker 3 を採用。
  sort の reward hack (R2-b 未実装)、cache/WAL/COMMIT/freeze への gate 結果の非束縛、
  `quarantine()` 外の materializer は**未閉鎖**として名指しで台帳に残す。

---

## 1. 所見の裁定表

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 / B-3 | 上流 blocker 未解除のまま実装開始 | real | 採用 (D-2/D-4 で主張を縮小) | 内 |
| A-2 | `L.quarantine()` は全 coder-derived source の単一 seam ではない (`p3_s4_red.py`、手動 patch + `--allow-coder-derived-build`、`_build_broken`、shell materializer) | real | 採用 (未閉鎖として名指し記録) | 外 |
| A-3 | cache/WAL/COMMIT/freeze が gate 実行を証明しない | real | 採用 (未閉鎖として記録、R3-3/R3-9 依存) | 外 |
| A-4 | denylist は host effect に対して閉じていない (`close`/`fsync` 不在、`File(...)` の間接、`2 - 1` の定数畳み込み) | real | 採用 (D-2。残余を明記) | 内 |
| A-5 | exact-token deny table の偽陽性 (`bool open = false;`)、`edited_text` を渡すと CCBench 固定部で恒真拒否 | real | **採用 (実装必須条件)** | 内 |
| A-6 | **W-2 は既に deny-only。新規 security credit ではない** | real、親 brief を refute | 採用 (W-2 を格下げ) | 内 |
| A-7 | backoff 4 種は synthetic template の seam contract test に限定される | real | 採用 | 内 |
| A-8 / B-6 | 親の M2 は driver E2E ではない、M4 の「repo に不在」は広すぎ | real、親の実測記述を refute | 採用 (記述を限定) | 内 |
| A-9 / B-5 | `forbidden_identifiers` は恒偽のまま | real | 採用 (未閉鎖として記録) | 外 |
| A-10 | bytes 非反射が全漏洩面を覆っていない (`value`/`literal`、S6 provenance の `str(e)`) | real | 採用 (実装必須条件) | 内 |
| B-2 | R3-3 field mapping を踏んでいる (scanner 入力 / rendered source / `working_diff` の 3 domain) | real | **部分採用** — 3 domain の関係をコードと test で束縛する。canonical field 分離そのものは scope 外 | 内 (束縛) / 外 (分離) |
| B-7 | 変異帰属が W-1/W-2 で未分離 | real | 採用 (変異登録に反映) | 内 |
| B-8 | backoff 経路に auditor は存在しない | real | 採用 (明記) | 内 |
| — | 親 brief「W-2 がなければ auditor を騙すと W-1 も迂回できる」 | **refuted** (A-6) | 撤回 | — |
| — | 親 brief「閉じた効果 denylist」 | **refuted** (A-4、段 2 プラン自身も認める) | 表現を撤回 | — |
| — | 親 brief「編集候補 5 file に生きた bytes pin なし」 | confirmed (両レンズ) | 維持 | — |
| — | 親 brief N2 (trigger の α 閉鎖) | confirmed (標準 proposal 経路について) | 限定して維持 | — |
| — | 親 brief N3 (backoff pin 不一致) | confirmed | 維持 | — |

---

## 2. プラン v2 (段 2 プランからの差分だけを書く)

段 2 プラン `s2-plan-c.md` を基礎とし、次を**必須変更**とする。

- **(V-1) scanner 入力の束縛 (A-5、B-2)。** scanner に渡すのは `coder` が供給した hole 実装
  文字列**そのもの**であり、`edited_text` (骨格を含む全文) や `working_diff` ではない。
  これを spy test で機械固定する。`edited_text` を渡す実装は CCBench 固定部の
  `open`/`read`/`write`/`thread`/`syscall` により**恒真拒否**になる (レンズ A が実コードで実証)。
  さらに「scanner が見た bytes」と「実際に source へ書かれる hole bytes」が同一であることを
  test で束縛する (B-2 の 3 domain 対応付けのうち、本 wave が担う部分)。
- **(V-2) W-2 の格下げ (A-6)。** `apply_mandatory_deny_only_veto()` は**新規の安全性差分では
  なく、既存性質の factoring と docstring 是正**として実装する。docstring に
  「mandatory deny-only veto; affirmative security credit なし」を固定し、
  **「advisory」と書かない** (R1 の指定)。加えて sink で auditor を必ず再検証する
  (mutable dataclass の事後書き換えに対する防御。A-6 後段)。
- **(V-3) 変異可能性の確保 (A-6、B-7)。** W-2 が「呼び出しを元の分岐へ戻す変異」で生存しないよう、
  W-2 の受理集合効果を**実 driver 経路**で検査するテストを置く
  (正常 machine-pass + auditor `reject`/`uncertain` が reject されること)。
- **(V-4) deny rule の個別検査 (A-7)。** deny table の各 category について、
  その category を削る変異が殺されるテストを置く。攻撃 4 種だけでは
  例えば `read` rule を削る変異が生存する。
- **(V-5) backoff テストの限定 (A-7)。** backoff の 4 種注入は既存 `_mk_template_dir()` /
  `_TEMPLATE` を使う **synthetic template の seam contract test** と明記する。
  「実 backoff 軸 E2E」とは書かない (現行 pin で `applied()` が停止するため書けない)。
- **(V-6) bytes 非反射の全面化 (A-10)。** `value` / `literal` / `implementation` に
  それぞれ別 sentinel を置き、例外・WAL・critic render・S6 provenance (`str(e)` 経路) の
  **全投影に一つも現れない**ことを検査する。
- **(V-7) 残余の明記 (A-4)。** `close`/`fsync` 等の未収載 identifier、`File(...)` のような
  型経由の間接効果、`2 - 1` 等の定数畳み込みを要する無退出 loop、macro token-pasting、
  事前取得済み function pointer を**残余**として docstring と台帳に列挙する。
  `while (true) { break; }` を保守的に拒否することも明記する。
- **(V-8) 未閉鎖層の列挙 (A-2、A-3、A-9)。** レンズ A の「層別の閉鎖判定」表をそのまま
  成果物へ載せる。scope 外の層を実装したふりにしない。

---

## 3. 変異事前登録 (`DW-M01`、B-057)

実装後の最終 commit で anchor を再検証してから本走する (`DW-M07`)。
各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つに絞れること」を
実装完了時にコードで確認してから確定する。確認できないものは登録せず実効 gate へ再照準する。

| ID | 位置 | 変異の意図 | 期待 | 単一理由性の根拠 (実装後に再確認) |
|---|---|---|---|---|
| M1 | `coder_effect_gate` の process/shell rule | `system` 等を deny table から外す | KILLED | 前段の structural quarantine は `std::system` を通す (段 1 で実測)。後段に効果検査は無い |
| M2 | 同 file/stdio rule | `ofstream` を外す | KILLED | 同上 |
| M3 | 同 network rule | `socket`/`connect` を外す | KILLED | 同上 |
| M4 | 同 sleep/block rule | `read` を外す (V-4 の個別検査) | KILLED | 4 種注入テストでは殺せない。個別 rule テストだけが殺す |
| M5 | 無退出 loop 検出 | `while (true)` の判定を無効化 | KILLED | structural quarantine は loop を見ない |
| M6 | `quarantine()` の gate 呼び出し | scan 結果を無視して常に pass | KILLED | seam の唯一性。ここを外すと全注入が通る |
| M7 | scanner 入力 | `coder.implementation` の代わりに `edited_text` を渡す | KILLED (**過剰拒否側**) | V-1 の spy test と、正常候補の正例テストが同時に赤くなる |
| M8 | W-2 の合成関数 | 呼び出しを元の `verdict != "pass"` 分岐へ戻す | KILLED | V-3 の実 driver テストだけが殺す。A-6 が「これは現状生存する」と予告した変異 |
| M9 | bytes 非反射 | 例外へ `implementation` を再び反射させる | KILLED | V-6 の sentinel テスト |
| M10 | 正例 | deny table に `sort` を足す (過剰拒否の注入) | KILLED (**正例側**) | 受理集合を承認外に縮小する変異。正常候補 15 件が赤くなる |
| M11 | `DiffRejectSubtype.HOST_EFFECT` | subtype 文字列を別値へ | KILLED | reject 経路の相乗り検査 |

**受理集合を縮小する wave なので、承認外の過剰拒否を検出する正例 (M7、M10) を登録した**
(`DW-M01` の要求)。

---

## 4. 成果物影響 (`DW-G05`)

- **W-1 を実装しない場合:** 測定済みの 4 種注入が hole seam を通り、certified 選択・fitness・
  proof chain に任意 host 効果を含む variant が正規経路で入りうる (段 1 で実路実測)。
  実装すると `CODER_DERIVED` hole の受理集合が「deny table を満たすもの」へ狭まる。
  現行の正常候補 (sort 15 件、trigger 32 wire、backoff 正常形) の受理は不変 (親が偽陽性 0 件を実測)。
- **W-2 を実装しない場合:** 受理集合は変わらない (A-6 により既に deny-only)。変わるのは
  docstring の実態整合と、将来の順序変更に対する耐性。**新規の security credit は生じない。**
- **凍結 bytes・certified の既存値・レポート数値は不変。** 受理集合を狭めるだけ。
- **未閉鎖のまま残るもの (成果物への影響が残る):** sort の reward hack (R2-b)、
  cache/WAL/COMMIT/freeze への gate 結果の非束縛、`quarantine()` 外の materializer、
  `forbidden_identifiers` の恒偽、案 2 の build 段防壁本体。

---

## 5. ユーザーへ返す裁定パッケージ (段 7 で成果物化)

1. **R-1 (核心):** 案 2 の build 段防壁として (a) source の DSL/IR 化、(b) build 出力 copy-out の
   厳格化、(c) 本 wave の lexical 効果 gate をもって充当、のいずれを採るか。
   **親の推奨 = (b) を次 wave で実装し、(c) は defense-in-depth として併置する。**
   理由: (a) は R1 が sort について明示的に却下しており、backoff/trigger だけに入れても
   sort の raw 経路が残る。(b) は sandbox blocker に依存せず今すぐ実装でき、
   R3-6 の must-fix そのものである。
2. **R-2:** `quarantine()` 外の coder-derived build 経路 (`p3_s4_red.py`、手動 patch +
   `--allow-coder-derived-build`、直接 `buildcache` caller) を admission 外の
   「非認証成果物」として機械隔離するか、現状どおり残余とするか。
3. **R-3:** cache/WAL/COMMIT/freeze へ semantic gate receipt を束縛するか (R3-3/R3-9 依存)。
4. **R-4:** `forbidden_identifiers` を producer/consumer/schema から削除するか、
   実 finding schema へ接続するか (レンズ A の推奨は削除)。
