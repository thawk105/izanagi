# 段 4 裁定 — [T-139] land 2 session 2

親が段 2 (NO-GO / blocker 6) と段 3 の 2 レンズ (lensA = NO-GO / blocker 15、lensC = NO-GO /
blocker 4 + 1 deferred) を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。

- base tip: `19f15758` (session 1 の `c6ab6272` + local main `bc260989` 取り込み 2 回)
- `F_r` = `39d76098…` / `F_p` = `b13b7ea8…`。**どちらも HEAD の祖先であることを実測確認済み**

---

## 1. 段 2 の blocker 6 件 — 2 レンズの独立判定と親の裁定

| ID | lensA | lensC | **親の裁定** |
|---|---|---|---|
| B1 CMakeCache raw pointer 無し | real / (i) 内部矛盾 | real / (i) 内部矛盾 | **real / (i)。両者一致。** §7.1(12) は実装不能 |
| B2 intent 母集合・create-only provenance 無し | real / (i) 内部矛盾 | real / (i) 内部矛盾 | **real / (i)。両者一致。** §7.1(16) は実装不能 |
| B3 別 stage receipt が validator 入力に無い | real / (iii) 次 session | real / (i) 内部矛盾 | **real。分類は (i) を採る** (下記) |
| B4 `J` transcript の byte grammar 無し | real / (i) 内部矛盾 | real / (i) 内部矛盾 | **real / (i)。両者一致。** §6.8 は実装不能 |
| B5 「他の作業なし」の event 列無し | real / (iii) producer 側 | **refuted** (§9 引受残余) | **refuted を採る** (下記) |
| B6 §6.7(8) の第 3 consumer が scope 外 | real / (ii) scope 誤り | real / (iii) 次 session | **real。両分類とも結論は同じ** (下記) |

### B3 の分類 — lensC (i) を採る

lensA は「次 session の receipt-set consumer で閉じる」とし、lensC は「schema に peer receipt
pointer / receipt-set namespace が無いので内部矛盾」とした。**両者の事実認定は同じ**で、
「schema に入力が無い」点は一致している。分かれたのは「consumer を作れば閉じるか」である。

親は **lensC を採る。** 理由: consumer を作っても、比較対象の peer receipt を**どこから得るか**が
承認済み文書に無い。lensA 自身が「persisted pilot/main receipt の両 path を受ける」と書くが、
その両 path を producer 以外の誰が決めるかが未定義である。producer が渡す path を信じるなら
§8 の否定検査 (producer 申告値を受理条件の入力にしない) を破る。
**したがって新しい canonical decision (peer receipt の canonical namespace) が要る。**

### B5 の分類 — lensC の refuted を採る

lensC は `record-items-v2.md` §9 の逐語 (`:803-813`) を挙げ、
「その raw が実際のカーネル出力かは producer 権限内では判別できない。閉じるには producer 権限外の
collector が要り、それは本書の射程外である。**この残余は承認時に明示的に引き受けられたものとして
扱う**」を根拠にした。**承認済み文書が明示的に引き受けた残余は blocker ではない。**

ただし lensA の要求は採用する — **validator の verdict を「記録された窓・間隔の整合」に限定し、
「他の作業が無かった」を保証したとは記録しない。** これは絶対規律 3 (保証していない性質を
保証したと書かない) の直接適用である。

### B6 — 分類は割れたが結論は同じ

lensA (ii) scope 誤り / lensC (iii) 次 session の real 要件。**どちらでも結論は
「本 session が『§6 全件を閉じた』と記録してはならない」**で一致する。親はこれを確定とする。

---

## 2. 確定裁定の前提が canonical decision で覆った (最重要)

### RP-4 (a) は D292 により失効している

- **RP-4 (a)** = 「pilot 解禁条件 = 公表 core 3 文書の凍結承認 + その fold」(2026-08-11 第 9 回)。
- **D292** (2026-08-11 land 済み、`docs/decisions.md:13581`) =
  「`pilot_submission` / `main_submission` の禁止を解除できるのは canonical 台帳へ fold された
  decision だけである。**wave の自己申告・manifest の宣言・実装 wave の完了報告・handoff の記載では
  解除しない。**解除条件の中身は本決定では定めない」。
