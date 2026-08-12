# 裁定パッケージ — [T-139] land 2 session 4 (R1〜R5)

正本。wave `dev-wave-t139-manifest-land2-s4` が段 4 で確定させた、ユーザー手番の設計択一 5 件。

**前提:** 2026-08-12 第 2 束の Q4 は「投入の実務経路 + 解除 decision + 束縛検査だけを
1 session・同一 land で組む」と裁定した。本 wave はそれを実行しようとして、
**裁定時点で未見だった事実 3 件** (README の N1〜N3) により実装しないと判断し、
`DW-S04` の定めどおり親が不採用にせず再裁定へ戻す。

---

## R1 — `a12` を誰がいつ実装・実走するか (最上流)

**決めること.** Q4 の「投入の実務経路」に `a12` の producer・独立 verifier・実 pass artifact まで
含むか。

**事実.**

- `a12` は **pilot 1 本目の投入より前に完走**を要求し、未完了なら `design_not_feasible`
  (追補 A `a12` 逐語)。実装も実行結果も **0 件**。
- そのため `submit_pilot` の受理集合は空になり、**束縛検査が恒真**になる (README の N1)。
  段 2・段 3 の 3 子が独立にここへ到達した。
- **合格条件は承認済み文書で完全に固定済み** — 固定入力は実在し digest 一致
  (`755cfa7e…`)、`α₁ = 0.025`、B = 1,000,000 × 60 セル、seed、counter-mode PRNG、
  判定式 `U_{Jk} ≤ α₁`。つまり「中身を見ずに凍結」ではない。
- 規模は約 60 億 draw。**それ自体が計算ノード job 1 本分**である。

**選択肢.**

- **(a) `a12` を独立の 1 wave として先に立てる (親推奨)。**
  理由: 投入経路と同じ session に入れると両方が半端になる。`a12` は仕様が完全に凍結され
  入力も実在するので、単独 wave として最も着手しやすい。完走すれば正例が構成可能になり、
  R3 の恒真問題が自然に解消する。
- (b) Q4 の「投入の実務経路」に含めると解釈し、次 session で両方を組む。
  → 親は推奨しない。計算 job と投入機構は所有も検証手段も別である。
- (c) `a12` を gate の拒否条件としてだけ扱い、恒真な束縛検査を先に land する。
  → 親は反対 (R3 を参照)。

---

## R2 — `a09` の canonical serialization (§10 閉包 4) を採るか

**決めること.** driver が canonical schedule digest を名乗るために、`record-items-v2.md` §10 の
未承認閉包 第 4 番 (schedule 表の canonical TSV・header・157 行・並び順) を採用するか。

**事実.**

- 追補 A `a09` が凍結しているのは**導出規則まで** (逐語 seed、`key(j, w, p)` の式、
  preimage の byte grammar、tie-break)。**serialization は定めていない。**
- serialization は §10 が「承認済み文書から一意には導けない選択」として明示した閉包 8 件の 1 つ。
- 採用すれば **Q1/Q2 の「機構を新設しない」と衝突する**。採用しなければ、同じ意味的 schedule から
  実装依存の異なる digest が出て、intent・binding・collector record の hash が実装依存になる。

**選択肢.**

- **(a) 本 wave では判断せず、R1 の `a12` wave で `a09` の意味的 generator だけを先に作り、
  serialization は `operational-only` と明記して canonical `schedule_sha256` を名乗らない (親推奨)。**
  理由: 意味的な導出規則の実装は承認済み仕様の実装であって新設ではない (段 3 レンズ A が
  この一般化を refuted 側で追認)。名乗らなければ Q1/Q2 に触れない。
- (b) 閉包 4 を canonical として採用する新 decision を起こす。
  → Q1/Q2 の見送りと正面から衝突する。採るならその衝突を明示的に裁定する必要がある。
- (c) driver を作らない。
  → Q4 の scope が空になる。

---

## R3 — 恒真な防壁を land してよいか

**決めること.** 受理集合が空の gate を、正例が作れるようになるまで先に land することを認めるか。

**事実.** 現状では次の 4 実装が観測上区別できない — 正しい gate / `a09`・`a12` 不在で拒否する
gate / binding を一度も検査せず常に拒否する実装 / どの入力も読まず `raise` する実装。
負例テストは検査が発火した証拠にならない。

**選択肢.**

- **(a) 認めない (親推奨)。** 理由: D292 の理由欄が禁じた「未実装・未検証の gate の合格条件を
  凍結し、実装が条件に合わないとき**条件側を緩める圧力**が生まれる」形そのものである。
  絶対規律 2 (正しさゲートを緩める変異を許さない) と規律 3 (正しさシグナルを後付けにしない) の面。
- (b) 認める (「常時拒否は fail-closed なので安全」と読む)。
  → 段 3 レンズ B の指摘: 常時拒否そのものは直ちに fail-open ではないが、
  正しさ防壁として land すると**後続で正例を通すために gate を緩める圧力だけが残る**。

---

## R4 — D308 の同一 land を機械が執行するか

**決めること.** 「認可の解禁と束縛検査は同一 land に含める」(D308) を執行する機械検査を作るか。

**事実.** 現状は規律であって検査が無い。canonical HEAD に release decision があれば、
後から別 commit・dirty worktree の実装で gate を動かせる (段 3 レンズ B の B7)。

**選択肢.**

- **(a) [T-508] の機械化移管枠で扱う (親推奨)。** 2026-08-12 第 2 束の Q5 が
  「段 8 候補は T-508 裁定 ((b) 機械検査・ツール化への移管) を先に試す」と定めており、routing 先が既にある。
- (b) 解除 decision を land する wave が同時に作る。
  → その wave の scope をさらに広げる。

---

## R5 — `submission.py:150` の単発 `os.write` (T-126 側の既存欠陥)

**決めること.** `orchestrator/qualification/submission.py` の `_durable_json` が単発 `os.write` で
short-write 検査も read-back も持たない件を、どのタスクで直すか。

**事実.** 段 3 レンズ B が発見。T-126 の durable submission intent の書き込み経路であり、
**本 wave の scope 外** (T-139 は 1 byte も触っていない)。

**選択肢.**

- **(a) 別タスクとして起票する (親推奨)。** T-126 の所有 wave が直す。
- (b) T-139 の投入経路を作る wave が、pattern を写す際に同時に直す。
  → 他 wave の所有物への横断変更になる。

---

## 本 wave が land したもの

実装差分 0。session 1・2 の実装 (`erratum.py` / `blobref.py` / `approval_payload.py` /
`addendum_envelope.py` / Git trust root 部分集合 + test 3 file)、本 session の記録と本パッケージ、
先行 session の未 land fragment 7 件。

**解除 decision・`submit_pilot`・PBS driver・collector・束縛検査は land していない。**
両方 land しないため、D308 が警告する「止める文が canonical に無く、通す gate も未実装」の
窓は開いていない。**pilot は依然投入できない** (認可は 2026-08-12 第 1 束で解除されたが、
D292 が要求する canonical decision は無く、投入機構も存在しない)。
