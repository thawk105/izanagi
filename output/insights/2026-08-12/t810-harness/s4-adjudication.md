# 段 4 裁定 — [T-810] 測定装置 slice 1

段 3 の 2 レンズはともに **NO-GO**。レンズ A = blocker 8 + must-fix 3、レンズ B = blocker 7 +
8 群対応表 (○1 / △7 / 手続きは ×) + 変異 40 件。**両者は独立に同じ中心へ収束した** —
**canonical JSON の digest は「値」を凍結するが「手続き」(区間式・slope gate・状態遷移・実行の
仲介) を拘束しない。**これを直さない限り、同じ事前登録を指したまま τ の値・判定・受理集合を
変更できる。中心所見は real と裁定する。

## 1. 親の provisional 裁定の帰趨

### (P1) `.claude/` を走査から除く → **撤回する (refuted)**

レンズ A が実在 path で反証した。main checkout から見ると `.claude/worktrees/<別 wave>/` の下に
`output/s8b-freeze/holdout_freeze.json`、`output/campaigns/.../runs/wal.jsonl`、
`orchestrator/campaign/env_contract_activations/00000001.json` が**実在する**。
親 brief の「禁止領域はいずれも `output/` と `orchestrator/` の下」は checkout ごとには真だが、
**除外は他 checkout のそれらを丸ごと検出外にする。**

さらにレンズ A は親の実測の一般化そのものを崩した — **158,011 file / 185 秒は main checkout の
topology の値**であり、入れ子 worktree を持たない standalone checkout では成り立たない
(本 worktree の実測 = 11,875 file / 365 MB)。**除外の費用根拠は、除外が不要な topology の値だった。**

**裁定: 除外しない。走査面を「入れ子 worktree を含まない静穏な専用 checkout」へ束縛する。**

- validator は `repo_root` を caller の任意文字列として受けない。**承認済みの git identity
  (realpath・gitdir・common-dir) と一致することを要求**し、不一致は非 0。
- その checkout の内側に `.claude/worktrees/` が存在しないことを**機械検査**する
  (存在したら非 0。「除外」ではなく「入れ子がないことの証明」である)。
- gitignore は一切参照せず filesystem を歩く。ignored **directory の中の入れ子ファイルまで**歩く。
- 加えて **canonical な禁止領域を絶対 path の inventory として別途取る** (§6.3 の第 2 項)。

### (P2) 検出は `DurableRootPolicy` に依存しない → **維持 (両レンズ賛成)**

ただしレンズ A の条件を採る。**(d) を 2 つに割る。**

- **d1 = 協調的 routing policy の注入** — 本 wave。`DurableRootPolicy` を使う。
- **d2 = 測定ノード上の repo 不在 (唯一の構造的防壁)** — **後続 wave (PBS wrapper)。**
  本 wave は d2 を実装しない。**「(d) を実装した」と書かない。**

### (P3) policy ディレクトリへ置き digest を pin → **配置は維持、凍結方式は強化**

両レンズが「test だけの pin では runtime 保証にならない」「artifact・loader・test の 3 コピーは
同一 commit で同時更新でき、事後変更を止めない」と指摘した。real。

**裁定: loader は外部 authority を必須引数として要求する。**
`load_t810_preregistration(path, *, approval_receipt)` とし、`approval_receipt` が持つ
`{artifact_sha256, approval_id, schema_version}` の digest と実 bytes の digest が一致しなければ
拒否する。**artifact 自身から expected を導出する経路を API から持たない** (恒真化の遮断)。
実 receipt は第 1 段承認時に人間が発行する。本 wave は API と fixture receipt で閉じる。

## 2. 所見の裁定表

