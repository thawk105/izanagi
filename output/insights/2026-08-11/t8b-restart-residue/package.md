# 裁定パッケージ — 8b 再開の残余 (toolchain 束縛を実装せず返す)

wave `dev-wave-t8b-restart-residue` / branch `worktree-dev-wave-t8b-restart-residue` /
base main `0c336b8e` → 取り込み後 `f4db7036`。**本番コードを 1 行も編集していない。**

起票根拠 = worklog 403 の [T-747] R-4 = (B) / [T-748] / [T-770]、worklog 404 の
[T-781] / [T-782]、および 402 の 8b 統合 wave が返した新事実。
手順の正本 = `docs/phase3-8b-restart-runbook.md`。

---

## 0. 結論を先に

**依頼は「床値実測 → freeze v2 再凍結 → oracle 実走の再開」だったが、3 段とも実行できない。**
実行できたのは docs の訂正だけである。理由は次の 2 層。

**下表は本 wave の段 1 brief 時点 (2026-08-11、base main `0c336b8e`、worklog 末尾 404) の事実である。**
本 wave の走行中に main 側で動いた分は §8 にまとめた。**§8 を読まずに下表を現状として引かないこと。**

| 段 | 塞いでいるもの | brief 時点の状態 |
|---|---|---|
| 床値実測 (W-2) | W-1 (official 解禁) = [T-781] | **裁定で「択保留・調査先行」。実装不可** |
| freeze v2 再凍結 (W-3) | [T-750] | **未裁定** (worklog 403 / 404 が明記) |
| oracle 実走 (W-4 / W-5) | [T-750] + W-3 | **未裁定** |

そのうえで、**W-2 の前提整備として裁定済みだった toolchain 束縛 ([T-747] (B) → [T-783]) も
実装しなかった。** 段 3 の敵対 2 レンズがいずれも NO-GO を返し、blocker 4 件が
いずれも「裁定時点で未見の新事実」だったためである (`DW-S04`)。

---

## 1. 決め手 — A-1 単独は fail-closed 障壁を緩めるだけである

段 4 で親が気づいた非対称性であり、段 2 のプランも段 3 の 2 レンズも指摘していない。

- **現状**: 床値 build は `buildcache.DEFAULT_CC/CXX` = `gcc-13` / `g++-13` を固定要求する。
  Pegasus には無いので `_tool_version` が
  `toolchain cxx が PATH に存在しない: 'g++-13' (fails-closed)` で倒れる。
  **これは事故ではなく、現に効いている障壁である。**
- **[T-783] (compiler 解決を `compilers_for_current_site()` へ寄せる) を入れると**、
  Pegasus compute で `("gcc","g++")` = 実測 gcc 11.4.0 が返り、**build が通るようになる。**
- **束縛検査が無ければ**、これは「認可されていない compiler で床値を測れるようにする」
  だけの変更である。手順書 §1.2 が「既定 compiler へ黙って倒すのは選択肢にしない」と
  書いた当のものになる。

**したがって [T-783] と束縛検査は不可分であり、束縛検査を完全形で出せない以上、
[T-783] だけを先に出すことはできない。** [T-783] の起票文自身が
「[T-747] の択が (B) に決まった場合の実装単位」と条件付けており、単独実装を意図していない。

---

## 2. 束縛検査を完全形で出せない理由 (blocker 4 件)

### B-1. 裁定文が指定する三者照合のうち、attempt 実測値の脚が配線されていない

[T-747] (B) の裁定文は「`calibration_ref` の実 calibration bytes を derived toolchain
authority とし、**attempt 実測値と** `build_v2` toolchain manifest を照合する」である。
これは **三者**照合を指す。

- `tools/pegasus/floor_campaign.sh:769-778` は attempt の実測 toolchain を
  `$ATTEMPT_DIR/{compiler,cxx,cmake}.{path,version}` へ書いている
- **しかしその値は driver へ渡らず、`job-result.json` (`:970-1005`) にも入らない**
- したがって現在の配線では attempt の脚が欠けたまま、authority ↔ `build_v2` manifest の
  二者比較にしかならない

閉じるには shell と driver の両方に手を入れる必要がある。shell は投入インタフェースの正本
(手順書 §8) であり、**scope の拡大についてユーザー裁定が要る。**

### B-2. 現行 calibration に cmake の path と cxx の version が無い

登録済み calibration が持つ toolchain 証拠は次だけである (実測)。

- `/acquisition_receipt/toolchain/compiler_path` = `/usr/bin/x86_64-linux-gnu-gcc-11`
- `/acquisition_receipt/toolchain/compiler_version` (cc のみ)
- `/acquisition_receipt/toolchain/cmake_version` (**path なし**)
- `/acquisition_receipt/ccbench/build_argv` の
  `-DCMAKE_C_COMPILER=` / `-DCMAKE_CXX_COMPILER=` (cc / cxx の絶対 path)

