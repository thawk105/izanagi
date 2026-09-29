---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-gc-connection-prototype
seq: 2
---

## {{D:vhash-gc-connection-prototype}}. Cicada の forwarding を GC の回収境界へつなぐ構成 E は、待機の安全点で GC flag を立て、前進に成功したときだけ時刻と読み取り下限を公開する。tx の途中で読み取り下限を最新の値へ上げない

**決定:** VHash 論文の構成 E (`patches/cicada-forwarding-gc.patch`、md_6 の patch の上に重ねる) を次の仕様とする (一次資料 `output/insights/2026-09-29/vhash-gc-connection-prototype/README.md` §2)。
1. 読み取りの後に待つ tx は、待機を slice (100 µs) に分け、各 slice 末の安全点で「GC 間隔経過 ∧ 自分の GC flag が 0」なら GC flag を立てる。安全点では回収 (gc_versions) を走らせない。
2. E はそこで前進を試す。t′ は自 thread の clock から作る厳密に新しい時刻。手順は md_6 と同じ事前確認 → 既読版の rts を t′ へ CAS-max → seq_cst fence → 版列を観測し直して可視を確認 → 確定 (D2290 の G2・G3)。
3. **前進に成功したときだけ**、確定の後の別 step で ThreadWtsArray := t′、ThreadRtsArray := max(旧, t′−1) を公開する (D2290 の G4)。失敗したとき、および対照 E-hb では、ThreadWtsArray・ThreadRtsArray を tx 開始時の値のまま変えない。
4. 3 macro (`CICADA_GC_SAFEPOINT`・`CICADA_GC_WAIT`・`CICADA_GC_COUNT`) を条件 gate の許可ドメインへ登録し (D2288 と同じ足跡、所有外だが必須)、`patches/ledger.json` には載せない。md_6 の patch は変えない。
5. 比較は md_11 の観測最良の Cicada 設定で行い、待機型の長い tx は skew {0.9, 0} の両方で測る。主比較は E 対 E-hb (前進と公開だけが違う組)。

**理由:**
- stock Cicada で tx の既読版を物理的に守っているのは「ThreadRtsArray = tx 開始時の MinWts−1 を tx の間変えない」ことで、これが回収境界を tx 開始後に確定しうる後続版の wts より小さく保つ。安全点でこれを最新の MinWts−1 へ上げると、待機中に t0 より前の時刻で既読 key を上書きした確定版より古い既読版が回収・再利用される (実測: 保持版検査で 3,938 件中 159 件)。前進に成功した後は「既読版と t′ の間に確定版も pending も無く、t′ 未満の writer は rts で止まる」ので t′−1 までの公開が安全。
- 待機中の worker が GC flag を上げないと leader は公開できない (stock で 3 秒あたり約 290 回)。flag だけ (E-hb) で公開は再開するが、境界は長い tx の開始時刻に張り付く。前進が成り立つ skew 0 では E が境界の遅れを約半分にした。
- skew 0.9 では「今」への前進が既読不一致でほぼ失敗し、E と E-hb が同じになる。skew 0 は CCBench 論文 §7.2 の長い tx の実験と同じ条件である。

**却下した選択肢:**
- 安全点で読み取り下限を最新の MinWts−1 へ上げる (段 4 の仮裁定 P5) — 上記のとおり既読版を回収させる。
- 安全点で gc_versions も走らせる — tx の途中で版の再利用 pool に触れ、前進の効果の測定にも要らない。
- 待機位置を write の前へ移す — md_6 の前進は未設置の書き込み版の時刻も書き換えるので不要で、腕の間で workload が変わる。
- md_6 の patch を直接更新する — md_6 の検査・図の記録がその patch の hash に束縛されている。
