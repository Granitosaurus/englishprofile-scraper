# EnglishProfile.org scraper

Small scraper to collect word data from <https://www.englishprofile.org/wordlists/evp>

Install:

```
$ pip install git+https://github.com/Granitosaurus/englishprofile-scraper.git
```

run:

```
$ englishprofile-scraper --help
Usage: englishprofile-scraper [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  discover  discover word previews from word pagination
  worddata  collect word data from discovered word previews
$ englishprofile-scraper discover
$ cat englishprofile.json
...
$ englishprofile-scraper discover
$ cat worddata.json
...
