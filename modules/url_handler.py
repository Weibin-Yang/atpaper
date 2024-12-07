from DrissionPage import Chromium
from DrissionPage import SessionPage
import requests
from dotenv import load_dotenv
from openai import OpenAI
import os
from modules.logger import setup_logger
import traceback

log = setup_logger("url_handler")

try:
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    log.info(f"初始化 OpenAI API 时出错：{e}")

def getabstract(url):

    reference = None
    doi_text = None
    page = SessionPage()

    try:
        page.get(url,retry=1, interval=1, timeout=3)
        if "www.sciencedirect.com" in url:
            try:
                # 提取摘要
                abstract_elements = page.eles("@@class=u-margin-s-bottom@@id=sp0010") or \
                    page.eles("@@class=u-margin-s-bottom@@id=sp0040") or \
                    page.eles("@@class=u-margin-s-bottom@@id=abspara0010") or \
                    page.eles("@@class=u-margin-s-bottom@@id=sp0075") or \
                    page.eles("@@class=u-margin-s-bottom@@id=sp0015") or \
                    page.eles("@@class=u-margin-s-bottom@@id=sp0050")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 调用 GPT 翻译摘要
                if abstract:
                    translation = gpt_translate(abstract)
                else:
                    log.info("未找到摘要")
                    with open("error_links.txt", "a", encoding="utf-8") as error_file:
                        error_file.write(f"{url}\n")
                    translation = None

                # 提取 DOI 链接
                # 提取 class="anchor doi anchor-primary" 的 href 属性
                doi_element = page.eles('@@class=anchor doi anchor-primary@@title=Persistent link using digital object identifier')
                if doi_element:
                    doi_link = doi_element[0].attr('href')  # 获取 href 属性
                    doi_link = doi_link.replace("https://doi.org/","")
                    reference = get_apa_citation(doi_link)

                    # 添加摘要原文和翻译到字典中
                    reference["abstract"] = abstract
                    reference["translation"] = translation
                else:
                    log.info("DOI 链接未找到")
                    with open("error_links.txt", "a", encoding="utf-8") as error_file:
                        error_file.write(f"{url}\n")

                return reference

            except Exception as e:
                log.info(f"Error: {e}")
                return None

        elif "www.frontiersin.org" in url:
            # 提取摘要
            abstract_elements = page.eles("@class=mb0")
            if not abstract_elements:
                abstract_elements = page.eles("@class=JournalAbstract__AcceptedArticle")
            abstract = abstract_elements[0].text if abstract_elements else None
            log.info(abstract)
            # 调用 GPT 翻译摘要
            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            # 提取 DOI 链接
            doi_element = page.ele('text:doi')
            doi_text = doi_element.text.split(": ")[1] if doi_element else None
            doi_text = doi_text.replace("https://doi.org/","")
            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'link.springer.com' in url or 'www.nature.com' in url or 'bmcpsychiatry.biomedcentral.com' in url:
            try:
                abstract_elements = page.eles("@id=Abs1-content")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('@class=c-bibliographic-information__value')
                doi_text = doi_element.filter_one.text('doi') if doi_element else None
                doi_text = doi_text.text.replace("https://doi.org/","")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("@id=Abs1-content")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('@class=c-bibliographic-information__value')
                doi_text = doi_element.filter_one.text('doi') if doi_element else None
                doi_text = doi_text.text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'www.tandfonline.com' in url:
            try:
                abstract_elements = page.eles("tag:p@class=last")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:li@class=dx-doi')
                doi_text = doi_element[0].text.replace("https://doi.org/", "") if doi_element else None
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:p@class=last")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:li@class=dx-doi')
                doi_text = doi_element[0].text.replace("https://doi.org/", "") if doi_element else None
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'journals.sagepub.com' in url:
            try:
                abstract_elements = page.eles("tag:div@role=paragraph")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:div@role=paragraph")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'econtent.hogrefe.com' in url:
            try:
                abstract_elements = page.eles("tag:div@class=abstractSection abstractInFull")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@class=epub-section__doi__text')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "") if doi_text else None
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:div@class=abstractSection abstractInFull")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@class=epub-section__doi__text')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'onlinelibrary.wiley.com' in url or "el.wiley.com" in url:
            try:
                abstract_elements = page.eles("tag:div@class=article-section__content en main")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@class=epub-doi')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:div@class=article-section__content en main")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@class=epub-doi')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'www.liebertpub.com' in url:
            try:
                abstract_elements = page.eles("tag:section@id=abstract")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:section@id=abstract")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'psycnet.apa.org' in url:
            browser = Chromium()
            tab = browser.latest_tab
            tab.get(url)
            abstract_elements = tab.ele("xpath=/html/body/app/main/recorddisplay/div/div/div/div[3]/div[1]/abstract/div/div/p")
            abstract = abstract_elements.text if abstract_elements else None
            if not abstract:
                abstract_elements = tab.eles("tag:div@class=col-md-12 p-0")
                abstract = abstract_elements[0].text if abstract_elements else None
            # 提取 DOI 链接
            doi_element = tab.eles('@text():doi.org')
            for doi in doi_element:
                d = doi.attr('href')
                doi_text = d.replace("https://psycnet.apa.org/doi/", "")
            browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'www.mdpi.com' in url:
            try:
                abstract_elements = page.eles("tag:div@class=html-p")
                abstract = abstract_elements[0].text if abstract_elements else None
                log.info(abstract)
                doi_element = page.eles('@text():doi.org')
                for doi in doi_element:
                    log.info(doi)
                    d = doi.attr('href')
                    log.info(d)
                    if isinstance(d, str) and 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                        break
                    else:
                        doi_text = None
            except Exception as e:

                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:div@class=html-p")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('@text():doi.org')
                for doi in doi_element:
                    d = doi.attr('href')
                    if isinstance(d, str) and 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                        break
                    else:
                        doi_text = None
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'academic.oup.com' in url:
            try:
                abstract_elements = page.eles("tag:p@class=chapter-para")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('@text():doi.org')
                for doi in doi_element:
                    d = doi.attr('href')
                    if 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                    else:
                        doi_text = None
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:p@class=chapter-para")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('@text():doi.org')
                for doi in doi_element:
                    d = doi.attr('href')
                    if isinstance(d, str) and 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                        break
                    else:
                        doi_text = None
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'www.jneurosci.org' in url:
            try:
                abstract_elements = page.eles("tag:p@id=p-5")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:span@class=highwire-cite-metadata-doi highwire-cite-metadata')
                doi_text = doi_element[0].text if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:p@id=p-5")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:span@class=highwire-cite-metadata-doi highwire-cite-metadata')
                doi_text = doi_element[0].text if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'direct.mit.edu' in url:
            try:
                abstract_elements = page.eles("tag:section@class=abstract")
                abstract = abstract_elements[0].text if abstract_elements else None

                doi_element = page.eles('@text():doi.org')
                for doi in doi_element:
                    d = doi.attr('href')
                    if isinstance(d, str) and 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                        break
                    else:
                        doi_text = None

            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:section@class=abstract")
                abstract = abstract_elements[0].text if abstract_elements else None

                # 提取 DOI 链接
                doi_element = tab.eles('@text():doi.org')
                for doi in doi_element:
                    d = doi.attr('href')
                    if isinstance(d, str) and 'doi.org' in d:
                        doi_text = d.replace("https://doi.org/", "")
                        break
                    else:
                        doi_text = None
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'www.pnas.org' in url:
            try:
                abstract_elements = page.eles("tag:div@id=abstracts")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:div@id=abstracts")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@property=sameAs')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        elif 'pmc.ncbi.nlm.nih.gov' in url:
            try:
                abstract_elements = page.eles("tag:section@@class=abstract@@id=abstract1")
                abstract = abstract_elements[0].text if abstract_elements else None
                doi_element = page.eles('tag:a@class=usa-link usa-link--external')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/", "")
            except Exception as e:
                browser = Chromium()
                tab = browser.latest_tab
                tab.get(url)
                abstract_elements = tab.eles("tag:section@@class=abstract@@id=abstract1")
                abstract = abstract_elements[0].text if abstract_elements else None
                # 提取 DOI 链接
                doi_element = tab.eles('tag:a@class=usa-link usa-link--external')
                doi_text = doi_element[0].attr('href') if doi_element else None
                doi_text = doi_text.replace("https://doi.org/","")
                browser.quit(timeout=3)

            if abstract:
                translation = gpt_translate(abstract)
            else:
                log.info("未找到摘要")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")
                translation = None

            if doi_text:
                reference = get_apa_citation(doi_text)

                reference["abstract"] = abstract
                reference["translation"] = translation
            else:
                log.info("DOI 链接未找到")
                with open("error_links.txt", "a", encoding="utf-8") as error_file:
                    error_file.write(f"{url}\n")

        else:
            with open("error_links.txt", "a", encoding="utf-8") as error_file:
                error_file.write(f"{url}\n")
            pass

        if reference:
            return reference
    
    except Exception as e:
        log.info(e.__traceback__)
        with open("error_links.txt", "a", encoding="utf-8") as error_file:
            error_file.write(f"{url}\n")
        log.info(f"Error: {e}")

