---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1218-floor-reseal-rulings
seq: 2
---

## {{D:floor-reseal-drop-per-contract-lock}}. 床値 protocol の契約単位封鎖を撤去し、組単位の発行前拒否だけを残す

**決定 (2026-08-16 ユーザー裁定 = 案 3、機械化なし、`FROZEN_MANIFEST` へ載せない):**

D444 決定 5 (target の `contract_sha256` が組 index に既出なら発行を拒否する) を**撤去する**。
撤去は issuer と index 不変条件の両方で行う。同じ `contract_sha256` のまま `ccbench_pin` だけを
進めた 2 件目の protocol は、index が受理し issuer が発行できる。

代わりに issuer へ**組単位の発行前拒否**を置く。target の組 `(contract_sha256, ccbench_pin)` が
走査済み index の key に既出なら、create-only writer を呼ぶ**前に**拒否する。この拒否は artifact を
作らないため、復旧用の exact path 文言 (D444 決定 7 の「取り除くまで発行できない」) を載せない。
載せると、今回作っていない正規の既存 artifact の削除を誘導する。

versioned artifact を `FROZEN_MANIFEST` へ登録しない。登録を強制する scan・meta test・allowlist・
checker は実在しないことを実測した (23 key の明示 mapping であり namespace の directory scan はない)。
「登録してはならない」という逆向きの検査も新設しない。

`resolve_current_floor_protocol` は変更しない。

**維持するもの:** D444 決定 1〜4・6・7 (組からの path 一意導出、chain record pattern 登録、
不変 16 field の byte-exact 継承、固定 HEAD blob からの anchor 読み、恒真ゲート不採用、
失敗した発行の artifact を自動削除しない)、組単位一意性、create-only、既存の凍結 bytes、
凍結チェーン検証の保留状態、D460 の resolver 契約。

**理由:**

- 既定方針 3 本 (粗い provenance で足りる / 凍結チェーン検証は保留 / 防御的堅牢化は見送り) が
  いずれも束縛機構を増やす側と衝突する。「環境契約 1 世代につき床値 1 件」は世代が進むたび
  再取得を義務づけ、計測コストを構造的に増やす。
- 契約単位の封鎖は、採られた案 3 の唯一の実行形 (contract 据え置き・pin 前進) を機械拒否していた。
  実測: 封印済み protocol の組は (contract `e576e9cd…`, pin `d706650c…`)、現行 env 契約は同じ
  `e576e9cd…`、HEAD の `external/ccbench` gitlink は `511c9538…`。撤去しなければ床値 protocol を
  今後 1 件も発行できない。
- 組単位の拒否を writer より前に置くのは、後段の post-write full index 検査だけに任せると、
  無効な artifact をディスクへ書いてから拒否することになるためである。

**却下した選択肢:**

- **resolver を「現行 (contract, HEAD pin) の組に exact 一致があればそれ、無ければ現行 contract に
  exact 1 件」へ変える** — 親が段 1 で提案し、段 3 の敵対検証と一次資料で撤回した。
  (i) D460 が「選択条件に ccbench pin を入れてはならない」と明記しており、本裁定は D460 に
  触れていない。(ii) 実 driver `tools/pegasus/floor_campaign.sh` は固定 legacy path を `--protocol` に
  渡すため、admission が versioned protocol を authority として通し実測は legacy protocol で走る
  **authority 分裂**が起こりうる。fail-closed で止まるほうが良い。
  (iii) 配線は [T-419] (3)、実発行は [T-1255] が所有する。
- **contract 単位拒否を丸ごと消して組単位の発行前拒否を置かない** — 段 2 プランの初稿。
  組が legacy anchor 側で埋まっている場合に versioned path が空いているため writer が成功し、
  post-write の full index 検査で初めて赤になる。無効 artifact が残り、例外 message が
  正規 artifact の削除を誘導する。
- **`FROZEN_MANIFEST` へ versioned artifact を登録する** — 裁定が明示的に否定した。
  23 key 固定の assert と held/keep 分割が動き、凍結台帳の件数という provenance の数字が変わる。

**残る限界 (この決定では閉じない):**

- 契約単位の封鎖が消えたことで、同一 contract の record が 2 件ある状態が**到達可能になった**。
  この状態では `resolve_current_floor_protocol` が `count=2` で fail-closed になり、
  `certified_writer_admission` の床値 admission が停止する。D460 の却下理由が前提にしていた
  「index が同一 contract hash の 2 件目を上流で既に拒否しており production では到達不能」は、
  本決定以後は成り立たない。これは事実の記録であって D460 の決定の変更ではない。
- したがって**実 artifact の発行は、consumer 配線より先に行ってはならない**。
  発行だけを先行させると床値 submit の受理集合が空になり、pilot result・レポート・試行台帳が
  新規生成されなくなる。段 6 の独立レビュー 2 本が同じ結論に達した。
- 削除すれば同じ組を再発行できる点、protocol 単位であって run 単位でない点、
  ratified pointer が sanctioned namespace 外を指せる点は D444 の残る限界のまま変わらない。
