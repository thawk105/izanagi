# 段 6 裁定 — レビュー A/B 所見 28 件と fix 指示 (2026-08-04)

## 裁定サマリ

RA-1〜RA-12、RB-1〜RB-16 の全 28 件を **real** と裁定する (refuted 0)。全件 scope 内
(実装・テスト・変異登録の是正)。production 受理集合は依然不変 (未結線・空 authority) のため
ユーザー再裁定は不要。fix は同一ファイル集合に重なるため単一 fix 子へ一枚岩で投入する。

## 裁定に伴う Δ の改訂 (`DW-O12`: 実行手順の正本をここで更新する)

- **Δ2 改訂 (RA-1):** certifiable seal の floor 判定は「**sealed batch で消費した query 数**」で行う。
  tombstoned batch の消費は予算からは引く (no-refund) が floor 充足には数えない。
  これで tombstone のみの certifiable 到達を封じる
- **Δ4 改訂 (RA-2):** 「観測 tail 宣言 + exact request 一致時のみ truncate」を撤回する。
  代わりに: prepare の原子点は「完全 record + fsync 成功」。open 時に完全 record prefix の
  chain を検証し、**未完 tail は無条件 truncate** (ack 前の書き掛けであり依拠者はいない)。
  完全 prefix が破損していれば fail-closed。CAS base は常に prepare 時点の clean commitment B で
  一貫させ、repair 経路でも request の base を書き換えない。tail 状態の commitment 混入 (旧 Δ4) は
  「repair 不能な破損を fail-closed にする」目的にのみ残す
- **Δ10/Δ1 補強 (RA-4, RA-5):** prospective semantic state を含む**すべての pre-seal 永続 bytes と
  commitment は、結果・class の平文に依存してはならない** (salted commitment のみを経由する)。
  salt は 16 byte 以上・origin 内で一意 (batch 間再利用も拒否)・全ゼロ拒否。テスト helper も
  呼び出しごとに distinct salt を使う
- **Δ5 補強 (RA-6):** `origin-opened:` prefix の operation_id を公開 API で予約拒否し、
  genesis を operation index に登録する
- **Δ7 補強 (RA-7, RA-10):** symlink ancestor 検査は runtime root 自身と全中間成分を覆う。
  `_FAULT_HOOK` は fixture store のときだけ参照する (production 経路から構造的に切る)
- **Δ11 補強 (RA-11):** admission に物理 feasibility を足す: codec 定数
  (batch cardinality 上限・class 数上限・record/ledger サイズ) から導ける上限を超える
  Qmax / Kmax / required_q の authority entry は拒否する
- **Δ13 改訂 (RB 群):** 変異登録の是正 —
  M-A3 は fixture を Imax 単独律速 (Qmax 余裕) に変更。
  M-A4 は実効 gate (committed head と ledger 整合検査) へ再照準 (`DW-M01` の再照準を記録)。
  M-A5 は多重拘束 (防御深度) と認め、実効 gate = exact-continuation 比較へ再照準し、
  旧登録は冗長 gate として単独変異証拠から外す。
  M-A6 は fixture の B record も per-origin chain に整合させる。
  M-N6 はテスト側に独立 preimage 再構成 oracle を置く。
  M-N2 は cell 4 要素それぞれの正負例。M-N4 は `batch_cardinality_min=1` の admission 拒否。
  M-N8 は `query_floor_constraints=[]` の admission 拒否。M-N10 は prepared 時点の
  candidate↔result 対応 (順序不一致拒否) に戻す。M-N17 は cross-origin 再利用の負例

## 所見→fix 対応 (fix 子への指示は s6-fix-directives を参照)

| 所見 | fix 要点 |
|---|---|
| RA-1 / RB (V14) | sealed-query floor 判定 + tombstone-only 反例テスト |
| RA-2 | 完全 prefix 検証 + 未完 tail 無条件 truncate + base 一貫 CAS + 修復後 exact replay テスト |
| RA-3 | fsync 失敗は全経路 fail-closed (成功 receipt を返さない・store poison)。event/commit の fsync 失敗テスト |
| RA-4 / RB-15 | pre-seal bytes の平文非依存化 + 「観測者再構成」テスト (平文を除く射影から全 pre-seal bytes を再計算し byte 一致) |
| RA-5 | salt 契約 (長さ・一意・非ゼロ) + テスト salt の distinct 化 |
| RA-6 | genesis op_id 予約 + index 登録 + 負例 |
| RA-7 | ancestor symlink 検査の root 込み全成分化 + V15 負例 |
| RA-8 / RB-6 / RB-13 | fixture 限定 hook による決定論 latch (base 読取後)、cross-process flock 実測 (in-process mutex を迂回する 2 subprocess)、inode 差し替え latch テスト |
| RA-9 / RB-12 | V1 を test 内 literal frame + 独立 sha256 計算へ置換 (production helper 経由禁止) |
| RA-10 | `_FAULT_HOOK` を fixture store 限定 |
| RA-11 | admission feasibility 上限 + 負例 |
| RA-12 / RB-14 | V15 の欠落負例 (missing key、event duplicate/非 canonical/LF、absolute path、ancestor symlink、non-regular file、サイズ上限) を追加 |
| RB-1〜RB-5, RB-7〜RB-11 | Δ13 改訂のとおり fixture / 帰属 / 負例を是正 |
| RB-16 | subprocess.run に timeout、thread join 後の is_alive assert |

## 変異登録の確定版 (fix 後に `DW-M07` の anchor 再検証をして本走)

M-A1, M-A2, M-A3(fixture 改), M-A4(再照準), M-A5(再照準・旧位置は冗長 gate 記録),
M-A6(fixture 改), M-N1〜M-N18 (N2/N4/N6/N8/N10/N17 は上記是正込み)。
正例 3 件は現テストに実在をレビュー B が確認済み (実走は親)。
