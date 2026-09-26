---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: t2838-gate-argv-unify
seq: 1
title: [T-2838] 択 A — 受入門番の leader の数え方を argv 先頭一致に統一し、写し元を repo 外の雛形 1 本にした。採用前に走行中の受入 1 本で見逃し 0・誤検出 0 を実測し、採用後の取り直しを択 B 再提示の基準線として記録した (記録 + insight、雛形と記憶は repo 外、branch worktree-t2838-gate-argv-unify)
---
## 本文

- 依頼: D2211 項 4 の択 A の実施 (写し元は `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/`、閾値・周期・lease TTL は変えない、repo に置かない、採用前に argv 一致を 1 回実測、採用後に同じ probe で閉門内訳を取り直す、長い待ちが残っても択 B は採らず材料として記録)。insight `output/insights/2026-09-26/t2838-gate-argv-unify/README.md`。
- 結果: 雛形 `_shared-templates/run-acceptance-gated.sh` を 2026-09-26 14:36:53 JST に設置 (sha256 b30be0fb…、写し元は同日 green の `dev-wave-t2273-shard0-local-copy/run-acceptance-gated.sh` で、3 値と先頭コメントだけ替えた)。記憶 `acceptance-gate-no-workers-threshold` と索引行が雛形を指す。設置前の直近 40 本の門番は部分文字列一致 22・裁定の正規表現 6・狭い先頭一致 12 の 3 系統だった。
- 採用前の一致実測: 14:36 JST に走行中の受入 1 本 ([T-2864] wave、pid 2659242) で、`/proc/<pid>/cmdline` の引数単位の判定と `ps -eo args` への正規表現の一致が同じ集合 (見逃し 0・誤検出 0)。正規表現は `python3 -u` と `python3.10` 起動を数えないが、9/19 以降の起動形に該当は無かった。
- 採用後の取り直し (同じ probe、`--since 2026-09-21 --until 2026-09-26T14:38`): leaders 起因閉門 445 tick (推定 891.9 分) のうち記録上の走行 ≤ 1 は 61 tick (122.9 分、約 13.8%、診断時は約 48.9%)。雛形経由の門番 log は 0 本なので、これは採用効果ではなく基準線である。30 分以上の待ちは 11 区間 (打切り 1)、飢餓候補 1 件。argv 先頭一致の門番にも走行 1 本で leaders=2 の閉門が 17 tick 残り、原因は当時の process 一覧が無く決められない。
- 裁定の扱い: 段 2・3 は軽量版で省いた (設計択一は裁定済み、正しさ防壁と受理集合に触れない)。雛形は既存 script の写しと 3 値の置換だけなので親が作った (段 1 (P1))。repo の実装面の差分はゼロで、変異 matrix は免除 (DW-S04)。
- 異常: submodule 初期化の 1 回目が `update-no-fetch` (既知の 30 秒時間切れ型) で、再走で rc=0。probe の 2 走 (採用前 14:14 頃に 14:25 締め、採用後 14:37:26 開始で 14:38 締め) は締めが実行開始時刻より未来だったので、締めを過去に直して取り直した (採用前 14:14 締め、採用後 14:38 締め。後者は取り直しと bytes 同一だった)。
- 段 6: 独立 read-only レビュー 1 本 (照合 47 行中 41 一致、条件付き GO)。must-fix 2 件 (採用前後の母集合の差の書き方が直近 20 では誤り、記憶に旧来の実装例と数え方が注記なしで残っていた)・should 5 件・nit 5 件を全件 real と裁定して文言を直した。うち should 1 は、再提示に裁定 (D2219 項 5) に無い条件を足していた誤りで、案と条件を書き分けた。
- 工数: Codex 子 0 本 (段 6 の read-only レビュー 1 本は Claude 子)。

## 次の一手差分

### 更新
- [T-2838] **P2・択 A 実施済み → 択 B は条件付きで再提示**: 択 A (leader の数え方を argv 先頭一致に統一、写し元を repo 外の雛形 `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` 1 本にし、記憶 `acceptance-gate-no-workers-threshold` が指す) は本エントリで実施した (D2211 項 4)。
  採用後の取り直し (`output/insights/2026-09-26/t2838-gate-argv-unify/README.md` §4) は雛形経由の門番 0 本の基準線で、30 分以上の待ちは 11 区間残る。
  択 B (他 wave の受入 leader 上限を期間限定で 2) は依頼により今は採らない。D2219 項 5 の条件 (A の後の取り直しで、なお長い待ちが残る) はこの取り直しで満たされうるので、
  次の裁定収集で B を改めて提示する (試すときは待ち・受入 wall・赤率を同時刻対照で比べる)。材料の読み方の案は同 README §5.3。
  base: ca7e03ea10377d6b2dd3f41bf892b2d04fe24571ad1089bd2c5946fb349bd1f4
