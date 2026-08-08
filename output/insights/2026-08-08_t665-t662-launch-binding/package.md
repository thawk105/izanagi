# 裁定パッケージ — [T-665] + [T-662] 起動値の機械束縛 (2026-08-08)

wave = `dev-wave-t665-t662-launch-binding` / branch = `worktree-dev-wave-t665-t662-launch-binding`
逐語 = 同ディレクトリの `verbatim/` (段 1 brief・段 1 実測・段 2 プラン・段 3 レンズ A/B・段 4 裁定)

**本 wave は実装していない。** ユーザー裁定「[T-665]/[T-662] = 束ねた設計 wave 起票可
(launcher 集約か receipt 事後検査かをパッケージで返す)」に従い、設計択一だけを返す。

---

## 何が問題か (1 段落)

dev-wave は `DW-O01` の雛形に従って親が手で `codex exec -m <model> -c model_reasoning_effort=<値>` を
組み立てて子を起動する。model の権威は `DW-O01` の 1 行、effort の権威は各 worker 節にある。
しかし **その権威と実際の起動引数を突き合わせる機構はどこにも無い**。`tools/check_docs.py` の pin が
拘束するのは docs の**文面**だけで、親が組み立てる command は拘束しない。Claude の PreToolUse hook は
Codex 経路に未配線である (`hooks/guard_bash.py` に文字列 `codex` の出現は 0 件)。

---

## 段 1〜3 で実測した事実 (すべて本 wave で測定)

1. **素の `codex exec` も実効値を機械可読に残す。** `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` の
   `turn_context.payload.model` / `.effort`、`session_meta.payload.cwd` / `session_id` /
   `originator="codex_exec"` / `cli_version`。prompt 全文も残る。保持は 2026/07 から現存。
2. **収集層は既に実装済みで production 未使用。** `tools/codex_worker_ledger.py` (1150 行) が
   rollout を決定的に集計し、`--manifest` (exact session selector)・`--stage-map`・`--strict` を持つ。
   `tools/codex_worker_launch.py` (2591 行) は要求値と実効値の一致を検査する launcher だが、
   **repo 内の production caller は自テストのみ** (本日再測)。欠けているのは「**権威と突き合わせる層**」。
3. **段の同定機構は既に drift で壊れている。** 段の判定は prompt 先頭行の正規表現 ([T-179] 当時の
   英語 role 語を要求)。実測で 33 session 中 **30 が `unclassified`**。現行 wave の prompt 先頭行は
   自由文で 10 種類以上あり、規則に合致するものは 1 件も無い。
4. **cwd による wave 帰属は 46% 取りこぼす。** [T-181] wave の 13 session のうち **6 本**が
   wave worktree 以外 (`dw-t181-impl` / `-fix` / `-fix2` / `-fix3` / `-merge`) で走った。
   これは `DW-S05-A` / `DW-S06-B` が実装子・fix 子を別 worktree へ隔離する契約どおりの挙動であり、
   **[T-665] が名指しする段 6 fix 子 4 本が全部この取りこぼしに入る**。
5. **時刻窓では分離できない。** 同 wave の時間窓に 70 session / 14 cwd が存在し、当該 wave は 13 本
   (5.4 倍の過剰包含)。並行 wave が常時 4〜9 本走っている。
6. **`--cwd-contains` は別 wave・別 checkout まで拾う** (33 件中 20 件が別 wave、うち cwd は別 checkout)。
7. **権威は model も effort も時間変化する。** `DW-O01` の luna 行 = `16e0bbb9` 2026-08-08 18:27 JST、
   `DW-S06-A` / `DW-S06-C` の high = `b97ad3b5` 同日 17:30 JST、`DW-S05-A` の high = `2cd329d5` 07-24。
   さらに **[T-181] は自分が land する新契約を wave 内で dogfood した**ため、
   wave 初期 base だけでは足りない。
8. **`turn_context` は 1 session 1 件ではない。** 109 session 中 **14 件 (12.8%) が 2 件持ち**。
   ただし 14 件とも model / effort は不変だった (親の独立再測。段 1 の当初記述を訂正)。
9. **現状維持の害は実測済み。** F56 (`docs/failures.md:1304`) が
   「`-c model_reasoning_effort="ultra"` (存在しない値) は **rc=0 のまま成功**し、rollout に
   `reasoning=ultra` が記録される」を実測。恒久対応 (c) は
   **「未知の reasoning 値と model×reasoning の非対応組は起動前に落とす」**。
10. **docs 予算残 16 bytes** (dev-wave aggregate 25,184 / 25,200)、command 残 43 bytes。
    worktree 命名規約を足すだけでも 91 bytes 要る (裸 ASCII でも 53 bytes)。

---

## 段 3 の判定

レンズ A (sol) = **NO-GO / must-fix 7 件**、レンズ B (luna) = **NO-GO / must-fix 8 件**。
両者が独立に一致した中核所見は 3 つ。