- 3 文書の凍結承認 + fold は D291 として**既に起きた**。しかし D291 自身が
  `operational_state_on_fold: pilot_submission = forbidden / main_submission = forbidden` を固定し、
  D292 が解除を canonical decision の専権にした。
- **したがって「3 文書の fold で pilot が解禁される」は成り立たない。**
  両レンズが独立にこれを指摘した (lensA §D291 追補 必答 5、lensC §4)。

**親の裁定: RP-4 (a) の解禁条件部分は失効として扱い、裁定パッケージでユーザーへ返す。**
本 session は pilot / 本走を投入しない (もともと scope 外) ので、実装上の帰結は次の 1 点だけである
— **resolver の「解決成功」を「投入してよい」と読ませない型設計が必須になる。**

### manifest 表現が未裁定である

D282 の閉包 (三つ組 7 件) と D291 の `exact_closure` (approved role **ちょうど 2 件**、
`document_relations` **節全体** exact、`historical_candidates_rejected_for_role` の拒否義務) は、
**1 枚の平坦な manifest に同居できない。** 両レンズが独立に同じ結論へ達した。

- flat union にすると D291 の「2 role ちょうど」を破る
- D291 の 2 role だけにすると D282 の三つ組・erratum 順序・schema root が落ちる

lensC は namespaced projection (`approval_manifest/v2` に `d282_record_approval` と
`d291_publication_approval` の 2 区画) を提案した。**これは設計択一であり、親が独断で決めない。**

---

## 3. 親の裁定 — 本 session の scope

### 実装する (段 5、1 lane)

**§S7 #2 = Git trust root 部分集合 (確定裁定 RP-2 (a) の逐語) のみ。**

これを選ぶ理由は 2 つある。

1. **これは「呼ばれない新規コードを積む」ことではなく、既存コードに現存する穴を塞ぐことである。**
   `orchestrator/preregistration/blobref.py:198` は `subprocess.run(["git", ...])` で
   **git を名前解決**しており、`_GIT_ENV_ALLOW` (同 `:21-30`) は `PATH` を継承している。
   この module は既に `read_pinned_blob` → `approval_payload.load_approval_payload` として
   `F_r` の `docs/decisions.md` を読む経路で使われている。**穴は今そこにある。**
2. **RP-2 (a) は確定裁定であり、実装部分集合は manifest 表現にも B1〜B4 にも依存しない。**
   段 1 で覆ったのは却下理由 1 本 (「(b) を採ると本環境を拒否する」) だけで、
   選択そのものと部分集合の内容は不変である。両レンズもこれを追認した。

**実装する差分 (RP-2 (a) の 8 項目に対する現状の充足検査):**

| # | RP-2 (a) の要求 | 現状 | 本 session |
|---|---|---|---|
| 1 | `PATH` 非継承 | **未充足** (`_GIT_ENV_ALLOW` に `PATH`) | 実装する |
| 2 | 絶対 path 起動 | **未充足** (`["git", ...]`) | 実装する |
| 3 | 全 `GIT_*` 破棄 | 充足 (allowlist に `GIT_*` 無し) | 回帰検査を足す |
| 4 | `GIT_CONFIG_NOSYSTEM` | 充足 | 回帰検査を足す |
| 5 | `core.commitGraph=false` | **未充足** | 実装する |
| 6 | alternates / promisor 拒否 | **未充足** | 実装する |
| 7 | `--no-pager` | **未充足** | 実装する |
| 8 | `core.fsmonitor=false` | **未充足** | 実装する |

**成果物影響 (DW-G05):** これを実装しないと、`PATH` 上に置いた偽 `git` が `rev-parse` /
`merge-base` の出力だけを偽装することで、**`F_r` より前の checkout で測った試行が
「承認済み事前登録の子孫で測った」として受理される。**SHA の偽造は不要である。
certified 選択の根拠になる事前登録 identity が、同一権限の攻撃者でなく単なる `PATH` 汚染で崩れる。

### 実装しない (裁定パッケージで返す)

manifest 実体 / `resolve_effective_preregistration` / `PreregBinding` / 受領証 writer /
固定 semantic validator / conformance vectors / raw snapshot API。