**cxx の version と cmake の path は authority を持たない。** その結果、

- PATH 先頭に「`--version` の第 1 行だけ正しく返し、configure 時に別 flag / 別 compiler を
  注入する cmake wrapper」を置くと通る (`cmake.realpath` 非束縛)
- 期待 realpath 上の g++ が別版へ差し替わっても通る (`cxx.version_first_line` 非束縛)

閉じるには executable の SHA-256 まで持つ authority が要り、**新しい calibration 世代の
発行**を意味する。これは事前登録性 (式 3) に触るため、**pin をどこへ張るかを先に裁定する必要がある。**

### B-3. floor 限定の gate では、同じ contract を使う他の producer が無防備

`pipeline` / `loop` / `s8b_oracle_driver` / `screening_driver` / silo ladder は同じ
env contract を使うが、`build_v2` は toolchain を cache identity に入れるだけで
**認可照合をしない**。floor だけに gate を置くと「1 経路だけ守った」ことになる。
レンズ A は「**裁定なしの floor-only 実装は不可**」と判定した。

### B-4. gate に本番の発火経路が無い (`DW-G04`)

`DW-G04` は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に
書ける場合だけ実装する。書けなければ設計メモに留める」と定める。

- official は W-1 が拒否する
- 投入 script は official 固定で pilot 経路を持たない
- pilot を手で走らせても `require_heavy_work_site` が login を拒否するため、
  計算ノードへ載せる手段が無い
- `output/calibration/` は存在せず、**どの mode でも床値は 1 度も走っていない**

**発火条件を満たす既存 artifact path も計測 ID も書けない。**

---

## 3. 実装するなら必ず要る設計制約 (段 3 の real 所見、moot だが同送する)

1. **version 比較は逐語一致にしてはならない (親実測)。**
   calibration は `command -v gcc` 由来で `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、
   `buildcache._tool_version` は realpath 由来で
   `x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` になる。
   **gcc は argv0 を先頭 token に出すため、同一 compiler でも一致しない。**
   逐語一致にすると Pegasus の正規 run が恒常的に赤になる。
   `silo_ladder_rung1.tool_version_body()` と同型の argv0 除去が必須。
   realpath 同士は完全一致する。
2. **検査は `_toolchain_manifest()` 直後・cache directory 作成前へ置く。**
   build 後に拒否すると、認可外の cache entry・依存物 build・claim 副作用が残る。
3. **authority に `contract_sha256` / calibration path・SHA / generation を含める。**
   tool の 4 値だけだと g1 authority + g2 contract の誤配線が型で拒否できない
   (g1 / g2 の 4 値は同一なので全比較が通ってしまう)。
4. **照合結果を portable artifact へ残す。**
   現状 `build_cells()` は toolchain manifest を built record・portable manifest・journal・
   result のどれにも保存しない。ratified verifier は `configure_argv` / `build_argv` が
   非空文字列列であることしか見ないため、**将来 gate 呼出しだけが消えても artifact から
   検出できない。**
5. **`BuildResult` に toolchain manifest が無い。** `build_v2` の completion manifest には
   あり、戻り値組立て関数も同じ値を受け取って捨てている。additive field で載せるのが
   最小かつ TOCTOU のない形 (cache identity・completion bytes・legacy API は不変)。
6. **`silo_ladder_rung1.py:3554-3588` に同型の束縛が既にある。**
   build_argv からの compiler 抽出、`toolchain.compiler_path` との交差検証、
   `tool_version_body()` による version 比較まで実装済み。共通 helper 化しないと
   silo artifact と floor artifact が別の toolchain を受理しうる。
   ただし silo ladder の現行検査は `contract.calibration_ref.sha256` と比べず、
   calibration file と report 側 `binding.calibration.sha256` を一緒に差し替えると通る。

---

## 4. 裁定へ返す項目

> **裁定結果 (2026-08-11 /rulings 第 5 回、worklog 412、発話「推奨通りで」)。**
> **S-1〜S-4 は全問、下記の親推奨どおり裁定された** —
> S-1 = 共通 helper / S-2 = 現行較正の範囲 + 穴明記 /
> S-3 = shell の `$ATTEMPT_DIR` 値を driver へ渡す / S-4 = W-1 の wave に含める。
> 一次控えは `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §84。
> **S-5 ([T-750]) は本束に含まれず未裁定のまま。**
> 以下は裁定時点の提示内容であり、記録として残す。

### S-1. toolchain 束縛の scope をどこまで広げるか

- **(a) floor だけに置く。** B-3 を明示受諾する (他 producer は無防備のまま)。最小。
- **(b) contract-aware な build 境界へ置き、`pipeline` / `loop` / `oracle` / `screening` /
  silo ladder の全 producer を守る。** 正しいが規模が大きく、silo ladder は所有外。
