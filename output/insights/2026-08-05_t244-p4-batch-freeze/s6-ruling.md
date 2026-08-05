# 段 6 所見裁定と変異の再登録 — [T-244] P4 batch freeze

対象 = `out/s6-revA.md` (blocker 3 / major 3 / minor 1) と `out/s6-revB.md` (major 3)。**両者 NO-GO**。
親の実測 = 対象 3 file の部分走が計算ノードで **35 passed / rc=0** (request 889289)。
つまり「現行テストは全部緑だが、レビューが指す穴を現行テストが観測していない」状態である。

## 所見別裁定 (すべて real、すべて本 wave の編集面内で fix する)

| 所見 | 判定 | 処置 |
|---|---|---|
| RA-1 / RB-1 (到達不能 floor を受理) | **real (blocker)** | F1: partition 存在検査を入れる |
| RA-2 (runtime-head を origin 横断で会計していない) | **real (blocker)** | F2: authority 全体で合算して拒否 |
| RA-3 (`_affine_batch_bytes` が cardinality の十進桁を無視) | **real (blocker)** | F3: 桁を含む保守的上界へ |
| RA-4 (2249-member commit の公開経路拒否が未検査) | **real (major)** | F4: 正例 2248 / 負例 2249 を公開経路で |
| RA-5 (旧 2-event tombstone 経路の再導入を検出しない) | **real (major)** | F5: unknown event 拒否 + 型不在の構造検査 |
| RA-6 (M-9/M-10/M-14/M-16/M-18 が偽の kill 対) | **real (major)** | F6 + 親による変異再登録 (下記) |
| RA-7 / RB-3 (テスト名が row proxy を query accounting と呼ぶ) | **real (minor/major)** | F7: 改名 (Δ10 の未履行分) |
| RB-2 (三値 matrix の不正セル 3 件が未固定) | **real (major)** | F8: 3 負例を追加 |
| RB-3 の `six_event_transition_matrix` 陳腐化 | **real** | F5 に含めて改名 |

refuted はゼロ。両レビューとも「seal 前 privacy は保たれている」「独立 golden は自己参照でない」
「codec 数値 2248 と byte 数は独立再計算と一致」「consumer 取り残しは 0 件」を**反証できなかった**と
報告しており、この 4 点は親も採用する。

RA-6 が指摘した「同一 wire の水増しは ordinal が止めるのではなく正しく番号付ければ通る」は、
**裁定済みの残余** (Δ10、A-1 本体は scope 外) であり新規 blocker に数えない。レビュー A 自身も同じ扱いにしている。

## 変異の再登録 (`DW-M01` / `DW-M04` / F28)

段 4 の登録のうち 5 件は単一理由性を満たさないと判明したので、**登録前に再照準する**。
偽の kill 対のまま本走して KILLED に数えることはしない。

| # | 変異 | 期待 node | 備考 |
|---|---|---|---|
| M-1〜M-8 | 段 4 のまま | V17 / V16 | レビュー A が観測性を確認済み |
| M-9′ | opening cardinality 検査**と** query partition 検査の**両層同時**除去 | V18 | 冗長 gate ゆえ両層変異。`DW-M04` に従い kill 期待を事前登録 |
| M-10′ | **codec/reducer 共有の outcome closure** を除去 (「reducer 専用」の名乗りを撤回) | V18 | 帰属を実装構造へ合わせる |
| M-11〜M-13 | 段 4 のまま (M-13 は evidence tamper のみ単一理由。outcome tamper は二重不一致なので登録から外す) | V18 | |
| M-14′ | floor 式を `sealed_queries` から `sealed + tombstoned` へ変える (弱化方向) | V14 改訂 + F8 の floor 負例 | 旧 M-14 は過剰拒否変異だったので破棄 |
| M-15 | 段 4 のまま | V20 | |
| M-16′ | committed member payload へ**実 ordinal を載せて replay まで受理させる** | V20 | anchor を実装後に確定する |
| M-17 | 段 4 のまま | V21 | |
| M-18a | qmax を単一 batch へ戻す退行 | V21 / V14 | 旧 M-18 を 3 分割 |
| M-18b | per-batch runtime cardinality guard の除去 | F4 の負例 | |
| M-18c | ledger-total byte guard の除去 | F3 の境界負例 | |
| M-19 | partition 存在検査の除去 | F1 の到達不能 floor 負例 | |
| M-20 | origin 横断の head 合算検査の除去 | F2 の 2-origin 負例 | |
| M-21 | 桁を含む byte 上界を旧 affine へ戻す | F3 の境界負例 | |
| M-22 | unknown event type (`batch-tombstoned`) の拒否を除去 | F5 の負例 | |
| M-23 | accepted + constraint の拒否を除去 | F8 | |
| M-24 | rejected の evidence 必須を除去 | F8 | |
| M-25 | tombstoned + constraint の拒否を除去 | F8 | |

**恒真 residual (段 4 のまま。KILLED に数えない)** — 実 query 一対一 / seal 前の外部漏洩 /
referent 実在 / `"provider" not in source` の 4 件。

## fix 後にやること

1. 親が対象テスト + meta-test を計算ノードで再走。
2. `DW-O16` の焦点再レビュー (所見ごとの closed / partial / regressed 表を要求)。
3. `DW-M07` に従い最終 commit で anchor を再検証してから変異 matrix を本走。
4. 受入全走 → 段 7 記録。
