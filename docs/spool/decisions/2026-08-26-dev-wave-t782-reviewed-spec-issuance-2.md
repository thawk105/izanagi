---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t782-reviewed-spec-issuance
seq: 2
---

## {{D:spec-issuance-waits-for-ratified-freeze}}. 査読済み spec の凍結発行は批准凍結の発効まで着手しない

**決定:** 判定用 schedule の権威を査読済み凍結 spec に置く実装 (候補 producer と durable 発行の
lifecycle) は、共有 8b ratified freeze が active になるまで着手しない。D840 の向き
(査読済み spec を凍結成果物として先に作り、CLI は指紋照合だけ行う) は維持し、不採用にしない。
着手順序だけを後ろへ送る。

**理由:**
- D959 は 8b の閉塞を依存の層として記録し、schedule authority の無条件 raise を最上流に従属する
  下流症状と位置づけ、順序を入れ替えて先に解除してはならないと定めた。本決定はその順序規定を
  査読済み spec の発行へ適用したものである。同 decision は共有 ratified freeze だけが
  最上流と独立に進められる別線だと明記しており、そちらが先である。
- 候補 bytes を読む production consumer が repo 内に 1 つも存在しない。manifest builder・
  driver・report・judge・verdict はすべて固定 path の bytes を承認 loader 経由で読み、
  producer の戻り値や標準出力を読む呼び手は無い。D841 が名指しした「受領証はあるが誰も読まない」
  型を新規に作ることになる。
- 凍結対象の binding identity は生成 site 依存である。source digest は cxx と環境に依存すると
  実装自身が明記しており、生成 site と実走 site が異なれば実走時の再実体化と一致せず拒否される。
  どの site の identity を凍結するかを決めずに凍結すると、再現しない値を権威にする。
- 実装しないことによる成果物影響は無い。承認 pin は不在、durable spec は 0 件、
  official manifest は 0 件のままで、certified 選択・レポート・台帳の値は 1 つも変わらない。
  実装した場合に増えるのは休眠 capability と休眠 test state だけである。

**却下した選択肢:**
- **候補 producer だけ先に land する** — consumer 不在のまま生成器を置くことになり、
  生成 site 依存と trust root 迂回の穴を抱えた実装が先行する。
- **durable 発行の lifecycle だけ先に land する** — 承認 pin が不在である限り承認済み側の枝は
  一度も実行されず、発火条件を artifact path でも計測 ID でも書けない。
  条件付き機能の発火 gate が禁じる形である。
- **裁定の向きごと取り下げる** — 親が承認済み裁定を不採用にすることは許されない。
  新事実を添えてユーザー再裁定へ返すのが正しい経路である。

## {{D:spec-axis-classified-by-binding-layer}}. 査読済み spec の各軸は導出可否でなく拘束層で分類する

**決定:** 査読済み spec の各軸を「repo 内権威から導出できるか」で二分せず、
**どの層がその値を拘束するか** (spec の schema validator か、実走時の driver か、どちらでもないか)
で分類する。設計文書・brief・実装 prompt はこの分類で書く。

**理由:**
- 二分法は誤った安心を生む。実行環境タグ・時計数・環境契約 hash・CCBench pin は
  spec validator では型しか見られず、任意値が通る。拘束は driver 実走で初めて起きる。
  「導出できる」と書くと、schema を通っただけの値を権威と誤認する。
- 逆向きの誤りも起きた。別 module の承認凍結表を、その表を強制していない consumer の権威として
  引用すると、無裁定の受理集合縮小を既成事実にする。実際に oracle spec の承認経路 positive
  fixture は、floor protocol の凍結 4 行とは別の値を意図的に通している。
- 拘束層で書けば、schema 検証を通るが実走で必ず拒否される spec を作る経路が設計時に見える。

**却下した選択肢:**
- **導出可否の二分を維持し、註記で例外を書く** — 例外註記は読み飛ばされる。
  分類そのものを拘束層へ変えないと同じ誤りが再発する。