| # | 出典 | 所見 | 裁定 | 本 wave での扱い |
|---|---|---|---|---|
| 1 | A-1 / B-5 | `.claude/` 除外は禁止領域を落とす | **real** | 採用。専用静穏 checkout への束縛へ置換 (上記 P1) |
| 2 | A-2 | (d) を半分だけ実装して全部の名前を付けている | **real** | 採用。d1 / d2 に分割、d2 は後続と明記 |
| 3 | A-3 | digest pin が同一 trust domain の 3 コピー | **real** | 採用。承認 receipt 必須引数へ (上記 P3) |
| 4 | A-4 | 凍結 closure 不足 (§3.2 seed・§7 下流表・preflight・`run_authorized`) | **real** | 採用。**§9.1 item 2 の列挙の上位集合**を凍結し、全群を projection へ露出 |
| 5 | A-5 | `repo_root` が authority 非束縛、空集合で恒真合格 | **real** | 採用。identity 束縛 + 非空性不変条件 + 正例 test |
| 6 | A-6 | 5 終端状態への写像が排他でない | **real** | 採用。join 規則を確定 (下記 §3) |
| 7 | A-7 / B-6 | slice 1 の合格が実行許可と誤読されうる | **real** | 採用。dormant seal 型 (下記 §4) |
| 8 | A-8 / B-4 | release token 束縛が自己申告 boolean | **real** | **部分採用**。lineage の schema は凍結、edge の強制は (a) へ |
| 9 | B-1 | digest が手続きを凍結していない | **real・最重要** | 採用。**参照 evaluator + golden vector** を作る (下記 §5) |
| 10 | B-3 | `terminal_reduced` の effective N が estimator に非束縛 | **real** | 採用。状態ごとに `effective_node_count` を束縛し ν1・ν2 を導出 |
| 11 | B-2 | assurance 再現条件が不完全 | **real** | 採用 (縮約形)。下記 §6 |
| 12 | A-9 | 環境契約 hash が 63 桁 (親も独立に実測) | **real** | 採用。64 桁 `…4187ad1c` へ訂正、桁数と exact 値を test で殺す |
| 13 | A-10 | `.git` 除外を補う semantic snapshot が不足 | **real** | 採用。gitdir/common-dir identity・全 ref・packed-refs・config を閉じる |
| 14 | A-11 | pass witness と scan race が未定義 | **real** | 採用。dev/inode/ctime_ns 追加、receipt は create-only + attempt nonce 束縛 |
| 15 | A-B7 / B-7 | 未記録 exec の不存在は証明できない | **real だが本 slice で閉じない** | **能力限界として宣言**。artifact の `/limitations` と land 報告へ明記 |

### 不採用にした提案

- **レンズ B「NumPy/SciPy の wheel hash・raw 配列 hash まで凍結する」** — 不採用。
  費用に対して得るものが小さく、版固定の連鎖を新設する。代わりに §6 の fail-closed を採る
  (研究最優先・プロトタイプ基準)。
- **レンズ A「d2 (repo 不在) を本 wave で閉じる」** — scope 外。後続 wave。
  ただし**「(d) 実装済み」と書かない**ことで誤読を塞ぐ。
- **レンズ A「全面走査を維持し、静穏な専用 checkout の機械化は scope に足さない」** —
  半分採用。専用 checkout への**束縛検査**は本 wave に入れる (安いため)。checkout を用意する
  運用手順自体は後続。

## 3. 終端状態 join 規則 (A-6 の確定形)

証拠の完全性を先に評価する。**caller の claimed state を分類に使わない。**

1. coordinator receipt と全 node receipt が**完全に読めない / 欠損 / 矛盾**する
   → `incomplete_after_start` (保守側。retry 不可)。
2. いずれかの slot に `measurement_start` が実在する → `incomplete_after_start`。
3. release event が実在し、どの slot にも `measurement_start` が無い
   → `post_release_pre_measurement_invalid`。
4. **receipt の完全性が検証できた上で** release event が不在 → `pre_release_invalid`。
5. claimed `valid` / `terminal_reduced` の post validator が失敗 → `incomplete_after_start` へ強制。

**「event 不在」は receipt 完全性が検証できた場合にだけ使える。**欠損を不在と読んで retry 可の
`pre_release_invalid` へ倒す経路を塞ぐ (これが A-6 の実害 = 2 回目 attempt で性能値を選び直せる)。

