## 🚀 Lệnh chạy

```bash
./build.sh && python3 -m pytest -v --timeout=3 tests/test_parser.py
./build.sh && python3 -m pytest -v --timeout=3 tests/test_lexer.py
./build.sh && python3 -m pytest -v --timeout=3 tests/test_ast_gen.py
```
## REQUIREMENTS

```build.sh
Turn CRLF to LF
```

```ANTLR
install ANTLR extension directly to the Docker project to successfully compile .g4 files
---
