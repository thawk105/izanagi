---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2757-mocc-mutation-proof-design
seq: 2
---

## {{D:mocc-mutation-proof-design}}. mocc の auditor-live 相当の機械実証は、温度述語を proof の接続先候補とし、既存防壁の保存と発火範囲を実測する設計にする — 設計完了は探索・pin 前進・軸採用のいずれも認可しない

**決定:** D579 が mocc の変異探索面化に要求する「独立の auditor-live 相当の機械実証」の設計を、
`output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` を正本として次の形に固定する。

1. **hole の接続先候補 = 温度述語** (`cc/mocc/transaction.cc` の 4 site `read_internal` / `update` / `delete_record` / `construct_RLL` の
   `loadepot.temp >= FLAGS_temp_threshold` を file-scope helper の 1 hole に括る、契約 = 4 site で同じ温度分類、読取契約 = 温度と閾値の
   値渡しと定数だけ)。これは proof の接続先候補であり、正式な変異軸の採用 (axis-onboarding の段階 A / B) ではない。
2. **安全論拠は「既存防壁 (validation・CLL/RLL・X/P 計装・write_set_ 登録) を骨格で固定し、その保存と発火範囲を実測する」に限定する。**
   「hot/cold は正しさの入力ではない (torn read は validation で必ず捕まる)」は定理として置かない — stock mocc (RWLOCK 版) には
   版と counter の別読みによる観測間隙と、hot 読みの `absent` 非検査という静的反例候補が残る (実走未確認、還元判断はユーザー確認待ち)。
3. **証拠を経路共通部分と template 依存部分に分ける。** 経路共通 = 固定 producer (`e9e477ca` + 計装 patch) 上の X/P、hot / cold / 既定の
   3 regime × 1 / 4 thread、既存負例 3 本、hot 専用負例 (update の早期 w_lock 直後に unlock、publish 前に `rwlock_.w_lock()` で直接再取得する
   balanced 形、blind UPDATE 1 操作の workload)。template 依存 = 4 callsite、読取契約、DiffQuarantine 対照、template に関する同一性 3 比較 (旧 pin↔候補の D297 比較は別 T)、auditor の mocc 節、
   n=1 定性、template sha。軸が変わったら依存部分だけ再検証する。
4. **hot 経路の実行証拠は負例の発火で示し、計数行は足さない。** 保証名は「stock 等価述語における hot-update 負例の到達と既存 X 3 検査点の検出」に
   固定し、4 site 全被覆・read 側 hot 経路・RLL 再試行・候補ごとの空振り検査を含意しない。
5. **36 走の matrix は受入必須と観測のみに二分し、必須走だけを check に対応させる。** T-2294 の driver・JSON・14 check・patch sha は歴史的結果として
   保持し、新 driver・新 JSON に記録する (旧 JSON に無い field を旧証拠へ要求しない)。n=1 定性は機械 `all_pass` に入れない。
6. **gate の鍵は「mocc の template (EVOLVE-BLOCK marker) または軸定数 module の登録」とし、既存の `EVOLVE_BLOCK_SOURCES` 所属は使わない**
   (mocc は D579 で既に所属しており前件が常時 true になる)。加えて mocc の mutation consumer が実際に使う source / template / PIN と proof JSON の
   束縛を consumer 導入時テストで検査し、別名 template・軸 module なし・別 PIN の対照を置く。任意の直書き経路を機械的に閉じたとは主張しない。
7. **I 行 (write-intent) は本 gate に含めない。** 根拠は許可された述語の作用範囲 (値渡しの純粋述語は write_set_ を変更できない) と固定骨格にあり、
   write_set_ 登録行の侵食は DiffQuarantine の対照に含める。I absent と write-intent 未実証は明記し、D1603 の pin 手続きを省略する根拠にしない。
8. **後続は 2 wave に分ける。** wave 1 = 経路共通の実証 (template 不要、新負例 + 新 driver + 36 走 + 登録簿閉包)。wave 2 = template 接続の実証
   (前提 = wave 1 完了 + 軸の A / B。template + 軸定数 + 計装 patch の `#line` 再生成 + auditor の mocc 節 + DQ / consumer 束縛の対照 + gate test +
   n=1 の 3 候補)。
