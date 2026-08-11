# 段 1 brief — [T-793] 公表層の機械執行 (4 必須要件)

- wave: `dev-wave-t793-pubcore-impl` / 2026-08-11
- branch: `worktree-dev-wave-t793-pubcore-impl`、base tip `974207ae` (= local main)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl`
- job artifact: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t793-pubcore-impl/`
- `F_p` = `b13b7ea840ad51199f40b3a534c9d1cdb422af2e` (D291 の fold commit。段 1 で実測再同定済み)
- 受入・実測環境: Pegasus。計算ノードへ出すのは受入全走のみ。所在は worklog、機体固有は環境 runbook

## 確定裁定 (実装の授権)

| ID | 内容 |
|---|---|
| C-5 (a) | 公表層の機械執行を既存 producer 実装 wave 系列へ足す |
| Q1 (a) | `b03` 縮小 + gate 喪失を受容。**条件** = 本 wave が「source 側の本走 gate 新設 (旧 `b03` の投入前 admission の復元)」を必須要件に含めて実装する |
| Q3 (b) | 追補 P の凍結は本 wave が公表台帳の実体を確定した後。pilot もそれまで投入しない |
| D291 | 承認 payload。`exact_closure` は allowlist、`document_relations` は節全体が exact 一致対象 |
| D292 | pilot / 本走の投入禁止を解除できるのは canonical decision だけ |
| RP-4 (a) | land 2 は `b03` consumer を 1 行も書かず §S7 #7 を本 wave へ委譲 |

## scope (成果物影響つき — DW-G05)

新規 package `orchestrator/publication/` に置く (land 2 の `orchestrator/preregistration/` と file 非重複)。

| # | 実装するもの | 実装しない場合に成果物のどの値が動くか |
|---|---|---|
| 1 | **(i) 根 → 唯一の台帳実体の束縛。** 固定 literal `family_root` + `ledger_kind` から台帳 path を決定的に導出し、caller の引数・受領証申告・環境変数を入力にしない | 未実装なら**空台帳へ差し替えて同じ ordinal を取り直せる**。試行台帳の公表 entry が一意でなくなり、公表表の proof chain が「予約済み」と偽れる |
| 2 | **(i-b) 台帳 schema と create-only 検査。** `(family_root, kind, ordinal)` の一意性、append-only、ordinal 非解放、公表 entry 空間と primary 空間の互いに素性 | 未実装なら失敗した試行が ordinal を解放し、同一 dataset へ 2 度目の公表表を出せる (pubcore §8.2 / §8.3 が塞げない) |
| 3 | **(ii) 追補の未確定 marker gate。** `__UNRESOLVED_APPROVAL_FOLD_COMMIT__` / `__UNRESOLVED__` を含む文書を承認対象・fold 対象にできなくする | 未実装なら `core_ref.commit` が未解決のままの追補 P を承認 payload へ書け、**resolver が永続的に解決失敗する文書を「承認済み」と台帳が記録する** |
| 4 | **(iii) source 側の本走 gate。** 旧 `b03` (v)「予約一意性が成立しないまま本走を投入してはならない」を復元する admission 述語 | 未実装なら Q1 (a) の裁定条件が未履行のまま。source 本走が公表側の予約一意性を確認せず投入でき、公表 study の事前登録性が事後に失われる |
| 5 | **(iv) `F_p` payload を trust root とする承認 role resolver + report 層。** D291 の payload を `F_p` の `docs/decisions.md` から読み、role 集合・三つ組・`document_relations` 節全体・承認値集合・閉包条件を exact 照合して role → 承認状態を返す。report は `authority: none` の文書に対し「canonical decision による承認済み」を機械的に示す | 未実装なら承認 2 文書は fold 後も `authority: none` のままで、**decision を読まない reader が未承認と誤判定する**。材料レポートの承認欄が自己申告になる |
| 6 | **(iv-b) `p01`〜`p03` の exact-key 検査** (既存検査は `a01`〜`a13` 専用) | 未実装なら追補 P が閉集合外の field を設定でき、pubcore §9 / §10.4 変異 9 が塞げない |

**scope 外 (書かない):** `resolve_effective_preregistration` / `PreregBinding` / 受領証 writer /
source semantic validator / conformance vectors (すべて land 2 session 2 の所有)、
`submit_pilot` / `submit_main` の本体、PBS preflight / driver / collector、
公表 validator の統計計算本体 (`T_k` / Holm / 同時下限)、公表表 renderer、追補 P の凍結、
**予約 entry の実発行** ((P3) を見よ)。

## 不変条件 (破ったら赤)

1. **絶対規律 2/3 を緩めない。** gate を通すために受理集合・期待値を緩めない
2. **本 wave の gate はすべて deny を増やす方向にのみ働く。D292 の投入禁止を解除しない。**
   実装完了は解除条件ではない。gate が緑でも `pilot_submission` / `main_submission` は `forbidden` のまま
3. **D291 が承認した 2 文書の bytes を 1 bit も変えない** (`publication-core-v2.md` / `addendum-b-v2.md`)。
   `authority: none` を書き換えて発効を表現しない (D291 却下選択肢)
4. **manifest / 文書側の自己申告を単独の trust root にしない。** 必ず `F_p` の `docs/decisions.md` の
   D291 payload と exact 照合する
5. **`output/registry/t139-alpha-reservations.jsonl` (143 bytes) を追記も編集もしない。** D282 が bytes を pin する
6. **恒真な gate を作らない。** 各 gate に「通る正例 1 つ」を必ず添える (`DW-S04`)
7. `document_relations` は**節全体**が照合対象。括弧内に挙がっていない field も対象、key の追加も削除も解決失敗
8. 実装面は Codex `role=author` が書く。親は brief・裁定・統合 commit・変異・全走・記録のみ

