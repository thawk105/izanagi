# [T-2582] K2 manifest の知識源を測定記録へ絞る運用反映

`authority: none` / `default_effect: no-state-change` — 本 dir は wave の逐語凍結と裁定パッケージで
あり、可変状態の正本ではない。正本は worklog 末尾と `docs/agent-architecture.md`。

- 日付: 2026-09-14
- wave branch: `worktree-dev-wave-t2582-manifest-measurement-sources`
- 裁定: D1936 項 2
- 実装面差分: **ゼロ** (docs のみ 17 行追加)

---

## 何をしたか

K2 宣言アームの知識 manifest を作る側 (信頼中核) が `sources` に何を選んでよいかの規律を、
正本 docs へ書き、実走導線から引けるようにした。

- `docs/agent-architecture.md` の `coder-v4-autonomous-k2` 節に「知識源の選定 (送り手側の義務、
  D1936 項 2)」項を足した (13 行)。
- `docs/phase3-s4b-runbook.md` の §1 に、K2 アームを回すときに上記項へ従う旨の**参照 3 行**を置いた。
  規律本文は複製していない。

## なぜ要ったか (発火の一次記録)

2026-09-02 の走行で、知識源に含めた `campaign.lock` の `spec_content` を読んだ
`coder-v4-autonomous-k2` が「外部データ側から自分の参照範囲を狭める働きかけ = 信頼境界の逆転」
として退け、`instruction_like_content_detected: true` を申告し、production の K2 consumer が
走行を止めた (job `988634.nqsv`)。**gate の誤作動ではなく設計どおりの発火**であり、
起票時点で「gate 側で解決してはならない」と定められていた。

是正は送り手側で行われ、知識源を測定 WAL 1 件へ絞って通した。しかしその判断は
`output/insights/2026-09-10_cc-next-precheck/run-card.md` に**当該 1 走の指定として**あるだけで、
常設の規律にも、manifest を作るときに読む導線にもなっていなかった。

**したがって純増は「1 走限りの判断を常設規律にし、作成時の導線を足したこと」である。**
「運用文書に何も無かった」は誤りで、段 3 のレンズ b がこれを反証した (`reviews/consult-luna2.md` M-03)。

## 判定基準を「書き手」から「文の種類」へ移した

段 2 plan の初案は「人間または AI が書いた自由文フィールドを含む file は選ばない」だった。
段 3・段 6 の敵対検査が、この基準では**両側へ外す**ことを示した。

- **広すぎる側** (`reviews/consult-sol.md` S-01): 裁定は「測定記録へ絞る」「設計説明を置かない」
  であって、書き手による一律除外までは決めていない。設計説明を含まない外部の測定記録まで
  締め出す。
- **狭すぎる側** (`reviews/consult-luna2.md` M-02): `s4_loop_digest.txt` は
  `orchestrator/critic/digest.py` が埋め込む「閾値判定なし、異常かどうかは読み手が stock 対照比で
  判断」という**定型の運用説明**を持つ。機械生成なので書き手基準では素通りする。

確定した基準は **「誰が書いたか」ではなく「何を述べた文か」** である。

### 実在成果物へ当てた判定 (段 3・段 6 が独立に実施)

`output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/` の 4 件:

| 成果物 | 判定 | 根拠 |
|---|---|---|
| `runs/wal.jsonl` | **選定可** | 全 record が build 条件・検証判定・測定値・commit 結果 |
| `campaign.lock` | 除外 | `spec_content` が設計説明。命令形の文を含む |
| `s4_loop_digest.txt` | 除外 | 測定表に定型の運用説明が同居 |
| `loop_state.json` | **当初は判定が割れた** | 進行状態と抽象的な成否のみ。観測値なし (`delta_pct` 全件 null) |

`loop_state.json` の割れは段 6 レビュー B (`reviews/review-b.md` RB-01) が出した blocker で、
「観測値と判定を伴わず、探索の進行状態と抽象的な成否だけを保存した checkpoint は測定記録に
当たらない」を本文へ足して一意に決まるようにした。

**転移の確認:** レビュー B は別 campaign `p3-s4-red-s4-red-consumer-9a1897c4` の 3 件にも当て、
file 名の許可リストを作らずに同じ結論が出ることを確かめた (`reviews/review-b.md` RB-03)。
同 campaign の `s4_rejections_digest.txt` にも同じ定型注記があった。

## 加工へ滑る一歩手前で止めた

段 6 レビュー A (`reviews/review-a.md` RA-02) が、初稿の「どちらも測定値と同居していても外す」は
**field や注記を削る指南として読める**と指摘した。裁定が明示的に禁じた「指示検出をすり抜ける
文章加工」そのものである。「これらの説明を含む**成果物**は、測定値が同居していても source に
選ばない。説明部分を削って投入するのではなく、別の測定記録を選ぶ。」へ置換した。

**gate は 1 行も触っていない。** K2 consumer の指示検出、manifest の schema・parser・受領証、
role 契約、2026-09-02 の歴史 fixture はいずれも不変である。

## 子と段の実績

| 段 | 子 | 結果 |
|---|---|---|
| 2 plan | 1 | 反映先・挿入位置・文案・実装面差分ゼロの判断 |
| 3 consult | 3 (sol / luna / luna2) | real 7・refuted 6 |
| 6 review | 2 | blocker 4 件 (RA-01 / RA-02 / RB-01 / RB-02) |
| 6 focus | 1 | 全 10 件 closed、新規 real なし |

**luna 初回は部分レビューで終わった。** 自分で組み立てた不在 path 1 件に対して、prompt の
「読めなければ即停止」を適用しレビュー全体を打ち切った。停止条件の射程 (射影 file に限る) を
明示して luna2 で再実施し、全レンズを回収した。この型は段 8 で routing した。

変異 matrix は実装面差分ゼロにより `DW-S04` で免除。**受入全走は免除していない。**

## 裁定パッケージ (本 wave では実装せず、ユーザーへ返す)

`docs/agent-architecture.md` の実行境界項が「この role の wrapper が実際に consumer を通った
成果物は 0 件である」と現在形で断定している。2026-09-02 の走行では同 role が proposal を出し、
production の consumer がそれを判定している。ただし本文の「wrapper」が Codex adapter を指すのか
role 一般を指すのかが一意でなく、断定が偽なのか語の射程が狭いのかは別途の一次資料照合が要る。
T-2582 の名指し範囲外なので本 wave では直していない
(`reviews/consult-sol.md` S-02、`adjudication.md`)。

## 収録物

- `brief.md` — 段 1 brief (凍結)
- `adjudication.md` — 段 4 裁定 (凍結)
- `reviews/plan.md` — 段 2
- `reviews/consult-sol.md` / `consult-luna.md` / `consult-luna2.md` — 段 3
- `reviews/review-a.md` / `review-b.md` / `focus.md` — 段 6