## 4. dormant seal (A-7 / B-6 の確定形)

- 本 slice の結果型は `Slice1ValidationResult` とし、**launch / approval の capability を返さない。**
- `run_authorized = false` を projection へ露出し、実行を開始する API は
  `T810NotAuthorizedError` を送出する。**通る正例は無い** (gate 禁止は署名で書く。DW-S04)。
- artifact に `/authorization/stage1_satisfied = false`、
  `/authorization/missing_components = ["a","b","c","d2","f","g"]` を持たせる。
- **正例:** `validate_t810()` は rc=0 を返せるが、その戻り値からは投入経路へ到達できない
  (型に launch method が無い)。これが「通る正例」である。

## 5. 手続きの凍結 (B-1 の確定形) — 本裁定の中心

**式を文字列で置くだけでは凍結にならない。**次を作る。

- `orchestrator/campaign/t810_estimator_v1.py` — 参照実装。`eval()` を使わない。
  - 区間: `τ̂` / `τ_L` / `τ_U` (§1.1 の単一式。`max(0, …)`、除算位置、F 分位の 0.05 / 0.95 の
    取り違えを golden で殺す)。
  - slope gate: node ごとの OLS 傾き `β̂_i` と `se_i`、`S_β`、`V_β`、`S_β > 2·V_β` の**狭義**不等号。
  - 判定: §5.3 の順序付き first-match、§5.4 の順序付き終端 FSM。
- **golden vector を artifact へ凍結する。**入力 (対数 throughput 行列) → 出力
  (`τ̂`, `τ_L`, `τ_U`, gate 発火, 結論 code) の組を、
  **N=13 と reduced N=12 の双方**、および**境界 (等号・切捨て `τ_U=0`)** について持つ。
  評価器の version id `node_random_round_fixed_f_interval_v1` を artifact に束縛する。
- 将来の別実装は golden を再現しない限り受理されない。**これが「同じ digest で別実装」を塞ぐ唯一の形。**

## 6. assurance 再現の扱い (B-2 の縮約形)

artifact には §4.2 の再現条件 (NumPy 2.2.6 / `Generator(PCG64(810))` / 40 万 draw / 生成順序
`MS_A`→`MS_E` / 当選数 338,491・323,211 / σ_e=0.012479) を凍結する。**本 wave では再走しない。**

**再現を試みて不一致だった場合、値を更新してはならない。**`reference_not_reproduced` として
fail-closed で停止する。この規則自体を artifact の field として凍結する。

## 7. plan v2 の scope (確定)

**作る。**

| 所有 | 成果物 |
|---|---|
| 子 A | `tools/pegasus/policies/t810_prereg_v1.json` (凍結 artifact、64 桁 hash、N=13・R=10、golden vector、§3.2・§7 を含む上位集合、`/authorization`、`/limitations`) |
| 子 A | `tools/pegasus/policies/registry_v1.json` への登録 (閉集合) |
| 子 A | `orchestrator/campaign/t810_preregistration.py` (canonical bytes、承認 receipt 必須の loader、深い immutable projection、状態別 effective N、presence 展開) |
| 子 A | `orchestrator/campaign/t810_estimator_v1.py` (参照 evaluator。区間・slope gate・判定 FSM) |
| 子 A | `orchestrator/tests/test_t810_preregistration.py`、`orchestrator/tests/test_t810_estimator_v1.py` |
| 子 B | `orchestrator/campaign/t810_validator.py` (§6.3 の 5 検査、checkout identity 束縛、非空性、git semantic closure、scan race、join 規則、dormant seal) |
| 子 B | `tools/pegasus/validate_t810.py` (pre / post の単一 CLI) |
| 子 B | `orchestrator/tests/test_t810_validator.py` |

**作らない (後続 wave。裁定パッケージで返す)。**

