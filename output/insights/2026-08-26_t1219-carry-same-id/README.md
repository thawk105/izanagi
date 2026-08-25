# [T-1219] worklog carry 検査の同一 ID 化 — 実測と一次資料

D837 (択 c) の実装 wave。`docs/worklog.md` と `docs/archive/` の「次の一手」にある carry stub を、
「参照先 entry が実在する」だけでなく「参照先 entry の次の一手に**同じ ID** が在る」ところまで
検査する。既存違反 4 件は digest 台帳へ登録し、赤にするのは新規発生だけとする。

- branch: `worktree-dev-wave-t1219-carry-same-id`
- base: `d8f777a407d49c32b926fca8f0a0dbe1a74e0194`
- 実装 commit: `03569f58` / 変異 spec: `fa24d393` / ASCII 表示 ID: `bf8bc6f8`

## 1. コーパスの実測 (base d8f777a4、login node)

| 量 | 値 |
|---|---|
| carry 参照の母数 | **404,326** |
| 内訳 | 現行 worklog 2,749 / 採番 archive 401,577 |
| 非採番 archive の carry (検査対象外) | 1 |
| 次の一手トップレベル項目の総数 | 412,401 |
| 次の一手を索引できた entry | 957 (索引値が None のものは 0) |
| 同一 ID が参照先に在る carry | 404,322 |
| **ID 不一致 (既存違反)** | **4** |
| 参照先 key 不在 / 索引 None / 空集合 | 0 / 0 / 0 |

**現行検査は母数の 0.24% しか見ていなかった。** 収集が参照先番号ごとに `setdefault` で
1 件へ潰していたため、実質 957 件しか検査していない。

**probe と production の収集条件は完全一致する (差 0)。** 親が両条件を別々に数えて確認した。
これは段 3 のレンズが指摘した「hard-coded floor と既知 4 件の根拠が実装の受理集合へ
移送できていない」への直接の回答である。

## 2. 既存違反 4 件の実体

すべて `docs/archive/worklog-phase3-0731-77.md` の **entry 77** にある。
参照先はすべて **entry 73** (`docs/archive/worklog-phase3-0731-73.md`)。

| task ID | 形式 | 参照先 |
|---|---|---|
| `[T-208]` | `- [T-208] 変わらず ((73) 参照)` | 73 |
| `[T-209]` | `- [T-209] 変わらず ((73) 参照)` | 73 |
| `[T-210]` | `- [T-210] 変わらず ((73) 参照)` | 73 |
| `[T-211]` | `- [T-211] 変わらず ((73) 参照)` | 73 |

entry 73 の次の一手は `[T-177]` から `[T-206]` までを持つが、**`[T-207]` 以降を 1 つも持たない**。
これが 4 件すべての直接の原因である。

**段 2 プランは source entry を 74 / 76 / 77 / 78 と書いていたが、これは行番号である。**
当該 archive が持つ entry は 77 の 1 件だけで、親が実測で訂正した。
訂正しなければ 4 件とも `expected=1, actual=0` になり、同時に新規違反が 4 件出て実 repo が赤になった。

## 3. 台帳の digest (D837 の既知違反登録)

外側 key = entry 77 の H2 raw 行 sha256
`6bc0dfb4679d3be38c2a97c7c81c595b62a2b033800e5b27d7f9a63b75c3814b`

内側 key = carry 論理行 (list marker を含む raw slice) の sha256、各 1 件。

| task ID | sha256 |
|---|---|
| `[T-208]` | `34209a9f738fe90a9f3cd57531c3ef900085884b79fc6c1dd833fdf3c46ee45c` |
| `[T-209]` | `f46fe17fc7831678f44471bf5c7c460be6bd65bac6a7e5a47cd0535c150a54a6` |
| `[T-210]` | `f5e03b5bb559682274a1731a73e6d4dca0208c7846fabe312cad1834bc74c14e` |
| `[T-211]` | `5e4a6cb7d118a27df5b710ca20351ea9e5e45ef764ed559b597dc9931140b666` |

**凍結 archive の bytes は 1 byte も変えていない。**

## 4. 恒真化を止めた検査の実測

### carry 風 candidate の述語 (偽陽性と取りこぼしの両方向)

| item_text | candidate | 厳密 parse | 判定 |
|---|---|---|---|
| `[T-500] (D837)` | False | False | 正当な項目。赤にしない |
| `[T-500] (Python 3)` | False | False | 正当な項目。赤にしない |
| `[T-500] (953)` | True | True | 正しい carry |
| `[T-500] (073)` | True | False | **捕まえる不正形** |
| `[T-500] (73 )` | True | False | **捕まえる不正形** |
| `[T-500] ( 73)` | True | False | **捕まえる不正形** |
| `[T-500] (0)` | True | False | **捕まえる不正形** |
| `[T-500] 変わらず ((73) 参照)` | True | True | 正しい legacy carry |
| `[T-500] 変わらず ( (73) 参照)` | True | False | **捕まえる不正形** |
| `[T-500] backlog (2 件)` | False | False | carry ではない |
| `[T-500] 実装 (D95) を守る` | False | False | carry ではない |

