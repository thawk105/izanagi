# 段 4 裁定 — [T-665] + [T-662] 起動値束縛の設計 wave

親が段 2 プランと段 3 レンズ A / B の全所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
**本 wave は実装しない (`4→7→8→9`)。** 実装差分ゼロのため変異 matrix は免除 (`DW-S04`)。
受入全走は免除しない。

## 0. 受領検査

| 子 | model | effort | rc | validator | bytes |
|---|---|---|---|---|---|
| 段 2 プラン | gpt-5.6-sol | max | 0 | OK | 29,250 |
| 段 3 レンズ A | gpt-5.6-sol | max | 0 | OK | 14,958 |
| 段 3 レンズ B | gpt-5.6-luna | max | 0 | OK | 15,265 |

段 3 の model は `DW-O01` の権威行 (sol → luna) に適合。両レンズとも判定 **NO-GO**
(レンズ A must-fix 7 件、レンズ B must-fix 8 件)。

## 1. 親が裏取りして refuted にした所見

### R-01 (refuted) — レンズ B must-fix 8 の D60 引用は誤り

レンズ B は「D60 = 現用 Codex 相談は launcher を経由しない、という既存決定」との移行境界の明示を
must-fix にした (`docs/decisions.md:2323-2328`)。**親が一次資料を読んで refuted と裁定する。**

D60 の当該文は「codex_roles は D55/D56 で全 12 role runtime blocked の休眠サブシステムであり、
現用の codex 相談 (codex exec) は**この launcher**を経由しない」である。文脈上「この launcher」は
**codex_roles の role runtime launcher** (`orchestrator/codex_roles/launcher.py`、pinned Codex +
bwrap + trusted busybox を要求する隔離実行体) を指す。D60 の主題は codex-cli の自動更新で
在庫番人テストが恒常 fail した件であり、`tools/codex_worker_launch.py` には言及していない。
レンズ B 自身も同 report 内で `orchestrator/codex_roles/launcher.py:592-600` を**別物として**引用しており、
must-fix 8 の中でのみ両者を同一視している。

→ **D60 は案 A の移行境界を作らない。** ただし must-fix 8 の後半 ([T-664] 予算を先に解決する /
[T-667] を再提案しない) は real であり、別項で採用する。

### R-02 (real、親の実測を訂正) — `turn_context` は 1 session 1 件ではない

レンズ A が実測 A の一般化過剰を指摘した。**親が独立に再測して real と裁定する。**

2026-08-08 の rollout 109 session を全走査した結果:

- `turn_context` **1 件 = 95 session、2 件 = 14 session (12.8%)**
- ただし **2 件持ちの 14 session すべてで model / effort の組は不変**だった (変化 0 件)

→ 実測 A の「1 session あたり 1 件」は撤回する。正しい主張は
**「`turn_context` は複数現れうる (実測 13%)。観測範囲では値は不変だったが、値の不変は保証されない」**。
検査は「最初の 1 件」ではなく**全 `turn_context` が同一期待値であること**を要求しなければならない
(既存 launcher `tools/codex_worker_launch.py:773-778` はこの形になっている)。

## 2. 両レンズが独立に一致した real 所見 (採用)

### R-03 (real、採用) — 「raw `codex exec` を契約違反にする」は docs 文だけの拘束

段 2 プランの A+ 採用条件 4 点目は、契約文を足すだけなら **docs pin と同じ強度**である。
これは本 wave が解こうとしている問題 (docs pin は docs しか拘束しない) の再演であり、
**単独では選択肢として成立しない**。両レンズが独立に同じ結論。

成果物影響: これを放置すると、裁定パッケージの R1 で A+ を選んだユーザーは
「起動が機械的に拘束された」と受け取るが、実際には拘束されない受理集合のまま land する。

→ **採用。** raw 起動の扱いは独立の択一 (実行面の閉包) として裁定へ返す。
「契約文だけの raw 禁止」は選択肢から**除外**する。

### R-04 (real、採用) — 純粋な案 B は現行 wave を監査できない

段 2 プランの案 B は既存 `_classify_stage()` (prompt 先頭行の regex) を再利用し
「分類不能は赤」とする。親の実測 G は 33 session 中 30 が `unclassified`。
**分類不能を赤にすれば通常運用が常時止まり、無視すれば検出力ゼロ**という二択にしかならない。
機械的 launch ID を producer 側で付ければ成立するが、その時点で B ではなく C または A である。

→ **採用。純粋な案 B は viable でない**ため、裁定の選択肢から外す。
(段 2 プランの B の LOC 見積り 600 も、壊れた classifier をそのまま使う前提でしか成立しない。)

### R-05 (real、採用、ただし scope 外へ) — F56(c) の「起動前に落とす」を三案とも満たさない

`docs/failures.md:1321` の恒久対応 (c) は「未知の reasoning 値と model×reasoning の非対応組は
**起動前に落とす**」であり、実体化の所有は [T-183] / [T-184]。
A は spawn 後の rollout 照合、B / C は事後検査であり、いずれも capability の事前検証を持たない。