- **(c) 共通 pure helper を作り、floor と silo ladder の 2 者だけを先に寄せる。**
  `DW-G03` の「独立 2 例」は成立している (floor と silo ladder)。
- **親の推奨は (c)。** (a) は「守ったつもり」を作るだけで、レンズ A が明確に不可と判定した。
  (b) は 1 wave に収まらず、W-1 も W-2 も動いていない現在に投じる規模ではない。
  (c) なら既存の実装 (silo ladder) を正本として抽出でき、純増は floor 側の結線だけになる。

### S-2. authority の強度をどこまで上げるか (B-2)

- **(a) 現行 calibration の範囲で作る。** cc/cxx の realpath + cc version 本体 + cmake version
  本体だけを束縛し、**cmake path と cxx version が非束縛であることを明示受諾する。**
- **(b) executable の SHA-256 まで持つ新しい calibration 世代を発行してから作る。**
  wrapper 差し替えを閉じられるが、**事前登録に触る** (どこへ pin するかを先に決める必要がある)。
- **(c) 独立した immutable receipt を新設し、contract を触らずに強い authority を持たせる。**
- **親の推奨は (a) を先に出し、(b) を [T-657] の世代交代と同じ wave へ寄せる。**
  理由は、(b) 単独では第 2 世代の発効順序 (§4 の争点) と衝突し、
  floor protocol と selector 封印の作り直しを誘発するためである。
  ただし (a) を採る場合、**残る穴を手順書と成果物へ明記する**ことが条件になる。

### S-3. attempt 実測値の脚をどう配線するか (B-1)

- **(a) shell が書いた `$ATTEMPT_DIR/*` の path を driver へ渡し、三者照合にする。**
  裁定文の逐語どおり。shell (投入インタフェースの正本) に手が入る。
- **(b) `job-result.json` へ toolchain 値を足し、collector 経由で照合する。**
- **(c) 三者照合を諦め、authority ↔ `build_v2` manifest の二者にする。**
  裁定文の「attempt 実測値と」を読み替えることになる。
- **親の推奨は (a)。** shell が既に値を採っており、捨てているだけである。
  (c) は「shell が記録した値と build が観測した値が食い違っても検出しない」を残すため、
  そもそも束縛を入れる動機と噛み合わない。

### S-4. 発火経路が無いまま実装するか (B-4 / `DW-G04`)

- **(a) W-1 が開くまで設計メモに留める** (`DW-G04` の既定)。
- **(b) 先に実装し、W-1 と同時に効かせる。** 束縛は W-1 の前提なので、
  W-1 の wave で一緒に作るほうが検査の発火を実証できる。
- **(c) 束縛検査を W-1 の実装 wave に含める** ([T-781] の調査 wave の後段)。
- **親の推奨は (c)。** 束縛と解禁は同じ受理集合の表裏であり、別 wave に割ると
  「解禁したが束縛が入っていない」窓が構造的に開く。**この窓は W-1 が開いた瞬間に、
  認可外 compiler の床値が通る形で顕在化する。**

**本 wave の走行中に W-1 側の新事実が main へ入った (2026-08-11)。**
[T-781] の bounded 調査 wave (`output/insights/2026-08-11_t781-spool-feasibility/package.md`) が
「起票時の前提は誤りで、`qcat -i` により scheduler の spool bytes は独立取得できる。
ただし取得できるのは caller が指定した live request の入力であって現プロセスの同定ではなく、
`qattach command = Enable` のため同一 uid の攻撃者が真正 request の外から command を注入できる。
よって案 A 単独では認可を閉じない」と結論し、択を Q1〜Q4 として再提示した。

**これは S-4 の推奨 (c) を補強する。** W-1 は本 wave が想定したより開いておらず、
admission 設計そのものが未裁定のまま Q1〜Q4 へ差し戻されている。
束縛検査を先に単独で land しても、発火するのは W-1 の裁定が済んだ後になる。

### S-5. [T-750] (W-3 / W-4) の再裁定

**本 wave では触れていない。** worklog 402 が返した 2 点 (producer identity と
budget authority) が未裁定のままであり、freeze v2 再凍結と oracle 実走はここで止まっている。
**8b 再開の残余で最も上流にある未裁定はこれである。**

---

## 5. 本 wave が実施した docs 訂正

| 対象 | 内容 |
|---|---|
| `output/insights/2026-08-11_known-red-exceptions/README.md` | 表の分類語を訂正し erratum を追記 ([T-770] R1 = (b) の census 側)。**実測値は 1 つも変えていない** |
| `output/insights/2026-08-11_t8b-restart-integration/package.md` | R-4 節へ superseded 表示。旧裁定 (a) を実装根拠にしないための導線 |
| `docs/phase3-8b-restart-runbook.md` | §1.3 再測、§1.2 の既定 compiler と version 形式 2 系統、§3 W-1 の 3 点、§3 W-2 の順序、§5 の裁定状態、並走ガードへ検査系 dispatch の 1 段落 (段 8) |

