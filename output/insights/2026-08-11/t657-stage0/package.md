# [T-657] 恒久機構 段 0 — 逐語と裁定パッケージ

対象: `docs/calibration-freeze-authority-bundle-design.md` §10 の段 0
「択一の裁定、語彙・schema・fixture の確定」。

branch: `worktree-dev-wave-t657-stage0`。
子成果物の逐語は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0/` に置いた
(段 2 プラン、段 3 敵対 2 本、段 5 実装 3 本、段 6 レビュー 2 本 + fix 2 本、変異台帳 2 走分)。

---

## 1. 本 wave が確定したこと

ユーザー裁定 (worklog エントリ 376、一次控えは 2026-08-10 の裁定 inbox §63) を設計正本へ
畳み込み、段 0 が定めるべき語彙・schema・完了判定を exact 化した。

| 項目 | 内容 |
|---|---|
| Q1 | (i) 候補 record は権威 directory の外の候補 namespace。公式 record を**包む**形にして公式 schema を変えない |
| Q2 | 上位 A・X とも人間。A は 1 file 追加、X は (E-1) により exact 3 path |
| Q3 (lockstep 部分) | 片側交代は拒否。**承認条件を Q の自己申告 `pass` で満たすことを禁じ、再計算規則を書いた** |
| Q4 | (E-1) literal 保持。source-side pin を失わない |

あわせて次を新たに定めた。

- 上位 namespace と、承認 A / pointer X / 検査 receipt Q / 裁定 profile / 候補 record の exact schema。
- 上位 digest の domain separator と原像 7 成分の順序、canonical bytes の規則。
- **Git に導入 commit を持たない実行時成果物の cutoff 規則** (v1 が「未定義」と明記していた箇所)。
  legacy catalog は X の strict ancestor で導入され、その hash を Q と A へ束縛する。
  発効後に catalog へ root を足して legacy を名乗る経路と、既存成果物の遡及拒否の**両方**を閉じた。
- 段 8 の完了判定 (先行拒否を外した隔離環境で実 entrypoint を呼び、拒否理由が対象述語へ
  到達したことを確認する。既存の世代 scope test とは変異 lane を分ける)。
- 段 0 の status 規則。

## 2. 実測で覆した前提 — 候補 record の発行経路は実在する

段 1 brief は「候補 record を権威 directory へ置く経路は存在しない」と書いたが、これは広すぎた。
`tools/issue_env_contract_activation.py` は次 serial を検証して権威 directory へ create-only で
書き、明示的に非 active と表示する CLI として**実在する**。

成立するのは**「候補だけを載せた健全な HEAD を独立に land できない」**という狭い命題である。
権威 directory の列挙は `[0-9]{8}\.json` 以外を拒否し、chain の終端 serial と state hash を
pinned head へ exact 照合するため、正しい形の後続 record を置くだけでその HEAD 全体が赤になる。
Q1 = (i) を必要にしているのはこの狭い命題の方であり、裁定自体は覆らない。
同 CLI は §9 の移行対象へ加えた (放置すると発行経路が二重化する)。

## 3. Q3 は lockstep しか裁定されていなかった

一次控え §63 の逐語は「Q3 lockstep 既定」だけで、ユーザー発話は「推奨通りで」である。
設計正本 §12 Q3 の親の推奨も lockstep だけだった。同じ Q3 が併せて問うていた
**rollback / revocation / 下位 X_f の位置**には答えが付いていない。

段 3 の敵対レンズ A は、段 2 プランが **revocation を丸ごと落としている**ことを見つけた。
失効 record の namespace・schema が無いまま上位層を作ると、失効後に

- resolver が失効 record を無視して侵害済み束を active のまま残す、または
- 失効を「解決不能」と扱って precedence 規則により**下位 authority へ fallback**し、
  上位が承認していない環境と凍結の直積を再生成する

のどちらかになる。**裁定前に失効系の固定 schema を land させない**ことを設計正本へ明記した。

## 4. 設計で塞いだ穴が実装で再現した

段 3 のレンズ B が設計段階で名指しした 2 つの穴が、段 5 の実装で**実際に再現した**。
段 6 のレビュー 2 本 (sol / luna) が独立に構成し、両方 NO-GO を出した。

| 穴 | 段 3 での指摘 | 段 5 実装での再現 |
|---|---|---|
| 検査が fixture を意味的に読まずに終われる | 「`loads_every_fixture` という node 名だけでは実 load・実行を保証しない」 | `execute_case()` を `accept` / `reject` の固定二値へ差し替えても execution 4 node が全部通った。builder は fixture 本文を捨て、実入力は実行器内の hard-code だった |
| hash pin の自己再計算 | 「manifest の entries と entries_sha256 を同時に変更すれば通る」 | 照合が「case file の実 bytes」と「manifest literal」の 2 者だけで、両方を同時に書き換えると通った |

これに加えて段 6 が新たに 4 件を見つけた。

- **public entrypoint の固定値化を誰も検出できない。** 負例 node が private 実装を直接呼んでいた
  ため、public `validate_repository()` を固定 dict へ差し替えても落ちる node が 1 つも無かった。
- **required gate の集合が自己申告。** 空配列にしても、他の blocker のおかげで status は
  `incomplete` のままなので気付かれない。
- **完了を要求する node が無い。** 整合検査の緑を段 0 完了の証明として使えてしまう。
- **production で発火済みの行を `pending` で代用していた。**

**教訓: 設計文書に「この穴を塞ぐ」と書いても、実装が別の場所で同じ穴を作る。**
段 3 の所見は段 6 のレビュー観点として明示的に再投入する価値がある。

## 5. 実行可能にした既存拒否

§11.1 の「保存しなければならない既存の拒否」6 行のうち **5 行**を、実 entrypoint へ
入力を流して陽性 (受理) と陰性 (拒否) の両方を観測する形にした。

| row | 拒否 | entrypoint | 陰性が到達する理由 |
|---|---|---|---|
| `CFAB-11.1-01` | 同一 path に別 bytes が歴史へ入る | `resolve_active_generation` | `history-mutated` |
| `CFAB-11.1-03` | 環境活性化だけ進み floor は旧世代 | `validate_protocol_against_current` | 契約 SHA-256 不一致 |
| `CFAB-11.1-04` | 活性化 record は増えたが有効 head は旧 | `validate_activation_records` | activation head serial 不一致 |
| `CFAB-11.1-05` | 世代 record はあるが承認・pointer が無い | `resolve_active_generation` | orphan 世代を権限として返さない |
| `CFAB-11.1-06` | 承認を経ていない世代が production 権限になる | `resolve_active_generation` | `pointer-approval` |

`CFAB-11.1-02` (封印時 floor と現行 floor の不一致) だけが `pending` である。

**fixture の射程は entrypoint が担う層に限る**と設計正本へ明記した。敵対レビュー B が
「合成入力が実物より甘い」と指摘したのは正しく、射程を書かずに「実 entrypoint で確認した」と
だけ書くのが過剰主張だった。上位の semantic 層は、それを担う entrypoint の行として別に持つ。

## 6. 変異 — 2 走と erratum

初回走行は **KILLED 3 / MISMATCH 5 / SURVIVED 1** だった (台帳は
`mutation-ledger-run1-erratum.json` として保存)。

- **MISMATCH 5 件は検出漏れではない。** 事前登録の期待 node が過小で、変異は予測より
  **多くの** node を落とした。特に fix で追加した実行証跡 node が M6 / M7 を独立に捕まえている。
- **SURVIVED 1 件 (M9) は等価変異だった。** 段 0 完了要求の条件が `or` の連鎖で、
  先頭の項だけを潰しても後続の項が仮面になる。条件全体を潰す実効 gate へ再照準した。

再走で **9/9 KILLED、rc=0**。

**教訓: `or` 連鎖の条件を変異させるときは、単一の項ではなく条件全体を潰す。**
単一項の変異は他の項に必ず仮面されるため、生存しても検出力の欠如を意味しない。

## 6.1 受入で出た赤の帰属 — フレーク

受入 1 走目は **8278 passed / 20 skipped / 1 failed / 680.30 秒 / rc=1** だった。
落ちたのは `orchestrator/tests/test_codex_worker_launch.py::test_check_receipt_detects_output_tampering`
で、失敗した述語は `process_group_residual` と `termination_verified`。
本 wave の差分が到達しないファイルであり、並行 session が直前に land した起動束縛の test である。

推測で片付けず、**同一 worktree で ref だけを切り替える 3 走**で帰属を実測した。

| 走 | ref | rc |
|---|---|---|
| tip 1 回目 | `48ed15b5` | 0 |
| main | `b2411e11` | 0 |
| tip 2 回目 | `48ed15b5` | 0 |

**3 走とも再現しない。** 実装差分にも main にも帰属しないフレークである。
失敗時の実行環境は `loadavg=(18.07, 4.81, 2.42)`、`PYTEST_XDIST_WORKER=gw32` で、
termination 予算は 0.05 秒だった。**負荷依存の時間予算**が疑わしい。

## 7. 段 0 は `incomplete` である

これは宣言ではなく機械的な算出結果である。閉じるには次が要る。

- ユーザー裁定 3 束 (下記 §8)。
- 他者の手番の gate 2 件 (conformance 期待出力 literal = 下位 W-a wave の親、
  下位 A・X commit topology の不適合 = 下位 family の実装 wave)。
- `pending` 5 件 (`CFAB-11.1-02` と、上位層が未実装の 4 行) の実行可能化。

---

## 8. 裁定パッケージ (ユーザーへ返す 3 束)

### 束 1 — U-A1: 下位承認の有効期間

`docs/freeze-permanent-design-s2.md` §S2-11.1 が未解決として記録し、決定権者を**ユーザー**と
明記している。上位束は下位の承認済み束を参照するため、これが決まるまで上位の参照規則を
確定できない。

- **(a) 未発効 activation window** — A から X までの間だけ期限を検査し、X 後は期限で失効させない。
  下位正本の推奨。**親の推奨もこれ。**
- (b) 発効後 lease — X 後も全 use-time consumer が再検査する。19 consumer の各利用時点に
  再検査手順が要り、変更面が大きい。

### 束 2 — Q3 の残部 (3 問)

2026-08-10 の裁定は Q3 のうち lockstep だけを確定した。

- **(i) rollback。** 祖先世代の既承認成分へ戻すとき、新しい導入 commit を要求するか、
  既存の承認をそのまま参照させるか。
  **親の推奨: 巻き戻しではなく、両成分を新しい番号で進める forward compensating generation。**
- **(ii) revocation。** 上位束の失効 record の namespace と schema、および**失効後に下位
  authority へ fallback するか**。
  **親の推奨: fallback しない (解決不能は fail-closed)。** fallback を許すと上位が承認していない
  直積が再生成される。
- **(iii) 下位 X_f の位置。** 下位 pointer の発効を上位 X の前に置くか後に置くか。
  **親の推奨: consumer 移行の後、上位 X の後。**

### 束 3 — §8 と §10 の矛盾

§8 は封印 S と副作用境界 B を先送り確定とする一方、§10 の段 0 完了判定は「各段の陽性・陰性
fixture が実体として固定される」ことを要求し、段 5 の fixture は S / B が決まらないと書けない。
親判断で例外化しない。

- **(a) 段 0 の完了判定から、先送り確定項目に依存する段 (段 5) を除外する。**
  §8-2 の「適用される裁定項目だけ」と同型。**親の推奨。**
- (b) S と B を裁定してから段 0 を閉じる。
- (c) 段 0 を `incomplete` のまま後続段へ進むことを許す
  (§10 の「未定義の段は完了と宣言できない」に抵触する)。

---

## 9. 他者の手番として記録する gate (ユーザー裁定ではない)

- **conformance 期待出力 literal** — 決定権者は `docs/freeze-permanent-design-s2.md` §S2-11.2 が
  「W-a 開始時の親。外部参照実装で導出後レビュー」と明記。
- **下位 A・X の commit topology 不適合** — expected = 別 commit (同書 §S2-1.14)、
  observed = 同一 commit 要求 (`orchestrator/campaign/s8b_ratified_freeze.py` の pairing 検証)、
  status = nonconforming。下位 family の実装 wave が正本へ合わせる。
  **これは「どちらへ寄せるか」の二択ではない** — 下位の exact 正本は凍結済み design 族であり、
  同一 commit を正本へ昇格したい場合にだけ、凍結 design を再開する別のユーザー裁定が要る。

## 10. 触っていないもの

- `orchestrator/campaign/env_contract.py` / `env_contract_activation.py` /
  `s8b_ratified_freeze.py` (`REQUIRED_CODE_IDENTITY_PATHS` と下位検証器)。
- `docs/freeze-permanent-design.md` / `docs/freeze-permanent-design-s2.md` (凍結 design 族)。
- [T-139] の凍結 (追補 A 段階 2・blob 束縛)。
- 凍結 manifest の pin。敵対レビュー B が path 検索で交差ゼロを確認した。
