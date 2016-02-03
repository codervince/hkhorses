import scrapy
#from scrapy.loader import ItemLoader
from hkhorses.items import HkhorsesItem
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from scrapy import log
from scrapy.http import Request
from scrapy.contrib.loader.processor import TakeFirst
import re
import csv
import logging
from hkhorses.utilities2 import *
from urlparse import urljoin

RE_VAL  = re.compile(r"^:*\s*")
T_PAT = re.compile(r'.*trainercode=([A-Z]{2,3})&.*')
J_PAT = re.compile(r'.*JockeyCode=([A-Z]{2,3})&.*')
RACENO_PAT = re.compile(r'.*raceno=([0-9]{1,2})&.*')
RACECOURSE_PAT = re.compile(r'.*venue=([A-Z]{2})$')
#RE_HCODE = re.compile(r'value=\"[A-Z]\d{3}\"')
#convenience function from Constantin
def tf(values, encoding="utf-8"):
    value = ""
    for v in values:
        if v is not None and v != "":
            value = v
            break
    return value.encode(encoding).strip()

def tf2(v, encoding="utf-8"):
    v = v[0]
    value = ""
    if v is not None and v != "":
        value = v
    return value.encode(encoding).strip()

# class HorseItemLoader(ItemLoader):
#     default_output_processor = TakeFirst()

