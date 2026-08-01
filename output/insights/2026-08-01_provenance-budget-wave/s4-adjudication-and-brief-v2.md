# 段 4 裁定 + brief v2 (scope 拡張: 縮約 + コンテキスト外出し)

## 0. ユーザー裁定によるscope 拡張 (2026-08-01)

「意味保存縮約は state of the art なのか、コンテキスト外出しは」という問いに対し、親は
**縮約は一時的延命であり、この repo 自身が dev-wave で使う「入口 + 条件付き reference + dispatch」
の方が構造的に強い** と回答した。ユーザーは **「縮約を land → 外出しも本 wave で」** を裁定した。

- 根拠: 予算は「全 commit で読む context 費用」の代理指標である。縮約は総量と常時読量を同じだけ
  減らすが、外出しは常時読量だけを大きく減らし、かつ将来の incident 固有契約が入口へ積み上がる
  増加ダイナミクス自体を止める。実測の増加ペースは 2.5 週で +3,313 bytes。
- 本 wave で `check_docs.py` の registry・閉包検査を変えるため **gate 新設が確定 = `DW-O13` が発火**した。
  期限 (段 2 前) を過ぎての成立なので、入口の巻き戻し規則に従い **段 2 から再実行**する。
  段 1 の brief は本書 §2 の v2 へ差し替える。段 2 の縮約プランと段 3 の 2 レンズは
  「phase 1 (縮約) に関する証拠入力」として保持し、下記裁定を経て plan v2 の一部になる。
- `check_docs.py` と test の変更は実装面なので **Codex `role=author` が必須** (D95 / D105)。親は編集しない。

## 1. 段 3 所見の裁定 (real/refuted・採否・scope)

| ID | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-01 (BLOCKER) | **real** | 採用 (scope 内) | 親が独立に裏取り: checker は `not correction.waiver.exact` を連言に持つ (`tools/check_ai_provenance.py` の carrier 判定) が、**現行公表契約に書かれていない**。縮約ではなく**欠落の追記**として直す |
| A-02 (HIGH) | real | 採用 | CAB の「raw 候補数 = 隔離 parser の認識数」照合義務を 1 文で保持する |
| A-03 (HIGH) | real | 採用 | `AI-Agent: none` を「次の 1 行**だけ**を使う」と書き換えない。排他は「唯一の `AI-Agent` trailer」に限定する現行言い回しを維持 |
| A-04 (HIGH) | real | 採用 | 対応表は planner 独自採番でなく**親目録 O1〜O45 基準**で作り、非義務は「非義務」と明示裁定する |
| A-05 (MEDIUM) | real | 採用 | docs 本文を実質起草したのは codex planner なので、commit trailer に `product=codex; ...; role=author; scope=<docs>` を記録する。D95 の強制対象外であることと、一般記録義務は別 |
| A-06 (MEDIUM) | real | 採用 | 「checker も内容検出した導入 commit 以後だけ検査」を短く保持する |
| A-07 (MEDIUM) | real | 採用 | `default` の発火は「**明示的に既定設定を選んだ場合**」を維持する |
| A-08 / B-05 (nit) | real | 採用 | brief の「凍結 bytes pin は皆無」を訂正 — 現行 HEAD を束縛する pin はないが、`tools/codex_reasoning_ab.py` に固定 commit 再構成の歴史 snapshot 参照が 1 件ある (現行編集は非到達) |
| A-09 / B-06 (nit) | real | 採用 | 受入は exact byte 一致でなく**上限判定**にする。案本文の実測は 7,101 bytes (planner の 7,104 は誤差) |
| A-10 (nit) | real | 採用 | `git log` の確認例は「義務ではない任意の確認手段」と明示裁定し、**外出し先の `audit.md` へ移して残す** (外出しにより削除せず済む) |
| B-01 (HIGH) | **real** | **scope 外 → 裁定パッケージ** | `_scope_policy_commit` / `_implementation_policy_commit` は HEAD 基準の単一 epoch で、CAB のような per-lineage 判定でない。D98 が却下したはずの形が scope/implementation 側に残っている。checker 変更なので本 wave では実装しない。brief の (P4) は「単一親・同一 lineage・ff-only の範囲でのみ epoch 不動」へ限定する |
| B-02 (HIGH) | real | 採用 | waiver の `reason` も識別子正規表現の対象だと明記し、correction 節へ「`AI-Agent-Waiver` を持つ commit は correction を担えない」を追加する (A-01 と同じ穴) |
| B-03 (MEDIUM) | real | 採用 (docs 側のみ) | 実装面の定義を「非 Markdown」→「`.md` / `.rst` 以外」に直し、公表契約と checker を一致させる。checker 側を広げる案は scope 外 |
| B-04 (MEDIUM) | real | 採用 (phase 2 が担う) | 一回限りの受入 gate として byte 上限と逐語照合を課す。**恒久 ratchet は phase 2 の予算 schema (入口を今より小さい上限で登録し、family 合計は据え置き) が担う** |