→ **real。ただし本 wave の scope 外** (所有が [T-183]/[T-184])。裁定パッケージへ返す。

### R-06 (real、採用) — stage matrix の所有は [T-184]

段 2 プランの `launch_kind → docs 節 → 期待値` 表 (`s2-plan.md:13-23`) と
`tools/dev_waves/launch_contract.py` は、値を直書きしなくても **stage matrix の実行可能表現**である。
`docs/phase3.md:694` は「`DW-O01` の結線と stage 別上限値は [T-184] の所有」と明記する。

→ **採用。本 wave が stage matrix を新規定義してはならない。** 順序と所有境界を裁定へ返す。

### R-07 (real、採用) — 三案とも docs 予算に収まらず [T-664] が前提条件

現在 aggregate 25,184 / 25,200 (**残 16 bytes**)、command 9,457 / 9,500 (残 43 bytes)。
段 2 見積りは A 400〜700 / B 350〜550 / C 800〜1,200 bytes の純増。
レンズ B は「worktree 命名規約だけでも 91 bytes (裸 ASCII でも 53 bytes)」と実測し、
命名規約単独でも予算超過することを示した。

→ **採用。どの案を選んでも [T-664] が先行する。** 順序裁定として返す。

## 3. 両レンズが対立した所見 (親が裁定)

### R-08 — 権威の時制: job 起動時 snapshot か wave base 固定か

- レンズ A: **job ごとの起動時 authority snapshot** が必要。理由は、[T-181] wave が
  **自分が land する新契約を wave 内で dogfood した** (`docs/worklog.md:1987-1988` =
  「段 6 レビュー 2 本と焦点再レビュー 2 巡はすべて `reasoning=high` で起動した — 本 wave が
  land する新契約の最初の適用例 (dogfood)」)。wave 初期 base 固定では、その wave 自身が
  途中で導入した権威を表せない。
- レンズ B: **wave 開始時の base commit / snapshot で固定**し、live HEAD を過去 wave の権威に使わない。

**親の裁定: レンズ A の事実認定が real。** dogfood は実在し、一次資料で裏が取れた。
親の実測 E (「base commit 時点の権威と照合せよ」) は**この点で不十分**であり訂正する。
ただしレンズ B の案は「wave 中の権威変更を禁止する」という別の不変条件を置けば成立するため、
**非同値な設計択一**である。両方を選択肢として裁定へ返す (親推奨 = job 起動時 snapshot)。

また親の実測 E は model 行だけを見ていたが、レンズ A が effort 側も時間変化することを
`git blame` で示した (`docs/dev-wave/workers.md:48` / `:67` = `b97ad3b55` 2026-08-08 17:30 JST、
`docs/dev-wave/workers.md:24` の `DW-S05-A` high = `2cd329d58` 2026-07-24)。**実測 E を拡張する。**

### R-09 — (P2) trust root は択一材料になるか

- 段 2 プラン + レンズ A: 「trust の差は択一材料になる」(A は exact session ID と sealed rollout)。
- レンズ B: 「親の (P2) が正しい。同一 account が docs / launcher / receipt / rollout を
  書き換えられる以上、**trust root 自体は変わらない**。プランは**証拠の結合強度**と
  **trust root** を混同している」。

**親の裁定: レンズ B が正しい。** 三案とも trust root は同一 (同一 account が全 artifact を改変可能) で、
異なるのは**欺瞞コスト = 証拠の結合強度**である。したがって (P2) は次の形へ訂正して維持する。

> **(P2 訂正)** trust root は三案とも self-attest で同一であり、trust の**強さ**では択一を決められない。
> 異なるのは (i) 取りこぼし率、(ii) docs 予算、(iii) **欺瞞コスト (証拠の結合強度)** の 3 軸である。

段 2 プランの「P2 は一部誤り」という判定は**不採用**とする。

### R-10 — (P6) 段 3 の識別

- 段 2 プラン: 「多重集合は結論が誤り。`launch_kind=s03-consult-0/1` と cardinality を分離すべき」。
- レンズ B: 「多重集合は**必要だが不十分**。プランが P6 全体を誤りとしたのは過剰。
  正しい形は **lane keyed mapping + cardinality/multiset projection**」。

**親の裁定: レンズ B の定式化を採用。** (P6) は「多重集合で表現する必要がある」までは real だが、
**lane 同定を多重集合だけに委ねると sol/luna の入れ替え・retry・再投入を区別できない**。
`sol/max` と `luna/max` を入れ替えても多重集合は一致する (レンズ B の反例) 。
→ (P6) を「lane keyed mapping を主、多重集合を補助不変条件とする」へ訂正。

## 4. 親の provisional 裁定 (P1)〜(P6) の最終処置