- 段 2 プランの推奨 A+ が挙げる採用条件「raw `codex exec` を契約違反にする」は、
  **契約文を足すだけなら docs pin と同じ強度**であり、本 wave が解こうとしている問題の再演。
- **純粋な案 B (事後検査だけ) は viable でない。** 壊れた段分類を再利用するため、
  分類不能を赤にすれば通常運用が止まり、無視すれば検出力ゼロになる。
- **stage matrix の所有は [T-184]**。`launch_kind → docs 節 → 期待値` の表は、値を直書きしなくても
  stage matrix の実行可能表現であり、本 wave が新規定義してはいけない。

親が裏取りして **refuted** にした所見が 1 件ある。レンズ B が「D60 が『現用 Codex 相談は launcher を
経由しない』と決めている」として移行境界を要求したが、D60 の「この launcher」は
**codex_roles の role runtime launcher** を指しており、争点の `tools/codex_worker_launch.py` ではない。
**D60 は案 A の障害にならない。**

---

## 裁定 R1 — 基本方式

**論点:** 起動値を権威と突き合わせる層をどこに置くか。
段 1 で親は A (launcher 集約) / B (事後検査) / C (宣言 + 事後照合) の 3 択としたが、
段 3 で「**排他 3 択ではなく層の組合せ**」と訂正された。純粋な B は上記のとおり除外する。

**選択肢:**

- **(a) A+ = launcher へ集約する。** `DW-O01` の雛形を `tools/codex_worker_launch.py` 経由へ置換し、
  caller から model / effort の指定権を外して段種別から docs 由来の値を導出する。
  別 worktree を表現できる manifest v2 が必須。段 7 で期待 job 集合と receipt 集合の等価も要求する。
  実装規模の概算 800〜1,300 LOC / docs 純増 400〜700 bytes。
- **(b) C = 起動口は変えず、宣言層を足す。** 親が投入前に段種別・cwd・sessions root・出力先を
  宣言し、prompt へ埋めた launch-id で rollout と exact join する。
  概算 1,000〜1,600 LOC / 800〜1,200 bytes。宣言漏れを完全に閉じようとすると exec まで
  helper が担うことになり、実質 (a) へ収束する。
- **(c) 実装しない (現状維持)。** 害は F56 で実測済み (不正 effort 値が rc=0 で通る) だが、
  前提条件が 2 件 ([T-664] 予算、[T-184] 所有) 未解決である。

**親の推奨: (a)。** 理由は、取りこぼしの本丸である段 6 fix 子 (実測 4)、段 3 の lane 同定、
壊れた段分類 (実測 3) の 3 つが、いずれも「起動時に段種別を機械キーとして持つ」ことで同時に閉じるため。
(b) は同じキーを親の自由入力に委ねるので、誤った段種別を宣言すれば検査は通る。
ただし **(a) を選んでも raw 起動は閉じない** — それは R2 で別に裁定する。

---

## 裁定 R2 — raw 起動 (雛形を通らない一回限りの呼び出し) の閉包

**論点:** どの方式でも、親が launcher / 宣言を通さず素の `codex exec` を叩けば 100% 取りこぼす。
段 2 プランはこれを「契約文で禁止する」としたが、両レンズが「それは docs pin と同じ強度」と否定した。

**選択肢:**

- **(a) 集合等価で機械的に赤くする。** 段 7 で「期待された全 job」と「receipt / 宣言の集合」の
  exact equality を要求し、欠落があれば記録・commit の前に停止する。
  未知の raw 起動そのものは見えないが、**期待 job が receipt を持たないことは赤にできる**。
- **(b) 実行面を閉じる。** `hooks/guard_bash.py` を Codex 経路へ配線し、
  sanctioned な起動形以外の `codex exec` を Bash 面で拒否する。(a) より強いが、
  hook の受理集合変更を伴い、hook 変更の契約 (`hooks/README.md`) に従う必要がある。
- **(c) 許容し、検出保証が無いことを明記する。** 契約文だけの禁止は**選択肢から除外**する
  (両レンズ一致。書いても効かないため)。

**親の推奨: (a)。** (b) は本質的に強いが、hook の受理集合を変える変更であり、
本 wave の射程を超える (別タスクとして起票するのが筋)。(a) は R1 のどちらを選んでも同じ形で載る。

---

## 裁定 R3 — 権威の時制 (いつの docs と照合するか)

**論点:** 権威行は model も effort も時間変化する (実測 7)。しかも wave が自分の land する契約を
wave 内で dogfood した実例がある ([T-181])。照合先を固定しないと、過去 wave に偽の赤が出る。

**選択肢:**

- **(a) job ごとに、起動時点の authority snapshot と digest を固定する。**
  wave 内で権威が変わっても正しく扱える。
- **(b) wave 開始時の base commit に固定し、wave 中の権威変更 (dogfood) を禁止する。**
  実装は簡単になるが、[T-181] のような「新契約の最初の適用例を自分で回す」運用ができなくなる。
