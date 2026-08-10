# 段 6 レビュー裁定と親の自己是正

2026-08-09 / レビュー C (測定器の正しさ) と D (裁定の誠実さ) を受けた親の裁定。

## must-fix の裁定

| # | 所見 | 裁定 | 是正 |
|---|---|---|---|
| C-1 | 段 4 の負制御事前登録「decoy loop は C1 が殺せない」は実装と矛盾。`len(loops)==2` により decoy は必ず赤 | **real・採用 (親の誤り)** | 負制御表を訂正。C1 は decoy を**殺す**。段 4 §3 の記述を撤回 |
| C-2 | C3 の 2 番目 node は「全走査」を検証しておらず、gate が即 `return None` でも緑 | **real・採用** | C3 の主張を「当該 subclass への直接 `__getitem__(slice)` 検出」へ格下げ |
| C-3 | B2 は自ファイル scope と専用環境へ隔離が必要 (未導入環境では collection error が他候補を巻き込む) | **real・採用** | 候補 matrix は 1 候補 1 ファイル scope で実行 (`run_candidates.sh`)。実施済み |
| C-4 | sibling import が import mode に暗黙依存。C1 が誤った `REPO_ROOT` を掴むと全 mutant を SURVIVED と誤判定しうる | **real・採用 (自己検証で担保)** | C1 の事前登録は 14/14 KILLED。誤束縛が起きれば全件 MISMATCH として顕在化する。結果で判定する |
| C-5 | 候補ごとの一意 scratch/out と終了時 byte 照合が未確認 | **real・採用** | 候補ごとに `scratch-cand-<stem>` と `mutation-ledger-cand-<stem>.json` を分離。終了時に byte 照合を実施 |
| D-1 | V1「現行本番では一度も呼ばれない」は issuer 経路と未 land の serial 2 を落としている | **real・採用 (親の誤り)** | §「V1 の訂正」で書き換え |
| D-2 | 9 択への平坦化がユーザーの問い (A 対 B2) を薄めている | **real・採用** | パッケージ本文を **A 対 B2 の二択**に戻し、A′/B1/C1/C3 を対照実験、D/E/F/integration pin を併用可能な付録へ分離 |
| D-3 | B2 の frontier は `@example(64)` が単独で決めており、PBT 一般の効用ではない | **real・採用** | 「これは Hypothesis で包んだ bounded sweep の評価であり、shrinking や多軸探索を含む PBT 一般の評価ではない」と明記 |
| D-4 | 恒久コストが大幅に未計上 | **real・採用** | コスト表に「測っていないコスト」の節を作り、列挙する |
| D-5 | D を「将来候補」とだけ書くと、本番編集禁止が結論を現状維持へ誘導した事実を隠す | **real・採用** | D は「禁止により未測定。不採用ではない」と前面に書く |

## V1 の訂正 (親の誤りの訂正)

**誤 (段 4 §0):** 「現行本番では遷移検査が一度も呼ばれない。」

**正:**

1. **main の現在の checkout では、定常 loader は遷移検査を呼ばない。** activation record は
   `00000001.json` の 1 件で、`env_contract_activation.py:395` の `if previous_rows is not None`
   に入らない。
2. **発行 tool の publish 経路は今日でも遷移検査を発火させる。**
   `tools/issue_env_contract_activation.py` は候補 serial 2 を既存 chain に足して
   同じ `validate_activation_records()` を通す。
3. **実 serial 2 は既に存在し、land 待ちである。** commit `677d0952`
   (branch `worktree-dev-wave-t657-t660-g2-activation`、main 未取り込み) が
   `00000002.json` (linux-baremetal g1 / pegasus g2) と head=2 を作っている。
   これが land すれば遷移検査は**毎回の load で発火する**。
4. **ただしその実 edge は本変異族に対して安全側である (親が実確認)。**
   変化 env は pegasus 1 個だけなので `changed` は 1 要素で、`changed[:N]` は全 N≥1 で恒等。
   `successor_rows[:1]` は変化 env を取りこぼして `changed` を空にし、no-op 拒否
   (`:293`) を引く。これは**誤受理でなく誤拒否 (fail-closed)** である。

したがって現状維持の正しい根拠は「遷移検査が呼ばれないから」ではなく、
**「現行および直近で land される入力は M=2 であり、直接 `[:N]` 族で誤受理を作れる余地が無いから」**である。
「呼ばれない」を根拠に使うことは撤回する。

## C1 負制御表の訂正

段 4 §3 は「C1 が殺せない形」として (i) 事前 slice、(ii) `del changed[N:]`、(iii) decoy loop を挙げた。
実装を読んだ結果、**(iii) は誤り**である。C1 は `len(loops) == 2` を assert するため decoy を殺す。
さらに (i)(ii) も `_preloop_slice_rebindings_or_deletes` が検出する。

**C1 が実際に殺せないのは**、レビュー C が構成した次である。

- `limited = successor_rows[:N]` のように**別名へ代入**し、loop は元の名前のまま body 内で絞る
  (alias 代入は検出対象外)
- `islice` や helper 呼出しで実効集合を縮め、見た目の 2 loop を保つ
- 関数冒頭に `return None` を置いて 2 loop を到達不能にする

**C1 が誤って殺すのは** (偽陽性): 変数 rename、`tuple(changed)` 化、helper extraction、
診断用 loop の追加、到達不能な nested function 内の同名 loop。

## 実施する追加測定

- C1 の負制御は **親の in-memory 測定器**で実施する (dispatch 不要)。
  上記の「殺せない形」3 種と「誤って殺す形」5 種を、C1 の判定関数へ直接かけて表にする。
