import ssl
import time
import json

from bs4 import BeautifulSoup
import urllib3


class Crawler:
    baseUrl = "https://www.stats.gov.cn/sj/tjbz/tjyqhdmhcxhfdm/2023/"
    homePage = baseUrl + "index.html"

    def __init__(self):
        self.http = urllib3.PoolManager(cert_reqs=ssl.CERT_NONE)

    def get_soup(self, number):
        raw_data = self.http.request('GET', self.baseUrl + str(number) + ".html")
        soup = BeautifulSoup(raw_data.data, "html.parser")
        return soup

    def extract_info(self, tr):
        td_list = tr.find_all("td")
        if len(td_list) <= 1:
            raise Exception("td not found")
        td = td_list[1]
        return self.extract_info_from_td(td)

    @staticmethod
    def extract_info_from_td(td):
        a_list = td.find_all("a")
        if len(a_list) <= 0:
            raise Exception("a not found in td")
        a = a_list[0]
        href = a.attrs["href"]
        if href is None:
            raise Exception("href not found of a")
        identification = href.replace(".html", "").split("/")[-1]
        name = a.text
        return identification, name

    def get_province(self):
        soup = self.get_soup("index")
        table = soup.find_all("table", {"class": "provincetable"})[0]
        trs = table.find_all("tr", {"class": "provincetr"})
        tds = []
        for tr in trs:
            tds.extend(tr.find_all("td"))
        children = []
        for td in tds:
            try:
                province_id, name = self.extract_info_from_td(td)
                item = {
                    "id": province_id,
                    "name": name,
                    "children": self.get_city(province_id)
                }
                children.append(item)
            except:
                continue
        return children

    def get_city(self, province_id):
        soup = self.get_soup(province_id)
        table = soup.find_all("table", {"class": "citytable"})
        trs = table[0].find_all("tr", {"class": "citytr"})
        children = []
        for tr in trs:
            try:
                city_id, name = self.extract_info(tr)
                item = {
                    "id": city_id,
                    "name": name,
                    "children": self.get_county(province_id, city_id)
                }
                children.append(item)
            except:
                continue
        return children

    def get_county(self, province_id, city_id):
        soup = self.get_soup(province_id + "/" + city_id)
        table = soup.find_all("table", {"class": "countytable"})
        trs = table[0].find_all("tr", {"class": "countytr"})
        children = []
        for tr in trs:
            try:
                county_id, name = self.extract_info(tr)
                item = {
                    "id": county_id,
                    "name": name,
                    "children": self.get_town(province_id, city_id.replace(province_id, ""), county_id)
                }
                children.append(item)
            except:
                continue
        return children

    def get_town(self, province_id, city_id, county_id):
        soup = self.get_soup(province_id + "/" + city_id + "/" + county_id)
        table = soup.find_all("table", {"class": "towntable"})
        trs = table[0].find_all("tr", {"class": "towntr"})
        children = []
        for tr in trs:
            try:
                town_id, name = self.extract_info(tr)
                item = {
                    "id": town_id,
                    "name": name,
                }
                children.append(item)
            except:
                continue
        return children

    def main(self):
        result = self.get_province()
        with open('data.json', 'w') as f:
            json.dump(result, f, ensure_ascii=False)


if __name__ == '__main__':
    startTime = time.time()
    crawler = Crawler()
    crawler.main()
    print('Program running time: {} seconds'.format(time.process_time()))
    print('Total running time: {} seconds'.format(time.time() - startTime))