(a) barrier / release / cancel marker / 開始ばらつき / 完了 verifier、
(b) T-810 専用 PBS wrapper、**(c) runner 自身の argv を解釈する policy module**
(レンズ B の「単独 mediation が無い限り receipt-only」を容れ、**(b) と同じ wave へ送る**。
ただし**凍結された canonical argv と、実行 receipt との照合は §6.3 の検査として 子 B に残す**)、
(d2) 測定ノード上の repo 不在、(f) 並走ガード機械化、(g) 予算 admission。

## 8. ユーザーへ返す裁定パッケージ候補

1. **測定窓の静穏要件。**完全な非流入検出は、coordinator が到達できる全 checkout の静穏を要する。
   T-810 の測定窓の間、**他の dev-wave の書き込みを止める**運用を受け入れるか、
   canonical 禁止領域の churn を別扱いにするか。
2. **§9.1 item 2 の列挙の訂正。**protocol 自身が §3.2 (投入順 seed) と §7 (下流許可表) を
   凍結列挙から落としている。本 wave は上位集合を凍結したが、**protocol 本文を訂正するか**。
3. **digest authority の発行形。**第 1 段承認 receipt に `{artifact_sha256, approval_id}` を封印し、
   第 2 段が同一 authority を消費する方式でよいか。
4. **実行 mediation の完了条件。**未記録 exec の不存在は (b) の単一 mediation 点まで閉じない。
   §9.1 第 1 段の充足判定に、この能力限界をどう書くか。

## 9. 変異事前登録 (DW-M01)

実装後に走らせる。各変異は「同じ入力を拒否する層が前後に無い」ことを実装後にコードで確認し、
確認できないものは登録から外して実効 gate へ再照準する。

| # | 位置 | 変異 | 期待 |
|---:|---|---|---|
| M1 | validator の filesystem 走査 | **wave 前の実コードの形**へ差し替える — `git ls-files --others --exclude-standard` (`orchestrator/campaign/s8b_ratified_freeze.py:2417` ほかに実在する逐語) を列挙源にする | ignored 未追跡の検出 test が KILLED |
| M2 | 同上 | ignored **directory** を走査打ち切りにする (git 既定と同じ畳み方) | 入れ子 ignored file の test が KILLED |
| M3 | loader の digest 照合 | 再直列化後の bytes を hash する (raw bytes でなく) | 1 byte 改竄 test が KILLED |
| M4 | loader の承認 receipt | `approval_receipt` を無視し artifact 自身の digest を expected にする | 恒真化 test が KILLED |
| M5 | 区間 evaluator | `F_{0.05}` と `F_{0.95}` を入れ替える | golden vector が KILLED |
| M6 | 区間 evaluator | `max(0, …)` の切捨てを外す | 境界 golden が KILLED |
| M7 | slope gate | `>` を `>=` にする | 境界 golden が KILLED |
| M8 | 状態別 effective N | `terminal_reduced` でも N=13 の自由度を使う | reduced golden が KILLED |
| M9 | 終端 join | claimed state を優先し `measurement_start` 実在を無視する | join test が KILLED |
| M10 | 終端 join | receipt 欠損を「event 不在」と読み `pre_release_invalid` へ倒す | 保守側 join test が KILLED |
| M11 | checkout 束縛 | `repo_root` の identity 照合を外す (caller の文字列を信じる) | 恒真合格 test が KILLED |
| M12 | 非空性 | member 0 件・slot 0 件で「全一致」と判定する | 空集合恒真 test が KILLED |
| M13 | dormant seal | `run_authorized` を無視し launch 経路を露出する | seal test が KILLED |
| M14 | 禁止領域 inventory | `env_contract_activations/` を inventory から落とす | 領域別 test が KILLED |
| M15 | pass receipt | 既存 receipt の存在で合格に倒す (今回生成でなくてよい) | witness test が KILLED |
| M16 (正例) | 走査面 | 正規の静穏 checkout と正規の attempt を与える | **SURVIVED** (過剰拒否が無いことの正例) |

**M1 は memory の規律に従う** — 検査を新設する wave で、禁止したい形を wave 前の実コードが
使っていた場合、その逐語と同型の変異を必ず 1 件登録する。
