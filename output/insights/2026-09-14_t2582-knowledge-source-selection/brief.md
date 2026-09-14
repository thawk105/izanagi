# 段 1 brief — [T-2582] K2 manifest の知識源を測定記録へ絞る運用反映

## 研究前進

段 4 loop の K2 宣言アームは 2026-09-10 に production の K2 consumer で 1 本が停止した
(job `988634.nqsv`)。role が `campaign.lock` の自由文 `spec_content` を「信頼境界の逆転」として
退け `instruction_like_content_detected: true` を申告した。これは gate の誤作動ではなく設計どおりの
発火である。親は送り手側で知識源を測定 WAL 1 件へ絞って通したが、その判断は運用文書に無い。
書かれていないので次の K2 走行は同じ場所で再び止まる。本 wave はその規律を正本へ書き、
K2 試行の再現性を立てる (roadmap の knowledge-conditioned 成立へ向けた土台)。
**完了判定** = 送り手側の source 選定規律が正本 docs にあり、`tools/check_docs.py` と受入全走が緑。

## 確定済みユーザー裁定 (D1936 項 2、逐語は rulings.md)

> **決定:** manifestの知識源を測定記録へ絞る。設計説明を未信頼入力側へ置かず、gate変更や
> 指示検出をすり抜ける文章加工はしない。

D1936 前文は「各実装は名指しの変更に限定し、付随するgate・台帳・汎用化を足さない」と定める。

## scope

- **IN:** K2 manifest の `sources` に何を選ぶかの**送り手側**規律を、既存の正本 docs へ書く。
- **OUT:** gate・検査・台帳・一般化の新設。K2 consumer (規律 6 の指示検出) の変更。
  role 契約 (`.claude/agents/*.md`) の変更。歴史的 fixture の書き換え。知識源の許可リストや
  機械的 leak 判定 (D1429 が明示的に不採用、decisions.md の同 D「採らない案」)。

## 不変条件

1. 規律 2 を緩めない。正しさ・identity・性能ゲートの受理集合を 1 bit も変えない。
2. 規律 6 の送り手側義務を書く。逆に「検出を避けるために文章を加工する」と読める文言は
   書かない — 裁定が明示的に禁止している。
3. 絶対規律 7: 2026-09-02 の歴史的 K2 走行 (`campaign.lock` を source に含む) は事実として残す。
   `orchestrator/tests/test_knowledge_manifest.py` の歴史 fixture を書き換えない。
4. 実装面 (コード・テスト・実行可能 script・機械設定) の差分ゼロを既定とする。必要が判明したら
   段 4 で再裁定し Codex `role=author` を立てる (D95)。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a) 反映先 = `docs/agent-architecture.md` の `### coder-v4-autonomous-k2` 節。**
  同節が K2 の「知識境界」(受け手が何を使ってよいか) と「投入は信頼中核が射影で行う」を持つ
  唯一の生きた正本であり、送り手側規律の自然な同居先だから。
  対抗案 = `docs/phase3-s4b-runbook.md` (knowledge / K2 を 1 語も持たず、新節の起こしが要る
  = 名指しの変更を超える)。
- **(P1-b) docs-only。** 実装面差分ゼロ。
- **(P1-c) 「測定記録」の外延** = campaign が機械的に書いた測定成果物 (`runs/wal.jsonl` など)。
  人間または AI が書いた自由文フィールド (`spec_content` など) を含む file は source にしない。

## 既存被覆の検索結果 (性質で検索、純増だけ)

- `docs/agent-architecture.md` §coder-v4-autonomous-k2「知識境界」= **受け手**が何を使ってよいか。
  送り手が何を source に選ぶかは無い。
- `docs/phase3-s4b-runbook.md` §2 リーク制御チェックリスト = K0/K1 coder への勝ち筋値遮断。
  知識源選定は無い (K2 の語自体が無い)。
- D1429 / D1493 / D1559 = 記録の分離、実在検証の置き場所、受領証からの射影。source 選定規律は無い。

→ **純増 = 送り手側の source 選定規律 1 点。**

## 変更面の実アンカー表

| # | path | アンカー (節・bullet) | 予定 |
|---|---|---|---|
| A1 | `docs/agent-architecture.md` | `### coder-v4-autonomous-k2` の `- **構造遮断は撤去しない:**` bullet | その近傍に送り手側規律 bullet を 1 つ足す |
| A2 | `docs/decisions.md` | 段 7 の `docs/spool/` fragment | 採用理由・不採用案を記録 |

pin 閉包 (DW-O09): `docs/agent-architecture.md` は `check_docs.py` の `LIVING_DOCS` 列挙に入るが、
byte 予算も whole-file SHA-256 pin も持たない (予算表は command / skill-self-improvement /
tools README / provenance 族のみ)。docs 間の行番号参照禁止は掛かる。

## 受入・実測環境

login node。`python3 tools/check_docs.py` と受入全走
(`tools/dev_wave_wait.py acceptance --lease-optional`)。性能計測は伴わない。

## 並列分割方針

docs-only なので段 5 実装子なし (親が docs 本文を編集する)。
段 2 = plan 1 本。段 3 = consult 2 本 (レンズ (a) 裁定逐語との整合と規律 6 送り手側義務の正しさ、
レンズ (b) 文面が指示に読めないか・scope 超過・既存正本との重複)。段 6 = review 2 本。