def get_apa_citation(doi):
    """
    通过 DOI 获取论文的 APA 格式引用。
    :param doi: 文档的 DOI
    :return: APA 格式的引用字符串
    """
    url = f"https://api.crossref.org/works/{doi}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            item = data.get("message", {})

            # 提取 APA 引用所需信息
            authors = item.get("author", [])
            title = item.get("title", [""])[0]
            journal = item.get("container-title", [""])[0]
            year = item.get("created", {}).get("date-parts", [[None]])[0][0]
            volume = item.get("volume", "")
            issue = item.get("issue", "")
            pages = item.get("page", "")
            doi_link = f"{doi}"

            # 生成 APA 格式引用
            author_names = ", ".join(
                [f"{author['given']} {author['family']}" for author in authors]
            )
            apa_citation = (
                f"{author_names} ({year}). {title}. *{journal}*, *{volume}*" +
                (f"({issue})" if issue else "") +
                f", {pages}. {doi_link}"
            )

            # 返回字典
            return {
                "authors": author_names,
                "title": title,
                "journal": journal,
                "year": year,
                "volume": volume,
                "issue": issue,
                "pages": pages,
                "doi": "https://doi.org/{}".format(doi_link),
                "apa_citation": apa_citation,
            }

        else:
            log.info(f"Error: {response.status_code} - {response.text}")
            return {
                "authors": "Unknown",
                "title": "Unknown",
                "journal": "Unknown",
                "year": "Unknown",
                "volume": "Unknown",
                "issue": "Unknown",
                "pages": "Unknown",
                "doi": "https://doi.org/{}".format(doi),
                "apa_citation": "Unknown",
            }
    except Exception as e:
        log.info(f"Error fetching APA citation: {e}")
        return {
            "authors": "Unknown",
            "title": "Unknown",
            "journal": "Unknown",
            "year": "Unknown",
            "volume": "Unknown",
            "issue": "Unknown",
            "pages": "Unknown",
            "doi": "https://doi.org/{}".format(doi),
            "apa_citation": "Unknown",
        }