**[T-770] の tests README 側は並行 wave `dev-wave-t770-conditional-unrun` に先を越された。**
本 wave も同じ裁定 (R1 (b) + R2 (a)) を実装していたが、受入 3 走目の merge 段 (rc=70) で
相手の land (main `04e99891`) と衝突して発覚した。相手は
`skiputil.skip_conditional_unrun()` と `test_skip_classification.py` で分類の結線を機械固定し、
変異 4/4 KILLED で裏取りしている上位互換の実装であり、**本 wave 側の同 file 変更は全面取り下げて
main の版を採った。** 相手が触れなかった census 側だけを本 wave が揃える。

## 6. 親 brief の訂正 (レンズが正した親の主張)

- **M-6 は refuted。** 同型の束縛は `silo_ladder_rung1.py:3554-3588` に既に実装済み。
  正しい主張は「floor / `build_v2` 経路に consumer が無い」という狭い形だけ。
- **M-1 の言い方を訂正。** 「投入できない」は誤り。`submit_floor.sh` に mode の分岐は無く
  `qsub` は実行される。正しくは「**enqueue はできるが、official run は計算ノードで rc=2 になり、
  再凍結適格な artifact を完遂できない**」。キュー資源は消費されうる。
- **M-4 の言い方を訂正。** 直接の凍結 pin は無いが、submission receipt の `source_commit` と
  実行時の imported module bytes 照合という **submission→execution の commit pin は在る。**
- **M-3 の一般化を撤回。** 「計算ノードの既定は 11.4.0」は登録済み 2 世代の観測であって
  `gen_S` 全ノードの現在値ではない。

## 7. 並走ガード (3 条件とも遵守)

1. **ノード同居なし** — 本 wave は**計測系のキュー投入を 1 件も行っていない**
   (床値投入が不可のため)。投入したのは検査系 dispatch だけで、provenance 監査
   (request `901529.nqsv`、Elapse 17 秒) と受入全走である
2. **T-139 の pilot / 本走 job 走行中はキュー投入を控える** — 投入の直前に毎回 `qstat` で確認し、
   **T-139 の pilot / 本走 job は一度も queue に無かった**。見えたのは第 3 波の受入全走と
   本 wave 自身の検査 dispatch だけである
3. **裁定帯域は A 優先** — 本パッケージ (B 系) は A 系の後ろに並べる

---

## 8. 本 wave の走行中に main 側で動いた分 (2026-08-11)

本 wave は base main `0c336b8e` (worklog 末尾 404) で brief を書き、land までに 5 回 main を
取り込んだ。その間に **§0 の表が前提にした 3 件がいずれも動いた。**
以下は取り込み後の main から採った事実である。

| 件 | 動き |
|---|---|
| **[T-750] (W-3 / W-4)** | worklog **405** で裁定 2 点 (ともに (a))、**417** で並行 wave `dev-wave-t750-freeze-v2-manifest` が実装・land。freeze v2 の g1 candidate producer と `generate-v2-candidate` CLI、新 module `s8b_oracle_spec.py` と `build-approved` CLI が入り、`verify_manifest` へ cell-product 検査が加わった (受理集合の縮小のみ)。**承認権威は両者とも module 内 pinned literal で現在 `None` = 未承認のため fail-closed** |
| **[T-781] (W-1)** | worklog **413** で Q1〜Q4 が全問 (a)。**official は空集合のまま維持し、A 系列の後まで保留**。§4 S-4 の裁定 (束縛検査は W-1 の wave に含める) と合わせると、**束縛検査の着手は A 系列の後になる** |
| **[T-770]** | 並行 wave `dev-wave-t770-conditional-unrun` が R1 (b) + R2 (a) を先に land (§5 参照) |

**§0 の表の結論は変わらない。** W-3 / W-4 は実装されたが oracle 実走 (W-5) は
承認権威が未承認 (`None`) のため依然 fail-closed であり、W-2 (床値実測) は W-1 が
空集合維持である以上開かない。**本 wave が返した 4 blocker と §3 の設計制約も、
実装先が W-1 の wave へ移っただけで内容は有効である。**

**親の見落としを 1 件記録する。** 当初「投入ゼロの wave」と書いたが、
`tools/check_ai_provenance.py` は login では完走せず計算ノードへ自動 dispatch する。
検査系がこの主張を破ることを見落としていた。T-139 の pilot は走っていなかったため
実害は無いが、「投入ゼロ」を名乗る wave では検査系の dispatch も数える必要がある。