refuted はゼロ。D105 却下案 (f) の歯止め (優劣断定禁止) は案文で保存されており、レンズ A も反証できていない。

## 2. brief v2

### scope

- **phase 1 (commit 1、docs-only)**: `docs/ai-provenance.md` を意味保存縮約し、上記裁定の追記
  (A-01/A-02/A-03/A-06/A-07/B-02/B-03) を反映する。**実ファイル 7,200 bytes 以下**。
- **phase 2 (commit 2、docs + 実装面)**: 常時読む入口と条件付き reference へ分割する。
  - `docs/ai-provenance.md` = 全 commit で読む義務 (必須形式、Codex author 契約、waiver、記録単位)
    + **条件 dispatch 表**。
  - `docs/provenance/correction.md` = `6b64d21` の一回限り forward correction (2026-07-29 に
    `6d7141dc` で消費済み。新規の担い手は規約上あり得ない) と、その監査 range 権威。
  - `docs/provenance/audit.md` = 範囲監査・`--message-file`・legacy 遡及・任意の確認コマンド例。
  - `tools/check_docs.py` に新 registry と閉包検査 (予算未登録実体の拒否、入口 dispatch と
    reference の相互到達性) を足し、境界テストを同じ変更単位へ入れる (D96)。**Codex author 必須**。
  - 新しい D を `docs/decisions.md` へ記録する (受理集合が変わるため D96 手続き)。

### 不変条件 (破ったら停止)

1. 3 逐語 (Codex author 必須文 / CAB 最終 block 配置文 / waiver 形式) は **`docs/ai-provenance.md`
   に逐語で各 1 回**残す。`POLICY_PATH` は checker 定数なので、reference へ移してはならない。
   `scope=` の出現も入口に 1 回だけ残す (`_scope_policy_commit` の履歴検出対象)。
2. 義務の削除ゼロ。外出しは**移設であって削除ではない**。移設先は入口の dispatch 表から一意に
   到達でき、機械検査で孤児・逃がしを拒否する。
3. **family 合計予算は 9,000 bytes を超えない** (今日の総量を上げない)。入口の上限は今日より
   小さくし、常時読量を実際に減らす。個々の値は plan v2 で確定する。
4. 予算 schema 変更は D として記録し、境界テストを同じ commit に入れる。
5. 実装面 (`tools/check_docs.py`、`orchestrator/tests/**`) は Codex `role=author` が書く。親は書かない。

### 前提の実測 (訂正済み)

- `docs/ai-provenance.md` 実測 8,942 / 予算 9,000 (headroom 58)。縮約案の実体は 7,101 bytes。
- 現行 HEAD を束縛する bytes pin はない。歴史 snapshot 参照 1 件は固定 commit 再構成で非到達 (A-08)。
- forward correction は 2026-07-29 `6d7141dc` で**既に消費済み**。以後の担い手は規約が禁じている
  ため、この節は「発火し終えた条件付き契約」であり外出しの最有力候補。
- (P4 訂正) epoch 不動が言えるのは**単一親・同一 lineage・ff-only** の範囲に限る (B-01)。

### 成果物影響 (`DW-G05`)

- phase 1 を欠くと、次に義務を 1 行足す変更が `check_docs` 赤で入らず、未審査の予算引き上げか
  義務削除へ圧力がかかる。A-01/B-02 の欠落を放置すると、公表契約から実装した consumer が
  「waiver 付き commit でも forward correction を担える」と読み、D105 が閉じた受理集合が再び広がる。
- phase 2 を欠くと、常時読量が減らないまま incident 固有契約が積み上がり、同じ逼迫が数週間で再発する。

### 分割方針

- 段 2 (再実行): read-only codex が phase 1 + phase 2 の統合 plan v2 を file:line 粒度で起草する。
- 段 3 (再実行): 敵対 2 本 (A = 義務保存と移設の完全性、B = 機械束縛・新 gate の実効性・恒真化)。
- 段 5: Codex `role=author` (workspace-write) が `check_docs.py` + テストを実装。docs 本文は親。
- 段 6: 敵対レビュー 2 本 + fix。受入は計算ノードで全走 + `check_docs` + `check_ai_provenance`。
- 変異 matrix: 3 逐語の削除、reference の予算未登録化、dispatch からの参照削除 (孤児化) を
  positive control として事前登録し、統合 commit 後に `DW-O19` で本走する。