**理由:** RP-1 (a) の裁定は「この session の終わりに §S7 #1・#2 が発火すると初めて言える」ことを
目的にしていた。しかし
- §S7 #1 は manifest 表現が未裁定で書けない (§2)
- §7.1 の 20 項目のうち 4 項目 (12 / 16 / §6.1 / §6.8) が承認済み文書の内部矛盾で実装不能 (§1)
- §S7 #3 の consumer である semantic validator が上記により完成しない

**裁定の目的が達成不能である以上、部分実装を積んで「実装した」と記録するのは
絶対規律 3 が禁じる方向である。** `DW-STOP` の「承認済み裁定の前提を覆す未見の新事実がある」に
該当するため、段 5 でこれらへ着手しない。

### 親が採用するレンズ所見 (実装に反映するもの)

- **lensA BLK-03 / lensC Q3:** `PreregBinding` は identity-only とし、`pilot_ready` 等の
  投入可否を表す field / 命名を持たせない。→ **本 session では `PreregBinding` 自体を作らないので、
  次 session への必須要件として記録する。**
- **lensA の Git 所見:** 同一 SHA-256 は同じ bytes を示すが同じ file object / inode / mount を
  示さない。→ **段 1 brief の「binary の SHA-256 は同一なので同じ file」という推論は撤回する。**
  親が主張してよいのは「sandbox の uid 表示を親環境の事実へ移せない」までである。
- **lensA / lensC の一致:** RP-2 (a) を「owner に依存しないので十分」と記録してはならない。
  部分集合は owner に依存しないが、**十分性は独立には証明されていない。**

### 却下 / 不採用

- **段 2 プランの `addendum_b=None` を pilot-ready、非 None を恒真 deny とする案** — 不採用。
  D291 が承認済み追補 B を持つ以上、恒真 deny は `DW-S04` の「通る正例を 1 つ添える」を満たせない。
  本 session では resolver を作らないので争点にならないが、次 session へ要件として記録する。
- **B1 / B2 / B4 を producer 申告値で代用する経路** — 全面却下。
  両レンズが最大 risk として名指しした false-green である。

---

## 4. 変異事前登録 (暫定。段 6 で実装を読んで再導出する)

`DW-M01` に従い実装前に登録する。**本登録は暫定であり、session 1 の申し送り 5
(段 4 の 10 件中 7 件が実効 gate に当たっていなかった) に従って段 6 で再導出する。**

対象は段 5 で実装する Git trust root 部分集合のみ。

| # | 変異位置 | 期待する赤の理由 | 単一理由性の確認事項 |
|---|---|---|---|
| M1 | `PATH` を allowlist へ戻す | 偽 `git` が解決される負例が緑になる | 絶対 path 検査が先に落ちないか要確認 |
| M2 | 絶対 path を名前 `"git"` へ戻す | 同上 | M1 と同じ入力で落ちるなら 1 本へ統合する |
| M3 | `core.commitGraph=false` を外す | commit-graph 経由の祖先偽装負例が緑 | 祖先検査より前に別 guard が無いか |
| M4 | alternates 拒否を外す | 外部 object store 由来 blob が受理される | blob digest 検査が先に落ちないか |
| M5 | promisor 拒否を外す | 同上 | M4 と同一入力なら統合 |
| M6 | `--no-pager` を外す | pager 経由の出力汚染が検出されない | 出力 size 上限が先に落ちないか |
| M7 | `core.fsmonitor=false` を外す | fsmonitor hook 実行が阻止されない | — |
| M8 | `GIT_CONFIG_NOSYSTEM` を外す (回帰) | system config 注入が通る | — |
| M9 | `_GIT_ENV_ALLOW` へ `GIT_DIR` を足す (回帰) | 別 repo が参照される | — |
| **M-正例** | 変異なし | **緑** | 承認外の過剰拒否が無いことを示す正例 |

**単一理由性が確認できない変異は登録せず、実効 gate へ再照準する (F28)。**
最終確定は段 6 で行う。

## 5. 遷移

`4 → 5 → 6 → 7 → 8 → 9`。段 5 は 1 lane (Codex `role=author`)。
**段 9 で land しない** (本 session は最終ではない)。
