# Extension Provider for WizQl

## Purpose

The purpose of this repo is to direct all the reduce api hits to the main servers serving the extension data.
It also provides an list of all the extensions that can be installed on various databases.
Common names include DuckDB and SQLite.

### Features

- This repo provides a mirror to the extensions hosted by various databases in the form of json data.

- A pseudo api for the data.

## Get Started

```bash
pip install requirements.txt

python3 main.py
```

## Online version

[https://razein97.github.io/extprovider](https://razein97.github.io/extprovider)

### JSON Data

- [https://razein97.github.io/extprovider/json/sqlite.json](https://razein97.github.io/extprovider/json/sqlite.json)
- [https://razein97.github.io/extprovider/json/duckdb.json](https://razein97.github.io/extprovider/json/duckdb.json)

Example usage:

```js
const response = await fetch(
  'https://razein97.github.io/extprovider/json/sqlite.json'
);
const extensions = await response.json();
```