**厳密 parser の受理集合が candidate 集合に包含されることを全件で確認した (包含違反 0 件)。**
これを壊すと正常入力で `candidate != parsed` が発火する。

段 6 のレビューが入るまで、述語は「括弧で終わり数字を含む」だけだったため
`(D837)` `(Python 3)` を赤にしていた。これは将来ふつうに書いた項目で全 wave の検査を止める。

## 5. 費用 (親の実測)

| 経路 | wall | maxrss | finding |
|---|---|---|---|
| 変更前 `check_docs.py` | 10.52 秒 | 157MB | 0 |
| 変更後 `check_docs.py` | **14.05 秒 (1.34 倍)** | 162MB | 0 |
| 最悪赤経路 (全 carry が不一致) | 12.27 秒 | 133MB | **22 行 / 4,974 bytes** |

最悪赤経路の抑止行は `carry 同一 ID 不一致: 他 404306 件を抑止` で、母数 404,326 と整合する。
**上限に達した後も数え上げは継続する。** 40 万件の finding が常駐する経路は無い。

## 6. 変異 matrix (B-057) — 10/10 KILLED、生存ゼロ

spec は `mutation-spec.json` (sha256 `97e19165b8acb1fafceb97c32d59e03082363f4d9e56f784513cff2e34a28d26`)、
実測台帳は `mutation-ledger.json`。baseline は 552 passed / 3 skipped / rc=0。
repo_head `bf8bc6f8`。

**登録した期待 node は 10 件すべてで実際に落ちた (`expected ⊆ failed` が全件成立)。**

| 変異 | 無効化する層 | status | 失敗 node 数 | 証拠の強さ |
|---|---|---|---:|---|
| M4 | 台帳総数の固定値照合 | KILLED | 1 | **単一理由** |
| M5 | candidate == parsed の同数検査 | KILLED | 3 | **単一理由** |
| M6 | 粗い母数下限 | KILLED | 1 | **単一理由** |
| M9 | universe == index の集合一致 | KILLED | 1 | **単一理由** |
| M10 | 入力不完全時の fail-closed な早期 return | KILLED | 1 | **単一理由** |
| M1 | 同一 ID 比較 | MISMATCH | 10 | 冗長 gate |
| M2 | 未登録不一致を既知として受理 | MISMATCH | 4 | 冗長 gate |
| M3 | 登録 key ごとの観測数照合 | MISMATCH | 2 | 冗長 gate |
| M7 | 索引三分割 (key 不在 / None / 空集合) | MISMATCH | 2 | 冗長 gate |
| M8 | occurrence を target 単位へ collapse | MISMATCH | 12 | 冗長 gate |

MISMATCH は「殺されなかった」ではなく「**期待した node に加えて他も落ちた**」である。
`DW-M03` に従い、過剰決定した 5 件は単独変異の証拠から外す。
中核の層 (同一 ID 比較、occurrence 粒度) は多数のテストが同時に観測するため構造的にこうなる。

**失敗 digest の切り詰めは全件 `omitted_failures=0`。** F220 の再発はなく、失敗集合は完全である。

## 7. 一次資料

`verbatim/` に段ごとの子成果物と親の裁定を逐語で置く。

| file | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief (親) |
| `s2-plan.md` | 段 2 プラン (codex, plan) |
| `s3-consult-sol.md` / `s3-consult-luna.md` | 段 3 敵対相談 2 レンズ (codex, consult) |
| `s4-adjudication.md` | 段 4 裁定とプラン v2、変異事前登録 (親) |
| `s5-author.md` | 段 5 実装子の報告 (codex, author) |
| `s6-review-sol.md` / `s6-review-luna.md` | 段 6 敵対レビュー 2 本 (codex, review) |
| `s6-fix-orders.md` | 段 6 の親の裁定と修正指示 F-1〜F-9 |
| `s6-fix1.md` / `s6-fix2.md` / `s6-fix3.md` | 段 6 fix 3 巡 (codex, fix) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異の事前登録と実測 |

## 8. scope 外として裁定へ返したもの

- 非採番 archive の carry が構造的に検査対象外である件。
  既存テストが `..._is_out_of_scope` という名前で対象外を意図的に固定しており、
  該当は全コーパスで 1 件。D837 は archive 全体への拡張を命じていない。
- 既知違反台帳・固定総数・exact テストを同一 patch で書き換えれば無裁定で緑にできる件。
  既存の `KNOWN_PLACEHOLDER_DEBTS` 族が現に持つ性質であり、本 wave が新設した欠陥ではない。
  塞ぐには承認 receipt か保護レビュー境界という新機構が要る。
- carry 文法を読む他 consumer (fold、land、rulings 収集) と checker の 2 regex が
  一致する保証が無い件。
- F58 型の「同じ ID で内容を差し替える」検査。本 gate は参照先に同じ ID が在るかを見るだけで、
  内容の同一性は見ない。段 3 の 2 レンズが独立に指摘した。
