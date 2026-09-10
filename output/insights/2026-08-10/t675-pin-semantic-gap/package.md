# [T-675] 裁定パッケージ — whole-file SHA-256 pin は bytes しか守らない

authority: none / default_effect: no-state-change

**実装差分ゼロ。**以下は裁定へ返す推奨であって、実装ではない。
実測の一次資料は `verbatim/measurements.md` (M1〜M12)。

---

## 1. 問題 — 実測で確定した

`.claude/commands/cleanup-branches.md` は whole-file SHA-256 で pin されている。
pin が守るのは **bytes の同一性だけ**で、「この bytes が安全義務を保っているか」は見ない。

F173 では、byte 予算を捻出するために「正本は `docs/failures.md` F26。」
(他文書にしか無い運用則への唯一の到達手段) を削り、pin を同時再同期しかけた。

| 状態 | `check_docs` | `test_check_docs.py` |
|---|---|---|
| 安全文を削るだけ (M2) | rc=1、違反 1 件「whole-file SHA-256 が契約と不一致」 | 未実行 |
| 削除 + pin 3 箇所を同時再 pin (M3) | **rc=0 / 違反なし** | **357 passed / rc=0** (計算ノード `900462.nqsv`) |

**失われた義務を名指す検査はゼロ。**意味の欠落を含む bytes が「正しい bytes」として固定される。

**pin の費用は反対側にも出ている (M12、一次資料 = F26 本文)。**
F26 の運用則「1 worktree ずつ削除し、必要なら timeout を延ばす」は、
**「whole-file SHA-256 parity 契約下にあり checker 定数の同時更新を要するため未実施」**として
command へ反映されないまま「次の一手」へ登録された。その未反映のせいで bare `F26` の
到達先が非一意になり、F173 の削除を許した。**同じ pin が安全な追記を止め、危険な削除を通した。**

---

## 2. 択一

- **(a) 意味検査の機械化** — 正本ポインタ・path・ID の到達性を機械が検査する
- **(b) pin の役割を「改変検知」に限ると明記** — whole-file SHA-256 は
  「誰かが黙って bytes を変えていないこと」しか保証しないと文書側に書き下す
- **(c) 両方**
- **(d) いずれもしない** — 手順 (`DW-O16` の焦点再レビュー) と敵対監査で担う

---

## 3. 実測が決めたこと

### 3.1 (a) の形は 1 つではない。token 形は迂回でき、edge 形は迂回を殺す (M11)

段 2 プランは必須要素を `docs/failures.md` と `F26` の**別々の token** に分解していた。
段 3 レンズ A が「それは token の存在検査であって参照 edge の検査ではない」と攻撃し、
親が両形式を同時に probe 実装して 4 状態を測った。

| 状態 | token 存在形 | edge 共起形 (同一可視行) |
|---|---|---|
| (i) 現行のまま | 緑 | 緑 |
| (ii) F173 の削除 + 再 pin | — | **赤** |
| (iii) **削除したうえで `docs/failures.md` を別行へ足す** + 再 pin | **緑 (発火せず)** | **赤** |
| (iv) 「F26 (`docs/failures.md`) が正本。」へ言い換え + 再 pin | 緑 | 緑 |

- **(iii) が決定的。**token 形は 1 件も違反を出さない。**レンズ A の所見は real。**
- **(iv) が偽陽性面。**語順・助詞を変える正当な言い換えで edge 形は緑。
  **edge 形は日本語の文言を pin しない。**
- 4 状態すべてで **whole-file pin は緑**である (pin は 1 件も止めていない)。

### 3.2 (a) は新機構ではなく既存契約の欠落補修である (M6 / M10)

- `tools/check_docs.py:4104-4107` は既に、pin 済みの cleanup-branches command に対して
  「`docs/skill-self-improvement.md` への到達性がない」を検査している。
- `tools/check_docs.py:4697-4713` は `docs/archive/` の**双方向到達性 lint** を実装しており、
  `docs/archive/README.md` 自身がそれを「到達性 lint」と呼んでいる。

**「到達性は機械が守り、意味は人間が守る」は既にこの repo の実装方針である。**
`docs/skill-self-improvement.md:84`「義務本文の文言と意味の保存は lint に固定せず、
敵対監査と人間レビューで担保する」との衝突は、段 3 レンズ A が **refuted** と判定した
(D227 が禁じるのは機械化を**既存 prose の削除根拠**にすることであり、
prose を残したまま住所を補助検査する狭い読みは成立する)。

**ただし呼称は「意味検査」ではなく「住所 (address edge) の構造 lint」とすべきである。**

### 3.3 (a) は trust root にならない (レンズ A 所見 2、real)

期待値 (必須 edge の一覧) は**同じ commit で削除できる**。sha256 を 3 箇所同時に再 pin するのと
同様に、edge 契約も同時に消せる。増えるのは**レビュー時の顕著性**だけである。

- sha256 の再同期は**意味を持たない機械作業**で、byte 予算に追われた編集が自然に行う。
- edge 契約から 1 行消す差分は**自己記述的**で、「安全義務への到達契約を外した」と読める。

**(a) を「協調改変を防ぐ防壁」と書いてはならない。**正しい位置づけは
**「非協調 drift の検出と、意図の diff への顕在化」**であり、最終的な trust root は人間レビューである。

