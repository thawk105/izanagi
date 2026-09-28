---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-forwarding
seq: 2
---

## {{D:vhash-forwarding-protocol-v2}}. Cicada の選択的 forwarding は read 相だけで前進し、最終保証を stock の validation に置く

**決定:** VHash 論文の試作 (`patches/cicada-forwarding-variant.patch`) の forwarding は次の仕様とする (一次資料 `output/insights/2026-09-29/vhash-forwarding-prototype/README.md` §2)。
1. 発火は `read()` 経由の read だけで、T.ts で見える版の物理位置 (pending / aborted を含む) が先頭から K 版より奥のとき。scan・read-only・特殊操作後は発火しない。
2. 前進先は先頭 K 版の最古の committed 版の wts より大きい、自 thread 形式の最小の ts'。
3. 前進前の確認 (既読版が ts' でも見えるか、write set の制約、pending に当たらないか) は早期判定であり最終保証ではない。rts は書かない。
4. 成功時は T.ts・localClock_・未設置の書き込み版の wts を ts' にし、read / write set の探索開始位置 (`later_ver_`) をすべて捨てる。失敗時は何も変えない。
5. validation 以降は変えず、stock の validation を最終 ts で走らせることを最終保証とする。GC の保護 (ThreadWtsArray / ThreadRtsArray) は旧 ts のまま据え置く。
6. 比較対照 F は同じ発火条件で abort して新しい ts で再実行する。

**理由:**
- Cicada の validation は wts_ だけをパラメタにし、既読版が最終 ts で見える版と一致しない限り commit しない。前進を validation の前に限れば、reader と writer の順序付け (rts を先に上げる / pending を先に置く) を stock のまま使える。
- 旧 ts で得た探索開始位置を残すと、検証が最終 ts より古い位置から辿り、その間に commit された版を見落とす (段 3 の反例)。未設置版の wts を書き換えないと、設置版の時刻と tx の時刻が食い違う。
- GC 保護を動かさないので、旧 ts で読んだ版も前進先で読む版も回収されない (保守的)。GC の前進はメモの段階 5 に分ける。

**却下した選択肢:**
- 前進時に既読版の rts を先に書く — 共有書き込みが増え、validation の順序付けで足りる。
- 最新版を読み max(wts) を採る — 既読の可視区間の上限を確かめられない (メモ §10)。
- pending 版を待ってから確認する — 前進の判断で待つと、失敗時に戻る先の費用が読めない。待たずに「競合」として元の ts へ戻す。

## {{D:vhash-forwarding-registration}}. forwarding patch は条件 gate に登録し、patches/ledger.json には載せない

**決定:** `patches/cicada-forwarding-variant.patch` の 3 macro (`CICADA_FWD_ENABLE`・`CICADA_FWD_COUNT`・`CICADA_LONGTX`) は `orchestrator/campaign/condition_meaning_gate.py` の許可ドメインへ登録し
(先例 3867e6ec5 と同じ足跡、判定・受理述語と既存 entry は不変)、`patches/ledger.json` には entry を足さず `patches/README.md` の節で登録する。macro 名に `IZANAGI_` 接頭辞を使わない。

**理由:**
- patch が新しい `#if` を持ち込むと、patch の define 一覧と許可ドメインの完全一致を求めるテストが接頭辞に関係なく赤になり、build する driver は gate の supply / meaning を通す必要がある。登録しないと patch を置けない。
- `patches/ledger.json` は `silo_ladder_rung1` 専用で、契約 (`silo_ladder_rung1_contract.py` の ledger 検査) が entry 1 件を要求する。依頼文の「ledger の entry」とはこの点で食い違い、契約を優先した。
- 接頭辞なしは合成 variant の命名慣行 (`BACKOFF_FIXED`、`MOCC_TEMP_PREDICATE`) に合わせたもので、gate 登録が必須なので検査を逃れる効果は無い。
- gate 登録は依頼の所有範囲の外だったが、段 3 の 2 レンズとも「必要最小の登録に限れば賛成」で一致し、自分の 3 entry と連動する件数・起動一覧の登録だけに限った。

**却下した選択肢:**
- ledger の entry 数契約を緩めて追加する — 別件の契約変更で、本試作の研究前進に不要。
- 専用 manifest を新設する — 成果物の値・受理集合を変えない新しい検査で、DW-G05 に反する。
- patch を patches/ 以外に置いて検査を避ける — 検査逃れであり D18 の inert patch 方針から外れる。
