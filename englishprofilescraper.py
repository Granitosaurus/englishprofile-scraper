import asyncio
import json
from pathlib import Path
from typing import List, TypedDict, Union
from urllib.parse import urljoin

import asyncclick as click
import httpx
from parsel import Selector


class WordPreview(TypedDict):
    baseword: str
    guideword: str
    level: str
    partofspeech: str
    topic: str
    url: str


class WordSense(TypedDict):
    definition: str
    label: str
    dict_example: str
    learner_example: str
    learner_example_cite: str


class WordData(WordPreview):
    pronunciation: str
    word_type: str
    senses: List[WordSense]


def discover() -> List[WordPreview]:
    body = """filter_search=&filter_custom_Topic=&filter_custom_Parts=&filter_custom_Category=&filter_custom_Grammar=&filter_custom_Usage=&filter_custom_Prefix=&filter_custom_Suffix=&limit=0&directionTable=asc&sortTable=base&task=&boxchecked=0&filter_order=pos_rank&filter_order_Dir=asc&ce91224c5693e21d15ac97cc105e6520=1"""
    resp = httpx.post(
        "https://www.englishprofile.org/wordlists/evp",
        headers={"content-type": "application/x-www-form-urlencoded"},
        content=body,
        timeout=httpx.Timeout(30.0),
    )
    sel = Selector(text=resp.text)
    data = []
    for row in sel.css("#reportList>tbody>tr"):
        data.append(
            {
                "baseword": row.xpath("td[1]/text()").get(),
                "guideword": row.xpath("td[2]/text()").get(),
                "level": row.xpath("td[3]/span/text()").get(),
                "partofspeech": row.xpath("td[4]/text()").get(),
                "topic": row.xpath("td[5]/text()").get(),
                "url": row.xpath("td[6]/a/@href").get(),
            }
        )
    return data


async def scrape_word_page(word: WordPreview, session: httpx.AsyncClient) -> WordData:
    url = urljoin("https://www.englishprofile.org/", word["url"])
    resp = await session.get(url)
    sel = Selector(text=resp.text)

    word["word_type"] = sel.css(".pos::text").get("").strip()
    word["pronunciation"] = sel.css(".written::text").get("").strip()
    word["senses"] = []
    for sense in sel.css(".info.sense"):
        word["senses"].append(
            {
                "definition": sense.css("span.definition::text").get("").strip(),
                "label": sense.css(".label::text").get("").strip(),
                "dict_example": "".join(
                    sense.css(".example p.blockquote ::text").getall()
                ),
                "learner_example": sense.css(".learnerexamp::text ").get(),
                "learner_example_cite": sense.css(".learnerexamp span::text ").get(),
            }
        )
    return word


async def scrape_words(words: List[WordPreview], filename: Union[str, Path], con_limit=4, batch_size=12):
    """
    Update word previews with full word data

    Parameters
    ----------
    words:
        iterable of word previews to update
    filename: 
        where to save the data
    con_limit: 
        concurrent connection limit. This website is runnin on small instance of Joomla CMS - keep this low! 
    batch_size : int, optional
        decrease for low memory systems.
    """
    limits = httpx.Limits(
        max_connections=con_limit, max_keepalive_connections=con_limit
    )
    with open(filename, "w") as f:
        f.write("[\n")
        async with httpx.AsyncClient(limits=limits) as session:
            for i in range(0, len(words), batch_size):
                print(f"scraping [{i}:{i+batch_size}]/{len(words)}")
                batch = words[i : i + batch_size]
                full_words = await asyncio.gather(
                    *[scrape_word_page(word, session=session) for word in batch]
                )
                f.write(
                    ",\n".join(
                        json.dumps(full_word, ensure_ascii=False)
                        for full_word in full_words
                    )
                )
        f.write("\n]")


@click.group()
async def main():
    pass


@main.command()
async def discover():
    """discover word previews from word pagination"""
    with open("englishprofile.json", "w") as f:
        f.write(json.dumps(discover(), indent=2))


@main.command()
@click.option("--speed", default=4, help="connection speed", type=click.INT)
async def worddata():
    """collect word data from discovered word previews"""
    with open("englishprofile.json") as f:
        words = json.loads(f.read())
        return await scrape_words(words, "worddata.json")


if __name__ == "__main__":
    main()
