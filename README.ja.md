# pytest-esp32-lib

[English README](README.md)

`pytest` を使って ESP32 の Arduino スケッチをテストするための、最小構成のライブラリ兼サンプルプロジェクトです。

このリポジトリには大きく 2 つの要素があります。

- `addTest` という非常に小さな Arduino ライブラリ
- `pytest`、`pytest-embedded`、`arduino-cli` を使った `tests/` 配下のテスト環境

目的はフレームワーク提供ではなく、次のような用途の実用的なひな形を置くことです。

- `pytest` から Arduino スケッチをビルドする
- ESP32 実機に対してハードウェアテストを実行する
- `esp32` や `esp32s3` のような Arduino CLI の profile を切り替える
- Wi-Fi 資格情報のような環境依存値をテストスケッチへ渡す

## 関連リポジトリ

Arduino ライブラリではなく、通常の Arduino スケッチプロジェクトを対象にした姉妹リポジトリもあります。

- `pytest-esp32-ino`
  https://github.com/tanakamasayuki/pytest-esp32-ino

どちらから見るか迷った場合は、まずこの `pytest-esp32-lib` から見るのがおすすめです。  
ライブラリ構成の方がきれいで、共有コードを `src/` からそのまま参照できるため、テスト側の構成も素直になります。

一方で `pytest-esp32-ino` は、Arduino IDE でそのまま開ける `.ino` プロジェクトを前提にした例です。  
その場合はアプリ側コードをスケッチディレクトリに残す必要があるため、`tests/` 側で `.h` / `.cpp` を参照する薄いラッパーが必要になり、少し泥臭い構成になります。

## 構成

- `src/`
  Arduino ライブラリ本体
- `examples/`
  ライブラリの最小サンプル
- `tests/`
  Python テスト環境、実機用スケッチ、実行スクリプト、ローカル設定

`tests/` 配下には次の runner スケッチがあります。

- `esp32_serial_runner`
  Unity を使わず、シリアル出力だけを確認するテスト
- `esp32_unity_runner`
  Unity の複数テストを実機で実行するテスト
- `esp32_wifi_runner`
  Wi-Fi 接続して IP アドレス取得を確認するテスト

## 必要なもの

- Python 3.13 以上
- `uv`
- `arduino-cli`
- シリアル接続された対応 ESP32 ボード

付属の `sketch.yaml` を使う場合、ESP32 Arduino core を事前に手動インストールしておく必要はありません。

Python 側の依存関係は `tests/pyproject.toml` で管理しています。

## テスト環境

`tests/` は独立したテスト用ワークスペースです。

主なファイル:

- `conftest.py`
  build/test の共通ロジック
- `pytest.ini`
  `pytest-embedded` と `pytest-html` の既定設定
- `run.*`, `run_build.*`, `run_test.*`
  Linux/WSL と Windows 向けの実行スクリプト
- `clean.*`
  生成物削除スクリプト

## テスト実行

### Linux / WSL

ビルドとテストをまとめて実行:

```bash
./tests/run.sh
```

ビルドのみ:

```bash
./tests/run_build.sh
```

テストのみ:

```bash
./tests/run_test.sh
```

WSL でビルドし、その後 Windows 側でシリアル実行:

```bash
./tests/run_wsl.sh
```

### Windows

ビルドとテストをまとめて実行:

```bat
tests\run.bat
```

ビルドのみ:

```bat
tests\run_build.bat
```

テストのみ:

```bat
tests\run_test.bat
```

## 主なオプション

このプロジェクト独自に使っている `pytest` オプションは次の 2 つです。

- `--run-mode=all|build|test`
- `--profile <profile-name>`

例:

```bash
./tests/run.sh --profile esp32s3
./tests/run_test.sh --profile esp32s3 tests/esp32_unity_runner/test_unity_runner.py
```

`--profile` を省略した場合は、各スケッチの `sketch.yaml` にあるデフォルト profile を使い、生成物は `build/default` に出力されます。

## シリアルポート指定

シリアルポート指定は、独自実装ではなく `pytest-embedded` の標準機能に任せています。

使用できるのは次のいずれかです。

- `--port`
- `ESPPORT`

例:

```bash
ESPPORT=/dev/ttyUSB0 ./tests/run.sh
```

```bat
set ESPPORT=COM5
tests\run.bat
```

## ローカル環境変数

テスト環境では次の dotenv ファイルを読めます。

- `tests/.env`
- `tests/.env.local`

これらはあくまでデフォルト値で、すでにシェル側に設定済みの環境変数は上書きしません。

サンプルは次にあります。

- `tests/.env.example`

例:

```env
TEST_WIFI_SSID=your-ssid
TEST_WIFI_PASSWORD=your-password
```

## ビルド時 define

一部のテストスケッチでは、環境変数の値をビルド時 define として渡します。

例えば `tests/esp32_wifi_runner/build_config.toml` では、環境変数名と Arduino 側 define 名の対応を定義しています。

```toml
[defines]
TEST_WIFI_SSID = "TEST_WIFI_SSID"
TEST_WIFI_PASSWORD = "TEST_WIFI_PASSWORD"
```

この対応では:

- 左辺が読み取る環境変数名
- 右辺がスケッチのビルド時に渡す `#define` 名

ビルド時には `conftest.py` が現在の環境値を解決し、`arduino-cli` に `--build-property` として渡します。

## レポート

HTML レポートは次に出力されます。

- `tests/report.html`

レポートの Environment セクションには、使用した Arduino sketch profile が表示されます。

実行スクリプトは通常、毎回新しい実行前に古い `report.html` を削除します。

## クリーンアップ

`tests/` 配下の生成物を削除するには:

```bash
./tests/clean.sh
```

```bat
tests\clean.bat
```

これにより build フォルダ、キャッシュ、仮想環境、ログ、HTML レポートが削除されます。

## 補足

- このプロジェクトは、重い抽象化よりも単純で明示的な runner を優先しています。
- Wi-Fi 資格情報はソースへコミットせず、環境変数またはローカル dotenv から与える想定です。
- ライブラリ本体は最小のまま維持し、環境依存の動作確認は `tests/` 配下の専用スケッチで扱います。