logger = logging.getLogger('hkhorses_application')
class HKhorsesSpider(scrapy.Spider):
    name = "hkhorses"
    allowed_domains = ["racing.hkjc.com"]

        #input.csv
    def __init__(self, input_filename='horsecodes.csv', *args, **kwargs):
        super(HKhorsesSpider, self).__init__(*args, **kwargs)
        with open(input_filename, 'rU') as f:
            self.input_data = list(csv.DictReader(f, skipinitialspace=True))

        self.base_url = "http://www.hkjc.com/english/racing/horse.asp?horseno="
        self.skimpy_url = "http://www.hkjc.com/english"
        self.reference_date = datetime.today()

    def start_requests(self):
        for data in self.input_data:
            url = self.base_url + data['horsecode'] + '&Option=1#htop'
            #check alt url http://www.hkjc.com/english/racing/horse.asp?horseno=S379&Option=1%0A
            yield scrapy.Request(url, self.parse,meta={'try_num': 1, 'horsecode': data['horsecode']})

    def parse(self, response):
        logger.info('A response from %s just arrived!', response.url)
        # loader = HorseItemLoader(HkhorsesItem(), response=response)
        # item = HkhorsesItem()
        horsecode = response.meta['horsecode']
        tw_url = "http://www.hkjc.com/english/racing/Track_Result.asp?txtHorse_BrandNo={}".format(horsecode)
        vet_url= "http://www.hkjc.com/english/racing/ove_horse.asp?HorseNo={}".format(horsecode)
        MAX_ROWS = 9999
        samesirecodes = []
        try:
            horse_name = tf(response.css(".subsubheader .title_eng_text").xpath("text()").extract()).split("\xc2\xa0")[0].strip()
            age = RE_VAL.sub("", tf(response.xpath("//font[contains(text(),'Country') and contains(text(),'Origin')]/../following-sibling::td[1]/font/text()").extract())).split("/")[1]
            country_of_origin = countryoforigin= RE_VAL.sub("", tf(response.xpath("//font[contains(text(),'Country') and contains(text(),'Origin')]/../following-sibling::td[1]/font/text()").extract())).split("/")[0].strip()
            year_of_birth = getdateofbirth(self.reference_date,int(age.strip()), country_of_origin)
            sirecodes = response.xpath("//select[@name='SIRE']/option/@value").extract()
            samesirecodes = [s.strip() for s in sirecodes]

            #URLS
            #pedigreeurl
            pedigree_url = response.xpath("//a[contains(text(), 'Pedigree')]/@href").extract()[0].strip()
            pedigree_url = urljoin('http://www.hkjc.com/', pedigree_url.replace(u'..', u'english'))
            meta2 = dict(horsecode=horsecode,
                        horsename=horse_name,
                        yob= year_of_birth,
                        samesirecodes= samesirecodes,
                        countryoforigin= country_of_origin,
                        twurl = tw_url,
                        veturl = vet_url,
                        pedigreeurl= pedigree_url,
                        importtype=RE_VAL.sub("", tf(response.xpath("//font[contains(text(),'Import') and contains(text(),'Type')]/../following-sibling::td[1]/font/text()").extract())),
                        owner=tf(response.xpath("//font[text()='Owner']/../following-sibling::td[1]/font/a/text()").extract()),
                        sirename=tf(response.xpath("//font[text()='Sire']/../following-sibling::td[1]/font/a/text()").extract()),
                        damname=RE_VAL.sub("", tf(response.xpath("//font[text()='Dam']/../following-sibling::td[1]/font/text()").extract())),
                        damsirename=RE_VAL.sub("", tf(response.xpath("//font[text()=\"Dam's Sire\"]/../following-sibling::td[1]/font/text()").extract())))
            item = HkhorsesItem(**meta2)

            #results table
            #per row
            pastraceindexes = list()
            pastracedates = list()
            pastplaces = list()
            pastdistances= list()
            pastgoings= list()
            pastraceclasses= list()
            pasttrainers= list()
            pastjockeys= list()
            pastrps= list()
            pastfinishtimes= list()
            pasthorseweights= list()
            pastgears= list()
            pastracecourses= list()
            pastsurfaceconfigs= list()
            pastraceconfigs = list()

            results_table = response.xpath("//table[@class='bigborder']//tr[ @bgcolor and not(@height) and not(@width) and position()>1]")
            maxi = 0
            #do until MAX_ROWS
            for i, row in enumerate(results_table):
                if i < MAX_ROWS:
                #cutoff point
                    maxi = i
                    #collect
                    # print(row)
                    #issue need to exclude season rows
                    h_raceindex = row.xpath("td")[0].xpath("a/text()").extract()
                    h_racenumberracecourse= row.xpath("td")[0].xpath("a/@href").extract()[0].strip()
                    h_raceno = re.match(RACENO_PAT, h_racenumberracecourse).group(1)

                    print (h_raceno)
                    print (re.match(RACECOURSE_PAT, h_racenumberracecourse).group(1))
                    pastraceindexes.extend(h_raceindex)
                    h_racedate = row.xpath("td")[2].xpath("text()").extract()[0]
                    pastracedates.extend(h_racedate)
                    h_racedateobj = datetime.strptime(h_racedate, "%d/%m/%y").date()
                    urlracedate = datetime.strftime(h_racedateobj, "%Y%m%d")
                    #racevideourl
                    racevideofull_url = "http://racing.hkjc.com/racing/video/play.asp?type=replay-full&date={0}&no={1}&lang=eng".format(urlracedate,h_raceno)
                    racevideoaerial_url = "http://racing.hkjc.com/racing/video/aerial.aspx?date={0}&no={1}&lang=eng".format(urlracedate,h_raceno)
                    print(racevideofull_url,racevideoaerial_url)
                    #place, #ractrackcourse, #dist, #going..#class, #draw, ....trainer

                    h_place = row.xpath("td")[1].xpath("*//text()").extract()
                    pastplaces.extend(h_place)

                    h_distance = row.xpath("td")[4].xpath("text()").extract()[0].strip()
                    h_going = row.xpath("td")[5].xpath("text()").extract()[0].strip()
                    h_raceclass = row.xpath("td")[6].xpath("text()").extract()[0].strip()
                    h_draw = row.xpath("td")[7].xpath("font").xpath("text()").extract()[0].strip()
                    h_rating = row.xpath("td")[8].xpath("text()").extract()[0].strip()
                    h_trainer = " ".join(row.xpath("td")[9].xpath("a/@href").extract()).strip()
                    h_jockey = " ".join(row.xpath("td")[10].xpath("a/@href").extract()).strip()
                    # print(h_distance)
                    print(h_distance,h_going,h_raceclass,h_draw,h_rating, re.match(T_PAT, h_trainer).group(1),
                    re.match(J_PAT, h_jockey).group(1))

                    h_lbw =  row.xpath("td")[11].xpath("*/text()| text()").extract()[0].strip()
                    h_winodds =  row.xpath("td")[12].xpath("text()").extract()[0].strip()
                    h_actwt =  row.xpath("td")[13].xpath("text()").extract()[0].strip()
                    h_rp = " ".join(row.xpath("td")[14].xpath("*//text()").extract()).strip().replace(unichr(160), "")
                    h_finishtime = row.xpath("td")[15].xpath("text()").extract()[0].strip()
                    h_horseweight = row.xpath("td")[16].xpath("text()").extract()[0].strip()
                    h_gear = row.xpath("td")[17].xpath("text()").extract()[0].strip()

                    print(h_lbw, h_winodds, h_actwt, h_rp, h_finishtime, h_horseweight, h_gear)

                # h_distance = row.xpath("td")[4].xpath("text()").extract()
                # pastdistances.extend(h_distance)
                # h_raceconfigs = row.xpath("td")[3].xpath("/text()").extract()
                # pastraceconfigs.extend(h_raceconfigs)
                #20/01/16

                #h_places = row.xpath("td")[1].xpath("*//text()").extract()[0].strip()
                # h_racedates = datetime.strptime(
                #                     row.xpath("td")[2].xpath("text()").extract()[0].strip(),
                #                     "%d/%m/%y")
                #print("pastplaces", h_places)
                # print("pastdate", h_racedate)

            pastraceindexes= filter(lambda x: x.strip(), pastraceindexes)
            print("should be equal", maxi+1, len(pastraceindexes)) #filter based on max race depth
            # td[not(@width) and not(@height) and contains(@class, 'htable_eng_text')]
            #cleaning lists 1
            # pastraceconfigs_ = filter(lambda x: x.strip(), pastraceconfigs)
            # # pastdistances_ = filter(lambda x: x.strip(), pastdistances)

            # pastracedates_= filter(lambda x: x.strip(), pastracedates)
            # pastracedates = [ datetime.strptime(x, "%d/%m/%y").date() for x in pastracedates_]
            item['pastraceindexes'] = pastraceindexes
            # item['pastracedates'] = pastracedates
            # item['pastraceconfigs'] = pastraceconfigs_
            # item['pastdistances'] = pastdistances_
            #aggregate data in lists e.g. distancebetweenruns


            #correlations


            yield item
        except Exception, e:
            log.msg("Skipping horse code %s because of error: %s" % (horsecode, str(e)))

        #countryoforigin, age, importtype, sirename sirecode
        #damname damcode damsirename, samsirecode
        #twurl veturl pedigreeurl

        #results
