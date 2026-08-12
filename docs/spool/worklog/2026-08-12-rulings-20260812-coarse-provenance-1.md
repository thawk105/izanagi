---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: rulings-20260812-coarse-provenance
seq: 1
title: 45 件を一括裁定した — 論文主張は生成物と概ねの時期で足りる新前提で bytes 級 provenance 系を見送りへ、正しさゲート系は不変 (docs のみ、branch worktree-rulings-20260812-coarse-provenance)
---

## 本文

- **ユーザー裁定 (2026-08-12、/rulings セッション)。** 前提の逐語: 「この研究ではどのような
  CC 自動合成システムでどのようなものが生み出せたかを論文で主張する。論文中でソースコードや
  git commit id まで言わないからさ。生成が大体どのくらいの時期で、ソースコードではこのくらいの
  時期でくらいが分かれば良い。少なくともこれは言える」。この前提で引き直した推奨 45 件 + 横断提案
  (基準の決定化と仕分けへの適用) を「推奨通りでよろしく頼む」で一括確定した。
- **適用境界。** 下げたのは「過去の成果物の bytes 同一性を守る機構」の価値だけであり、規律 1〜3・
  正しさゲート (verifier / admission / 変異検査)・測定の公正 (同条件比較・環境契約タグ) は不変。
  基準の正本は {{D:coarse-provenance-standard}}。