def gpt_translate(text, model="gpt-4o-mini"):
    """
    使用 GPT 进行摘要翻译，专注于心理学和神经科学领域。
    :param text: 需要翻译的英文摘要
    :param model: 使用的 GPT 模型
    :return: 专业、优雅的中文翻译文本
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator specializing in academic research articles, "
                        "particularly in the fields of psychology and neuroscience. Your task is to produce "
                        "high-quality, accurate, and elegant Chinese translations of English abstracts. "
                        "Ensure the translation retains the original meaning while using professional and precise terminology."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Translate the following academic abstract to Chinese:\n\n{text}\n\n"
                        "Requirements:\n"
                        "1. Maintain high accuracy and fidelity to the original meaning.\n"
                        "2. Use professional terminology commonly used in psychology and neuroscience.\n"
                        "3. Ensure the translation reads naturally and elegantly in Chinese."
                    )
                }
            ]
        )
        # 提取翻译结果
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.info(f"调用 GPT API 进行翻译时出错：{e}")
        return None

def stork_url (storkurl):
    page = SessionPage()
    reference = None
    doi_text = None
    try:
        page.get(storkurl, retry=1, interval=1, timeout=3)
        title_element = page.eles("tag:h1@class=h3")
        title = title_element[0].text if title_element else None
        abstract_element = page.eles("tag:p@id=abstractHolder")
        abstract = abstract_element[0].text if abstract_element else None
        doi_element = page.eles('@text():doi.org')
        for doi in doi_element:
            d = doi.attr('href')
            if isinstance(d, str) and 'doi.org' in d:
                doi_text = d.replace("https://doi.org/", "")
                break
            else:
                doi_text = None
    except Exception as e:
        browser = Chromium()
        tab = browser.latest_tab
        tab.get(url)
        title_element = tab.eles("tag:h1@class=h3")
        title = title_element[0].text if title_element else None
        abstract_element = tab.eles("tag:p@id=abstractHolder")
        abstract = abstract_element[0].text if abstract_element else None
        # 提取 DOI 链接
        doi_element = tab.eles('@text():doi.org')
        for doi in doi_element:
            d = doi.attr('href')
            if isinstance(d, str) and 'doi.org' in d:
                doi_text = d.replace("https://doi.org/", "")
                break
            else:
                doi_text = None
        browser.quit(timeout=3)
    if abstract:
        translation = gpt_translate(abstract)
    else:
        log.info("未找到摘要")
        with open("error_links.txt", "a", encoding="utf-8") as error_file:
            error_file.write(f"{url}\n")
        translation = None

    if doi_text:
        reference = get_apa_citation(doi_text)

        reference["abstract"] = abstract
        reference["translation"] = translation
    else:
        log.info("DOI 链接未找到")
        with open("error_links.txt", "a", encoding="utf-8") as error_file:
            error_file.write(f"{url}\n")

    if reference:
        return reference

if __name__ == '__main__':
    url = "https://www.storkapp.me/paper/showPaper.php?id=1947272613&displayKey=n6ubCqAUEh"
    reference = stork_url(url)
    # log.info(reference)