### 3.4 コストの段差 (M8 / レンズ B 所見 6)

- **a1 (edge / 必須 literal だけ)**: 合成 repo の command / Skill は実ファイルの全文逐語コピーなので、
  **baseline fixture のデータ追加は不要**。ただし**負例テストと再 pin helper の追加は必要**。
- **a2 (F 番号の到達性 / path 実在性)**: `_build_min_repo()` は `docs/failures.md` を作らない
  (`_ENUMERATED_DOCS` に含まれない。Python で直接確認)。判定 helper
  `_assert_cleanup_digest_violation` が **違反ちょうど 1 件**を assert するため、
  **既存負例テスト群が一斉に赤くなる**。fixture 拡張が必須。

### 3.5 (b) の置き場所と byte 予算 (M5 / M7 / レンズ B 所見 9)

- (a) の実装面は `tools/check_docs.py` (Python) にあり `TextLimit` の対象外。
  **F173 恒久対応の「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」は、
  この形の機械化には当たらない。**
- (b) を command 本文へ書くのは不可。command は 3959 / 4000 bytes で、
  追記型テストが 17 bytes を要求するため**実質上限 3983 = headroom 24 bytes**
  (`_assert_cleanup_digest_violation` の「違反ちょうど 1 件」assert によって創発的に強制される)。
  安全文を削って捻出すれば **F173 の再演**である。
- 段 2 プランの提案どおり、置き場所は `docs/skill-self-improvement.md` の
  「検査と commit 境界」節 (既存 2 行の精密化置換、予算内)。

### 3.6 安い代替の実効性 (レンズ B 所見 8)

| 代替 | F173 を止める力 | 判定 |
|---|---|---|
| pin 定数変更時の警告 | 警告は無視できる | **refuted** |
| 既存の予算超過メッセージ | F173 は**予算内に縮めた**ので発火しない | **refuted** |
| (b) の明記だけ | 受理集合を 1 つも変えない (M2/M3) | **refuted** |
| `DW-O16` の焦点再レビュー | **F173 を実際に捕まえたのはこれ** | **real** |

---

## 4. 推奨 (R1〜R4)

### R1 — 呼称と位置づけを先に固定する【推奨: 採用】

「意味検査の機械化」という呼称を捨て、**「正本への到達 edge の構造 lint」**とする。
効能は「非協調 drift の検出と意図の顕在化」であり、**trust root は人間レビュー**と明記する。
これは (a) を採る / 採らないに関わらず先に決めるべきである。

### R2 — pin の責務限定を明記する ((b))【推奨: 採用】

`docs/skill-self-improvement.md`「検査と commit 境界」節の既存 2 行を、
「whole-file SHA-256 pin は期待値と異なる bytes だけを検知し、義務の意味を保証しない。
他の lint も予算・dispatch 等の構造に限る」の趣旨へ精密化置換する (予算内、追加ではない)。

**ただし「(b) を実施したので F173 対策を打った」と書いてはならない** — (b) は受理集合を変えない。

### R3 — (a) を採るなら **edge 共起形の 1 件だけ**に限る【裁定を求める】

- 対象: `.claude/commands/cleanup-branches.md` の
  **`F26` と `docs/failures.md` が同一可視行に共起すること**、ただ 1 件。
- 形: 既存の command 到達性検査 (`tools/check_docs.py:4104-4107`) と同じ場所へ足す。
  **専用関数・新台帳・新 gate を作らない。**
- **落とすもの (`DW-G03` = 独立 2 例が無いため)**: F51、helper path の literal 固定
  (レンズ B: 改名で正当編集が死ぬ)、Skill 側、全 path 実在性、全 F 番号到達性 (a2)。
  これらは**2 例目が出るまで却下**する。
- 実測の裏付け: M11 (iii) で迂回を殺し、(iv) で正当な言い換えを殺さないことを確認済み。

**この項が本パッケージの主たる要裁定事項である。**

### R4 — `DW-G05` 上は backlog である【明記を求める】

certified 選択・レポート・試行台帳の**どの値も受理集合も変えない**。変わるのは AI 作業手順の
受理集合だけである。`DW-G05` に従い **must-fix ではなく backlog** と明記し、
**このためだけの単独 wave も追加 review wave も起動しない**。

ただし「次に cleanup-branches 系を触る wave へ相乗り」という先送りには**実際の再発例がある**
(M12: F26 の反映が「pin コスト」を理由に先送りされ、その未反映が F173 を生んだ)。
したがって先送りにするなら、**所有 wave・発火条件・期限を裁定で明示する**か、
`DW-O16` の焦点再レビューのレンズとして手順側で正本化する。

---

## 5. 本 wave が測っていないこと (誠実な限界)

- **land 経路・hooks・provenance では測っていない。**M3 は
  「working tree 上で `check_docs` と `test_check_docs.py` が緑」に限定される。
- `.agents/skills/cleanup-branches/SKILL.md` 側の攻撃は**実測していない**。
- edge 形の**負例テストが実際に書けるか**は、コードを読んだ静的推論までである
  (既存負例は「その file に違反が出ること」を assert する形なので書けると推定した)。
- `docs/failures.md` が将来ローテーション / archive 移動した場合の F 番号到達性は
  未成熟である (レンズ B 所見 5-2)。R3 は F 番号到達性を採らないので現時点では影響しない。