- **(c) live HEAD と照合する。** 過去 wave に偽赤が出るため**不採用**。

**親の推奨: (a)。** dogfood は実在の運用であり (一次資料で確認)、禁止するコストが大きい。

---

## 裁定 R4 — [T-183] / [T-184] との所有境界

**論点:** 2 件が本 wave の外に所有されている。

- **stage matrix** (段 → 期待 model / effort の写像) は `docs/phase3.md:694` により **[T-184] の所有**。
- **起動前の model×effort capability 検査** は F56 恒久対応 (c) であり、実体化の所有は **[T-183] / [T-184]**。
  A / B / C のいずれも spawn 後の照合しか持たず、この要求を満たさない。

**選択肢:**

- **(a) [T-184] が canonical な stage matrix と起動前 policy を先に発行し、本機構はその consumer になる。**
  本 wave 由来の実装は「権威を読んで実効値と突き合わせる generic binder」だけを持つ。
- **(b) 機械表現の狭い所有だけを本機構へ移管し、policy 値は [T-184] に残す。**
  ([T-184] を待たずに着手できるが、二重所有の risk がある。)
- **(c) stage 照合をしない。** 本 wave の目的が消えるため**不採用**。

**親の推奨: (a)。** ただし [T-184] は P1 で [T-180]〜[T-183] 後という依存があるため、
これを選ぶと本機構の着手はさらに後ろへ動く。それが許容できないなら (b)。

---

## 裁定 R5 — 着手順序 ([T-664] docs 予算との関係)

**論点:** どの案でも docs 契約の純増が要るが、aggregate の残は **16 bytes** しかない。
worktree 命名規約だけでも 91 bytes 必要 (実測)。

**選択肢:**

- **(a) [T-664] で予算を捻出してから着手する。** 順序 = [T-664] → ([T-184]) → 本機構。
- **(b) code だけ先に作り、docs 契約は予算が空いてから足す。**
  その間、運用 gate は発火しない (機構はあるが誰も呼ばない期間が生じる)。
- **(c) 予算を引き上げる。** 既存裁定 ([T-127]) により**提案しない**。

**親の推奨: (a)。**

---

## どの案を選んでも満たす不変条件 (裁定不要。実装 wave への申し送り)

1. 権威 field は `turn_context.payload.model` / `.effort` **だけ**。
   `collaboration_mode.settings.*` は診断専用で、fallback にも正本にもしない (内部名も分離する)。
2. **全 `turn_context`** が同一期待値であることを要求する (最初の 1 件ではない。実測 8 が根拠)。
   欠落・複数値・途中変更はいずれも赤。
3. fail-closed は **段 7 の記録・commit 前**に置く。段 9 だけでは、誤値での資源消費・
   成果物利用・wave branch commit が既に起きている。
4. **0 件で緑にしない。** 期待 job 集合との集合等価を要求し、receipt 0 件を列挙ループで恒真にしない
   (既存 ledger は `--strict` なしでは 0 session でも rc=0)。
5. 検査は「**docs から導出した値が実 argv / 実効値と一致する**」という property に限定する。
   期待値をテストへ hardcode しない ([T-667] の実質的再提案を避けるため)。
6. 要求値と記録値を **`requested_*` / `recorded_*` と別名で持つ**。記録値を served identity の
   attest として扱わない。`model_calls=0` を「finding 0 件の観測」として集計しない (F56 恒久対応 (a)(b))。
7. 段 3 の lane は **lane keyed mapping を主、多重集合を補助不変条件**とする。
   多重集合だけでは `sol/max` と `luna/max` の入れ替えを検出できない。

## 検出力の証明に必要な負例 (実装 wave への申し送り)

正例 1 件では検出力を証明できない。最低限、次が赤になることを要求する。

- 期待 job を 1 件消す (集合等価の破れ)
- 全 receipt を消す (0 件恒真の検出)
- rollout を未知 root へ移す (母集団完全性)
- 段 3 の lane を入れ替える (多重集合では検出できない)
- 1 job だけ effort を落とす (値検査)

## scope 外として返すもの

- **served model の attest** → [T-189] (ユーザー指示で切り離し済み)
- **stage matrix の定義** → [T-184] (R4)
- **起動前の model×effort capability 検査** → F56(c)、[T-183] / [T-184] (R4)
- **docs 予算の捻出** → [T-664] (R5)
- **hook を Codex 経路へ配線する案** → R2 (b)。採るなら別タスクとして起票する

## 未確認情報の扱い

段 3 レンズ A は外部 URL (`learn.chatgpt.com`) 3 件を根拠に「session 中の model 変更」等を主張した。
**親は検証していないため、本パッケージの根拠に含めない。** ただし「`turn_context` が複数現れる」
こと自体は親の独立実測 (実測 8) で確認済みであり、不変条件 2 は外部主張に依存せず成立する。
