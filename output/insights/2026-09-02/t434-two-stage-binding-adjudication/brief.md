# [T-434] 段 1 brief — D1407 の二段束縛を実装する

基準 main: `28ebff456b9f57a927854950b5030fa77aec6529`。branch `worktree-dev-wave-t434-two-stage-binding`。

## scope (親の provisional 裁定。段 3 の攻撃対象)

上限引き上げの**発効 topology を強制する検査機構**を、既存の commit 検査機構の再利用で実装する。
検査する述語は次の 4 つで、いずれも fail-closed とする。
(i) 発効 commit `A` が非 merge、(ii) `A` の親集合が exact `{G}`、
(iii) `A` が追加する path が認定記録と受領証のちょうど 2 件で、いずれも create-only (変更・削除・
mode 変更・別 path の同時追加はすべて拒否)、(iv) `A` の message が `AI-Agent: none` を逐語で
ちょうど 1 本持つ。**上限は 1 bit も開かない。**

## 確定済みユーザー裁定 (覆さない)

- **D1407** — topology を `G` + `A` の二段束縛に確定。`A` の追加可能 path は認定記録と受領証の 2 件。
  `G` と `A` は同一 land transaction。現行 manifest の exact 世代数 2 と 8c 事前登録は変更しない。
  受領証で開く上限は新しい manifest 版へ隔離する。D121 決定 (7) / D150 決定 (4) / D156 を supersede しない。
- **D841** — 受領証は consumer 結線と同じ変更単位で設計する。受領証だけ先に作る形は採らない。
  D1407 が「D841 は不変」と明記している。
- **D156** — P6 認定の 4 コア要件 (end-to-end calibration・反転変異と検査者選択権・独立検査者
  attestation・認定記録と失効照合)。
- **D882** — 条件 11 の locus と runbook の承認上限の主張文は T-435 の所有。触らない。

## 不変条件

- 絶対規律 2: 受理集合を広げる向きの緩和をしない。P6 が未実装である限り fail-closed のままとする。
- 現行の受理集合 (受領証なしの 1 世代・2 世代運転) を**縮小もしない**。design-v3 §1 が
  「v2 の『受領証が無ければ実効 cap = literal 1』をそのまま実装してはならない」と警告している。
- 凍結 bytes、8c 事前登録本文、条件 11 の証拠契約、runbook の承認上限文に触れない。
- 新規 parser を増やさない。producer と completeness で 2 つ目の receipt parser を作らない。

## 実アンカー表 (すべて本 wave で一次資料に当たって確認済み)

| アンカー | 実測した内容 |
|---|---|
| `orchestrator/campaign/trial_registry.py:1243` `assert_effective_commit_exact_parent` | 親集合 exact 検査が**既に実装済み**。root commit・merge・別親・graft・replace ref・shallow を拒否 |
| `orchestrator/campaign/trial_registry.py:1211` `_parents_at_commit` | `rev-list --parents -n 1` を 1 行・ASCII・commit identity 不変で読む |
| `orchestrator/campaign/s8b_ratified_freeze.py:518,528,546,558,573` | `AI-Agent: none` を raw 行ちょうど 1 本と parse 値の二重で判定。`_assert_user_commit` は非 merge も見るが親がちょうど 1 つとは言わない |
| `orchestrator/campaign/s8c_acceptance_receipt.py:172,259,152,421-423` | canonical bytes・exact key・封印型。`certifying is not False` を構造的に拒否する |
| `orchestrator/campaign/reflux_formal_consumer.py:108,248,934,1034` | 条件評価は `P6Unavailable` で無条件停止する |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:144,506` | `MAX_APPROVED_GENERATIONS = 2` |
| `orchestrator/campaign/trial_registry.py:771` | registered manifest は `generations` を「整数 2」だけ受理する |

## 成果物の形

`A` の topology を検査する fail-closed な部品と、実 git commit で構成した正例・負例。
正例は実体を stub しない — 実 repo に実 commit を作って通す。上限・受理集合は動かさない。

## (P1) scope の割れ目 — 段 3 の主攻撃対象

D1407 §1 は `G` が「実装一式 (P6 の本体・calibration・admission 結線・受領証機構・新 manifest・
全 consumer 結線)」を導入すると書き、§3 は `G` と `A` を同一 land transaction と定める。
一方 `A` は `AI-Agent: none` 逐語 1 本を要求する**人間の commit** であり AI は作れない。
worklog 1155 は「残る blocker は P6 の本体実装」と書く。したがって
**(a)** 本 wave の narrow scope は D841 の「受領証だけ先に作らない」に抵触しないか、
**(b)** DW-G04 の発火条件 (認定記録・受領証の実 artifact path) を書けないまま実装してよいか、
**(c)** `G` の内容を複数 commit に分けて積み上げてよいか (認定記録は revision に束縛されるので
tree が揃えばよいのか、`G` 1 本での導入を要求するのか) — この 3 点を独立に検査させる。

## 分割方針

実装面は Codex `role=author` 1 単位 (D95)。編集 path は素集合になる見込みで並列不要。
親は brief・裁定・統合 commit・変異 matrix・受入・記録・land を担い、実装面を直接編集しない。

## DW-G05 成果物影響

放置すると、発効 commit の形が機械検査されないまま「二段束縛にした」という記述だけが台帳に残る。
将来 `A` が提示されたとき、親が exact `{G}` を目視で確かめる以外に検査手段が無い。
逆に上限を開く向きの変更は本 wave では一切行わないため、certified 選択・材料レポート・
試行台帳の値と受理集合はいずれも 1 bit も変わらない。

## 稼働 wave との編集面重複

branch tip 25 本と稼働 worktree の未 commit 差分の双方を走査した。上表のアンカー file を
触る稼働 wave は **0 件**。
