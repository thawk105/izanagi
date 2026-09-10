# 段 1 brief — [T-781] 案 A (scheduler spool 証拠の独立取得) の実現可能性調査

## scope と成果物

- **bounded 調査 wave。実装差分ゼロ。** repo へ入るコード・テスト・probe は書かない
  (probe は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t781-spool-feasibility/probe/`)。
- 成果物 = (1) 実測に基づく案 A の実現可能性判定、(2) 択 (A)〜(D) の結果付き再提示
  (裁定パッケージ)、(3) insights 凍結 + spool fragment。**択の決定はユーザーが行う。**

## 確定済みユーザー裁定 (覆さない)

- worklog 404 [T-781]: 「択は保留し調査先行。(A) の実現可能性を測る bounded 調査 wave を起票可 (B 系)」。
  (B) は受理集合の明示拡大、(C)(D) は D86 の明示裁定を覆すため、W-2 稼働中は択を急がない。
- D86 (1)(3)(4)(5)(8) は本 wave では一切覆さない。official の受理集合は空集合のまま。
- 並走ガード 3 条件 (`docs/phase3-8b-restart-runbook.md`): (i) ノード同居なし、
  (ii) T-139 pilot/本走 走行中はキュー投入を控える、(iii) 裁定帯域は A 優先。
  **充足**: 投入直前の `qstat` はいずれも他 wave の受入 dispatch (`izdw-*`) のみで、T-139 の
  pilot/本走 は不在 (先例 = worklog 386)。probe は性能値を採らないため同居は測定を歪めない。
- D86(3)「AI は qsub しない」は floor official の**認可 qsub** に係る。診断 probe と dev harness
  dispatch には及ばない (dev-wave は日常的に `izdw-*` を投入している)。本 wave は
  `submit_floor.sh` を実行しない。

## 実測 (親、2026-08-11、Pegasus login pegasus02)

- M1: scheduler は PBS ではなく **NEC NQSV R1.16** (`/opt/nec/nqsv/bin`)。`/etc/pbs.conf` 不在。
- M2: **`qcat -i <ReqID>` が spool 済み request script を返す** (自分の request、rc=0)。
  → T-781 起票時の前提「独立取得の実装手段が無い」は**誤り**。
- M3: byte 忠実性 = 出力は投入 bytes + 末尾 `\n` 1 個 (2077→2078、2031→2032、先頭部の sha256 一致)。
  非 ASCII 保存。既定は末尾表示のため `-b -n <大>` が必要。
- M4: 保持期間 = **request 消滅後は取得不可** (`[BSV ENOREQ] No such request.`)。事後監査で再取得できない。
- M5: 状態依存 = HLD では **rc=0 のまま空 1 byte**、QUE / PRR / RUN では全 bytes。rc は成功判定に不十分。
- M6: `qstat -f` に script bytes も hash も無い。`-v` で渡した環境変数も出ない。
- M7: `qsub -U key=value` の User Attributes は 40 hex を保持し、`qalter` に `-U` が**無い**
  (`Invalid argument flag: -U`)。一方 **`qalter -N` は成功** = request 名は所有者が事後変更できる。
  script bytes を書き換える qalter option も無い。
- M8 (実行中): 計算ノード上で `qcat` が使えるか (admission は job 内で走るため決定的)。probe 901499。

## 親の provisional 裁定 (P、攻撃対象)

- **(P1)** 案 A は「D86 §4 の独立取得要求を満たす証拠経路」としては**実現可能**である
  (M2/M3/M7)。ただし M4/M5 により、証拠は run 中にしか取れず rc だけでは判定できない。
- **(P2)** 案 A は A-1 の恒真化を**部分的にしか閉じない**。spool bytes は「この request が
  その script で投入された」ことしか言わず、「現プロセスがその script の子孫である」ことを
  言わない。真正 floor job の中の兄弟プロセスは同じ真正 bytes を得られる。
- **(P3)** 逆に、A-2 (revision authority 不在) には **M7 の User Attributes が新しい候補**を与える
  — qsub 時に人間が置き、事後に所有者が変更できない値。これは「新しい Git launch receipt」ではなく
  scheduler 側の記録であり、D86(3) の禁止に直接は当たらない (該当判断はユーザー裁定)。

## 分割方針

段 2 = codex 1 本 (read-only) で案 A の実装面 file:line 素案。段 3 = 敵対 2 レンズで
**親の実測と P1〜P3 の一般化**を攻撃。段 5・6 は実装面ゼロのため飛ばす想定 (段 4 で確定)。
