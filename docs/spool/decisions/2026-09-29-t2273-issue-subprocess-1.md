---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: t2273-issue-subprocess
seq: 1
---

## {{D:t2273-issue-subprocess-land}}. 受入 shard-0 の律速 (b) 発行 subprocess は、三軸走査の正規表現照合を軸 literal の出現近傍の窓に局所化する係数削減 (report の bytes は不変) で縮め、実受入の隣接 3 対で事前登録の区分 (ii) = 小さい改善として land する。E1 は系列途中で shard-0 の割付一致に限定する erratum にした。5 分上限は B の W_max 中央値 276.1 秒で達成

**決定:**

1. 発行 child (約 86 秒) の CPU の 99 % を占めた `s8b_holdout_freeze.search_repository` の `_scan_one` を、D512 の枠内で係数削減する。軸 literal L (既存 `_derive_required_literal` の 1 要素 mapping 導出、非 None のときだけ) の各出現 p を重なりも含めて列挙し、同じ compiled 式を窓 `[max(0, p + len(L) − W), min(len, p + W))` で search する (W は stdlib `sre_parse` の `getwidth()` の最大値)。共通 literal の判定は 1 回の `search_repository` 内で (literal, rel) ごとに 1 回とし、既存の `_ScanMemo` の identity 束縛・内容変化拒否の後で、判定した text object と `is` で一致するときだけ再利用する。L が None・非 exact str の式は従来の全文 search。report の canonical bytes・受理集合・列挙と読取と例外・発行 child 内の走査回数は変えない。
2. 既存の発火回数の番人 (D513) は、数える単位を「局所化 helper に届いた (軸, text) 候補数」に移して数値 (5 / 0・5・9 / reference 3 回) を保ち、三段分離 fixture に局所化だけを外した段を足す。production に最適化無効化 knob を足さない。
3. 事前登録の land 判定 (隣接 3 対、A = local main `51f896352`、B = A + 実装 `ad8c91ecf`): shard-0 W_0 の対差 +32.333 / +40.457 / +16.512 秒 (3 対すべて正)、対率中央値 9.136 % で区分 (ii)。事前登録どおり小さい改善として land する (出力等価な変更で検出力の喪失が無く、目標値は合否判定ではない)。
4. 事前登録 E1 の erratum E1' (9/29 07:29 JST、01-A・02-B の後、W を閲覧する前に固定): 新設 8 node が所要時間台帳に無く shard-1 / 2 の分割を変えたため、旧 E1 (A/B 共通 node の 3 shard 割付の完全一致) は A/B の木で決まる性質として成立しない。land 判定量 W_0 を決める shard-0 の共通 node 集合 (4,302 件) は完全一致しているので、割付一致の要求を shard-0 に限定した。旧 E1 での判定は `undetermined` として並記する。
5. 5 分上限は別判定で達成: B の W_max 3 走の中央値 276.108 秒 (349.375 / 259.260 / 276.108)。02-B は shard-1 が最遅で 300 秒を超えた。

**理由:**

- 律速の実測 (計算ノードの単独走 py-spy): 走査 1 回 ≈ 6.6 秒 × 約 13 回で、fixture は計算ノード /tmp 上なので D512 が実 repo で測った律速 (共有 FS の metadata 遅延) ではなく正規表現照合が支配していた。係数削減の対象が D512 のときと違う。
- 窓式は、helper が非 None を返す文法では全 match が L を含み長さ ≤ W で anchor・lookaround が無いので、全文 search と真偽が同じ。段 3 の相談 A は反例を構成できなかった。変異 final (M1 右端・M2 左端・M3 重なり・M5 cache key・M7 identity は KILLED、M4 局所化の除去・M6 共通判定 memo の除去は出力等価の診断 pin) は期待と完全一致。
- 走査回数を減らす案 (validate の内包重複・draft の verifier 走査の共有) は観測点を減らすので、受領証の検査内容を変えないという依頼の条件に反する。
- E1' について、賛成側は W_0 を担う shard-0 の同一 test 集合という比較に要る性質が保たれることを、反対側は系列開始後の基準変更であり shard-1 / 2 の構成差が W_0 に間接的に効きうることを挙げた。分割を揃えた新系列は B の実装 commit を変えて系列をやり直す必要があり、揃う保証も無く、承認済みの計算上限を超えうる。付帯条件 (旧 E1 の並記、host 重なりの報告、W_1・W_2・pre の対差を効果と呼ばない) を付けて採った。

**却下した選択肢:**

- 走査結果を呼出しを跨いで cache する — D512 が memo を 1 回の呼出しに閉じると定めている。
- MAXREPEAT (無限幅) の分岐と注入 test — 現行 helper の受理文法では到達せず、幅が飽和しても窓が全文に広がるだけで結果は正しい (段 3 の相談 B、段 4)。
- E1 を維持して系列を無効にし、分割を揃えた B で新系列を取る — 上の理由。
- 03-B (無効になった対 2 の 1 回目) を採用する — 集計器の文法どおり赤の走を含む対は対ごと取り直す。
