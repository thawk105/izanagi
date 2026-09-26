T-2322 | 反対: keep にすべき | 本文は D1605 の「24反復」が確定した実規模18・campaign全体22と食い違うと明記する（判定表:201、D1529）。未訂正の実数値を含む記録なので、単なる注記として取り下げると、残す条件の「記録を実際に誤らせた実害」を見落とす。

T-2387 | 反対: keep にすべき | 本文は旧 nodeid 7 件と新 nodeid 17 件の欠落を実数で示し、shard 割当の根拠が現行 suite と食い違うと述べる（判定表:533）。台帳は実際に collection 時の並べ替えへ使われる（`orchestrator/tests/conftest.py:1707,1822`）。関門でないことは、記録と割付根拠の不一致を解消しない。

T-2415 | 反対: keep にすべき | D1818 は probe の申告 status と生の returncode・stdout・stderr の再導出不一致を、競合下の測定を正しい床値として通す実在経路と判定した。現行 `floor_pair_driver.py:2419-2452` は内部整合だけを検査して status を返しており、B-4 の対照対 driver に残る穴である。

T-2453 | 反対: keep にすべき | `Genome.canonical()` は flag 名を区切り文字の検査なしに連結し（`orchestrator/campaign/model.py:141-144`）、その値を現行 pipeline が identity に使う（`orchestrator/campaign/pipeline.py:145`）。D1907 は別の割当を同一視しうる認証入口の欠陥として局所拒否を決定している。実害の実測だけを理由に drop するのは規律2の現行経路を外す。

T-2459 | 反対: keep にすべき | A-2 の partial・full materializer は再導出した report と `dict ==` で比較したままである（`orchestrator/campaign/paper_story_a2_certification.py:4692,4803`）。D1904 は `True == 1` により JSON 型だけ違う偽造 report が certified 成果物として通ると明示し、直接呼出し境界も対象にしている。規律2・6に直結する。

T-2840 | 反対: keep にすべき | 本文は削除後の到達不能 object 13 件について「台帳 hit 0」と rescue gate `rc 2` を確認し、pending 記帳と再検査を未了の手番としている（判定表:2710）。bundle への退避は喪失リスクを下げるが、既に生じた台帳欠落と未確定の rescue 判定を完了にはしない。

## 総括

第2部の **275項**を読み、生データとの本文一致も全件確認した。反対は **6件**。最も重いのは **T-2459、T-2453、T-2415** で、いずれも現行の認証・測定経路に残る穴を指す。brief の **P1** は実測済みの誤記録を拾う基準として有効だが、規律2・6に直結する穴まで実害の実測を必須にすると狭すぎる。**P2** も、追加防壁の整理には使えても、これらの裁定済み局所修正を一律に取り下げる根拠にはならない。