- **経緯。** 収集は worklog 末尾 (459) 時点で裁定待ち 45 件 + ユーザー手番 5 件 + 未 push 249 commit
  を索引化。premise 変更で 11 件の推奨が反転した (bytes 級 provenance 系が見送りへ)。
  一次控え (全 45 件の索引・択・確定内容) =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-coarse-provenance-45rulings.md`。
- **収集後の並行 land との突き合わせ。** 記録時点で main は (462)。(460)〜(462) の新規項のうち、
  旧「floor-campaign-clone-cost」(収集時は未採番として索引 #40 で承認済み) は land 済みと判明したため
  同項も本裁定の更新に含めた。承認範囲外の新規 (機序の近い提案を含む) には触れない — ただし
  全履歴走査除去の新提案の親推奨 (a) は本裁定の方向と矛盾しない (個別確定は次回 rulings)。
- **land はしない。** 「rulings の land は区切りで束ねる」裁定と先例「一次控えは rulings-inbox、
  fold は別 wave」に従い、受入 lease を争う稼働 wave を妨げない。fragment は本 branch に commit し、
  fold dry-run で base digest の整合を検証済み。
- **docs-only 受入免除判定の証拠**: 本 wave の変更は `docs/spool/` の fragment 2 本のみ
  (判定手順 = `git diff --name-only main` が docs/spool 配下のみを示す)。実装面ゼロ、該当 nodeid 不存在。
- **ユーザー手番の控え (裁定でなく操作)。** hook 信頼の承認 + rc=0 確認を先に。仕様承認のハッシュ記入・
  実凍結手番・公開版承認は仕分け wave で「使う機構」が確定した後にまとめて 1 回。origin へ未 push
  249 commit。

## 次の一手差分

### 更新

- [T-816] **P1・裁定済み (2026-08-12 /rulings、{{D:coarse-provenance-standard}}) → 手順 4 wave 起票可**:
  Q1 = trace は v2 専用とし、赤になる凍結 v1 証拠テスト 4 本は退役する (歴史記録は日付級の 1 行)。
  v1 読み手の hash 束縛例外機構は作らない。Q2 = 検査で現用の校正 pin だけを新 gitlink で機械的に
  再 pin し、未使用は退役する。恒久の同一性証明機構は作らない。前段の乗せ直しは省略し、push 済み
  `511c9538` へ直接前進する ([T-837] Q1 (a) を本裁定が上書き)。
  正本 = `output/insights/2026-08-12_t816-step4-blockers/README.md`
  base: b816bc25de6823056cebd695618a8dfd586370c92e9875455350d28c6aec35e5
- [T-837] **P1・裁定済み (2026-08-12 /rulings) → 乗せ直し不要で終端**: [T-816] Q1/Q2 の裁定により
  `c9c1a9c` の乗せ直しを省略し `511c9538` へ直接前進する。Q1 (a) 旧裁定は上書きされた。
  残るユーザー手番なし。
  base: b2898a746276a7ca47f1f495614f56a116695208fd2851bac05d2f3b7dd08a8d
- [T-793] **P2・裁定済み (2026-08-12 /rulings) → R3/R4 のみ実施、R1/R2 は保留終端**: R3 (公表 core v2
  §8.1 の偽命題の訂正) と R4 (marker gate の保証範囲の記録。書式の規範化は [T-864] と同梱せず
  記録のみ) は実施する。R1 (source 側の本走 gate) と R2 ((i) の原子性・`(root, ordinal)` 一意性・
  予約 writer) は {{D:coarse-provenance-standard}} により保留終端 — 公表層の残り実装は論文粒度の
  主張に不要。再訪条件 = 外部公開で proof chain の提示が必要になったとき。
  正本 = `output/insights/2026-08-11_t793-pubcore-impl/package.md`
  base: bf550d7e849f3f7635ae8e4fb5765a5badc2cbfebaccccbcc49ae97468d97368
- [T-139] **P1・裁定済み (2026-08-12 /rulings、2 束) → land 2 は完了 land 可、pilot は投入経路 wave で**:
  第 1 束 = pilot/本走の投入禁止を Q3 (b) から切り離して解除。追補 P の blob 凍結は実施しない
  (値の承認 `p01`/`α_pub` は不変)。第 2 束 = land 2 session 2/3 の残問を確定 —
  Q1 (受理述語の入力欠落 4 件を閉じる decision) と Q2 (approval manifest の新表現) は
  {{D:coarse-provenance-standard}} により**機構を新設しない**。Q4 = scope を組み替え、投入の実務経路
  (`submit_pilot`・PBS driver・collector) + D292 を上書きする解除 decision + 束縛検査だけを
  1 session・同一 land で組む (解除 decision だけ先に land しない)。Q5 = 段 8 候補 3 件は機械化移管を
  先に試し、散文の残余のみ既開の独立審査束へ。Q6 = (a) S6 (a) を維持し可視性は repo 外控えで担保 —
  Q1/Q2 の見送り確定で待ちが消えるため、land 2 は現土台 + Q4 scope で完了 land できる。
  正本 = branch `worktree-dev-wave-t139-manifest-w2` の
  `output/insights/2026-08-11_t139-manifest-land2-s2/package.md`、一次控え = rulings-inbox の
  `2026-08-12-t139-land2-s2-five-rulings.md` / `2026-08-12-coarse-provenance-45rulings.md` /
  `2026-08-12-second-batch-11rulings.md`。
  base: 17290cdd8d0c915a1d8561d030280223120ce4638f3b042c999f0c76cb7f8463
- [T-748] **P1・裁定済み (2026-08-12 /rulings、(c)) → 実装 wave 起票可 (Codex author)**: 投入 script
  (`tools/pegasus/floor_campaign.sh`) へ pilot 経路を追加し、official 受理集合は空集合のまま維持する
  ([T-781] Q1 は不変)。`eligible_for_refreeze=False` も緩めない — W-2 床値は pilot 計測として実測し
  insight に記録する (再凍結への昇格は別裁定)。
  base: ce926217ac02c9d7ffbd6809c2040c6d362483973fcbf76dad615eec25fea047
- [T-871] **P1・裁定済み (2026-08-12 /rulings、{{D:coarse-provenance-standard}}) → 見送りで終端**:
  S-3 (a) の attempt 実測値の脚は実装しない。再訪条件 = 外部公開で証跡提示が必要になったとき。
  base: bfbad7f7691f0934bb7d6682269f803a8c0b18c40358946cd086608fa22ff417
- [T-872] **P1・裁定済み (2026-08-12 /rulings、同基準) → 見送りで終端**: 成果物への binding report は
  載せない。exact-key consumer の改修も行わない。
  base: 2d637491aad8d3f972b6a3cdbeba691353b6ba2a370d6a1242bab39e587ecb5e
- [T-873] **P2・裁定済み (2026-08-12 /rulings、同基準) → 見送りで終端**: cxx version / cmake path /
  module_list / bytes hash の authority への追加と calibration 再発行はしない。
  base: 2fcb30a43b3982ddd82c80fc457a216e357651f8f0fd74a55214c002f5b59feb
- [T-874] **P2・裁定済み (2026-08-12 /rulings、同基準) → 見送りで終端**: 束縛は floor と silo ladder の
  まま他 producer へ広げない。
  base: 1ac3494639b161bdae76bf65b4c130e0df1505c5520dfb56edff790943a7e833
- [T-868] **P2・裁定済み (2026-08-12 /rulings、同基準) → 受容で終端**: 承認 receipt への署名と外部
  trust root は導入しない。`/limitations/approval_receipt_trust_root_absent` の機械可読宣言を正とする。
  再訪条件 = 外部公開時。
  base: c065034873a3a3fb4b88ac04d12ef47f76d9b2ede3afd1eaea97bcf12e25b022
- [T-864] **P3・裁定済み (2026-08-12 /rulings、同基準) → 終端**: canonical decision への機械可読
  target schema の必須化はしない。marker gate の保証範囲の限界記録は [T-793] R4 が行う。
  base: 95689764fe4547fc3bb9587248b498f5ecbb606ffdbbcf142e562806d0734975
- [T-316] **P1・裁定済み (2026-08-12 /rulings、R-1 = (b)+(c)) → 実装 wave 起票可 (Codex author)**:
  build 段防壁は (b) build 出力 copy-out の厳格化を次 wave で実装し、(c) land 済み lexical 効果 gate を
  defense-in-depth として併置する。(a) DSL/IR 化は不採用 (sort の raw 経路が残る)。[T-840] の機械隔離を
  同一 wave に含める。実装段の残り blocker ([T-184] canonical stage matrix、R3-3〜R3-9、R2-b) は不変。
  正本 = `output/insights/2026-08-11_t316-semantic-gate-impl/package.md`
  base: d1128a0cd4cdc7a29ed2d96d288d8117f836d0dfdb80f888d69735ce7f3ee74a
- [T-840] **P2・裁定済み (2026-08-12 /rulings) → 機械隔離を採用**: `quarantine()` を通らない
  coder-derived build 経路 5 本を admission 外の非認証成果物として機械隔離する。[T-316] (b) と同一 wave。
  base: 1fbf0378025349a39512e984bed8af122395d65a106b4b8c72a66e1fbefe7270
- [T-841] **P2・裁定済み (2026-08-12 /rulings) → receipt 束縛を採用**: cache / WAL / COMMIT / freeze へ
  semantic gate receipt を束縛し、scanner を経ない binary の cache hit 混入を塞ぐ。R3-3 / R3-9 の後に実装。
  base: e8878bbfc3922644d9eed5502cd579ff21fe8f4f67d11f0823a84167e4f131f1
- [T-842] **P3・裁定済み (2026-08-12 /rulings) → 削除**: 恒偽の `forbidden_identifiers` を
  producer / consumer / schema の 3 箇所から削除する (段 6 レビュー推奨どおり)。
  base: fae03833389d0b980d3ad5a495de382641b83ae3a90f81c0c6091de296e935b6
- [T-513] **P2・裁定済み (2026-08-12 /rulings) → exact 比較へ**: admission の `.strip()` 比較を
  exact 比較へ変える。[T-515] と同時に、既存走行への影響を実測してから land する。受理集合を狭める方向。
  base: 520eecbb2b05b86034ca15426abbdb3541ff8d43a0a4948fd68307a0725f28fc
- [T-515] **P3・裁定済み (2026-08-12 /rulings) → [T-513] 実施後に再判断**: exact 比較の導入で
  重複 reject variant が消えるかを実測してから、reject key 導出の変更要否を決める。
  base: eaff1debd0bfbd5e4d6ed67d137915a97b6b07734699af90061dfbc088fdd33d
- [T-419] **P1・裁定済み (2026-08-12 /rulings、(b)) → 世代列照合へ**: 凍結 protocol の contract hash
  pin は世代列への照合 ([T-478] A′ 機構と同型) へ変える。実装は世代交代を実際に行う wave へ同梱
  (優先度下げ)。残る blocker (iv) 例外集合の空化の依存関係は不変。
  base: 41cd3ac150dc53f6d328e7d00369ec14087dbcc68341e291400a9f4de0357149
- [T-184] **P1・裁定済み (2026-08-12 /rulings) → 実測先行**: 段別の所要時間・失敗率の実測一覧を
  作ってから resource envelope の択一を再提示する。reasoning 面 (D266) は不変、retry policy は
  [T-183] 依存のまま。本項を他タスクの待ち解除根拠にしない規定も不変。
  base: d99a05907af4a35bacac1cfcdae503600070110d590c65b09ce93f8a8c749379
- [T-244] **P2・V-6〜V-10 の裁定順を確定 (2026-08-12 /rulings) → V-8 先行**: V-8 (物理実行を
  1 query = 1 campaign run にするか、費用 33 倍) を先に単独裁定する — 起票側は費用の内訳を添えて
  再提出する。V-10 (evidence writer の権限分離) は「分離しない・現状記録」を既定にする
  ({{D:coarse-provenance-standard}})。V-6 / V-7 / V-9 は V-8 の後。V-6〜V-10 の裁定まで結線実装 wave を
  起票しない原則、発行 3 条件 0/3、本番 authority entry 0、閉じた成果層 0/11、D114 上限 1 は不変。
  全体状態の正本 = (287) と `output/insights/2026-08-07_t244-8c-wiring-design/s4-adjudication.md` §6。
  base: ef459b1a23dd226dd60529cccfc1dadd1e3a6fc1ba279049b9df150788fd54ab
- [T-725] **P2・裁定済み (2026-08-12 /rulings) → 許可 + 配線 3 点**: 受入 lease 取得後の behind main は
  待ち手内 `--no-ff` merge で解消してよい。安全配線 3 点 (merge 失敗時の lease 即時返却を含む) を
  必須とし、runbook §7.3 の改訂は実装 wave 所有。memory の暫定運用を正式化する。
  base: 64f457f3c1e20c1207cf583eeee2bc164bfc6c512a305465cd0ccd45ddbe59a6
- [T-694] **P3・裁定済み (2026-08-12 /rulings) → 共通化**: 受入 lease 待ち手を `tools/` の正本 wrapper
  (`acquired` 検査・`trap` による確実な release・周期固定) にする。[T-725] と同一 wave (Codex author)。
  base: af86669b311311552c85c199d2ae8f4001bebd56f8acfb0846bb6447daeaaa1e
- [T-881] **P2・裁定済み (2026-08-12 /rulings) → 実測して分岐**: 変更 file 焦点走 1 本追加の増分時間を
  実測し、10 秒未満なら (b) 段 6 受入へ追加、以上なら (c) `DW-O18` の焦点走規定強化。
  正本 = `output/insights/2026-08-12_t860-test-red/package.md` R2。
  base: 593e1e397f3fc1a200a8a0a237a69049c6d9571aa1b4ac907d9696458b161837
- [T-880] **P2・裁定済み (2026-08-12 /rulings、(b))**: `_load_rotate_limit` の依存は対象 repo の
  `tools/` を import 文脈へ束縛する形で解決する。正本 = 同 package.md R1。
  base: d6d9f296d9209d4ca08f59a1ca0beea64344e2ff25b0886c599933fc991f6444
- [T-855] **P2・裁定済み (2026-08-12 /rulings) → 両方実施 (Codex author)**: 2 行の NFC 正規化と、
  「tracked file の非 NFC 行は赤」の機械検査の `tools/check_docs.py` への追加を両方行う。
  base: 42ed3944575fc53dcf27b5bd0a47d9dd7e49947241418f056056f3b72fd9ad71
- [T-709] **P3・裁定済み (2026-08-12 /rulings) → 枠を新設**: 波及の広い正例向けに部分集合一致
  (期待 node が実測失敗集合に含まれる) の判定枠を設ける。spec に部分一致を選ぶ理由の明記を必須とする。
  base: f66766eceb4c85e0fab044c54d8025e4de1525207aa1f58cc1fd80a23cb12ff0
- [T-594] **P2・裁定済み (2026-08-12 /rulings) → reference 側を直す**: guard は触らず、`DW-O01` 系の
  記載を実挙動 (launcher script を wave 専用 subdirectory へ書いてから起動する形) に合わせる。
  追記 bytes は [T-508] 裁定の余白造成後に入れる。
  base: ac0f8201e01d275c9de4c72cf66a1b9055b24ed81a5a16b786d3b4618d251412
- [T-508] **P2・裁定済み (2026-08-12 /rulings) → (b) 主 (a) 従**: docs/dev-wave 予算は機械検査・
  ツール化への移管 (b) を主、陳腐化削除 (a) を従として余白を作る。(c) 予算の独立審査は開かない。
  安全義務の削除はしない。[T-620] [T-778] [T-845] [T-875] の受け皿。
  base: 13073513712b4863bf148fc261518c65260da0b9bb0d67b3d7c5925b26ec2dd0
- [T-620] **P3・裁定済み (2026-08-12 /rulings) → ハーネス側へ移管**: `--runner-mode` の経路要求と
  spec / out の置き場は docs 追記でなく変異ハーネス側の機械検査にする ([T-508] (b))。
  base: 534a996abdd100ae51f26d865d12a9e3728a1a70d6b9a7b577d9530850d720c9
- [T-778] **P3・裁定済み (2026-08-12 /rulings) → ハーネス側へ移管**: 期待 node の完全一致と走行範囲の
  絞りの注意は runner 側の検査・警告にする ([T-508] (b))。`DW-M08` への追記はしない。
  base: 4a550f9e4e6c3d3a29deb381b7d2992129340e9358d5c22d2342eacb57589826
- [T-845] **P3・裁定済み (2026-08-12 /rulings) → ツール側へ移管**: `--artifact-root` の親 dir 取りと
  `<root>/<wave>/<job-id>` の事前作成は `dev_wave_codex.py` 側の自動作成 + 明確なエラーにする。
  `DW-O01` への追記はしない ([T-508] (b))。
  base: c8051333245cd1c48d191477718bd24414d908dc5bcb4f77fc988091531cad77
- [T-875] **P2・裁定済み (2026-08-12 /rulings) → ツール側へ移管**: 段別 argv 契約の検証は launcher が
  投入前に `--dry-run` 相当を自動実行して弾く形にする。`DW-O01` への追記はしない ([T-508] (b))。
  base: c85a3ce5f2d98c8ec0cde26556dad70bb82edaaf3804397e48aca6a695dec167
- [T-687] **P2・裁定済み (2026-08-12 /rulings) → 受容で終端**: xdist internal error / pre-item crash の
  診断項目は増やさず、既存 xdist summary を正本と定める (プロトタイプ基準)。
  base: 1c660b7356efd005d449ca77a87e0d82b214c0e6055e299b0fa34c0d9a7d7800
- [T-688] **P2・裁定済み (2026-08-12 /rulings) → 採用**: job wrapper 側に durable checkpoint /
  partial-log path を作り、SIGKILL・OOM・walltime 打ち切り・起動前 rc=16 の診断ゼロを塞ぐ。
  base: 48ba5381386362866ef87fef6b93b3d926cd4157c11b4285aff66801d0fdc098
- [T-689] **P3・裁定済み (2026-08-12 /rulings) → 受容で終端**: best-effort の中継を正とする。
  耐久経路も手順追記もしない (プロトタイプ基準)。
  base: 4ad28a9e1d3776f2a7e7fc45d23cfabdc103febdc834333ae04668fd49df751c
- [T-691] **P3・裁定済み (2026-08-12 /rulings) → 受容で終端**: failure stash の module global は
  現状維持 (経路実在未確認、回帰 pin 維持)。
  base: d400efb23d24d22fab3aaed240d0781ab9432d0e601b6b09cf00cd1e239f75f4
- [T-679] **P3・裁定済み (2026-08-12 /rulings) → 受容で終端**: 早期 receipt は置かない (プロトタイプ基準)。
  base: b8b4adc48ef32477e35daa2b6755b65357fcb5fa49c2cc6c68bcb699cb395513
- [T-680] **P3・裁定済み (2026-08-12 /rulings) → 表現規約を採用**: 不在の証明はしない。記録は
  「N 回連続緑。不在は主張しない」の正直形に固定する (規律 3 整合)。
  base: 5eb7616e739fa590fd24f0eaad91fabf55ce58d100b39684e76d877d1220d523
- [T-884] **P2・裁定済み (2026-08-12 /rulings) → 直す**: `_find_rollout` の全履歴 JSON parse
  (履歴比例走査) を除去する方向を承認。収集後に land した具体提案の親推奨 (SHA pin を持つ label に
  限る fast path、pin 無しは全走査維持) は本裁定と同方向で矛盾しない — 個別確定は次回 rulings。
  base: 7cc4538a0f84141f0b5c93c063bf8fa273ab52ff491998bfd4bbaceb33d34265
- [T-885] **P3・裁定済み (2026-08-12 /rulings) → 軽い複製へ**: 隔離の保証が変わらないことを確認の
  うえ `--no-checkout` / hardlink 等の軽量形へ変える。[T-893] と同一裁定 (同型 2 箇所)。
  base: 65f1ab4a325575e794844d2f5c565362a8d5c97b4f269a8cdee04f9adc99434b
- [T-893] **P2・裁定済み (2026-08-12 /rulings) → 軽い複製へ**: [T-885] と同一裁定。E2E の repo 全体
  clone は隔離意味論の確認つきで hardlink / `--no-checkout` 側へ (実装 wave、Codex author)。
  base: 93f15e2d923409c0affa43a256d2fc6bd99f3f8d8dbd06376703147b24ae4a85
- [T-511] **P3・裁定済み (2026-08-12 /rulings) → 規定追加**: runbook §7.0 へ初回走行の規定 (未計測
  script の 1 走目は保守的見積りで計算ノードへ) を足す。汎用 dispatch task は作らない。
  base: cf9405e559f2e8f6ca97e1a76e311bc1d796c74b26537579aee3fb0a8621cde0
- [T-751] **P2・裁定済み (2026-08-12 /rulings、{{D:coarse-provenance-standard}}) → 見送りで終端**:
  窓限定の現状を受容し checkpoint 連鎖は作らない。再訪条件 = 外部公開で監査地平の提示が必要に
  なったとき。
  base: 35eac470e2a682f0f72cde2e23ca721f94f4f979e3c392904067fd8e1d16dc16
- [T-777] **P3・裁定済み (2026-08-12 /rulings) → lint の結線のみ採用**: 住所構造 lint を受入経路で
  走らせる形だけ入れる。偽 edge (Markdown 意味解釈) の対処は却下維持 (`DW-G03` 独立 2 例まで)。
  base: 4b12c21687406a005b088f0acc61e0fd30dfbddfba150fa913f9cbc379967533
- [T-530] **P2・裁定済み (2026-08-12 /rulings) → パッケージ化要求**: 読み出し境界の残件 6 問は択一の
  形の裁定パッケージにしてから再提出する ([T-674] 所有)。{{D:coarse-provenance-standard}} により
  provenance 専用の問は落ちる見込み。
  base: a9828a01828870e125f1ebd57d87ea9eef3550947b02d30e2821d6602b5887d6
- [T-499] **P2・裁定済み (2026-08-12 /rulings) → 仕分け wave 起票可**: 三値分類の基準に
  {{D:coarse-provenance-standard}} を適用する (provenance 系の項は既定で見送り側へ)。129 件 +
  本裁定で終端化した項の退役実務 (見送り台帳への移動) も同 wave が担う。凍結手番系のユーザー操作は
  仕分けで「使う機構」が確定した後にまとめて 1 回とする。
  base: 9ee8836756032443f71ad4d54d5d66e124e66b98c8061a5e8c8cf7828d903fc7