9. **非解禁。** 本設計の完了も、後続 2 wave の緑も、mocc の変異探索・pin 前進・certified 比較の開始を認可しない。探索開始は D579 の証拠、
   pin 手続き (D1603 / D297 / D2114 項 3)、producer の proof surface (pin 候補へ X/P 計装をどう載せるか) が揃ってからの別判断である。

**理由:**
- D38 決定 4 の auditor live (機械 4 点 + n=1 定性 2 点) のうち、mocc は X/P の被覆 assert と positive control が T-2294 (D1686) で patch 水準で済んで
  いる。純増は hole 位置、hot / cold の実行証拠、auditor 入力、gate の鍵、n=1 であり、これらは D579 / D38 / D1686 の再掲では固定できない。
- T-2294 の compute 6 走には hot/cold を弁別する field がない。1 thread で温度述語が false と見なせるのは code からの推論であり実測値ではない。
  4 thread の hot 到達は未確認である。
  `FLAGS_temp_threshold` は runtime gflag なので、0 / 21 で hot / cold を強制でき、負例の発火で実行証拠を機械化できる。
- 段 3 レンズ A が親 brief の「torn read は validation で必ず捕まる」を現物で反証した: cold 読みは counter 検査 → body 読み → 版の再読の順で、
  validation は版比較の後に counter を読む。writer の publish + unlock がその間に入ると両検査を通る。Silo は lock bit を tidword に同居させるので
  この隙間が無い。これは stock の性質であり、D2114 が未確定とする mocc の G2 anomaly の根因候補になりうる。安全論拠を「既存防壁の保存」に限定する
  のはこのためである。
- 段 3 レンズ B が「proof 用 template と正式な軸の境界」「同一性の 4 比較と `#line` 整合」「36 走と check の対応」「gate の執行範囲」を must-fix に
  挙げ、いずれも実装者が再設計する必要のある未確定だった。2 wave 分割は template 無しで今すぐ投げられる部分を先に固める。
- Silo の gate (`test_lock_path_edit_surface_requires_auditor_live`) は EBS 所属を前件にするが、mocc は trace-hook 用に既に所属している。
  所属を鍵にすると trace-hook 用の所属と変異面の導入を区別できない。

**却下した選択肢:**
- **「hot/cold は正しさの入力ではない」を根拠に温度述語を安全な変異面と宣言する** — 上記の観測間隙により証明が成立しない。
- **温度上昇則・`lock()` の `vioctr > 100`・abort の backoff を hole にする** — 契約と被覆証明が大きい / 既存 workload で stock 枝の実行証拠を得にくい /
  Silo の D48 とほぼ同型で mocc 固有性が薄い。
- **hot 経路の計数 line を trace に足す** — helper 呼出回数は hot 側の選択や lock 成功を示さず、verifier の parse も触る。負例の発火の方が空振り
  (型 4) を直接閉じる。
- **I 行を mocc の gate に含める** — Silo の機械 4 点より強い gate になり、固定骨格と DQ 対照で write_set_ 登録の侵食は塞げる。
- **旧 driver の 14 check を拡張して JSON を再生成する** — 歴史的結果の書換えになる。新 driver・新 JSON で参照する。
- **`SOURCE_REL == "cc/mocc/transaction.cc"` だけで全 module を探索する gate** — 既存の診断 driver が同じ定数を持ち偽陽性になる。
- **チェックリストの再掲として実証 wave の plan 段へ統合する** — 上記の純増があり、設計を正本として残す方が後続 2 wave の入力になる。
- **`docs/phase3.md` を編集する** — 準備 T の進捗は worklog 末尾が正本 (2026-09-17 改訂 (5))。

**この決定が主張しないこと:** stock mocc の観測間隙と `absent` 非対称が実走で再現すること (静的反例候補にとどまる)、read 側 hot 経路・RLL 再試行・
DELETE 経路の動的被覆、mocc が certified な第 2 例として成立すること、温度述語が正式な変異軸として承認されること。