## 実測済みの前提 (段 1 で測った) — **承認済み文書の記述を覆す新事実 2 件**

| # | 実測 |
|---|---|
| 1 | `F_p` = `b13b7ea8`。`git show b13b7ea8 -- docs/decisions.md` が追加する `## D` 見出しは **D291 の 1 件のみ**。local main `974207ae` はその子孫 |
| 2 | **[前提の反証] pubcore v2 §8.1 の「`family_root` が primary 系列と同じ commit である」は、land 済み台帳に照らして偽である。** 公表側 `family_root` = `88d68f91…` (D234 限定例外の fold)、primary 側の実台帳 `output/registry/t139-alpha-reservations.jsonl` の `family_root` = **`dce4ae4f…`** (事前登録承認の fold)。両者は別 commit。§8.1 が引き出す結論 (2 系列の互いに素性) は**強まる**方向なので blocker ではないが、**実装は §8.1 の同一性主張を互いに素性の根拠にしてはならない**。文書は承認 bytes なので編集しない (不変条件 3) |
| 3 | **[前提の反証候補] 承認済み台帳の `kind` は `alpha_reservation`、`schema_version` は `t139-alpha-reservation/v1`** であり、pubcore §8.1 が公表側に課す `ledger_kind = individual_publication` とは値空間が異なる。互いに素性は (root, kind) の 2 軸で成立する |
| 4 | 未確定 marker は実在する — `addendum-p-draft.md:36` = `__UNRESOLVED_APPROVAL_FOLD_COMMIT__`、`:37` = `__UNRESOLVED__` (DW-O13 充足) |
| 5 | main 側に公表層コードは 0 行。`orchestrator/preregistration/` は `addendum_envelope.py` (a01〜a13 専用) / `blobref.py` / `erratum.py` / `__init__.py` の 4 file のみ。`approval_payload.py` は **land 2 branch のみ**で main に無く、その `DECISION_KIND` は D282 専用 (`t139-preregistration-approval-supersession/v1`)。D291 の grammar は別物 |
| 6 | `FROZEN_MANIFEST` は 23 件 (`output/s1-freeze` / `output/s8b-freeze` / 2026-07-16 insights)。本 wave の対象 path は 1 件も含まない。DW-O09 の pin 閉包は `output/registry/…jsonl` が D282 payload に 1 箇所 (`docs/decisions.md:12942`) |

## land 2 との二重実装照合 (結論)

- land 2 session 2 は **段 3 稼働中で実装 commit ゼロ**。その brief の scope 外宣言に
  `b03` consumer・`submit_pilot`/`submit_main` 本体・§S7 #7 が明記されている → **(i)(ii)(iii) は非重複**
- **(iv) のみ接触面**: land 2 の追加裁定 (P6) が「resolver は `addendum_b` role を D291@`F_p` から読む」。
  ただし land 2 は **land しない**方針で branch を引き渡すため、main へ先に入るのは本 wave である。
  本 wave は D291 payload の**読み手を 1 つだけ**作り、land 3 がそれを consume できる形にする
  (package 分離により file 衝突は `__init__.py` すら発生しない)

## 親の provisional 裁定 (攻撃対象。覆してよい)

- **(P1)** 公表台帳の実体 = `output/registry/t139-publication-reservations.jsonl` (固定 path、JSONL、
  append-only)。path は module 内の固定 literal から導出し、環境変数・引数・設定 file の口を作らない
- **(P2)** 新規 package `orchestrator/publication/` に置く (`ledger.py` / `approval_d291.py` /
  `addendum_p_envelope.py` / `admission.py` / `report.py`)。`orchestrator/preregistration/` は触らない
- **(P3)** **本 wave は予約 entry を 1 行も発行しない。** 台帳 file は空 (0 entry) で作るか、
  そもそも作らず「不在 = 予約なし」を gate が fail-closed で扱う。ordinal 1 の消費は
  追補 P 凍結後の別 land の判断であり、D292 の禁止解除に触れない
- **(P4)** (iii) の本走 gate は `require_publication_reservation_for_main_run()` として実装し、
  **`submit_main` 本体は作らない**。gate は「呼ばれたら検査する述語」として export し、
  land 3 が `submit_main` を書くときに結線する。恒真回避のため正例 (予約が一意に成立する台帳) を添える
- **(P5)** (ii) の marker gate は 2 層 — (a) 文書 bytes を走査する述語、(b) `tools/` の docs 検査へ
  結線して承認 payload fragment が marker 入り文書を pin したら赤にする。fold 本体
  (`spool_fold.py`) の改造は行わず、検査側で止める
- **(P6)** report 層は「role → 承認状態」の構造化 dict を返す純関数 + CLI 1 本とし、
  `authority: none` の文書について「D291@`F_p` が承認済み」と機械的に述べる。文書は書き換えない

## 並列分割方針

段 2 (プラン 1 本) → 段 3 (2 レンズ並列) → 段 4 (親裁定 + 変異事前登録) →
段 5 (3 lane 並列 — A: (iv) D291 payload resolver + report / B: (i)(i-b) 台帳束縛 + create-only /
C: (ii) marker gate + (iii) 本走 gate + (iv-b) `p01`〜`p03` exact-key) →
段 6 (敵対レビュー 2 本並列 → fix → 変異 matrix → 受入全走) → 段 7 記録 → 段 8 自己改善 → 段 9 land。