| # | 元の主張 | 裁定 |
|---|---|---|
| P1 | 択一は A / B / C の 3 案 | **訂正**: 排他 3 択ではなく**層の組合せ**。純粋 B は viable でない (R-04)。A は B 型の wave 集合再照合を必要とし、C は B に宣言層を足したもの |
| P2 | trust では決められない、決め手は取りこぼし率と予算 | **維持 + 訂正** (R-09): 第 3 軸「欺瞞コスト = 証拠の結合強度」を追加 |
| P3 | A は起動口を 1 本にするので構造的に閉じる | **誤り** (両レンズ一致): hook は codex に未配線 (`hooks/guard_bash.py` に codex の出現 0)、現 manifest は単一 repo root 要求 (`tools/codex_worker_launch.py:1480-1484`) で段 6 fix と両立しない |
| P4 | 予算残 16 bytes は純増を許さず [T-664] が前提 | **維持** (R-07) |
| P5 | [T-662] と [T-665] は同一機構で同時に閉じる | **訂正**: 同じ rollout field を読む点は共通だが、model の権威は `DW-O01`、effort の権威は worker 節に分散し、CLI flag も別 (`-m` / `-c model_reasoning_effort`)。F56 は model ごとに effort 受理集合が違うことを実測済み。**必要なのは共通観測器 + 同一 job の model×effort pair 検査** |
| P6 | 段→期待多重集合で表現する | **訂正** (R-10): lane keyed mapping を主、多重集合を補助へ |

## 5. scope の確定

**本 wave の scope (実装しない、設計択一を返すのみ):**
上記 R-01〜R-10 の裁定と、下記 R1〜R5 の裁定パッケージ。

**scope 外 (裁定パッケージで所有を明示して返す):**

- served model の attest → [T-189] (ユーザー指示で切り離し済み)
- stage matrix の定義 → [T-184] (R-06)
- 起動前の model×effort capability 検査 → F56(c)、[T-183] / [T-184] (R-05)
- docs 予算の捻出 → [T-664] (R-07)

**再提案しない (見送り済み裁定):**

- [T-667] docs pin の対象拡大 — 段 2 プランは `DW-S05-A` の literal pin 追加を明示的に避けており、
  再提案には当たらない (レンズ A が確認)。ただし**新規テストが `S05=high` を hardcode すれば
  実質的な再提案になる**ため、検査は「docs から導出した値が argv と一致する」という property に
  限定する、という不変条件を裁定パッケージへ明記する。
- [T-658] 受領証の全書込み口配線 — 案 C の汎用 hash chain / seal / 全 `.done` 配線のうち、
  model/effort の受理集合を変えない部分は T-658 型の防御的 hardening にあたる。削る。

## 6. 不変条件へ格上げ (裁定に載せない)

両レンズが「これは択一ではなく正しさ不変条件」と指摘したものを親が確認し、格上げする。
どの案を採っても満たさなければならない。

1. **権威 field は `turn_context.payload.model` / `.effort` だけ**。
   `collaboration_mode.settings.*` は診断専用で、fallback にも正本にもしない (内部名も分離する)。
2. **全 `turn_context` が同一期待値であること**を要求する (最初の 1 件ではない)。
   欠落・複数値・途中変更はいずれも赤 (R-02 の実測が根拠)。
3. **fail-closed は段 7 の記録・commit 前**に置く。段 9 だけでは、誤値での資源消費・成果物利用・
   wave branch commit が既に起きている。
4. **0 件で緑にしない**。期待 job 集合との集合等価を要求し、receipt 0 件を列挙ループで恒真にしない。
   (既存 ledger は `--strict` なしでは 0 session でも rc=0 = `tools/codex_worker_ledger.py:1096-1099`。)
5. **検査は「docs から導出した値が実 argv / 実効値と一致する」property に限定する**。
   期待値を test へ hardcode しない ([T-667] の実質的再提案を避けるため)。
6. **要求値と記録値を別名で持つ** (`requested_*` / `recorded_*`)。記録値を served identity の
   attest として扱わない。`model_calls=0` を「finding 0 件の観測」として集計しない (F56 恒久対応 (a)(b))。

## 7. 検出力の証明に必要な負例 (実装 wave への申し送り)

正例 1 件だけでは検出力を証明できない。最低限、次の負例が赤になることを要求する。

- 期待 job を 1 件消す (集合等価の破れ)
- 全 receipt を消す (0 件恒真の検出)
- rollout を未知 root へ移す (母集団完全性)
- 段 3 の lane を入れ替える (`sol/max` ↔ `luna/max`、多重集合では検出できない)
- 1 job だけ effort を落とす (値検査)

## 8. 未確認情報の扱い (信頼境界)

レンズ A は `learn.chatgpt.com` の外部 URL 3 件を根拠に「`/model` による session 中の model 変更」
「App Server の turn ごと override」「subagent の spawn 値 override」を主張した。
**親はこれらを検証していない (外部データであり一次資料ではない)。**
ただし親の独立実測 (R-02) で「`turn_context` が複数現れる」こと自体は確認できているため、
**結論 (全 `turn_context` を検査する) は外部主張に依存せず成立する**。
外部 URL の主張は裁定パッケージに根拠として載せない。
